# Day 14: Polishing & Error Handling

# 0. 목표

<aside>
💡 **완성도 있는 앱을 위한 마무리 작업: 아바타와 에러 처리**

1. 챗봇의 프로필 사진(Avatar)을 내 마음대로 설정합니다.
2. `try-except` 구문을 사용하여 에러 발생 시 앱이 멈추지 않게 방어합니다.
3. 실제 배포 가능한 수준(Production-Ready)의 안정성을 확보합니다.

</aside>

# 1. 개념 및 이론 (Theory)

### Graceful Degradation (우아한 실패)
인터넷이 끊기거나 LLM 서비스가 점검 중일 때, 사용자가 알 수 없는 영어 에러 코드(`Traceback...`)를 보게 해서는 안 됩니다. 대신 **"잠시 문제가 생겼습니다. 다시 시도해주세요"** 라는 친절한 안내 메시지를 보여주는 것이 좋은 개발자의 자세입니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 아바타 적용

`st.chat_message` 함수에 `avatar` 파라미터를 추가합니다. 이모지(Emoji)나 이미지 파일 경로를 넣을 수 있습니다.

```python
# 사용자와 봇의 아이콘 설정
user_icon = "🧑‍💻"
bot_icon = "🤖"

# 사용자 메시지 표시
with st.chat_message("user", avatar=user_icon):
    st.write(prompt)

# 봇 메시지 표시
with st.chat_message("assistant", avatar=bot_icon):
    st.write(response)
```

### Step 2: 에러 핸들링 (Try-Except)

핵심 로직인 LLM 호출 부분을 보호막(`try`)으로 감쌉니다.

```python
try:
    # 1. 시도할 코드
    response = call_cortex_llm(full_prompt)
    st.write(response)
    
except Exception as e:
    # 2. 에러 발생 시 실행될 코드
    st.error(f"오류가 발생했습니다! 🚨\n\nError details: {e}")
    st.info("잠시 후 다시 시도하거나, 질문 내용을 바꿔보세요.")
```

### Step 3: 디버그 모드 (선택 사항)

개발 중에 일부러 에러를 내보고 싶다면 사이드바에 체크박스를 만들어봅니다.

```python
with st.sidebar:
    debug_mode = st.checkbox("Debug Mode (Simulate Error)")

if debug_mode:
    st.error("This is a simulated error for testing.")
```

# 3. 핵심 포인트 (Key Takeaways)

- **사용자 경험(UX)**: 앱이 예쁘게 보이는 것(Avatar)만큼이나, 문제가 생겼을 때 당황시키지 않는 것(Error Handling)도 중요합니다.
- **방어적 프로그래밍**: "설마 에러가 나겠어?"라고 생각하지 말고, 항상 "에러가 날 수 있다"고 가정하고 코딩해야 합니다. 특히 외부 API를 사용할 때는 필수입니다.

---

# 👏 축하합니다! Part 1 (Basic App Building) 완료

여기까지 Day 14를 완료하셨습니다. 이제 여러분은 Streamlit으로 **기본적인 UI**를 만들고, **Snowflake Cortex LLM**을 연동하여, **대화형 챗봇**을 구축할 수 있는 능력을 갖추었습니다.

---

# 💡 실습 과제 (Hands-on Practice)

아바타 설정과 안정적인 에러 처리를 통해 앱의 완성도를 높여 봅니다.

1. `st.chat_message` 호출 시 `avatar` 파라미터에 원하는 이모지(예: 🤖, 🧑‍💻)를 넣어보세요.
2. LLM 호출 부분을 `try-except` 블록으로 감싸서 에러 발생 시 `st.error`로 안내 메시지를 출력하세요.

# ✅ 정답 코드 (Solution)

```python
# 아바타 및 에러 처리 실습
try:
    # 1. 아바타가 있는 사용자 메시지
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(prompt)
    
    # 2. 아바타가 있는 어시스턴트 메시지 + 에러 방어
    with st.chat_message("assistant", avatar="🤖"):
        response = call_llm(context)
        st.write(response)
        
except Exception as e:
    st.error(f"죄송합니다. 응답을 생성하는 중 오류가 발생했습니다: {e}")
```
