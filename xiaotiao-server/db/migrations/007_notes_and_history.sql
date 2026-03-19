-- 通用笔记表 + 翻译历史表
CREATE TABLE IF NOT EXISTS notes (
    id          TEXT PRIMARY KEY,
    module      TEXT NOT NULL,
    ref_id      TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS translation_history (
    id              TEXT PRIMARY KEY,
    source_text     TEXT NOT NULL,
    direction       TEXT DEFAULT 'en_to_zh',
    result_json     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notes_module_ref ON notes(module, ref_id);
CREATE INDEX IF NOT EXISTS idx_translation_history_created ON translation_history(created_at DESC);
