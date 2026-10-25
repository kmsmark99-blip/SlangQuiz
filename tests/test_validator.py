import pytest
from utils.validator import validate_and_filter_questions


def test_valid_questions_parsing():
    """정상 문제 데이터 검증 테스트"""
    sample_raw = [
        {
            "id": "t1",
            "q": "'억까'의 의미는?",
            "options": ["억지로 까다", "억수로 까칠함", "억만장자", "억울함"],
            "answer": 1,
            "explanation": "억지로 깎아내리다의 줄임말입니다.",
            "difficulty": "쉬움"
        }
    ]
    questions, is_valid = validate_and_filter_questions(sample_raw, expected_count=1, difficulty="쉬움")
    assert is_valid is True
    assert len(questions) == 1
    assert questions[0].q == "'억까'의 의미는?"
    assert questions[0].answer == 1


def test_invalid_options_count():
    """보기가 4개가 아닌 경우 검증 실패 테스트"""
    sample_raw = [
        {
            "q": "잘못된 문제",
            "options": ["보기1", "보기2", "보기3"],
            "answer": 1,
            "explanation": "설명"
        }
    ]
    questions, is_valid = validate_and_filter_questions(sample_raw, expected_count=1)
    assert is_valid is False
    assert len(questions) == 0


def test_invalid_answer_range():
    """정답 범위를 벗어난 경우 테스트"""
    sample_raw = [
        {
            "q": "정답 범위 오류 문제",
            "options": ["1", "2", "3", "4"],
            "answer": 5,
            "explanation": "설명"
        }
    ]
    questions, is_valid = validate_and_filter_questions(sample_raw, expected_count=1)
    assert is_valid is False
    assert len(questions) == 0