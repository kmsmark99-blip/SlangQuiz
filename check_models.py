import streamlit as st
from google import genai

# .streamlit/secrets.toml의 키를 사용해 클라이언트 생성
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

print("\n=== [사용 가능한 generateContent 모델 목록] ===")
for model in client.models.list():
    # 퀴즈 생성(generateContent)을 지원하는 모델명만 출력
    if "generateContent" in (model.supported_actions or []):
        print(model.name)
print("===========================================\n")