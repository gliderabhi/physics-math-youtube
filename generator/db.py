from contextlib import contextmanager

import pymysql
import pymysql.cursors

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS curriculum_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    class INT NOT NULL,
    chapter VARCHAR(150) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    content_type VARCHAR(20) NOT NULL,
    difficulty VARCHAR(30) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'generated',
    run_id VARCHAR(32),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_curriculum_item (subject, class, chapter, subtopic, content_type, difficulty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR(32) PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    class INT NOT NULL,
    chapter VARCHAR(150) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    content_type VARCHAR(20) NOT NULL,
    difficulty VARCHAR(30) NOT NULL DEFAULT '',
    language VARCHAR(20) NOT NULL DEFAULT 'hi-en',
    title VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    video_path TEXT,
    thumbnail_path TEXT,
    youtube_video_id VARCHAR(64),
    playlist_id VARCHAR(64),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS playlists (
    chapter_key VARCHAR(255) PRIMARY KEY,
    youtube_playlist_id VARCHAR(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS content_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    class INT NOT NULL,
    chapter VARCHAR(150) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    content_type VARCHAR(20) NOT NULL,
    difficulty VARCHAR(30) NOT NULL DEFAULT '',
    title VARCHAR(255) NOT NULL,
    body JSON NOT NULL,
    metadata JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_content_item (subject, class, chapter, subtopic, content_type, difficulty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS narrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content_item_id INT NOT NULL,
    language VARCHAR(20) NOT NULL,
    narration JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_narration (content_item_id, language),
    CONSTRAINT fk_narration_content FOREIGN KEY (content_item_id) REFERENCES content_items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS topic_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    class INT NOT NULL,
    chapter VARCHAR(150) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    language VARCHAR(20) NOT NULL,
    explanation TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_topic_note (subject, class, chapter, subtopic, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS wiki_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    class INT NOT NULL,
    chapter VARCHAR(150) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    wiki_title VARCHAR(255) NOT NULL,
    wiki_text TEXT NOT NULL,
    wiki_source_url VARCHAR(500) NOT NULL,
    wiki_images JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_wiki_note (subject, class, chapter, subtopic)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS topic_problems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    class INT NOT NULL,
    chapter VARCHAR(150) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    language VARCHAR(20) NOT NULL,
    problems JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_topic_problems (subject, class, chapter, subtopic, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS subtopic_wiki_html (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    class INT NOT NULL,
    chapter VARCHAR(150) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    language VARCHAR(20) NOT NULL DEFAULT 'en',
    wiki_title VARCHAR(255) NOT NULL,
    wiki_url VARCHAR(500) NOT NULL,
    html_content MEDIUMTEXT NOT NULL,
    has_diagrams TINYINT(1) DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_subtopic_wiki_lang (subject, class, chapter, subtopic, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS subtopic_wiki_parts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(20) NOT NULL,
    class INT NOT NULL,
    chapter VARCHAR(150) NOT NULL,
    subtopic VARCHAR(200) NOT NULL,
    language VARCHAR(20) NOT NULL DEFAULT 'en',
    part_index INT NOT NULL,
    heading VARCHAR(255) NOT NULL,
    paragraph TEXT NOT NULL,
    paragraph_html MEDIUMTEXT NOT NULL,
    diagram_url VARCHAR(500),
    diagram_caption TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_subtopic_part (subject, class, chapter, subtopic, language, part_index)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


@contextmanager
def get_conn():
    conn = pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            for statement in SCHEMA.split(";"):
                statement = statement.strip()
                if statement:
                    cur.execute(statement)
