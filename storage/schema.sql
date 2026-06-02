-- ebook-content-studio 数据库建表语句
-- SQLite 数据库模式定义

-- 书籍表
CREATE TABLE IF NOT EXISTS books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    file_path TEXT NOT NULL,
    category TEXT DEFAULT '',             -- 分类（如：历史军事、幽默笑话）
    file_hash TEXT DEFAULT '',            -- 文件 MD5，用于去重
    language TEXT DEFAULT '中文',         -- 语言类型：中文/中英混合/英文
    summary TEXT DEFAULT '',              -- 书籍摘要
    total_chars INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    embedding_model TEXT DEFAULT 'bge-m3',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 章节表
CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    book_id TEXT REFERENCES books(id),
    parent_id TEXT REFERENCES chapters(id),
    level INTEGER DEFAULT 1,
    title TEXT NOT NULL,
    start_char INTEGER DEFAULT 0,
    end_char INTEGER DEFAULT 0,
    summary TEXT DEFAULT '',
    chunk_ids TEXT DEFAULT '[]'
);

-- 分块表
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(id),
    content TEXT NOT NULL,
    struct_path TEXT DEFAULT '',
    start_char INTEGER DEFAULT 0,
    end_char INTEGER DEFAULT 0,
    heading_stack TEXT DEFAULT '[]'
);

-- 分块标签表（用于按主题分类筛选）
CREATE TABLE IF NOT EXISTS chunk_tags (
    chunk_id TEXT REFERENCES chunks(chunk_id),
    tag TEXT NOT NULL,
    PRIMARY KEY (chunk_id, tag)
);

-- 全文索引（由 FullTextEngine 通过 FTS5 管理）
CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(
    chunk_id,
    content,
    tokenize='unicode61'
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_chapters_book_id ON chapters(book_id);
CREATE INDEX IF NOT EXISTS idx_chapters_parent_id ON chapters(parent_id);
CREATE INDEX IF NOT EXISTS idx_chunks_book_id ON chunks(book_id);
CREATE INDEX IF NOT EXISTS idx_chunks_struct_path ON chunks(struct_path);
CREATE INDEX IF NOT EXISTS idx_chunk_tags_tag ON chunk_tags(tag);