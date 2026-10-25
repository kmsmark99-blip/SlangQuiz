import sqlite3
import json
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


def init_db():
    """SQLite 데이터베이스 및 테이블을 초기화합니다."""
    config.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    
    with sqlite3.connect(config.DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                score REAL NOT NULL,
                user_answers_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_quiz_result(username: str, difficulty: str, total_q: int, correct_count: int, score: float, user_answers: dict) -> bool:
    """퀴즈 결과를 DB에 저장합니다."""
    try:
        init_db()
        with sqlite3.connect(config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quiz_results (username, difficulty, total_questions, correct_count, score, user_answers_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, difficulty, total_q, correct_count, score, json.dumps(user_answers)))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"DB 저장 오류: {e}")
        return False