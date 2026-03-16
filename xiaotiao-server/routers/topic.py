import os
import random
from fastapi import APIRouter, Depends, HTTPException
from schemas import TopicGenerateRequest, TopicGenerateResponse
from services.llm import call_claude_json
from services.srs import SRSEngine
from db.database import get_db

router = APIRouter(prefix="/topic", tags=["话题生成"])

def load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@router.post(
    "/generate",
    response_model=TopicGenerateResponse,
    summary="生成话题文章",
    description="根据指定主题、领域与难度生成学习文章，并返回新词与术语。",
)
async def generate_topic(req: TopicGenerateRequest, db = Depends(get_db)):
    system_prompt = load_prompt("topic_generate.txt")

    # Hook into SRS Engine to get target words dynamically
    srs = SRSEngine(db)
    user_db_words = req.db_words
    
    if not user_db_words and req.db_word_count > 0:
        # If frontend didn't pass explicit words, fetch from SRS pipeline
        srs_words = srs.select_words_for_topic(limit=req.db_word_count)
        user_db_words = srs_words
    
    user_prompt = f"""
Please generate an article based on the following specs:
- Topics: {', '.join(req.topics) if req.topics else 'General knowledge'}
- Domains: {', '.join(req.domains) if req.domains else 'General'}
- Level: {req.level}
- Target Length: ~{req.article_length} words
- Style: {req.article_style_id}
- Required DB Words (MUST INCLUDE): {', '.join(user_db_words) if user_db_words else 'None'}
- Number of new words to introduce: {req.new_word_count}
    """

    try:
        data = await call_claude_json(system_prompt, user_prompt, max_tokens=int(req.article_length)*3 + 1000)
    except Exception as e:
        # Fallback to length heuristics
        data = await call_claude_json(system_prompt, user_prompt, max_tokens=3000)

    # Normalize model output to TopicGenerateResponse schema.
    if isinstance(data, dict):
        data.setdefault("result_text", "")
        data.setdefault("db_words_used", [])
        data.setdefault("new_words", [])
        data.setdefault("terms", [])
        data.setdefault("notes", [])
        data.setdefault("confidence_hint", "medium")

    # Simple validation against schema
    try:
        response = TopicGenerateResponse(**data)
        
        # After successful generation, simulate a review exposure
        srs.process_article_exposure("article_runtime_id", response.db_words_used)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 返回数据格式错误：{e}。原始数据：{data}")
