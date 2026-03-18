"""Tracker service — topic persistence and multi-source paper discovery.

All sources use public APIs (no scraping) for reliability from any server location.
"""

import asyncio
import json
import os
import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List




def list_topics(db):
    rows = db.execute("SELECT * FROM topics ORDER BY created_at DESC").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        # Parse sources JSON string back to list
        try:
            d["sources"] = json.loads(d.get("sources") or '["arxiv"]')
        except (json.JSONDecodeError, TypeError):
            d["sources"] = ["arxiv"]
        result.append(d)
    return result


# Available sources registry — all API-based for reliability
AVAILABLE_SOURCES = {
    "arxiv": {"label": "ArXiv", "status": "active", "description": "开放获取预印本 (物理/数学/计算机/经济)"},
    "openalex": {"label": "OpenAlex", "status": "active", "description": "全球最大开放学术数据库 (2亿+ 论文)"},
    "semantic_scholar": {"label": "Semantic Scholar", "status": "active", "description": "AI 驱动的学术搜索 (语义理解)"},
    "crossref": {"label": "CrossRef", "status": "active", "description": "DOI 注册机构 (正式发表的期刊论文)"},
    "doaj": {"label": "DOAJ", "status": "active", "description": "开放获取期刊 (含法律类)"},
    "core": {"label": "CORE", "status": "active", "description": "全球开放获取论文聚合"},
    "cnki": {"label": "CNKI (知网)", "status": "active", "description": "中国知网 (中文论文)"},
    "ssrn": {"label": "SSRN", "status": "active", "description": "社科/法律预印本 (Elsevier)"},
    "baidu_scholar": {"label": "百度学术", "status": "active", "description": "百度学术搜索 (国内可靠)"},
}


def create_topic(db, title: str, check_frequency: str, sources: List[str] = None):
    if sources is None:
        sources = ["arxiv"]
    # Validate sources
    valid_sources = [s for s in sources if s in AVAILABLE_SOURCES]
    if not valid_sources:
        valid_sources = ["arxiv"]

    topic_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    sources_json = json.dumps(valid_sources)
    db.execute(
        "INSERT INTO topics (id, title, check_frequency, sources, created_at) VALUES (?, ?, ?, ?, ?)",
        (topic_id, title, check_frequency, sources_json, now),
    )
    db.commit()
    return {
        "id": topic_id,
        "title": title,
        "check_frequency": check_frequency,
        "sources": valid_sources,
        "created_at": now,
    }


def delete_topic(db, topic_id: str):
    db.execute("DELETE FROM topics WHERE id=?", (topic_id,))
    db.commit()
    return {"status": "deleted"}


async def _generate_brief(title: str, abstract: str) -> str:
    """Generate a brief summary from the abstract — no LLM, just truncate."""
    if not abstract:
        return title[:120]
    clipped = abstract[:200].strip()
    return clipped + ("..." if len(abstract) > 200 else "")


def _get_or_create_folders(conn, topic_id, title):
    """Create/reuse folder hierarchy for auto-filing discovered papers."""
    parent_folder = conn.execute(
        "SELECT id FROM paper_folders WHERE topic_id=? AND parent_id IS NULL",
        (topic_id,)
    ).fetchone()
    if parent_folder:
        parent_folder_id = parent_folder["id"]
    else:
        parent_folder_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO paper_folders (id, name, parent_id, source, topic_id, created_at) VALUES (?,?,NULL,'tracker',?,?)",
            (parent_folder_id, title, topic_id, datetime.utcnow().isoformat())
        )

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    existing_today = conn.execute(
        "SELECT COUNT(*) FROM paper_folders WHERE parent_id=? AND name LIKE ?",
        (parent_folder_id, f"{today_str}%")
    ).fetchone()[0]
    nth = existing_today + 1
    sub_folder_name = f"{today_str} 第{nth}次查询"
    sub_folder_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO paper_folders (id, name, parent_id, source, topic_id, created_at) VALUES (?,?,?,'tracker',?,?)",
        (sub_folder_id, sub_folder_name, parent_folder_id, topic_id, datetime.utcnow().isoformat())
    )
    return sub_folder_id, sub_folder_name


