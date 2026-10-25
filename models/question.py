from pydantic import BaseModel, Field, field_validator
from typing import List


class Question(BaseModel):
    id: str = Field(..., description="문제 고유 식별자")
    q: str = Field(..., description="신조어 및 맞춤법 관련 질문/제시문")
    options: List[str] = Field(..., description="4지 선다형 보기 목록")
    answer: int = Field(..., description="정답 보기 번호 (1~4)")
    explanation: str = Field(..., description="바른 우리말 및 맥락 해설")
    difficulty: str = Field(default="보통", description="문제 난이도")

    @field_validator("options")
    def validate_options_count_and_uniqueness(cls, v):
        if len(v) != 4:
            raise ValueError("보기는 정확히 4개여야 합니다.")
        # 빈 문자열 보기 검사
        if any(not opt.strip() for opt in v):
            raise ValueError("빈 보기가 포함되어 있습니다.")
        # 보기 중복 검사
        if len(set(v)) != len(v):
            raise ValueError("보기 중 중복된 내용이 있습니다.")
        return v

    @field_validator("answer")
    def validate_answer_range(cls, v):
        if not (1 <= v <= 4):
            raise ValueError("정답 번호는 1과 4 사이의 정수여야 합니다.")
        return v

    @field_validator("q", "explanation")
    def validate_non_empty_str(cls, v):
        if not v or not v.strip():
            raise ValueError("질문과 해설은 비어 있을 수 없습니다.")
        return v.strip()