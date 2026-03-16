"""Papers router — CRUD, AI insight, chat, PDF management."""

import os
import uuid
import json
import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List

from db.database import get_db
from services.llm import call_claude_json, call_claude_stream
from services.paper_service import process_paper_url, process_paper_pdf, get_paper_text, UPLOAD_DIR

router = APIRouter(prefix="/papers", tags=["papers"])


# ── Request / Response Models ─────────────────

class BatchUrlRequest(BaseModel):
    urls: List[str]

class ChatRequest(BaseModel):
    message: str

class PageSummaryRequest(BaseModel):
    page_number: int
    page_text: str

class TextRequest(BaseModel):
    text: str

class AnnotationCreate(BaseModel):
    type: str = "highlight"
    selected_text: Optional[str] = None
    note: Optional[str] = None
    page_number: Optional[int] = None
    position: Optional[str] = None


# ── Paper CRUD ────────────────────────────────

@router.get("")
def list_papers(
    page: int = 1,
    limit: int = 20,
    collection_id: Optional[str] = None,
    favorites_only: bool = False,
    db=Depends(get_db)
):
    offset = (page - 1) * limit

    if collection_id:
        rows = db.execute(
            """SELECT p.* FROM papers p
               JOIN collection_papers cp ON cp.paper_id = p.id
               WHERE cp.collection_id = ?
               ORDER BY p.created_at DESC LIMIT ? OFFSET ?""",
            (collection_id, limit, offset)
        ).fetchall()
        total = db.execute(
            "SELECT COUNT(*) FROM collection_papers WHERE collection_id=?",
            (collection_id,)
        ).fetchone()[0]
    elif favorites_only:
        rows = db.execute(
            "SELECT * FROM papers WHERE is_favorite=1 ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = db.execute("SELECT COUNT(*) FROM papers WHERE is_favorite=1").fetchone()[0]
    else:
        rows = db.execute(
            "SELECT * FROM papers ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = db.execute("SELECT COUNT(*) FROM papers").fetchone()[0]

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "total_pages": max(1, (total + limit - 1) // limit)
    }


@router.post("/batch-url")
async def batch_import_urls(body: BatchUrlRequest, background_tasks: BackgroundTasks, db=Depends(get_db)):
    created = []
    for url in body.urls:
        url = url.strip()
        if not url:
            continue
        # Check duplicate
        existing = db.execute("SELECT id FROM papers WHERE url=?", (url,)).fetchone()
        if existing:
            created.append({"id": existing["id"], "url": url, "duplicate": True})
            continue

        paper_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        db.execute(
            """INSERT INTO papers (id, title, url, source, status, created_at, updated_at)
               VALUES (?, ?, ?, 'url', 'pending', ?, ?)""",
            (paper_id, url[:100], url, now, now)
        )
        db.commit()
        background_tasks.add_task(asyncio.to_thread, lambda pid=paper_id, u=url: asyncio.run(process_paper_url(pid, u)))
        created.append({"id": paper_id, "url": url, "duplicate": False})

    return {"papers": created}


@router.post("/upload-pdf")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are accepted")

    paper_id = str(uuid.uuid4())
    filename = f"{paper_id}.pdf"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 50MB)")

    with open(filepath, "wb") as f:
        f.write(content)

    now = datetime.utcnow().isoformat()
    db.execute(
        """INSERT INTO papers (id, title, source, status, pdf_path, created_at, updated_at)
           VALUES (?, ?, 'upload', 'pending', ?, ?, ?)""",
        (paper_id, file.filename or "Uploaded PDF", filepath, now, now)
    )
    db.commit()

    background_tasks.add_task(process_paper_pdf, paper_id, filepath)
    return {"id": paper_id, "filename": file.filename}


@router.get("/stats")
def get_paper_stats(db=Depends(get_db)):
    row = db.execute(
        """SELECT
            COALESCE(SUM(CASE WHEN created_at >= datetime('now','-7 days') THEN 1 ELSE 0 END), 0) AS imported_7d,
            COALESCE(SUM(CASE WHEN updated_at >= datetime('now','-7 days') THEN 1 ELSE 0 END), 0) AS viewed_7d
           FROM papers"""
    ).fetchone()
    return {
        "imported_7d": int(row["imported_7d"]) if row else 0,
        "viewed_7d": int(row["viewed_7d"]) if row else 0,
    }


@router.get("/{paper_id}")
def get_paper(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Paper not found")

    now = datetime.utcnow().isoformat()
    db.execute("UPDATE papers SET updated_at=? WHERE id=?", (now, paper_id))
    db.commit()

    paper = dict(row)
    paper["updated_at"] = now

    # Include chat history
    chats = db.execute(
        "SELECT role, content, created_at FROM paper_chats WHERE paper_id=? ORDER BY created_at",
        (paper_id,)
    ).fetchall()
    paper["chats"] = [dict(c) for c in chats]

    return paper


@router.delete("/{paper_id}")
def delete_paper(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT pdf_path FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Paper not found")

    # Delete PDF file if exists
    if row["pdf_path"] and os.path.exists(row["pdf_path"]):
        os.remove(row["pdf_path"])

    db.execute("DELETE FROM papers WHERE id=?", (paper_id,))
    db.commit()
    return {"status": "deleted"}


@router.post("/{paper_id}/toggle-favorite")
def toggle_favorite(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT is_favorite FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Paper not found")

    new_val = 0 if row["is_favorite"] else 1
    db.execute("UPDATE papers SET is_favorite=?, updated_at=? WHERE id=?",
               (new_val, datetime.utcnow().isoformat(), paper_id))
    db.commit()
    return {"is_favorite": bool(new_val)}


# ── AI Endpoints (Streaming) ─────────────────

@router.post("/{paper_id}/insight")
async def insight_paper(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Paper not found")

    paper_text = get_paper_text(paper_id)
    if not paper_text:
        raise HTTPException(400, "No text content available for this paper")

    system_prompt = """你是一位资深学术论文分析专家。请对以下论文内容进行深入、结构化的解读分析。

请按以下结构输出（使用 Markdown 格式）：

## 原文摘要
简要概括论文的核心内容和研究目的。

## 为什么重要？
解释这项研究的学术和实际意义。

## 创新点
详细说明论文的创新之处。

## 与同类工作相比的优势
对比分析该研究相对于现有工作的优势。

## 局限性
客观指出研究的不足之处。

## 实验设计评价
分析实验方法的合理性。

## 关键概念详解
列出并解释论文中的核心概念和术语。

## 智能标签
为这篇论文生成 3-5 个分类标签。

请用中文回答，保持学术严谨性。"""

    async def generate():
        full_text = ""
        async for chunk in call_claude_stream(system_prompt, f"请分析以下论文：\n\n{paper_text[:6000]}"):
            full_text += chunk
            yield chunk

        # Save insight after streaming completes
        try:
            conn = __import__('sqlite3').connect(os.getenv("DB_PATH", "./db/xiaotiao.db"))
            conn.execute("UPDATE papers SET insight=?, updated_at=? WHERE id=?",
                         (full_text, datetime.utcnow().isoformat(), paper_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[papers] Error saving insight: {e}")

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# Backward-compatible alias
@router.post("/{paper_id}/explain")
async def explain_paper(paper_id: str, db=Depends(get_db)):
    return await insight_paper(paper_id, db)


@router.post("/{paper_id}/chat")
async def chat_with_paper(paper_id: str, body: ChatRequest, db=Depends(get_db)):
    row = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Paper not found")

    paper_text = get_paper_text(paper_id)

    # Get chat history
    history = db.execute(
        "SELECT role, content FROM paper_chats WHERE paper_id=? ORDER BY created_at",
        (paper_id,)
    ).fetchall()

    # Build context
    context_parts = [f"论文标题: {row['title']}"]
    if paper_text:
        context_parts.append(f"论文内容（摘要/正文）:\n{paper_text[:4000]}")
    if row['insight']:
        context_parts.append(f"AI 解读:\n{row['insight'][:2000]}")

    history_text = ""
    for h in history[-10:]:  # Last 10 messages
        role_label = "用户" if h["role"] == "user" else "AI"
        history_text += f"\n{role_label}: {h['content']}"

    system_prompt = f"""你是一位学术论文研究助手。基于以下论文信息回答用户的问题。

{chr(10).join(context_parts)}

{f'对话历史:{history_text}' if history_text else ''}

请用中文回答，保持准确和学术性。如果论文内容中没有相关信息，请如实说明。"""

    # Save user message
    db.execute("INSERT INTO paper_chats (paper_id, role, content) VALUES (?, 'user', ?)",
               (paper_id, body.message))
    db.commit()

    async def generate():
        full_response = ""
        async for chunk in call_claude_stream(system_prompt, body.message):
            full_response += chunk
            yield chunk

        # Save assistant response
        try:
            conn = __import__('sqlite3').connect(os.getenv("DB_PATH", "./db/xiaotiao.db"))
            conn.execute("INSERT INTO paper_chats (paper_id, role, content) VALUES (?, 'assistant', ?)",
                         (paper_id, full_response))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[papers] Error saving chat: {e}")

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post("/{paper_id}/page-summary")
async def page_summary(paper_id: str, body: PageSummaryRequest):
    system_prompt = """你是一位学术论文阅读助手。请为以下 PDF 页面内容生成简洁的中文摘要。
摘要应该：
1. 概括该页面的主要内容
2. 提取关键信息和数据
3. 使用简明的语言
控制在 100-200 字以内。"""

    async def generate():
        async for chunk in call_claude_stream(
            system_prompt,
            f"第 {body.page_number} 页内容：\n{body.page_text[:3000]}"
        ):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post("/{paper_id}/translate")
async def translate_selection(paper_id: str, body: TextRequest):
    system_prompt = "你是一位专业翻译。请将以下英文学术文本翻译为准确、流畅的中文。只输出翻译结果，不要添加解释。"

    async def generate():
        async for chunk in call_claude_stream(system_prompt, body.text[:2000]):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post("/{paper_id}/explain-selection")
async def explain_selection(paper_id: str, body: TextRequest):
    system_prompt = """你是一位学术论文阅读助手。请解释以下学术文本的含义。
包括：
1. 中文翻译
2. 术语解释
3. 在论文语境中的含义
用中文回答，简洁明了。"""

    async def generate():
        async for chunk in call_claude_stream(system_prompt, body.text[:2000]):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post("/{paper_id}/summarize-selection")
async def summarize_selection(paper_id: str, body: TextRequest):
    system_prompt = """你是一位学术论文阅读助手。请对以下选中内容做简要摘要。
要求：
1. 50-120 字
2. 聚焦核心观点与结论
3. 使用简洁中文"""

    async def generate():
        async for chunk in call_claude_stream(system_prompt, body.text[:2000]):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# ── Annotations ───────────────────────────────

@router.get("/{paper_id}/annotations")
def list_annotations(paper_id: str, db=Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM paper_annotations WHERE paper_id=? ORDER BY created_at DESC",
        (paper_id,)
    ).fetchall()
    return [dict(r) for r in rows]


@router.post("/{paper_id}/annotations")
def create_annotation(paper_id: str, body: AnnotationCreate, db=Depends(get_db)):
    ann_id = str(uuid.uuid4())
    db.execute(
        """INSERT INTO paper_annotations (id, paper_id, type, selected_text, note, page_number, position)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ann_id, paper_id, body.type, body.selected_text, body.note, body.page_number, body.position)
    )
    db.commit()
    return {"id": ann_id, "type": body.type, "selected_text": body.selected_text}


@router.delete("/annotations/{annotation_id}")
def delete_annotation(annotation_id: str, db=Depends(get_db)):
    db.execute("DELETE FROM paper_annotations WHERE id=?", (annotation_id,))
    db.commit()
    return {"status": "deleted"}


# ── PDF File Serving ──────────────────────────

@router.get("/{paper_id}/pdf")
def serve_pdf(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT pdf_path, pdf_url FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Paper not found")

    if row["pdf_path"] and os.path.exists(row["pdf_path"]):
        return FileResponse(row["pdf_path"], media_type="application/pdf")

    if row["pdf_url"]:
        # Return the URL for client-side fetching
        return {"pdf_url": row["pdf_url"]}

    raise HTTPException(404, "No PDF available for this paper")
