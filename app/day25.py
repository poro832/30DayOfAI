# Day 25
# 음성 인터페이스 (Voice Interface)

import streamlit as st
import json
from snowflake.snowpark.functions import ai_complete
import io
import time
import hashlib

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

def call_llm(prompt_text: str) -> str:
    """Snowflake Cortex LLM 호출."""
    df = session.range(1).select(
        ai_complete(model="claude-3-5-sonnet", prompt=prompt_text).alias("response")
    )
    response_raw = df.collect()[0][0]
    response_json = json.loads(response_raw)
    if isinstance(response_json, dict):
        return response_json.get("choices", [{}])[0].get("messages", "")
    return str(response_json)

# 상태 초기화
if "voice_messages" not in st.session_state:
    st.session_state.voice_messages = []

# 환영 메시지가 항상 존재하는지 확인
if len(st.session_state.voice_messages) == 0:
    st.session_state.voice_messages = [
        {
            "role": "assistant",
            "content": "안녕하세요! :material/waving_hand: 저는 음성 지원 AI 비서입니다. 사이드바의 마이크 버튼을 클릭하여 메시지를 녹음하면 답변해 드립니다!"
        }
    ]

if "voice_database" not in st.session_state:
    st.session_state.voice_database = "RAG_DB"
    st.session_state.voice_schema = "RAG_SCHEMA"

if "processed_audio_id" not in st.session_state:
    st.session_state.processed_audio_id = None

# 세션 상태에서 스테이지 경로 가져오기
database = st.session_state.voice_database
schema = st.session_state.voice_schema
full_stage_name = f"{database}.{schema}.VOICE_AUDIO"
stage_name = f"@{full_stage_name}"

