import os
from fastapi import APIRouter, HTTPException
from schemas import ArticleAnalyzeRequest, ArticleAnalyzeResponse
from services.llm import call_claude_json
from services.research_store import search_rag_chunks

router = APIRouter(prefix="/article", tags=["文章解读"])

def load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@router.post(
    "/analyze",
    response_model=ArticleAnalyzeResponse,
    summary="文章解读",
    description="对输入文本进行结构化解读，输出段落解析、术语与关键句。",
)
async def analyze_article(req: ArticleAnalyzeRequest):
    if len(req.source_text.split()) > 3500:
        raise HTTPException(status_code=422, detail="文本超过 3500 词限制。")

    system_prompt = load_prompt("article_analyze.txt")
    
    context_block = ""
    if req.grounded:
        contexts = search_rag_chunks(req.source_text, top_k=req.top_k)
        if contexts:
            context_lines = []
            for idx, item in enumerate(contexts, start=1):
                title = item.get("title") or item.get("source_id") or f"source-{idx}"
                chunk = str(item.get("chunk_text") or "").strip()
                context_lines.append(f"[{idx}] {title}\n{chunk}")
            context_block = "\n\nGrounded Context (must cite where useful):\n" + "\n\n".join(context_lines)

    user_prompt = f"""
Analysis Mode: {req.analysis_mode}

Source Text:
{req.source_text}
{context_block}
    """

    data = await call_claude_json(system_prompt, user_prompt, max_tokens=4000)

    try:
        paragraphs_raw = data.get("paragraphs", []) if isinstance(data, dict) else []
        normalized_paragraphs = []
        for p in paragraphs_raw:
            if not isinstance(p, dict):
                continue
            original = p.get("original") or ""
            explanation = p.get("explanation") or p.get("explanation_zh") or p.get("analysis") or ""
            if original.strip() and explanation.strip():
                normalized_paragraphs.append({"original": original, "explanation": explanation})

        terms_raw = data.get("terms", []) if isinstance(data, dict) else []
        if not terms_raw:
            for p in paragraphs_raw:
                if isinstance(p, dict) and isinstance(p.get("terms"), list):
                    terms_raw.extend(p.get("terms"))
        normalized_terms = []
        for t in terms_raw:
            if not isinstance(t, dict):
                continue
            term = t.get("term") or t.get("word") or ""
            definition = t.get("definition_zh") or t.get("zh") or ""
            example = t.get("example") or t.get("in_sentence") or ""
            if term and definition:
                normalized_terms.append({"term": term, "zh": definition, "example": example})

        key_raw = data.get("key_sentences", []) if isinstance(data, dict) else []
        normalized_keys = []
        for item in key_raw:
            if not isinstance(item, dict):
                continue
            text = item.get("text") or item.get("sentence") or ""
            reason = item.get("reason") or ""
            if text and reason:
                normalized_keys.append({"text": text, "reason": reason})

        if req.grounded:
            contexts = search_rag_chunks(req.source_text, top_k=req.top_k)
            for idx, c in enumerate(contexts, start=1):
                title = c.get("title") or c.get("source_id") or f"source-{idx}"
                normalized_keys.append({"text": f"[引用 {idx}] {title}", "reason": "证据来源"})

        normalized = {
            "paragraphs": normalized_paragraphs,
            "terms": normalized_terms,
            "key_sentences": normalized_keys,
        }
        response = ArticleAnalyzeResponse(**normalized)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 返回数据格式错误：{e}。原始数据：{data}")