def _save_paper(conn, topic_id, entry_title, entry_url, brief, sub_folder_id, source_label, now):
    """Save a discovered paper to topic_papers and auto-import to papers library."""
    existing = conn.execute(
        "SELECT id FROM topic_papers WHERE topic_id=? AND url=?",
        (topic_id, entry_url),
    ).fetchone()
    if existing:
        return False

    tp_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO topic_papers (id, topic_id, title, url, brief, status, discovered_at)
           VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
        (tp_id, topic_id, entry_title, entry_url, brief, now),
    )

    # Auto-save to papers library
    paper_exists = conn.execute("SELECT id FROM papers WHERE url=?", (entry_url,)).fetchone()
    if not paper_exists:
        paper_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO papers (id, title, url, source, status, folder_id, read_status, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'pending', ?, 'unread', ?, ?)""",
            (paper_id, entry_title, entry_url, source_label, sub_folder_id, now, now)
        )
        return True
    return False


# ═══════════════════════════════════════════
#  ArXiv Search (XML API — reliable)
# ═══════════════════════════════════════════
async def search_arxiv_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search ArXiv for papers related to a topic."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        query = title.replace(" ", "+")
        api_url = (
            "http://export.arxiv.org/api/query"
            f"?search_query=all:{query}&max_results={max_results}"
            "&sortBy=submittedDate&sortOrder=descending"
        )

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(api_url)
            resp.raise_for_status()

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(resp.text)

        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for entry in root.findall("atom:entry", ns):
            entry_title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
            summary = entry.findtext("atom:summary", "", ns).strip()

            entry_url = None
            for link in entry.findall("atom:link", ns):
                if link.get("type") == "text/html" or (not link.get("title") and link.get("rel") == "alternate"):
                    entry_url = link.get("href")
                    break
            if not entry_url:
                entry_url = entry.findtext("atom:id", "", ns)

            brief = await _generate_brief(entry_title, summary)
            if _save_paper(conn, topic_id, entry_title, entry_url, brief, sub_folder_id, "arxiv", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] ArXiv: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] ArXiv search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


# ═══════════════════════════════════════════
#  OpenAlex Search (free REST API — very reliable)
# ═══════════════════════════════════════════
async def search_openalex_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search OpenAlex for papers. Free, no auth, global access, 200M+ works."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.openalex.org/works",
                params={
                    "search": title,
                    "per_page": max_results,
                    "sort": "relevance_score:desc",
                    "mailto": "xiaotiao@example.com",  # Polite pool
                },
                headers={"User-Agent": "xiaotiao/1.0 (mailto:xiaotiao@example.com)"}
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for work in results:
            work_title = work.get("title", "").strip()
            if not work_title:
                continue
            # Get best URL
            doi = work.get("doi", "")
            oa_url = ""
            if work.get("open_access", {}).get("oa_url"):
                oa_url = work["open_access"]["oa_url"]
            entry_url = oa_url or doi or work.get("id", "")
            if not entry_url:
                continue

            # Get abstract from inverted index
            abstract = ""
            inv_index = work.get("abstract_inverted_index")
            if inv_index and isinstance(inv_index, dict):
                # Reconstruct abstract from inverted index
                positions = []
                for word, pos_list in inv_index.items():
                    for pos in pos_list:
                        positions.append((pos, word))
                positions.sort()
                abstract = " ".join(w for _, w in positions)

            brief = await _generate_brief(work_title, abstract)
            if _save_paper(conn, topic_id, work_title, entry_url, brief, sub_folder_id, "openalex", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] OpenAlex: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] OpenAlex search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


# ═══════════════════════════════════════════
#  Semantic Scholar Search (free API — AI-powered)
# ═══════════════════════════════════════════
async def search_semantic_scholar_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search Semantic Scholar. Free API, AI-powered relevance ranking."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": title,
                    "limit": max_results,
                    "fields": "title,url,abstract,externalIds",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        papers = data.get("data", [])
        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for p in papers:
            p_title = (p.get("title") or "").strip()
            if not p_title:
                continue
            p_url = p.get("url", "")
            ext = p.get("externalIds", {})
            if ext.get("DOI"):
                p_url = p_url or f"https://doi.org/{ext['DOI']}"
            if not p_url:
                p_url = f"https://www.semanticscholar.org/paper/{p.get('paperId', '')}"

            abstract = p.get("abstract", "") or ""
            brief = await _generate_brief(p_title, abstract)
            if _save_paper(conn, topic_id, p_title, p_url, brief, sub_folder_id, "semantic_scholar", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] Semantic Scholar: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] Semantic Scholar search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


# ═══════════════════════════════════════════
#  CrossRef Search (DOI registry — formal publications)
# ═══════════════════════════════════════════
async def search_crossref_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search CrossRef for formally published papers with DOIs."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.crossref.org/works",
                params={
                    "query": title,
                    "rows": max_results,
                    "sort": "relevance",
                    "order": "desc",
                },
                headers={
                    "User-Agent": "xiaotiao/1.0 (mailto:xiaotiao@example.com)",
                }
            )
            resp.raise_for_status()
            data = resp.json()

        items = data.get("message", {}).get("items", [])
        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for item in items:
            # CrossRef titles are in a list
            titles = item.get("title", [])
            p_title = titles[0] if titles else ""
            if not p_title:
                continue
            doi = item.get("DOI", "")
            p_url = f"https://doi.org/{doi}" if doi else item.get("URL", "")
            if not p_url:
                continue

            # Get abstract (if available)
            abstract = item.get("abstract", "") or ""
            # Remove XML tags from CrossRef abstracts
            abstract = re.sub(r'<[^>]+>', '', abstract)

            brief = await _generate_brief(p_title, abstract)
            if _save_paper(conn, topic_id, p_title, p_url, brief, sub_folder_id, "crossref", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] CrossRef: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] CrossRef search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


# ═══════════════════════════════════════════
#  DOAJ Search (Directory of Open Access Journals)
# ═══════════════════════════════════════════
async def search_doaj_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search DOAJ for open access journal articles (includes legal journals)."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://doaj.org/api/search/articles/" + title.replace(" ", "%20"),
                params={"pageSize": max_results, "sort": "relevance"},
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for item in results:
            bibjson = item.get("bibjson", {})
            p_title = bibjson.get("title", "").strip()
            if not p_title:
                continue

            # Get URL from links or DOI
            p_url = ""
            for link in bibjson.get("link", []):
                if link.get("type") == "fulltext":
                    p_url = link.get("url", "")
                    break
            if not p_url:
                ids = bibjson.get("identifier", [])
                for ident in ids:
                    if ident.get("type") == "doi":
                        p_url = f"https://doi.org/{ident['id']}"
                        break
            if not p_url:
                p_url = f"https://doaj.org/article/{item.get('id', '')}"

            abstract = bibjson.get("abstract", "") or ""
            brief = await _generate_brief(p_title, abstract)
            if _save_paper(conn, topic_id, p_title, p_url, brief, sub_folder_id, "doaj", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] DOAJ: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] DOAJ search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


# ═══════════════════════════════════════════
#  CORE Search (Open Access aggregator)
# ═══════════════════════════════════════════
async def search_core_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search CORE for open access research papers."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        core_api_key = os.getenv("CORE_API_KEY", "")
        headers = {}
        if core_api_key:
            headers["Authorization"] = f"Bearer {core_api_key}"

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.core.ac.uk/v3/search/works",
                params={"q": title, "limit": max_results},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for item in results:
            p_title = (item.get("title") or "").strip()
            if not p_title:
                continue
            p_url = item.get("downloadUrl") or item.get("sourceFulltextUrls", [""])[0] if item.get("sourceFulltextUrls") else ""
            if not p_url:
                doi = item.get("doi", "")
                p_url = f"https://doi.org/{doi}" if doi else f"https://core.ac.uk/works/{item.get('id', '')}"

            abstract = item.get("abstract", "") or ""
            brief = await _generate_brief(p_title, abstract)
            if _save_paper(conn, topic_id, p_title, p_url, brief, sub_folder_id, "core", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] CORE: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] CORE search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


# ═══════════════════════════════════════════
#  CNKI Search (中国知网 — via public search)
# ═══════════════════════════════════════════
async def search_cnki_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search CNKI for Chinese academic papers."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                "https://kns.cnki.net/kns8s/brief/grid",
                params={
                    "txt_1_sel": "SU",
                    "txt_1_value1": title,
                    "currentid": "txt_1_value1",
                    "pageNum": 1,
                    "pageSize": max_results,
                    "sorttype": "FT",
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://kns.cnki.net/",
                }
            )
            resp.raise_for_status()

        papers_found = _parse_cnki_html(resp.text)

        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for p in papers_found[:max_results]:
            brief = await _generate_brief(p["title"], p.get("abstract", ""))
            if _save_paper(conn, topic_id, p["title"], p["url"], brief, sub_folder_id, "cnki", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] CNKI: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] CNKI search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


def _parse_cnki_html(html_text):
    papers = []
    pattern = r'<a[^>]*class="fz14"[^>]*href="(/kcms2/article/abstract[^"]*)"[^>]*>(.*?)</a>'
    for match in re.finditer(pattern, html_text, re.DOTALL):
        url_path = match.group(1)
        raw_title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if raw_title:
            papers.append({
                "title": raw_title,
                "url": f"https://kns.cnki.net{url_path}",
                "abstract": ""
            })
    return papers


# ═══════════════════════════════════════════
#  SSRN Search (Social Science Research Network)
# ═══════════════════════════════════════════
async def search_ssrn_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search SSRN for social science and legal papers."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                "https://api.ssrn.com/content/v1/bindings",
                params={"term": title, "count": max_results, "sort": "Relevance"},
                headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code == 200:
                papers_found = _parse_ssrn_json(resp.json())
            else:
                # Fallback: scrape search page
                resp2 = await client.get(
                    "https://papers.ssrn.com/sol3/results.cfm",
                    params={"txtKey_Words": title, "npage": 1},
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                resp2.raise_for_status()
                papers_found = _parse_ssrn_html(resp2.text)

        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for p in papers_found[:max_results]:
            brief = await _generate_brief(p["title"], p.get("abstract", ""))
            if _save_paper(conn, topic_id, p["title"], p["url"], brief, sub_folder_id, "ssrn", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] SSRN: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] SSRN search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


def _parse_ssrn_json(data):
    papers = []
    for item in (data if isinstance(data, list) else data.get("papers", data.get("results", []))):
        title = item.get("title", "").strip()
        abstract_id = item.get("id") or item.get("abstractId", "")
        url = f"https://papers.ssrn.com/sol3/papers.cfm?abstract_id={abstract_id}" if abstract_id else ""
        if title and url:
            papers.append({"title": title, "url": url, "abstract": item.get("abstract", "")})
    return papers


def _parse_ssrn_html(html_text):
    papers = []
    pattern = r'<a[^>]*href="(https://papers\.ssrn\.com/sol3/papers\.cfm\?abstract_id=\d+)"[^>]*>\s*([^<]+)'
    for match in re.finditer(pattern, html_text):
        url, title = match.group(1), match.group(2).strip()
        if title and len(title) > 5:
            papers.append({"title": title, "url": url, "abstract": ""})
    return papers


# ═══════════════════════════════════════════
#  Unified dispatcher — search all selected sources
# ═══════════════════════════════════════════

# ── Baidu Scholar Search (百度学术 — web scraping) ──
async def search_baidu_scholar_for_topic(topic_id: str, title: str, max_results: int = 10, db_path: str = None):
    """Search Baidu Scholar for academic papers. Reliable from Chinese servers."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(
                "https://xueshu.baidu.com/s",
                params={"wd": title, "pn": 0, "ie": "utf-8"},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Referer": "https://xueshu.baidu.com/",
                }
            )
            resp.raise_for_status()

        papers_found = _parse_baidu_scholar_html(resp.text)

        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for p in papers_found[:max_results]:
            brief = await _generate_brief(p["title"], p.get("abstract", ""))
            if _save_paper(conn, topic_id, p["title"], p["url"], brief, sub_folder_id, "baidu_scholar", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] BaiduScholar: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] BaiduScholar search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


