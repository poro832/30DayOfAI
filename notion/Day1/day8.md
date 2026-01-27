# Day 8: Meet the Chat Elements

# 0. 목표

<aside>
💡 **Streamlit의 채팅 전용 요소를 활용하여 챗봇 UI 뼈대 만들기**

1. `st.chat_message`: 카카오톡이나 슬랙 같은 말풍선 대화창을 구현합니다.
2. `st.chat_input`: 화면 하단에 고정된 채팅 입력창을 만듭니다.
3. 사라지는 메시지 현상(State 초기화 문제)을 직접 겪어보고 이해합니다.

</aside>

# 1. 개념 및 이론 (Theory)

### Chat Elements
Streamlit 1.24 버전부터 채팅 앱을 위한 전용 함수들이 추가되었습니다. 예전에는 CSS를 해킹해서 말풍선을 만들었지만, 이제는 함수 하나로 역할(User/AI)에 따른 아이콘과 디자인이 적용된 말풍선을 그릴 수 있습니다.

### The "Glitchy" Loop (리런 구조의 이해)
Streamlit은 버튼을 누르거나 입력을 할 때마다 **코드 전체를 맨 위부터 다시 실행(Rerun)** 합니다. 채팅창에 "안녕"이라고 치고 엔터를 누르면 앱이 새로고침되면서 코드가 다시 실행되는데, 이때 이전에 "안녕"이라고 썼던 사실을 기억하는 변수가 없다면 화면은 다시 깨끗하게 비워집니다. 이것이 오늘 실습에서 겪게 될 현상입니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 기본 채팅 UI

`day8.py`를 생성합니다.

```python
import streamlit as st

st.title("Day 8: Basic Chat UI 💬")

# 1. 메시지 출력하기 (하드코딩)
# 'user' 역할의 말풍선
with st.chat_message("user"):
    st.write("Hello! I am a human.")
    
# 'assistant' 역할의 말풍선
with st.chat_message("assistant"):
    st.write("Beep Boop. I am a robot. 🤖")
    st.bar_chart([1, 2, 3]) # 말풍선 안에는 차트도 들어갈 수 있습니다.
```

### Step 2: 채팅 입력창 붙이기

```python
# 화면 하단에 입력창 생성
# 사용자가 입력하고 엔터를 칠 때까지 기다립니다. (:= 연산자 활용)
if user_input := st.chat_input("Say something..."):
    
    # 사용자가 입력한 내용 즉시 표시
    with st.chat_message("user"):
        st.write(user_input)
        
    # 로봇의 응답 표시
    with st.chat_message("assistant"):
        st.write(f"You said: {user_input}")
```

### Step 3: 문제점 확인

앱을 실행하고 대화를 두 번 이상 시도해보세요.
1. "안녕" 입력 -> 화면에 "안녕" 표시됨.
2. "반가워" 입력 -> 화면에 "반가워"만 표시되고, **"안녕"은 사라짐!**

이것이 Streamlit의 동작 방식입니다. 내일(Day 9) 배울 `Session State`가 이 문제를 해결해줍니다.

# 3. 핵심 포인트 (Key Takeaways)

- **`st.chat_input`**: 항상 화면 최하단에 고정되며, 값을 입력받으면 앱을 Rerun 시킵니다.
- **`st.chat_message`**: 단순 텍스트뿐만 아니라 그림, 표, 그래프 등 어떤 Streamlit 요소든 담을 수 있는 만능 컨테이너입니다.
- **휘발성**: 별도의 저장소가 없으면 지난 대화는 Rerun 시 날아갑니다. 그래서 "채팅 히스토리 리스트"가 필요합니다.
