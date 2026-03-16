from __future__ import annotations

from fastapi import APIRouter, HTTPException

from schemas import RagIngestRequest, RagQueryRequest, RagQueryResponse
from services.github_search import refresh_github_cases
from services.rag import build_citations, build_grounded_answer, github_case_to_doc, split_chunks
from services.research_store import (
    list_github_cases,
    list_org_units,
    rag_stats,
    replace_rag_chunks,
    search_rag_chunks,
    upsert_rag_document,
)

router = APIRouter(prefix="/research", tags=["研究资料"])


@router.get(
    "/github-cases",
    summary="获取 GitHub 案例",
    description="获取已缓存的 GitHub 项目案例列表。",
)
async def get_github_cases(limit: int = 20):
    return {"items": list_github_cases(limit=limit)}


@router.post(
    "/github-cases/refresh",
    summary="刷新 GitHub 案例",
    description="从 GitHub 拉取最新案例并更新缓存。",
)
async def refresh_cases():
    try:
        return refresh_github_cases()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub 刷新失败：{exc}")


@router.get(
    "/org-units",
    summary="获取组织单位",
    description="获取研究组织单位列表。",
)
async def get_org_units():
    return {"items": list_org_units()}


@router.post(
    "/rag/ingest",
    summary="写入 RAG 文档",
    description="写入单篇文档并分块到 RAG 索引。",
)
async def ingest_rag(req: RagIngestRequest):
    if not req.content.strip():
        raise HTTPException(status_code=422, detail="content 为必填字段。")
    document_id = upsert_rag_document(
        source_id=req.source_id,
        source_type=req.source_type,
        title=req.title,
        source_url=req.source_url,
        metadata=req.metadata,
    )
    chunks = split_chunks(req.content)
    chunk_count = replace_rag_chunks(document_id, chunks)
    return {
        "ok": True,
        "document_id": document_id,
        "chunk_count": chunk_count,
        "stats": rag_stats(),
    }


@router.post(
    "/rag/ingest/github-cases",
    summary="批量写入 GitHub 案例",
    description="将 GitHub 案例批量写入 RAG 索引。",
)
async def ingest_rag_from_github(limit: int = 30):
    cases = list_github_cases(limit=max(1, min(limit, 100)))
    docs = 0
    chunks = 0
    for case in cases:
        source_id, source_type, title, source_url, metadata, content = github_case_to_doc(case)
        document_id = upsert_rag_document(
            source_id=source_id,
            source_type=source_type,
            title=title,
            source_url=source_url,
            metadata=metadata,
        )
        chunk_count = replace_rag_chunks(document_id, split_chunks(content, chunk_size=500, overlap=80))
        docs += 1
        chunks += chunk_count
    return {
        "ok": True,
        "ingested_documents": docs,
        "ingested_chunks": chunks,
        "stats": rag_stats(),
    }


@router.post(
    "/rag/query",
    response_model=RagQueryResponse,
    summary="RAG 查询",
    description="基于 RAG 索引检索并生成答案与引用。",
)
async def query_rag(req: RagQueryRequest):
    contexts = search_rag_chunks(req.query, top_k=req.top_k)
    answer = build_grounded_answer(req.query, contexts)
    citations = build_citations(contexts)
    return {
        "answer": answer,
        "citations": citations,
        "chunks": [str(item.get("chunk_text") or "") for item in contexts],
    }
