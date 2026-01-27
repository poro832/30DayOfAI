# Day 21
# Cortex Search를 활용한 RAG (RAG with Cortex Search)

import streamlit as st

st.title(":material/link: Cortex Search를 활용한 RAG")
st.write("검색 결과와 LLM 생성을 결합하여 근거 있는 답변을 제공합니다.")

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

st.divider()
st.subheader(":material/menu_book: RAG 작동 방식 (How RAG Works)")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("**:material/looks_one: 검색 (Retrieve)**")
        st.markdown("""
        Cortex Search가 
        질문을 기반으로 
        관련 문서 청크를 
        찾습니다.
        """)

with col2:
    with st.container(border=True):
        st.markdown("**:material/looks_two: 증강 (Augment)**")
        st.markdown("""
        검색된 청크가 
        LLM의 컨텍스트로 
        프롬프트에 
        추가됩니다.
        """)

with col3:
    with st.container(border=True):
        st.markdown("**:material/looks_3: 생성 (Generate)**")
        st.markdown("""
        LLM이 검색된 
        문서를 바탕으로 
        근거 있는 답변을 
        생성합니다.
        """)

st.divider()

# 사이드바 구성
with st.sidebar:
    st.header(":material/settings: 설정 (Settings)")
    
    # Day 19의 기본 검색 서비스
    default_service = 'RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH'
    
    # 사용 가능한 서비스 가져오기 시도
    try:
        services_result = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
        available_services = [f"{row['database_name']}.{row['schema_name']}.{row['name']}" 
                            for row in services_result] if services_result else []
    except:
        available_services = []
    
    # 기본 서비스가 항상 첫 번째에 오도록 설정
    if default_service in available_services:
        available_services.remove(default_service)
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
            "검색 서비스:",
            value=default_service,
            placeholder="database.schema.service_name",
            help="Cortex Search 서비스의 전체 경로"
        )
    
    num_chunks = st.slider("컨텍스트 청크 수:", 1, 10, 3,
                           help="검색할 관련 청크의 수")
    
    model = st.selectbox(
        "LLM 모델:",
        ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"],
        help="답변을 생성할 모델"
    )
    
    show_context = st.checkbox("검색된 컨텍스트 표시", value=True)

# 메인 인터페이스
st.subheader(":material/help: 질문하기 (Ask a Question)")

question = st.text_input(
    "질문:",
    value="Are the thermal gloves warm enough for winter?",
    placeholder="예: 어떤 제품에 내구성 문제가 있나요?"
)

if st.button(":material/search: 검색 및 답변 (Search & Answer)", type="primary"):
    if question and search_service:
        with st.status("처리 중...", expanded=True) as status:
            
            # 1단계: Cortex Search에서 컨텍스트 검색
            st.write(":material/search: **1단계:** 문서 검색 중...")
            
            try:
                from snowflake.core import Root
                
                root = Root(session)
                parts = search_service.split(".")
                
                if len(parts) != 3:
                    st.error("서비스 경로는 다음 형식이어야 합니다: database.schema.service_name")
                    st.stop()
                
                svc = (root
                    .databases[parts[0]]
                    .schemas[parts[1]]
                    .cortex_search_services[parts[2]])
                
                search_results = svc.search(
                    query=question,
                    columns=["CHUNK_TEXT", "FILE_NAME"],
                    limit=num_chunks
                )
                
                # 메타데이터와 함께 컨텍스트 추출
                context_chunks = []
                sources = []
                for item in search_results.results:
                    context_chunks.append(item.get("CHUNK_TEXT", ""))
                    sources.append(item.get("FILE_NAME", "Unknown"))
                
                context = "\n\n---\n\n".join(context_chunks)
                
                st.write(f"   :material/check_circle: {len(context_chunks)}개의 관련 청크 발견")
                
                # 2단계: LLM으로 답변 생성
                st.write(":material/smart_toy: **2단계:** 답변 생성 중...")
                
                rag_prompt = f"""You are a helpful assistant. Answer the user's question based ONLY on the provided context.
If the context doesn't contain enough information to answer, say "I don't have enough information to answer that based on the available documents."

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}

Provide a clear, accurate answer based on the context. If you use information from the context, mention it naturally."""
                
                # [실습] LLM을 호출하여 답변을 생성하세요.
                # 힌트: SNOWFLAKE.CORTEX.COMPLETE(model, prompt) 함수를 사용하세요.
                
                response_sql = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{model}',
                    '{rag_prompt.replace("'", "''")}'
                ) as response
                """
                
                # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
                # response = session.sql(response_sql).collect()[0][0]
                
                # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요.
                response = "실습 코드를 완성하여 답변을 생성하세요." # 이 부분을 수정하세요
                pass
                
                # [실습 정답용 코드 - 학생에게 제공하지 않음 / 실제 동작을 위해 아래 코드를 사용하지만, 학생 버전에서는 가려야 합니다]
                # response = session.sql(response_sql).collect()[0][0]

                st.write("   :material/check_circle: 답변 생성됨")
                status.update(label="완료!", state="complete", expanded=True)
                
                # 결과 표시
                st.divider()
                
                st.subheader(":material/lightbulb: 답변 (Answer)")
                with st.container(border=True):
                    st.markdown(response)
                
                if show_context:
                    st.subheader(":material/library_books: 검색된 컨텍스트 (Retrieved Context)")
                    st.caption(f"고객 리뷰에서 {len(context_chunks)}개의 청크 사용됨")
                    for i, (chunk, source) in enumerate(zip(context_chunks, sources), 1):
                        with st.expander(f":material/description: 청크 {i} - {source}"):
                            st.write(chunk)
                
            except Exception as e:
                status.update(label="오류", state="error")
                st.error(f"오류: {str(e)}")
                st.info(":material/lightbulb: **문제 해결:**\n- 검색 서비스가 존재하는지 확인하세요 (Day 19 확인)\n- 서비스 인덱싱이 완료되었는지 확인하세요\n- 권한을 확인하세요")
    else:
        st.warning(":material/warning: 질문을 입력하고 검색 서비스를 구성하세요.")
        st.info(":material/lightbulb: **검색 서비스가 필요한가요?**\n- Day 19를 완료하여 `CUSTOMER_REVIEW_SEARCH`를 생성하세요\n- 서비스가 위의 드롭다운에 자동으로 나타납니다")

st.divider()
st.caption("Day 21: Cortex Search를 활용한 RAG (RAG with Cortex Search) | 30 Days of AI")
