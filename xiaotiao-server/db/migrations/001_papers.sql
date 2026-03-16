-- 001_papers.sql — AInsight 论文系统数据表
-- 在 init.sql 中 source 或在 database.py 中执行

-- 论文主表
CREATE TABLE IF NOT EXISTS papers (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    url         TEXT,
    source      TEXT DEFAULT 'upload',   -- 'arxiv'|'url'|'upload'
    status      TEXT DEFAULT 'pending',  -- 'pending'|'processing'|'ready'|'failed'
    abstract    TEXT,
    authors     TEXT,       -- JSON array
    arxiv_id    TEXT,
    doi         TEXT,
    pdf_path    TEXT,       -- local storage path
    pdf_url     TEXT,       -- remote PDF URL
    insight     TEXT,       -- AI generated JSON
    tags        TEXT,       -- JSON array
    is_favorite INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 论文批注
CREATE TABLE IF NOT EXISTS paper_annotations (
    id            TEXT PRIMARY KEY,
    paper_id      TEXT NOT NULL,
    type          TEXT NOT NULL,     -- 'highlight'|'note'
    selected_text TEXT,
    note          TEXT,
    page_number   INTEGER,
    position      TEXT,             -- JSON
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
    check_frequency TEXT DEFAULT 'daily',    -- 'daily'|'weekly'
    last_checked_at TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 主题发现的论文
CREATE TABLE IF NOT EXISTS topic_papers (
    id            TEXT PRIMARY KEY,
    topic_id      TEXT NOT NULL,
    title         TEXT NOT NULL,
    url           TEXT,
    brief         TEXT,         -- AI short summary
    status        TEXT DEFAULT 'pending',  -- 'pending'|'done'|'ignored'
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

-- 论文对话记录
CREATE TABLE IF NOT EXISTS paper_chats (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id   TEXT NOT NULL,
    role       TEXT NOT NULL,      -- 'user'|'assistant'
    content    TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);
