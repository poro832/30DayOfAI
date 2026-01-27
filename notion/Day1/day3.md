# Day 3: Write Streams

# 0. 목표

<aside>
💡 **Snowflake Cortex LLM의 응답을 실시간으로 스트리밍하기**

1. 챗지피티(ChatGPT)처럼 글자가 한 자씩 나오는 효과(Typewriter effect)를 구현합니다.
2. `snowflake.cortex.Complete` API와 Python의 `yield` (제너레이터) 개념을 이해합니다.
3. `st.write_stream`을 사용하여 사용자 경험(UX)을 향상시킵니다.

</aside>

# 1. 개념 및 이론 (Theory)

### 왜 스트리밍이 필요한가요?
LLM이 긴 답변을 생성할 때, 전체 답변이 완성될 때까지 기다리면 사용자는 수 초 이상 멈춘 화면을 보게 됩니다. **스트리밍(Streaming)** 기술을 사용하면 모델이 토큰(Token)을 생성하는 즉시 화면에 보여주어, 사용자가 "AI가 생각하고 쓰고 있구나"라고 느끼게 하여 지루함을 덜어줍니다.

### Generator와 Yield
Python의 `yield` 키워드는 함수가 값을 한 번에 반환(return)하고 끝나는 것이 아니라, 필요할 때마다 값을 하나씩 꺼내주는 **제너레이터(Generator)** 를 만듭니다. 스트리밍 구현의 핵심이 바로 이 제너레이터 패턴입니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 파일 생성 및 라이브러리 준비

`day3.py` 파일을 생성합니다. 이번에는 SQL 함수가 아닌 Python Native API인 `snowflake.cortex`를 사용합니다.

```python
import streamlit as st
from snowflake.cortex import Complete # Python Native API
import time

st.title("Day 3: Streaming Responses 🌊")
```

### Step 2: Snowflake 연결

(Day 1, 2와 동일한 코드입니다. 복사해서 사용하세요.)

```python
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except ImportError:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
```

### Step 3: UI 구성

모델 선택과 스트리밍 방식을 선택하는 옵션을 추가합니다.

```python
# 모델 선택
model = st.selectbox(
    "Select a model", 
    ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"]
)

# 프롬프트 입력
prompt = st.text_input("Enter your prompt:", "Explain quantum computing in simple terms.")

# 스트리밍 방식 선택 (교육용 비교를 위해)
streaming_method = st.radio(
    "Streaming Method:",
    ["Method 1: Direct (stream=True)", "Method 2: Custom Generator"]
)
```

### Step 4: 스트리밍 로직 구현

버튼을 클릭하면 선택한 방식에 따라 스트리밍이 동작하도록 합니다.

```python
if st.button("Generate"):
    if prompt:
        st.markdown("### Response:")
        
        # 방식 1: 가장 간편한 방법 (권장)
        if streaming_method == "Method 1: Direct (stream=True)":
            # Complete 함수 리턴값 자체가 반복 가능한 객체(Iterator)가 됩니다.
            stream = Complete(model, prompt, session=session, stream=True)
            
            # st.write_stream이 알아서 이터레이터를 받아 타자기 효과를 냅니다.
            st.write_stream(stream)
            
        # 방식 2: 커스텀 제너레이터 (원리 이해용)
        else:
            def custom_generator():
                # 실제로는 스트리밍이 아닌 전체 응답을 받아옵니다 (예시용)
                # 실제 스트리밍 API를 래핑할 때도 유사한 패턴을 씁니다.
                full_response = Complete(model, prompt, session=session)
                
                # 글자를 5개씩 끊어서 조금씩 내보내는 척(Simulate) 합니다.
                for i in range(0, len(full_response), 5):
                    yield full_response[i:i+5]
                    time.sleep(0.05) # 타이핑 효과를 위한 지연
            
            st.write_stream(custom_generator())
```

# 3. 핵심 포인트 (Key Takeaways)

- **`st.write_stream`**: Streamlit 1.31+ 버전부터 도입된 강력한 함수로, 제너레이터 객체만 넘겨주면 복잡한 UI 코드 없이도 채팅 같은 스트리밍 효과를 냅니다.
- **`snowflake.cortex.Complete(..., stream=True)`**: `session.sql`을 쓰는 것보다 훨씬 파이썬 친화적이며, `stream=True` 옵션 하나로 스트리밍 객체를 받을 수 있습니다.

---

# 💡 실습 과제 (Hands-on Practice)

이번 실습에서는 `Complete` 함수의 `stream=True` 옵션을 직접 구현해 봅니다.

1. `Complete` 함수의 인자로 `stream=True`를 전달하여 스트리밍 객체를 생성하세요.
2. `st.write_stream()` 함수를 사용하여 해당 객체를 화면에 출력하세요.

# ✅ 정답 코드 (Solution)

```python
# Direct (stream=True) 방식 구현
with st.spinner(f"`{model}` 모델로 응답 생성 중..."):
    # 1. 스트림 제너레이터 생성
    stream_generator = Complete(model=model, prompt=prompt, session=session, stream=True)
    
    # 2. write_stream으로 출력
    st.write_stream(stream_generator)
```
