오늘의 과제는 더 나은 히스토리 관리 기능으로 챗봇을 개선하는 것입니다. 환영 메시지를 추가하고, 사이드바에 대화 통계를 표시하며, 채팅 기록을 지울 수 있는 방법을 제공해야 합니다. 이 작업이 완료되면 대화 추적이 가능한 더 세련된 챗봇 경험을 제공할 수 있습니다.

**참고:** 사이드바 통계가 즉시 업데이트되도록 어시스턴트의 응답 후 `st.rerun()`을 추가합니다.

---

### :material/bug_report: Day 10의 문제점

Day 10에서는 메시지를 세션 상태에 저장하여 UI에 표시했습니다. 하지만 LLM은 실제로 그 히스토리를 보지 못했습니다:

**예시 대화 (Day 10 동작):**
```
User: "What's the capital of France?"
AI: "Paris"

User: "What's the population?"
AI: "What location are you asking about?" ❌
```

화면에서 이전 질문을 **볼 수** 있지만, AI는 볼 수 없습니다! 이는 채팅 인터페이스가 기억하는 것처럼 보이지만 AI에게는 기억이 없는 혼란스러운 경험을 만듭니다.

**이유는?** 현재 프롬프트만 LLM에 전송했기 때문입니다:
```python
response = call_llm(prompt)  # Only sends current message!
```

### :material/check_circle: 해결책 (Day 11)

오늘은 **전체 대화 히스토리**를 LLM에 전달하여 이 문제를 해결합니다:

**동일한 대화 (Day 11 동작):**
```
User: "What's the capital of France?"
AI: "Paris"

User: "What's the population?"
AI: "Paris has approximately 2.1 million people in the city proper..." ✅
```

이제 AI는 후속 질문에 답하고, 이전 주제를 참조하며, 대화 전반에 걸쳐 맥락을 유지할 수 있습니다!

**어떻게?** 전체 대화를 구성하고 전송함으로써:
```python
# Build the full conversation history for context
conversation = "\n\n".join([
    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
    for msg in st.session_state.messages
])
full_prompt = f"{conversation}\n\nAssistant:"

response = call_llm(full_prompt)  # Sends entire conversation!
```

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 환영 메시지로 초기화

```python
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
    ]
```

* **미리 채워진 리스트**: 빈 리스트 대신 어시스턴트의 환영 메시지로 시작합니다. 이렇게 하면 사용자가 앱을 처음 로드할 때 챗봇이 더 친근하게 느껴집니다.

#### 2. 사이드바 통계 및 컨트롤

```python
with st.sidebar:
    st.header("Conversation Stats")
    user_msgs = len([m for m in st.session_state.messages if m["role"] == "user"])
    assistant_msgs = len([m for m in st.session_state.messages if m["role"] == "assistant"])
    st.metric("Your Messages", user_msgs)
    st.metric("AI Responses", assistant_msgs)
```

* **리스트 컴프리헨션**: `[m for m in messages if m["role"] == "user"]` 구문은 역할이 "user"인 메시지만 포함하는 새 리스트를 생성합니다. 리스트를 필터링하는 간결한 방법입니다. 처음 접하는 경우, 이는 내부에 if문이 있는 for 루프와 동일합니다.
* **`st.metric(...)`**: 시각적으로 매력적인 메트릭 카드 형식으로 개수를 표시합니다.

#### 3. 히스토리 지우기 버튼

```python
    if st.button("Clear History"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
        ]
        st.rerun()
```

* **초기 상태로 재설정**: 클릭하면 메시지 리스트를 환영 메시지만으로 교체합니다.
* **`st.rerun()`**: 앱을 즉시 재실행하여 지워진 상태를 표시하도록 디스플레이를 새로 고칩니다.

#### 4. 향상된 메시지 표시

```python
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
```

* **`st.markdown(...)`**: 응답에서 **굵게**, *기울임꼴*, 글머리 기호와 같은 풍부한 서식을 지원하기 위해 `st.write()` 대신 마크다운을 사용합니다.

#### 5. `st.spinner`로 로딩 표시기 추가

AI가 요청을 처리 중임을 사용자에게 표시하기 위해 `st.spinner`를 도입합니다:

```python
with st.spinner("Thinking..."):
    # Build conversation history and get response
    response = Complete(...)
```

* **`st.spinner(...)`**: 컨텍스트 내부의 코드가 실행되는 동안 사용자 지정 텍스트와 함께 애니메이션 스피너를 표시합니다. 이는 몇 초가 걸릴 수 있는 LLM 처리 중에 시각적 피드백을 제공합니다.
* **더 나은 UX**: 이것이 없으면 사용자는 응답을 기다리는 동안 앱이 멈춘 것으로 생각할 수 있습니다. 스피너는 AI가 "생각 중"임을 명확하게 나타냅니다.
* **참고**: Day 12에서 스트리밍을 추가할 때 스트리밍이 자체 시각적 피드백을 제공하므로 스피너를 제거할 것입니다!

#### 6. LLM에 대화 히스토리 전달

이것은 챗봇에 실제 메모리를 제공하는 **중요한 단계**입니다:

```python
# Build the full conversation history for context
conversation = "\n\n".join([
    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
    for msg in st.session_state.messages
])
full_prompt = f"{conversation}\n\nAssistant:"

response = call_llm(full_prompt)
```

* **왜 중요한가**: 이것이 없으면 LLM은 현재 메시지만 보고 이전에 무엇이 말해졌는지 기억할 수 없습니다. UI에 히스토리를 저장하고 있더라도 챗봇은 메모리가 없는 것처럼 보일 것입니다.
* **컨텍스트 구축**: 명확한 "User:" 및 "Assistant:" 레이블이 있는 형식화된 문자열로 전체 대화를 재구성합니다.
* **전체 프롬프트**: 전체 대화 히스토리와 새 사용자 메시지가 LLM에 전송되어 맥락을 유지하고 후속 질문에 답할 수 있습니다.
* **`call_llm()`**: 모든 배포 환경에서 작동하는 SQL 기반 `ai_complete()` 함수를 사용합니다.

#### 7. st.rerun()으로 사이드바 통계 업데이트

어시스턴트의 응답을 세션 상태에 추가한 후 즉시 재실행을 강제합니다:

```python
# Add assistant response to state
st.session_state.messages.append({"role": "assistant", "content": response})
st.rerun()  # Force rerun to update sidebar stats
```

* **`st.rerun()`**: 앱을 즉시 재실행하여 사이드바 통계가 바로 업데이트되도록 합니다
* **이것이 없으면**: 사이드바 메트릭이 한 메시지 뒤처져서 다음 사용자 상호작용 시에만 업데이트됩니다
* **더 나은 UX**: 사용자는 각 AI 응답 후 대화 개수가 즉시 업데이트되는 것을 볼 수 있습니다

이 코드를 실행하면 환영 초기 메시지, 대화 통계를 표시하는 사이드바(즉시 업데이트됨), 대화를 재설정하는 버튼, 그리고 후속 질문을 허용하는 **진정한 대화 메모리**를 갖춘 챗봇을 볼 수 있습니다.

---

### :material/library_books: 리소스
- [st.metric 문서](https://docs.streamlit.io/develop/api-reference/data/st.metric)
- [st.rerun 문서](https://docs.streamlit.io/develop/api-reference/execution-flow/st.rerun)
- [세션 상태 관리](https://docs.streamlit.io/develop/concepts/architecture/session-state)

