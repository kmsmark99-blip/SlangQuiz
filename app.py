import streamlit as st
import config
from models.question import Question
from services import quiz_generator, feedback_generator
from database import db

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="AI 기반 우리말 신조어 퀴즈",
    page_icon="✏️",
    layout="centered"
)

# 2. 브라우저 자동 번역 방지 스타일 및 UI 커스텀 CSS
st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            -webkit-translate: no !important;
            translate: no !important;
        }
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 1px solid #e9ecef;
        }
    </style>
    """,
    unsafe_allow_html=True
)


def init_session_state():
    """세션 상태 초기화"""
    if "quiz_started" not in st.session_state:
        st.session_state.quiz_started = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "보통"
    if "quiz_count" not in st.session_state:
        st.session_state.quiz_count = config.DEFAULT_QUIZ_COUNT
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "current_step" not in st.session_state:
        st.session_state.current_step = 0
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False
    if "db_saved" not in st.session_state:
        st.session_state.db_saved = False


def render_start_screen():
    """STEP 4: 퀴즈 시작 화면"""
    st.title("✏️ AI 기반 우리말 신조어 퀴즈")
    st.caption("신조어는 바르게, 소통은 넓게! Gemini AI가 생성하는 바른 우리말 언어 감수성 퀴즈")

    st.divider()

    st.subheader("🎮 퀴즈 설정")

    username_input = st.text_input(
        "사용자 이름 (닉네임)",
        value=st.session_state.username,
        placeholder="예: 홍길동 (2자 이상 입력)",
        max_chars=12
    )

    col1, col2 = st.columns(2)

    with col1:
        difficulty_choice = st.selectbox(
            "🎯 난이도 선택",
            options=config.DIFFICULTY_LEVELS,
            index=config.DIFFICULTY_LEVELS.index(st.session_state.difficulty)
        )

    with col2:
        count_choice = st.select_slider(
            "📝 문제 수 선택",
            options=config.AVAILABLE_QUIZ_COUNTS,
            value=st.session_state.quiz_count
        )

    if st.button("🚀 퀴즈 시작하기", use_container_width=True):
        clean_name = username_input.strip()

        if not clean_name or len(clean_name) < 2:
            st.error("⚠️ 이름은 최소 2자 이상 입력해 주세요.")
            return

        st.session_state.username = clean_name
        st.session_state.difficulty = difficulty_choice
        st.session_state.quiz_count = count_choice

        st.session_state.user_answers = {}
        st.session_state.current_step = 0
        st.session_state.quiz_submitted = False
        st.session_state.db_saved = False

        with st.spinner("Gemini AI가 맞춤형 퀴즈 문제를 생성하고 있습니다..."):
            questions, is_ai = quiz_generator.generate_quiz_from_gemini(
                difficulty=difficulty_choice,
                count=count_choice
            )

        st.session_state.questions = questions
        st.session_state.quiz_started = True
        st.rerun()


def render_quiz_screen():
    """STEP 5: 객관식 문제 풀이 화면"""
    questions = st.session_state.questions
    total_q = len(questions)
    curr_idx = st.session_state.current_step
    curr_q: Question = questions[curr_idx]

    st.caption(f"👤 **{st.session_state.username}**님의 퀴즈 풀이 | 난이도: **{st.session_state.difficulty}**")
    
    progress_val = (curr_idx + 1) / total_q
    st.progress(progress_val, text=f"문제 진행률: {curr_idx + 1} / {total_q} ({int(progress_val * 100)}%)")

    st.divider()

    st.subheader(f"Q{curr_idx + 1}. {curr_q.q}")

    saved_answer = st.session_state.user_answers.get(curr_idx, None)
    
    selected_option_str = st.radio(
        "올바른 답을 선택하세요:",
        options=curr_q.options,
        index=curr_q.options.index(curr_q.options[saved_answer - 1]) if saved_answer else None,
        key=f"radio_q_{curr_idx}"
    )

    if selected_option_str:
        selected_num = curr_q.options.index(selected_option_str) + 1
        st.session_state.user_answers[curr_idx] = selected_num

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if curr_idx > 0:
            if st.button("⬅️ 이전 문제", use_container_width=True):
                st.session_state.current_step -= 1
                st.rerun()

    with col2:
        if curr_idx < total_q - 1:
            if st.button("다음 문제 ➡️", use_container_width=True):
                if curr_idx not in st.session_state.user_answers:
                    st.warning("⚠️ 답안을 선택한 후 이동해 주세요!")
                else:
                    st.session_state.current_step += 1
                    st.rerun()

    with col3:
        if curr_idx == total_q - 1:
            if st.button("🎯 제출하기", type="primary", use_container_width=True):
                unanswered = [i + 1 for i in range(total_q) if i not in st.session_state.user_answers]
                if unanswered:
                    st.error(f"⚠️ 풀어지지 않은 문제가 있습니다: {unanswered}번")
                else:
                    st.session_state.quiz_submitted = True
                    st.rerun()


def render_result_screen():
    """STEP 10, 11: 결과 리포트 및 통합 화면"""
    st.title("🏆 퀴즈 결과 및 분석 리포트")
    
    questions = st.session_state.questions
    total_q = len(questions)
    user_answers = st.session_state.user_answers
    username = st.session_state.username
    
    correct_count = 0
    wrong_questions = []

    for idx, q in enumerate(questions):
        user_ans = user_answers.get(idx)
        if user_ans == q.answer:
            correct_count += 1
        else:
            wrong_questions.append({
                "index": idx + 1,
                "q": q.q,
                "user_ans": user_ans,
                "correct_ans": q.answer,
                "user_opt": q.options[user_ans - 1] if user_ans else "미제출",
                "correct_opt": q.options[q.answer - 1],
                "explanation": q.explanation
            })

    score = (correct_count / total_q) * 100
    wrong_count = total_q - correct_count

    # 1. 제출 전 이전 최고 기록 조회
    previous_best = db.get_user_best_score(username)

    # 2. DB 저장 (최초 1회)
    if "db_saved" not in st.session_state or not st.session_state.db_saved:
        saved_ok = db.save_quiz_session(
            username=username,
            difficulty=st.session_state.difficulty,
            questions=questions,
            user_answers=user_answers
        )
        if saved_ok:
            st.session_state.db_saved = True

    # 3. 성적 요약 UI
    st.write(f"### 👤 {username}님의 성적 요약")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="최종 점수", value=f"{score:.0f}점")
    with m_col2:
        st.metric(label="정답 수", value=f"{correct_count}개")
    with m_col3:
        st.metric(label="오답 수", value=f"{wrong_count}개")
    with m_col4:
        best_val = f"{previous_best['max_score']:.0f}점" if previous_best else f"{score:.0f}점"
        st.metric(label="개인 최고 기록", value=best_val)

    if previous_best and score > previous_best["max_score"]:
        st.balloons()
        st.success(f"🎉 축하합니다! 기존 최고 기록({previous_best['max_score']:.0f}점)을 경신하셨습니다!")

    st.divider()

    # 4. 실시간 순위표
    st.subheader("🥇 명예의 전당 (실시간 순위표)")
    selected_diff = st.radio("순위 조회 난이도 선택:", options=["전체", "쉬움", "보통", "어려움"], horizontal=True, key="rank_diff")
    leaderboard_data = db.get_leaderboard(difficulty=selected_diff, limit=10)

    if leaderboard_data:
        table_data = []
        for rank_item in leaderboard_data:
            medal = "🥇" if rank_item["rank"] == 1 else "🥈" if rank_item["rank"] == 2 else "🥉" if rank_item["rank"] == 3 else f"{rank_item['rank']}위"
            table_data.append({
                "순위": medal,
                "닉네임": rank_item["username"],
                "최고 점수": f"{rank_item['score']:.0f}점",
                "난이도": rank_item["difficulty"]
            })
        st.table(table_data)
    else:
        st.caption("아직 기록된 순위 정보가 없습니다.")

    st.divider()

    # 5. 문제별 오답률 통계
    st.subheader("📈 오답률 높은 핵심 문제 Top 5")
    stats_diff = st.radio("통계 조회 난이도 선택:", options=["전체", "쉬움", "보통", "어려움"], horizontal=True, key="stats_diff")
    error_stats = db.get_question_error_rates(difficulty=stats_diff)

    if error_stats:
        wrong_stats = [item for item in error_stats if item["error_rate"] > 0][:5]

        if wrong_stats:
            stats_table = []
            for idx, item in enumerate(wrong_stats, 1):
                sample_note = " ⚠️(표본부족)" if item["total_answers"] < 3 else ""
                stats_table.append({
                    "순위": f"Top {idx}",
                    "신조어/문제": item["question"],
                    "난이도": item["difficulty"],
                    "오답률": f"{item['error_rate']}%",
                    "응답 기록": f"{item['wrong_answers']}회 오답 / 총 {item['total_answers']}회{sample_note}"
                })
            st.table(stats_table)
        else:
            st.success("👏 선택한 난이도에서 오답이 발생한 문제가 없습니다!")
    else:
        st.caption("등록된 문제 통계 데이터가 없습니다.")

    st.divider()

    # 6. Gemini AI 교정 총평
    st.subheader("💡 Gemini AI 언어 감수성 총평")
    with st.spinner("AI 피드백 분석 중..."):
        ai_feedback = feedback_generator.generate_ai_feedback(
            username=username,
            score=score,
            wrong_questions=wrong_questions
        )
    st.info(ai_feedback)

    st.divider()

    # 7. 오답 노트 및 상세 해설
    st.subheader("📝 상세 오답 복습 및 정답 해설")
    
    only_wrong = st.checkbox("❌ 틀린 문제만 모아보기", value=False)

    for idx, q in enumerate(questions, 1):
        user_ans = user_answers.get(idx - 1)
        is_correct = user_ans == q.answer

        if only_wrong and is_correct:
            continue

        status_tag = "✅ 정답" if is_correct else "❌ 오답"
        with st.expander(f"{status_tag} Q{idx}. {q.q}"):
            st.write(f"**내가 선택한 답:** {user_ans}번 ({q.options[user_ans - 1]})")
            st.write(f"**올바른 정답:** {q.answer}번 ({q.options[q.answer - 1]})")
            st.caption(f"💡 **해설:** {q.explanation}")

    st.divider()

    if st.button("🔄 새로운 퀴즈 도전하기", use_container_width=True):
        st.session_state.quiz_started = False
        st.session_state.quiz_submitted = False
        st.session_state.db_saved = False
        st.rerun()


def main():
    init_session_state()

    if not st.session_state.quiz_started:
        render_start_screen()
    elif not st.session_state.quiz_submitted:
        render_quiz_screen()
    else:
        render_result_screen()


if __name__ == "__main__":
    main()