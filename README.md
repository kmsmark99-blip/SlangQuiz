# ✏️ AI 기반 우리말 신조어 퀴즈 웹 서비스

Google Gemini API와 Streamlit, SQLite를 활용하여 제작된 **실시간 신조어 객관식 퀴즈 및 언어 감수성 분석 웹 애플리케이션**입니다.

---

## 📌 주요 기능

1. **AI 실시간 퀴즈 생성:** 난이도(쉬움/보통/어려움)와 문제 수(5/10문항)에 맞춰 Gemini API가 신조어 문제를 실시간 생성
2. **네트워크 장애 대응 (Fallback):** API 장애나 인터넷 연결 끊김 시 내장된 예시 문제로 자동 전환
3. **인터페이스 & 번역 방지:** 브라우저 자동 번역으로 인한 한글 뭉개짐 현상을 CSS 태그로 완벽 차단
4. **SQLite 데이터베이스 연동:** 사용자, 문제, 퀴즈 수행 이력, 문제별 답안 로그를 트랜잭션으로 저장
5. **명예의 전당 (실시간 순위표):** 난이도별 및 전체 실시간 랭킹 집계 (동점자 발생 시 선달성자 우대)
6. **문제별 오답률 통계:** 오답률이 높은 핵심 문제를 가공하여 오답률 Top 5 표로 시각화
7. **Gemini AI 언어 감수성 총평:** 퀴즈 점수 및 틀린 문제를 분석하여 다정한 어조로 맞춤형 가이드 제공
8. **오답 노트 복습:** 제출 후 '틀린 문제만 모아보기' 필터링으로 효율적인 복습 지원

---

## 📂 프로젝트 폴더 구조

```text
slangQuiz/
├── app.py                     # Streamlit 메인 실행 파일
├── config.py                  # 프로젝트 설정 및 환경 변수 로더
├── requirements.txt           # 필요 라이브러리 목록
├── README.md                  # 프로젝트 사용 설명서
├── .gitignore                 # Git 제외 설정 파일
├── check_models.py            # Gemini API 사용 가능 모델 조회 스크립트
├── data/
│   └── sample_questions.json  # 퀴즈 샘플 데이터
├── database/
│   ├── db.py                  # SQLite 트랜잭션 및 데이터 처리 로직
│   ├── db_manager.py          # DB 연결 및 관리 로직
│   └── schema.sql             # 데이터베이스 테이블 정의 SQL
├── services/
│   ├── quiz_generator.py      # Gemini API 문제 생성 서비스
│   ├── feedback_generator.py  # Gemini AI 맞춤 피드백 생성 서비스
│   ├── ranking_service.py     # 사용자 랭킹 서비스
│   └── statistics_service.py  # 통계 데이터 처리 서비스
├── models/
│   ├── question.py            # Pydantic 기반 퀴즈 데이터 모델
│   ├── answer_log.py          # 정/오답 기록 모델
│   ├── record.py              # 사용자 기록 모델
│   └── user.py                # 사용자 프로필 모델
├── static/
│   └── css/
│       └── style.css          # 커스텀 스타일시트
├── utils/
│   ├── quiz_logic.py          # 퀴즈 진행 및 계산 로직
│   └── validator.py           # 문제 데이터 유효성 검증기
└── tests/
    ├── test_quiz_logic.py     # 퀴즈 모델 및 기본 로직 단위 테스트
    ├── test_records.py        # 기록 저장 단위 테스트
    ├── test_statistics.py     # 통계 기능 단위 테스트
    └── test_validator.py      # 유효성 검증 단위 테스트