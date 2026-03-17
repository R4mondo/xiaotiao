"""
Admin Dashboard — 管理后台 AI 操控中心

通过 /admin 访问，固定密码保护。
提供 AI 功能地图、API 配置、连接测试、提示词模板编辑等功能。
"""

import html as html_mod
import json
import os
import secrets
import time
import traceback
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

router = APIRouter(prefix="/admin", tags=["管理后台"])

# ── Config ──────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "xiaotiao2026")
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
_start_time = time.time()

# Simple in-memory session store for admin
_admin_sessions: dict[str, float] = {}
SESSION_COOKIE = "admin_sid"
SESSION_TTL = 3600 * 8  # 8 hours

# ── AI Feature Registry ────────────────────────────────
AI_FEATURES = [
    {
        "id": "topic_generate",
        "name": "主题文章生成",
        "icon": "📝",
        "frontend": "主题探索",
        "frontend_path": "/#/topic",
        "frontend_action": "选择主题 → 生成文章",
        "template": "topic_generate.j2",
        "call_type": "JSON",
        "description": "根据用户选择的主题和词汇，AI 生成包含指定单词的教学文章",
        "variables": ["topics", "domains", "level", "article_length", "db_words", "new_word_count", "style_modifier", "rag_context"],
    },
    {
        "id": "article_analyze",
        "name": "文章解读分析",
        "icon": "🔍",
        "frontend": "文章实验室",
        "frontend_path": "/#/article-lab",
        "frontend_action": "粘贴英文文章 → AI 解读",
        "template": "article_analyze.j2",
        "call_type": "JSON",
        "description": "AI 逐段解读英文文章，提供中文翻译、术语提取、关键句分析",
        "variables": ["source_text", "analysis_mode", "grounded_context"],
    },
    {
        "id": "translation",
        "name": "翻译练习",
        "icon": "🌐",
        "frontend": "翻译工作室",
        "frontend_path": "/#/translation",
        "frontend_action": "输入源文 → AI 提供三种风格译文",
        "template": "translation.j2",
        "call_type": "JSON",
        "description": "AI 提供直译/法律/简明三种翻译风格，并对用户自译进行点评",
        "variables": ["source_text", "direction", "user_translation"],
    },
    {
        "id": "multimodal",
        "name": "多模态词汇提取",
        "icon": "📸",
        "frontend": "多模态",
        "frontend_path": "/#/multimodal",
        "frontend_action": "上传图片/文档 → AI 提取专业词汇",
        "template": "multimodal.j2",
        "call_type": "Vision + JSON",
        "description": "从图片、PDF、文档中 AI 识别并提取专业领域词汇",
        "variables": ["domain", "extracted_text"],
    },
    {
        "id": "paper_ai",
        "name": "论文 AI 分析",
        "icon": "📄",
        "frontend": "论文库",
        "frontend_path": "/#/papers",
        "frontend_action": "打开论文 → AI 分析/对话/翻译/总结",
        "template": None,
        "call_type": "Stream",
        "description": "AI 流式分析论文内容，支持对话问答、段落翻译、术语提取、摘要生成",
        "variables": [],
    },
    {
        "id": "vocab_import",
        "name": "生词本 AI 导入",
        "icon": "📚",
        "frontend": "生词本",
        "frontend_path": "/#/vocab",
        "frontend_action": "粘贴文本/拍照 → AI 批量提取生词",
        "template": None,
        "call_type": "JSON + Vision",
        "description": "AI 从文本或图片中批量提取单词并自动添加到生词本",
        "variables": [],
    },
]


def _check_session(request: Request) -> bool:
    sid = request.cookies.get(SESSION_COOKIE, "")
    if sid and sid in _admin_sessions:
        if time.time() - _admin_sessions[sid] < SESSION_TTL:
            return True
        del _admin_sessions[sid]
    return False


def _create_session() -> str:
    sid = secrets.token_hex(24)
    _admin_sessions[sid] = time.time()
    return sid


# ── Styles ──────────────────────────────────────────────
_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter','Noto Sans SC',system-ui,sans-serif;background:#0a0e17;color:#e2e8f0;min-height:100vh}
a{color:#60a5fa;text-decoration:none}
a:hover{text-decoration:underline}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(99,102,241,.3);border-radius:3px}

