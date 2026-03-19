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
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "xiaotiao")
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
        "how_it_works": [
            {"who": "user", "text": "👤 用户选择主题、领域、难度"},
            {"who": "system", "text": "⚙️ 系统读取用户生词本"},
            {"who": "system", "text": "📄 填入提示词模板 topic_generate.j2"},
            {"who": "ai", "text": "🤖 AI 生成含指定词汇的文章(JSON)"},
            {"who": "system", "text": "📤 返回文章 + 词汇高亮到前端"},
        ],
        "requires": ["🔑 AI API Key(如 Gemini/OpenAI)", "📄 模板文件 topic_generate.j2", "📚 用户生词本数据"],
        "variables": ["topics", "domains", "level", "article_length", "db_words", "new_word_count", "style_modifier", "rag_context"],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "template", "label": "模板渲染", "test": "template", "file": "topic_generate.j2"},
            {"step": "llm", "label": "AI 生成", "test": "llm_json"},
            {"step": "parse", "label": "JSON 解析", "test": "auto"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
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
        "how_it_works": [
            {"who": "user", "text": "👤 用户粘贴英文文章"},
            {"who": "user", "text": "👤 选择分析模式(通用/法律)"},
            {"who": "system", "text": "📄 填入提示词模板 article_analyze.j2"},
            {"who": "ai", "text": "🤖 AI 逐段翻译 + 术语提取(JSON)"},
            {"who": "system", "text": "📤 前端渲染双语对照阅读"},
        ],
        "requires": ["🔑 AI API Key(如 Gemini/OpenAI)", "📄 模板文件 article_analyze.j2"],
        "variables": ["source_text", "analysis_mode", "grounded_context"],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "template", "label": "模板渲染", "test": "template", "file": "article_analyze.j2"},
            {"step": "llm", "label": "AI 解读", "test": "llm_json"},
            {"step": "parse", "label": "JSON 解析", "test": "auto"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
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
        "how_it_works": [
            {"who": "user", "text": "👤 用户输入源文 + 选择翻译方向"},
            {"who": "user", "text": "👤 (可选) 输入自己的翻译"},
            {"who": "system", "text": "📄 填入提示词模板 translation.j2"},
            {"who": "ai", "text": "🤖 AI 生成三种风格译文 + 点评(JSON)"},
            {"who": "system", "text": "📤 前端展示多风格翻译对比"},
        ],
        "requires": ["🔑 AI API Key(如 Gemini/OpenAI)", "📄 模板文件 translation.j2"],
        "variables": ["source_text", "direction", "user_translation"],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "template", "label": "模板渲染", "test": "template", "file": "translation.j2"},
            {"step": "llm", "label": "AI 翻译", "test": "llm_json"},
            {"step": "parse", "label": "JSON 解析", "test": "auto"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
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
        "how_it_works": [
            {"who": "user", "text": "👤 用户上传图片/PDF/文档"},
            {"who": "system", "text": "⚙️ OCR 识别 / 文件解析取文本"},
            {"who": "system", "text": "📄 填入提示词模板 multimodal.j2"},
            {"who": "ai", "text": "🤖 AI Vision 提取专业词汇(JSON)"},
            {"who": "system", "text": "📤 前端展示提取结果"},
        ],
        "requires": ["🔑 AI API Key(支持 Vision)", "📄 模板文件 multimodal.j2", "📁 文件解析服务"],
        "variables": ["domain", "extracted_text"],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "ocr", "label": "文件处理", "test": "route"},
            {"step": "template", "label": "模板渲染", "test": "template", "file": "multimodal.j2"},
            {"step": "llm", "label": "AI 提取", "test": "llm_json"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
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
        "how_it_works": [
            {"who": "user", "text": "👤 用户打开论文 → 点击AI功能"},
            {"who": "system", "text": "⚙️ 提取论文段落 + 构建 Prompt"},
            {"who": "ai", "text": "🤖 AI 流式输出(SSE Stream)"},
            {"who": "system", "text": "📤 前端实时渲染AI回复"},
        ],
        "requires": ["🔑 AI API Key(支持 Stream)", "📡 SSE 流式传输支持"],
        "variables": [],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "prompt", "label": "构建 Prompt", "test": "route"},
            {"step": "llm", "label": "AI 流式生成", "test": "llm_stream"},
            {"step": "stream", "label": "SSE 推流", "test": "auto"},
            {"step": "response", "label": "前端渲染", "test": "auto"},
        ],
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
        "how_it_works": [
            {"who": "user", "text": "👤 用户粘贴文本 / 拍照上传"},
            {"who": "system", "text": "⚙️ 文本预处理 / 图片OCR"},
            {"who": "ai", "text": "🤖 AI 提取生词 + 释义(JSON)"},
            {"who": "system", "text": "💾 写入生词本数据库"},
            {"who": "system", "text": "📤 前端显示导入结果"},
        ],
        "requires": ["🔑 AI API Key(支持 Vision 可选)", "💾 SQLite 数据库"],
        "variables": [],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "process", "label": "文本/图片处理", "test": "route"},
            {"step": "llm", "label": "AI 提取", "test": "llm_json"},
            {"step": "save", "label": "写入数据库", "test": "auto"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
    },
    {
        "id": "concept_analysis",
        "name": "概念解析",
        "icon": "🔎",
        "frontend": "选词工具",
        "frontend_path": "/#/translation",
        "frontend_action": "选中英文单词 → AI 语义解析",
        "template": None,
        "call_type": "JSON",
        "description": "对选中的英文词汇或短语进行语义解析，返回音标、释义、例句和关联词汇",
        "how_it_works": [
            {"who": "user", "text": "👤 用户在页面上选中英文单词"},
            {"who": "system", "text": "⚙️ 发送词汇到后端 /vocab/concept"},
            {"who": "ai", "text": "🤖 AI 返回释义、例句、关联词(JSON)"},
            {"who": "system", "text": "📤 前端弹窗展示解析结果"},
        ],
        "requires": ["🔑 AI API Key(如 Gemini/OpenAI)"],
        "variables": [],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "llm", "label": "AI 解析", "test": "llm_json"},
            {"step": "parse", "label": "JSON 解析", "test": "auto"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
    },
    {
        "id": "paper_reader",
        "name": "PDF 阅读器 AI 概要",
        "icon": "📖",
        "frontend": "论文阅读器",
        "frontend_path": "/#/papers/:id/read",
        "frontend_action": "滚动阅读 PDF → AI 自动生成逐页概要",
        "template": None,
        "call_type": "Stream",
        "description": "在 PDF 阅读器中，AI 自动为每一页生成阅读概要和关键要点",
        "how_it_works": [
            {"who": "user", "text": "👤 用户在 PDF 阅读器中滚动阅读"},
            {"who": "system", "text": "⚙️ 检测到新页面可见，提取页面文本"},
            {"who": "ai", "text": "🤖 AI 流式生成页面概要"},
            {"who": "system", "text": "📤 实时显示在侧边栏"},
        ],
        "requires": ["🔑 AI API Key(支持 Stream)"],
        "variables": [],
        "pipeline": [
            {"step": "request", "label": "页面文本提取", "test": "route"},
            {"step": "llm", "label": "AI 概要生成", "test": "llm_stream"},
            {"step": "response", "label": "侧边栏展示", "test": "auto"},
        ],
    },
    {
        "id": "paper_chat",
        "name": "论文对话问答",
        "icon": "💬",
        "frontend": "论文详情/阅读器",
        "frontend_path": "/#/papers/:id",
        "frontend_action": "基于论文内容提问 → AI 回答",
        "template": None,
        "call_type": "Stream",
        "description": "用户可基于论文内容向 AI 提问，获得上下文相关的回答",
        "how_it_works": [
            {"who": "user", "text": "👤 用户输入问题"},
            {"who": "system", "text": "⚙️ 构建包含论文上下文的 Prompt"},
            {"who": "ai", "text": "🤖 AI 流式回答"},
            {"who": "system", "text": "📤 实时渲染回答"},
        ],
        "requires": ["🔑 AI API Key(支持 Stream)"],
        "variables": [],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "llm", "label": "AI 对话", "test": "llm_stream"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
    },
    {
        "id": "paper_translate",
        "name": "论文段落翻译",
        "icon": "🌍",
        "frontend": "论文阅读器",
        "frontend_path": "/#/papers/:id/read",
        "frontend_action": "选中段落 → AI 翻译",
        "template": None,
        "call_type": "Stream",
        "description": "选中论文中的段落文本，AI 流式翻译为中文",
        "how_it_works": [
            {"who": "user", "text": "👤 用户选中文本"},
            {"who": "ai", "text": "🤖 AI 流式翻译"},
            {"who": "system", "text": "📤 弹窗展示翻译结果"},
        ],
        "requires": ["🔑 AI API Key(支持 Stream)"],
        "variables": [],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "llm", "label": "AI 翻译", "test": "llm_stream"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
    },
    {
        "id": "paper_glossary",
        "name": "论文术语提取",
        "icon": "📋",
        "frontend": "论文阅读器",
        "frontend_path": "/#/papers/:id/read",
        "frontend_action": "选中段落 → AI 提取专业术语",
        "template": None,
        "call_type": "Stream",
        "description": "从选中的论文段落中提取专业术语及完整释义",
        "how_it_works": [
            {"who": "user", "text": "👤 用户选中文本"},
            {"who": "ai", "text": "🤖 AI 提取术语并给出释义"},
            {"who": "system", "text": "📤 弹窗展示术语列表"},
        ],
        "requires": ["🔑 AI API Key(支持 Stream)"],
        "variables": [],
        "pipeline": [
            {"step": "request", "label": "前端请求", "test": "route"},
            {"step": "llm", "label": "AI 提取", "test": "llm_stream"},
            {"step": "response", "label": "返回前端", "test": "auto"},
        ],
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
.fc-status.untested{background:#64748b;box-shadow:0 0 6px rgba(100,116,139,.3)}
.fc-frontend{display:flex;align-items:center;gap:6px;font-size:.82rem;color:#94a3b8;margin-bottom:8px;padding:6px 10px;background:rgba(99,102,241,.08);border-radius:8px}
.fc-frontend .arrow{color:#6366f1;font-size:.75rem}
.fc-desc{font-size:.8rem;color:#64748b;margin-bottom:8px;line-height:1.5}
.fc-error{font-size:.75rem;color:#f87171;margin-bottom:8px;padding:6px 10px;background:rgba(248,113,113,.06);border-radius:6px;word-break:break-all}
.fc-ok{font-size:.75rem;color:#4ade80;margin-bottom:8px}
.fc-untested{font-size:.75rem;color:#64748b;margin-bottom:8px;font-style:italic}
.fc-latency{font-size:.7rem;color:#475569;margin-top:4px}
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

/* Pipeline flow */
.pipeline{display:flex;align-items:center;gap:0;margin:12px 0 8px;padding:8px 0;overflow-x:auto}
.pipe-step{display:flex;flex-direction:column;align-items:center;gap:4px;min-width:60px;flex-shrink:0;position:relative}
.pipe-dot{width:14px;height:14px;border-radius:50%;border:2px solid rgba(148,163,184,.2);background:#1e293b;transition:all .4s}
.pipe-dot.active{background:#4ade80;border-color:#4ade80;box-shadow:0 0 8px rgba(74,222,128,.5)}
.pipe-dot.error{background:#f87171;border-color:#f87171;box-shadow:0 0 8px rgba(248,113,113,.5)}
.pipe-dot.testing{background:#fbbf24;border-color:#fbbf24;box-shadow:0 0 8px rgba(251,191,36,.4);animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.pipe-label{font-size:.65rem;color:#64748b;text-align:center;max-width:70px;line-height:1.2}
.pipe-arrow{color:#334155;font-size:.7rem;margin:0 2px;flex-shrink:0;align-self:flex-start;margin-top:3px}
.pipe-err-msg{font-size:.68rem;color:#f87171;margin-top:4px;max-width:100%;word-break:break-all;text-align:center;padding:4px 8px;background:rgba(248,113,113,.06);border-radius:4px}

/* Prompt flow diagram */
.prompt-flow{margin-bottom:0}
.flow-header{display:flex;align-items:center;gap:10px;margin-bottom:18px;padding:12px 16px;background:rgba(99,102,241,.08);border-radius:10px;border:1px solid rgba(99,102,241,.15)}
.flow-icon{font-size:1.4rem}
.flow-title{font-size:1rem;font-weight:600;color:#e2e8f0}
.flow-call-type{margin-left:auto;font-size:.75rem;padding:3px 10px;border-radius:6px;background:rgba(99,102,241,.15);color:#818cf8;font-weight:500}
.flow-diagram{display:flex;align-items:stretch;gap:0;overflow-x:auto;padding:4px 0}
.flow-col{flex:1;min-width:180px;display:flex;flex-direction:column;gap:12px}
.flow-col.center-col{flex:0.8}
.flow-arrow-col{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:60px;gap:4px;padding:0 4px}
.flow-arrow-line{width:2px;height:30px;background:linear-gradient(180deg,rgba(99,102,241,.3),rgba(99,102,241,.1))}
.flow-arrow-label{font-size:.65rem;color:#818cf8;text-align:center;white-space:nowrap}
.flow-arrow-tip{font-size:1.2rem;color:#818cf8}
.flow-panel{border-radius:10px;padding:14px;border:1px solid rgba(148,163,184,.1);transition:border-color .2s}
.flow-panel:hover{border-color:rgba(99,102,241,.3)}
.flow-panel.user-panel{background:rgba(59,130,246,.06);border-color:rgba(59,130,246,.15)}
.flow-panel.system-panel{background:rgba(245,158,11,.04);border-color:rgba(245,158,11,.12)}
.flow-panel.template-panel{background:rgba(139,92,246,.06);border-color:rgba(139,92,246,.15)}
.flow-panel.ai-panel{background:rgba(16,185,129,.06);border-color:rgba(16,185,129,.15)}
.flow-panel.output-panel{background:rgba(99,102,241,.04);border-color:rgba(99,102,241,.12)}
.flow-panel-title{font-size:.88rem;font-weight:600;color:#e2e8f0;margin-bottom:4px}
.flow-panel-sub{font-size:.72rem;color:#64748b;margin-bottom:10px}
.flow-panel-note{font-size:.72rem;color:#818cf8;margin-top:10px;text-align:center}
.flow-template-preview{font-size:.75rem;color:#94a3b8;line-height:1.5;padding:8px 10px;background:rgba(0,0,0,.15);border-radius:6px}
.flow-var-item{padding:8px 10px;border-radius:8px;margin-bottom:6px;display:flex;flex-direction:column;gap:2px}
.flow-var-item.user{background:rgba(59,130,246,.08)}
.flow-var-item.system{background:rgba(245,158,11,.06)}
.flow-var-item code{font-size:.78rem;color:#818cf8;background:rgba(99,102,241,.12);padding:1px 6px;border-radius:3px;align-self:flex-start}
.flow-var-desc{font-size:.75rem;color:#cbd5e1;margin-top:2px}
.flow-var-ui{font-size:.68rem;color:#64748b}
.flow-var-example{font-size:.65rem;color:#475569}
.flow-var-example em{color:#94a3b8;font-style:normal}
.flow-var-empty{font-size:.75rem;color:#475569;font-style:italic;padding:8px 0}
.flow-legend{display:flex;gap:18px;margin-top:14px;padding:8px 12px;border-top:1px solid rgba(148,163,184,.08)}
.flow-legend-item{font-size:.72rem;color:#64748b;display:flex;align-items:center;gap:6px}
.flow-dot{width:10px;height:10px;border-radius:50%}
.flow-dot.user{background:#3b82f6}
.flow-dot.system{background:#f59e0b}

/* How-it-works workflow steps */
.fc-desc{font-size:.78rem;color:#94a3b8;margin:8px 0 4px;line-height:1.4}
.hiw-section,.req-section,.pipeline-section{margin:10px 0 6px;padding:10px 12px;background:rgba(0,0,0,.12);border-radius:8px}
.hiw-title,.req-title{font-size:.75rem;font-weight:600;color:#94a3b8;margin-bottom:8px}
.hiw-steps{display:flex;flex-direction:column;gap:0}
.hiw-step{display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:6px;font-size:.78rem;color:#cbd5e1}
.hiw-step.hiw-user{background:rgba(59,130,246,.08)}
.hiw-step.hiw-ai{background:rgba(74,222,128,.08)}
.hiw-step.hiw-system{background:rgba(245,158,11,.06)}
.hiw-num{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.65rem;font-weight:700;flex-shrink:0}
.hiw-user .hiw-num{background:rgba(59,130,246,.2);color:#60a5fa}
.hiw-ai .hiw-num{background:rgba(74,222,128,.2);color:#4ade80}
.hiw-system .hiw-num{background:rgba(245,158,11,.15);color:#fbbf24}
.hiw-text{flex:1}
.hiw-connector{display:flex;justify-content:center;height:8px}
.hiw-connector::before{content:'';display:block;width:2px;height:100%;background:rgba(148,163,184,.15)}
.req-list{display:flex;flex-wrap:wrap;gap:6px}
.req-item{font-size:.72rem;padding:3px 10px;border-radius:12px;background:rgba(99,102,241,.08);color:#a5b4fc;border:1px solid rgba(99,102,241,.12)}

/* API assignment section */
.api-assign-section{margin:10px 0 6px;padding:10px 12px;background:rgba(16,185,129,.04);border-radius:8px;border:1px solid rgba(16,185,129,.1)}
.api-assign-header{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
.api-badge-active{font-size:.72rem;padding:2px 10px;border-radius:10px;background:rgba(16,185,129,.15);color:#34d399;font-weight:600}
.api-badge-none{font-size:.72rem;padding:2px 10px;border-radius:10px;background:rgba(239,68,68,.12);color:#f87171;font-weight:600}
.api-override{font-size:.65rem;color:#fbbf24;background:rgba(251,191,36,.08);padding:1px 6px;border-radius:6px}
.api-default{font-size:.65rem;color:#64748b;background:rgba(100,116,139,.08);padding:1px 6px;border-radius:6px}
.api-assign-body{display:flex;align-items:center;gap:8px}
.api-select{flex:1;padding:6px 10px;border-radius:6px;background:#1e293b;color:#e2e8f0;border:1px solid rgba(148,163,184,.15);font-size:.78rem;outline:none;min-width:0;max-width:100%}
.api-select:focus{border-color:#6366f1}
.api-select optgroup{color:#94a3b8;font-weight:600;font-size:.72rem}
.api-select option{color:#e2e8f0;padding:4px;font-size:.78rem}
.api-save-msg{font-size:.7rem;transition:opacity .3s}
/* Expandable requirements */
.req-expand{cursor:pointer;user-select:none}
.req-expand-icon{transition:transform .2s;display:inline-block}
.req-expand-icon.open{transform:rotate(90deg)}
.req-detail{display:none;margin-top:8px;padding:10px 12px;background:rgba(99,102,241,.04);border-radius:8px;border:1px solid rgba(99,102,241,.06);font-size:.72rem;color:#94a3b8}
.req-detail.show{display:block}
.req-model-tag{display:inline-block;padding:1px 6px;border-radius:4px;margin:2px;font-size:.68rem;background:rgba(99,102,241,.08);color:#a5b4fc}
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
    """Return each AI feature's status from last real test, or 'untested'."""
    statuses = {}
    for f in AI_FEATURES:
        result = _last_test_results.get(f["id"])
        if result:
            statuses[f["id"]] = result
        else:
            # Not yet tested — show as untested
            provider, _ = _get_provider_info()
            statuses[f["id"]] = {
                "status": "untested",
                "message": "未测试 — 点击「逐项测试」查看真实状态",
                "tested_at": None,
                "latency_ms": None,
            }
    return statuses


# In-memory store of real test results
_last_test_results: dict[str, dict] = {}


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
        <p>请输入管理员用户名和密码</p>
        <form method="POST" action="/admin/login">
            <input type="text" name="username" placeholder="用户名" autofocus required>
            <input type="password" name="password" placeholder="密码" required>
            <button type="submit">登 录</button>
        </form>
    </div></div>
    """
    return HTMLResponse(_page("登录", body))


@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def admin_login(request: Request):
    form = await request.form()
    username = form.get("username", "")
    pwd = form.get("password", "")
    if username == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
        sid = _create_session()
        resp = RedirectResponse("/admin/dashboard", status_code=302)
        resp.set_cookie(SESSION_COOKIE, sid, httponly=True, max_age=SESSION_TTL, samesite="lax")
        return resp
    body = """
    <div class="login-wrap"><div class="login-card">
        <h1>🔧 再译 AI 操控中心</h1>
        <p>请输入管理员用户名和密码</p>
        <form method="POST" action="/admin/login">
            <input type="text" name="username" placeholder="用户名" autofocus required>
            <input type="password" name="password" placeholder="密码" required>
            <button type="submit">登 录</button>
        </form>
        <div class="login-error">❌ 用户名或密码错误，请重试</div>
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
    active_count = sum(1 for s in statuses.values() if isinstance(s, dict) and s.get('status') == 'active')
    error_count = sum(1 for s in statuses.values() if isinstance(s, dict) and s.get('status') == 'error')
    untested_count = sum(1 for s in statuses.values() if isinstance(s, dict) and s.get('status') == 'untested')

    # ── Per-feature provider assignments ──
    from services.llm import get_feature_provider, get_compatible_providers, get_all_feature_assignments, PROVIDER_CAPABILITIES
    assignments = get_all_feature_assignments()

    # ── Build feature cards with pipeline ──
    feature_cards = ""
    for f in AI_FEATURES:
        st_info = statuses.get(f["id"], {"status": "untested"})
        st = st_info.get("status", "untested") if isinstance(st_info, dict) else "untested"
        card_class = "type-json"
        if "Stream" in (f.get("call_type") or ""):
            card_class = "type-stream"
        elif "Vision" in (f.get("call_type") or ""):
            card_class = "type-vision"

        tpl_tag = ""
        if f["template"]:
            tpl_tag = f'<a class="fc-tag tpl" href="/admin/prompts/{f["template"]}">📄 {f["template"]}</a>'
        else:
            tpl_tag = '<span class="fc-tag inline">⚡ 内联 prompt</span>'

        # Build how-it-works visual steps
        how_html = ""
        for idx, step in enumerate(f.get("how_it_works", [])):
            who = step.get("who", "system")
            color_cls = "hiw-user" if who == "user" else ("hiw-ai" if who == "ai" else "hiw-system")
            connector = '<div class="hiw-connector"></div>' if idx < len(f.get("how_it_works", [])) - 1 else ""
            how_html += f'<div class="hiw-step {color_cls}"><span class="hiw-num">{idx+1}</span><span class="hiw-text">{step["text"]}</span></div>{connector}'

        # Build requires HTML with expandable API key details
        fid = f["id"]
        compatible = get_compatible_providers(fid)
        req_html = ""
        for r in f.get("requires", []):
            req_html += f'<span class="req-item">{r}</span>'
        # Add expandable API key details section
        api_detail_models = ""
        for p in compatible:
            if not p["compatible"]:
                continue
            key_status = '✅ 已配置' if p.get('has_key') else '❌ 未配置'
            model_tags = ''.join(f'<span class="req-model-tag">{m}</span>' for m in p.get('models', []))
            api_detail_models += f'<div style="margin:6px 0"><strong style="color:#e2e8f0">{p["name"]}</strong> <span style="font-size:.65rem">{key_status}</span><br>{model_tags}</div>'
        req_html += f'''
            <div class="req-expand" onclick="toggleReqDetail('{fid}')">
                <span class="req-item" style="cursor:pointer">🔑 <span class="req-expand-icon" id="req-icon-{fid}">▶</span> 查看可用 API 及模型详情</span>
            </div>
            <div class="req-detail" id="req-detail-{fid}">
                <div style="margin-bottom:6px;color:#a5b4fc;font-weight:600">该功能兼容的 API 提供商和模型：</div>
                {api_detail_models}
            </div>'''

        # Build per-feature API assignment selector
        assign = assignments.get(fid, {})
        current_provider = assign.get("provider", "mock")
        is_override = assign.get("is_override", False)
        cur_caps = PROVIDER_CAPABILITIES.get(current_provider, {})
        cur_name = cur_caps.get("name", current_provider.upper()) if cur_caps else current_provider.upper()
        cur_badge_cls = "api-badge-active" if current_provider != "mock" else "api-badge-none"
        override_tag = '<span class="api-override">✏️ 手动指定</span>' if is_override else '<span class="api-default">🔄 全局默认</span>'

        # Build dropdown options — only show providers that have keys configured
        options_html = f'<option value="default"{"" if is_override else " selected"}>🔄 使用全局默认</option>'
        for p in compatible:
            if not p["compatible"] or not p["has_key"]:
                continue
            options_html += f'<optgroup label="{p["name"]}">'
            for model in p.get('models', []):
                val = f'{p["id"]}:{model}'
                sel = ' selected' if is_override and p['id'] == current_provider else ''
                options_html += f'<option value="{p["id"]}"{sel}>  {model}</option>'
            options_html += '</optgroup>'

        api_section = f'''
            <div class="api-assign-section" id="api-section-{fid}">
                <div class="api-assign-header">
                    <span class="hiw-title">🔗 AI API 分配</span>
                    <span class="{cur_badge_cls}">{cur_name}</span>
                    {override_tag}
                </div>
                <div class="api-assign-body">
                    <select class="api-select" id="api-select-{fid}" onchange="setFeatureProvider('{fid}', this.value)">
                        {options_html}
                    </select>
                    <span class="api-save-msg" id="api-msg-{fid}"></span>
                </div>
            </div>'''

        # Build pipeline HTML
        pipeline_html = ""
        step_results = st_info.get("steps", {}) if isinstance(st_info, dict) else {}
        for i, ps in enumerate(f.get("pipeline", [])):
            step_st = step_results.get(ps["step"], "untested")
            dot_class = ""
            if isinstance(step_st, dict):
                dot_class = "active" if step_st.get("ok") else "error"
            elif step_st == "active":
                dot_class = "active"
            elif step_st == "error":
                dot_class = "error"
            if i > 0:
                pipeline_html += '<span class="pipe-arrow">→</span>'
            pipeline_html += f'<div class="pipe-step"><div class="pipe-dot {dot_class}" id="dot-{f["id"]}-{ps["step"]}"></div><div class="pipe-label">{ps["label"]}</div></div>'

        # Error message if any
        err_html = ""
        if st == "error" and isinstance(st_info, dict):
            msg = html_mod.escape(str(st_info.get("message", ""))[:200])
            err_html = f'<div class="pipe-err-msg" id="err-{f["id"]}">❌ {msg}</div>'
        elif st == "untested":
            err_html = f'<div class="pipe-err-msg" id="err-{f["id"]}" style="color:#64748b;background:transparent">⚪ 未测试 — 点击「逐项测试」查看真实状态</div>'
        elif st == "active":
            latency = st_info.get("latency_ms", "") if isinstance(st_info, dict) else ""
            err_html = f'<div class="pipe-err-msg" id="err-{f["id"]}" style="color:#4ade80;background:transparent">✅ 全部步骤正常{" · " + str(latency) + "ms" if latency else ""}</div>'

        feature_cards += f"""
        <div class="feature-card {card_class}" id="fc-{f['id']}">
            <div class="fc-header">
                <div class="fc-title">
                    <span class="icon">{f["icon"]}</span>
                    <span class="name">{f["name"]}</span>
                </div>
                <div class="fc-status {st}" id="dot-{f['id']}"></div>
            </div>
            <div class="fc-frontend">
                <span>🖥️ {f["frontend"]}</span>
                <span class="arrow">→</span>
                <span>{f["frontend_action"]}</span>
            </div>
            <div class="fc-desc">{f["description"]}</div>

            <div class="hiw-section">
                <div class="hiw-title">📋 工作流程（一步步如何运行）</div>
                <div class="hiw-steps">{how_html}</div>
            </div>

            <div class="req-section">
                <div class="req-title">🔧 技术需求（缺一不可）</div>
                <div class="req-list">{req_html}</div>
            </div>

            {api_section}

            <div class="pipeline-section">
                <div class="hiw-title">🚦 实时状态检测</div>
                <div class="pipeline" id="pipeline-{f['id']}">
                    {pipeline_html}
                </div>
                {err_html}
            </div>

            <div class="fc-meta">
                <span class="fc-tag call">⚡ {f["call_type"]}</span>
                {tpl_tag}
            </div>
        </div>
        """

    # ── Build API provider cards ──
    providers_info = [
        ("gemini", "Gemini", "gemini-2.5-flash", "GEMINI_API_KEY", "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta", True, True, True),
        ("openai", "OpenAI", "gpt-4o-mini", "OPENAI_API_KEY", "OPENAI_BASE_URL", "https://api.openai.com/v1", True, True, False),
        ("qwen", "Qwen (通义千问)", "qwen-plus", "QWEN_API_KEY", "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1", True, True, True),
        ("anthropic", "Anthropic", "claude-3-7-sonnet", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "https://api.anthropic.com", True, True, True),
    ]
    api_cards = ""

    # ── 蓝移API — dedicated card with dropdown model selection ──
    lanyi_key = os.getenv("LANYI_API_KEY", "").strip()
    lanyi_base = os.getenv("LANYI_BASE_URL", "").strip()
    lanyi_model_val = os.getenv("LANYI_MODEL", "").strip() or "claude-sonnet-4-20250514"
    lanyi_selected = "selected" if provider == "lanyi" else ""
    lanyi_status = f'<div class="key-status ok">✓ 已配置</div>' if lanyi_key else f'<div class="key-status" style="color:#64748b">未配置</div>'
    lanyi_models = [
        ("claude-opus-4-20250514", "Claude Opus 4 (最强)"),
        ("claude-sonnet-4-20250514", "Claude Sonnet 4 (推荐)"),
        ("claude-haiku-4-5-20250514", "Claude Haiku 4.5 (快速)"),
        ("claude-3-7-sonnet-20250219", "Claude 3.7 Sonnet"),
        ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
        ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
        ("gpt-4o", "GPT-4o"),
        ("gpt-4o-mini", "GPT-4o Mini (便宜)"),
        ("gpt-4-turbo", "GPT-4 Turbo"),
        ("gemini-2.5-flash", "Gemini 2.5 Flash"),
        ("gemini-2.0-flash", "Gemini 2.0 Flash"),
        ("deepseek-chat", "DeepSeek Chat"),
    ]
    lanyi_model_options = ""
    for mid, mname in lanyi_models:
        sel = 'selected' if mid == lanyi_model_val else ''
        lanyi_model_options += f'<option value="{mid}" {sel}>{mname}</option>'

    api_cards += f"""
    <div class="api-card {lanyi_selected}" data-provider="lanyi" style="border:2px solid rgba(99,102,241,.6);grid-column:1/-1;">
        <div class="provider-name" style="font-size:1.1rem;">🚀 蓝移API (中转代理)</div>
        <div class="provider-models" style="color:#a5b4fc">支持 Claude / GPT / Gemini / DeepSeek 全系列模型</div>
        <div class="caps">
            <span class="cap y">JSON ✓</span>
            <span class="cap y">Stream ✓</span>
            <span class="cap y">Vision ✓</span>
        </div>
        <input class="api-input" type="password" id="key-lanyi" placeholder="蓝移API Key" value="{html_mod.escape(lanyi_key)}" autocomplete="off">
        <div style="font-size:.7rem;color:#94a3b8;margin:4px 0 2px">选择模型：</div>
        <select class="api-input" id="model-lanyi" style="background:#1e293b;color:#e2e8f0;border:1px solid rgba(99,102,241,.3);border-radius:6px;padding:6px 8px;font-size:.8rem;cursor:pointer">
            {lanyi_model_options}
        </select>
        <input class="api-input" type="text" id="baseurl-lanyi" placeholder="API Base URL（留空=默认）" value="{html_mod.escape(lanyi_base)}" autocomplete="off" style="font-size:.75rem;color:#94a3b8">
        <div style="font-size:.65rem;color:#475569;margin-top:2px">默认: http://1.95.142.151:3000/v1</div>
        {lanyi_status}
    </div>
    """

    # ── Other providers ──
    for pid, pname, default_model, key_env, base_url_env, default_base_url, has_json, has_stream, has_vision in providers_info:
        key_val = os.getenv(key_env, "").strip()
        base_url_val = os.getenv(base_url_env, "").strip()
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
            <input class="api-input" type="text" id="baseurl-{pid}" placeholder="API Base URL（留空=官方默认）" value="{html_mod.escape(base_url_val)}" autocomplete="off" style="font-size:.75rem;color:#94a3b8">
            <div style="font-size:.65rem;color:#475569;margin-top:2px">默认: {default_base_url}</div>
            {status_html}
        </div>
        """

    # ── Template list — 3-layer tree view ──
    def _tpl_size(name):
        p = PROMPTS_DIR / name
        return p.stat().st_size if p.exists() else 0

    # Feature templates with their user input fields
    FEATURE_TEMPLATES = [
        {
            "file": "topic_generate.j2",
            "name": "📝 文章生成",
            "frontend": "话题探索 · 文章生成",
            "user_inputs": ["话题/标签", "文章长度", "难度等级", "文章风格", "DB 复习词", "新词数量"],
        },
        {
            "file": "translation.j2",
            "name": "🔤 翻译",
            "frontend": "翻译工作室 · 翻译练习",
            "user_inputs": ["原文文本", "翻译方向", "用户自译文本"],
        },
        {
            "file": "article_analyze.j2",
            "name": "🔍 文章解读",
            "frontend": "文章实验室 · 文章解读分析",
            "user_inputs": ["待分析文本", "分析模式", "RAG 检索上下文"],
        },
        {
            "file": "multimodal.j2",
            "name": "📷 多模态",
            "frontend": "多模态 · 多模态词汇提取",
            "user_inputs": ["上传图片/截图", "识别模式"],
        },
    ]

    feature_tree_items = ""
    for ft in FEATURE_TEMPLATES:
        size = _tpl_size(ft["file"])
        input_tags = "".join(f'<span class="prompt-input-tag">📥 {inp}</span>' for inp in ft["user_inputs"])
        feature_tree_items += f'''
            <div class="prompt-tree-leaf">
                <div class="prompt-tree-branch"></div>
                <div class="prompt-tree-card layer3">
                    <div class="prompt-tree-card-header">
                        <div>
                            <span class="prompt-layer-badge l3">第 3 层</span>
                            <span class="prompt-tree-name">{ft["name"]}</span>
                        </div>
                        <a class="edit-btn" href="/admin/prompts/{ft["file"]}">编辑</a>
                    </div>
                    <div class="prompt-tree-file">📄 {ft["file"]} <span class="size">— {size} bytes</span></div>
                    <div class="prompt-tree-frontend">🖥️ {ft["frontend"]}</div>
                    <div class="prompt-tree-inputs-title">用户输入的功能性参数：</div>
                    <div class="prompt-tree-inputs">{input_tags}</div>
                    <div class="prompt-assembly">
                        <div class="prompt-assembly-title">💡 最终提示词组装</div>
                        <div class="prompt-assembly-flow">
                            <span class="pa-box pa-l1">统摄层</span>
                            <span class="pa-arrow">+</span>
                            <span class="pa-box pa-l2">全局层</span>
                            <span class="pa-arrow">+</span>
                            <span class="pa-box pa-l3">功能层 系统部分</span>
                            <span class="pa-arrow">→</span>
                            <span class="pa-box pa-sys">System Prompt</span>
                        </div>
                        <div class="prompt-assembly-flow" style="margin-top:4px;">
                            <span class="pa-box pa-l3">功能层 用户部分</span>
                            <span class="pa-arrow">→</span>
                            <span class="pa-box pa-usr">User Prompt</span>
                        </div>
                    </div>
                </div>
            </div>'''

    body_tpl = f"""
        <!-- Panel 3: Prompt Templates — Tree View -->
        <div class="section">
            <h2>📝 提示词三层架构</h2>
            <div class="subtitle">树形展示三层提示词结构。每层都可由管理员编辑模版，用户输入的信息会自动填充到模版变量中。</div>

            <style>
            .prompt-tree {{
                position:relative;
                padding-left:0;
            }}
            .prompt-tree-root {{
                position:relative;
                padding-left:32px;
            }}
            .prompt-tree-root::before {{
                content:'';
                position:absolute;
                left:16px;
                top:42px;
                bottom:0;
                width:2px;
                background:linear-gradient(to bottom, #a78bfa, #6366f1, #3b82f6);
            }}
            .prompt-tree-card {{
                background:rgba(255,255,255,.04);
                border:1px solid rgba(255,255,255,.08);
                border-radius:10px;
                padding:14px 18px;
                margin-bottom:12px;
                transition:all .2s;
            }}
            .prompt-tree-card:hover {{
                background:rgba(255,255,255,.07);
                border-color:rgba(255,255,255,.15);
            }}
            .prompt-tree-card.layer1 {{
                border-left:3px solid #a78bfa;
                background:rgba(167,139,250,.06);
            }}
            .prompt-tree-card.layer2 {{
                border-left:3px solid #6366f1;
                background:rgba(99,102,241,.06);
            }}
            .prompt-tree-card.layer3 {{
                border-left:3px solid #3b82f6;
                background:rgba(59,130,246,.06);
            }}
            .prompt-tree-card-header {{
                display:flex;
                justify-content:space-between;
                align-items:center;
                margin-bottom:6px;
            }}
            .prompt-layer-badge {{
                display:inline-block;
                padding:2px 8px;
                border-radius:4px;
                font-size:.7rem;
                font-weight:700;
                margin-right:6px;
            }}
            .prompt-layer-badge.l1 {{ background:rgba(167,139,250,.2);color:#a78bfa; }}
            .prompt-layer-badge.l2 {{ background:rgba(99,102,241,.2);color:#818cf8; }}
            .prompt-layer-badge.l3 {{ background:rgba(59,130,246,.2);color:#60a5fa; }}
            .prompt-tree-name {{
                font-weight:700;
                color:#e2e8f0;
                font-size:.95rem;
            }}
            .prompt-tree-file {{
                font-size:.78rem;
                color:#94a3b8;
                margin-bottom:4px;
            }}
            .prompt-tree-file .size {{ color:#64748b; }}
            .prompt-tree-desc {{
                font-size:.8rem;
                color:#94a3b8;
                margin-bottom:6px;
            }}
            .prompt-tree-frontend {{
                font-size:.75rem;
                color:#64748b;
                margin-bottom:8px;
            }}
            .prompt-tree-inputs-title {{
                font-size:.72rem;
                color:#818cf8;
                font-weight:600;
                margin-bottom:4px;
            }}
            .prompt-tree-inputs {{
                display:flex;
                flex-wrap:wrap;
                gap:4px;
                margin-bottom:8px;
            }}
            .prompt-input-tag {{
                display:inline-block;
                padding:2px 8px;
                background:rgba(99,102,241,.1);
                border:1px solid rgba(99,102,241,.2);
                border-radius:4px;
                font-size:.68rem;
                color:#a5b4fc;
            }}
            .prompt-global-input-tag {{
                display:inline-block;
                padding:2px 8px;
                background:rgba(167,139,250,.1);
                border:1px solid rgba(167,139,250,.2);
                border-radius:4px;
                font-size:.68rem;
                color:#c4b5fd;
            }}
            .prompt-tree-leaf {{
                position:relative;
                padding-left:32px;
                margin-bottom:0;
            }}
            .prompt-tree-branch {{
                position:absolute;
                left:-16px;
                top:22px;
                width:16px;
                height:2px;
                background:#3b82f6;
            }}
            .prompt-tree-connector {{
                position:relative;
                margin-left:16px;
                padding-left:16px;
            }}
            .prompt-tree-connector::before {{
                content:'';
                position:absolute;
                left:0;
                top:0;
                bottom:0;
                width:2px;
                background:linear-gradient(to bottom, #6366f1, #3b82f6);
            }}
            .prompt-assembly {{
                background:rgba(0,0,0,.15);
                border-radius:6px;
                padding:8px 12px;
                margin-top:4px;
            }}
            .prompt-assembly-title {{
                font-size:.7rem;
                color:#94a3b8;
                margin-bottom:4px;
                font-weight:600;
            }}
            .prompt-assembly-flow {{
                display:flex;
                align-items:center;
                flex-wrap:wrap;
                gap:4px;
                font-size:.68rem;
            }}
            .pa-box {{
                padding:2px 8px;
                border-radius:4px;
                font-weight:600;
            }}
            .pa-l1 {{ background:rgba(167,139,250,.15);color:#c4b5fd; }}
            .pa-l2 {{ background:rgba(99,102,241,.15);color:#a5b4fc; }}
            .pa-l3 {{ background:rgba(59,130,246,.15);color:#93c5fd; }}
            .pa-sys {{ background:rgba(74,222,128,.15);color:#4ade80; }}
            .pa-usr {{ background:rgba(251,191,36,.15);color:#fbbf24; }}
            .pa-arrow {{ color:#64748b;font-weight:700; }}
            </style>

            <div class="prompt-tree">
                <!-- Layer 1: Meta System -->
                <div class="prompt-tree-root">
                    <div class="prompt-tree-card layer1">
                        <div class="prompt-tree-card-header">
                            <div>
                                <span class="prompt-layer-badge l1">第 1 层</span>
                                <span class="prompt-tree-name">🏛️ 统摄性提示词 — AI 行为总纲</span>
                            </div>
                            <a class="edit-btn" href="/admin/prompts/meta_system.j2">编辑</a>
                        </div>
                        <div class="prompt-tree-file">📄 meta_system.j2 <span class="size">— {_tpl_size('meta_system.j2')} bytes</span></div>
                        <div class="prompt-tree-desc">控制所有 AI 功能的输出格式、严谨性、安全性和一致性。修改此文件影响所有功能。</div>
                        <div class="prompt-tree-inputs-title">管理员可调整：</div>
                        <div class="prompt-tree-inputs">
                            <span class="prompt-input-tag">📋 输出格式规范</span>
                            <span class="prompt-input-tag">🎯 准确性要求</span>
                            <span class="prompt-input-tag">🛡️ 安全性约束</span>
                            <span class="prompt-input-tag">🌐 语言质量标准</span>
                            <span class="prompt-input-tag">📐 一致性规则</span>
                        </div>
                    </div>

                    <!-- Layer 2: Global Context -->
                    <div class="prompt-tree-card layer2">
                        <div class="prompt-tree-card-header">
                            <div>
                                <span class="prompt-layer-badge l2">第 2 层</span>
                                <span class="prompt-tree-name">🌍 全局性提示词 — 用户画像上下文</span>
                            </div>
                            <a class="edit-btn" href="/admin/prompts/global_context.j2">编辑</a>
                        </div>
                        <div class="prompt-tree-file">📄 global_context.j2 <span class="size">— {_tpl_size('global_context.j2')} bytes</span></div>
                        <div class="prompt-tree-desc">将用户的全局设置（画像）注入到所有 AI 功能中。用户修改画像后，所有功能自动同步。</div>
                        <div class="prompt-tree-inputs-title">用户画像数据（自动从设置页读取）：</div>
                        <div class="prompt-tree-inputs">
                            <span class="prompt-global-input-tag">🎓 备考目标 (CET4/CET6/IELTS/TOEFL...)</span>
                            <span class="prompt-global-input-tag">📚 学科领域</span>
                            <span class="prompt-global-input-tag">🔬 细分专业方向</span>
                            <span class="prompt-global-input-tag">💡 兴趣标签</span>
                            <span class="prompt-global-input-tag">📊 英语水平</span>
                        </div>
                    </div>

                    <!-- Layer 3: Feature Templates -->
                    <div style="margin-top:4px;margin-bottom:8px;">
                        <span class="prompt-layer-badge l3">第 3 层</span>
                        <span style="color:#94a3b8;font-size:.82rem;">功能性提示词 — 每个功能各自的参数和逻辑</span>
                    </div>
                    <div class="prompt-tree-connector">
                        {feature_tree_items}
                    </div>
                </div>
            </div>
        </div>"""

    # Inject into body between API config and database section
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
                <div class="stat-sub">{'<span class="ok">' + str(active_count) + ' 正常</span>' if active_count else ''}{' <span class="err">' + str(error_count) + ' 异常</span>' if error_count else ''}{' <span style="color:#64748b">' + str(untested_count) + ' 未测试</span>' if untested_count else ''}</div>
            </div>
        </div>

        <!-- Panel 1: AI Feature Map -->
        <div class="section">
            <h2>🗺️ AI 功能地图</h2>
            <div class="subtitle">
                可视化展示每个 AI 功能的真实运行状态。绿灯=正常，红灯=异常，灰灯=未测试。
                <button class="test-btn" style="display:inline-flex;padding:6px 16px;font-size:.8rem;margin-left:12px;vertical-align:middle" id="btn-test-all" onclick="testAllFeatures()">🧪 逐项测试全部功能</button>
            </div>
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

        {body_tpl}

        <!-- Panel 4: Database Viewer -->
        <div class="section">
            <h2>🗄️ 数据库管理</h2>
            <div class="subtitle">查看和管理所有数据库表的内容。</div>
            <a href="/admin/database" style="display:inline-block;padding:8px 20px;background:rgba(99,102,241,.15);color:#a5b4fc;border-radius:8px;text-decoration:none;font-size:.85rem;margin-top:8px;transition:background .2s" onmouseover="this.style.background='rgba(99,102,241,.25)'" onmouseout="this.style.background='rgba(99,102,241,.15)'">📋 打开数据库浏览器 →</a>
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
        ['lanyi', 'gemini', 'openai', 'qwen', 'anthropic'].forEach(p => {{
            const keyEl = document.getElementById('key-' + p);
            const modelEl = document.getElementById('model-' + p);
            const baseUrlEl = document.getElementById('baseurl-' + p);
            // Always send value (even empty) so server can delete removed keys
            if (keyEl) config[p + '_key'] = keyEl.value || '';
            if (modelEl) config[p + '_model'] = modelEl.value || '';
            if (baseUrlEl) config[p + '_base_url'] = (baseUrlEl.value || '').trim();
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
                result.innerHTML = '<span class="ok">✅ 配置已保存！正在刷新页面... 已更新: ' + (data.updated||[]).join(', ') + '</span>';
                setTimeout(() => location.reload(), 1200);
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

    async function testAllFeatures() {{
        const btn = document.getElementById('btn-test-all');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 正在逐项测试...';

        try {{
            const resp = await fetch('/admin/api/test-all-features', {{
                method: 'POST',
                credentials: 'include'
            }});
            const data = await resp.json();
            if (data.results) {{
                for (const [fid, result] of Object.entries(data.results)) {{
                    // Update main status dot
                    const mainDot = document.getElementById('dot-' + fid);
                    if (mainDot) {{
                        mainDot.className = 'fc-status ' + result.status;
                    }}
                    // Update pipeline step dots
                    if (result.steps) {{
                        for (const [stepId, stepResult] of Object.entries(result.steps)) {{
                            const dot = document.getElementById('dot-' + fid + '-' + stepId);
                            if (dot) {{
                                dot.className = 'pipe-dot ' + (stepResult.ok ? 'active' : 'error');
                            }}
                        }}
                    }}
                    // Update error message
                    const errEl = document.getElementById('err-' + fid);
                    if (errEl) {{
                        if (result.status === 'active') {{
                            errEl.style.color = '#4ade80';
                            errEl.style.background = 'transparent';
                            errEl.innerHTML = '✅ 全部步骤正常' + (result.latency_ms ? ' · ' + result.latency_ms + 'ms' : '');
                        }} else if (result.status === 'error') {{
                            errEl.style.color = '#f87171';
                            errEl.style.background = 'rgba(248,113,113,.06)';
                            errEl.innerHTML = '❌ ' + (result.message || '未知错误');
                        }}
                    }}
                }}
            }}
        }} catch(e) {{
            console.error('Test failed:', e);
        }}
        btn.disabled = false;
        btn.innerHTML = '🧪 逐项测试全部功能';
    }}

    function toggleReqDetail(fid) {{
        const detail = document.getElementById('req-detail-' + fid);
        const icon = document.getElementById('req-icon-' + fid);
        detail.classList.toggle('show');
        icon.classList.toggle('open');
    }}

    async function setFeatureProvider(featureId, provider) {{
        const msgEl = document.getElementById('api-msg-' + featureId);
        msgEl.textContent = '⏳ 保存中...';
        msgEl.style.color = '#94a3b8';
        try {{
            const resp = await fetch('/admin/api/set-feature-provider', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                credentials: 'include',
                body: JSON.stringify({{feature_id: featureId, provider: provider}})
            }});
            const data = await resp.json();
            if (data.ok) {{
                msgEl.textContent = '✅ 已保存: ' + data.provider_name;
                msgEl.style.color = '#4ade80';
                setTimeout(() => {{ msgEl.textContent = ''; }}, 3000);
            }} else {{
                msgEl.textContent = '❌ ' + (data.error || '保存失败');
                msgEl.style.color = '#f87171';
            }}
        }} catch(e) {{
            msgEl.textContent = '❌ 网络错误';
            msgEl.style.color = '#f87171';
        }}
    }}
    </script>
    """
    return HTMLResponse(_page("AI 操控中心", body))


# ── API Endpoints ────────────────────────────────────────

@router.post("/api/set-feature-provider", include_in_schema=False)
async def set_feature_provider_api(request: Request):
    if not _check_session(request):
        return JSONResponse({"ok": False, "error": "未登录"}, status_code=401)
    try:
        body = await request.json()
        feature_id = body.get("feature_id", "")
        provider = body.get("provider", "default")
        from services.llm import set_feature_provider, PROVIDER_CAPABILITIES
        ok = set_feature_provider(feature_id, provider)
        if ok:
            caps = PROVIDER_CAPABILITIES.get(provider, {})
            name = caps.get("name", "全局默认") if provider != "default" else "全局默认"
            return JSONResponse({"ok": True, "provider_name": name})
        else:
            return JSONResponse({"ok": False, "error": f"该 API 不兼容此功能所需的能力"})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)})


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


@router.post("/api/test-all-features", include_in_schema=False)
async def test_all_features(request: Request):
    """Test each AI feature's pipeline steps and return real status."""
    if not _check_session(request):
        return JSONResponse({"ok": False, "error": "未登录"}, status_code=401)

    from services.llm import _llm_provider

    provider = _llm_provider()
    results = {}

    for f in AI_FEATURES:
        fid = f["id"]
        steps = {}
        overall_ok = True
        error_msg = ""
        start = time.time()

        # Step 1: Route check (server is running → always OK)
        for ps in f.get("pipeline", []):
            if ps["test"] == "route":
                steps[ps["step"]] = {"ok": True}

        # Step 2: Template check
        for ps in f.get("pipeline", []):
            if ps["test"] == "template":
                tpl_file = ps.get("file", "")
                tpl_path = PROMPTS_DIR / tpl_file
                if tpl_path.exists():
                    try:
                        tpl_path.read_text(encoding="utf-8")
                        steps[ps["step"]] = {"ok": True}
                    except Exception as e:
                        steps[ps["step"]] = {"ok": False, "error": str(e)}
                        overall_ok = False
                        error_msg = f"模板文件读取失败: {e}"
                else:
                    steps[ps["step"]] = {"ok": False, "error": "文件不存在"}
                    overall_ok = False
                    error_msg = f"模板文件不存在: {tpl_file}"

        # Step 3: LLM call test
        if overall_ok:
            for ps in f.get("pipeline", []):
                if ps["test"] in ("llm_json", "llm_stream"):
                    if provider == "mock":
                        steps[ps["step"]] = {"ok": False, "error": "Mock 模式"}
                        overall_ok = False
                        error_msg = "AI 服务为 Mock 模式，未配置真实 API Key"
                    else:
                        try:
                            if ps["test"] == "llm_json":
                                from services.llm import call_claude_json
                                await call_claude_json(
                                    "You are a test. Reply with valid JSON.",
                                    'Return {"ok":true} exactly.',
                                    max_tokens=50,
                                )
                            else:  # llm_stream
                                from services.llm import call_claude_stream
                                chunks = []
                                async for chunk in call_claude_stream(
                                    "You are a test. Reply with one word.",
                                    "Say hello.",
                                    max_tokens=20,
                                ):
                                    chunks.append(chunk)
                                    if len(chunks) > 3:
                                        break
                            steps[ps["step"]] = {"ok": True}
                        except Exception as e:
                            steps[ps["step"]] = {"ok": False, "error": str(e)[:150]}
                            overall_ok = False
                            error_msg = str(e)[:200]

        # Auto steps: inherit from LLM result
        for ps in f.get("pipeline", []):
            if ps["test"] == "auto":
                steps[ps["step"]] = {"ok": overall_ok}

        latency = int((time.time() - start) * 1000)
        result = {
            "status": "active" if overall_ok else "error",
            "steps": steps,
            "latency_ms": latency,
            "message": error_msg if not overall_ok else "",
        }
        results[fid] = result
        _last_test_results[fid] = result

    return JSONResponse({"ok": True, "results": results})


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
    updates = {}  # keys to set
    deletes = []  # keys to remove from .env
    if body.get("provider"):
        updates["LLM_PROVIDER"] = body["provider"]
    for pid in ("lanyi", "gemini", "openai", "qwen", "anthropic"):
        key_field = f"{pid}_key"
        model_field = f"{pid}_model"
        base_url_field = f"{pid}_base_url"
        env_key = f"{pid.upper()}_API_KEY"
        env_model = f"{pid.upper()}_MODEL"
        env_base_url = f"{pid.upper()}_BASE_URL"

        # Handle key: set if non-empty, delete if empty and field was sent
        if key_field in body:
            val = (body[key_field] or "").strip()
            if val:
                updates[env_key] = val
            else:
                deletes.append(env_key)
        if model_field in body:
            val = (body[model_field] or "").strip()
            if val:
                updates[env_model] = val
            else:
                deletes.append(env_model)
        if base_url_field in body:
            val = (body[base_url_field] or "").strip()
            if val:
                updates[env_base_url] = val
            else:
                deletes.append(env_base_url)

    # Update or append values
    for k, v in updates.items():
        line_content = f'{k}="{v}"' if " " in v else f"{k}={v}"
        if k in existing_keys:
            env_lines[existing_keys[k]] = line_content
        else:
            env_lines.append(line_content)

    # Delete removed keys from .env lines
    for k in deletes:
        if k in existing_keys:
            idx = existing_keys[k]
            env_lines[idx] = f"# {k}="  # Comment out instead of removing to preserve line indices
        # Also remove from runtime environment
        os.environ.pop(k, None)

    # Write back
    ENV_PATH.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

    # Reload env into running process so changes take effect immediately
    for k, v in updates.items():
        os.environ[k] = v
    # Re-import dotenv to refresh all values
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH, override=True)
    except ImportError:
        pass  # dotenv not available, manual os.environ update above is sufficient

    changed = list(updates.keys()) + [f"{k} (已删除)" for k in deletes if k not in updates]
    return JSONResponse({"ok": True, "updated": changed})


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

    # Feature info and visual flow
    feat = _TPL_FEATURE_MAP.get(filename)

    # Enriched variable metadata: source ("user" = 用户前端输入, "system" = 后端系统注入)
    _VAR_META = {
        "topics": {"desc": "用户选择的主题列表", "source": "user", "ui": "主题选择器（Chip 多选）", "example": '["科技", "法律"]'},
        "domains": {"desc": "学科领域", "source": "user", "ui": "领域下拉菜单", "example": '["计算机", "法学"]'},
        "level": {"desc": "难度等级", "source": "user", "ui": "难度滑块", "example": "intermediate"},
        "article_length": {"desc": "目标文章长度", "source": "user", "ui": "长度选择器", "example": "300"},
        "db_words": {"desc": "用户生词本中的单词列表", "source": "system", "ui": "自动从数据库读取", "example": '["litigation", "verdict"]'},
        "new_word_count": {"desc": "需要引入的新词汇数量", "source": "system", "ui": "基于用户设置自动计算", "example": "5"},
        "style_modifier": {"desc": "文章风格提示", "source": "system", "ui": "数据库配置字段", "example": "academic, formal"},
        "rag_context": {"desc": "RAG 检索到的参考上下文", "source": "system", "ui": "后端向量检索结果", "example": "(相关文档片段)"},
        "source_text": {"desc": "用户输入的源文本", "source": "user", "ui": "文本输入框", "example": "The court ruled..."},
        "analysis_mode": {"desc": "分析模式", "source": "user", "ui": "模式切换按钮", "example": "legal_focus"},
        "grounded_context": {"desc": "RAG 系统注入的上下文", "source": "system", "ui": "后端自动检索注入", "example": "(知识库片段)"},
        "direction": {"desc": "翻译方向", "source": "user", "ui": "方向切换按钮", "example": "en_to_zh"},
        "user_translation": {"desc": "用户自译文本", "source": "user", "ui": "翻译输入框（可选）", "example": "法院裁定..."},
        "domain": {"desc": "提取词汇的领域聚焦", "source": "user", "ui": "领域输入框", "example": "法律"},
        "extracted_text": {"desc": "从文档提取的文本内容", "source": "system", "ui": "OCR / 文件解析结果", "example": "(提取的文字)"},
    }

    flow_html = ""
    if feat:
        # Split variables by source
        user_vars = [(v, _VAR_META.get(v, {})) for v in feat.get("variables", []) if _VAR_META.get(v, {}).get("source") == "user"]
        system_vars = [(v, _VAR_META.get(v, {})) for v in feat.get("variables", []) if _VAR_META.get(v, {}).get("source") == "system"]

        # User input panel
        user_items = ""
        for v, meta in user_vars:
            user_items += f'''<div class="flow-var-item user">
                <code>{{{{{v}}}}}</code>
                <span class="flow-var-desc">{meta.get("desc", v)}</span>
                <span class="flow-var-ui">🖥️ {meta.get("ui", "")}</span>
                <span class="flow-var-example">例: <em>{html_mod.escape(meta.get("example", ""))}</em></span>
            </div>'''

        # System input panel
        sys_items = ""
        for v, meta in system_vars:
            sys_items += f'''<div class="flow-var-item system">
                <code>{{{{{v}}}}}</code>
                <span class="flow-var-desc">{meta.get("desc", v)}</span>
                <span class="flow-var-ui">⚙️ {meta.get("ui", "")}</span>
                <span class="flow-var-example">例: <em>{html_mod.escape(meta.get("example", ""))}</em></span>
            </div>'''

        flow_html = f'''
        <div class="prompt-flow">
            <div class="flow-header">
                <span class="flow-icon">{feat["icon"]}</span>
                <span class="flow-title">{feat["frontend"]} → {feat["name"]}</span>
                <span class="flow-call-type">{feat["call_type"]}</span>
            </div>

            <div class="flow-diagram">
                <!-- Column 1: Inputs -->
                <div class="flow-col">
                    <div class="flow-panel user-panel">
                        <div class="flow-panel-title">👤 用户前端输入</div>
                        <div class="flow-panel-sub">用户在前端 UI 操作产生的数据</div>
                        {user_items if user_items else '<div class="flow-var-empty">此功能无用户输入变量</div>'}
                    </div>
                    <div class="flow-panel system-panel">
                        <div class="flow-panel-title">⚙️ 后端系统注入</div>
                        <div class="flow-panel-sub">服务器自动填充的数据</div>
                        {sys_items if sys_items else '<div class="flow-var-empty">此功能无系统注入变量</div>'}
                    </div>
                </div>

                <!-- Arrow -->
                <div class="flow-arrow-col">
                    <div class="flow-arrow-line"></div>
                    <div class="flow-arrow-label">填充变量</div>
                    <div class="flow-arrow-tip">→</div>
                </div>

                <!-- Column 2: Template -->
                <div class="flow-col center-col">
                    <div class="flow-panel template-panel">
                        <div class="flow-panel-title">📄 提示词模板</div>
                        <div class="flow-panel-sub">{filename}</div>
                        <div class="flow-template-preview">管理员编写的 System Prompt 模板，<br>包含 Jinja2 变量占位符。<br>用户输入 + 系统数据填充变量后，<br>组装成完整的 Prompt 发送给 AI。</div>
                        <div class="flow-panel-note">⬇️ 下方可直接编辑模板内容</div>
                    </div>
                </div>

                <!-- Arrow -->
                <div class="flow-arrow-col">
                    <div class="flow-arrow-line"></div>
                    <div class="flow-arrow-label">发送给 AI</div>
                    <div class="flow-arrow-tip">→</div>
                </div>

                <!-- Column 3: AI Output -->
                <div class="flow-col">
                    <div class="flow-panel ai-panel">
                        <div class="flow-panel-title">🤖 AI 模型</div>
                        <div class="flow-panel-sub">{feat["call_type"]} 调用</div>
                        <div class="flow-template-preview">AI 根据完整 Prompt 生成结果，<br>返回给前端展示。</div>
                    </div>
                    <div class="flow-panel output-panel">
                        <div class="flow-panel-title">📤 输出到前端</div>
                        <div class="flow-panel-sub">{feat["frontend"]} 页面</div>
                        <div class="flow-template-preview">{feat["description"]}</div>
                    </div>
                </div>
            </div>

            <div class="flow-legend">
                <span class="flow-legend-item"><span class="flow-dot user"></span> 用户控制 — 修改前端 UI 影响此变量</span>
                <span class="flow-legend-item"><span class="flow-dot system"></span> 后端控制 — 修改模板/代码影响此变量</span>
            </div>
        </div>
        '''

    body = f"""
    <div class="dash">
        <div class="dash-header">
            <h1>📝 编辑模板: {filename}</h1>
            <a href="/admin/logout" class="logout">退出登录</a>
        </div>
        <div class="section">
            {flow_html}
        </div>
        <div class="section editor-wrap">
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


# ── Database Viewer + Editing with Approval ──────────────

_DB_REGISTRY = {
    "xiaotiao": {"path": os.getenv("DB_PATH", "./db/xiaotiao.db"), "label": "📚 小跳主数据库"},
    "auth": {"path": os.getenv("AUTH_DB_PATH", "./db/auth.db"), "label": "🔐 用户认证数据库"},
}

# Chinese display names for tables based on their purpose
_TABLE_LABELS = {
    # xiaotiao.db tables
    "vocabulary_items": "📖 生词本 — 用户保存的词汇",
    "vocabulary_srs_states": "🧠 间隔复习状态 — SRS 记忆曲线",
    "target_ranges": "🎯 目标词表 — 如 CET4/CET6/IELTS",
    "target_range_words": "📝 目标词表词汇 — 各词表所含单词",
    "article_styles": "🎨 文章风格 — 生成文章的风格模板",
    "github_cases": "⚖️ 法律案例库 — GitHub 案例数据",
    "org_units": "🏢 组织机构 — 单位/部门信息",
    "rag_documents": "📄 RAG 文档 — 知识库原始文档",
    "rag_chunks": "🔍 RAG 分片 — 文档向量化分片",
    "papers": "📑 论文库 — 上传的学术论文",
    "paper_annotations": "✏️ 论文标注 — 阅读批注和高亮",
    "collections": "📂 论文集 — 论文分类收藏夹",
    "collection_papers": "🔗 论文集关联 — 论文与集合的映射",
    "topics": "💡 研究主题 — 用户创建的研究主题",
    "topic_papers": "🔗 主题关联 — 论文与主题的映射",
    "paper_chats": "💬 论文对话 — AI 与论文的问答记录",
    "paper_folders": "📁 论文文件夹 — 论文目录结构",
    "reading_log": "📊 阅读记录 — 论文阅读进度追踪",
    "topic_sources": "📰 主题来源 — 主题探索的文章来源",
    # auth.db tables
    "users": "👤 用户账户 — 注册用户信息",
    "auth_sessions": "🔑 登录会话 — 用户认证 Token",
    # SQLite internal FTS tables
    "rag_chunks_fts": "🔍 RAG 全文索引",
    "rag_chunks_fts_config": "⚙️ RAG 索引配置",
    "rag_chunks_fts_content": "📄 RAG 索引内容",
    "rag_chunks_fts_data": "💾 RAG 索引数据",
    "rag_chunks_fts_docsize": "📏 RAG 文档大小",
    "rag_chunks_fts_idx": "🗂️ RAG 索引目录",
}


def _table_label(tname: str) -> str:
    return _TABLE_LABELS.get(tname, f"📋 {tname}")


_PENDING_CHANGES_PATH = os.path.join(os.path.dirname(__file__), "..", "pending_db_changes.json")


def _load_pending() -> list:
    try:
        with open(_PENDING_CHANGES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_pending(changes: list) -> None:
    with open(_PENDING_CHANGES_PATH, "w", encoding="utf-8") as f:
        json.dump(changes, f, indent=2, ensure_ascii=False)


_DB_CSS = """
.db-card{background:rgba(30,41,59,.7);border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid rgba(148,163,184,.08)}
.db-card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;font-weight:600;color:#e2e8f0}
.db-path{font-size:.7rem;color:#64748b;font-weight:400}
.db-tables{display:flex;flex-direction:column;gap:4px}
.db-table-link{display:flex;justify-content:space-between;padding:8px 12px;border-radius:6px;background:rgba(99,102,241,.04);color:#a5b4fc;text-decoration:none;font-size:.82rem;transition:background .2s}
.db-table-link:hover{background:rgba(99,102,241,.12)}
.db-table-count{color:#64748b;font-size:.72rem}
.back-link{color:#94a3b8;text-decoration:none;font-size:.85rem}
.back-link:hover{color:#e2e8f0}
.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px}
.db-table-wrap{overflow-x:auto;background:rgba(30,41,59,.7);border-radius:10px;border:1px solid rgba(148,163,184,.08)}
.db-table{width:100%;border-collapse:collapse;font-size:.75rem}
.db-table th{background:rgba(99,102,241,.08);color:#a5b4fc;padding:8px 10px;text-align:left;font-weight:600;white-space:nowrap;border-bottom:1px solid rgba(148,163,184,.1)}
.db-table td{padding:6px 10px;border-bottom:1px solid rgba(148,163,184,.04);color:#cbd5e1;max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.db-table tr:hover td{background:rgba(99,102,241,.03)}
.db-pagination{display:flex;justify-content:center;align-items:center;gap:16px;padding:12px;color:#94a3b8;font-size:.8rem}
.db-pagination a{color:#6366f1;text-decoration:none}
.db-pagination a:hover{color:#a5b4fc}
.btn-edit{padding:2px 8px;border-radius:4px;background:rgba(99,102,241,.12);color:#a5b4fc;border:none;cursor:pointer;font-size:.7rem}
.btn-edit:hover{background:rgba(99,102,241,.25)}
.pending-badge{display:inline-block;padding:2px 8px;border-radius:10px;background:rgba(251,191,36,.15);color:#fbbf24;font-size:.72rem;font-weight:600}
/* Edit modal */
.edit-modal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:1000;align-items:center;justify-content:center}
.edit-modal.show{display:flex}
.edit-panel{background:#1e293b;border-radius:12px;padding:20px;width:90%;max-width:600px;max-height:80vh;overflow-y:auto;border:1px solid rgba(148,163,184,.1)}
.edit-panel h3{margin:0 0 12px;color:#e2e8f0}
.edit-field{margin-bottom:10px}
.edit-field label{display:block;font-size:.72rem;color:#94a3b8;margin-bottom:3px}
.edit-field input,.edit-field textarea{width:100%;padding:6px 8px;border-radius:6px;background:#0f172a;color:#e2e8f0;border:1px solid rgba(148,163,184,.15);font-size:.8rem;font-family:inherit;box-sizing:border-box}
.edit-field textarea{min-height:60px;resize:vertical}
.edit-btns{display:flex;gap:8px;margin-top:12px}
.edit-btns button{padding:6px 16px;border-radius:6px;border:none;cursor:pointer;font-size:.8rem}
.btn-submit{background:rgba(99,102,241,.2);color:#a5b4fc}
.btn-submit:hover{background:rgba(99,102,241,.3)}
.btn-cancel{background:rgba(148,163,184,.1);color:#94a3b8}
/* Pending changes */
.pending-card{background:rgba(30,41,59,.7);border-radius:10px;padding:14px;margin-bottom:10px;border:1px solid rgba(148,163,184,.08)}
.pending-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px}
.pending-meta{font-size:.72rem;color:#94a3b8}
.pending-diff{font-size:.75rem;margin:6px 0}
.pending-diff .old{color:#f87171;text-decoration:line-through}
.pending-diff .new{color:#4ade80}
.pending-actions{display:flex;gap:6px;margin-top:8px}
.btn-approve{padding:4px 12px;border-radius:6px;background:rgba(74,222,128,.15);color:#4ade80;border:none;cursor:pointer;font-size:.75rem}
.btn-approve:hover{background:rgba(74,222,128,.25)}
.btn-reject{padding:4px 12px;border-radius:6px;background:rgba(248,113,113,.12);color:#f87171;border:none;cursor:pointer;font-size:.75rem}
.btn-reject:hover{background:rgba(248,113,113,.22)}
"""


@router.get("/database", response_class=HTMLResponse, include_in_schema=False)
def admin_database(request: Request):
    if not _check_session(request):
        return RedirectResponse("/admin", status_code=302)

    import sqlite3
    pending = _load_pending()
    pending_count = sum(1 for p in pending if p.get("status") == "pending")

    db_cards = ""
    for db_id, db_info in _DB_REGISTRY.items():
        db_path = db_info["path"]
        label = db_info["label"]
        tables_html = ""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            for t in tables:
                tname = t["name"]
                count = conn.execute(f"SELECT COUNT(*) as c FROM [{tname}]").fetchone()["c"]
                tlabel = _table_label(tname)
                tables_html += f'<a class="db-table-link" href="/admin/database/{db_id}/{tname}"><span class="db-table-name">{tlabel}</span><span class="db-table-count">{count} 行</span></a>'
            conn.close()
        except Exception as exc:
            tables_html = f'<div style="color:#f87171">❌ 无法连接: {exc}</div>'

        db_cards += f"""
        <div class="db-card">
            <div class="db-card-header"><span>🗄️ {label}</span><span class="db-path">{db_path}</span></div>
            <div class="db-tables">{tables_html}</div>
        </div>
        """

    pending_link = ""
    if pending_count > 0:
        pending_link = f'<a href="/admin/database/pending" class="pending-badge">⏳ {pending_count} 条待审核变更</a>'

    body = f"""
    <div class="section-header">
        <h2>🗄️ 数据库浏览器</h2>
        <div>{pending_link} <a href="/admin/dashboard" class="back-link">← 返回仪表盘</a></div>
    </div>
    <style>{_DB_CSS}</style>
    {db_cards}
    """
    return HTMLResponse(_page("数据库浏览器", body))


@router.get("/database/pending", response_class=HTMLResponse, include_in_schema=False)
def admin_pending_changes(request: Request):
    if not _check_session(request):
        return RedirectResponse("/admin", status_code=302)

    pending = _load_pending()
    pending_items = [p for p in pending if p.get("status") == "pending"]

    cards_html = ""
    if not pending_items:
        cards_html = '<p style="color:#64748b;text-align:center;padding:20px">✅ 没有待审核的变更</p>'
    else:
        for idx, p in enumerate(pending):
            if p.get("status") != "pending":
                continue
            db_label = _DB_REGISTRY.get(p["db_id"], {}).get("label", p["db_id"])
            diff_html = ""
            for col, vals in p.get("changes", {}).items():
                old_v = html_mod.escape(str(vals.get("old", ""))[:80])
                new_v = html_mod.escape(str(vals.get("new", ""))[:80])
                diff_html += f'<div class="pending-diff"><strong>{html_mod.escape(col)}</strong>: <span class="old">{old_v}</span> → <span class="new">{new_v}</span></div>'

            pk_desc = ", ".join(f"{k}={v}" for k, v in p.get("pk", {}).items())
            cards_html += f"""
            <div class="pending-card" id="pending-{idx}">
                <div class="pending-header">
                    <span style="color:#e2e8f0;font-weight:600">📋 {html_mod.escape(p['table'])} — {pk_desc}</span>
                    <span class="pending-meta">{db_label} · {p.get('timestamp', '')}</span>
                </div>
                {diff_html}
                <div class="pending-actions">
                    <button class="btn-approve" onclick="handlePending({idx}, 'approve')">✅ 批准执行</button>
                    <button class="btn-reject" onclick="handlePending({idx}, 'reject')">❌ 拒绝</button>
                </div>
            </div>
            """

    body = f"""
    <div class="section-header">
        <h2>⏳ 待审核变更 ({len(pending_items)})</h2>
        <a href="/admin/database" class="back-link">← 返回数据库</a>
    </div>
    <style>{_DB_CSS}</style>
    {cards_html}
    <script>
    async function handlePending(idx, action) {{
        const card = document.getElementById('pending-' + idx);
        card.style.opacity = '0.5';
        try {{
            const resp = await fetch('/admin/api/db-change-action', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                credentials: 'include',
                body: JSON.stringify({{index: idx, action: action}})
            }});
            const data = await resp.json();
            if (data.ok) {{
                card.style.display = 'none';
                if (action === 'approve') {{
                    alert('✅ 变更已执行');
                }} else {{
                    alert('❌ 变更已拒绝');
                }}
            }} else {{
                alert('操作失败: ' + (data.error || '未知错误'));
                card.style.opacity = '1';
            }}
        }} catch(e) {{
            alert('网络错误');
            card.style.opacity = '1';
        }}
    }}
    </script>
    """
    return HTMLResponse(_page("待审核变更", body))


@router.get("/database/{db_id}/{table_name}", response_class=HTMLResponse, include_in_schema=False)
def admin_database_table(request: Request, db_id: str, table_name: str):
    if not _check_session(request):
        return RedirectResponse("/admin", status_code=302)

    import sqlite3
    db_info = _DB_REGISTRY.get(db_id)
    if not db_info:
        return HTMLResponse(_page("错误", "<p>数据库不存在</p>"))

    page = int(request.query_params.get("page", "1"))
    per_page = 50
    offset = (page - 1) * per_page

    try:
        conn = sqlite3.connect(db_info["path"])
        conn.row_factory = sqlite3.Row
        # Get columns + primary key
        col_info = conn.execute(f"PRAGMA table_info([{table_name}])").fetchall()
        columns = [row["name"] for row in col_info]
        pk_cols = [row["name"] for row in col_info if row["pk"] > 0]
        if not pk_cols:
            pk_cols = [columns[0]] if columns else []
        total = conn.execute(f"SELECT COUNT(*) as c FROM [{table_name}]").fetchone()["c"]
        rows = conn.execute(f"SELECT * FROM [{table_name}] LIMIT {per_page} OFFSET {offset}").fetchall()
        conn.close()
    except Exception as exc:
        return HTMLResponse(_page("错误", f"<p style='color:#f87171'>❌ 查询失败: {exc}</p>"))

    total_pages = max(1, (total + per_page - 1) // per_page)

    # Build table HTML with edit buttons
    thead = "<th>操作</th>" + "".join(f"<th>{html_mod.escape(c)}</th>" for c in columns)
    tbody = ""
    for row in rows:
        # Build PK JSON for this row
        pk_data = {c: (row[c] if row[c] is not None else "") for c in pk_cols}
        row_data = {c: (str(row[c]) if row[c] is not None else "") for c in columns}
        pk_json = html_mod.escape(json.dumps(pk_data, ensure_ascii=False))
        row_json = html_mod.escape(json.dumps(row_data, ensure_ascii=False))
        cells = f'<td><button class="btn-edit" onclick=\'openEdit({pk_json}, {row_json})\'>✏️ 编辑</button></td>'
        for c in columns:
            val = row[c]
            cell_str = html_mod.escape(str(val) if val is not None else "NULL")
            if len(cell_str) > 100:
                cell_str = cell_str[:100] + "…"
            cells += f"<td>{cell_str}</td>"
        tbody += f"<tr>{cells}</tr>"

    # Pagination
    pagination = '<div class="db-pagination">'
    if page > 1:
        pagination += f'<a href="/admin/database/{db_id}/{table_name}?page={page-1}">← 上一页</a>'
    pagination += f'<span>第 {page}/{total_pages} 页 · 共 {total} 行</span>'
    if page < total_pages:
        pagination += f'<a href="/admin/database/{db_id}/{table_name}?page={page+1}">下一页 →</a>'
    pagination += '</div>'

    # Columns JSON for modal
    cols_json = json.dumps(columns, ensure_ascii=False)
    pk_cols_json = json.dumps(pk_cols, ensure_ascii=False)

    body = f"""
    <div class="section-header">
        <h2>{_table_label(table_name)}</h2>
        <a href="/admin/database" class="back-link">← 返回数据库列表</a>
    </div>
    <p style="color:#94a3b8;font-size:.8rem;margin-bottom:12px">🗄️ {db_info['label']} · {total} 行 · 点击行首「✏️ 编辑」可修改数据（需审批后生效）</p>
    <style>{_DB_CSS}</style>
    <div class="db-table-wrap">
        <table class="db-table">
            <thead><tr>{thead}</tr></thead>
            <tbody>{tbody}</tbody>
        </table>
    </div>
    {pagination}

    <!-- Edit Modal -->
    <div class="edit-modal" id="editModal">
        <div class="edit-panel">
            <h3>✏️ 编辑行数据</h3>
            <div id="editFields"></div>
            <p style="color:#fbbf24;font-size:.72rem;margin-top:8px">⚠️ 修改不会立即生效，需管理员在「待审核变更」中批准后才会执行。</p>
            <div class="edit-btns">
                <button class="btn-submit" onclick="submitEdit()">📤 提交变更</button>
                <button class="btn-cancel" onclick="closeEdit()">取消</button>
            </div>
            <div id="editMsg" style="margin-top:8px;font-size:.75rem"></div>
        </div>
    </div>

    <script>
    const DB_ID = '{db_id}';
    const TABLE = '{table_name}';
    const COLUMNS = {cols_json};
    const PK_COLS = {pk_cols_json};
    let currentPK = {{}};
    let originalData = {{}};

    function openEdit(pk, row) {{
        currentPK = typeof pk === 'string' ? JSON.parse(pk) : pk;
        originalData = typeof row === 'string' ? JSON.parse(row) : row;
        const container = document.getElementById('editFields');
        container.innerHTML = '';
        for (const col of COLUMNS) {{
            const isPK = PK_COLS.includes(col);
            const val = originalData[col] || '';
            const field = document.createElement('div');
            field.className = 'edit-field';
            const long = val.length > 60;
            field.innerHTML = '<label>' + col + (isPK ? ' 🔑 (主键)' : '') + '</label>' +
                (long ? '<textarea id="ef-' + col + '"' + (isPK ? ' readonly style="opacity:.6"' : '') + '>' + val.replace(/</g,'&lt;') + '</textarea>'
                       : '<input id="ef-' + col + '" value="' + val.replace(/"/g,'&quot;') + '"' + (isPK ? ' readonly style="opacity:.6"' : '') + '>');
            container.appendChild(field);
        }}
        document.getElementById('editModal').classList.add('show');
        document.getElementById('editMsg').textContent = '';
    }}

    function closeEdit() {{
        document.getElementById('editModal').classList.remove('show');
    }}

    async function submitEdit() {{
        const changes = {{}};
        for (const col of COLUMNS) {{
            const el = document.getElementById('ef-' + col);
            const newVal = el.value || el.textContent || '';
            if (newVal !== (originalData[col] || '')) {{
                changes[col] = {{old: originalData[col] || '', new: newVal}};
            }}
        }}
        if (Object.keys(changes).length === 0) {{
            document.getElementById('editMsg').textContent = '没有变更';
            document.getElementById('editMsg').style.color = '#94a3b8';
            return;
        }}
        const msgEl = document.getElementById('editMsg');
        msgEl.textContent = '⏳ 提交中...';
        msgEl.style.color = '#94a3b8';
        try {{
            const resp = await fetch('/admin/api/db-submit-change', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                credentials: 'include',
                body: JSON.stringify({{db_id: DB_ID, table: TABLE, pk: currentPK, changes: changes}})
            }});
            const data = await resp.json();
            if (data.ok) {{
                msgEl.textContent = '✅ 已提交，等待管理员审批';
                msgEl.style.color = '#4ade80';
                setTimeout(() => closeEdit(), 1500);
            }} else {{
                msgEl.textContent = '❌ ' + (data.error || '提交失败');
                msgEl.style.color = '#f87171';
            }}
        }} catch(e) {{
            msgEl.textContent = '❌ 网络错误';
            msgEl.style.color = '#f87171';
        }}
    }}

    document.getElementById('editModal').addEventListener('click', function(e) {{
        if (e.target === this) closeEdit();
    }});
    </script>
    """
    return HTMLResponse(_page(f"{_table_label(table_name)}", body))


# ── Database change API endpoints ──

@router.post("/api/db-submit-change", include_in_schema=False)
async def db_submit_change(request: Request):
    if not _check_session(request):
        return JSONResponse({"ok": False, "error": "未登录"}, status_code=401)
    try:
        body = await request.json()
        import datetime
        change = {
            "db_id": body["db_id"],
            "table": body["table"],
            "pk": body["pk"],
            "changes": body["changes"],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending",
        }
        pending = _load_pending()
        pending.append(change)
        _save_pending(pending)
        return JSONResponse({"ok": True})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)})


@router.post("/api/db-change-action", include_in_schema=False)
async def db_change_action(request: Request):
    if not _check_session(request):
        return JSONResponse({"ok": False, "error": "未登录"}, status_code=401)
    try:
        body = await request.json()
        idx = body["index"]
        action = body["action"]  # "approve" or "reject"
        pending = _load_pending()
        if idx < 0 or idx >= len(pending):
            return JSONResponse({"ok": False, "error": "索引无效"})
        item = pending[idx]
        if item.get("status") != "pending":
            return JSONResponse({"ok": False, "error": "该变更已处理"})

        if action == "approve":
            # Execute the change
            import sqlite3
            db_info = _DB_REGISTRY.get(item["db_id"])
            if not db_info:
                return JSONResponse({"ok": False, "error": "数据库不存在"})
            conn = sqlite3.connect(db_info["path"])
            # Build UPDATE statement
            set_parts = []
            values = []
            for col, vals in item["changes"].items():
                set_parts.append(f"[{col}] = ?")
                values.append(vals["new"])
            where_parts = []
            for col, val in item["pk"].items():
                where_parts.append(f"[{col}] = ?")
                values.append(val)
            sql = f"UPDATE [{item['table']}] SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
            conn.execute(sql, values)
            conn.commit()
            conn.close()
            item["status"] = "approved"
        else:
            item["status"] = "rejected"

        pending[idx] = item
        _save_pending(pending)
        return JSONResponse({"ok": True, "action": action})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)})

