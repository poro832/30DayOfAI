# Day 1
# Snowflake 연결 (Connect to Snowflake)

import streamlit as st

st.title(":material/vpn_key: Day 1: Snowflake 연결 확인")

# Snowflake 연결
try:
    # SiS (Streamlit in Snowflake) 환경에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 개발 환경 및 Streamlit 커뮤니티 클라우드 환경에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Snowflake 버전 조회 쿼리 실행
version = session.sql("SELECT CURRENT_VERSION()").collect()[0][0]

# 결과 출력
st.success(f"연결 성공! Snowflake Version: {version}")
