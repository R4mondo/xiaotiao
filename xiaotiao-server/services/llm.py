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


# ── Per-feature provider configuration ──────────────────

PROVIDER_CAPABILITIES: dict[str, dict] = {
    "gemini": {
        "name": "Google Gemini",
        "models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        "default_model": "gemini-2.5-flash",
        "env_key": "GEMINI_API_KEY",
        "env_model": "GEMINI_MODEL",
        "json": True, "stream": True, "vision": True, "schema": True,
    },
    "openai": {
        "name": "OpenAI (ChatGPT)",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "env_model": "OPENAI_MODEL",
        "json": True, "stream": True, "vision": False, "schema": True,
    },
    "anthropic": {
        "name": "Anthropic (Claude)",
        "models": ["claude-3-7-sonnet-20250219", "claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"],
        "default_model": "claude-3-7-sonnet-20250219",
        "env_key": "ANTHROPIC_API_KEY",
        "env_model": "ANTHROPIC_MODEL",
        "json": True, "stream": True, "vision": True, "schema": False,
    },
    "qwen": {
        "name": "通义千问 (Qwen)",
        "models": ["qwen-max", "qwen-plus", "qwen-turbo", "qwen-vl-max"],
        "default_model": "qwen-max",
        "env_key": "QWEN_API_KEY",
        "env_model": "QWEN_MODEL",
        "json": True, "stream": False, "vision": True, "schema": False,
    },
    "deepseek": {
        "name": "DeepSeek",
        "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "env_model": "DEEPSEEK_MODEL",
        "json": True, "stream": True, "vision": False, "schema": False,
    },
    "zhipu": {
        "name": "智谱AI (GLM)",
        "models": ["glm-4-plus", "glm-4", "glm-4v-plus", "glm-4v"],
        "default_model": "glm-4-plus",
        "env_key": "ZHIPU_API_KEY",
        "env_model": "ZHIPU_MODEL",
        "json": True, "stream": True, "vision": True, "schema": False,
    },
    "kimi": {
        "name": "Kimi (月之暗面)",
        "models": ["moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k"],
        "default_model": "moonshot-v1-32k",
        "env_key": "KIMI_API_KEY",
        "env_model": "KIMI_MODEL",
        "json": True, "stream": True, "vision": False, "schema": False,
    },
}

# What capability each feature requires
FEATURE_REQUIRED_CAPS: dict[str, list[str]] = {
    "topic_generate":  ["json"],
    "article_analyze":  ["json"],
    "translation":      ["json"],
    "multimodal":       ["json", "vision"],
    "paper_ai":         ["stream"],
    "vocab_import":     ["json"],  # vision is optional for vocab
}

_FEATURE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "feature_providers.json")


