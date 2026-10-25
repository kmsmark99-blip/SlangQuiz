import sqlite3
import json
import logging
from pathlib import Path
import config

logger = logging.getLogger(__name__)

DB_PATH = config.DATABASE_DIR / "slang_quiz.db"
SCHEMA_PATH = config.BASE_DIR / "database" / "schema.sql"


def get_connection():
    """데이터베이스 연결 객체를 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """schema.sql을 읽어 데이터베이스 및 테이블을 초기화합니다."""
    try:
        config.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        with get_connection() as conn:
            if SCHEMA_PATH.exists():
                with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
                logger.info("데이터베이스 테이블 초기화 완료")
            else:
                logger.error("schema.sql 파일을 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")


def save_quiz_session(username: str, difficulty: str, questions: list, user_answers: dict) -> bool:
    """퀴즈 수행 결과를 데이터베이스 트랜잭션으로 저장합니다."""
    try:
        init_db()
        with get_connection() as conn:
            cursor = conn.cursor()

            # 1. 사용자 조회 또는 신규 등록
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if user_row:
                user_id = user_row[0]
            else:
                cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
                user_id = cursor.lastrowid

            # 2. 문제 정보 저장
            total_q = len(questions)
            correct_count = 0

            for idx, q in enumerate(questions):
                q_id = getattr(q, 'id', f"q_{idx}")
                q_text = getattr(q, 'q', '')
                q_opts = getattr(q, 'options', ["", "", "", ""])
                q_ans = getattr(q, 'answer', 1)
                q_exp = getattr(q, 'explanation', '')
                q_diff = getattr(q, 'difficulty', difficulty)

                cursor.execute("""
                    INSERT OR IGNORE INTO questions (id, question, option1, option2, option3, option4, answer, explanation, difficulty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (q_id, q_text, q_opts[0], q_opts[1], q_opts[2], q_opts[3], q_ans, q_exp, q_diff))

                user_ans = user_answers.get(idx)
                if user_ans == q_ans:
                    correct_count += 1

            score = (correct_count / total_q) * 100 if total_q > 0 else 0.0

            # 3. 퀴즈 이력 저장
            cursor.execute("""
                INSERT INTO quiz_history (user_id, difficulty, total_questions, correct_count, score)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, difficulty, total_q, correct_count, score))
            quiz_history_id = cursor.lastrowid

            # 4. 개별 문제 답안 로그 저장
            for idx, q in enumerate(questions):
                q_id = getattr(q, 'id', f"q_{idx}")
                q_ans = getattr(q, 'answer', 1)
                user_ans = user_answers.get(idx, 0)
                is_correct = 1 if user_ans == q_ans else 0

                cursor.execute("""
                    INSERT INTO answer_logs (quiz_history_id, question_id, selected_option, is_correct)
                    VALUES (?, ?, ?, ?)
                """, (quiz_history_id, q_id, user_ans, is_correct))

            conn.commit()
            logger.info(f"{username}님의 퀴즈 결과 DB 저장 성공 (점수: {score}점)")
            return True

    except Exception as e:
        logger.error(f"퀴즈 결과 DB 저장 실패: {e}")
        return False


def get_leaderboard(difficulty: str = None, limit: int = 10) -> list[dict]:
    """사용자별 최고 점수를 기준으로 순위를 조회합니다."""
    try:
        init_db()
        with get_connection() as conn:
            cursor = conn.cursor()
            
            if difficulty and difficulty != "전체":
                query = """
                    SELECT u.username, MAX(q.score) as max_score, MAX(q.correct_count) as max_correct, q.difficulty, MIN(q.created_at) as first_achieved
                    FROM quiz_history q
                    JOIN users u ON q.user_id = u.id
                    WHERE q.difficulty = ?
                    GROUP BY u.id
                    ORDER BY max_score DESC, first_achieved ASC
                    LIMIT ?
                """
                cursor.execute(query, (difficulty, limit))
            else:
                query = """
                    SELECT u.username, MAX(q.score) as max_score, MAX(q.correct_count) as max_correct, '전체' as difficulty, MIN(q.created_at) as first_achieved
                    FROM quiz_history q
                    JOIN users u ON q.user_id = u.id
                    GROUP BY u.id
                    ORDER BY max_score DESC, first_achieved ASC
                    LIMIT ?
                """
                cursor.execute(query, (limit,))

            rows = cursor.fetchall()
            leaderboard = []
            for rank, row in enumerate(rows, 1):
                leaderboard.append({
                    "rank": rank,
                    "username": row[0],
                    "score": row[1],
                    "correct_count": row[2],
                    "difficulty": row[3],
                    "created_at": row[4]
                })
            return leaderboard
    except Exception as e:
        logger.error(f"순위표 조회 오류: {e}")
        return []


def get_user_best_score(username: str) -> dict | None:
    """특정 사용자의 개인 최고 점수 기록을 가져옵니다."""
    try:
        init_db()
        with get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT MAX(q.score), MAX(q.correct_count)
                FROM quiz_history q
                JOIN users u ON q.user_id = u.id
                WHERE u.username = ?
            """
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            if row and row[0] is not None:
                return {"max_score": row[0], "max_correct": row[1]}
    except Exception as e:
        logger.error(f"사용자 최고 기록 조회 오류: {e}")
    return None


def get_question_error_rates(difficulty: str = None) -> list[dict]:
    """문제별 총 응답 수, 오답 수, 오답률을 계산하여 반환합니다."""
    try:
        init_db()
        with get_connection() as conn:
            cursor = conn.cursor()
            
            if difficulty and difficulty != "전체":
                query = """
                    SELECT q.id, q.question, q.difficulty,
                           COUNT(a.id) as total_answers,
                           SUM(CASE WHEN a.is_correct = 0 THEN 1 ELSE 0 END) as wrong_answers
                    FROM questions q
                    LEFT JOIN answer_logs a ON q.id = a.question_id
                    WHERE q.difficulty = ?
                    GROUP BY q.id
                    ORDER BY (CAST(SUM(CASE WHEN a.is_correct = 0 THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(a.id), 0)) DESC
                """
                cursor.execute(query, (difficulty,))
            else:
                query = """
                    SELECT q.id, q.question, q.difficulty,
                           COUNT(a.id) as total_answers,
                           SUM(CASE WHEN a.is_correct = 0 THEN 1 ELSE 0 END) as wrong_answers
                    FROM questions q
                    LEFT JOIN answer_logs a ON q.id = a.question_id
                    GROUP BY q.id
                    ORDER BY (CAST(SUM(CASE WHEN a.is_correct = 0 THEN 1 ELSE 0 END) AS REAL) / NULLIF(COUNT(a.id), 0)) DESC
                """
                cursor.execute(query)

            rows = cursor.fetchall()
            stats = []
            for row in rows:
                q_id, q_text, q_diff, total, wrong = row
                error_rate = (wrong / total * 100) if total > 0 else 0.0
                stats.append({
                    "question_id": q_id,
                    "question": q_text,
                    "difficulty": q_diff,
                    "total_answers": total,
                    "wrong_answers": wrong,
                    "error_rate": round(error_rate, 1)
                })
            return stats
    except Exception as e:
        logger.error(f"문제별 오답률 통계 조회 오류: {e}")
        return []