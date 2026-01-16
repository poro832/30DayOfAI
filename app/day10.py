# Day 10
# Your First Chatbot (with State)

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

def call_llm(prompt_text):
    # 간단한 응답 시뮬레이션 (실제 연결 시 ai_complete 사용)
    return f"Echo: {prompt_text}"

st.title(":material/chat: 첫 번째 챗봇 만들기")

# [실습 1] 메시지 기록("messages")이 없으면 빈 리스트로 초기화하세요.
# 여기에 코드를 작성하세요
pass

# [실습 2] 저장된 모든 메시지를 화면에 다시 그리는(Re-render) 코드를 작성하세요.
# 여기에 코드를 작성하세요
pass

# 채팅 입력 처리
if prompt := st.chat_input("무엇을 도와드릴까요?"):
    
    # [실습 3] 사용자 메시지를 Session State에 추가하고(append), 화면에 표시(write)하세요.
    
    # 여기에 코드를 작성하세요
    pass
    
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        response = call_llm(prompt)
        st.write(response)
    
    # AI 응답 저장
    if "messages" in st.session_state:
        st.session_state.messages.append({"role": "assistant", "content": response})

st.divider()
st.caption("Day 10: Your First Chatbot (with State) | 30 Days of AI")