def _load_feature_providers() -> dict[str, str]:
    """Load per-feature provider overrides from JSON config."""
    try:
        with open(_FEATURE_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_feature_providers(mapping: dict[str, str]) -> None:
    """Persist per-feature provider overrides to JSON config."""
    with open(_FEATURE_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def get_feature_provider(feature_id: str) -> str:
    """Get the provider for a specific feature (override or global default)."""
    overrides = _load_feature_providers()
    if feature_id in overrides and overrides[feature_id]:
        provider = overrides[feature_id]
        caps = PROVIDER_CAPABILITIES.get(provider, {})
        env_key = caps.get("env_key", "")
        if env_key and _env(env_key):
            return provider
    return _llm_provider()


def set_feature_provider(feature_id: str, provider: str) -> bool:
    """Set provider for a feature. Returns True if compatible."""
    if provider and provider != "default":
        caps = PROVIDER_CAPABILITIES.get(provider, {})
        required = FEATURE_REQUIRED_CAPS.get(feature_id, ["json"])
        for cap in required:
            if not caps.get(cap, False):
                return False
    mapping = _load_feature_providers()
    if provider == "default" or provider == "":
        mapping.pop(feature_id, None)
    else:
        mapping[feature_id] = provider
    _save_feature_providers(mapping)
    return True


def get_compatible_providers(feature_id: str) -> list[dict]:
    """Return list of providers compatible with a feature, with availability info."""
    required = FEATURE_REQUIRED_CAPS.get(feature_id, ["json"])
    result = []
    for pid, caps in PROVIDER_CAPABILITIES.items():
        compatible = all(caps.get(cap, False) for cap in required)
        env_key = caps.get("env_key", "")
        has_key = bool(_env(env_key)) if env_key else False
        result.append({
            "id": pid,
            "name": caps.get("name", pid),
            "models": caps.get("models", []),
            "default_model": caps.get("default_model", ""),
            "compatible": compatible,
            "has_key": has_key,
            "available": compatible and has_key,
        })
    return result


def get_all_feature_assignments() -> dict[str, dict]:
    """Get current provider assignment for all features."""
    overrides = _load_feature_providers()
    default = _llm_provider()
    assignments = {}
    for fid in FEATURE_REQUIRED_CAPS:
        provider = overrides.get(fid, "") or default
        is_override = fid in overrides and overrides[fid]
        assignments[fid] = {
            "provider": provider,
            "is_override": is_override,
            "is_default": not is_override,
        }
    return assignments


def _clean_json_text(content: str) -> str:
    """Robustly clean LLM text output into parseable JSON."""
    import re
    text = content.strip()
    # Strip markdown fences
    if text.startswith("```"):
        first_brace = text.find("{")
        if first_brace != -1:
            text = text[first_brace:]
    if text.endswith("```"):
        last_brace = text.rfind("}")
        if last_brace != -1:
            text = text[: last_brace + 1]
    # Extract JSON object if surrounded by other text
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        text = text[first_brace : last_brace + 1]
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    # Remove single-line JS-style comments
    text = re.sub(r'//[^\n]*', '', text)
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


def _safe_openai_content(data: dict) -> str:
    """Safely extract content from an OpenAI-compatible response.
    Handles empty choices arrays from third-party proxies."""
    choices = data.get("choices")
    if not choices:
        # Some proxies return error info in a different field
        err = data.get("error")
        if err:
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise RuntimeError(f"API returned error: {msg}")
        raise RuntimeError(f"API returned empty choices: {json.dumps(data, ensure_ascii=False)[:500]}")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    return _extract_message_content(content)


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
    max_retries = int(_env("OPENAI_HTTP_RETRIES", "2"))
    timeout_seconds = int(_env("OPENAI_HTTP_TIMEOUT", "180"))
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
    content = _safe_openai_content(data)
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
            "responseMimeType": "application/json",
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
try:
    anthropic_client = AsyncAnthropic() if (anthropic_key and AsyncAnthropic) else None
except TypeError:
    # httpx/anthropic version mismatch (proxies kwarg removed in newer httpx)
    anthropic_client = None


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
    content = _safe_openai_content(response)
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
    content = _safe_openai_content(response)
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


async def call_claude_stream(system_prompt: str, user_prompt: str, max_tokens: int = 4000, feature_id: str = ""):
    """Yield text chunks from the LLM as a generator (for StreamingResponse)."""
    provider = get_feature_provider(feature_id) if feature_id else _llm_provider()

    if provider == "mock":
        raise RuntimeError("AI 服务未配置：当前为 Mock 模式，请在管理后台配置真实的 API Key。")

    try:
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
            result = await _call_qwen_json(system_prompt, user_prompt, max_tokens)
            text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            yield text
        else:
            raise RuntimeError(f"AI 服务配置错误：不支持的 Provider '{provider}'，请检查管理后台配置。")
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"AI 调用失败 ({provider}): {exc}") from exc

# ──────────────────────────────────────────────
#  Schema-aware LLM calls — used by PromptEngine
# ──────────────────────────────────────────────


async def _call_gemini_with_schema(
    system_prompt: str, user_prompt: str, response_schema: dict, max_tokens: int = 4000
) -> dict:
    """Gemini with native responseSchema constraint."""
    model = _env("GEMINI_MODEL", "gemini-2.5-flash")
    max_retries = int(_env("GEMINI_HTTP_RETRIES", "1"))
    timeout_seconds = int(_env("GEMINI_HTTP_TIMEOUT", "120"))
    combined = f"{system_prompt}\n\n{user_prompt}".strip()

    gen_config = {
        "maxOutputTokens": max_tokens,
        "temperature": 0.7,
        "responseMimeType": "application/json",
    }
    # Attach response schema — Gemini uses a subset of JSON Schema.
    # Strip $defs and flatten references for compatibility.
    cleaned_schema = _flatten_schema_for_gemini(response_schema)
    if cleaned_schema:
        gen_config["responseSchema"] = cleaned_schema

    payload = {
        "contents": [{"role": "user", "parts": [{"text": combined}]}],
        "generationConfig": gen_config,
    }
    headers = {
        "x-goog-api-key": _gemini_api_key(),
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        for attempt in range(max_retries + 1):
            resp = await client.post(
                f"{_gemini_base_url()}/models/{model}:generateContent",
                json=payload,
                headers=headers,
            )
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


async def _call_openai_with_schema(
    system_prompt: str, user_prompt: str, response_schema: dict, max_tokens: int = 4000
) -> dict:
    """OpenAI with Structured Outputs or simple JSON mode for proxies."""
    model = _env("OPENAI_MODEL", "gpt-4o-mini")
    max_retries = int(_env("OPENAI_HTTP_RETRIES", "2"))
    timeout_seconds = int(_env("OPENAI_HTTP_TIMEOUT", "180"))

    # Detect if using a third-party proxy (custom base URL)
    custom_base = _env("OPENAI_BASE_URL", "").strip()
    is_official = not custom_base or "api.openai.com" in custom_base

    if is_official:
        # Official OpenAI: use Structured Outputs (json_schema)
        strict_schema = _prepare_openai_strict_schema(response_schema)
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "api_response",
                "strict": True,
                "schema": strict_schema,
            }
        }
        schema_instruction = ""
    else:
        # Third-party proxy: use simple json_object mode + inject schema in prompt
        response_format = {"type": "json_object"}
        schema_instruction = f"\n\nYou MUST respond with a JSON object following this schema:\n{json.dumps(response_schema, ensure_ascii=False, indent=2)}"

    payload = {
        "model": model,
        "temperature": 0.7,
        "max_tokens": max_tokens,
        "response_format": response_format,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
                + "\n\nIMPORTANT: Return one raw valid JSON object only. No markdown wrappers."
                + schema_instruction,
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
            resp = await client.post(
                f"{_openai_base_url()}/chat/completions",
                json=payload,
                headers=headers,
            )
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
    content = _safe_openai_content(data)
    return json.loads(_clean_json_text(content))


def _flatten_schema_for_gemini(schema: dict) -> dict:
    """
    Flatten a Pydantic-generated JSON Schema for Gemini's responseSchema.
    Gemini doesn't support $defs or $ref — inline all definitions.
    """
    if not isinstance(schema, dict):
        return schema

    defs = schema.pop("$defs", {})
    if not defs:
        # Remove unsupported keys
        schema.pop("title", None)
        schema.pop("description", None)
        return schema

    def _resolve(node):
        if not isinstance(node, dict):
            return node
        # Resolve $ref
        if "$ref" in node:
            ref_path = node["$ref"]  # e.g. "#/$defs/NewWord"
            ref_name = ref_path.rsplit("/", 1)[-1]
            if ref_name in defs:
                resolved = dict(defs[ref_name])
                resolved.pop("title", None)
                resolved.pop("description", None)
                return _resolve(resolved)
            return node

        # Handle anyOf (Pydantic Optional wrapping)
        if "anyOf" in node:
            non_null = [s for s in node["anyOf"] if s.get("type") != "null"]
            if len(non_null) == 1:
                resolved = dict(node)
                del resolved["anyOf"]
                resolved.update(_resolve(non_null[0]))
                return resolved

        # Recurse into properties
        if "properties" in node:
            for key, val in node["properties"].items():
                node["properties"][key] = _resolve(val)
        # Recurse into array items
        if "items" in node:
            node["items"] = _resolve(node["items"])
        node.pop("title", None)
        node.pop("description", None)
        return node

    return _resolve(schema)


def _prepare_openai_strict_schema(schema: dict) -> dict:
    """
    Prepare a Pydantic JSON Schema for OpenAI Structured Outputs strict mode.
    - Resolves $defs/$ref inline
    - Adds additionalProperties: false to all objects
    - Ensures all properties are in required (strict mode requirement)
    """
    import copy
    schema = copy.deepcopy(schema)
    defs = schema.pop("$defs", {})

    def _resolve(node):
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            ref_name = node["$ref"].rsplit("/", 1)[-1]
            if ref_name in defs:
                resolved = dict(defs[ref_name])
                return _resolve(resolved)
            return node

        # Handle anyOf for Optional
        if "anyOf" in node:
            non_null = [s for s in node["anyOf"] if s.get("type") != "null"]
            if len(non_null) == 1:
                resolved = dict(node)
                del resolved["anyOf"]
                resolved.update(_resolve(non_null[0]))
                return resolved

        if node.get("type") == "object" and "properties" in node:
            node["additionalProperties"] = False
            # Strict mode requires all properties in 'required'
            if "required" not in node:
                node["required"] = list(node["properties"].keys())
            for key, val in node["properties"].items():
                node["properties"][key] = _resolve(val)
        if "items" in node:
            node["items"] = _resolve(node["items"])
        return node

    resolved = _resolve(schema)
    resolved.pop("title", None)
    return resolved


async def call_llm_with_schema(
    system_prompt: str,
    user_prompt: str,
    response_schema: dict,
    max_tokens: int = 4000,
    feature_id: str = "",
) -> dict:
    """
    Schema-aware LLM call — used by PromptEngine.

    - Gemini: uses native responseSchema for constrained decoding
    - OpenAI: uses Structured Outputs (json_schema response_format)
    - Qwen/Anthropic/Mock: falls back to existing JSON mode + _clean_json_text
    """
    provider = get_feature_provider(feature_id) if feature_id else _llm_provider()
    try:
        if provider == "gemini":
            return await _call_gemini_with_schema(
                system_prompt, user_prompt, response_schema, max_tokens=max_tokens
            )
        if provider == "openai":
            return await _call_openai_with_schema(
                system_prompt, user_prompt, response_schema, max_tokens=max_tokens
            )
        # Qwen, Anthropic, Mock — use existing JSON mode (no native schema)
        if provider == "qwen":
            return await _call_qwen_json(system_prompt, user_prompt, max_tokens=max_tokens)
        if provider == "anthropic":
            return await _call_anthropic_json(system_prompt, user_prompt, max_tokens=max_tokens)
        raise RuntimeError("AI 服务未配置：当前为 Mock 模式，请在管理后台配置真实的 API Key。")
    except Exception as exc:
        if _env("LLM_FALLBACK_TO_MOCK", "false").lower() in {"1", "true", "yes"}:
            print(f"LLM schema call failed ({provider}), fallback to mock: {exc}")
            return await mock_claude_json(system_prompt, user_prompt)
        raise RuntimeError(f"AI 调用失败 ({provider}): {exc}") from exc


async def call_claude_json(system_prompt: str, user_prompt: str, max_tokens: int = 4000, feature_id: str = "") -> dict:
    provider = get_feature_provider(feature_id) if feature_id else _llm_provider()
    try:
        if provider == "gemini":
            return await _call_gemini_json(system_prompt, user_prompt, max_tokens=max_tokens)
        if provider == "openai":
            return await _call_openai_json(system_prompt, user_prompt, max_tokens=max_tokens)
        if provider == "qwen":
            return await _call_qwen_json(system_prompt, user_prompt, max_tokens=max_tokens)
        if provider == "anthropic":
            return await _call_anthropic_json(system_prompt, user_prompt, max_tokens=max_tokens)
        raise RuntimeError("AI 服务未配置：当前为 Mock 模式，请在管理后台配置真实的 API Key。")
    except Exception as exc:
        if _env("LLM_FALLBACK_TO_MOCK", "false").lower() in {"1", "true", "yes"}:
            print(f"LLM call failed ({provider}), fallback to mock: {exc}")
            return await mock_claude_json(system_prompt, user_prompt)
        raise RuntimeError(f"AI 调用失败 ({provider}): {exc}") from exc


async def call_claude_vision_json(
    system_prompt: str, user_prompt: str, base64_image: str, media_type: str, max_tokens: int = 4000, feature_id: str = ""
) -> dict:
    provider = get_feature_provider(feature_id) if feature_id else _llm_provider()
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
        raise RuntimeError("AI 服务未配置：当前为 Mock 模式，请在管理后台配置真实的 API Key。")
    except Exception as exc:
        if _env("LLM_FALLBACK_TO_MOCK", "false").lower() in {"1", "true", "yes"}:
            print(f"LLM vision call failed ({provider}), fallback to mock: {exc}")
            return await mock_claude_json(system_prompt, user_prompt)
        raise RuntimeError(f"AI 视觉调用失败 ({provider}): {exc}") from exc
