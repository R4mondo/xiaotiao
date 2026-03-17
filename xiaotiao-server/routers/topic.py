import os
from fastapi import APIRouter, Depends, HTTPException
from schemas import TopicGenerateRequest, TopicGenerateResponse
from services.prompt_engine import prompt_engine
from services.srs import SRSEngine
from db.database import get_db

router = APIRouter(prefix="/topic", tags=["话题生成"])


@router.post(
    "/generate",
    response_model=TopicGenerateResponse,
    summary="生成话题文章",
    description="根据指定主题、领域与难度生成学习文章，并返回新词与术语。",
)
async def generate_topic(req: TopicGenerateRequest, db=Depends(get_db)):
    # SRS 引擎：获取需要复习的目标词汇
    srs = SRSEngine(db)
    db_words = req.db_words
    if not db_words and req.db_word_count > 0:
        db_words = srs.select_words_for_topic(limit=req.db_word_count)

    # 从数据库读取文章风格的 prompt_modifier
    style_modifier = ""
    style_row = db.execute(
        "SELECT prompt_modifier FROM article_styles WHERE id=?",
        (req.article_style_id,),
    ).fetchone()
    if style_row:
        style_modifier = style_row["prompt_modifier"] or ""

    # 一站式调用：模板渲染 → JSON Schema 约束 → LLM → Pydantic 校验
    try:
        response = await prompt_engine.generate(
            template_name="topic_generate.j2",
            response_model=TopicGenerateResponse,
            max_tokens=int(req.article_length) * 3 + 1000,
            # 模板变量 — 前端参数直接注入
            topics=req.topics,
            domains=req.domains,
            level=req.level,
            article_length=req.article_length,
            style_modifier=style_modifier,
            db_words=db_words,
            new_word_count=req.new_word_count,
        )
    except Exception as e:
        import logging
        logging.getLogger("xiaotiao").error("Topic generate error: %s", e)
        raise HTTPException(
            status_code=500, detail="AI 生成失败，请稍后重试。"
        )

    # SRS 更新：记录词汇曝光
    srs.process_article_exposure("article_runtime_id", response.db_words_used)
    return response
