import os
from fastapi import APIRouter, HTTPException
from schemas import ArticleAnalyzeRequest, ArticleAnalyzeResponse
from services.prompt_engine import prompt_engine
from services.research_store import search_rag_chunks

router = APIRouter(prefix="/article", tags=["文章解读"])


def _format_rag_contexts(contexts: list) -> str:
    """将 RAG 检索结果格式化为模板可用的文本块。"""
    if not contexts:
        return ""
    lines = []
    for idx, item in enumerate(contexts, start=1):
        title = item.get("title") or item.get("source_id") or f"source-{idx}"
        chunk = str(item.get("chunk_text") or "").strip()
        lines.append(f"[{idx}] {title}\n{chunk}")
    return "\n\n".join(lines)


@router.post(
    "/analyze",
    response_model=ArticleAnalyzeResponse,
    summary="文章解读",
    description="对输入文本进行结构化解读，输出段落解析、术语与关键句。",
)
async def analyze_article(req: ArticleAnalyzeRequest):
    if len(req.source_text.split()) > 3500:
        raise HTTPException(status_code=422, detail="文本超过 3500 词限制。")

    # RAG 上下文准备
    grounded_context = ""
    rag_citations = []
    if req.grounded:
        contexts = search_rag_chunks(req.source_text, top_k=req.top_k)
        grounded_context = _format_rag_contexts(contexts)
        rag_citations = contexts

    try:
        response = await prompt_engine.generate(
            template_name="article_analyze.j2",
            response_model=ArticleAnalyzeResponse,
            max_tokens=4000,
            # 模板变量
            analysis_mode=req.analysis_mode,
            source_text=req.source_text,
            grounded_context=grounded_context,
        )
    except Exception as e:
        import logging
        logging.getLogger("xiaotiao").error("Article analyze error: %s", e)
        raise HTTPException(
            status_code=500, detail="AI 解读失败，请稍后重试。"
        )

    # 如果使用了 Grounded 模式，追加引用到 key_sentences
    if req.grounded and rag_citations:
        extra_keys = []
        for idx, c in enumerate(rag_citations, start=1):
            title = c.get("title") or c.get("source_id") or f"source-{idx}"
            extra_keys.append({"text": f"[引用 {idx}] {title}", "reason": "证据来源"})
        # Append citations — response is a Pydantic model, convert & rebuild
        data = response.model_dump()
        data["key_sentences"].extend(extra_keys)
        response = ArticleAnalyzeResponse(**data)

    return response
