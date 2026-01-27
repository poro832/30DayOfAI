Day 12의 스트리밍 챗봇을 기반으로, 오늘은 시스템 프롬프트를 사용하여 **맞춤형 개성**을 추가합니다. 사용자는 봇에게 해적부터 교사, 코미디언까지 다양한 페르소나를 부여하고, 동일한 AI가 "캐릭터"에 따라 완전히 다르게 응답하는 것을 볼 수 있습니다.

---

### :material/settings: 작동 방식: 단계별 설명

Day 13은 Day 12의 모든 기능(커스텀 제너레이터를 사용한 스트리밍)을 유지하면서 **시스템 프롬프트 커스터마이제이션**을 추가합니다.

#### Day 12에서 유지된 기능:
- :material/check_circle: `st.write_stream()`을 사용한 스트리밍 응답 (Day 12)
- :material/check_circle: 안정적인 스트리밍을 위한 커스텀 제너레이터 (Day 12)
- :material/check_circle: "Processing" 상태를 표시하는 스피너 (Day 12)
- :material/check_circle: LLM에 전달되는 전체 대화 히스토리 (Day 11)
- :material/check_circle: 대화 통계가 있는 사이드바 (Day 11)
- :material/check_circle: 히스토리 지우기 버튼 (Day 11)
- :material/check_circle: 환영 메시지 (Day 11)

#### 새로운 기능: 시스템 프롬프트 & 개성

#### 1. 시스템 프롬프트와 메시지를 조기에 초기화

```python
# Initialize system prompt if not exists
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful pirate assistant named Captain Starlight. You speak with pirate slang, use nautical metaphors, and end sentences with 'Arrr!' when appropriate. Be helpful but stay in character."

# Initialize messages with a personality-appropriate greeting
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Ahoy! Captain Starlight here, ready to help ye navigate the high seas of knowledge! Arrr!"}
    ]
```

* **조기 초기화**: 사이드바 위젯을 생성하기 전에 시스템 프롬프트와 메시지를 모두 설정합니다.
* **세션 상태**: 프롬프트가 재실행 간에 유지되고 프리셋 버튼으로 업데이트될 수 있도록 보장합니다.
* **개성에 맞는 인사말**: 환영 메시지가 기본 해적 페르소나와 일치합니다.

#### 2. 프리셋 개성 버튼 (상단에 배치)

```python
with st.sidebar:
    st.header(":material/theater_comedy: Bot Personality")
    
    # Preset personalities
    st.subheader("Quick Presets")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(":material/sailing: Pirate"):
            st.session_state.system_prompt = "You are a helpful pirate assistant..."
            st.rerun()
    
    with col2:
        if st.button(":material/library_books: Teacher"):
            st.session_state.system_prompt = "You are Professor Ada, a patient and encouraging teacher..."
            st.rerun()
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button(":material/mood: Comedian"):
            st.session_state.system_prompt = "You are Chuckles McGee, a witty comedian assistant..."
            st.rerun()
    
    with col4:
        if st.button(":material/smart_toy: Robot"):
            st.session_state.system_prompt = "You are UNIT-7, a helpful robot assistant..."
            st.rerun()
```

* **프리셋 버튼 우선 배치**: 더 나은 UX를 위해 상단에 배치 - 사용자가 텍스트 영역보다 프리셋을 먼저 봅니다.
* **빠른 전환**: 각 버튼은 사전 정의된 개성으로 `st.session_state.system_prompt`를 업데이트합니다.
* **`st.rerun()`**: 아래의 텍스트 영역에 새 값이 표시되도록 앱을 새로고침합니다.
* **네 가지 페르소나**: 해적(Captain Starlight), 교사(Professor Ada), 코미디언(Chuckles McGee), 로봇(UNIT-7).

#### 3. 시스템 프롬프트 텍스트 영역 (프리셋 아래)

```python
st.divider()

st.text_area(
    "System Prompt:",
    height=200,
    key="system_prompt"
)
```

* **`key="system_prompt"`**: `st.session_state.system_prompt`에 자동으로 바인딩됩니다 - `value` 매개변수가 필요 없습니다.
* **충돌 경고 없음**: `key`만 사용(`key`와 `value` 모두 사용하지 않음)하여 Session State API 충돌을 방지합니다.
* **편집 가능**: 사용자가 프리셋 프롬프트를 수정하거나 완전히 커스텀 프롬프트를 작성할 수 있습니다.
* **프리셋 아래 배치**: 더 나은 흐름 - 위에서 프리셋을 클릭하고 아래에서 결과를 보거나 편집합니다.

#### 4. 스트리밍과 함께 시스템 프롬프트 주입

```python
# Custom generator for reliable streaming
def stream_generator():
    # Build the full conversation history for context
    conversation = "\n\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in st.session_state.messages
    ])
    
    # Create prompt with system instruction
    full_prompt = f"""{st.session_state.system_prompt}

Here is the conversation so far:
{conversation}

Respond to the user's latest message while staying in character."""
    
    response_text = call_llm(full_prompt)
    for word in response_text.split(" "):
        yield word + " "
        time.sleep(0.02)

with st.spinner("Processing"):
    response = st.write_stream(stream_generator)
```

* **시스템 프롬프트 우선**: 개성 지시사항이 프롬프트 상단에 위치하여 이후 모든 내용의 톤을 설정합니다.
* **"캐릭터 유지"**: 이 명시적인 알림은 LLM이 대화 전반에 걸쳐 일관성을 유지하도록 돕습니다.
* **커스텀 제너레이터**: 지연과 함께 단어를 생성하여 스트리밍을 시뮬레이션합니다.
* **`call_llm()`**: 범용 호환성을 위해 SQL 기반 `ai_complete()` 함수를 사용합니다.
* **`split(" ")`**: 응답을 공백으로 분할합니다(모든 공백으로 분할하는 `split()`이 아님).
* **스피너 래퍼**: 생성 중 "Processing" 표시기를 표시하여 스트리밍이 시작되기 전에 시각적 피드백을 제공합니다.

#### 5. 시스템 프롬프트가 중요한 이유

시스템 프롬프트는 다음과 같은 이유로 강력합니다:
- **동작 정의**: LLM에게 *무엇*에 응답할지가 아니라 *어떻게* 응답할지를 알려줍니다
- **톤과 스타일 설정**: 공식적, 캐주얼, 유머러스 또는 기술적. 모두 제어 가능합니다
- **역할 연기 활성화**: 다양한 사용 사례에 대한 전문 어시스턴트를 만듭니다
- **제약 제공**: 응답을 특정 주제나 형식으로 제한합니다

이 코드를 실행하면 사이드바에 개성 선택기가 있는 챗봇을 갖게 됩니다. 페르소나를 전환해보고 시스템 프롬프트에 따라 동일한 질문이 어떻게 다르게 답변되는지 확인해보세요!

---

### :material/library_books: 리소스
- [Prompt Engineering Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#best-practices)
- [st.text_area Documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.text_area)
- [System Prompts Best Practices](https://docs.anthropic.com/claude/docs/system-prompts)