.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.login-card{background:rgba(15,23,42,.85);border:1px solid rgba(99,102,241,.25);border-radius:16px;padding:48px 40px;width:100%;max-width:400px;backdrop-filter:blur(24px)}
.login-card h1{font-size:1.5rem;font-weight:700;margin-bottom:8px;background:linear-gradient(135deg,#818cf8,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.login-card p{color:#94a3b8;font-size:.875rem;margin-bottom:28px}
.login-card input{width:100%;padding:12px 16px;border:1px solid rgba(148,163,184,.2);border-radius:10px;background:rgba(30,41,59,.6);color:#e2e8f0;font-size:.95rem;outline:none;transition:border .2s}
.login-card input:focus{border-color:#818cf8}
.login-card button{width:100%;padding:12px;margin-top:16px;border:none;border-radius:10px;background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;font-size:.95rem;font-weight:600;cursor:pointer;transition:opacity .2s}
.login-card button:hover{opacity:.9}
.login-error{color:#f87171;font-size:.85rem;margin-top:12px;text-align:center}

.dash{max-width:1200px;margin:0 auto;padding:24px 20px 60px}
.dash-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:32px;flex-wrap:wrap;gap:12px}
.dash-header h1{font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,#818cf8,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.dash-header .logout{padding:8px 18px;border:1px solid rgba(148,163,184,.2);border-radius:8px;background:transparent;color:#94a3b8;font-size:.85rem;cursor:pointer;transition:all .2s;text-decoration:none}
.dash-header .logout:hover{border-color:#f87171;color:#f87171}

/* Top stats row */
.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:28px}
.stat-card{background:rgba(15,23,42,.7);border:1px solid rgba(99,102,241,.15);border-radius:14px;padding:20px;backdrop-filter:blur(12px);transition:border-color .2s}
.stat-card:hover{border-color:rgba(99,102,241,.4)}
.stat-label{font-size:.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.stat-value{font-size:1.3rem;font-weight:700;color:#e2e8f0}
.stat-sub{font-size:.78rem;margin-top:4px}
.ok{color:#4ade80}
.warn{color:#fbbf24}
.err{color:#f87171}

/* Section panels */
.section{background:rgba(15,23,42,.7);border:1px solid rgba(99,102,241,.15);border-radius:14px;padding:28px;margin-bottom:24px;backdrop-filter:blur(12px)}
.section h2{font-size:1.15rem;font-weight:700;margin-bottom:6px;color:#c7d2fe;display:flex;align-items:center;gap:8px}
.section .subtitle{font-size:.82rem;color:#64748b;margin-bottom:20px}

/* AI Feature Map */
.feature-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}
.feature-card{background:rgba(30,41,59,.5);border:1px solid rgba(148,163,184,.1);border-radius:12px;padding:20px;transition:all .3s;position:relative;overflow:hidden}
.feature-card:hover{border-color:rgba(99,102,241,.4);transform:translateY(-2px)}
.feature-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:12px 12px 0 0}
.feature-card.type-json::before{background:linear-gradient(90deg,#818cf8,#60a5fa)}
.feature-card.type-stream::before{background:linear-gradient(90deg,#f472b6,#fb923c)}
.feature-card.type-vision::before{background:linear-gradient(90deg,#4ade80,#22d3ee)}
.fc-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.fc-title{display:flex;align-items:center;gap:10px}
.fc-title .icon{font-size:1.4rem}
.fc-title .name{font-weight:700;font-size:1rem;color:#e2e8f0}
.fc-status{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.fc-status.active{background:#4ade80;box-shadow:0 0 8px rgba(74,222,128,.5)}
.fc-status.mock{background:#fbbf24;box-shadow:0 0 8px rgba(251,191,36,.4)}
.fc-status.error{background:#f87171;box-shadow:0 0 8px rgba(248,113,113,.4)}
.fc-frontend{display:flex;align-items:center;gap:6px;font-size:.82rem;color:#94a3b8;margin-bottom:8px;padding:6px 10px;background:rgba(99,102,241,.08);border-radius:8px}
.fc-frontend .arrow{color:#6366f1;font-size:.75rem}
.fc-desc{font-size:.8rem;color:#64748b;margin-bottom:12px;line-height:1.5}
.fc-meta{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.fc-tag{font-size:.72rem;padding:3px 10px;border-radius:6px;font-weight:500}
.fc-tag.call{background:rgba(99,102,241,.12);color:#818cf8}
.fc-tag.tpl{background:rgba(74,222,128,.1);color:#4ade80;cursor:pointer;text-decoration:none;transition:background .2s}
.fc-tag.tpl:hover{background:rgba(74,222,128,.2);text-decoration:none}
.fc-tag.inline{background:rgba(251,191,36,.1);color:#fbbf24}

/* API Config */
.api-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-bottom:20px}
.api-card{background:rgba(30,41,59,.5);border:1px solid rgba(148,163,184,.08);border-radius:12px;padding:18px;position:relative;transition:all .2s}
.api-card.selected{border-color:rgba(99,102,241,.5);background:rgba(99,102,241,.08)}
.api-card .provider-name{font-weight:700;font-size:.95rem;color:#e2e8f0;margin-bottom:4px}
.api-card .provider-models{font-size:.75rem;color:#64748b;margin-bottom:10px}
.api-card .caps{display:flex;gap:6px;margin-bottom:12px}
.api-card .cap{font-size:.68rem;padding:2px 8px;border-radius:5px;font-weight:500}
.cap.y{background:rgba(74,222,128,.1);color:#4ade80}
.cap.n{background:rgba(248,113,113,.08);color:#f87171}
.api-input{width:100%;padding:8px 12px;border:1px solid rgba(148,163,184,.15);border-radius:8px;background:rgba(15,23,42,.5);color:#e2e8f0;font-size:.82rem;outline:none;transition:border .2s;margin-bottom:6px;font-family:'JetBrains Mono',monospace}
.api-input:focus{border-color:#818cf8}
.api-input::placeholder{color:#475569}
.key-status{font-size:.72rem;margin-top:2px}

/* Connection Test */
.test-area{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.test-btn{padding:10px 24px;border:none;border-radius:10px;background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;font-size:.9rem;font-weight:600;cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:8px}
.test-btn:hover{opacity:.9}
.test-btn:disabled{opacity:.5;cursor:not-allowed}
.test-btn.saving{background:linear-gradient(135deg,#059669,#10b981)}
.test-result{padding:14px 18px;background:rgba(30,41,59,.5);border-radius:10px;font-size:.85rem;line-height:1.6;flex:1;min-width:200px;border:1px solid rgba(148,163,184,.08)}

/* Template editor */
.tpl-list{list-style:none;display:flex;flex-direction:column;gap:8px}
.tpl-item{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;background:rgba(30,41,59,.5);border-radius:10px;border:1px solid rgba(148,163,184,.08)}
.tpl-item .name{font-weight:600;font-size:.95rem;color:#e2e8f0}
.tpl-item .tpl-feature{font-size:.78rem;color:#818cf8;margin-left:8px}
.tpl-item .size{font-size:.8rem;color:#64748b}
.tpl-item .edit-btn{padding:6px 16px;border:1px solid rgba(99,102,241,.3);border-radius:8px;background:transparent;color:#818cf8;font-size:.82rem;cursor:pointer;transition:all .2s;text-decoration:none}
.tpl-item .edit-btn:hover{background:rgba(99,102,241,.15);text-decoration:none}

.editor-wrap textarea{width:100%;min-height:400px;padding:18px;border:1px solid rgba(148,163,184,.15);border-radius:10px;background:rgba(30,41,59,.6);color:#e2e8f0;font-family:'JetBrains Mono','Fira Code',monospace;font-size:.86rem;line-height:1.7;resize:vertical;outline:none;tab-size:4;transition:border .2s}
.editor-wrap textarea:focus{border-color:#818cf8}
.editor-actions{display:flex;align-items:center;gap:12px;margin-top:14px}
.editor-actions .save-btn{padding:10px 28px;border:none;border-radius:10px;background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;font-size:.9rem;font-weight:600;cursor:pointer;transition:opacity .2s}
.editor-actions .save-btn:hover{opacity:.9}
.editor-actions .back-link{color:#94a3b8;font-size:.88rem}
.save-msg{font-size:.85rem;margin-left:8px}
.var-table{width:100%;border-collapse:collapse;margin:16px 0}
.var-table th,.var-table td{text-align:left;padding:8px 12px;border-bottom:1px solid rgba(148,163,184,.08);font-size:.82rem}
.var-table th{color:#94a3b8;font-weight:500;font-size:.72rem;text-transform:uppercase;letter-spacing:.5px}
.var-table td code{background:rgba(99,102,241,.12);padding:2px 6px;border-radius:4px;font-size:.8rem;color:#818cf8}
.feature-banner{background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.2);border-radius:10px;padding:14px 18px;margin-bottom:18px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.feature-banner .fb-icon{font-size:1.3rem}
.feature-banner .fb-text{font-size:.88rem;color:#c7d2fe}
.feature-banner .fb-text strong{color:#e2e8f0}

@keyframes spin{to{transform:rotate(360deg)}}
.spinner{display:inline-block;width:16px;height:16px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite}
"""


def _page(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — 再译管理后台</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>{_CSS}</style>
</head><body>{body}</body></html>"""


def _uptime() -> str:
    secs = int(time.time() - _start_time)
    if secs < 60:
        return f"{secs}秒"
    mins = secs // 60
    if mins < 60:
        return f"{mins}分{secs%60}秒"
    hours = mins // 60
    return f"{hours}小时{mins%60}分"


def _mask_key(key_val: str) -> str:
    if not key_val or len(key_val) < 8:
        return "***"
    return key_val[:4] + "…" + key_val[-4:]


def _get_provider_info():
    """Return current LLM provider and status."""
    from services.llm import _llm_provider, _env
    provider = _llm_provider()
    key_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "qwen": "QWEN_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    has_key = False
    if provider in key_map:
        has_key = bool(_env(key_map[provider]))
    status = "active" if has_key else ("mock" if provider == "mock" else "error")
    return provider, status


def _feature_status():
    """Determine each AI feature's status."""
    provider, api_status = _get_provider_info()
    statuses = {}
    for f in AI_FEATURES:
        if api_status == "active":
            # Vision features need specific provider support
            if "Vision" in f["call_type"] and provider in ("openai",):
                statuses[f["id"]] = "mock"
            else:
                statuses[f["id"]] = "active"
        elif api_status == "mock":
            statuses[f["id"]] = "mock"
        else:
            statuses[f["id"]] = "error"
    return statuses


# Template → Feature mapping
_TPL_FEATURE_MAP = {f["template"]: f for f in AI_FEATURES if f["template"]}


# ── Routes ──────────────────────────────────────────────

@router.get("", response_class=HTMLResponse, include_in_schema=False)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def admin_login_page(request: Request):
    if _check_session(request):
        return RedirectResponse("/admin/dashboard", status_code=302)
    body = """
    <div class="login-wrap"><div class="login-card">
        <h1>🔧 再译 AI 操控中心</h1>
        <p>请输入管理密码以继续</p>
        <form method="POST" action="/admin/login">
            <input type="password" name="password" placeholder="管理密码" autofocus required>
            <button type="submit">登 录</button>
        </form>
    </div></div>
    """
    return HTMLResponse(_page("登录", body))


@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def admin_login(request: Request):
    form = await request.form()
    pwd = form.get("password", "")
    if pwd == ADMIN_PASSWORD:
        sid = _create_session()
        resp = RedirectResponse("/admin/dashboard", status_code=302)
        resp.set_cookie(SESSION_COOKIE, sid, httponly=True, max_age=SESSION_TTL, samesite="lax")
        return resp
    body = """
    <div class="login-wrap"><div class="login-card">
        <h1>🔧 再译 AI 操控中心</h1>
        <p>请输入管理密码以继续</p>
        <form method="POST" action="/admin/login">
            <input type="password" name="password" placeholder="管理密码" autofocus required>
            <button type="submit">登 录</button>
        </form>
        <div class="login-error">❌ 密码错误，请重试</div>
    </div></div>
    """
    return HTMLResponse(_page("登录", body))


@router.get("/logout", include_in_schema=False)
def admin_logout(request: Request):
    sid = request.cookies.get(SESSION_COOKIE, "")
    _admin_sessions.pop(sid, None)
    resp = RedirectResponse("/admin", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard(request: Request):
    if not _check_session(request):
        return RedirectResponse("/admin", status_code=302)

    import sqlite3
    from db.auth_db import AUTH_DB_PATH

    # ── System stats ──
    uptime = _uptime()
    db_status, db_class = "正常", "ok"
    try:
        conn = sqlite3.connect(os.getenv("DB_PATH", "./db/xiaotiao.db"))
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        db_status, db_class = "异常", "err"

    # ── Provider info ──
    provider, api_status = _get_provider_info()
    provider_display = provider.upper() if provider != "mock" else "Mock"
    api_class = "ok" if api_status == "active" else ("warn" if api_status == "mock" else "err")
    api_text = "已连接" if api_status == "active" else ("模拟模式" if api_status == "mock" else "未配置")

    # ── User stats ──
    user_count, session_count = 0, 0
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row
        user_count = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        session_count = conn.execute("SELECT COUNT(*) as c FROM auth_sessions WHERE expires_at > ?", (now,)).fetchone()["c"]
        conn.close()
    except Exception:
        pass

    # ── Feature status ──
    statuses = _feature_status()

    # ── Build feature cards ──
    feature_cards = ""
    for f in AI_FEATURES:
        st = statuses.get(f["id"], "error")
        card_class = "type-json"
        if "Stream" in f["call_type"]:
            card_class = "type-stream"
        elif "Vision" in f["call_type"]:
            card_class = "type-vision"

        tpl_tag = ""
        if f["template"]:
            tpl_tag = f'<a class="fc-tag tpl" href="/admin/prompts/{f["template"]}">📄 {f["template"]}</a>'
        else:
            tpl_tag = '<span class="fc-tag inline">⚡ 内联 prompt</span>'

        feature_cards += f"""
        <div class="feature-card {card_class}">
            <div class="fc-header">
                <div class="fc-title">
                    <span class="icon">{f["icon"]}</span>
                    <span class="name">{f["name"]}</span>
                </div>
                <div class="fc-status {st}" title="{'正常运行' if st == 'active' else ('模拟模式' if st == 'mock' else '不可用')}"></div>
            </div>
            <div class="fc-frontend">
                <span>🖥️ {f["frontend"]}</span>
                <span class="arrow">→</span>
                <span>{f["frontend_action"]}</span>
            </div>
            <div class="fc-desc">{f["description"]}</div>
            <div class="fc-meta">
                <span class="fc-tag call">⚡ {f["call_type"]}</span>
                {tpl_tag}
            </div>
        </div>
        """

    # ── Build API provider cards ──
    providers_info = [
        ("gemini", "Gemini", "gemini-2.5-flash", "GEMINI_API_KEY", True, True, True),
        ("openai", "OpenAI", "gpt-4o-mini", "OPENAI_API_KEY", True, True, False),
        ("qwen", "Qwen (通义千问)", "qwen-plus", "QWEN_API_KEY", True, False, True),
        ("anthropic", "Anthropic", "claude-3-7-sonnet", "ANTHROPIC_API_KEY", True, True, True),
    ]
    api_cards = ""
    for pid, pname, default_model, key_env, has_json, has_stream, has_vision in providers_info:
        key_val = os.getenv(key_env, "").strip()
        selected = "selected" if provider == pid else ""
        key_display = _mask_key(key_val) if key_val else ""
        key_placeholder = "未配置" if not key_val else ""
        status_html = f'<div class="key-status ok">✓ 已配置</div>' if key_val else f'<div class="key-status" style="color:#64748b">未配置</div>'

        model_env = f"{pid.upper()}_MODEL"
        model_val = os.getenv(model_env, "").strip() or default_model

        api_cards += f"""
        <div class="api-card {selected}" data-provider="{pid}">
            <div class="provider-name">{pname}</div>
            <div class="provider-models">默认模型: {default_model}</div>
            <div class="caps">
                <span class="cap {'y' if has_json else 'n'}">JSON {'✓' if has_json else '✗'}</span>
                <span class="cap {'y' if has_stream else 'n'}">Stream {'✓' if has_stream else '✗'}</span>
                <span class="cap {'y' if has_vision else 'n'}">Vision {'✓' if has_vision else '✗'}</span>
            </div>
            <input class="api-input" type="password" id="key-{pid}" placeholder="API Key {key_placeholder}" value="{html_mod.escape(key_val)}" autocomplete="off">
            <input class="api-input" type="text" id="model-{pid}" placeholder="模型名称" value="{html_mod.escape(model_val)}" autocomplete="off">
            {status_html}
        </div>
        """

    # ── Template list ──
    templates = []
    if PROMPTS_DIR.exists():
        for fp in sorted(PROMPTS_DIR.glob("*.j2")):
            size = fp.stat().st_size
            feat = _TPL_FEATURE_MAP.get(fp.name)
            feat_label = f'<span class="tpl-feature">→ {feat["frontend"]} · {feat["name"]}</span>' if feat else ""
            templates.append(
                f'<li class="tpl-item">'
                f'<div><span class="name">{fp.name}</span>{feat_label}'
                f'<span class="size"> — {size} bytes</span></div>'
                f'<a class="edit-btn" href="/admin/prompts/{fp.name}">编辑</a>'
                f'</li>'
            )

    tpl_html = "\n".join(templates) if templates else '<li class="tpl-item"><span class="name" style="color:#64748b">未找到模板文件</span></li>'

    body = f"""
    <div class="dash">
        <div class="dash-header">
            <h1>🔧 再译 AI 操控中心</h1>
            <a href="/admin/logout" class="logout">退出登录</a>
        </div>

        <!-- Stats Row -->
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-label">运行时长</div>
                <div class="stat-value">{uptime}</div>
                <div class="stat-sub" style="color:#64748b">自上次启动</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">数据库</div>
                <div class="stat-value {db_class}">{db_status}</div>
                <div class="stat-sub" style="color:#64748b">SQLite</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">AI 引擎</div>
                <div class="stat-value" style="font-size:1.1rem">{provider_display}</div>
                <div class="stat-sub {api_class}">{api_text}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">用户</div>
                <div class="stat-value">{user_count}</div>
                <div class="stat-sub" style="color:#64748b">活跃会话: {session_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">AI 功能</div>
                <div class="stat-value">{len(AI_FEATURES)}</div>
                <div class="stat-sub ok">{sum(1 for s in statuses.values() if s == 'active')} 正常运行</div>
            </div>
        </div>

        <!-- Panel 1: AI Feature Map -->
        <div class="section">
            <h2>🗺️ AI 功能地图</h2>
            <div class="subtitle">可视化展示每个 AI 功能连接的前端模块、提示词模板和调用方式。绿灯=正常，黄灯=模拟，红灯=不可用。</div>
            <div class="feature-grid">
                {feature_cards}
            </div>
        </div>

        <!-- Panel 2: API Config -->
        <div class="section">
            <h2>⚙️ API 配置</h2>
            <div class="subtitle">选择 AI 服务商并配置 API Key。修改后点击「保存配置」即可生效。</div>
            <div class="api-grid">
                {api_cards}
            </div>
            <div class="test-area">
                <button class="test-btn saving" id="btn-save-config" onclick="saveConfig()">💾 保存配置</button>
                <button class="test-btn" id="btn-test" onclick="testConnection()">🔍 测试连接</button>
                <div class="test-result" id="test-result" style="color:#64748b">点击「测试连接」验证 API 可用性</div>
            </div>
        </div>

        <!-- Panel 3: Prompt Templates -->
        <div class="section">
            <h2>📝 提示词模板</h2>
            <div class="subtitle">点击「编辑」可修改 AI 的行为逻辑。每个模板旁标注了它驱动的前端功能。</div>
            <ul class="tpl-list">
                {tpl_html}
            </ul>
        </div>
    </div>

    <script>
    // Select provider on card click
    document.querySelectorAll('.api-card').forEach(card => {{
        card.addEventListener('click', function(e) {{
            if (e.target.tagName === 'INPUT') return;
            document.querySelectorAll('.api-card').forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
        }});
    }});

    async function saveConfig() {{
        const btn = document.getElementById('btn-save-config');
        const result = document.getElementById('test-result');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 保存中...';

        const selected = document.querySelector('.api-card.selected');
        const provider = selected ? selected.dataset.provider : '';

        const config = {{}};
        ['gemini', 'openai', 'qwen', 'anthropic'].forEach(p => {{
            const keyEl = document.getElementById('key-' + p);
            const modelEl = document.getElementById('model-' + p);
            if (keyEl && keyEl.value) config[p + '_key'] = keyEl.value;
            if (modelEl && modelEl.value) config[p + '_model'] = modelEl.value;
        }});
        config.provider = provider;

        try {{
            const resp = await fetch('/admin/api/save-config', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(config),
                credentials: 'include'
            }});
            const data = await resp.json();
            if (data.ok) {{
                result.innerHTML = '<span class="ok">✅ 配置已保存。重启服务后生效。</span>';
            }} else {{
                result.innerHTML = '<span class="err">❌ ' + (data.error || '保存失败') + '</span>';
            }}
        }} catch(e) {{
            result.innerHTML = '<span class="err">❌ 网络错误: ' + e.message + '</span>';
        }}
        btn.disabled = false;
        btn.innerHTML = '💾 保存配置';
    }}

    async function testConnection() {{
        const btn = document.getElementById('btn-test');
        const result = document.getElementById('test-result');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 测试中...';
        result.innerHTML = '<span style="color:#94a3b8">正在向 AI API 发送测试请求...</span>';

        try {{
            const resp = await fetch('/admin/api/test-connection', {{
                method: 'POST',
                credentials: 'include'
            }});
            const data = await resp.json();
            if (data.ok) {{
                result.innerHTML = '<span class="ok">✅ 连接成功</span>'
                    + '<br>提供商: <strong>' + data.provider + '</strong>'
                    + '<br>响应时间: <strong>' + data.latency_ms + 'ms</strong>'
                    + (data.response_preview ? '<br>预览: <em>' + data.response_preview + '</em>' : '');
            }} else {{
                result.innerHTML = '<span class="err">❌ 连接失败</span>'
                    + '<br>提供商: ' + (data.provider || 'unknown')
                    + '<br>错误: <span style="color:#f87171">' + (data.error || '未知错误') + '</span>';
            }}
        }} catch(e) {{
            result.innerHTML = '<span class="err">❌ 网络错误: ' + e.message + '</span>';
        }}
        btn.disabled = false;
        btn.innerHTML = '🔍 测试连接';
    }}
    </script>
    """
    return HTMLResponse(_page("AI 操控中心", body))


# ── API Endpoints ────────────────────────────────────────

@router.post("/api/test-connection", include_in_schema=False)
async def test_connection(request: Request):
    if not _check_session(request):
        return JSONResponse({"ok": False, "error": "未登录"}, status_code=401)

    from services.llm import _llm_provider
    provider = _llm_provider()

    if provider == "mock":
        return JSONResponse({
            "ok": True,
            "provider": "mock",
            "latency_ms": 1,
            "response_preview": "Mock 模式无需真实 API，返回模拟数据",
        })

    start = time.time()
    try:
        from services.llm import call_claude_json
        result = await call_claude_json(
            "You are a test assistant. Reply with a simple JSON object.",
            'Return {"status":"ok","message":"连接成功"} exactly.',
            max_tokens=100,
        )
        latency = int((time.time() - start) * 1000)
        preview = json.dumps(result, ensure_ascii=False)[:120]
        return JSONResponse({
            "ok": True,
            "provider": provider,
            "latency_ms": latency,
            "response_preview": preview,
        })
    except Exception as exc:
        latency = int((time.time() - start) * 1000)
        return JSONResponse({
            "ok": False,
            "provider": provider,
            "latency_ms": latency,
            "error": str(exc)[:300],
        })


@router.post("/api/save-config", include_in_schema=False)
async def save_config(request: Request):
    if not _check_session(request):
        return JSONResponse({"ok": False, "error": "未登录"}, status_code=401)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "无效的 JSON"})

    # Read existing .env
    env_lines = []
    existing_keys = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                key = stripped.split("=", 1)[0].strip()
                existing_keys[key] = len(env_lines)
            env_lines.append(line)

    # Map request body to env vars
    updates = {}
    if body.get("provider"):
        updates["LLM_PROVIDER"] = body["provider"]
    for pid in ("gemini", "openai", "qwen", "anthropic"):
        key_val = body.get(f"{pid}_key", "").strip()
        if key_val:
            updates[f"{pid.upper()}_API_KEY"] = key_val
        model_val = body.get(f"{pid}_model", "").strip()
        if model_val:
            updates[f"{pid.upper()}_MODEL"] = model_val

    # Update or append
    for k, v in updates.items():
        line_content = f'{k}="{v}"' if " " in v else f"{k}={v}"
        if k in existing_keys:
            env_lines[existing_keys[k]] = line_content
        else:
            env_lines.append(line_content)

    # Write back
    ENV_PATH.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    return JSONResponse({"ok": True, "updated": list(updates.keys())})


@router.get("/api/status", include_in_schema=False)
def api_status(request: Request):
    if not _check_session(request):
        return JSONResponse({"ok": False, "error": "未登录"}, status_code=401)
    provider, api_st = _get_provider_info()
    statuses = _feature_status()
    return JSONResponse({
        "provider": provider,
        "api_status": api_st,
        "features": {f["id"]: {"name": f["name"], "status": statuses.get(f["id"], "error")} for f in AI_FEATURES},
    })


# ── Template Editor ──────────────────────────────────────

@router.get("/prompts/{filename}", response_class=HTMLResponse, include_in_schema=False)
def edit_prompt(filename: str, request: Request):
    if not _check_session(request):
        return RedirectResponse("/admin", status_code=302)

    if not filename.endswith(".j2") or "/" in filename or "\\" in filename:
        return HTMLResponse(_page("错误", '<div class="login-wrap"><div class="login-card"><h1>❌ 无效文件名</h1></div></div>'))

    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        return HTMLResponse(_page("错误", '<div class="login-wrap"><div class="login-card"><h1>❌ 模板不存在</h1></div></div>'))

    content = filepath.read_text(encoding="utf-8")
    escaped = html_mod.escape(content)

    # Feature info banner
    feat = _TPL_FEATURE_MAP.get(filename)
    banner = ""
    if feat:
        banner = f"""
        <div class="feature-banner">
            <span class="fb-icon">{feat["icon"]}</span>
            <div class="fb-text">
                此模板驱动 <strong>{feat["frontend"]} → {feat["name"]}</strong> 功能
                <br>前端路径: <code>{feat["frontend_path"]}</code> · 调用方式: <strong>{feat["call_type"]}</strong>
            </div>
        </div>
        """
        # Variables table
        if feat["variables"]:
            var_descriptions = {
                "topics": "用户选择的主题列表",
                "domains": "用户选择的学科领域",
                "level": "难度等级: beginner / intermediate / advanced",
                "article_length": "目标文章长度（字数）",
                "db_words": "从用户生词本中提取的单词列表",
                "new_word_count": "需要引入的新词汇数量",
                "style_modifier": "文章风格提示（来自数据库配置）",
                "rag_context": "RAG 检索到的参考上下文",
                "source_text": "用户输入的源文本",
                "analysis_mode": "分析模式: plain / legal_focus",
                "grounded_context": "RAG 系统注入的上下文",
                "direction": "翻译方向: zh_to_en / en_to_zh",
                "user_translation": "用户自译文本（可选）",
                "domain": "提取词汇的领域聚焦",
                "extracted_text": "从文档提取的文本内容",
            }
            rows = ""
            for v in feat["variables"]:
                desc = var_descriptions.get(v, "—")
                rows += f"<tr><td><code>{{{{{v}}}}}</code></td><td>{desc}</td></tr>"
            banner += f"""
            <table class="var-table">
                <thead><tr><th>模板变量</th><th>说明</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            """

    body = f"""
    <div class="dash">
        <div class="dash-header">
            <h1>📝 编辑模板: {filename}</h1>
            <a href="/admin/logout" class="logout">退出登录</a>
        </div>
        <div class="section editor-wrap">
            {banner}
            <form method="POST" action="/admin/prompts/{filename}" id="edit-form">
                <textarea name="content" id="editor" spellcheck="false">{escaped}</textarea>
                <div class="editor-actions">
                    <button type="submit" class="save-btn" id="save-btn">💾 保存模板</button>
                    <a href="/admin/dashboard" class="back-link">← 返回操控中心</a>
                    <span class="save-msg" id="save-msg"></span>
                </div>
            </form>
        </div>
    </div>
    <script>
    document.getElementById('editor').addEventListener('keydown', function(e) {{
        if (e.key === 'Tab') {{
            e.preventDefault();
            let s = this.selectionStart, end = this.selectionEnd;
            this.value = this.value.substring(0, s) + '    ' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = s + 4;
        }}
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {{
            e.preventDefault();
            document.getElementById('edit-form').submit();
        }}
    }});
    </script>
    """
    return HTMLResponse(_page(f"编辑 {filename}", body))


@router.post("/prompts/{filename}", response_class=HTMLResponse, include_in_schema=False)
async def save_prompt(filename: str, request: Request):
    if not _check_session(request):
        return RedirectResponse("/admin", status_code=302)

    if not filename.endswith(".j2") or "/" in filename or "\\" in filename:
        return HTMLResponse(_page("错误", '<div class="login-wrap"><div class="login-card"><h1>❌ 无效文件名</h1></div></div>'))

    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        return HTMLResponse(_page("错误", '<div class="login-wrap"><div class="login-card"><h1>❌ 模板不存在</h1></div></div>'))

    form = await request.form()
    content = form.get("content", "")
    filepath.write_text(content, encoding="utf-8")

    escaped = html_mod.escape(content)

    feat = _TPL_FEATURE_MAP.get(filename)
    banner = ""
    if feat:
        banner = f"""
        <div class="feature-banner">
            <span class="fb-icon">{feat["icon"]}</span>
            <div class="fb-text">
                此模板驱动 <strong>{feat["frontend"]} → {feat["name"]}</strong> 功能
                <br>前端路径: <code>{feat["frontend_path"]}</code> · 调用方式: <strong>{feat["call_type"]}</strong>
            </div>
        </div>
        """

    body = f"""
    <div class="dash">
        <div class="dash-header">
            <h1>📝 编辑模板: {filename}</h1>
            <a href="/admin/logout" class="logout">退出登录</a>
        </div>
        <div class="section editor-wrap">
            {banner}
            <form method="POST" action="/admin/prompts/{filename}" id="edit-form">
                <textarea name="content" id="editor" spellcheck="false">{escaped}</textarea>
                <div class="editor-actions">
                    <button type="submit" class="save-btn" id="save-btn">💾 保存模板</button>
                    <a href="/admin/dashboard" class="back-link">← 返回操控中心</a>
                    <span class="save-msg" id="save-msg" style="color:#4ade80">✅ 已保存，模板已热更新生效</span>
                </div>
            </form>
        </div>
    </div>
    <script>
    document.getElementById('editor').addEventListener('keydown', function(e) {{
        if (e.key === 'Tab') {{
            e.preventDefault();
            let s = this.selectionStart, end = this.selectionEnd;
            this.value = this.value.substring(0, s) + '    ' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = s + 4;
        }}
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {{
            e.preventDefault();
            document.getElementById('edit-form').submit();
        }}
    }});
    </script>
    """
    return HTMLResponse(_page(f"编辑 {filename}", body))
