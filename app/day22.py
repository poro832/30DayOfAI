# Day 22
# 내 문서와 채팅하기 (Chat with Your Documents)

import streamlit as st

st.title(":material/chat: 내 문서와 채팅하기 (Chat with Your Documents)")
st.write("Cortex Search를 기반으로 하는 대화형 RAG 챗봇입니다.")

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 상태 초기화
if "doc_messages" not in st.session_state:
    st.session_state.doc_messages = []

# 사이드바
with st.sidebar:
    st.header(":material/settings: 설정 (Settings)")
    
    # Day 19의 검색 서비스 확인
    default_service = st.session_state.get('search_service', 'RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH')
    
    # 사용 가능한 서비스 가져오기 시도
    try:
        services_result = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
        available_services = [f"{row['database_name']}.{row['schema_name']}.{row['name']}" 
                            for row in services_result] if services_result else []
    except:
        available_services = []
    
    # 기본 서비스가 항상 목록의 첫 번째에 오도록 설정
    if default_service:
        # 목록의 다른 곳에 있다면 제
        if default_service in available_services:
            available_services.remove(default_service)
        # 맨 앞에 추가
        available_services.insert(0, default_service)
    
    # 수동 입력 옵션 추가
    if available_services:
        available_services.append("-- 직접 입력 (Enter manually) --")
        
        search_service_option = st.selectbox(
            "검색 서비스:",
            options=available_services,
            index=0,
            help="Day 19에서 생성한 Cortex Search 서비스를 선택하세요"
        )
        
        # 수동 입력 선택 시 텍스트 입력 표시
        if search_service_option == "-- 직접 입력 (Enter manually) --":
            search_service = st.text_input(
                "서비스 경로 입력:",
                placeholder="database.schema.service_name"
            )
        else:
            search_service = search_service_option
            
            # Day 19 서비스인 경우 상태 표시
            if search_service == st.session_state.get('search_service'):
                st.caption(":material/check_circle: Day 19의 서비스를 사용 중입니다")
    else:
        # 서비스가 없는 경우 텍스트 입력으로 대체
        search_service = st.text_input(
            "Cortex Search 서비스:",
            value=default_service,
            placeholder="database.schema.service_name"
        )
    
    num_chunks = st.slider("컨텍스트 청크 수:", 1, 5, 3,
                           help="질문당 검색할 관련 청크의 수")
    
    st.divider()
    
    if st.button(":material/delete: 채팅 지우기 (Clear Chat)", use_container_width=True):
        st.session_state.doc_messages = []
        st.rerun()

# 검색 함수
def search_documents(query, service_path, limit):
    from snowflake.core import Root
    root = Root(session)
    parts = service_path.split(".")
    if len(parts) != 3:
        raise ValueError("서비스 경로는 다음 형식이어야 합니다: database.schema.service_name")
    svc = root.databases[parts[0]].schemas[parts[1]].cortex_search_services[parts[2]]
    results = svc.search(query=query, columns=["CHUNK_TEXT", "FILE_NAME"], limit=limit)
    
    chunks_data = []
    for item in results.results:
        chunks_data.append({
            "text": item.get("CHUNK_TEXT", ""),
            "source": item.get("FILE_NAME", "Unknown")
        })
    return chunks_data

# 메인 인터페이스
if not search_service:
    st.info(":material/arrow_back: 채팅을 시작하려면 Cortex Search 서비스를 구성하세요!")
    st.caption(":material/lightbulb: **검색 서비스가 필요한가요?**\n- Day 19를 완료하여 `CUSTOMER_REVIEW_SEARCH`를 생성하세요\n- 서비스가 위의 드롭다운에 자동으로 나타납니다")
else:
    # 채팅 기록 표시
    for msg in st.session_state.doc_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # 채팅 입력
    if prompt := st.chat_input("문서에 대해 질문하세요..."):
        st.session_state.doc_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                with st.spinner("검색 및 생각 중..."):
                    # 컨텍스트 검색
                    chunks_data = search_documents(prompt, search_service, num_chunks)
                    context = "\n\n---\n\n".join([c["text"] for c in chunks_data])
                    
                    # 가드레일이 포함된 응답 생성
                    rag_prompt = f"""You are a customer review analysis assistant. Your role is to ONLY answer questions about customer reviews and feedback.

STRICT GUIDELINES:
1. ONLY use information from the provided customer review context below
2. If asked about topics unrelated to customer reviews (e.g., general knowledge, coding, math, news), respond: "I can only answer questions about customer reviews. Please ask about product feedback, customer experiences, or review insights."
3. If the context doesn't contain relevant information, say: "I don't have enough information in the customer reviews to answer that."
4. Stay focused on: product features, customer satisfaction, complaints, praise, quality, pricing, shipping, or customer service mentioned in reviews
5. Do NOT make up information or use knowledge outside the provided reviews

CONTEXT FROM CUSTOMER REVIEWS:
{context}

USER QUESTION: {prompt}

Provide a clear, helpful answer based ONLY on the customer reviews above. If you cite information, mention it naturally."""
                    
                    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', '{rag_prompt.replace(chr(39), chr(39)+chr(39))}')"
                    
                    # [실습] 생성된 SQL을 실행하여 LLM 응답을 얻으세요.
                    # 힌트: session.sql(sql).collect()[0][0]
                    
                    # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
                    # response = session.sql(sql).collect()[0][0]
                    
                    # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요. 
                    response = "실습 코드를 완성하여 답변을 생성하세요." # 이 부분을 수정하세요
                    pass

                    # [실습 정답용 코드 - 학생에게 제공하지 않음 / 실제 동작을 위해 아래 코드를 사용하지만, 학생 버전에서는 가려야 합니다]
                    # response = session.sql(sql).collect()[0][0]
                
                st.markdown(response)
                
                # 파일 이름과 함께 출처 표시
                with st.expander(f":material/library_books: 출처 ({len(chunks_data)}개 리뷰 사용됨)"):
                    for i, chunk_info in enumerate(chunks_data, 1):
                        st.caption(f"**[{i}] {chunk_info['source']}**")
                        st.write(chunk_info['text'][:200] + "..." if len(chunk_info['text']) > 200 else chunk_info['text'])
                
                st.session_state.doc_messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"오류: {str(e)}")
                st.info(":material/lightbulb: **문제 해결:**\n- 검색 서비스가 존재하는지 확인하세요 (Day 19 확인)\n- 서비스 인덱싱이 완료되었는지 확인하세요\n- 권한을 확인하세요")

st.divider()
st.caption("Day 22: 내 문서와 채팅하기 (Chat with Your Documents) | 30 Days of AI")
