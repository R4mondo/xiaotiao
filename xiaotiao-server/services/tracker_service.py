"""Tracker service — topic persistence and ArXiv discovery."""

import asyncio
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

from services.llm import call_claude_json


def list_topics(db):
    rows = db.execute("SELECT * FROM topics ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def create_topic(db, title: str, check_frequency: str):
    topic_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    db.execute(
        "INSERT INTO topics (id, title, check_frequency, created_at) VALUES (?, ?, ?, ?)",
        (topic_id, title, check_frequency, now),
    )
    db.commit()
    return {"id": topic_id, "title": title, "check_frequency": check_frequency, "created_at": now}


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


async def search_arxiv_for_topic(topic_id: str, title: str, max_results: int = 5):
    """Search ArXiv for papers related to a topic and save results."""
    import httpx
    import sqlite3

    db_path = os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(db_path)
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

            existing = conn.execute(
                "SELECT id FROM topic_papers WHERE topic_id=? AND url=?",
                (topic_id, entry_url),
            ).fetchone()
            if existing:
                continue

            brief = await _generate_brief(entry_title, summary)
            tp_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO topic_papers (id, topic_id, title, url, brief, status, discovered_at)
                   VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
                (tp_id, topic_id, entry_title, entry_url, brief, datetime.utcnow().isoformat()),
            )

        conn.execute(
            "UPDATE topics SET last_checked_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), topic_id),
        )
        conn.commit()

    except Exception as exc:
        print(f"[tracker] ArXiv search error for topic {topic_id}: {exc}")
    finally:
        conn.close()
