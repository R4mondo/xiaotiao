import uuid
import os
import base64
import csv
from io import BytesIO, StringIO
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from db.database import get_db
from schemas_vocab import VocabItemCreate, VocabItemUpdate, VocabItemResponse, VocabStatsResponse, VocabListResponse
from services.llm import call_claude_json, call_claude_vision_json

router = APIRouter(prefix="/vocab", tags=["生词本"])


def _load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


VOCAB_IMPORT_SYSTEM_PROMPT = """You are a vocabulary extraction assistant. Given the content from a file, extract English vocabulary words suitable for a language learner's word bank.

Return a JSON object with this structure:
{
  "words": [
    {
      "word": "jurisdiction",
      "definition_zh": "管辖权",
      "part_of_speech": "n.",
      "example_sentence": "The court has jurisdiction over this matter."
    }
  ]
}

Rules:
- Extract meaningful English words/phrases (not common words like "the", "is", "a")
- Provide accurate Chinese definitions
- Part of speech should be one of: n., v., adj., adv., prep., phrase
- If the content already has word-definition pairs, preserve them
- If the content is a word list without definitions, generate appropriate definitions
- For CSV/tabular data, detect which column contains words and which contains definitions
- Maximum 100 words per extraction
- Return ONLY the JSON object, no markdown wrappers
"""


# SQLite3 compatibility shim — passes through raw SQL strings.
# Named-parameter queries (`:param`) work directly with SQLite3 execute().
def text(query: str) -> str:
    return query

@router.get(
    "",
    response_model=VocabListResponse,
    summary="获取生词列表",
    description="分页获取生词本列表，支持搜索与领域筛选。",
)
def get_vocab_list(
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str = None,
    domain: str = None,
    filter: str = None,
    date: str = None
):
    offset = (page - 1) * limit
    
    # Build query
    base_query = """
        SELECT v.*, s.traversal_count, s.ease_factor, s.interval_days, 
               s.next_review_date, s.is_mastered
        FROM vocabulary_items v
        LEFT JOIN vocabulary_srs_states s ON v.id = s.vocab_id
        WHERE 1=1
    """
    count_query = "SELECT count(1) FROM vocabulary_items v WHERE 1=1"
    
    params = {}
    if search:
        base_query += " AND v.word LIKE :search"
        count_query += " AND v.word LIKE :search"
        params['search'] = f"%{search}%"
    if domain:
        base_query += " AND v.domain = :domain"
        count_query += " AND v.domain = :domain"
        params['domain'] = domain

    # Time-based and status filters
    if filter == 'today':
        target_date = date or datetime.now().strftime('%Y-%m-%d')
        base_query += " AND date(v.created_at) = :target_date"
        count_query += " AND date(v.created_at) = :target_date"
        params['target_date'] = target_date
    elif filter == 'month':
        target_month = date or datetime.now().strftime('%Y-%m')
        base_query += " AND strftime('%Y-%m', v.created_at) = :target_month"
        count_query += " AND strftime('%Y-%m', v.created_at) = :target_month"
        params['target_month'] = target_month
    elif filter == 'year':
        target_year = date or datetime.now().strftime('%Y')
        base_query += " AND strftime('%Y', v.created_at) = :target_year"
        count_query += " AND strftime('%Y', v.created_at) = :target_year"
        params['target_year'] = target_year
    elif filter == 'mastered':
        base_query += " AND s.is_mastered = 1"
        count_query = count_query.replace("FROM vocabulary_items v WHERE", "FROM vocabulary_items v LEFT JOIN vocabulary_srs_states s ON v.id = s.vocab_id WHERE") + " AND s.is_mastered = 1"
    elif filter == 'unmastered':
        base_query += " AND (s.is_mastered = 0 OR s.is_mastered IS NULL)"
        count_query = count_query.replace("FROM vocabulary_items v WHERE", "FROM vocabulary_items v LEFT JOIN vocabulary_srs_states s ON v.id = s.vocab_id WHERE") + " AND (s.is_mastered = 0 OR s.is_mastered IS NULL)"
    elif filter == 'easily_forgotten':
        base_query += " AND v.is_easily_forgotten = 1"
        count_query += " AND v.is_easily_forgotten = 1"

    base_query += " ORDER BY v.created_at DESC LIMIT :limit OFFSET :offset"
    params['limit'] = limit
    params['offset'] = offset

    total_row = db.execute(text(count_query), params).fetchone()
    total_count = int(total_row[0]) if total_row else 0
    
    rows = db.execute(text(base_query), params).fetchall()
    
    items = []
    for r in rows:
        next_rev = None
        if r['next_review_date']:
            try:
                next_rev = datetime.fromisoformat(r['next_review_date'])
            except:
                pass
                
        items.append({
            "id": r['id'],
            "word": r['word'],
            "definition_zh": r['definition_zh'],
            "part_of_speech": r['part_of_speech'],
            "domain": r['domain'],
            "source": r['source'],
            "example_sentence": r['example_sentence'],
            "is_active": bool(r['is_active']),
            "created_at": datetime.fromisoformat(r['created_at']) if r['created_at'] else datetime.now(),
            "traversal_count": r['traversal_count'] or 0,
            "ease_factor": r['ease_factor'] or 2.5,
            "interval_days": r['interval_days'] or 1,
            "next_review_date": next_rev,
            "is_mastered": bool(r['is_mastered']),
            "duplicate_count": r['duplicate_count'] if 'duplicate_count' in r.keys() else 0,
            "is_easily_forgotten": bool(r['is_easily_forgotten']) if 'is_easily_forgotten' in r.keys() else False,
        })

    import math
    return {
        "items": items,
        "total_count": total_count,
        "page": page,
        "total_pages": math.ceil(total_count / limit) if total_count > 0 else 0
    }

