"""主题追踪路由：话题追踪与 ArXiv 论文发现。"""

import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

from db.database import get_db
from services.tracker_service import (
    list_topics,
    create_topic,
    delete_topic,
    search_arxiv_for_topic,
)

router = APIRouter(prefix="/topics", tags=["主题追踪"])


class TopicCreate(BaseModel):
    title: str
    check_frequency: str = "daily"
    sources: List[str] = ["arxiv"]


# ── Topics CRUD ───────────────────────────────

@router.get(
    "",
    summary="获取追踪主题",
    description="返回当前所有追踪主题列表。",
)
def list_topics_route(db=Depends(get_db)):
    return list_topics(db)


@router.post(
    "",
    summary="创建追踪主题",
    description="新增一个主题并设置检查频率。",
)
def create_topic_route(body: TopicCreate, db=Depends(get_db)):
    return create_topic(db, body.title, body.check_frequency, body.sources)


@router.delete(
    "/{topic_id}",
    summary="删除追踪主题",
    description="删除指定追踪主题。",
)
def delete_topic_route(topic_id: str, db=Depends(get_db)):
    return delete_topic(db, topic_id)


@router.post(
    "/{topic_id}/check-now",
    summary="立即检查",
    description="立即触发该主题的论文检索。",
)
async def check_now(topic_id: str, background_tasks: BackgroundTasks, db=Depends(get_db)):
    row = db.execute("SELECT * FROM topics WHERE id=?", (topic_id,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该主题。")

    background_tasks.add_task(
        asyncio.to_thread,
        lambda: asyncio.run(search_arxiv_for_topic(topic_id, row["title"]))
    )
    return {"status": "checking", "topic_id": topic_id}


# ── Discovered Papers ─────────────────────────

@router.get(
    "/papers",
    summary="获取发现论文",
    description="获取主题追踪发现的论文列表，可按状态筛选。",
)
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


@router.post(
    "/papers/{paper_id}/import",
    summary="导入到论文库",
    description="将发现的论文导入论文库。",
)
def import_paper(paper_id: str, db=Depends(get_db)):
    tp = db.execute("SELECT * FROM topic_papers WHERE id=?", (paper_id,)).fetchone()
    if not tp:
        raise HTTPException(404, "未找到该发现论文。")

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


@router.delete(
    "/papers/{paper_id}",
    summary="忽略论文",
    description="将发现论文标记为已忽略。",
)
def ignore_paper(paper_id: str, db=Depends(get_db)):
    db.execute("UPDATE topic_papers SET status='ignored' WHERE id=?", (paper_id,))
    db.commit()
    return {"status": "ignored"}
