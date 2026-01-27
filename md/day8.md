2주차에 오신 것을 환영합니다! 지금까지 배운 것을 되돌아봅시다.

1주차에서는 선형 앱(입력 → 처리 → 출력)을 구축했습니다. 이제 챗봇을 구축하기 위해 채팅 요소를 사용하는 방법을 배웁니다. 여기서 Streamlit이 정말 빛을 발하지만 앱이 결국 컨텍스트를 "기억"해야 합니다.

오늘의 챌린지 목표는 채팅 사용자 인터페이스(UI)에만 순수하게 집중하는 것입니다. 여기서는 메모리나 API 호출에 대해 걱정하기 전에 채팅 요소를 사용하여 시각적 채팅 대화를 렌더링합니다. 완료되면 챗봇의 시각적 골격을 갖게 됩니다. 완전히 기능하는 챗봇은 아니지만 그 길을 향한 훌륭한 시작입니다.

---

### :material/settings: 작동 방식: 단계별 설명

두 가지 특정 명령을 사용합니다: 말풍선을 위한 `st.chat_message()`와 텍스트 상자를 위한 `st.chat_input()`.

#### 1. 정적 메시지 시각화

```python
import streamlit as st

with st.chat_message("user"):
    st.write("Hello! Can you explain what Streamlit is?")

with st.chat_message("assistant"):
    st.write("Streamlit is an open-source Python framework for building data apps.")
    st.bar_chart([10, 20, 30, 40]) 
```

* **`st.chat_message("role")`**: 메시지 컨테이너를 생성합니다. Streamlit은 역할("user" 대 "assistant")에 따라 아바타와 정렬을 자동으로 할당합니다.
* **`st.bar_chart(...)`**: 채팅 말풍선에 일반 텍스트뿐만 아니라 풍부한 미디어(차트, 이미지, 데이터프레임)가 포함될 수 있음을 보여줍니다.

#### 2. 채팅 입력 위젯

```python
prompt = st.chat_input("Type a message here...")
```

* **`st.chat_input(...)`**: 화면 하단에 고정된 텍스트 입력 상자를 생성합니다. 레이아웃을 자동으로 처리하므로 메시지 기록과 겹치지 않습니다.
* **`prompt`**: 사용자가 입력한 문자열을 저장합니다. 사용자가 "Enter"를 누를 때까지 `None`으로 유지됩니다.

#### 3. 입력에 반응 ("결함 있는" 루프)

```python
if prompt:
    # Display the user's new message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Display a mock assistant response
    with st.chat_message("assistant"):
        st.write(f"You just said:\n\n '{prompt}' \n\n(I don't have memory yet!)")
```

* **`if prompt:`**: 이 코드가 사용자가 텍스트를 제출한 후에만 실행되도록 합니다.
* **`st.write(prompt)`**: 입력을 즉시 사용자 말풍선으로 화면에 에코합니다.

**8일차 관찰 사항:**
메시지를 입력하면 표시되는 것을 볼 수 있습니다. 그러나 두 번째 메시지를 입력하면 첫 번째 메시지가 사라집니다. 이는 Streamlit이 모든 상호 작용에서 화면을 다시 그리는데, 아직 기록을 저장하라고 지시하지 않았기 때문입니다.

이 "사라지는 메시지" 문제를 해결하려면 Streamlit 앱 개발에서 가장 중요한 개념인 **세션 상태**를 마스터해야 하며, 이는 내일 다룰 것입니다.

---

### :material/library_books: 리소스
- [st.chat_message 문서](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message)
- [st.chat_input 문서](https://docs.streamlit.io/develop/api-reference/chat/st.chat_input)
- [기본 LLM 채팅 앱 구축](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
