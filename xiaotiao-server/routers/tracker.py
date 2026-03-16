"""Tracker router — topic tracking and paper discovery via ArXiv."""

import os
import uuid
import json
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from db.database import get_db
from services.llm import call_claude_json

router = APIRouter(prefix="/api/v1/topics", tags=["tracker"])


class TopicCreate(BaseModel):
    title: str
    check_frequency: str = "daily"


# ── Topics CRUD ───────────────────────────────

@router.get("")
def list_topics(db=Depends(get_db)):
    rows = db.execute("SELECT * FROM topics ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


@router.post("")
def create_topic(body: TopicCreate, db=Depends(get_db)):
    topic_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    db.execute(
        "INSERT INTO topics (id, title, check_frequency, created_at) VALUES (?, ?, ?, ?)",
        (topic_id, body.title, body.check_frequency, now)
    )
    db.commit()
    return {"id": topic_id, "title": body.title, "check_frequency": body.check_frequency, "created_at": now}


@router.delete("/{topic_id}")
def delete_topic(topic_id: str, db=Depends(get_db)):
    db.execute("DELETE FROM topics WHERE id=?", (topic_id,))
    db.commit()
    return {"status": "deleted"}


@router.post("/{topic_id}/check-now")
async def check_now(topic_id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    row = db.execute("SELECT * FROM topics WHERE id=?", (topic_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Topic not found")

    background_tasks.add_task(
        asyncio.to_thread,
        lambda: asyncio.run(_search_arxiv_for_topic(topic_id, row["title"]))
    )
    return {"status": "checking", "topic_id": topic_id}


# ── Discovered Papers ─────────────────────────

@router.get("/papers")
def list_discovered_papers(status: Optional[str] = None, db=Depends(get_db)):
    if status:
        rows = db.execute(
            """SELECT tp.*, t.title as topic_title
               FROM topic_papers tp
               JOIN topics t ON t.id = tp.topic_id
               WHERE tp.status = ?
               ORDER BY tp.discovered_at DESC""",
            (status,)
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT tp.*, t.title as topic_title
               FROM topic_papers tp
               JOIN topics t ON t.id = tp.topic_id
               ORDER BY tp.discovered_at DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("/papers/{paper_id}/import")
def import_paper(paper_id: str, db=Depends(get_db)):
    tp = db.execute("SELECT * FROM topic_papers WHERE id=?", (paper_id,)).fetchone()
    if not tp:
        raise HTTPException(404, "Discovered paper not found")

    # Create in main papers table
    new_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Check if URL already exists in papers
    if tp["url"]:
        existing = db.execute("SELECT id FROM papers WHERE url=?", (tp["url"],)).fetchone()
        if existing:
            db.execute("UPDATE topic_papers SET status='done' WHERE id=?", (paper_id,))
            db.commit()
            return {"id": existing["id"], "duplicate": True}

    db.execute(
        """INSERT INTO papers (id, title, url, source, status, created_at, updated_at)
           VALUES (?, ?, ?, 'arxiv', 'pending', ?, ?)""",
        (new_id, tp["title"], tp["url"], now, now)
    )
    db.execute("UPDATE topic_papers SET status='done' WHERE id=?", (paper_id,))
    db.commit()
    return {"id": new_id, "title": tp["title"], "duplicate": False}


@router.delete("/papers/{paper_id}")
def ignore_paper(paper_id: str, db=Depends(get_db)):
    db.execute("UPDATE topic_papers SET status='ignored' WHERE id=?", (paper_id,))
    db.commit()
    return {"status": "ignored"}


# ── Background Search Logic ──────────────────

async def _search_arxiv_for_topic(topic_id: str, title: str):
    """Search ArXiv for papers related to a topic and save results."""
    import httpx
    import sqlite3

    db_path = os.getenv("DB_PATH", "./db/xiaotiao.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        # Clean the query for ArXiv search
        query = title.replace(" ", "+")
        api_url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results=5&sortBy=submittedDate&sortOrder=descending"

        async with httpx.AsyncClient(timeout=30) as client:
            await asyncio.sleep(3)  # Respect ArXiv rate limits
            resp = await client.get(api_url)
            resp.raise_for_status()

        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        root = ET.fromstring(resp.text)

        for entry in root.findall('atom:entry', ns):
            entry_title = entry.findtext('atom:title', '', ns).strip().replace('\n', ' ')
            summary = entry.findtext('atom:summary', '', ns).strip()

            # Get the abstract page URL
            entry_url = None
            for link in entry.findall('atom:link', ns):
                if link.get('type') == 'text/html' or (not link.get('title') and link.get('rel') == 'alternate'):
                    entry_url = link.get('href')
                    break
            if not entry_url:
                entry_id = entry.findtext('atom:id', '', ns)
                entry_url = entry_id

            # Check if already discovered
            existing = conn.execute(
                "SELECT id FROM topic_papers WHERE topic_id=? AND url=?",
                (topic_id, entry_url)
            ).fetchone()
            if existing:
                continue

            tp_id = str(uuid.uuid4())
            # Use first 200 chars of summary as brief
            brief = summary[:200] + "..." if len(summary) > 200 else summary

            conn.execute(
                """INSERT INTO topic_papers (id, topic_id, title, url, brief, status, discovered_at)
                   VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
                (tp_id, topic_id, entry_title, entry_url, brief, datetime.utcnow().isoformat())
            )

        # Update last checked time
        conn.execute(
            "UPDATE topics SET last_checked_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), topic_id)
        )
        conn.commit()

    except Exception as e:
        print(f"[tracker] ArXiv search error for topic {topic_id}: {e}")
    finally:
        conn.close()
