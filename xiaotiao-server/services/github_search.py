from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from services.research_store import upsert_github_case


DEFAULT_QUERIES = [
    "fastapi react openai template stars:>20",
    "legal ai assistant fastapi react openai stars:>5",
    "streaming fastapi openai stars:>10",
    "rag legal assistant fastapi stars:>5",
]

FALLBACK_ITEMS = [
    {
        "full_name": "BCG-X-Official/agentkit",
        "html_url": "https://github.com/BCG-X-Official/agentkit",
        "stargazers_count": 1900,
        "description": "Starter-kit for constrained agents with Next.js + FastAPI",
        "language": "TypeScript",
    },
    {
        "full_name": "Ramseygithub/ai-legal-compliance-assistant",
        "html_url": "https://github.com/Ramseygithub/ai-legal-compliance-assistant",
        "stargazers_count": 300,
        "description": "AI-powered legal compliance assistant with RAG pipeline",
        "language": "Python",
    },
    {
        "full_name": "nomic-ai/semantic-search-app-template",
        "html_url": "https://github.com/nomic-ai/semantic-search-app-template",
        "stargazers_count": 110,
        "description": "Semantic search template with FastAPI and OpenAI",
        "language": "Python",
    },
]


def fetch_repositories(query: str, per_page: int = 20) -> List[Dict[str, Any]]:
    encoded = quote_plus(query)
    url = (
        "https://api.github.com/search/repositories"
        f"?q={encoded}&sort=stars&order=desc&per_page={max(1, min(per_page, 50))}"
    )
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "xiaotiao-research-bot",
        },
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    items = payload.get("items", [])
    if isinstance(items, list):
        return items
    return []


def refresh_github_cases(queries: Optional[List[str]] = None, per_page: int = 20) -> Dict[str, Any]:
    selected_queries = queries or DEFAULT_QUERIES
    total_saved = 0
    cycle_details = []
    for query in selected_queries:
        try:
            items = fetch_repositories(query, per_page=per_page)
        except Exception:
            items = FALLBACK_ITEMS
        saved = 0
        for item in items:
            full_name = item.get("full_name")
            html_url = item.get("html_url")
            if not full_name or not html_url:
                continue
            upsert_github_case(
                query=query,
                full_name=str(full_name),
                html_url=str(html_url),
                stars=int(item.get("stargazers_count", 0)),
                description=item.get("description"),
                language=item.get("language"),
            )
            saved += 1
        total_saved += saved
        cycle_details.append({"query": query, "fetched": len(items), "saved": saved})
    return {
        "ok": True,
        "saved_total": total_saved,
        "queries": cycle_details,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
    }
