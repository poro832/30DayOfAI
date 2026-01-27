# 음성 인터페이스 (Voice Interface)

# 0. 목표

<aside>
💡

**음성 대화가 가능한 AI 비서 구현**

1. 음성 녹음 및 Snowflake 스테이지 저장
2. `AI_TRANSCRIBE` 함수를 사용한 음성-텍스트 변환 (STT)
3. 대화 맥락을 이해하고 응답하는 챗봇 구현

</aside>

# 1. 개요 (Overview)

- **음성 인터페이스(Voice Interface)**: 키보드 입력 대신 목소리로 AI와 상호작용하는 방식입니다.
- **Snowflake Cortex**: `AI_TRANSCRIBE` 함수를 통해 오디오 파일에서 텍스트를 추출할 수 있습니다.
- **오디오 처리**: 스트림릿의 `st.audio_input`을 통해 받은 오디오 데이터를 Snowflake 스테이지에 업로드하여 처리합니다.

# 2. 구현 내용 (Implementation)

## 2-1. 오디오 처리를 위한 스테이지 설정

`AI_TRANSCRIBE` 함수는 스테이지에 있는 파일만 읽을 수 있으며, **서버 측 암호화(Server-Side Encryption)**가 필수적입니다.

```sql
CREATE STAGE IF NOT EXISTS VOICE_AUDIO
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' ); -- 필수: 서버 측 암호화
```

## 2-2. 음성 녹음 및 업로드

Streamlit의 `st.audio_input` 위젯을 사용하여 사용자의 목소리를 녹음합니다.

```python
# 음성 입력 위젯
audio = st.audio_input("클릭하여 녹음")

if audio:
    # 중복 처리 방지를 위한 해시 생성
    audio_bytes = audio.read()
    
    # 스테이지에 업로드
    session.file.put_stream(
        io.BytesIO(audio_bytes),
        f"@{stage_name}/{filename}",
        overwrite=True,
        auto_compress=False
    )
```

## 2-3. 음성 인식 (STT) 호출

업로드된 오디오 파일을 `AI_TRANSCRIBE` 함수로 전달하여 텍스트로 변환합니다.

```python
sql_query = f"""
SELECT SNOWFLAKE.CORTEX.AI_TRANSCRIBE(
    TO_FILE('@{stage_name}', '{filename}')
) as transcript
"""

result = session.sql(sql_query).collect()
transcript = json.loads(result[0]['TRANSCRIPT'])['text']
```

## 2-4. 대화 맥락 유지

변환된 텍스트를 LLM에 전달할 때, 이전 대화 기록을 함께 제공하여 자연스러운 대화를 이어갑니다.

```python
# 대화 기록 구성
context = "Conversation history:\n"
for msg in st.session_state.voice_messages:
    context += f"{msg['role']}: {msg['content']}\n"

# 현재 질문 추가
context += f"User: {transcript}\nAssistant:"
```

# 3. 활용 사례 (Use Cases)

1. **핸즈프리 비서**: 손을 쓸 수 없는 상황에서 음성으로 정보 검색
2. **회의록 작성**: 회의 내용을 녹음하여 텍스트로 자동 변환 및 요약
3. **언어 학습**: 외국어 발음을 텍스트로 변환하여 교정

# 4. 실행 결과

## 실행 코드

`python -m streamlit run app/day25.py`

## 결과

- 사이드바의 마이크 버튼을 누르고 말을 하면, 잠시 후 AI가 내용을 이해하고 텍스트로 답변을 줍니다.
- 대화 내용이 화면에 채팅 형식으로 표시됩니다.
