# Day 12
# Streaming Responses

import streamlit as st
import time
# Snowflake 연결 생략 (이전 Day와 동일하다고 가정)

def call_llm_dummy(prompt):
    return "This is a simulated streaming response from Snowflake Cortex."

st.title(":material/chat: 스트리밍 챗봇")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # [실습] 제너레이터(Generator) 함수를 만들어 타자 치는 효과(Streaming)를 구현하세요.
    # 힌트: yield와 time.sleep() 사용
    
    # 여기에 함수를 작성하세요: def stream_generator(): ...
    def stream_generator():
        yield "실습 "
        time.sleep(0.1)
        yield "코드가 "
        time.sleep(0.1)
        yield "필요합니다."
    
    with st.chat_message("assistant"):
        # [실습] st.write_stream을 사용하여 제너레이터 출력을 화면에 그리세요.
        
        # 여기에 코드를 작성하세요
        st.write("실습 진행 필요")
        response = "..."
        
    st.session_state.messages.append({"role": "assistant", "content": response})

st.divider()
st.caption("Day 12: Streaming Responses | 30 Days of AI")