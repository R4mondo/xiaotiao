"""Tracker service — topic persistence and multi-source paper discovery."""

import asyncio
import json
import os
import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List

from services.llm import call_claude_json


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


# Available sources registry — all sources now active
AVAILABLE_SOURCES = {
    "arxiv": {"label": "ArXiv", "status": "active"},
    "ssrn": {"label": "SSRN", "status": "active"},
    "cnki": {"label": "CNKI (中国知网)", "status": "active"},
    "heinonline": {"label": "HeinOnline", "status": "active"},
    "google_scholar": {"label": "Google Scholar", "status": "active"},
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
    if not abstract:
        return title[:120]

    system_prompt = (
        "你是一位学术论文追踪助手。请基于标题与摘要生成一段中文短概要。"
        "要求：50-120字，聚焦核心贡献与结论，只返回 JSON："
        '{"brief":"..."}'
    )
    user_prompt = f"标题：{title}\n摘要：{abstract}"
    try:
        result = await call_claude_json(system_prompt, user_prompt, max_tokens=300)
        brief = (result.get("brief") or result.get("summary") or "").strip()
        if brief:
            return brief
    except Exception:
        pass

    clipped = abstract[:200]
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
    """Save a discovered paper to topic_papers and optionally to the papers library."""
    existing = conn.execute(
        "SELECT id FROM topic_papers WHERE topic_id=? AND url=?",
        (topic_id, entry_url),
    ).fetchone()
    if existing:
        return False

    tp_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO topic_papers (id, topic_id, title, url, brief, status, discovered_at)
           VALUES (?, ?, ?, ?, ?, 'done', ?)""",
        (tp_id, topic_id, entry_title, entry_url, brief, now),
    )

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
#  ArXiv Search
# ═══════════════════════════════════════════
async def search_arxiv_for_topic(topic_id: str, title: str, max_results: int = 5, db_path: str = None):
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

        async with httpx.AsyncClient(timeout=30) as client:
            await asyncio.sleep(3)  # Respect ArXiv rate limits
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
#  SSRN Search (via papers.ssrn.com)
# ═══════════════════════════════════════════
async def search_ssrn_for_topic(topic_id: str, title: str, max_results: int = 5, db_path: str = None):
    """Search SSRN for papers related to a topic."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(
                "https://api.ssrn.com/content/v1/bindings",
                params={"term": title, "count": max_results, "sort": "Relevance"},
                headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            # Fallback: scrape the search page if API is unavailable
            if resp.status_code != 200:
                resp = await client.get(
                    f"https://papers.ssrn.com/sol3/results.cfm",
                    params={"txtKey_Words": title, "npage": 1},
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                resp.raise_for_status()
                # Parse HTML for paper links
                papers_found = _parse_ssrn_html(resp.text)
            else:
                papers_found = _parse_ssrn_json(resp.json())

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
    # Extract paper links and titles from SSRN search results HTML
    pattern = r'<a[^>]*href="(https://papers\.ssrn\.com/sol3/papers\.cfm\?abstract_id=\d+)"[^>]*>\s*([^<]+)'
    for match in re.finditer(pattern, html_text):
        url, title = match.group(1), match.group(2).strip()
        if title and len(title) > 5:
            papers.append({"title": title, "url": url, "abstract": ""})
    return papers


# ═══════════════════════════════════════════
#  Google Scholar Search (via scraping)
# ═══════════════════════════════════════════
async def search_google_scholar_for_topic(topic_id: str, title: str, max_results: int = 5, db_path: str = None):
    """Search Google Scholar for papers related to a topic."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(
                "https://scholar.google.com/scholar",
                params={"q": title, "num": max_results, "hl": "en"},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
            resp.raise_for_status()

        papers_found = _parse_google_scholar_html(resp.text)

        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for p in papers_found[:max_results]:
            brief = await _generate_brief(p["title"], p.get("abstract", ""))
            if _save_paper(conn, topic_id, p["title"], p["url"], brief, sub_folder_id, "google_scholar", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] Google Scholar: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] Google Scholar search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


def _parse_google_scholar_html(html_text):
    papers = []
    # Parse Google Scholar result blocks
    # Each result is in a <div class="gs_ri"> with <h3 class="gs_rt">
    title_pattern = r'<h3[^>]*class="gs_rt"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
    snippet_pattern = r'<div[^>]*class="gs_rs"[^>]*>(.*?)</div>'

    titles = re.findall(title_pattern, html_text, re.DOTALL)
    snippets = re.findall(snippet_pattern, html_text, re.DOTALL)

    for i, (url, raw_title) in enumerate(titles):
        clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
        abstract = ""
        if i < len(snippets):
            abstract = re.sub(r'<[^>]+>', '', snippets[i]).strip()
        if clean_title:
            papers.append({"title": clean_title, "url": url, "abstract": abstract})
    return papers


# ═══════════════════════════════════════════
#  CNKI Search (中国知网)
# ═══════════════════════════════════════════
async def search_cnki_for_topic(topic_id: str, title: str, max_results: int = 5, db_path: str = None):
    """Search CNKI for papers related to a topic."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            # CNKI public search endpoint
            resp = await client.get(
                "https://kns.cnki.net/kns8s/brief/grid",
                params={
                    "txt_1_sel": "SU",  # Subject
                    "txt_1_value1": title,
                    "currentid": "txt_1_value1",
                    "pageNum": 1,
                    "pageSize": max_results,
                    "sorttype": "FT",  # Sort by publication time
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
    # CNKI results contain links like /kcms2/article/abstract?v=...
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
#  HeinOnline Search
# ═══════════════════════════════════════════
async def search_heinonline_for_topic(topic_id: str, title: str, max_results: int = 5, db_path: str = None):
    """Search HeinOnline for papers related to a topic."""
    import httpx
    import sqlite3

    target_db = db_path or os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(target_db)
    conn.row_factory = sqlite3.Row

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(
                "https://heinonline.org/HOL/OneBoxCitation",
                params={"cit_string": title, "collection": "journals", "max": max_results},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }
            )
            resp.raise_for_status()

        papers_found = _parse_heinonline_html(resp.text)

        sub_folder_id, sub_folder_name = _get_or_create_folders(conn, topic_id, title)
        now = datetime.utcnow().isoformat()
        imported_count = 0

        for p in papers_found[:max_results]:
            brief = await _generate_brief(p["title"], p.get("abstract", ""))
            if _save_paper(conn, topic_id, p["title"], p["url"], brief, sub_folder_id, "heinonline", now):
                imported_count += 1

        conn.execute("UPDATE topics SET last_checked_at=? WHERE id=?", (now, topic_id))
        conn.commit()
        print(f"[tracker] HeinOnline: imported {imported_count} papers for '{title}'")

    except Exception as exc:
        print(f"[tracker] HeinOnline search error for topic {topic_id}: {exc}")
    finally:
        conn.close()


def _parse_heinonline_html(html_text):
    papers = []
    # Parse HeinOnline citation results
    pattern = r'<a[^>]*href="(https?://heinonline\.org/HOL/[^"]+)"[^>]*>(.*?)</a>'
    for match in re.finditer(pattern, html_text, re.DOTALL):
        url = match.group(1)
        raw_title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
        if raw_title and len(raw_title) > 3:
            papers.append({"title": raw_title, "url": url, "abstract": ""})
    return papers


# ═══════════════════════════════════════════
#  Unified dispatcher — search all selected sources
# ═══════════════════════════════════════════
SOURCE_SEARCH_MAP = {
    "arxiv": search_arxiv_for_topic,
    "ssrn": search_ssrn_for_topic,
    "google_scholar": search_google_scholar_for_topic,
    "cnki": search_cnki_for_topic,
    "heinonline": search_heinonline_for_topic,
}


async def search_topic_all_sources(topic_id: str, title: str, sources: List[str] = None, db_path: str = None):
    """Search all selected sources for a topic in parallel."""
    if not sources:
        sources = ["arxiv"]

    tasks = []
    for source in sources:
        fn = SOURCE_SEARCH_MAP.get(source)
        if fn:
            tasks.append(fn(topic_id, title, db_path=db_path))

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