def _parse_baidu_scholar_html(html_text):
    """Parse Baidu Scholar search results HTML."""
    papers = []
    # Each result is in a div with class "result"
    # Title is in <h3 class="t"><a>...</a></h3>
    # Abstract is in <div class="c_abstract">...</div>
    title_pattern = r'<h3[^>]*class="t"[^>]*>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
    abstract_pattern = r'<div[^>]*class="c_abstract"[^>]*>(.*?)</div>'

    titles = list(re.finditer(title_pattern, html_text, re.DOTALL))
    abstracts = list(re.finditer(abstract_pattern, html_text, re.DOTALL))

    for i, match in enumerate(titles):
        url = match.group(1)
        raw_title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        abstract = ""
        if i < len(abstracts):
            abstract = re.sub(r'<[^>]+>', '', abstracts[i].group(1)).strip()

        if raw_title and url:
            papers.append({
                "title": raw_title,
                "url": url,
                "abstract": abstract
            })
    return papers


SOURCE_SEARCH_MAP = {
    "arxiv": search_arxiv_for_topic,
    "openalex": search_openalex_for_topic,
    "semantic_scholar": search_semantic_scholar_for_topic,
    "crossref": search_crossref_for_topic,
    "doaj": search_doaj_for_topic,
    "core": search_core_for_topic,
    "cnki": search_cnki_for_topic,
    "ssrn": search_ssrn_for_topic,
    "baidu_scholar": search_baidu_scholar_for_topic,
}


