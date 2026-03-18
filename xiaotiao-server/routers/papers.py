"""论文模块路由：增删改查、AI 解读、对话、PDF 管理。"""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List

from db.database import get_db
import sqlite3 as _sqlite3
from services.llm import call_claude_json, call_claude_stream
from services.paper_service import (
    process_paper_url,
    process_paper_pdf,
    process_paper_docx,
    get_paper_text,
    UPLOAD_DIR,
)

router = APIRouter(prefix="/papers", tags=["论文库"])


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

class InsightRequest(BaseModel):
    text: Optional[str] = None

class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None

class FolderRename(BaseModel):
    name: str

class MovePaper(BaseModel):
    folder_id: Optional[str] = None

class ReadingProgressUpdate(BaseModel):
    pages_read: int
    total_pages: int


# ── Paper CRUD ────────────────────────────────

@router.get(
    "",
    summary="获取论文列表",
    description="分页获取论文列表，支持收藏与合集过滤。",
)
def list_papers(
    page: int = 1,
    limit: int = 20,
    collection_id: Optional[str] = None,
    folder_id: Optional[str] = None,
    favorites_only: bool = False,
    root_only: bool = False,
    db=Depends(get_db)
):
    offset = (page - 1) * limit

    if folder_id:
        rows = db.execute(
            "SELECT * FROM papers WHERE folder_id=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (folder_id, limit, offset)
        ).fetchall()
        total = db.execute("SELECT COUNT(*) FROM papers WHERE folder_id=?", (folder_id,)).fetchone()[0]
    elif collection_id:
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
    elif root_only:
        rows = db.execute(
            "SELECT * FROM papers WHERE folder_id IS NULL ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = db.execute("SELECT COUNT(*) FROM papers WHERE folder_id IS NULL").fetchone()[0]
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


@router.post(
    "/batch-url",
    summary="批量导入论文链接",
    description="批量提交 ArXiv/URL 并异步抓取元数据。",
)
async def batch_import_urls(body: BatchUrlRequest, background_tasks: BackgroundTasks, request: Request, db=Depends(get_db)):
    created = []
    db_path = request.state.db_path if hasattr(request, "state") else None
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
        background_tasks.add_task(process_paper_url, paper_id, url, db_path)
        created.append({"id": paper_id, "url": url, "duplicate": False})

    return {"papers": created}


@router.post(
    "/upload-pdf",
    summary="上传论文文件",
    description="上传单个 PDF 或 Word 文档并创建论文记录。",
)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    filename_lower = (file.filename or "").lower()
    is_pdf = filename_lower.endswith(".pdf")
    is_docx = filename_lower.endswith(".docx")
    if not (is_pdf or is_docx):
        raise HTTPException(400, "仅支持 PDF 或 Word（.docx）文件。")

    paper_id = str(uuid.uuid4())
    ext = ".pdf" if is_pdf else ".docx"
    filename = f"{paper_id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "文件过大（最大 50MB）。")

    with open(filepath, "wb") as f:
        f.write(content)

    now = datetime.utcnow().isoformat()
    if is_pdf:
        db.execute(
            """INSERT INTO papers (id, title, source, status, pdf_path, created_at, updated_at)
               VALUES (?, ?, 'upload', 'pending', ?, ?, ?)""",
            (paper_id, file.filename or "Uploaded PDF", filepath, now, now)
        )
    else:
        db.execute(
            """INSERT INTO papers (id, title, source, status, docx_path, created_at, updated_at)
               VALUES (?, ?, 'upload', 'pending', ?, ?, ?)""",
            (paper_id, file.filename or "Uploaded Word", filepath, now, now)
        )
    db.commit()

    db_path = request.state.db_path if hasattr(request, "state") else None
    if is_pdf:
        background_tasks.add_task(process_paper_pdf, paper_id, filepath, db_path)
    else:
        background_tasks.add_task(process_paper_docx, paper_id, filepath, db_path)
    return {"id": paper_id, "filename": file.filename, "type": "pdf" if is_pdf else "docx"}


@router.get(
    "/stats",
    summary="论文统计",
    description="获取阅读统计数据。",
)
def get_paper_stats(db=Depends(get_db)):
    row = db.execute(
        """SELECT
            COALESCE(SUM(CASE WHEN created_at >= datetime('now','-7 days') THEN 1 ELSE 0 END), 0) AS imported_7d,
            COALESCE(SUM(CASE WHEN updated_at >= datetime('now','-7 days') THEN 1 ELSE 0 END), 0) AS viewed_7d
           FROM papers"""
    ).fetchone()

    # Reading stats
    total_papers = db.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    read_papers = db.execute("SELECT COUNT(*) FROM papers WHERE read_status='read'").fetchone()[0]
    reading_papers = db.execute("SELECT COUNT(*) FROM papers WHERE read_status='reading'").fetchone()[0]

    # Today's reading
    today_row = db.execute(
        "SELECT COALESCE(SUM(pages_read),0) as pages FROM reading_log WHERE read_date=date('now')"
    ).fetchone()
    today_pages = int(today_row["pages"]) if today_row else 0

    # Daily history (last 90 days)
    daily_rows = db.execute(
        """SELECT read_date, SUM(pages_read) as pages
           FROM reading_log
           WHERE read_date >= date('now', '-90 days')
           GROUP BY read_date
           ORDER BY read_date"""
    ).fetchall()

    return {
        "imported_7d": int(row["imported_7d"]) if row else 0,
        "viewed_7d": int(row["viewed_7d"]) if row else 0,
        "total_papers": total_papers,
        "read_papers": read_papers,
        "reading_papers": reading_papers,
        "today_pages": today_pages,
        "completion_rate": round(read_papers / total_papers * 100, 1) if total_papers > 0 else 0,
        "daily_history": [{"date": r["read_date"], "pages": int(r["pages"])} for r in daily_rows],
    }


# ── Folder Management ──────────────────────────

@router.get(
    "/folders",
    summary="获取文件夹树",
    description="返回所有文件夹，客户端自行构建树结构。",
)
def list_folders(db=Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM paper_folders ORDER BY created_at"
    ).fetchall()
    folders = [dict(r) for r in rows]
    # Add paper count per folder
    for f in folders:
        cnt = db.execute("SELECT COUNT(*) FROM papers WHERE folder_id=?", (f["id"],)).fetchone()[0]
        f["paper_count"] = cnt
    return folders


@router.post(
    "/folders",
    summary="创建文件夹",
    description="创建新文件夹，可指定父级。",
)
def create_folder(body: FolderCreate, db=Depends(get_db)):
    folder_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    db.execute(
        "INSERT INTO paper_folders (id, name, parent_id, created_at) VALUES (?, ?, ?, ?)",
        (folder_id, body.name, body.parent_id, now)
    )
    db.commit()
    return {"id": folder_id, "name": body.name, "parent_id": body.parent_id}


@router.put(
    "/folders/{folder_id}",
    summary="重命名文件夹",
)
def rename_folder(folder_id: str, body: FolderRename, db=Depends(get_db)):
    db.execute("UPDATE paper_folders SET name=? WHERE id=?", (body.name, folder_id))
    db.commit()
    return {"id": folder_id, "name": body.name}


@router.delete(
    "/folders/{folder_id}",
    summary="删除文件夹",
    description="删除文件夹，其中论文移至根级别。",
)
def delete_folder(folder_id: str, db=Depends(get_db)):
    # Move papers to root
    db.execute("UPDATE papers SET folder_id=NULL WHERE folder_id=?", (folder_id,))
    # Move sub-folders to parent
    row = db.execute("SELECT parent_id FROM paper_folders WHERE id=?", (folder_id,)).fetchone()
    parent_id = row["parent_id"] if row else None
    db.execute("UPDATE paper_folders SET parent_id=? WHERE parent_id=?", (parent_id, folder_id))
    db.execute("DELETE FROM paper_folders WHERE id=?", (folder_id,))
    db.commit()
    return {"status": "deleted"}


@router.put(
    "/{paper_id}/folder",
    summary="移动论文到文件夹",
)
def move_paper_to_folder(paper_id: str, body: MovePaper, db=Depends(get_db)):
    db.execute(
        "UPDATE papers SET folder_id=?, updated_at=? WHERE id=?",
        (body.folder_id, datetime.utcnow().isoformat(), paper_id)
    )
    db.commit()
    return {"paper_id": paper_id, "folder_id": body.folder_id}


@router.put(
    "/{paper_id}/reading-progress",
    summary="更新阅读进度",
)
def update_reading_progress(paper_id: str, body: ReadingProgressUpdate, db=Depends(get_db)):
    row = db.execute("SELECT pages_read, total_pages FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该论文。")

    # Determine read_status
    if body.pages_read >= body.total_pages and body.total_pages > 0:
        status = "read"
    elif body.pages_read > 0:
        status = "reading"
    else:
        status = "unread"

    now = datetime.utcnow().isoformat()
    db.execute(
        "UPDATE papers SET pages_read=?, total_pages=?, read_status=?, updated_at=? WHERE id=?",
        (body.pages_read, body.total_pages, status, now, paper_id)
    )

    # Log reading activity (upsert for today)
    old_pages = int(row["pages_read"]) if row["pages_read"] else 0
    new_pages = body.pages_read - old_pages
    if new_pages > 0:
        existing = db.execute(
            "SELECT id, pages_read FROM reading_log WHERE paper_id=? AND read_date=date('now')",
            (paper_id,)
        ).fetchone()
        if existing:
            db.execute(
                "UPDATE reading_log SET pages_read=pages_read+? WHERE id=?",
                (new_pages, existing["id"])
            )
        else:
            db.execute(
                "INSERT INTO reading_log (paper_id, pages_read) VALUES (?, ?)",
                (paper_id, new_pages)
            )

    db.commit()
    return {"pages_read": body.pages_read, "total_pages": body.total_pages, "read_status": status}


@router.get(
    "/{paper_id}",
    summary="获取论文详情",
    description="获取论文信息并附带聊天记录。",
)
def get_paper(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该论文。")

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


@router.delete(
    "/{paper_id}",
    summary="删除论文",
    description="删除论文记录并清理本地 PDF 文件（如存在）。",
)
def delete_paper(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT pdf_path, docx_path FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该论文。")

    # Delete PDF file if exists
    if row["pdf_path"] and os.path.exists(row["pdf_path"]):
        os.remove(row["pdf_path"])
    if row["docx_path"] and os.path.exists(row["docx_path"]):
        os.remove(row["docx_path"])

    db.execute("DELETE FROM papers WHERE id=?", (paper_id,))
    db.commit()
    return {"status": "deleted"}


@router.post(
    "/{paper_id}/toggle-favorite",
    summary="切换收藏",
    description="切换论文收藏状态。",
)
def toggle_favorite(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT is_favorite FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该论文。")

    new_val = 0 if row["is_favorite"] else 1
    db.execute("UPDATE papers SET is_favorite=?, updated_at=? WHERE id=?",
               (new_val, datetime.utcnow().isoformat(), paper_id))
    db.commit()
    return {"is_favorite": bool(new_val)}


# ── AI Endpoints (Streaming) ─────────────────

@router.post(
    "/{paper_id}/insight",
    summary="生成论文解读",
    description="流式生成论文的结构化解读（Insight）。支持传入临时文本进行测试。",
)
async def insight_paper(paper_id: str, request: Request, body: Optional[InsightRequest] = None, db=Depends(get_db)):
    row = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该论文。")

    manual_text = ""
    if body and body.text:
        manual_text = body.text.strip()
    db_path = request.state.db_path if request and hasattr(request, "state") else None
    paper_text = manual_text or get_paper_text(paper_id, db_path)
    if not paper_text:
        raise HTTPException(400, "该论文暂无可用文本内容，请上传可复制文本的 PDF，或在前端粘贴测试文本。")

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
        async for chunk in call_claude_stream(system_prompt, f"请分析以下论文：\n\n{paper_text[:6000]}", feature_id="paper_ai"):
            full_text += chunk
            yield chunk

        # Save insight after streaming completes
        try:
            conn = _sqlite3.connect(db_path or os.getenv("DB_PATH", "./db/xiaotiao.db"))
            conn.execute("UPDATE papers SET insight=?, updated_at=? WHERE id=?",
                         (full_text, datetime.utcnow().isoformat(), paper_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[papers] Error saving insight: {e}")

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# Backward-compatible alias
@router.post(
    "/{paper_id}/explain",
    summary="生成论文解读（兼容旧接口）",
    description="与 /insight 等价，保留旧接口兼容。",
)
async def explain_paper(paper_id: str, request: Request, db=Depends(get_db)):
    return await insight_paper(paper_id, request=request, db=db)


@router.post(
    "/{paper_id}/chat",
    summary="论文对话",
    description="基于论文内容进行对话问答（流式输出）。",
)
async def chat_with_paper(paper_id: str, body: ChatRequest, request: Request, db=Depends(get_db)):
    row = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该论文。")

    db_path = request.state.db_path if hasattr(request, "state") else None
    paper_text = get_paper_text(paper_id, db_path)

    # Get chat history (create table if missing)
    try:
        history = db.execute(
            "SELECT role, content FROM paper_chats WHERE paper_id=? ORDER BY created_at",
            (paper_id,)
        ).fetchall()
    except Exception:
        db.execute("""CREATE TABLE IF NOT EXISTS paper_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            content TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        db.commit()
        history = []

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
        async for chunk in call_claude_stream(system_prompt, body.message, feature_id="paper_chat"):
            full_response += chunk
            yield chunk

        # Save assistant response
        try:
            conn = _sqlite3.connect(db_path or os.getenv("DB_PATH", "./db/xiaotiao.db"))
            conn.execute("INSERT INTO paper_chats (paper_id, role, content) VALUES (?, 'assistant', ?)",
                         (paper_id, full_response))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[papers] Error saving chat: {e}")

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post(
    "/{paper_id}/page-summary",
    summary="页面摘要",
    description="对指定 PDF 页面的文本生成摘要（流式输出）。",
)
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
            f"第 {body.page_number} 页内容：\n{body.page_text[:3000]}",
            feature_id="paper_reader",
        ):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post(
    "/{paper_id}/translate",
    summary="选中文本翻译",
    description="将选中的英文段落翻译为中文（流式输出）。",
)
async def translate_selection(paper_id: str, body: TextRequest):
    system_prompt = """你是一位专业的英中翻译机器。将以下英文学术文本翻译为准确、流畅的中文。
严格要求：
1. 只输出中文翻译结果，不要输出任何英文原文
2. 保持学术用语的准确性
3. 不要添加解释、注释、评论或任何额外内容
4. 不要提问，不要说"请问""需要我"等对话性语句
5. 直接输出翻译结果，不要有任何前缀或后缀"""

    async def generate():
        async for chunk in call_claude_stream(system_prompt, body.text[:2000], feature_id="paper_translate"):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post(
    "/{paper_id}/explain-selection",
    summary="选中文本解释",
    description="解释选中段落含义，包含翻译与术语解释（流式输出）。",
)
async def explain_selection(paper_id: str, body: TextRequest):
    system_prompt = """你是一位学术论文阅读助手。请解释以下学术文本的含义。
包括：
1. 中文翻译
2. 术语解释
3. 在论文语境中的含义
用中文回答，简洁明了。"""

    async def generate():
        async for chunk in call_claude_stream(system_prompt, body.text[:2000], feature_id="paper_reader"):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@router.post(
    "/{paper_id}/summarize-selection",
    summary="选中文本摘要",
    description="对选中文本生成简短摘要（流式输出）。",
)
async def summarize_selection(paper_id: str, body: TextRequest):
    system_prompt = """你是一位学术论文摘要生成器。对以下选中的学术文本内容做简要的中文摘要分析。
严格要求：
1. 用中文输出 50-120 字的摘要
2. 解释这段文字在论文中的作用和含义
3. 提取关键信息和核心观点
4. 如果是英文内容，先理解含义再做中文摘要
5. 直接输出摘要内容，不要提问，不要有对话性语句
6. 不要添加任何前缀后缀，如"好的""以下是""请问"等"""

    async def generate():
        async for chunk in call_claude_stream(system_prompt, body.text[:2000], feature_id="paper_glossary"):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# ── Annotations ───────────────────────────────

@router.get(
    "/{paper_id}/annotations",
    summary="获取批注列表",
    description="获取论文的全部批注记录。",
)
def list_annotations(paper_id: str, db=Depends(get_db)):
    rows = db.execute(
        "SELECT * FROM paper_annotations WHERE paper_id=? ORDER BY created_at DESC",
        (paper_id,)
    ).fetchall()
    return [dict(r) for r in rows]


@router.post(
    "/{paper_id}/annotations",
    summary="新增批注",
    description="创建高亮或笔记批注。",
)
def create_annotation(paper_id: str, body: AnnotationCreate, db=Depends(get_db)):
    ann_id = str(uuid.uuid4())
    db.execute(
        """INSERT INTO paper_annotations (id, paper_id, type, selected_text, note, page_number, position)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ann_id, paper_id, body.type, body.selected_text, body.note, body.page_number, body.position)
    )
    db.commit()
    return {"id": ann_id, "type": body.type, "selected_text": body.selected_text}


@router.delete(
    "/annotations/{annotation_id}",
    summary="删除批注",
    description="删除指定批注。",
)
def delete_annotation(annotation_id: str, db=Depends(get_db)):
    db.execute("DELETE FROM paper_annotations WHERE id=?", (annotation_id,))
    db.commit()
    return {"status": "deleted"}


# ── PDF File Serving ──────────────────────────

@router.get(
    "/{paper_id}/pdf",
    summary="获取 PDF",
    description="返回本地 PDF 文件或远程 PDF 地址。",
)
def serve_pdf(paper_id: str, db=Depends(get_db)):
    row = db.execute("SELECT pdf_path, pdf_url FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该论文。")

    if row["pdf_path"] and os.path.exists(row["pdf_path"]):
        return FileResponse(row["pdf_path"], media_type="application/pdf")

    if row["pdf_url"]:
        # Try to download and cache the PDF server-side (avoids China firewall issues)
        import httpx
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "uploads", "papers")
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, f"{paper_id}.pdf")

        try:
            with httpx.Client(timeout=30, follow_redirects=True) as client:
                resp = client.get(row["pdf_url"])
                resp.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(resp.content)
            # Update database with local path
            db.execute("UPDATE papers SET pdf_path=? WHERE id=?", (local_path, paper_id))
            db.commit()
            return FileResponse(local_path, media_type="application/pdf")
        except Exception:
            # Fallback: return URL for client-side fetching
            return {"pdf_url": row["pdf_url"]}

    raise HTTPException(404, "该论文没有可用 PDF。")
