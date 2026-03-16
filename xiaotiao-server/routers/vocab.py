import uuid
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from db.database import get_db
from schemas_vocab import VocabItemCreate, VocabItemUpdate, VocabItemResponse, VocabStatsResponse, VocabListResponse

router = APIRouter(prefix="/vocab", tags=["vocabulary"])


def text(query: str) -> str:
    return query

@router.get("", response_model=VocabListResponse)
def get_vocab_list(
    db = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str = None,
    domain: str = None
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
            "is_mastered": bool(r['is_mastered'])
        })

    import math
    return {
        "items": items,
        "total_count": total_count,
        "page": page,
        "total_pages": math.ceil(total_count / limit) if total_count > 0 else 0
    }

@router.post("", response_model=VocabItemResponse)
def create_vocab(item: VocabItemCreate, db = Depends(get_db)):
    # Check if exists
    existing = db.execute(text("SELECT id FROM vocabulary_items WHERE word = :word"), {"word": item.word.lower()}).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Word already exists in database")
        
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
        INSERT INTO vocabulary_srs_states (id, vocab_id, traversal_count, ease_factor, interval_days, next_review_date, is_mastered)
        VALUES (:id, :vocab_id, 0, 2.5, 1, :next_review, 0)
    """), {
        "id": srs_id,
        "vocab_id": new_id,
        "next_review": now_str # Due today
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

@router.put("/{vocab_id}", response_model=dict)
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
        raise HTTPException(status_code=404, detail="Vocab not found")
    db.commit()
    
    return {"status": "ok"}

@router.delete("/{vocab_id}")
def delete_vocab(vocab_id: str, db = Depends(get_db)):
    res = db.execute(text("DELETE FROM vocabulary_items WHERE id = :id"), {"id": vocab_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Vocab not found")
    db.commit()
    return {"status": "ok"}

@router.get("/stats", response_model=VocabStatsResponse)
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
    
    return {
        "total": total or 0,
        "active": active or 0,
        "mastered": srs_stats[0] if srs_stats and srs_stats[0] else 0,
        "need_review_today": srs_stats[1] if srs_stats and srs_stats[1] else 0
    }
