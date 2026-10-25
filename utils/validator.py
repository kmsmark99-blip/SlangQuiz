import uuid
import logging
from typing import List, Tuple
from pydantic import ValidationError
from models.question import Question

logger = logging.getLogger(__name__)


def validate_and_filter_questions(raw_questions: List[dict], expected_count: int, difficulty: str = "보통") -> Tuple[List[Question], bool]:
    """
    전달받은 퀴즈 raw 데이터(dict 리스트)를 검증하고 Pydantic 객체 목록으로 변환합니다.
    
    :param raw_questions: AI가 생성한 원본 dict 데이터 리스트
    :param expected_count: 요청한 문제 수 (5 또는 10)
    :param difficulty: 선택한 난이도
    :return: (검증된 Question 객체 리스트, 검증 통과 여부)
    """
    valid_questions: List[Question] = []
    seen_questions = set()

    if not isinstance(raw_questions, list):
        logger.error("입력 데이터가 리스트 형식이 아닙니다.")
        return [], False

    for idx, item in enumerate(raw_questions):
        try:
            if not isinstance(item, dict):
                continue

            # ID가 없는 경우 고유 UUID 부여
            q_id = item.get("id") or f"q_{uuid.uuid4().hex[:8]}"
            
            question_obj = Question(
                id=q_id,
                q=item.get("q", ""),
                options=item.get("options", []),
                answer=item.get("answer", 0),
                explanation=item.get("explanation", ""),
                difficulty=item.get("difficulty", difficulty)
            )

            # 질문 텍스트 중복 검사 (동일 퀴즈 내부 중복 방지)
            normalized_q = question_obj.q.strip().replace(" ", "")
            if normalized_q in seen_questions:
                logger.warning(f"중복 문제 감지되어 제외됨: {question_obj.q}")
                continue

            seen_questions.add(normalized_q)
            valid_questions.append(question_obj)

        except (ValidationError, ValueError) as e:
            logger.warning(f"인덱스 {idx}번 문제 검증 실패: {e}")
            continue

    # 검증 통과 조건: 문제 수가 요청한 수와 일치하고 최소 1개 이상 존재
    is_valid = len(valid_questions) == expected_count
    return valid_questions, is_valid