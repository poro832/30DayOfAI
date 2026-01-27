오늘의 챌린지 목표는 Streamlit 앱에서 건망증 문제를 해결하는 것입니다. 표준 변수가 모든 상호 작용에서 재설정되는 이유와 데이터를 보존하기 위해 세션 상태를 사용하는 방법을 이해해야 합니다. 완료되면 버튼을 클릭할 때 실제로 값을 기억하는 카운터를 갖게 됩니다.

---

### :material/settings: 작동 방식: 단계별 설명

Streamlit은 위젯(버튼 클릭 등)과 상호 작용할 때마다 전체 Python 스크립트를 위에서 아래로 실행합니다. 주의하지 않으면 논리적 함정이 생깁니다.



#### 1. 함정: 표준 변수

```python
with col1:
    st.header(":material/cancel: Standard Variable")
    
    # This line runs every time you click ANY button.
    count_wrong = 0 
    
    if st.button(":material/add:", key="std_plus"):
        count_wrong += 1  # Becomes 0 + 1 = 1

    st.metric("Standard Count", count_wrong)
```

* `count_wrong = 0`: 범인입니다. 앱이 다시 실행될 때마다(모든 클릭마다 발생) 이 줄이 다시 실행되어 점수가 즉시 0으로 재설정됩니다.
* `key="std_plus"`: 버튼에 고유 ID를 할당합니다. 그렇지 않으면 Streamlit이 열 1과 열 2의 버튼을 혼동할 수 있습니다.

#### 2. 해결책: 초기화 패턴

```python
with col2:
    st.header(":material/check_circle: Session State")

    # 1. Initialization: Create the key only if it doesn't exist yet
    if "counter" not in st.session_state:
        st.session_state.counter = 0
```

* `st.session_state`: 앱 재실행에서 살아남는 지속적인 딕셔너리라고 생각하세요.
* `if "counter" not in...`: 표준 세션 상태 패턴입니다. 시작 값을 0으로 한 번만 설정합니다. 두 번째 실행에서 Streamlit은 "counter"가 이미 존재하는 것을 보고 이 블록을 건너뛰어 현재 카운트를 보존합니다.

#### 3. 상태 수정 및 읽기

```python
    # 2. Modification: Update the dictionary value
    if st.button(":material/add:", key="state_plus"):
        st.session_state.counter += 1

    # 3. Read: Display the value
    st.metric("State Count", st.session_state.counter)
```

* `st.session_state.counter += 1`: 임시 변수를 수정하는 대신 세션 상태 딕셔너리에 저장된 값을 수정합니다.
* `st.metric(...)`: 상태에서 직접 값을 읽습니다. 초기화 블록(2단계)이 이 재실행에서 건너뛰어졌기 때문에 값이 재설정되지 않고 계속 증가합니다.

이것은 대화 기록을 기억할 수 있도록 챗봇에 이 메모리 개념을 적용하는 다음 단계를 준비합니다.

---

### :material/library_books: 리소스
- [세션 상태 문서](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [세션 상태 가이드](https://docs.streamlit.io/develop/concepts/architecture/session-state)
