-- Ghost Story Factory - Database Schema
-- SQLite 数据库表结构
-- 创建日期: 2025-10-24

-- 城市表
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 故事表
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    slug TEXT,
    synopsis TEXT NOT NULL,  -- 故事简介
    estimated_duration_minutes INTEGER,  -- 预计游戏时长（分钟）
    total_nodes INTEGER,  -- 对话树节点总数
    max_depth INTEGER,  -- 对话树最大深度
    generation_cost_usd REAL,  -- 生成成本（美元）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE
);

-- 角色表
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    is_protagonist BOOLEAN DEFAULT 0,  -- 是否主角线（0=否，1=是）
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
);

-- 对话树表（存储 JSON）
CREATE TABLE IF NOT EXISTS dialogue_trees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    tree_data TEXT NOT NULL,  -- JSON 格式的完整对话树
    compressed BOOLEAN DEFAULT 0,  -- 是否 gzip 压缩（0=否，1=是）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    UNIQUE(story_id, character_id)  -- 每个故事的每个角色只有一棵对话树
);

-- 生成元数据表
CREATE TABLE IF NOT EXISTS generation_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    total_tokens INTEGER,  -- 总消耗 Token 数
    generation_time_seconds INTEGER,  -- 生成耗时（秒）
    model_used TEXT,  -- 使用的模型
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
);

-- 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_stories_city ON stories(city_id);
CREATE INDEX IF NOT EXISTS idx_stories_slug ON stories(slug);
CREATE INDEX IF NOT EXISTS idx_characters_story ON characters(story_id);
CREATE INDEX IF NOT EXISTS idx_dialogue_trees_story_char ON dialogue_trees(story_id, character_id);
CREATE INDEX IF NOT EXISTS idx_metadata_story ON generation_metadata(story_id);