@router.post(
    "",
    response_model=VocabItemResponse,
    summary="新增生词",
    description="创建一个新的生词条目并初始化记忆曲线状态。",
)
def create_vocab(item: VocabItemCreate, db = Depends(get_db)):
    # Check if exists — if duplicate, mark as 易忘
    existing = db.execute(text("SELECT id, duplicate_count FROM vocabulary_items WHERE word = :word"), {"word": item.word.lower()}).fetchone()
    if existing:
        new_count = (existing['duplicate_count'] or 0) + 1
        db.execute(text("""
            UPDATE vocabulary_items
            SET duplicate_count = :count, is_easily_forgotten = 1
            WHERE id = :id
        """), {"count": new_count, "id": existing['id']})
        # Increase mastery threshold and reset mastered status
        db.execute(text("""
            UPDATE vocabulary_srs_states
            SET mastery_threshold = mastery_threshold + 2,
                is_mastered = 0,
                next_review_date = :now
            WHERE vocab_id = :vid
        """), {"vid": existing['id'], "now": datetime.now().isoformat()})
        db.commit()
        return {
            "id": existing['id'],
            "word": item.word.lower(),
            "definition_zh": item.definition_zh,
            "part_of_speech": item.part_of_speech,
            "domain": item.domain,
            "source": item.source,
            "example_sentence": item.example_sentence,
            "is_active": True,
            "created_at": datetime.now(),
            "traversal_count": 0,
            "ease_factor": 2.5,
            "interval_days": 1,
            "next_review_date": datetime.now(),
            "is_mastered": False,
            "duplicate": True,
            "duplicate_count": new_count,
        }

    new_id = str(uuid.uuid4())
    now_str = datetime.now().isoformat()
    
    # 1. Insert vocab
    db.execute(text("""
        INSERT INTO vocabulary_items (id, word, definition_zh, part_of_speech, domain, source, example_sentence)
        VALUES (:id, :word, :definition_zh, :part_of_speech, :domain, :source, :example_sentence)
    """), {
        "id": new_id,
        "word": item.word.lower(),
        "definition_zh": item.definition_zh,
        "part_of_speech": item.part_of_speech,
        "domain": item.domain,
        "source": item.source,
        "example_sentence": item.example_sentence
    })
    
    # 2. Insert SRS state
    srs_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO vocabulary_srs_states (id, vocab_id, traversal_count, ease_factor, interval_days, next_review_date, is_mastered, mastery_threshold)
        VALUES (:id, :vocab_id, 0, 2.5, 1, :next_review, 0, 3)
    """), {
        "id": srs_id,
        "vocab_id": new_id,
        "next_review": now_str
    })
    
    db.commit()
    
    return {
        "id": new_id,
        "word": item.word.lower(),
        "definition_zh": item.definition_zh,
        "part_of_speech": item.part_of_speech,
        "domain": item.domain,
        "source": item.source,
        "example_sentence": item.example_sentence,
        "is_active": True,
        "created_at": datetime.now(),
        "traversal_count": 0,
        "ease_factor": 2.5,
        "interval_days": 1,
        "next_review_date": datetime.now(),
        "is_mastered": False
    }

@router.put(
    "/{vocab_id}",
    response_model=dict,
    summary="更新生词",
    description="更新生词的释义、词性、领域、例句或激活状态。",
)
def update_vocab(vocab_id: str, item: VocabItemUpdate, db = Depends(get_db)):
    updates = []
    params = {"id": vocab_id}
    
    if item.definition_zh is not None:
        updates.append("definition_zh = :def")
        params["def"] = item.definition_zh
    if item.part_of_speech is not None:
        updates.append("part_of_speech = :pos")
        params["pos"] = item.part_of_speech
    if item.domain is not None:
        updates.append("domain = :domain")
        params["domain"] = item.domain
    if item.example_sentence is not None:
        updates.append("example_sentence = :ex")
        params["ex"] = item.example_sentence
    if item.is_active is not None:
        updates.append("is_active = :active")
        params["active"] = 1 if item.is_active else 0
        
    if not updates:
        return {"status": "ok"}
        
    query = f"UPDATE vocabulary_items SET {', '.join(updates)} WHERE id = :id"
    res = db.execute(text(query), params)
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="未找到该生词。")
    db.commit()
    
    return {"status": "ok"}

@router.delete(
    "/{vocab_id}",
    summary="删除生词",
    description="从生词本中移除指定生词。",
)
def delete_vocab(vocab_id: str, db = Depends(get_db)):
    res = db.execute(text("DELETE FROM vocabulary_items WHERE id = :id"), {"id": vocab_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="未找到该生词。")
    db.commit()
    return {"status": "ok"}


@router.put(
    "/batch-mastery",
    summary="批量切换掌握状态",
    description="批量标记或取消标记多个生词为已掌握。",
)
def batch_toggle_mastery(body: dict, db = Depends(get_db)):
    ids = body.get("ids", [])
    mastered = body.get("is_mastered", True)
    if not ids:
        raise HTTPException(status_code=400, detail="请提供词汇ID列表。")
    updated = 0
    for vid in ids:
        srs = db.execute(text("SELECT id FROM vocabulary_srs_states WHERE vocab_id = :vid"), {"vid": vid}).fetchone()
        if srs:
            db.execute(text("UPDATE vocabulary_srs_states SET is_mastered = :m WHERE vocab_id = :vid"),
                       {"m": 1 if mastered else 0, "vid": vid})
        else:
            srs_id = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO vocabulary_srs_states (id, vocab_id, traversal_count, ease_factor, interval_days, next_review_date, is_mastered)
                VALUES (:id, :vid, 0, 2.5, 1, :now, :m)
            """), {"id": srs_id, "vid": vid, "now": datetime.now().isoformat(), "m": 1 if mastered else 0})
        updated += 1
    db.commit()
    return {"status": "ok", "updated": updated, "is_mastered": mastered}


