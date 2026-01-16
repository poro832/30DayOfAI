# Day 13
# Adding a System Prompt

import streamlit as st

st.title(":material/chat: 페르소나 챗봇")

# [실습 1] 시스템 프롬프트를 저장할 Session State("system_prompt")를 초기화하세요.
# 여기에 코드를 작성하세요
pass

# 사이드바: 페르소나 선택
with st.sidebar:
    st.header("페르소나 선택")
    if st.button("해적 (Pirate)"):
        st.session_state.system_prompt = "You are a pirate. Speak like one!"
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

# ... (기록 표시 로직 생략) ...

if prompt := st.chat_input("..."):
    # ... (사용자 메시지 처리) ...
    
    # [실습 2] 시스템 프롬프트를 대화 맨 앞에 주입(Injection)하여 LLM에게 성격을 부여하세요.
    
    # 여기에 코드를 작성하세요 (full_prompt 구성)
    pass
    
    st.info("시스템 프롬프트 주입 로직을 완성하세요.")

st.divider()
st.caption("Day 13: Adding a System Prompt | 30 Days of AI")
