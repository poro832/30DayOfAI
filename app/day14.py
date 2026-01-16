# Day 14
# Adding Avatars and Error Handling

import streamlit as st

st.title(":material/account_circle: 아바타 및 에러 처리")

# ... (기존 챗봇 로직들) ...

if prompt := st.chat_input("..."):
    # [실습 1] st.chat_message에 아바타(avatar) 아이콘을 적용해보세요.
    
    # 여기에 코드를 작성하세요
    st.write(prompt)
    
    # [실습 2] 에러 발생 시 앱이 멈추지 않도록 예외 처리(Try-Except) 코드를 작성하세요.
    
    # 여기에 코드를 작성하세요 (try-except 블록)
    pass
    
    st.warning("아직 에러 처리가 적용되지 않았습니다.")

st.divider()
st.caption("Day 14: Adding Avatars and Error Handling | 30 Days of AI")