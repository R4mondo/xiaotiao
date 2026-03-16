import asyncio
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

try:
    from anthropic import AsyncAnthropic
except Exception:  # pragma: no cover - allow runtime without anthropic package
    AsyncAnthropic = None


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _llm_provider() -> str:
    provider = _env("LLM_PROVIDER", "").lower()
    if provider:
        return provider
    if _env("QWEN_API_KEY"):
        return "qwen"
    if _env("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "mock"


def _clean_json_text(content: str) -> str:
    text = content.strip()
    if text.startswith("```json"):
        text = text[text.find("{") :]
    if text.endswith("```"):
        text = text[: text.rfind("}") + 1]
    return text


def _extract_message_content(raw: Any) -> str:
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts = []
        for item in raw:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(raw)


def _openai_compatible_call(payload: dict) -> dict:
    api_key = _env("QWEN_API_KEY")
    if not api_key:
        raise RuntimeError("QWEN_API_KEY is missing.")
    base_url = _env("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
    endpoint = f"{base_url}/chat/completions"
    timeout_seconds = int(_env("QWEN_HTTP_TIMEOUT", "120"))
    max_retries = int(_env("QWEN_HTTP_RETRIES", "1"))

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    verify_ssl = _env("LLM_SSL_VERIFY", "true").lower() in {"1", "true", "yes"}
    if verify_ssl:
        try:
            import certifi  # type: ignore

            ssl_context = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            ssl_context = ssl.create_default_context()
    else:
        ssl_context = ssl._create_unverified_context()

    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds, context=ssl_context) as response:
                response_text = response.read().decode("utf-8")
                return json.loads(response_text)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            retryable = exc.code in {408, 409, 429, 500, 502, 503, 504}
            if retryable and attempt < max_retries:
                time.sleep(0.8 * (attempt + 1))
                continue
            raise RuntimeError(f"Qwen HTTPError {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            if attempt < max_retries:
                time.sleep(0.8 * (attempt + 1))
                continue
            raise RuntimeError(f"Qwen URL error: {exc}") from exc

    raise RuntimeError("Qwen request failed after retries")


anthropic_key = _env("ANTHROPIC_API_KEY")
anthropic_client = AsyncAnthropic() if (anthropic_key and AsyncAnthropic) else None


async def _call_qwen_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    model = _env("QWEN_MODEL", "qwen-plus")
    payload = {
        "model": model,
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": system_prompt
                + "\n\nIMPORTANT: Return one raw valid JSON object only. No markdown wrappers.",
            },
            {"role": "user", "content": user_prompt},
        ],
    }
    response = await asyncio.to_thread(_openai_compatible_call, payload)
    content = _extract_message_content(response["choices"][0]["message"]["content"])
    return json.loads(_clean_json_text(content))


async def _call_qwen_vision_json(
    system_prompt: str, user_prompt: str, base64_image: str, media_type: str, max_tokens: int = 4000
) -> dict:
    model = _env("QWEN_VISION_MODEL", _env("QWEN_MODEL", "qwen-vl-plus"))
    payload = {
        "model": model,
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": system_prompt
                + "\n\nIMPORTANT: Return one raw valid JSON object only. No markdown wrappers.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{base64_image}"}},
                ],
            },
        ],
    }
    response = await asyncio.to_thread(_openai_compatible_call, payload)
    content = _extract_message_content(response["choices"][0]["message"]["content"])
    return json.loads(_clean_json_text(content))


async def _call_anthropic_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    if not anthropic_client:
        raise RuntimeError("Anthropic client unavailable.")
    response = await anthropic_client.messages.create(
        model=_env("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"),
        max_tokens=max_tokens,
        system=system_prompt
        + "\n\nIMPORTANT: Return one raw valid JSON object only. No markdown wrappers.",
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.7,
    )
    content = response.content[0].text.strip()
    return json.loads(_clean_json_text(content))


async def _call_anthropic_vision_json(
    system_prompt: str, user_prompt: str, base64_image: str, media_type: str, max_tokens: int = 4000
) -> dict:
    if not anthropic_client:
        raise RuntimeError("Anthropic client unavailable.")
    response = await anthropic_client.messages.create(
        model=_env("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"),
        max_tokens=max_tokens,
        system=system_prompt
        + "\n\nIMPORTANT: Return one raw valid JSON object only. No markdown wrappers.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image,
                        },
                    },
                    {"type": "text", "text": user_prompt},
                ],
            }
        ],
        temperature=0.7,
    )
    content = response.content[0].text.strip()
    return json.loads(_clean_json_text(content))


