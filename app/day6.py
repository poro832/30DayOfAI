# Day 6
# Status UI for Long-Running Task

import streamlit as st
import json
import time
from snowflake.snowpark.functions import ai_complete

# Snowflake 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# LLM 호출 함수
@st.cache_data
def call_cortex_llm(prompt_text):
    model = "claude-3-5-sonnet"
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt_text).alias("response")
    )
    return json.loads(df.collect()[0][0])

st.title(":material/post: LinkedIn 게시물 생성기 v2")

# 입력 위젯
content = st.text_input("콘텐츠 URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")
tone = st.selectbox("어조 (Tone):", ["Professional", "Casual", "Funny"])
word_count = st.slider("단어 수:", 50, 300, 100)

if st.button("Generate Post"):
    
    # [실습] st.status를 사용하여 "엔진 구동 중..." 상태를 표시하고 단계를 보여주세요.
    # 힌트: with st.status(...) as status: 사용
    
    # 여기에 코드를 작성하세요
    st.write("실습 코드를 작성해주세요.")
    
    # 내부 로직 예시 (참고용)
    # 1. 프롬프트 작성
    # prompt = f"Create a {tone} LinkedIn post about {content} in {word_count} words."
    # 2. 호출
    # response = call_cortex_llm(prompt)
    # 3. 완료 업데이트
    # status.update(...)
    
    
    # 결과 출력
    # st.subheader("Generated Post:")
    # st.markdown(response)

st.divider()
st.caption("Day 6: Status UI for Long-Running Task | 30 Days of AI")