import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import DATABASE_PATH


# =========================
# DATABASE CONNECTION
# =========================

def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================
# INITIALIZE DATABASE
# =========================

def init_db() -> None:

    Path(DATABASE_PATH).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            post_id TEXT UNIQUE,

            author TEXT,

            username TEXT,

            text TEXT,

            url TEXT,

            created_at TEXT,

            collected_at TEXT,

            source TEXT DEFAULT 'x_for_you'
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_posts_created_at
        ON posts(created_at)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_posts_collected_at
        ON posts(collected_at)
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            role TEXT,

            content TEXT,

            created_at TEXT
        )
        """
    )

    connection.commit()

    connection.close()


# =========================
# ADD POST
# =========================

def add_post(
    post_id: str,
    author: str,
    username: str,
    text: str,
    url: str,
    created_at: str,
    collected_at: str,
    source: str = "x_for_you"
) -> bool:

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT OR IGNORE INTO posts
            (
                post_id,
                author,
                username,
                text,
                url,
                created_at,
                collected_at,
                source
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_id,
                author,
                username,
                text,
                url,
                created_at,
                collected_at,
                source
            )
        )

        inserted = cursor.rowcount > 0

        connection.commit()

        return inserted

    finally:

        connection.close()


# =========================
# GET RECENT POSTS
# =========================

def get_recent_posts(
    limit: int = 100
) -> List[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            post_id,
            author,
            username,
            text,
            url,
            created_at,
            collected_at,
            source

        FROM posts

        ORDER BY
            collected_at DESC

        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================
# SEARCH POSTS
# =========================

def search_posts(
    query: str,
    limit: int = 100
) -> List[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    search_pattern = f"%{query}%"

    cursor.execute(
        """
        SELECT
            id,
            post_id,
            author,
            username,
            text,
            url,
            created_at,
            collected_at,
            source

        FROM posts

        WHERE
            text LIKE ?
            OR author LIKE ?
            OR username LIKE ?

        ORDER BY
            collected_at DESC

        LIMIT ?
        """,
        (
            search_pattern,
            search_pattern,
            search_pattern,
            limit
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================
# SAVE CHAT MESSAGE
# =========================

def save_chat_message(
    role: str,
    content: str,
    created_at: str
) -> None:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO chat_messages
        (
            role,
            content,
            created_at
        )

        VALUES (?, ?, ?)
        """,
        (
            role,
            content,
            created_at
        )
    )

    connection.commit()

    connection.close()


# =========================
# GET CHAT HISTORY
# =========================

def get_chat_history(
    limit: int = 30
) -> List[Dict[str, Any]]:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            role,
            content,
            created_at

        FROM chat_messages

        ORDER BY
            id DESC

        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    rows = list(reversed(rows))

    return [
        dict(row)
        for row in rows
    ]
