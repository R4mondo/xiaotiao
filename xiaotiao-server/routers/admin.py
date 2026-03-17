"""
Admin Dashboard — 管理后台仪表盘

通过 /admin 访问，固定密码保护。
提供系统状态、用户统计、提示词模板编辑等功能。
"""

import hashlib
import os
import secrets
import time
from pathlib import Path

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/admin", tags=["管理后台"])

# ── Config ──────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "xiaotiao2026")
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_start_time = time.time()

# Simple in-memory session store for admin
_admin_sessions: dict[str, float] = {}
SESSION_COOKIE = "admin_sid"
SESSION_TTL = 3600 * 8  # 8 hours


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

.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.login-card{background:rgba(15,23,42,.85);border:1px solid rgba(99,102,241,.25);border-radius:16px;padding:48px 40px;width:100%;max-width:400px;backdrop-filter:blur(24px)}
.login-card h1{font-size:1.5rem;font-weight:700;margin-bottom:8px;background:linear-gradient(135deg,#818cf8,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.login-card p{color:#94a3b8;font-size:.875rem;margin-bottom:28px}
.login-card input{width:100%;padding:12px 16px;border:1px solid rgba(148,163,184,.2);border-radius:10px;background:rgba(30,41,59,.6);color:#e2e8f0;font-size:.95rem;outline:none;transition:border .2s}
.login-card input:focus{border-color:#818cf8}
.login-card button{width:100%;padding:12px;margin-top:16px;border:none;border-radius:10px;background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;font-size:.95rem;font-weight:600;cursor:pointer;transition:opacity .2s}
.login-card button:hover{opacity:.9}
.login-error{color:#f87171;font-size:.85rem;margin-top:12px;text-align:center}

.dash{max-width:1100px;margin:0 auto;padding:24px 20px 60px}
.dash-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:32px;flex-wrap:wrap;gap:12px}
.dash-header h1{font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,#818cf8,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.dash-header .logout{padding:8px 18px;border:1px solid rgba(148,163,184,.2);border-radius:8px;background:transparent;color:#94a3b8;font-size:.85rem;cursor:pointer;transition:all .2s}
.dash-header .logout:hover{border-color:#f87171;color:#f87171}

.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:32px}
.card{background:rgba(15,23,42,.7);border:1px solid rgba(99,102,241,.15);border-radius:14px;padding:24px;backdrop-filter:blur(12px);transition:border-color .2s}
.card:hover{border-color:rgba(99,102,241,.4)}
.card-label{font-size:.78rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.card-value{font-size:1.5rem;font-weight:700;color:#e2e8f0}
.card-sub{font-size:.8rem;color:#64748b;margin-top:6px}
.card-ok{color:#4ade80}
.card-warn{color:#fbbf24}
.card-err{color:#f87171}

.section{background:rgba(15,23,42,.7);border:1px solid rgba(99,102,241,.15);border-radius:14px;padding:28px;margin-bottom:24px;backdrop-filter:blur(12px)}
.section h2{font-size:1.15rem;font-weight:700;margin-bottom:18px;color:#c7d2fe}

.tpl-list{list-style:none;display:flex;flex-direction:column;gap:8px}
.tpl-item{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;background:rgba(30,41,59,.5);border-radius:10px;border:1px solid rgba(148,163,184,.08)}
.tpl-item .name{font-weight:600;font-size:.95rem;color:#e2e8f0}
.tpl-item .size{font-size:.8rem;color:#64748b}
.tpl-item .edit-btn{padding:6px 16px;border:1px solid rgba(99,102,241,.3);border-radius:8px;background:transparent;color:#818cf8;font-size:.82rem;cursor:pointer;transition:all .2s;text-decoration:none}
.tpl-item .edit-btn:hover{background:rgba(99,102,241,.15);text-decoration:none}

.env-table{width:100%;border-collapse:collapse}
.env-table th,.env-table td{text-align:left;padding:10px 14px;border-bottom:1px solid rgba(148,163,184,.08);font-size:.88rem}
.env-table th{color:#94a3b8;font-weight:500;font-size:.78rem;text-transform:uppercase;letter-spacing:.5px}
.env-table td{color:#e2e8f0}
.env-table .mask{color:#64748b;font-style:italic}

.editor-wrap{margin-top:0}
.editor-wrap textarea{width:100%;min-height:450px;padding:18px;border:1px solid rgba(148,163,184,.15);border-radius:10px;background:rgba(30,41,59,.6);color:#e2e8f0;font-family:'JetBrains Mono','Fira Code','Cascadia Code',monospace;font-size:.88rem;line-height:1.7;resize:vertical;outline:none;tab-size:4;transition:border .2s}
.editor-wrap textarea:focus{border-color:#818cf8}
.editor-actions{display:flex;align-items:center;gap:12px;margin-top:14px}
.editor-actions .save-btn{padding:10px 28px;border:none;border-radius:10px;background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;font-size:.9rem;font-weight:600;cursor:pointer;transition:opacity .2s}
.editor-actions .save-btn:hover{opacity:.9}
.editor-actions .back-link{color:#94a3b8;font-size:.88rem}
.save-msg{font-size:.85rem;margin-left:8px}
"""

# ── HTML Helpers ────────────────────────────────────────


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


# ── Routes ──────────────────────────────────────────────

@router.get("", response_class=HTMLResponse, include_in_schema=False)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def admin_login_page(request: Request):
    if _check_session(request):
        return RedirectResponse("/admin/dashboard", status_code=302)
    body = """
    <div class="login-wrap"><div class="login-card">
        <h1>🔧 再译管理后台</h1>
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
        <h1>🔧 再译管理后台</h1>
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

    db_status = "正常"
    db_class = "card-ok"
    try:
        conn = sqlite3.connect(os.getenv("DB_PATH", "./db/xiaotiao.db"))
        conn.execute("SELECT 1")
        conn.close()
    except Exception:
        db_status = "异常"
        db_class = "card-err"

    # ── LLM config ──
    provider = os.getenv("LLM_PROVIDER", "").strip().lower() or "auto-detect"
    key_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "qwen": "QWEN_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    api_key_status = "未配置"
    api_key_class = "card-warn"
    actual_provider = provider if provider != "auto-detect" else ""
    if actual_provider in key_map:
        kv = os.getenv(key_map[actual_provider], "").strip()
        if kv:
            api_key_status = "已配置"
            api_key_class = "card-ok"
    elif provider == "auto-detect":
        for p, k in key_map.items():
            if os.getenv(k, "").strip():
                api_key_status = f"已配置 ({p})"
                api_key_class = "card-ok"
                actual_provider = p
                break
    elif provider == "mock":
        api_key_status = "Mock 模式"
        api_key_class = "card-warn"

    # ── User stats ──
    user_count = 0
    session_count = 0
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row
        user_count = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        session_count = conn.execute(
            "SELECT COUNT(*) as c FROM auth_sessions WHERE expires_at > ?", (now,)
        ).fetchone()["c"]
        conn.close()
    except Exception:
        pass

    # ── Prompt templates ──
    templates = []
    if PROMPTS_DIR.exists():
        for f in sorted(PROMPTS_DIR.glob("*.j2")):
            size = f.stat().st_size
            templates.append(
                f'<li class="tpl-item">'
                f'<div><span class="name">{f.name}</span>'
                f'<span class="size"> — {size} bytes</span></div>'
                f'<a class="edit-btn" href="/admin/prompts/{f.name}">编辑</a>'
                f'</li>'
            )

    tpl_html = "\n".join(templates) if templates else '<li class="tpl-item"><span class="name" style="color:#64748b">未找到模板文件</span></li>'

    # ── Env table ──
    env_rows = ""
    env_keys = [
        ("LLM_PROVIDER", "LLM 提供商"),
        ("GEMINI_API_KEY", "Gemini API Key"),
        ("OPENAI_API_KEY", "OpenAI API Key"),
        ("QWEN_API_KEY", "Qwen API Key"),
        ("ANTHROPIC_API_KEY", "Anthropic API Key"),
        ("DB_PATH", "数据库路径"),
        ("CORS_ORIGINS", "CORS 来源"),
    ]
    for key, label in env_keys:
        val = os.getenv(key, "")
        if "KEY" in key and val:
            display = f'<span>{_mask_key(val)}</span>'
        elif val:
            display = val
        else:
            display = '<span class="mask">未设置</span>'
        env_rows += f"<tr><td>{label}</td><td><code>{key}</code></td><td>{display}</td></tr>\n"

    body = f"""
    <div class="dash">
        <div class="dash-header">
            <h1>🔧 再译管理后台</h1>
            <a href="/admin/logout" class="logout">退出登录</a>
        </div>

        <div class="cards">
            <div class="card">
                <div class="card-label">运行时长</div>
                <div class="card-value">{uptime}</div>
                <div class="card-sub">自上次启动以来</div>
            </div>
            <div class="card">
                <div class="card-label">数据库状态</div>
                <div class="card-value {db_class}">{db_status}</div>
                <div class="card-sub">SQLite</div>
            </div>
            <div class="card">
                <div class="card-label">LLM 提供商</div>
                <div class="card-value" style="font-size:1.2rem">{provider}</div>
                <div class="card-sub {api_key_class}">{api_key_status}</div>
            </div>
            <div class="card">
                <div class="card-label">注册用户</div>
                <div class="card-value">{user_count}</div>
                <div class="card-sub">活跃会话: {session_count}</div>
            </div>
        </div>

        <div class="section">
            <h2>📝 提示词模板</h2>
            <ul class="tpl-list">
                {tpl_html}
            </ul>
        </div>

        <div class="section">
            <h2>⚙️ 环境配置</h2>
            <table class="env-table">
                <thead><tr><th>配置项</th><th>变量名</th><th>值</th></tr></thead>
                <tbody>{env_rows}</tbody>
            </table>
        </div>
    </div>
    """
    return HTMLResponse(_page("仪表盘", body))


@router.get("/prompts/{filename}", response_class=HTMLResponse, include_in_schema=False)
def edit_prompt(filename: str, request: Request):
    if not _check_session(request):
        return RedirectResponse("/admin", status_code=302)

    # Security: only allow .j2 files in prompts dir
    if not filename.endswith(".j2") or "/" in filename or "\\" in filename:
        return HTMLResponse(_page("错误", '<div class="login-wrap"><div class="login-card"><h1>❌ 无效文件名</h1></div></div>'))

    filepath = PROMPTS_DIR / filename
    if not filepath.exists():
        return HTMLResponse(_page("错误", '<div class="login-wrap"><div class="login-card"><h1>❌ 模板不存在</h1></div></div>'))

    content = filepath.read_text(encoding="utf-8")
    # Escape for HTML textarea
    import html
    escaped = html.escape(content)

    body = f"""
    <div class="dash">
        <div class="dash-header">
            <h1>📝 编辑模板: {filename}</h1>
            <a href="/admin/logout" class="logout">退出登录</a>
        </div>
        <div class="section editor-wrap">
            <form method="POST" action="/admin/prompts/{filename}" id="edit-form">
                <textarea name="content" id="editor" spellcheck="false">{escaped}</textarea>
                <div class="editor-actions">
                    <button type="submit" class="save-btn" id="save-btn">💾 保存</button>
                    <a href="/admin/dashboard" class="back-link">← 返回仪表盘</a>
                    <span class="save-msg" id="save-msg"></span>
                </div>
            </form>
        </div>
    </div>
    <script>
    // Tab key support in textarea
    document.getElementById('editor').addEventListener('keydown', function(e) {{
        if (e.key === 'Tab') {{
            e.preventDefault();
            let s = this.selectionStart, end = this.selectionEnd;
            this.value = this.value.substring(0, s) + '    ' + this.value.substring(end);
            this.selectionStart = this.selectionEnd = s + 4;
        }}
        // Ctrl+S save
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

    import html
    escaped = html.escape(content)

    body = f"""
    <div class="dash">
        <div class="dash-header">
            <h1>📝 编辑模板: {filename}</h1>
            <a href="/admin/logout" class="logout">退出登录</a>
        </div>
        <div class="section editor-wrap">
            <form method="POST" action="/admin/prompts/{filename}" id="edit-form">
                <textarea name="content" id="editor" spellcheck="false">{escaped}</textarea>
                <div class="editor-actions">
                    <button type="submit" class="save-btn" id="save-btn">💾 保存</button>
                    <a href="/admin/dashboard" class="back-link">← 返回仪表盘</a>
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
