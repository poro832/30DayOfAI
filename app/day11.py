# Day 11
# Displaying Chat History

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
    # 실제로는 Cortex를 호출해야 함
    return f"I received your context. Prompt length: {len(prompt_text)}"

st.title(":material/chat: 문맥을 기억하는 챗봇")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요!"}]

# 사이드바: 초기화 버튼
with st.sidebar:
    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

# 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("메시지 입력..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        # [실습] 이전 대화 기록을 모두 합쳐서 하나의 '문맥(Context)' 문자열을 만들고, 
        # 이를 프롬프트에 포함시켜 LLM을 호출하세요.
        
        # 여기에 코드를 작성하세요
        full_prompt = prompt # 임시 (실습 시 수정 필요)
        
        response = call_llm(full_prompt)
        st.write(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

st.divider()
st.caption("Day 11: Displaying Chat History | 30 Days of AI")