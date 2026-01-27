오늘의 챌린지 목표는 채팅 요소와 세션 상태에 대해 배운 모든 것을 결합하여 대화를 기억하는 챗봇을 만드는 것입니다. `st.session_state`에 메시지를 저장하고 `st.chat_message`를 사용하여 표시해야 합니다. 완료되면 상호 작용 간에 대화 기록을 유지하는 작동하는 챗봇을 갖게 됩니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 메시지 저장 초기화

```python
st.title(":material/chat: My First Chatbot")

# Initialize the messages list in session state
if "messages" not in st.session_state:
    st.session_state.messages = []
```

* **`st.session_state.messages = []`**: 대화를 저장할 빈 리스트를 생성합니다. 이 리스트는 `"role"`(사용자/비서)과 `"content"`(메시지 텍스트)가 있는 딕셔너리를 보유합니다. 이 형식은 OpenAI, Anthropic 및 대부분의 채팅 API에서 사용하는 **업계 표준**이므로 여기서 배우는 것은 어디서나 적용됩니다!
* **`if "messages" not in ...`**: 이 확인은 앱이 처음 로드될 때 특히 한 번만 초기화하도록 합니다. 이것이 없으면 모든 상호 작용에서 리스트가 비어 대화 기록이 지워집니다.

#### 2. 채팅 기록 표시

```python
# Display all messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
```

* **`for message in st.session_state.messages`**: 세션 상태에 저장된 모든 메시지를 반복합니다.
* **`st.chat_message(message["role"])`**: 메시지 딕셔너리에 저장된 역할에 따라 적절한 채팅 말풍선(사용자 또는 비서)을 생성합니다.

#### 3. 새 메시지 처리

```python
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
```

* **`:=` (Walrus 연산자)**: 입력 값을 `prompt`에 할당하고 비어 있지 않은지 한 줄로 확인합니다.
* **`.append(...)`**: 표시하기 전에 새 사용자 메시지를 지속적인 메시지 리스트에 추가합니다.

#### 4. 응답 생성 및 저장

```python
    with st.chat_message("assistant"):
        response = call_llm(prompt)
        st.write(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
```

* **`call_llm(...)`**: `ai_complete()` 함수를 사용하여 Snowflake Cortex를 호출하여 응답을 생성합니다.
* **두 번째 `.append(...)`**: 동일한 형식으로 비서의 응답을 저장하여 대화 턴을 완료합니다.

> :material/lightbulb: **왜 SQL 기반 `ai_complete()`인가요?** Python `Complete()` API 대신 SQL 기반 `ai_complete()` 함수를 사용하는 이유는 모든 배포 환경(Streamlit in Snowflake, Community Cloud, 로컬)에서 전체적으로 작동하기 때문입니다. Python SDK는 외부 환경에서 SSL 인증서 문제가 있을 수 있지만 SQL 접근 방식은 어디서나 안정적입니다.

이 코드가 실행되면 상호 작용 간에 메시지가 지속되어 표시되는 대화 기록을 구축하는 챗봇을 갖게 됩니다.

---

### :material/search: 무엇이 누락되었나요? 개선 여지

이 챗봇은 작동하지만 몇 가지 주목할 만한 제한 사항이 있습니다:

**현재 제한 사항:**
- :material/cancel: **시각적 피드백 없음**: 응답을 기다리는 동안 사용자에게 아무것도 표시되지 않음(앱이 정지된 것처럼 느껴질 수 있음)
- :material/cancel: **응답이 한 번에 나타남**: 전체 응답이 갑자기 표시되며 현대 채팅 앱처럼 점진적으로 표시되지 않음
- :material/cancel: **대화 인사이트 없음**: 교환된 메시지 수를 볼 수 없음
- :material/cancel: **새로 시작하는 방법 없음**: 명확한 버튼 없이 대화 기록이 축적됨
- :material/cancel: **일반적인 모양**: 모든 메시지가 동일하게 보임(개성이나 사용자 지정 없음)
- :material/cancel: **오류 처리 없음**: API가 실패하면 앱이 충돌함

걱정하지 마세요! 앞으로의 레슨에서 이러한 모든 문제를 해결하여 이 기본 챗봇을 프로덕션 준비가 된 애플리케이션으로 변환할 것입니다! :material/rocket_launch:

---

### :material/library_books: 리소스
- [대화형 앱 구축](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
- [Cortex Complete 함수](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