@router.put(
    "/{vocab_id}/mastery",
    summary="切换掌握状态",
    description="标记或取消标记某生词为已掌握。",
)
def toggle_mastery(vocab_id: str, body: dict, db = Depends(get_db)):
    mastered = body.get("is_mastered", False)
    # Check if SRS state exists
    srs = db.execute(text("SELECT id FROM vocabulary_srs_states WHERE vocab_id = :vid"), {"vid": vocab_id}).fetchone()
    if srs:
        db.execute(text("""
            UPDATE vocabulary_srs_states SET is_mastered = :m WHERE vocab_id = :vid
        """), {"m": 1 if mastered else 0, "vid": vocab_id})
    else:
        srs_id = str(uuid.uuid4())
        db.execute(text("""
            INSERT INTO vocabulary_srs_states (id, vocab_id, traversal_count, ease_factor, interval_days, next_review_date, is_mastered)
            VALUES (:id, :vid, 0, 2.5, 1, :now, :m)
        """), {"id": srs_id, "vid": vocab_id, "now": datetime.now().isoformat(), "m": 1 if mastered else 0})
    db.commit()
    return {"status": "ok", "is_mastered": mastered}


CONCEPT_ANALYSIS_PROMPT = """You are a bilingual English-Chinese vocabulary expert. Given an English word or short phrase, provide a clear, educational analysis.

Return a JSON object with this structure:
{
  "word": "the word",
  "phonetic": "phonetic transcription",
  "part_of_speech": "n./v./adj./adv./phrase",
  "definition_en": "English definition",
  "definition_zh": "中文释义",
  "explanation": "Detailed Chinese explanation of the concept, including usage context and nuances (2-3 sentences)",
  "examples": [
    {"en": "Example sentence in English", "zh": "例句中文翻译"}
  ],
  "related_terms": [
    {"term": "related word", "zh": "释义"}
  ]
}

Rules:
- Keep definitions concise but informative
- Provide 2-3 example sentences
- Provide 2-4 related terms
- Explanation should be in Chinese, detailed and educational
- Return ONLY the JSON object, no markdown wrappers
"""


