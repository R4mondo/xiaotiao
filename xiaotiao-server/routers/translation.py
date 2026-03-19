"""翻译 — 多风格翻译 + 历史记录"""
import os
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from sqlalchemy import text
from schemas import TranslationRequest, TranslationResponse
from services.prompt_engine import prompt_engine
from db.auth_db import get_user_profile
from db.database import get_db

router = APIRouter(prefix="/translation", tags=["翻译"])


@router.post(
    "/run",
    response_model=TranslationResponse,
    summary="文本翻译",
    description="对输入文本进行多风格翻译，支持直译、法律表达、简明表达。",
)
async def run_translation(req: TranslationRequest, request: Request, db=Depends(get_db)):
    if len(req.source_text) > 5000:
        raise HTTPException(status_code=422, detail="文本超过 5000 字符限制。")

    # V2.0: 读取用户画像，注入专业方向到翻译提示词
    user_profile = {}
    try:
        user_profile = get_user_profile(request.state.user["id"])
    except Exception:
        pass

    try:
        response = await prompt_engine.generate(
            template_name="translation.j2",
            response_model=TranslationResponse,
            max_tokens=4000,
            feature_id="translation",
            # 模板变量
            direction=req.direction,
            source_text=req.source_text,
            user_translation=req.user_translation or "",
            # V2.0: 用户画像注入
            user_specialty=user_profile.get("specialty", ""),
            user_subject_field=user_profile.get("subject_field", ""),
        )
    except Exception as e:
        import logging
        logging.getLogger("xiaotiao").error("Translation error: %s", e)
        raise HTTPException(
            status_code=500, detail="AI 翻译失败，请稍后重试。"
        )

    # V2.1: 自动保存翻译历史
    try:
        history_id = str(uuid.uuid4())
        result_data = response.model_dump() if hasattr(response, 'model_dump') else response
        db.execute(
            text("""
                INSERT INTO translation_history (id, source_text, direction, result_json, created_at)
                VALUES (:id, :src, :dir, :res, :now)
            """),
            {
                "id": history_id,
                "src": req.source_text[:2000],  # 截断防止过大
                "dir": req.direction,
                "res": json.dumps(result_data, ensure_ascii=False, default=str),
                "now": datetime.now().isoformat(),
            },
        )
        db.commit()
        # 在响应中附加 history_id（TranslationResponse 可能不包含此字段，放 header 或忽略）
    except Exception:
        pass  # 保存历史失败不影响正常响应

    return response


# ── 翻译历史 ──────────────────────────────

@router.get(
    "/history",
    summary="翻译历史列表",
)
def get_translation_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
):
    offset = (page - 1) * size
    total = db.execute(text("SELECT COUNT(*) FROM translation_history")).scalar() or 0
    rows = db.execute(
        text("SELECT * FROM translation_history ORDER BY created_at DESC LIMIT :lim OFFSET :off"),
        {"lim": size, "off": offset},
    ).fetchall()
    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": r.id,
                "source_text": r.source_text[:100] + ("..." if len(r.source_text) > 100 else ""),
                "source_text_full": r.source_text,
                "direction": r.direction,
                "created_at": r.created_at,
            }
            for r in rows
        ],
    }


@router.get(
    "/history/{history_id}",
    summary="翻译历史详情",
)
def get_translation_detail(history_id: str, db=Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM translation_history WHERE id = :id"),
        {"id": history_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="翻译记录不存在")
    result = None
    try:
        result = json.loads(row.result_json) if row.result_json else None
    except Exception:
        result = row.result_json
    return {
        "id": row.id,
        "source_text": row.source_text,
        "direction": row.direction,
        "result": result,
        "created_at": row.created_at,
    }


@router.delete(
    "/history/{history_id}",
    summary="删除翻译记录",
)
def delete_translation_history(history_id: str, db=Depends(get_db)):
    res = db.execute(text("DELETE FROM translation_history WHERE id = :id"), {"id": history_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="翻译记录不存在")
    db.commit()
    return {"status": "ok"}
