# Day 4
# Caching your App

import streamlit as st
import time
import json
from snowflake.snowpark.functions import ai_complete

st.title(":material/cached: 앱 캐싱 적용하기 (Caching your App)")

# Snowflake 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# [실습] Streamlit의 캐싱 데코레이터를 아래 함수에 적용하여 불필요한 LLM 재호출을 방지하세요.
# 여기에 데코레이터를 작성하세요 (예: @st...)

def call_cortex_llm(prompt_text):
    model = "claude-3-5-sonnet"
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt_text).alias("response")
    )
    
    # 응답 파싱
    response_raw = df.collect()[0][0]
    response_json = json.loads(response_raw)
    return response_json

prompt = st.text_input("프롬프트 입력", "하늘은 왜 파란가요?")

if st.button("Submit"):
    start_time = time.time()
    
    # 함수 호출
    response = call_cortex_llm(prompt)
    
    end_time = time.time()
    
    st.success(f"*소요 시간: {end_time - start_time:.2f} 초*")
    st.write(response)

st.divider()
st.caption("Day 4: Caching your App | 30 Days of AI")