"""Tracker router — topic tracking and paper discovery via ArXiv."""

import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from db.database import get_db
from services.tracker_service import (
    list_topics,
    create_topic,
    delete_topic,
    search_arxiv_for_topic,
)

router = APIRouter(prefix="/topics", tags=["tracker"])


class TopicCreate(BaseModel):
    title: str
    check_frequency: str = "daily"


# ── Topics CRUD ───────────────────────────────

@router.get("")
def list_topics_route(db=Depends(get_db)):
    return list_topics(db)


@router.post("")
def create_topic_route(body: TopicCreate, db=Depends(get_db)):
    return create_topic(db, body.title, body.check_frequency)


@router.delete("/{topic_id}")
def delete_topic_route(topic_id: str, db=Depends(get_db)):
    return delete_topic(db, topic_id)


@router.post("/{topic_id}/check-now")
async def check_now(topic_id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    row = db.execute("SELECT * FROM topics WHERE id=?", (topic_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Topic not found")

    background_tasks.add_task(
        asyncio.to_thread,
        lambda: asyncio.run(search_arxiv_for_topic(topic_id, row["title"]))
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
