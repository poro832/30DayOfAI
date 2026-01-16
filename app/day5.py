# Day 5
# Build a Post Generator App

import streamlit as st
import json
from snowflake.snowpark.functions import ai_complete

# Snowflake 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# LLM 호출 함수 (캐싱 적용됨)
@st.cache_data
def call_cortex_llm(prompt_text):
    model = "claude-3-5-sonnet"
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt_text).alias("response")
    )
    response_raw = df.collect()[0][0]
    return json.loads(response_raw)

# --- App UI ---
st.title(":material/post: LinkedIn 게시물 생성기")

# 입력 위젯
content = st.text_input("콘텐츠 URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")
tone = st.selectbox("어조 (Tone):", ["Professional", "Casual", "Funny"])
word_count = st.slider("단어 수:", 50, 300, 100)

if st.button("Generate Post"):
    # [실습] f-string을 사용하여 tone, word_count, content 변수가 포함된 프롬프트를 작성하세요.
    
    # 여기에 코드를 작성하세요
    prompt = "..."
    
    st.info("코드를 완성하고 실행하세요.") # 실습 안내
    
    # 실행 결과 확인 (작성 후 주석 해제)
    # response = call_cortex_llm(prompt)
    # st.subheader("Generated Post:")
    # st.markdown(response)

st.divider()
st.caption("Day 5: Build a Post Generator App | 30 Days of AI")