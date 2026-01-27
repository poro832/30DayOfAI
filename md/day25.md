오늘의 챌린지 목표는 완전한 음성 지원 대화형 AI 비서를 구축하는 것입니다. 사용자는 음성 메시지를 녹음할 수 있고, 이는 Snowflake의 `AI_TRANSCRIBE`를 사용하여 텍스트로 변환되며, 비서는 대화 기록을 사용하여 문맥을 인식한 답변을 제공합니다. 전체 상호 작용은 지속적인 채팅 기록이 있는 깔끔한 인터페이스를 통해 이루어집니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 세션 상태 초기화

```python
# Initialize conversation with welcome message
if "voice_messages" not in st.session_state:
    st.session_state.voice_messages = []

if len(st.session_state.voice_messages) == 0:
    st.session_state.voice_messages = [
        {
            "role": "assistant",
            "content": "Hello! :material/waving_hand: I'm your voice-enabled AI assistant..."
        }
    ]

# Track processed audio to prevent reprocessing
if "processed_audio_id" not in st.session_state:
    st.session_state.processed_audio_id = None
```

* **`voice_messages`**: 전체 대화 기록을 저장합니다.
* **환영 메시지**: 항상 친근한 인사로 시작합니다.
* **`processed_audio_id`**: `st.rerun()` 후 중복 처리를 방지합니다.
* **지속성**: 모든 상태는 Streamlit 재실행 간에 유지됩니다.

#### 2. 사이드바 레이아웃

```python
with st.sidebar:
    st.title(":material/record_voice_over: Voice-Enabled Assistant")
    st.subheader(":material/mic: Record Your Message")
    audio = st.audio_input("Click to record")
    
    st.header(":material/settings: Settings")
    # Database configuration, stage status, clear chat
```

* **컴팩트한 디자인**: 모든 컨트롤이 사이드바에 있습니다.
* **Material 아이콘**: Streamlit material 아이콘을 사용한 현대적인 UI입니다.
* **녹음 우선**: 오디오 입력이 상단에 눈에 띄게 배치됩니다.
* **설정 하단 배치**: 데이터베이스 구성 및 스테이지 관리 기능이 아래에 있습니다.

#### 3. AI_TRANSCRIBE를 위한 스테이지 구성

```python
# Create stage with server-side encryption (required for AI_TRANSCRIBE)
session.sql(f"""
CREATE STAGE {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
""").collect()
```

* **서버 측 암호화**: `SNOWFLAKE_SSE`는 **필수**입니다 (클라이언트 측 암호화는 지원되지 않음).
* **디렉토리 테이블**: 파일 추적을 위해 `ENABLE = true`로 설정합니다.
* **자동 재생성**: 암호화가 잘못된 경우 스테이지가 삭제되고 다시 생성됩니다.
* **수동 버튼**: 사용자는 설정에서 스테이지 재생성을 강제할 수 있습니다.

#### 4. 대화 표시 (처리 전)

```python
# Display chat history FIRST (before processing)
st.subheader(":material/voice_chat: Conversation")
for msg in st.session_state.voice_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Create a container for processing status (appears below)
status_container = st.container()
```

* **지속적 표시**: 오디오 처리 전에 대화가 렌더링됩니다.
* **사라짐 방지**: 스피너는 아래의 별도 `status_container`에 나타납니다.
* **채팅 메시지**: Streamlit의 기본 `st.chat_message` 위젯을 사용합니다.
* **항상 표시**: 처리 중에도 대화 헤더와 메시지가 유지됩니다.

#### 5. 중복 제거를 포함한 오디오 처리

```python
if audio is not None:
    audio_bytes = audio.read()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    
    if audio_hash != st.session_state.processed_audio_id:
        st.session_state.processed_audio_id = audio_hash
        # Process audio...
```

* **콘텐츠 기반 해시**: 고유 식별을 위해 오디오 바이트의 MD5 해시를 사용합니다.
* **루프 방지**: 동일한 오디오가 여러 번 처리되지 않습니다.
* **재실행 안전**: Streamlit 재실행 간에 올바르게 작동합니다.
* **초기화**: 오디오가 없으면 해시가 지워집니다.

#### 6. AI_TRANSCRIBE를 사용한 음성 변환

```python
with status_container:
    with st.spinner(":material/mic: Transcribing audio..."):
        # Upload to stage
        audio_stream = io.BytesIO(audio_bytes)
        session.file.put_stream(
            audio_stream,
            f"{stage_name}/{filename}",
            overwrite=True,
            auto_compress=False
        )
        
        # Transcribe
        sql_query = f"""
        SELECT SNOWFLAKE.CORTEX.AI_TRANSCRIBE(
            TO_FILE('{stage_name}', '{filename}')
        ) as transcript
        """
        result = session.sql(sql_query).collect()
        transcript = json.loads(result[0]['TRANSCRIPT']).get('text', '')
```

