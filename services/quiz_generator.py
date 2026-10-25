import json
import logging
import time
from pathlib import Path
from google import genai
from google.genai import types
import config
from models.question import Question
from utils.validator import validate_and_filter_questions

logger = logging.getLogger(__name__)

SAMPLE_DATA_PATH = Path(config.DATA_DIR) / "sample_questions.json"


def load_sample_questions(count: int = 10, difficulty: str = "보통") -> list[Question]:
    """API 실패 시 로드되는 예시 문제 데이터"""
    try:
        if SAMPLE_DATA_PATH.exists():
            with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                questions, _ = validate_and_filter_questions(
                    raw_data, expected_count=len(raw_data), difficulty=difficulty
                )
                return questions[:count]
    except Exception as e:
        logger.error(f"예시 문제 로드 실패: {e}")

    default_q = Question(
        id="fallback_01",
        q="'억까'의 올바른 의미는 무엇일까요?",
        options=["억지로 까다 (억지로 비난함)", "억수로 까칠함", "억만장자", "억울한 일"],
        answer=1,
        explanation="'억까'는 억지로 깎아내리다/비난하다의 줄임말입니다.",
        difficulty=difficulty,
    )
    return [default_q]


def generate_quiz_from_gemini(
    difficulty: str = "보통", count: int = 10, max_retries: int = 2
) -> tuple[list[Question], bool]:
    """Gemini API를 사용하여 정제된 한국어 신조어 퀴즈를 출제합니다."""
    api_key = config.get_api_key()

    if not api_key:
        logger.warning("API 키 누락으로 예시 문제를 로드합니다.")
        return load_sample_questions(count=count, difficulty=difficulty), False

    system_instruction = (
        "You are a native Korean linguistics expert. "
        "Create Korean slang quiz questions strictly using authentic Korean terms. "
        "NEVER translate Korean terms into English or any other language during generation. "
        "Do NOT use translated words like '에어로', '플레이하는', '열매우'. "
        "Keep terms like '개에바', '알잘딱깔센', '늙크크', '중꺾마', '폼 미쳤다' exactly as they are in Korean."
    )

    prompt = f"""
    대한민국 청소년과 인터넷 문화에서 사용되는 신조어(예: '억까', '알잘딱깔센', '늙크크', '폼 미쳤다', '중꺾마' 등)에 관한 객관식 퀴즈 {count}개를 출제하세요.
    난이도: {difficulty}

    [출력 규칙]
    1. 모든 질문, 보기, 해설은 자연스러운 대한민국 표준 한국어로만 작성하세요.
    2. 질문(q): "~의 올바른 뜻은 무엇일까요?", "다음 신조어 문장을 바른 표준어로 바꾼 것은?" 등 시험 문제 형식.
    3. 보기(options): 정확히 4개의 한국어 보기 (정답 1개, 오답 3개).
    4. 정답(answer): 1~4 중 정수.
    5. 해설(explanation): 바른 한국어 표준어 설명.
    """

    json_schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "q": {"type": "STRING"},
                "options": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                },
                "answer": {"type": "INTEGER"},
                "explanation": {"type": "STRING"},
            },
            "required": ["q", "options", "answer", "explanation"],
        },
    }

    for attempt in range(1, max_retries + 1):
        try:
            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model=config.GEMINI_MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=json_schema,
                    temperature=0.1,
                ),
            )

            if response and response.text:
                parsed_data = json.loads(response.text)
                valid_questions, _ = validate_and_filter_questions(
                    parsed_data, expected_count=count, difficulty=difficulty
                )

                clean_questions = [
                    q
                    for q in valid_questions
                    if "에어로" not in q.q and "에어로" not in "".join(q.options)
                ]

                if len(clean_questions) > 0:
                    logger.info(f"정상 검증된 퀴즈 {len(clean_questions)}개 생성 완료")
                    return clean_questions, True

        except Exception as e:
            logger.error(f"생성 실패 (시도 {attempt}/{max_retries}): {e}")

        time.sleep(1)

    return load_sample_questions(count=count, difficulty=difficulty), False