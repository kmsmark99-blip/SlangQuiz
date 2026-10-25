import logging
from google import genai
from google.genai import types
import config

logger = logging.getLogger(__name__)


def generate_ai_feedback(username: str, score: float, wrong_questions: list[dict]) -> str:
    """채점 결과와 오답 정보를 바탕으로 Gemini AI 교정 리포트를 생성합니다."""
    api_key = config.get_api_key()

    if not api_key:
        return f"🎉 **{username}**님, 퀴즈를 모두 완료하셨습니다! (점수: {score:.1f}점)"

    wrong_summary = ""
    if wrong_questions:
        wrong_summary = "오답 문항 내용:\n" + "\n".join([
            f"- 질문: {q['q']} | 제출 답: {q['user_ans']}번 | 정답: {q['correct_ans']}번 | 해설: {q['explanation']}"
            for q in wrong_questions
        ])
    else:
        wrong_summary = "모든 문제를 맞히셨습니다!"

    prompt = f"""
    당신은 칭찬과 따뜻한 격려를 전하는 한국어 언어 감수성 멘토입니다.
    사용자 이름: {username}
    최종 점수: {score:.1f}점 / 100점
    {wrong_summary}

    [작성 규칙]
    1. 총 3~4문장의 친절하고 다정한 말투(해요체)로 작성할 것.
    2. 무조건 비난하지 말고, 신조어를 이해하면서도 정제된 바른 표준어를 사용하는 긍정적인 가이드를 제시할 것.
    3. Markdown 형식을 사용할 것.
    """

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=config.GEMINI_MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4)
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        logger.error(f"피드백 생성 오류: {e}")

    return f"👏 **{username}**님, 퀴즈 완수를 축하드립니다! 앞으로도 바른 언어 습관을 함께 만들어가요."