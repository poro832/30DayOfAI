# Day 2
# Hello, Cortex!

import streamlit as st
from snowflake.snowpark.functions import ai_complete
import json

st.title(":material/smart_toy: Hello, Cortex!")

# Snowflake 연결
try:
    # SiS (Streamlit in Snowflake) 환경에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 개발 환경 및 Streamlit 커뮤니티 클라우드 환경에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 모델 및 프롬프트 설정
model = "claude-3-5-sonnet"
prompt = st.text_input("프롬프트를 입력하세요 (Enter your prompt):")

# LLM 추론 실행
if st.button("Generate Response"):
    # [실습] ai_complete 함수를 사용하여 선택한 모델과 프롬프트로 응답을 생성하는 코드를 작성하세요.
    # 힌트: session.range(1).select(...) 와 ai_complete(...) 사용
    
    # 여기에 코드를 작성하세요
    pass
    
    # ---------------------------------------------------------
    
    # 결과 수집 및 출력 확인 코드 (작성 후 주석 해제)
    # response_raw = df.collect()[0][0]
    # response = json.loads(response_raw)
    # st.write(response)
    
    st.info("코드를 완성하고 실행 버튼을 눌러주세요.") # 실습 안내용 메시지

# 하단 푸터
st.divider()
st.caption("Day 2: Hello, Cortex! | 30 Days of AI")