@router.post(
    "/concept",
    summary="概念解析",
    description="对单个英文词汇或短语进行语义解析，返回释义、例句和关联词汇。",
)
async def concept_analysis(req: dict):
    """Analyze a single English word/phrase and return educational content."""
    word = req.get("word", "").strip()
    if not word:
        raise HTTPException(status_code=400, detail="请提供要解析的词汇。")
    if len(word) > 100:
        raise HTTPException(status_code=400, detail="词汇过长。")

    try:
        data = await call_claude_json(
            CONCEPT_ANALYSIS_PROMPT,
            f"Please analyze this English word/phrase: {word}",
            max_tokens=2000,
            feature_id="concept_analysis",
        )
        return data
    except Exception as e:
        import logging
        logging.getLogger("xiaotiao").error("Concept analysis error: %s", e)
        raise HTTPException(status_code=500, detail=f"AI 解析失败：{str(e)}")

@router.post(
    "/import-file",
    summary="导入词汇文件",
    description="上传文件（txt/md/csv/xlsx/docx/图片）自动识别并提取词汇列表。",
)
async def import_vocab_file(
    file: UploadFile = File(...),
    domain: str = Form("general"),
):
    """Parse uploaded file and return extracted vocabulary words for preview."""
    contents = await file.read()
    filename = (file.filename or "unknown").lower()

    extracted_text = ""

    # --- Text-based files ---
    if filename.endswith((".txt", ".md")):
        try:
            extracted_text = contents.decode("utf-8")
        except UnicodeDecodeError:
            extracted_text = contents.decode("gbk", errors="ignore")

    elif filename.endswith(".csv"):
        try:
            text_content = contents.decode("utf-8")
        except UnicodeDecodeError:
            text_content = contents.decode("gbk", errors="ignore")
        try:
            reader = csv.reader(StringIO(text_content))
            rows = []
            for row in reader:
                non_empty = [cell.strip() for cell in row if cell.strip()]
                if non_empty:
                    rows.append(" | ".join(non_empty))
            extracted_text = "\n".join(rows)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解析 CSV 失败：{str(e)}")

    elif filename.endswith((".xlsx", ".xls")):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(BytesIO(contents), data_only=True)
            rows = []
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                rows.append(f"--- Sheet: {sheet_name} ---")
                for row in sheet.iter_rows(values_only=True):
                    non_empty = [str(cell).strip() for cell in row if cell is not None]
                    if non_empty:
                        rows.append(" | ".join(non_empty))
            extracted_text = "\n".join(rows)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解析 Excel 失败：{str(e)}")

    elif filename.endswith((".docx", ".doc")):
        try:
            import docx
            doc = docx.Document(BytesIO(contents))
            extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"解析 Word 文档失败：{str(e)}")

    elif filename.endswith((".png", ".jpg", ".jpeg")):
        # Use vision model for images
        base64_image = base64.b64encode(contents).decode("utf-8")
        media_type = "image/png" if filename.endswith(".png") else "image/jpeg"
        try:
            data = await call_claude_vision_json(
                system_prompt=VOCAB_IMPORT_SYSTEM_PROMPT,
                user_prompt=f"Domain focus: {domain}\n\nPlease extract all English vocabulary words visible in this image. If it's a word list, screenshot of a textbook, or vocabulary card, extract all words with their definitions.",
                base64_image=base64_image,
                media_type=media_type,
                max_tokens=4000,
                feature_id="vocab_import",
            )
            words = data.get("words", [])
            # Normalize each word entry
            result = []
            for w in words:
                result.append({
                    "word": w.get("word", ""),
                    "definition_zh": w.get("definition_zh", ""),
                    "part_of_speech": w.get("part_of_speech", "n."),
                    "example_sentence": w.get("example_sentence", ""),
                })
            return {"words": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图片识别失败：{str(e)}")
    else:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式。支持：.txt, .md, .csv, .xlsx, .xls, .docx, .doc, .png, .jpg, .jpeg",
        )

    # For text-based content, use LLM to extract words
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空。")

    truncated = extracted_text[:6000]
    user_prompt = f"Domain focus: {domain}\n\nPlease extract English vocabulary words from the following content:\n\n{truncated}"

    try:
        data = await call_claude_json(VOCAB_IMPORT_SYSTEM_PROMPT, user_prompt, max_tokens=4000, feature_id="vocab_import")
        words = data.get("words", [])
        result = []
        for w in words:
            result.append({
                "word": w.get("word", ""),
                "definition_zh": w.get("definition_zh", ""),
                "part_of_speech": w.get("part_of_speech", "n."),
                "example_sentence": w.get("example_sentence", ""),
            })
        return {"words": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 词汇提取失败：{str(e)}")


@router.post(
    "/batch",
    summary="批量导入词汇",
    description="批量添加多个词汇到生词本。",
)
def batch_create_vocab(
    items: List[VocabItemCreate],
    db=Depends(get_db),
):
    """Import multiple words at once, skipping duplicates."""
    imported = 0
    skipped = 0
    for item in items:
        existing = db.execute(
            text("SELECT id FROM vocabulary_items WHERE word = :word"),
            {"word": item.word.lower()},
        ).fetchone()
        if existing:
            skipped += 1
            continue

        new_id = str(uuid.uuid4())
        db.execute(
            text("""
                INSERT INTO vocabulary_items (id, word, definition_zh, part_of_speech, domain, source, example_sentence)
                VALUES (:id, :word, :definition_zh, :part_of_speech, :domain, :source, :example_sentence)
            """),
            {
                "id": new_id,
                "word": item.word.lower(),
                "definition_zh": item.definition_zh,
                "part_of_speech": item.part_of_speech,
                "domain": item.domain,
                "source": item.source or "file_import",
                "example_sentence": item.example_sentence,
            },
        )
        srs_id = str(uuid.uuid4())
        db.execute(
            text("""
                INSERT INTO vocabulary_srs_states (id, vocab_id, traversal_count, ease_factor, interval_days, next_review_date, is_mastered)
                VALUES (:id, :vocab_id, 0, 2.5, 1, :next_review, 0)
            """),
            {
                "id": srs_id,
                "vocab_id": new_id,
                "next_review": datetime.now().isoformat(),
            },
        )
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "total": len(items)}


