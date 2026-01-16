# Day 9
# Understanding Session State

import streamlit as st

st.title(":material/memory: Session State 이해하기")

col1, col2 = st.columns(2)

# --- 컬럼 1: 잘못된 방법 (초기화 문제) ---
with col1:
    st.header("일반 변수")
    st.write("클릭할 때마다 초기화됩니다.")
    count_wrong = 0
    if st.button("증가 (+1)", key="std_plus"):
        count_wrong += 1
    st.metric("Count", count_wrong)

# --- 컬럼 2: 올바른 방법 (Session State) ---
with col2:
    st.header("Session State")
    st.write("값이 유지됩니다.")

    # [실습] Session State를 초기화하고 값을 업데이트하는 코드를 작성하세요.
    # 1. 초기화 (Key가 없을 때만 생성)
    # 2. 버튼 클릭 시 값 증가
    # 3. 값 표시
    
    # 여기에 코드를 작성하세요
    pass 
    
    st.info("코드를 완성하세요.")

st.divider()
st.caption("Day 9: Understanding Session State | 30 Days of AI")
