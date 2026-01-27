# Day 10: Your First Chatbot (with State)

# 0. 목표

<aside>
💡 **대화 내용을 기억하는 기본 챗봇 만들기**

1. `messages` 리스트를 만들어 AI와 주고받은 대화 내역을 저장합니다.
2. `for` 반복문을 사용해 저장된 대화 내용을 화면에 다시 그려줍니다.
3. 사용자가 엔터를 치면 즉시 화면에 내 말을 띄우고 AI 응답을 요청합니다.

</aside>

# 1. 개념 및 이론 (Theory)

### 대화의 구조 (Message Schema)
OpenAI, Snowflake Cortex 등 대부분의 LLM API는 대화 내용을 다음과 같은 리스트 형태로 관리합니다.
- `{"role": "user", "content": "안녕"}`
- `{"role": "assistant", "content": "반갑습니다!"}`

### Rerun Loop와 Chat History
Day 9에서 배웠듯이, 새로운 질문을 입력하면 화면이 새로고침됩니다. 이때 빈 화면에 **이전 대화들이 순서대로 다시 그려져야(Re-render)** 사용자는 대화가 이어지고 있다고 느낍니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 저장소 초기화

`day10.py`를 생성합니다.

```python
import streamlit as st
from snowflake.snowpark.functions import ai_complete # 또는 Day 1,2의 연결 코드

st.title("Day 10: My Memory Bot 🧠")

# 대화 기록을 담을 빈 리스트 생성
if "messages" not in st.session_state:
    st.session_state.messages = []
```

### Step 2: 과거 대화 출력

앱이 실행될 때마다(Rerun), 저장된 모든 메시지를 화면에 뿌려줍니다.

```python
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
```

### Step 3: 새로운 대화 처리

입력창(`chat_input`)에 값이 들어오면 로직이 실행됩니다.

```python
# := 연산자는 값을 할당함과 동시에 True인지 검사합니다.
if prompt := st.chat_input("Say something..."):
    
    # 1. 사용자 메시지를 '기록'에 추가하고 '화면'에 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
        
    # 2. AI 응답 생성 (아직은 문맥 없이 단순 응답)
    # 실제로는 여기서 Cortex를 호출합니다.
    response = "I heard you! You said: " + prompt 
    
    # 3. AI 응답을 '기록'에 추가하고 '화면'에 표시
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
```

# 3. 핵심 포인트 (Key Takeaways)

- **History Management**: 챗봇 개발의 핵심은 "LLM 호출"보다 "대화 기록 관리(Append & Display)"에 있습니다.
- **Append -> Display**: 메시지 리스트에 `append` 하는 것과, 그것을 화면에 `write` 하는 것은 별개입니다. 보통은 즉시 피드백을 위해 **동시에** 수행합니다.