@router.get(
    "/stats",
    response_model=VocabStatsResponse,
    summary="生词统计",
    description="获取生词总量、活跃数与今日需复习数量。",
)
def get_stats(db = Depends(get_db)):
    total_row = db.execute(text("SELECT count(1) FROM vocabulary_items")).fetchone()
    active_row = db.execute(text("SELECT count(1) FROM vocabulary_items WHERE is_active = 1")).fetchone()
    total = int(total_row[0]) if total_row else 0
    active = int(active_row[0]) if active_row else 0
    
    srs_stats = db.execute(text("""
        SELECT 
            SUM(CASE WHEN is_mastered = 1 THEN 1 ELSE 0 END) as mastered,
            SUM(CASE WHEN is_mastered = 0 AND next_review_date <= :now THEN 1 ELSE 0 END) as due_today
        FROM vocabulary_srs_states
    """), {"now": datetime.now().isoformat()}).fetchone()

    # Time-based counts
    today_str = datetime.now().strftime('%Y-%m-%d')
    month_str = datetime.now().strftime('%Y-%m')
    year_str = datetime.now().strftime('%Y')

    today_count = db.execute(text(
        "SELECT count(1) FROM vocabulary_items WHERE date(created_at) = :d"
    ), {"d": today_str}).fetchone()[0] or 0
    month_count = db.execute(text(
        "SELECT count(1) FROM vocabulary_items WHERE strftime('%Y-%m', created_at) = :m"
    ), {"m": month_str}).fetchone()[0] or 0
    year_count = db.execute(text(
        "SELECT count(1) FROM vocabulary_items WHERE strftime('%Y', created_at) = :y"
    ), {"y": year_str}).fetchone()[0] or 0
    easily_forgotten = db.execute(text(
        "SELECT count(1) FROM vocabulary_items WHERE is_easily_forgotten = 1"
    )).fetchone()[0] or 0
    
    return {
        "total": total or 0,
        "active": active or 0,
        "mastered": srs_stats[0] if srs_stats and srs_stats[0] else 0,
        "need_review_today": srs_stats[1] if srs_stats and srs_stats[1] else 0,
        "today_count": int(today_count),
        "month_count": int(month_count),
        "year_count": int(year_count),
        "easily_forgotten": int(easily_forgotten),
    }


