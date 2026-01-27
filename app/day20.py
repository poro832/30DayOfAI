# Day 20
# Cortex Search 쿼리하기 (Querying Cortex Search)

import streamlit as st
from snowflake.core import Root

st.title(":material/search: Cortex Search 쿼리하기 (Querying Cortex Search)")
st.write("Cortex Search 서비스를 사용하여 관련 텍스트 청크를 검색합니다.")

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 입력 컨테이너
with st.container(border=True):
    st.subheader(":material/search: 검색 구성 및 쿼리 (Search Configuration and Query)")
    
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
            "검색 서비스 (Search Service):",
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
                st.success(":material/check_circle: Day 19의 서비스를 사용 중입니다")
    else:
        # 서비스가 없는 경우 텍스트 입력으로 대체
        search_service = st.text_input(
            "검색 서비스 (Search Service):",
            value=default_service,
            placeholder="database.schema.service_name",
            help="Cortex Search 서비스의 전체 경로"
        )
    
    st.code(search_service, language="sql")
    st.caption(":material/lightbulb: 이것은 Day 19의 CUSTOMER_REVIEW_SEARCH 서비스를 가리켜야 합니다")

    st.divider()

    # 검색 쿼리 입력
    query = st.text_input(
        "검색 쿼리 입력:",
        value="warm thermal gloves",
        placeholder="예: 내구성 문제, 편안한 헬멧"
    )

    num_results = st.slider("결과 수 (Number of results):", 1, 20, 5)
    
    search_clicked = st.button(":material/search: 검색 (Search)", type="primary", use_container_width=True)

# 출력 컨테이너
with st.container(border=True):
    st.subheader(":material/analytics: 검색 결과 (Search Results)")
    
    if search_clicked:
        if query and search_service:
            try:
                root = Root(session)
                parts = search_service.split(".")
                
                if len(parts) != 3:
                    st.error("서비스 경로는 다음 형식이어야 합니다: database.schema.service_name")
                else:
                    svc = (root
                        .databases[parts[0]]
                        .schemas[parts[1]]
                        .cortex_search_services[parts[2]])
                    
                    with st.spinner("검색 중..."):
                        # [실습] svc.search 메서드를 사용하여 검색을 수행하세요.
                        # 힌트: svc.search(query=..., columns=..., limit=...)
                        
                        # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
                        # results = svc.search(
                        #     query=query,
                        #     columns=["CHUNK_TEXT", "FILE_NAME", "CHUNK_TYPE", "CHUNK_ID"],
                        #     limit=num_results
                        # )
                        
                        # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요.
                        results = None # 이 부분을 수정하세요
                        pass 

                        # [실습 정답용 코드 - 학생에게 제공하지 않음 / 실제 동작을 위해 아래 코드를 사용하지만, 학생 버전에서는 가려야 합니다]
                        # results = svc.search(
                        #    query=query,
                        #    columns=["CHUNK_TEXT", "FILE_NAME", "CHUNK_TYPE", "CHUNK_ID"],
                        #    limit=num_results
                        # )
                    
                    if results:
                        st.success(f":material/check_circle: {len(results.results)}개의 결과를 찾았습니다!")
                        
                        # 결과 표시
                        for i, item in enumerate(results.results, 1):
                            with st.container(border=True):
                                col1, col2, col3 = st.columns([2, 1, 1])
                                with col1:
                                    st.markdown(f"**Result {i}** - {item.get('FILE_NAME', 'N/A')}")
                                with col2:
                                    st.caption(f"Type: {item.get('CHUNK_TYPE', 'N/A')}")
                                with col3:
                                    st.caption(f"Chunk: {item.get('CHUNK_ID', 'N/A')}")
                                
                                st.write(item.get("CHUNK_TEXT", "No text found"))
                                
                                # 관련성 점수가 있는 경우 표시
                                if hasattr(item, 'score') or 'score' in item:
                                    score = item.get('score', item.score if hasattr(item, 'score') else None)
                                    if score is not None:
                                        st.caption(f"Relevance Score: {score:.4f}")
                    else:
                        st.warning("결과가 반환되지 않았습니다. 실습 코드를 확인하세요.")
            
            except Exception as e:
                st.error(f"오류: {str(e)}")
                st.info(":material/lightbulb: **문제 해결:**\n- 검색 서비스가 존재하는지 확인하세요 (Day 19 확인)\n- 서비스 인덱싱이 완료되었는지 확인하세요\n- 액세스 권한이 있는지 확인하세요")
        else:
            st.warning(":material/warning: 쿼리를 입력하고 검색 서비스를 구성하세요.")
            st.info(":material/lightbulb: **검색 서비스가 필요한가요?**\n- Day 19를 완료하여 `CUSTOMER_REVIEW_SEARCH`를 생성하세요\n- 서비스가 위의 드롭다운에 자동으로 나타납니다")
    else:
        st.info(":material/arrow_upward: 검색 서비스를 구성하고 쿼리를 입력한 후, 검색을 클릭하여 결과를 확인하세요.")

st.divider()
st.caption("Day 20: Cortex Search 쿼리하기 (Querying Cortex Search) | 30 Days of AI")
