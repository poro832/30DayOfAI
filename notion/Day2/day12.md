# Day 12: Streaming Responses

# 0. 목표

<aside>
💡 **ChatGPT처럼 글자가 타자 치듯 나오는 스트리밍(Streaming) 구현하기**

1. LLM 응답을 기다리는 지루한 시간을 없앱니다.
2. `st.write_stream` 함수를 실전 챗봇에 적용합니다.
3. Python 제너레이터를 이용해 데이터 흐름을 제어합니다.

</aside>

# 1. 개념 및 이론 (Theory)

### Latency vs UX
LLM이 긴 답변을 생성하는 데는 5초~10초가 걸릴 수 있습니다. 사용자는 10초 동안 멈춘 화면을 보면 앱이 죽었다고 생각합니다. 첫 글자가 0.5초 만에 나오기 시작하면, 전체 완료 시간이 똑같이 10초라도 사용자는 훨씬 빠르다고 느낍니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 스트리밍 제너레이터

만약 사용하는 LLM API가 스트리밍을 지원하지 않는다면(예: SQL Function인 `ai_complete` 사용 시), 마치 스트리밍인 것처럼 흉내(Simulation)낼 수 있습니다.

```python
import time

def simulate_stream(text):
    """이미 완성된 텍스트를 단어 단위로 쪼개 천천히 내보냅니다."""
    for word in text.split():
        yield word + " "
        time.sleep(0.05) # 타자 속도 조절
```

### Step 2: 챗봇에 적용

`day12.py`의 AI 응답 부분을 수정합니다.

```python
if prompt := st.chat_input():
    # ... (사용자 메시지 처리) ...
    
    with st.chat_message("assistant"):
        # 1. 일단 전체 응답을 받습니다 (여기서 약간 딜레이 발생)
        full_response = call_cortex_llm(context) 
        
        # 2. 받아온 응답을 스트리밍으로 뿌려줍니다.
        # st.write_stream은 제너레이터가 끝날 때, 완성된 전체 문자열을 반환합니다!
        streamed_text = st.write_stream(simulate_stream(full_response))
    
    # 3. 완성된 텍스트를 기록에 저장합니다.
    st.session_state.messages.append({"role": "assistant", "content": streamed_text})
```

**참고**: `snowflake.cortex.Complete(..., stream=True)`를 사용하면(Day 3 참조) 실제로 토큰이 생성되는 즉시 받아올 수 있어 `simulate_stream`보다 더 반응성 좋은 진짜 스트리밍을 구현할 수 있습니다.

# 3. 핵심 포인트 (Key Takeaways)

- **`st.write_stream`의 반환값**: 이 함수는 화면에 글자를 뿌려주는 역할뿐만 아니라, 스트리밍이 끝난 후 **최종 완성된 문자열을 반환**해줍니다. 덕분에 별도로 문자열을 합치는 코드를 짤 필요가 없어 매우 편리합니다.
- **Visual Feedback**: 스트리밍은 단순한 시각 효과가 아니라, 사용자의 인내심을 유지시키는 중요한 UX 장치입니다.
