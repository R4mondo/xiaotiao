"""AI 连接测试接口 — 不需要用户登录，直接测试 LLM API 连通性"""
import os
import json
import time
import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/ai-test", tags=["AI测试"])


@router.get("/ping")
async def ai_test_ping():
    """简单测试 AI API 是否可访问。
    直接向配置的 LLM API 发送一个极简请求并返回结果。
    """
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    if provider != "openai" or not api_key:
        return {
            "status": "error",
            "message": f"当前 LLM_PROVIDER={provider}，非 OpenAI 兼容模式或缺少 API Key",
            "config": {
                "provider": provider,
                "has_key": bool(api_key),
                "base_url": base_url,
                "model": model,
            }
        }

    # 构造极简请求
    payload = {
        "model": model,
        "max_tokens": 50,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": "你是一个测试助手。"},
            {"role": "user", "content": "请回复：连接成功！当前模型是什么？"},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            elapsed = round(time.time() - start, 2)

            if resp.status_code >= 400:
                error_detail = ""
                try:
                    err = resp.json()
                    error_detail = json.dumps(err, ensure_ascii=False, indent=2)
                except Exception:
                    error_detail = resp.text[:500]
                return {
                    "status": "error",
                    "http_code": resp.status_code,
                    "elapsed_seconds": elapsed,
                    "message": f"API 返回错误 {resp.status_code}",
                    "detail": error_detail,
                    "config": {
                        "base_url": base_url,
                        "model": model,
                    }
                }

            data = resp.json()
            choices = data.get("choices", [])
            content = ""
            if choices:
                content = choices[0].get("message", {}).get("content", "")

            return {
                "status": "success",
                "elapsed_seconds": elapsed,
                "model_used": data.get("model", model),
                "ai_response": content,
                "usage": data.get("usage", {}),
                "config": {
                    "base_url": base_url,
                    "model": model,
                }
            }
    except httpx.ConnectError as e:
        return {
            "status": "error",
            "elapsed_seconds": round(time.time() - start, 2),
            "message": f"无法连接到 API 服务器: {e}",
            "config": {"base_url": base_url, "model": model},
        }
    except httpx.TimeoutException:
        return {
            "status": "error",
            "elapsed_seconds": round(time.time() - start, 2),
            "message": "请求超时（30秒）",
            "config": {"base_url": base_url, "model": model},
        }
    except Exception as e:
        return {
            "status": "error",
            "elapsed_seconds": round(time.time() - start, 2),
            "message": f"未知错误: {type(e).__name__}: {e}",
            "config": {"base_url": base_url, "model": model},
        }


@router.post("/chat")
async def ai_test_chat(prompt: str = "你好，请用一句话介绍你自己。"):
    """发送自定义 prompt 测试 AI 回复质量。"""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    if not api_key:
        return {"status": "error", "message": "OPENAI_API_KEY 未配置"}

    payload = {
        "model": model,
        "max_tokens": 500,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": "你是「再译」英语学习平台的AI助手，擅长学术英语翻译和教学。"},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
            elapsed = round(time.time() - start, 2)

            if resp.status_code >= 400:
                return {
                    "status": "error",
                    "http_code": resp.status_code,
                    "elapsed_seconds": elapsed,
                    "detail": resp.text[:500],
                }

            data = resp.json()
            choices = data.get("choices", [])
            content = choices[0].get("message", {}).get("content", "") if choices else ""

            return {
                "status": "success",
                "elapsed_seconds": elapsed,
                "model_used": data.get("model", model),
                "ai_response": content,
                "usage": data.get("usage", {}),
            }
    except Exception as e:
        return {
            "status": "error",
            "elapsed_seconds": round(time.time() - start, 2),
            "message": f"{type(e).__name__}: {e}",
        }