# 사이드바
with st.sidebar:
    # 상단 제목 및 설명
    st.title(":material/record_voice_over: AI 음성 비서 (Voice-Enabled Assistant)")
    st.write("음성 입력을 사용하여 AI 비서와 대화하세요!")
    
    # 오디오 녹음 섹션
    st.subheader(":material/mic: 메시지 녹음 (Record Your Message)")
    audio = st.audio_input("클릭하여 녹음")
    
    st.header(":material/settings: 설정 (Settings)")
    
    with st.expander("데이터베이스 구성", expanded=False):
        database = st.text_input("Database", value=st.session_state.voice_database, key="db_input")
        schema = st.text_input("Schema", value=st.session_state.voice_schema, key="schema_input")
        
        # 세션 상태 업데이트
        st.session_state.voice_database = database
        st.session_state.voice_schema = schema
        
        st.caption(f"Stage: `{database}.{schema}.VOICE_AUDIO`")
        st.caption(":material/edit_note: 스테이지는 서버 측 암호화를 사용합니다 (AI_TRANSCRIBE 필수)")
        
        # 수동 스테이지 재생성 버튼
        if st.button(":material/autorenew: 스테이지 재생성", help="올바른 암호화로 스테이지를 삭제하고 다시 생성합니다"):
            try:
                full_stage = f"{database}.{schema}.VOICE_AUDIO"
                session.sql(f"DROP STAGE IF EXISTS {full_stage}").collect()
                session.sql(f"""
                CREATE STAGE {full_stage}
                    DIRECTORY = ( ENABLE = true )
                    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
                """).collect()
                st.success(f":material/check_circle: 스테이지가 성공적으로 재생성되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"스테이지 재생성 실패: {str(e)}")
    
    # 스테이지 상태
    with st.expander("스테이지 상태 (Stage Status)", expanded=False):
        # 데이터베이스 및 스키마 가져오기
        database = st.session_state.voice_database
        schema = st.session_state.voice_schema
        full_stage_name = f"{database}.{schema}.VOICE_AUDIO"
        
        # AI_TRANSCRIBE를 위한 적절한 구성으로 스테이지 생성
        try:
            # 잘못된 암호화로 스테이지가 존재하는지 확인
            stage_info = session.sql(f"SHOW STAGES LIKE 'VOICE_AUDIO' IN SCHEMA {database}.{schema}").collect()
            
            if stage_info:
                # 스테이지가 존재하면 드롭하고 다시 생성하여 올바른 암호화 확인
                st.info(f":material/autorenew: 서버 측 암호화로 스테이지 재생성 중...")
                session.sql(f"DROP STAGE IF EXISTS {full_stage_name}").collect()
            
            # 서버 측 암호화로 스테이지 생성 (AI_TRANSCRIBE 필수)
            session.sql(f"""
            CREATE STAGE {full_stage_name}
                DIRECTORY = ( ENABLE = true )
                ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' )
            """).collect()
            st.success(f":material/check_box: 오디오 스테이지 준비됨 (서버 측 암호화)")
            
        except Exception as e:
            st.error(f":material/cancel: 스테이지를 생성할 수 없습니다")
            
            with st.expander(":material/build: 수동 수정"):
                st.code(f"""
DROP STAGE IF EXISTS {full_stage_name};
CREATE STAGE {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );
                """, language="sql")
                st.caption("위의 ':material/autorenew: 스테이지 재생성' 버튼을 사용하세요")
    
    if st.button(":material/delete: 대화 지우기"):
        st.session_state.voice_messages = [
            {
                "role": "assistant",
                "content": "안녕하세요! :material/waving_hand: 저는 음성 지원 AI 비서입니다. 사이드바의 마이크 버튼을 클릭하여 메시지를 녹음하면 답변해 드립니다!"
            }
        ]
        st.rerun()

# 채팅 기록 먼저 표시 (처리 전)
st.subheader(":material/voice_chat: 대화 (Conversation)")
for msg in st.session_state.voice_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 처리 상태를 위한 컨테이너 생성 (대화 아래에 표시됨)
status_container = st.container()

# 오디오 녹음 시 처리
if audio is not None:
    # 오디오 바이트 읽기 및 고유 녹음 식별을 위한 해시 생성
    audio_bytes = audio.read()
    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    
    # 이 오디오가 아직 처리되지 않은 경우에만 처리
    if audio_hash != st.session_state.processed_audio_id:
        st.session_state.processed_audio_id = audio_hash
        
        with status_container:
            transcript = None
            with st.spinner(":material/mic: 오디오 변환 중..."):
                try:
                    # 타임스탬프로 고유 파일 이름 생성
                    timestamp = int(time.time())
                    filename = f"audio_{timestamp}.wav"
                    
                    # put_stream을 위해 바이트를 BytesIO로 래핑
                    audio_stream = io.BytesIO(audio_bytes)
                    full_stage_path = f"{stage_name}/{filename}"
                    
                    # Snowflake 스테이지에 업로드
                    session.file.put_stream(
                        audio_stream,
                        full_stage_path,
                        overwrite=True,
                        auto_compress=False
                    )
                    
                    # SQL을 위한 파일 이름 정리
                    safe_file_name = filename.replace("'", "''")
                    
                    # AI_TRANSCRIBE 실행
                    sql_query = f"""
                    SELECT SNOWFLAKE.CORTEX.AI_TRANSCRIBE(
                        TO_FILE('{stage_name}', '{safe_file_name}')
                    ) as transcript
                    """
                    
                    result_rows = session.sql(sql_query).collect()
                    
                    if result_rows:
                        # JSON 응답 파싱
                        json_string = result_rows[0]['TRANSCRIPT']
                        transcript_data = json.loads(json_string)
                        transcript = transcript_data.get("text", "")
                        
                        if transcript:
                            # 사용자 메시지 추가
                            st.session_state.voice_messages.append({
                                "role": "user",
                                "content": transcript
                            })
                        else:
                            st.error("음성 변환에서 텍스트가 반환되지 않았습니다.")
                            st.json(transcript_data)
                    else:
                        st.error("음성 변환 쿼리가 결과를 반환하지 않았습니다.")
                
                except Exception as e:
                    st.error(f"음성 변환 중 오류 발생: {str(e)}")
                    
                    with st.expander(":material/edit_note: 문제 해결"):
                        st.code(f"""
-- 스테이지는 적절한 구성으로 생성되어야 합니다:
CREATE STAGE IF NOT EXISTS {full_stage_name}
    DIRECTORY = ( ENABLE = true )
    ENCRYPTION = ( TYPE = 'SNOWFLAKE_SSE' );

-- 예상되는 음성 변환 SQL:
SELECT SNOWFLAKE.CORTEX.AI_TRANSCRIBE(
    TO_FILE('{stage_name}', 'audio_xxxxx.wav')
) as transcript;
                        """, language="sql")
                        
                        st.markdown("""
                        **일반적인 문제:**
                        - **클라이언트 측 암호화 오류**: 스테이지는 클라이언트 측이 아닌 서버 측 암호화(`SNOWFLAKE_SSE`)를 사용해야 합니다.
                        - **디렉토리 테이블**: 스테이지에 `DIRECTORY = ( ENABLE = true )`가 있어야 합니다.
                        - **권한**: `SNOWFLAKE.CORTEX.AI_TRANSCRIBE`를 사용할 수 있는지 확인하세요.
                        - **가용성**: Snowflake 계정/리전에서 `AI_TRANSCRIBE`를 사용할 수 있는지 확인하세요.
                        - **오디오 형식**: 녹음된 오디오는 기본적으로 WAV 형식입니다.
                        
                        **참조:** [Snowflake AI_TRANSCRIBE 문서](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-audio)
                        """)
            
            # 음성 변환이 성공하면 어시스턴트 응답 생성
            if transcript:
                with st.spinner(":material/smart_toy: 응답 생성 중..."):
                    # 컨텍스트를 위한 대화 기록 구축
                    conversation_context = "You are a friendly voice assistant. Keep responses short and conversational.\n\nConversation history:\n"
                    
                    # 이전 메시지 추가 (환영 메시지가 유일한 경우 제외)
                    history_messages = st.session_state.voice_messages[:-1] if len(st.session_state.voice_messages) > 1 else []
                    
                    # 기록에서 환영 메시지 건너뛰기
                    history_messages = [msg for msg in history_messages if not (msg["role"] == "assistant" and "마이크 버튼을 클릭하여" in msg["content"])]
                    
                    for msg in history_messages:
                        role = "User" if msg["role"] == "user" else "Assistant"
                        conversation_context += f"{role}: {msg['content']}\n"
                    
                    # 현재 사용자 메시지 추가
                    conversation_context += f"\nUser: {transcript}\n\nAssistant:"
                    
                    response = call_llm(conversation_context)
                    
                    st.session_state.voice_messages.append({
                        "role": "assistant",
                        "content": response
                    })
                
                # 스테이지된 파일 정리
                try:
                    session.sql(f"REMOVE {stage_name}/{safe_file_name}").collect()
                except:
                    pass
                
                st.rerun()
else:
    # 오디오가 없으면 처리된 오디오 ID 초기화
    st.session_state.processed_audio_id = None

st.divider()
st.caption("Day 25: 음성 인터페이스 (Voice Interface) | 30 Days of AI")
