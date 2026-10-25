import os
from pathlib import Path
import streamlit as st

# 프로젝트 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"

# Gemini API 모델 설정 (SDK 공식 호환 모델명)
GEMINI_MODEL_NAME = "gemini-3.5-flash"

# 앱 기본 설정값 및 상수 정의
DEFAULT_QUIZ_COUNT = 10
DEFAULT_DIFFICULTY = "보통"
DIFFICULTY_LEVELS = ["쉬움", "보통", "어려움"]
AVAILABLE_QUIZ_COUNTS = [5, 10, 15, 20]


def get_api_key() -> str:
    """Streamlit secrets 또는 환경 변수에서 Gemini API 키를 가져옵니다."""
    # 1. Streamlit secrets (.streamlit/secrets.toml) 확인
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    # 2. OS 환경 변수 확인 (Fallback)
    return os.getenv("GEMINI_API_KEY", "")