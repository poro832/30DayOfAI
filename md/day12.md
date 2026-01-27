Day 11의 기반(대화 히스토리 및 사이드바 통계) 위에 오늘은 **스트리밍 응답**을 추가하여 더 역동적이고 반응성 있는 채팅 경험을 만듭니다. 완전한 응답을 기다리는 대신, 사용자는 현대적인 채팅 애플리케이션처럼 AI의 답변이 실시간으로 단어별로 나타나는 것을 볼 수 있습니다.

---

### :material/settings: 작동 방식: 단계별 설명

Day 12는 하나의 핵심 개선 사항 추가에 중점을 둡니다: **스트리밍 응답**.

#### 이전 날짜에서 유지된 것:
- :material/check_circle: 초기화 시 환영 메시지 (Day 11)
- :material/check_circle: LLM에 전달되는 전체 대화 히스토리 (Day 11)
- :material/check_circle: 대화 통계가 있는 사이드바 (Day 11)
- :material/check_circle: 히스토리 지우기 버튼 (Day 11)
- :material/check_circle: `st.chat_message()`를 사용한 채팅 인터페이스 (Days 8-11)

#### 새로운 기능: 스트리밍 응답

```python
# Build the full conversation history for context
conversation = "\n\n".join([
    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
    for msg in st.session_state.messages
])
full_prompt = f"{conversation}\n\nAssistant:"

# Generate stream
def stream_generator():
    response_text = call_llm(full_prompt)
    for word in response_text.split(" "):
        yield word + " "
        time.sleep(0.02)

# Display assistant response with streaming
with st.chat_message("assistant"):
    with st.spinner("Processing"):
        response = st.write_stream(stream_generator)

# Add assistant response to state
st.session_state.messages.append({"role": "assistant", "content": response})
st.rerun()  # Force rerun to update sidebar stats
```

**Day 11에서 변경된 사항:**

* **대화 구축 이동**: 이제 제너레이터 외부의 메인 플로우에서 발생합니다
* **사용자 정의 제너레이터 함수**: 응답에서 단어를 생성하여 스트리밍을 시뮬레이션하는 Python 제너레이터를 생성합니다.
* **`call_llm(full_prompt)`**: SQL 기반 `ai_complete()` 함수를 사용하여 LLM에서 전체 응답을 가져옵니다.
* **시뮬레이션된 스트리밍**: `ai_complete()`가 완전한 응답을 반환하므로 `.split(" ")`을 사용하여 공백으로 분할하고 한 번에 하나씩 단어를 생성합니다.
* **`time.sleep(0.02)`**: 단어 사이의 작은 지연(20ms)이 부드럽고 눈에 보이는 스트리밍 효과를 만듭니다.
* **`st.spinner("Processing")`**: 초기 응답을 가져오는 동안 로딩 표시기를 표시하기 위해 스트리밍을 래핑합니다.
* **`st.write_stream(stream_generator)`**: 사용자 정의 제너레이터에 의해 공급되는 Streamlit의 스트리밍 디스플레이 함수입니다.
* **`response = ...`**: 스트리밍이 완료되면 전체 텍스트를 반환하며, 이를 메시지 히스토리에 저장합니다.
* **`st.rerun()`**: 각 응답 후 사이드바 통계를 즉시 업데이트하기 위해 앱 재실행을 강제합니다.

**이 접근 방식을 사용하는 이유:**

- **범용 호환성**: SQL 기반 `ai_complete()`는 모든 배포 환경(SiS, Community Cloud, 로컬)에서 작동합니다
- **더 나은 UX**: 사용자는 완전한 응답을 기다리는 대신 실시간으로 단어가 나타나는 것을 봅니다
- **체감 속도**: 생성 시간은 동일하지만 스트리밍이 훨씬 더 빠르게 *느껴집니다*
- **자연스러운 대화**: 타이핑 효과가 사람 간 채팅을 모방합니다
- **간단한 구현**: 스트리밍 지연을 이해하고 사용자 정의하기 쉽습니다

이 코드를 실행하면 대화 히스토리 **및** 전문적이고 현대적인 채팅 경험을 위한 실시간 스트리밍 응답을 갖춘 챗봇을 갖게 됩니다.

---

### :material/library_books: 리소스
- [Cortex Complete 스트리밍](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#streaming-responses)
- [st.write_stream 문서](https://docs.streamlit.io/develop/api-reference/write-magic/st.write_stream)
- [대화형 앱 구축](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
