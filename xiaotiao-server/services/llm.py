import asyncio
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Any, AsyncGenerator

import httpx

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
    if _env("GEMINI_API_KEY"):
        return "gemini"
    if _env("OPENAI_API_KEY"):
        return "openai"
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


def _openai_base_url() -> str:
    base_url = _env("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    return base_url


def _openai_api_key() -> str:
    api_key = _env("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing.")
    return api_key


def _gemini_base_url() -> str:
    base_url = _env("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    return base_url


def _gemini_api_key() -> str:
    api_key = _env("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")
    return api_key


def _extract_gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    text_chunks = []
    for part in parts:
        if isinstance(part, dict) and part.get("text"):
            text_chunks.append(str(part.get("text")))
    return "".join(text_chunks)


async def _call_openai_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    model = _env("OPENAI_MODEL", "gpt-4o-mini")
    max_retries = int(_env("OPENAI_HTTP_RETRIES", "1"))
    timeout_seconds = int(_env("OPENAI_HTTP_TIMEOUT", "120"))
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
    headers = {
        "Authorization": f"Bearer {_openai_api_key()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for attempt in range(max_retries + 1):
            resp = await client.post(f"{_openai_base_url()}/chat/completions", json=payload, headers=headers)
            if resp.status_code >= 400:
                retryable = resp.status_code in {408, 409, 429, 500, 502, 503, 504}
                if retryable and attempt < max_retries:
                    await asyncio.sleep(0.8 * (attempt + 1))
                    continue
                detail = ""
                try:
                    err_payload = resp.json()
                    err_obj = err_payload.get("error") if isinstance(err_payload, dict) else None
                    detail = err_obj.get("message") if isinstance(err_obj, dict) else str(err_payload)
                except Exception:
                    detail = resp.text
                raise RuntimeError(f"OpenAI API {resp.status_code}: {detail}")
            data = resp.json()
            break
    content = _extract_message_content(data["choices"][0]["message"]["content"])
    return json.loads(_clean_json_text(content))


async def _call_gemini_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> dict:
    model = _env("GEMINI_MODEL", "gemini-2.5-flash")
    max_retries = int(_env("GEMINI_HTTP_RETRIES", "1"))
    timeout_seconds = int(_env("GEMINI_HTTP_TIMEOUT", "120"))
    combined = f"{system_prompt}\n\n{user_prompt}".strip()
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": combined}],
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7,
        },
    }
    headers = {
        "x-goog-api-key": _gemini_api_key(),
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for attempt in range(max_retries + 1):
            resp = await client.post(f"{_gemini_base_url()}/models/{model}:generateContent", json=payload, headers=headers)
            if resp.status_code >= 400:
                retryable = resp.status_code in {408, 409, 429, 500, 502, 503, 504}
                if retryable and attempt < max_retries:
                    await asyncio.sleep(0.8 * (attempt + 1))
                    continue
                detail = ""
                try:
                    err_payload = resp.json()
                    err_obj = err_payload.get("error") if isinstance(err_payload, dict) else None
                    detail = err_obj.get("message") if isinstance(err_obj, dict) else str(err_payload)
                except Exception:
                    detail = resp.text
                raise RuntimeError(f"Gemini API {resp.status_code}: {detail}")
            data = resp.json()
            break
    text = _extract_gemini_text(data)
    return json.loads(_clean_json_text(text))


async def _call_openai_stream(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> AsyncGenerator[str, None]:
    model = _env("OPENAI_MODEL", "gpt-4o-mini")
    max_retries = int(_env("OPENAI_HTTP_RETRIES", "1"))
    timeout_seconds = int(_env("OPENAI_HTTP_TIMEOUT", "120"))
    payload = {
        "model": model,
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "stream": True,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {_openai_api_key()}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for attempt in range(max_retries + 1):
            async with client.stream(
                "POST",
                f"{_openai_base_url()}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code >= 400:
                    retryable = resp.status_code in {408, 409, 429, 500, 502, 503, 504}
                    if retryable and attempt < max_retries:
                        await asyncio.sleep(0.8 * (attempt + 1))
                        continue
                    detail = ""
                    try:
                        err_payload = await resp.json()
                        err_obj = err_payload.get("error") if isinstance(err_payload, dict) else None
                        detail = err_obj.get("message") if isinstance(err_obj, dict) else str(err_payload)
                    except Exception:
                        detail = await resp.aread()
                    raise RuntimeError(f"OpenAI API {resp.status_code}: {detail}")
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        chunk = line[len("data: "):].strip()
                    else:
                        continue
                    if chunk == "[DONE]":
                        return
                    try:
                        data = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    text = delta.get("content")
                    if text:
                        yield text
            return


async def _call_gemini_stream(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> AsyncGenerator[str, None]:
    model = _env("GEMINI_MODEL", "gemini-2.5-flash")
    max_retries = int(_env("GEMINI_HTTP_RETRIES", "1"))
    timeout_seconds = int(_env("GEMINI_HTTP_TIMEOUT", "120"))
    combined = f"{system_prompt}\n\n{user_prompt}".strip()
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": combined}],
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7,
        },
    }
    headers = {
        "x-goog-api-key": _gemini_api_key(),
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for attempt in range(max_retries + 1):
            async with client.stream(
                "POST",
                f"{_gemini_base_url()}/models/{model}:streamGenerateContent",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status_code >= 400:
                    retryable = resp.status_code in {408, 409, 429, 500, 502, 503, 504}
                    if retryable and attempt < max_retries:
                        await asyncio.sleep(0.8 * (attempt + 1))
                        continue
                    detail = ""
                    try:
                        err_payload = await resp.json()
                        err_obj = err_payload.get("error") if isinstance(err_payload, dict) else None
                        detail = err_obj.get("message") if isinstance(err_obj, dict) else str(err_payload)
                    except Exception:
                        detail = await resp.aread()
                    raise RuntimeError(f"Gemini API {resp.status_code}: {detail}")
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    chunk = line
                    if line.startswith("data: "):
                        chunk = line[len("data: "):].strip()
                    if chunk == "[DONE]":
                        return
                    try:
                        data = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    text = _extract_gemini_text(data)
                    if text:
                        yield text
            return


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


async def _call_gemini_vision_json(
    system_prompt: str, user_prompt: str, base64_image: str, media_type: str, max_tokens: int = 4000
) -> dict:
    model = _env("GEMINI_MODEL", "gemini-2.5-flash")
    max_retries = int(_env("GEMINI_HTTP_RETRIES", "1"))
    timeout_seconds = int(_env("GEMINI_HTTP_TIMEOUT", "120"))
    combined = f"{system_prompt}\n\n{user_prompt}".strip()
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": combined},
                    {
                        "inline_data": {
                            "mime_type": media_type,
                            "data": base64_image,
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.7,
        },
    }
    headers = {
        "x-goog-api-key": _gemini_api_key(),
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for attempt in range(max_retries + 1):
            resp = await client.post(f"{_gemini_base_url()}/models/{model}:generateContent", json=payload, headers=headers)
            if resp.status_code >= 400:
                retryable = resp.status_code in {408, 409, 429, 500, 502, 503, 504}
                if retryable and attempt < max_retries:
                    await asyncio.sleep(0.8 * (attempt + 1))
                    continue
                detail = ""
                try:
                    err_payload = resp.json()
                    err_obj = err_payload.get("error") if isinstance(err_payload, dict) else None
                    detail = err_obj.get("message") if isinstance(err_obj, dict) else str(err_payload)
                except Exception:
                    detail = resp.text
                raise RuntimeError(f"Gemini API {resp.status_code}: {detail}")
            data = resp.json()
            break
    text = _extract_gemini_text(data)
    return json.loads(_clean_json_text(text))


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

    if "three distinct styles" in system_lower or '"variants"' in system_prompt or "翻译" in system_prompt or "translation" in system_lower:
        has_user_translation = "user's explicit translation attempt" in user_lower and '""' not in user_prompt
        return {
            "variants": [
                {"style": "literal", "label": "直译版", "text": "这是直译版本（模拟输出）"},
                {"style": "legal", "label": "法律表达版", "text": "这是法律专业翻译版本（模拟输出）"},
                {"style": "plain", "label": "简明表达版", "text": "这是简明翻译版本（模拟输出）"},
            ],
            "terms": [{"term": "tribunal", "definition_zh": "仲裁庭"}, {"term": "interim measures", "definition_zh": "临时措施"}],
            "notes": ["法律表达版需强调术语准确与正式措辞。", "简明表达版应优先可读性与清晰性。"],
            "common_errors": ["忽略法律术语固定译法。", "被动结构处理不当导致语义偏差。"],
            "confidence_hint": "high",
            "critique": {
                "score": "85 / 100",
                "feedback": "译文基本传达了原意，但法律语体仍可更正式。",
                "improvements": [
                    {
                        "original": "法院可以先做安排",
                        "suggested": "仲裁庭有权裁定临时措施",
                        "reason": "使用更准确的法律术语并强化法律语气。",
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

    if provider == "gemini":
        async for text in _call_gemini_stream(system_prompt, user_prompt, max_tokens=max_tokens):
            yield text
    elif provider == "openai":
        async for text in _call_openai_stream(system_prompt, user_prompt, max_tokens=max_tokens):
            yield text
    elif provider == "anthropic" and anthropic_client:
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
        if provider == "gemini":
            return await _call_gemini_json(system_prompt, user_prompt, max_tokens=max_tokens)
        if provider == "openai":
            return await _call_openai_json(system_prompt, user_prompt, max_tokens=max_tokens)
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
        if provider == "gemini":
            return await _call_gemini_vision_json(
                system_prompt, user_prompt, base64_image, media_type, max_tokens=max_tokens
            )
        if provider == "qwen":
            return await _call_qwen_vision_json(system_prompt, user_prompt, base64_image, media_type, max_tokens=max_tokens)
        if provider == "anthropic":
            return await _call_anthropic_vision_json(
                system_prompt, user_prompt, base64_image, media_type, max_tokens=max_tokens
            )
        if provider == "openai":
            raise RuntimeError("OpenAI vision is not configured for this project.")
        print("Using LLM Vision JSON MOCK (No provider key)")
        return await mock_claude_json(system_prompt, user_prompt)
    except Exception as exc:
        if _env("LLM_FALLBACK_TO_MOCK", "true").lower() in {"1", "true", "yes"}:
            print(f"LLM vision call failed ({provider}), fallback to mock: {exc}")
            return await mock_claude_json(system_prompt, user_prompt)
        raise RuntimeError(f"Failed to generate valid vision response from {provider}: {exc}") from exc
