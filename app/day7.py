# Day 7
# Theming and Layout

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

@st.cache_data
def call_cortex_llm(prompt_text):
    model = "claude-3-5-sonnet"
    df = session.range(1).select(
        ai_complete(model=model, prompt=prompt_text).alias("response")
    )
    return json.loads(df.collect()[0][0])

# --- App UI ---

# 메인 영역 입력 위젯
st.subheader(":material/input: 입력 콘텐츠")
content = st.text_input("콘텐츠 URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")

# [실습] st.sidebar를 사용하여 부가적인 설정(Tone, Word count)과 생성 버튼을 사이드바로 옮기세요.
# 여기에 코드를 작성하세요
# with st.sidebar:
#     ...

st.info("사이드바 코드를 작성하세요.")

# 편의상 실습 전 기본 변수 설정 (에러 방지용)
if 'tone' not in locals(): tone = "Professional"
if 'word_count' not in locals(): word_count = 100

# 결과 출력 (사이드바 버튼 클릭 시 로직에 따라 수정 필요할 수 있음)
if "result" in st.session_state:
    st.subheader("Generated Post:")
    st.markdown(st.session_state.result)

st.divider()
st.caption("Day 7: Theming and Layout | 30 Days of AI")