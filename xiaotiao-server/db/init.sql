-- 词汇主表 (vocabulary_items)
CREATE TABLE IF NOT EXISTS vocabulary_items (
    id TEXT PRIMARY KEY,
    word TEXT NOT NULL,
    definition_zh TEXT,
    part_of_speech TEXT,
    domain TEXT,
    source TEXT,
    example_sentence TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SRS 状态表 (vocabulary_srs_states)
CREATE TABLE IF NOT EXISTS vocabulary_srs_states (
    id TEXT PRIMARY KEY,
    vocab_id TEXT NOT NULL,
    traversal_count INTEGER DEFAULT 0,
    ease_factor REAL DEFAULT 2.5,
    interval_days INTEGER DEFAULT 1,
    next_review_date TIMESTAMP,
    is_mastered BOOLEAN DEFAULT 0,
    last_article_id TEXT,
    last_reviewed_at TIMESTAMP,
    FOREIGN KEY (vocab_id) REFERENCES vocabulary_items(id) ON DELETE CASCADE
);

-- 目标范围表 (target_ranges)
CREATE TABLE IF NOT EXISTS target_ranges (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    total_count INTEGER DEFAULT 0,
    description TEXT
);

-- 目标范围词汇表 (target_range_words)
CREATE TABLE IF NOT EXISTS target_range_words (
    range_id TEXT NOT NULL,
    word TEXT NOT NULL,
    frequency_rank INTEGER,
    FOREIGN KEY (range_id) REFERENCES target_ranges(id) ON DELETE CASCADE
);

-- 文章风格表 (article_styles)
CREATE TABLE IF NOT EXISTS article_styles (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    prompt_modifier TEXT,
    template_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预置目标范围初始数据
INSERT OR IGNORE INTO target_ranges (id, display_name, total_count, description) VALUES
('cet4', '四级词汇', 4425, '大学英语四级考试大纲词汇'),
('cet6', '六级词汇', 6710, '大学英语六级考试大纲词汇'),
('ielts', '雅思核心', 570, '雅思学术类(AWL)核心词族'),
('toefl', '托福核心', 3000, '托福核心高频词汇');

-- 预置文章风格初始数据
INSERT OR IGNORE INTO article_styles (id, type, name, prompt_modifier) VALUES
('economist', 'preset', 'The Economist', '严谨、精炼、使用 Latinate 词汇，善用隐喻，段落短而论点密集'),
('guardian', 'preset', 'The Guardian', '清晰可读，叙事性强，适度使用口语，引用专家观点'),
('ft', 'preset', 'Financial Times', '商业导向，数字与事实密集，行文节制，强调影响与因果'),
('academic', 'preset', '学术期刊风格', '正式、客观、使用被动语态，文献引用格式规范'),
('plain_english', 'preset', 'Plain English', '简洁，短句，尽量用常用词替换术语，适合初级读者');

-- GitHub 相似案例索引
CREATE TABLE IF NOT EXISTS github_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    full_name TEXT NOT NULL,
    html_url TEXT NOT NULL,
    stars INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    language TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(query, full_name)
);

-- 组织架构
CREATE TABLE IF NOT EXISTS org_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_key TEXT NOT NULL UNIQUE,
    unit_name TEXT NOT NULL,
    responsibility TEXT NOT NULL,
    owner_role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO org_units (unit_key, unit_name, responsibility, owner_role) VALUES
('product', 'Product & Research', 'Define roadmap, PRD, and user validation loops', 'Product Lead'),
('ai-platform', 'AI Platform', 'Prompt quality, model routing, and evaluation', 'AI Engineer'),
('backend-data', 'Backend & Data', 'APIs, persistence, and data quality controls', 'Backend Engineer'),
('frontend-experience', 'Frontend Experience', 'Learning workflow UI, interaction, and accessibility', 'Frontend Engineer'),
('quality-ops', 'Quality & Operations', 'Testing, release governance, observability', 'QA/DevOps Engineer');

-- RAG 文档与分块
CREATE TABLE IF NOT EXISTS rag_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    source_url TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES rag_documents(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks_fts USING fts5(
    chunk_text,
    chunk_id UNINDEXED,
    document_id UNINDEXED
);

-- ══════════════════════════════════════════════
-- AInsight 论文系统扩展表
-- ══════════════════════════════════════════════

-- 论文主表
CREATE TABLE IF NOT EXISTS papers (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    url         TEXT,
    source      TEXT DEFAULT 'upload',
    status      TEXT DEFAULT 'pending',
    abstract    TEXT,
    authors     TEXT,
    arxiv_id    TEXT,
    doi         TEXT,
    pdf_path    TEXT,
    pdf_url     TEXT,
    insight     TEXT,
    tags        TEXT,
    is_favorite INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 论文批注
CREATE TABLE IF NOT EXISTS paper_annotations (
    id            TEXT PRIMARY KEY,
    paper_id      TEXT NOT NULL,
    type          TEXT NOT NULL,
    selected_text TEXT,
    note          TEXT,
    page_number   INTEGER,
    position      TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- 论文合集
CREATE TABLE IF NOT EXISTS collections (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 合集-论文关联
CREATE TABLE IF NOT EXISTS collection_papers (
    collection_id TEXT NOT NULL,
    paper_id      TEXT NOT NULL,
    added_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, paper_id),
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);

-- 追踪主题
CREATE TABLE IF NOT EXISTS topics (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    check_frequency TEXT DEFAULT 'daily',
    last_checked_at TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 主题发现的论文
CREATE TABLE IF NOT EXISTS topic_papers (
    id            TEXT PRIMARY KEY,
    topic_id      TEXT NOT NULL,
    title         TEXT NOT NULL,
    url           TEXT,
    brief         TEXT,
    status        TEXT DEFAULT 'pending',
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- 论文对话记录
CREATE TABLE IF NOT EXISTS paper_chats (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id   TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);
