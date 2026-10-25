import pytest
from models.question import Question
from utils.validator import validate_and_filter_questions


def test_question_model_creation():
    """Question 데이터 모델 기본 동작 테스트"""
    q = Question(
        id="q_1",
        q="'억까'의 뜻은?",
        options=["억지 비난", "억수 까칠", "억만장자", "억울함"],
        answer=1,
        explanation="억지로 까다의 줄임말입니다.",
        difficulty="쉬움"
    )
    assert q.id == "q_1"
    assert q.answer == 1
    assert len(q.options) == 4


def test_validator_with_valid_data():
    """문제 데이터 검증 모듈 정성 동작 테스트"""
    raw_data = [
        {
            "id": "q_1",
            "q": "'중꺾마'의 뜻은?",
            "options": ["중요한 것은 꺾이지 않는 마음", "중국 마케팅", "중간에 꺾임", "중요 순간 마술"],
            "answer": 1,
            "explanation": "중요한 것은 꺾이지 않는 마음의 줄임말입니다.",
            "difficulty": "보통"
        }
    ]
    valid_list, is_valid = validate_and_filter_questions(raw_data, expected_count=1, difficulty="보통")
    assert is_valid is True
    assert len(valid_list) == 1
    assert valid_list[0].answer == 1


def test_validator_with_invalid_data():
    """잘못된 문제 데이터 거부 테스트"""
    raw_data = [
        {
            "id": "q_bad",
            "q": "잘못된 문제",
            "options": ["1번", "2번"],  # 보기가 2개뿐임 (4개 미만)
            "answer": 5,             # 범위를 벗어난 정답 번호
            "explanation": "오류 테스트",
            "difficulty": "쉬움"
        }
    ]
    valid_list, is_valid = validate_and_filter_questions(raw_data, expected_count=1, difficulty="쉬움")
    assert len(valid_list) == 0