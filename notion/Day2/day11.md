# Day 11: Displaying Chat History & Context

# 0. 목표

<aside>
💡 **"문맥(Context)"을 이해하는 똑똑한 챗봇 만들기**

1. 초기 환영 메시지(Welcome Message)를 설정합니다.
2. 이전 대화 내용을 모두 합쳐서 LLM에게 보냄으로써 대화의 맥락을 유지합니다.
3. 사이드바에 대화 초기화 버튼을 만듭니다.

</aside>

# 1. 개념 및 이론 (Theory)

### Stateless LLM
LLM(모델) 자체는 기억력이 없습니다. 우리가 "내 이름은 철수야"라고 말하고, 다음 턴에 "내 이름이 뭐지?"라고 물으면 LLM은 모른다고 대답합니다.
그래서 개발자가 **"아까는 철수라고 했고, 지금 내 이름은 뭐냐고 물어봤어"** 라고 전체 대본을 매번 다시 줘야 합니다. 이것이 **Context Injection**입니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 환영 메시지 추가

`day11.py`에서 초기화 로직을 조금 수정합니다.

```python
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 AI 비서입니다. 무엇을 도와드릴까요?"}
    ]
```

### Step 2: 문맥 구성 (Prompt Engineering)

이전 대화를 무시하고 현재 질문만 보내는 것이 아니라, 대화 내역 포맷팅을 수행합니다.

```python
def create_prompt(messages):
    prompt = ""
    for msg in messages:
        # User: 안녕 \n Assistant: 반가워요 \n 형식을 만듭니다.
        role = "User" if msg["role"] == "user" else "Assistant"
        prompt += f"{role}: {msg['content']}\n"
    return prompt

# 실제 호출 부분
if prompt := st.chat_input():
    # ... (메시지 표시 로직은 동일) ...
    
    # 전체 대화 기록을 넘겨줍니다.
    # LLM 입장에서는 마치 소설 대본을 읽고 다음 대사를 채우는 것과 같습니다.
    full_conversation = create_prompt(st.session_state.messages)
    
    response = call_cortex_llm(full_conversation) 
```

### Step 3: 초기화 버튼 (Reset)

대화가 너무 길어지거나 주제를 바꾸고 싶을 때를 위해 초기화 기능을 사이드바에 넣습니다.

```python
with st.sidebar:
    if st.button("Clear Conversation"):
        st.session_state.messages = [] # 또는 환영 메시지로 초기화
        st.rerun() # 화면 즉시 새로고침
```

# 3. 핵심 포인트 (Key Takeaways)

- **Context Window**: LLM이 한 번에 읽을 수 있는 글자 수에는 한계가 있습니다. 대화가 정말 길어지면 오래된 대화부터 삭제하거나 요약하는 기술(Sliding Window)이 필요합니다.
- **`st.rerun()`**: 초기화 버튼을 눌러서 데이터를 지웠는데 화면에는 여전히 글자가 남아있으면 곤란하겠죠? 이럴 때 `rerun`을 호출하여 화면을 강제로 갱신합니다.
