# Day 8
# Meet the Chat Elements

import streamlit as st

st.title(":material/chat: 채팅 요소 알아보기")

# 1. 정적 메시지 표시 (Displaying Static Messages)
# [실습] st.chat_message를 사용하여 'user'와 'assistant'의 대화를 표시하는 코드를 작성하세요.

# 여기에 코드를 작성하세요
st.info("정적 메시지 표시 실습 공간")


# 2. 채팅 입력 (Chat Input)
prompt = st.chat_input("여기에 메시지를 입력하세요...")

# 3. 입력에 반응하기 (Reacting to Input)
if prompt:
    # 왈러스 연산자(:=)를 사용하면 입력과 할당을 동시에 할 수 있다는 점을 상기하세요.
    
    with st.chat_message("user"):
        st.write(prompt)
        
    with st.chat_message("assistant"):
        st.write(f"방금 입력하신 내용: '{prompt}' (아직은 기억력이 없습니다!)")

st.divider()
st.caption("Day 8: Meet the Chat Elements | 30 Days of AI")