async def search_topic_all_sources(topic_id: str, title: str, sources: List[str] = None, db_path: str = None):
    """Search sources sequentially with real-time progress tracking."""
    if not sources:
        sources = ["arxiv"]

    import sqlite3
    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")

    # Initialize progress tracking
    conn = sqlite3.connect(target_db)
    conn.execute("CREATE TABLE IF NOT EXISTS search_progress (topic_id TEXT PRIMARY KEY, total INTEGER, completed INTEGER, current_source TEXT, status TEXT, updated_at TEXT)")
    now = datetime.utcnow().isoformat()
    conn.execute("INSERT OR REPLACE INTO search_progress (topic_id, total, completed, current_source, status, updated_at) VALUES (?,?,?,?,?,?)",
                 (topic_id, len(sources), 0, sources[0] if sources else '', 'searching', now))
    conn.commit()
    conn.close()

    completed = 0
    for source in sources:
        fn = SOURCE_SEARCH_MAP.get(source)
        if not fn:
            completed += 1
            continue

        # Update current source BEFORE starting
        try:
            c = sqlite3.connect(target_db)
            c.execute("UPDATE search_progress SET current_source=?, updated_at=? WHERE topic_id=?",
                      (source, datetime.utcnow().isoformat(), topic_id))
            c.commit()
            c.close()
        except Exception:
            pass

        try:
            await fn(topic_id, title, db_path=db_path)
            print(f"[tracker] Source {source} completed for '{title}'")
        except Exception as e:
            print(f"[tracker] Source {source} failed: {e}")

        # Update progress AFTER source completes
        completed += 1
        try:
            c = sqlite3.connect(target_db)
            c.execute("UPDATE search_progress SET completed=?, current_source=?, updated_at=? WHERE topic_id=?",
                      (completed, source + ' ✓', datetime.utcnow().isoformat(), topic_id))
            c.commit()
            c.close()
        except Exception:
            pass

    # Mark as done
    conn = sqlite3.connect(target_db)
    conn.execute("UPDATE search_progress SET status='done', completed=?, current_source='', updated_at=? WHERE topic_id=?",
                 (len(sources), datetime.utcnow().isoformat(), topic_id))
    conn.commit()
    conn.close()

