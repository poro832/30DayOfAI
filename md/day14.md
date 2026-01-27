이전 챗봇을 기반으로 오늘은 **아바타를 사용한 시각적 완성도**와 **강력한 오류 처리**를 추가하여 프로덕션 준비가 완료된 챗봇을 만듭니다. 사용자는 이제 채팅의 외관을 개인화할 수 있으며, 앱은 충돌 없이 API 실패를 우아하게 처리합니다.

---

### :material/settings: 작동 방식: 단계별 설명

Day 14는 이전 날짜의 모든 것을 유지하고 **사용자 정의 아바타**와 **오류 처리**를 추가합니다.

#### 이전 날짜에서 유지된 것:
- :material/check_circle: 사용자 정의 제너레이터를 사용한 스트리밍 응답 (Day 12)
- :material/check_circle: "Processing" 상태를 표시하는 스피너 (Day 12)
- :material/check_circle: 시스템 프롬프트 사용자 정의 (Day 13)
- :material/check_circle: 전체 대화 히스토리 (Day 11)
- :material/check_circle: 대화 통계가 있는 사이드바 (Day 11)
- :material/check_circle: 히스토리 지우기 버튼 (Day 11)
- :material/check_circle: 환영 메시지 (Day 11)
- :material/check_circle: `st.chat_message()`를 사용한 채팅 인터페이스 (Days 8-11)

#### 새로운 기능: 아바타 & 오류 처리

#### 1. 아바타 구성

```python
USER_AVATAR = ":material/account_circle:"
ASSISTANT_AVATAR = ":material/smart_toy:"

user_avatar = st.selectbox(
    "Your Avatar:",
    [":material/account_circle:", "🧑‍💻", "👨‍🎓", "👩‍🔬", "🦸", "🧙"],
    index=0
)
```

* **기본 아바타**: 일관된 스타일링을 위해 이모지 상수를 정의합니다.
* **사용자 선택**: 선택 상자를 통해 사용자가 선호하는 이모지를 선택하여 채팅 경험을 개인화할 수 있습니다.
* **두 아바타**: 사용자 및 어시스턴트 아바타는 독립적으로 사용자 정의할 수 있습니다.

#### 2. 디버그 모드 토글

```python
st.subheader(":material/bug_report: Debug Mode")
simulate_error = st.checkbox(
    "Simulate API Error",
    value=False,
    help="Enable this to test the error handling mechanism"
)
```

* **테스트 도구**: 요청 시 오류를 트리거할 수 있는 체크박스입니다.
* **교육적 가치**: 실제 실패를 기다리지 않고 오류 처리가 어떻게 작동하는지 보여줍니다.
* **기본적으로 꺼짐**: 기본적으로 정상 작동 (`value=False`).
* **도움말 텍스트**: 토글이 무엇을 하는지에 대한 컨텍스트를 제공합니다.

#### 3. 채팅 메시지에서 아바타 사용

```python
for message in st.session_state.messages:
    avatar = user_avatar if message["role"] == "user" else assistant_avatar
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
```

* **동적 아바타 선택**: 메시지 역할에 따라 적절한 아바타를 선택합니다.
* **`avatar=` 매개변수**: Streamlit의 `st.chat_message`는 사용자 정의 아바타를 위해 이모지, 이미지 URL 또는 이미지 파일 경로를 허용합니다.

#### 4. Try/Except 및 스트리밍을 사용한 오류 처리

```python
try:
    # Simulate error if debug mode is enabled
    if simulate_error:
        raise Exception("Simulated API error: Service temporarily unavailable (429)")
    
    # Custom generator for reliable streaming
    def stream_generator():
        # Build the full conversation history for context
        conversation = "\n\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in st.session_state.messages
        ])
        full_prompt = f"{conversation}\n\nAssistant:"
        
        response_text = call_llm(full_prompt)
        for word in response_text.split():
            yield word + " "
            time.sleep(0.02)
    
    with st.spinner("Processing"):
        response = st.write_stream(stream_generator)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    
except Exception as e:
    error_message = f"I encountered an error: {str(e)}"
    st.error(error_message)
    st.info(":material/lightbulb: **Tip:** This might be a temporary issue. Try again in a moment, or rephrase your question.")
```

* **`try/except` 블록**: 모든 오류(네트워크 문제, 속도 제한, 잘못된 응답)를 포착하기 위해 전체 스트리밍 프로세스를 래핑합니다.
* **시뮬레이션된 오류**: 디버그 모드가 활성화되면 오류 처리를 시연하기 위해 테스트 예외를 발생시킵니다.
* **`st.error(...)`**: 예외 메시지가 있는 빨간색 오류 상자를 표시합니다.
* **`st.info(...)`**: 실패 중에도 좋은 경험을 유지하면서 사용자에게 유용한 안내를 제공합니다.
* **사용자 정의 제너레이터**: 지연과 함께 단어를 생성하여 스트리밍을 시뮬레이션합니다.
* **`call_llm()`**: 범용 호환성을 위해 SQL 기반 `ai_complete()` 함수를 사용합니다.
* **스피너 래퍼**: 생성하는 동안 "Processing" 표시기를 표시합니다.

#### 5. 오류 처리가 중요한 이유

> :material/warning: **이것은 매우 중요합니다!** 프로덕션에서 LLM API는 결국 실패할 것입니다. 오류 처리가 없는 앱은 충돌하고 사용자를 좌절시킬 것입니다. 이 패턴은 실제 배포에 필수적입니다.

LLM API는 여러 가지 이유로 실패할 수 있습니다:
- **속도 제한**: 짧은 시간에 너무 많은 요청
- **네트워크 문제**: 일시적인 연결 문제
- **모델 과부하**: 높은 수요로 인한 시간 초과
- **잘못된 입력**: 안전 필터를 트리거하는 프롬프트

오류를 우아하게 처리함으로써 우리는:
- 앱이 충돌하는 것을 방지합니다
- 무슨 일이 일어났는지 사용자에게 알립니다
- 실행 가능한 제안을 제공합니다
- 실패한 응답을 채팅 히스토리에 저장하지 않습니다

이 코드를 실행하면 사용자 정의 가능한 아바타와 전문적인 사용자 경험을 유지하는 강력한 오류 처리를 갖춘 시각적으로 세련된 챗봇을 갖게 됩니다. 디버그 토글을 사용하여 오류 처리 메커니즘을 테스트하고 앱이 실패를 우아하게 처리하는 방법을 확인하세요.

---

### :material/lightbulb: 사용해 보기

사이드바에서 "Simulate API Error" 체크박스를 활성화하고 메시지를 보내세요. 다음을 볼 수 있습니다:
1. :material/cancel: 시뮬레이션된 오류를 표시하는 빨간색 오류 메시지
2. :material/lightbulb: 무엇을 해야 하는지 제안하는 유용한 팁
3. :material/check_circle: 앱이 계속 작동합니다 - 충돌하지 않았습니다!

그런 다음 체크박스를 비활성화하고 다시 시도하여 정상 작동을 확인하세요.

---

### :material/library_books: 리소스
- [st.chat_message 아바타 매개변수](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message)
- [st.error 문서](https://docs.streamlit.io/develop/api-reference/status/st.error)
- [Python 예외 처리](https://docs.python.org/3/tutorial/errors.html)