@router.get(
    "/export",
    summary="导出词汇表",
    description="导出当前筛选条件下的词汇为 Word 文档。",
)
def export_vocab(
    db=Depends(get_db),
    filter: str = None,
    date: str = None,
    search: str = None,
    domain: str = None,
):
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.table import WD_TABLE_ALIGNMENT

    # Build query (reuse filter logic)
    base_query = """
        SELECT v.*, s.is_mastered, v.is_easily_forgotten
        FROM vocabulary_items v
        LEFT JOIN vocabulary_srs_states s ON v.id = s.vocab_id
        WHERE 1=1
    """
    params = {}
    if search:
        base_query += " AND v.word LIKE :search"
        params['search'] = f"%{search}%"
    if domain:
        base_query += " AND v.domain = :domain"
        params['domain'] = domain

    title_suffix = "全部生词"
    if filter == 'today':
        target_date = date or datetime.now().strftime('%Y-%m-%d')
        base_query += " AND date(v.created_at) = :target_date"
        params['target_date'] = target_date
        title_suffix = f"当日生词本 ({target_date})"
    elif filter == 'month':
        target_month = date or datetime.now().strftime('%Y-%m')
        base_query += " AND strftime('%Y-%m', v.created_at) = :target_month"
        params['target_month'] = target_month
        title_suffix = f"当月生词本 ({target_month})"
    elif filter == 'year':
        target_year = date or datetime.now().strftime('%Y')
        base_query += " AND strftime('%Y', v.created_at) = :target_year"
        params['target_year'] = target_year
        title_suffix = f"当年生词本 ({target_year})"
    elif filter == 'mastered':
        base_query += " AND s.is_mastered = 1"
        title_suffix = "已掌握词汇"
    elif filter == 'unmastered':
        base_query += " AND (s.is_mastered = 0 OR s.is_mastered IS NULL)"
        title_suffix = "未掌握词汇"
    elif filter == 'easily_forgotten':
        base_query += " AND v.is_easily_forgotten = 1"
        title_suffix = "易忘生词"

    base_query += " ORDER BY v.created_at DESC"
    rows = db.execute(text(base_query), params).fetchall()

    # Create Word document
    doc = docx.Document()
    doc.add_heading(f"生词本 — {title_suffix}", level=1)
    doc.add_paragraph(f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}　共 {len(rows)} 个词汇")

    if rows:
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        headers = ['单词', '中文释义', '词性', '专业领域', '状态']
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = h
            for p in cell.paragraphs:
                for run in p.runs:
                    run.bold = True
                    run.font.size = Pt(10)

        for r in rows:
            status = '已掌握' if r['is_mastered'] else ('易忘' if r['is_easily_forgotten'] else '学习中')
            row_cells = table.add_row().cells
            row_cells[0].text = r['word'] or ''
            row_cells[1].text = r['definition_zh'] or ''
            row_cells[2].text = r['part_of_speech'] or ''
            row_cells[3].text = r['domain'] or ''
            row_cells[4].text = status

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    # Use RFC 5987 encoding for non-ASCII filenames
    from urllib.parse import quote
    safe_name = title_suffix.replace(' ', '_')
    encoded_name = quote(f"vocab_{safe_name}.docx")

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=vocab_export.docx; filename*=UTF-8''{encoded_name}"}
    )