async def mock_claude_json(system_prompt: str, user_prompt: str) -> dict:
    await asyncio.sleep(0.5)
    system_lower = system_prompt.lower()
    user_lower = user_prompt.lower()

    if "topicgenerateresponse" in system_prompt or "topics:" in user_lower:
        return {
            "result_text": "This is a mock generated article about international law. It includes key terms like jurisdiction and arbitration. The WTO plays a significant role in dispute resolution.",
            "db_words_used": ["jurisdiction", "arbitration"],
            "new_words": [
                {
                    "word": "justiciability",
                    "definition_zh": "可司法性",
                    "in_sentence": "The justiciability of the dispute depends on treaty scope.",
                },
                {
                    "word": "preclusion",
                    "definition_zh": "排除效力",
                    "in_sentence": "Issue preclusion may narrow the tribunal's review.",
                },
            ],
            "terms": [
                {"term": "jurisdiction", "zh": "管辖权", "example": "The court has no jurisdiction over this case."},
                {"term": "arbitration", "zh": "仲裁", "example": "They agreed to settle the dispute through arbitration."},
            ],
            "notes": ["Jurisdiction defines legal authority.", "Arbitration is an ADR mechanism."],
            "confidence_hint": "high",
        }

    if "articleanalyzeresponse" in system_prompt or "analyze the provided english text" in system_lower:
        return {
            "paragraphs": [{"original": "This is the first paragraph. It is very important.", "explanation": "这是第一段。它非常重要。"}],
            "terms": [{"term": "paragraph", "zh": "段落", "example": "Read the paragraph."}],
            "key_sentences": [{"text": "It is very important.", "reason": "Highlighting significance."}],
        }

    if "three distinct styles" in system_lower or '"variants"' in system_prompt:
        has_user_translation = "user's explicit translation attempt" in user_lower and '""' not in user_prompt
        return {
            "variants": [
                {"style": "literal", "label": "直译版 Literal", "text": "这是直译版本 (Mock)"},
                {"style": "legal", "label": "法律表达版 Legal", "text": "这是法律专业翻译版本 (Mock)"},
                {"style": "plain", "label": "简明表达版 Plain", "text": "这是简明翻译版本 (Mock)"},
            ],
            "terms": [{"term": "tribunal", "definition_zh": "仲裁庭"}, {"term": "interim measures", "definition_zh": "临时措施"}],
            "notes": ["Legal style favors precision and formality.", "Plain style prioritizes readability."],
            "confidence_hint": "high",
            "critique": {
                "score": "85 / 100",
                "feedback": "Your translation captures the core meaning but can be more formal.",
                "improvements": [
                    {
                        "original": "法院可以先做安排",
                        "suggested": "仲裁庭有权裁定临时措施",
                        "reason": "Use domain-specific legal terminology and stronger modal expression.",
                    }
                ],
            }
            if has_user_translation
            else None,
        }

    return {
        "extracted_words": [
            {"word": "contract", "definition_zh": "合同", "part_of_speech": "n.", "in_sentence": "Sign the contract."},
            {"word": "breach", "definition_zh": "违约", "part_of_speech": "n.", "in_sentence": "A breach of contract."},
        ],
        "summary": "This is a mock multimodal extraction summary.",
    }


async def call_claude_stream(system_prompt: str, user_prompt: str, max_tokens: int = 4000):
    """Yield text chunks from the LLM as a generator (for StreamingResponse)."""
    provider = _llm_provider()

    if provider == "anthropic" and anthropic_client:
        async with anthropic_client.messages.stream(
            model=_env("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.7,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    elif provider == "qwen":
        # Qwen doesn't support native streaming in our setup, so call sync and yield at once
        result = await _call_qwen_json(system_prompt, user_prompt, max_tokens)
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        yield text
    else:
        # Mock streaming
        import asyncio as _asyncio
        mock_text = "这是一段 AI 生成的模拟响应文本。在生产环境中，这里会是来自大语言模型的真实分析内容。"
        for char in mock_text:
            yield char
            await _asyncio.sleep(0.02)


async def call_claude_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    provider = _llm_provider()
    try:
        if provider == "qwen":
            return await _call_qwen_json(system_prompt, user_prompt, max_tokens=max_tokens)
        if provider == "anthropic":
            return await _call_anthropic_json(system_prompt, user_prompt, max_tokens=max_tokens)
        print("Using LLM JSON MOCK (No provider key)")
        return await mock_claude_json(system_prompt, user_prompt)
    except Exception as exc:
        if _env("LLM_FALLBACK_TO_MOCK", "true").lower() in {"1", "true", "yes"}:
            print(f"LLM call failed ({provider}), fallback to mock: {exc}")
            return await mock_claude_json(system_prompt, user_prompt)
        raise RuntimeError(f"Failed to generate valid response from {provider}: {exc}") from exc


async def call_claude_vision_json(
    system_prompt: str, user_prompt: str, base64_image: str, media_type: str, max_tokens: int = 4000
) -> dict:
    provider = _llm_provider()
    try:
        if provider == "qwen":
            return await _call_qwen_vision_json(system_prompt, user_prompt, base64_image, media_type, max_tokens=max_tokens)
        if provider == "anthropic":
            return await _call_anthropic_vision_json(
                system_prompt, user_prompt, base64_image, media_type, max_tokens=max_tokens
            )
        print("Using LLM Vision JSON MOCK (No provider key)")
        return await mock_claude_json(system_prompt, user_prompt)
    except Exception as exc:
        if _env("LLM_FALLBACK_TO_MOCK", "true").lower() in {"1", "true", "yes"}:
            print(f"LLM vision call failed ({provider}), fallback to mock: {exc}")
            return await mock_claude_json(system_prompt, user_prompt)
        raise RuntimeError(f"Failed to generate valid vision response from {provider}: {exc}") from exc
