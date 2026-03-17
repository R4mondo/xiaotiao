import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback for minimal runtime env
    def load_dotenv(dotenv_path=None, override=False, *args, **kwargs):
        path = Path(dotenv_path or Path(__file__).resolve().parent / ".env")
        if not path.exists():
            return False
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if override or key not in os.environ:
                os.environ[key] = value
        return True

load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import Request
from fastapi.responses import JSONResponse

from db.auth_db import init_auth_db
from db.database import init_db, run_migrations, get_user_db_path
from services.auth_service import extract_token, get_user_from_token
from routers import auth, topic, article, translation, vocab, research, papers, tracker, collections

try:
    from routers import multimodal
except Exception:
    multimodal = None

app = FastAPI(
    title="再译后端服务",
    description="再译平台后端 API 文档与调试入口。",
    version="1.0.0",
    swagger_ui_parameters={"lang": "zh-CN"},
)

@app.on_event("startup")
def on_startup():
    init_auth_db()
    init_db()
    run_migrations()

# Configure CORS — read allowed origins from env, or default to localhost for dev.
# Production: set CORS_ORIGINS=* or CORS_ORIGINS=https://yourdomain.com
_cors_env = os.environ.get("CORS_ORIGINS", "").strip()
if _cors_env:
    _cors_origins = ["*"] if _cors_env == "*" else [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    _cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_PATHS = {
    "/health",
    "/auth/login",
    "/auth/register",
    "/docs",
    "/openapi.json",
    "/redoc",
}


@app.middleware("http")
async def auth_guard(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS":
        return await call_next(request)
    if path in PUBLIC_PATHS or path.startswith("/docs"):
        return await call_next(request)
    token = extract_token(request)
    user = get_user_from_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"detail": "未登录或登录已失效。"})
    request.state.user = user
    request.state.db_path = get_user_db_path(user["id"])
    return await call_next(request)

@app.get(
    "/health",
    summary="健康检查",
    description="用于探活与负载均衡的基础健康检查接口。",
)
def health_check():
    return {"status": "正常", "db": "已连接"}  # We will update db status once connected

app.include_router(topic.router)
app.include_router(article.router)
app.include_router(translation.router)
app.include_router(vocab.router)
app.include_router(research.router)
app.include_router(papers.router)
app.include_router(tracker.router)
app.include_router(collections.router)
app.include_router(auth.router)
if multimodal:
    app.include_router(multimodal.router)

if __name__ == "__main__":
    import uvicorn
    # If run directly
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