* **`put_stream`**: 오디오 바이트를 Snowflake 스테이지에 업로드합니다.
* **`TO_FILE()`**: AI_TRANSCRIBE를 위해 스테이지된 파일을 참조합니다.
* **JSON 응답**: `{text, audio_duration}`을 반환합니다.
* **정리**: 음성 변환 후 스테이지된 파일이 제거됩니다.
* **상태 컨테이너**: 스피너가 대화를 대체하지 않고 아래에 나타납니다.

#### 7. 채팅 기록 메모리

```python
# Build conversation history for context
conversation_context = "You are a friendly voice assistant...\n\nConversation history:\n"

# Add previous messages (excluding welcome)
history_messages = [msg for msg in st.session_state.voice_messages 
                   if not (msg["role"] == "assistant" and "Click the microphone button" in msg["content"])]

for msg in history_messages:
    role = "User" if msg["role"] == "user" else "Assistant"
    conversation_context += f"{role}: {msg['content']}\n"

# Add current user message
conversation_context += f"\nUser: {transcript}\n\nAssistant:"
```

* **전체 컨텍스트**: LLM은 전체 대화 기록을 받습니다.
* **환영 메시지 제외**: 초기 인사 메시지를 필터링합니다.
* **형식화된 프롬프트**: 사용자/비서 레이블이 있는 명확한 구조입니다.
* **문맥 인식**: 비서는 이전 대화를 참조할 수 있습니다.

#### 8. 응답 생성

```python
with st.spinner(":material/smart_toy: Generating response..."):
    response = call_llm(conversation_context)
    
    st.session_state.voice_messages.append({
        "role": "assistant",
        "content": response
    })

st.rerun()
```

* **별도 스피너**: 음성 변환이 완료된 후 표시됩니다.
* **Snowflake Cortex**: Claude 3.5 Sonnet과 함께 SQL 기반 `ai_complete()` 함수를 사용합니다.
* **범용 호환성**: 모든 배포 환경(SiS, Community Cloud, 로컬)에서 작동합니다.
* **응답 추가**: 대화 기록에 추가합니다.
* **재실행**: 새 메시지를 표시하기 위해 UI를 업데이트합니다.

#### 9. 채팅 지우기 기능

```python
if st.button(":material/delete: Clear Chat"):
    st.session_state.voice_messages = [
        {
            "role": "assistant",
            "content": "Hello! :material/waving_hand: I'm your voice-enabled AI assistant..."
        }
    ]
    st.rerun()
```

* **환영 메시지로 초기화**: 기록을 지우지만 인사를 복원합니다.
* **새로운 시작**: 사용자는 새 대화를 시작할 수 있습니다.
* **사이드바 버튼**: 설정 섹션에서 쉽게 접근할 수 있습니다.

---

### :material/adjust: 주요 기능

| 기능 | 구현 |
|---------|----------------|
| **음성 입력** | 사이드바의 `st.audio_input` 위젯 |
| **음성 변환** | `TO_FILE()` 구문을 사용하는 `AI_TRANSCRIBE` |
| **채팅 메모리** | LLM에 전달되는 전체 대화 기록 |
| **지속적인 UI** | 처리 전에 대화 표시 |
| **중복 제거** | MD5 해시가 재처리를 방지 |
| **스테이지 구성** | 서버 측 암호화, 디렉토리 활성화 |
| **오류 처리** | 일반적인 문제에 대한 해결 가이드 |
| **Material 아이콘** | Streamlit material 디자인을 사용한 현대적인 UI |

---

### :material/library_books: 주요 기술 개념

**세션 상태 변수:**
- `voice_messages`: 대화 메시지 목록 (역할, 내용)
- `processed_audio_id`: 마지막으로 처리된 오디오의 MD5 해시
- `voice_database` / `voice_schema`: 구성 가능한 데이터베이스 위치

**오디오 처리:**
- 오디오 바이트 → MD5 해시 → 새로운지 확인 → 스테이지에 업로드 → 음성 변환 → 응답

**AI_TRANSCRIBE를 위한 스테이지 요구 사항:**
- :material/check_circle: 서버 측 암호화 (`SNOWFLAKE_SSE`)
- :material/check_circle: 디렉토리 테이블 활성화
- :material/cancel: 클라이언트 측 암호화는 지원되지 않음

**UI 패턴:**
1. 대화 먼저 표시
2. 상태 컨테이너 생성
3. 상태 컨테이너에서 오디오 처리
4. 스피너가 대화 아래에 나타남
5. 새 메시지를 표시하기 위해 재실행

---

### :material/library_books: 리소스

- [st.audio_input 문서](https://docs.streamlit.io/develop/api-reference/widgets/st.audio_input)
- [st.chat_message 문서](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message)
- [Snowflake AI_TRANSCRIBE 문서](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-audio)
- [Snowflake Cortex Complete](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Streamlit Material Icons](https://streamlit.io/components)
