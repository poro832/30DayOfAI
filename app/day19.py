# Day 19
# 고객 리뷰를 위한 Cortex Search 생성 (Creating Cortex Search for Customer Reviews)

import streamlit as st
from snowflake.core import Root
import pandas as pd

st.title(":material/search: 고객 리뷰 Cortex Search (Cortex Search for Customer Reviews)")
st.write("Day 16-18에서 처리된 고객 리뷰에 대한 의미론적 검색(Semantic Search) 서비스를 생성합니다.")

# Snowflake 연결
try:
    # Streamlit in Snowflake에서 작동
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # 로컬 및 Streamlit Community Cloud에서 작동
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 데이터베이스 구성을 위한 세션 상태 초기화
if 'day19_database' not in st.session_state:
    # Day 18에서 임베딩 확인
    if 'embeddings_database' in st.session_state:
        st.session_state.day19_database = st.session_state.embeddings_database
        st.session_state.day19_schema = st.session_state.embeddings_schema
    else:
        st.session_state.day19_database = "RAG_DB"
        st.session_state.day19_schema = "RAG_SCHEMA"

# 데이터베이스 구성
with st.container(border=True):
    st.subheader(":material/analytics: 데이터베이스 구성 (Database Configuration)")
    
    # 데이터베이스 구성
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.day19_database = st.text_input(
            "Database", 
            value=st.session_state.day19_database, 
            key="day19_db_input"
        )
    with col2:
        st.session_state.day19_schema = st.text_input(
            "Schema", 
            value=st.session_state.day19_schema, 
            key="day19_schema_input"
        )
    
    st.info(f":material/location_on: 사용 위치: `{st.session_state.day19_database}.{st.session_state.day19_schema}`")
    st.caption(":material/lightbulb: REVIEW_CHUNKS 테이블이 이 위치에 존재하는지 확인하세요.")

# 1단계: 데이터 뷰 준비
with st.container(border=True):
    st.subheader("1단계: 데이터 뷰 준비 (Prepare the Data View)")
    
    st.markdown("""
    검색을 위해 리뷰 청크와 메타데이터를 결합하는 뷰를 생성합니다:
    """)
    
    st.code(f"""
-- 고객 리뷰의 검색 가능한 뷰 생성
CREATE OR REPLACE VIEW {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW AS
SELECT 
    rc.CHUNK_ID,
    rc.CHUNK_TEXT,              -- 리뷰 텍스트 (검색 대상)
    rc.FILE_NAME,
    rc.DOC_ID,
    rc.CHUNK_TYPE
FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_CHUNKS rc
WHERE rc.CHUNK_TEXT IS NOT NULL;
""", language="sql")
    
    # 뷰 생성 버튼
    if st.button(":material/build: 검색 뷰 생성 (Create Search View)", type="primary", use_container_width=True):
        try:
            create_view_sql = f"""
            CREATE OR REPLACE VIEW {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW AS
            SELECT 
                rc.CHUNK_ID,
                rc.CHUNK_TEXT,
                rc.FILE_NAME,
                rc.DOC_ID,
                rc.CHUNK_TYPE
            FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_CHUNKS rc
            WHERE rc.CHUNK_TEXT IS NOT NULL
            """
            session.sql(create_view_sql).collect()
            st.success(f":material/check_circle: 뷰 생성됨: `{st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW`")
        except Exception as e:
            st.error(f"뷰 생성 오류: {str(e)}")

# 2단계: Cortex Search 서비스 생성
with st.container(border=True):
    st.subheader("2단계: Cortex Search 서비스 생성 (Create the Cortex Search Service)")
    
    st.code(f"""
CREATE OR REPLACE CORTEX SEARCH SERVICE {st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH
    ON CHUNK_TEXT                        -- 텍스트 컬럼 검색
    ATTRIBUTES FILE_NAME, CHUNK_TYPE     -- 메타데이터로 반환할 컬럼
    WAREHOUSE = COMPUTE_WH               -- 웨어하우스 (본인 환경에 맞게 수정)
    TARGET_LAG = '1 hour'                -- 인덱스 갱신 주기
AS (
    SELECT 
        CHUNK_TEXT,
        FILE_NAME,
        CHUNK_TYPE,
        CHUNK_ID
    FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW
);
""", language="sql")
    
    st.info("""
    :material/lightbulb: **핵심 파라미터:**
    - **ON**: 검색할 텍스트 컬럼 (리뷰 텍스트)
    - **ATTRIBUTES**: 결과에 포함할 추가 컬럼 (파일 이름, 청크 유형)
    - **TARGET_LAG**: 인덱스 갱신 빈도
    - **WAREHOUSE**: 인덱싱을 위한 컴퓨팅 웨어하우스
    """)
    
    # 웨어하우스 선택
    warehouse = st.text_input("웨어하우스 이름 (Warehouse Name)", value="COMPUTE_WH", 
                              help="Snowflake 웨어하우스 이름을 입력하세요")
    
    # 검색 서비스 생성 버튼
    if st.button(":material/rocket_launch: 검색 서비스 생성 (Create Search Service)", type="primary", use_container_width=True):
        try:
            with st.status("Cortex Search 서비스 생성 중...", expanded=True) as status:
                st.write(":material/looks_one: 서비스 생성 중...")
                
                # [실습] Cortex Search 서비스를 생성하는 SQL을 실행하세요.
                # 힌트: CREATE OR REPLACE CORTEX SEARCH SERVICE ...
                
                create_service_sql = f"""
                CREATE OR REPLACE CORTEX SEARCH SERVICE {st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH
                    ON CHUNK_TEXT
                    ATTRIBUTES FILE_NAME, CHUNK_TYPE
                    WAREHOUSE = {warehouse}
                    TARGET_LAG = '1 hour'
                AS (
                    SELECT 
                        CHUNK_TEXT,
                        FILE_NAME,
                        CHUNK_TYPE,
                        CHUNK_ID
                    FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW
                )
                """
                
                # 여기에 코드를 작성하세요 (아래 코드를 완성하세요)
                # session.sql(create_service_sql).collect()
                
                # 실습을 위해 임시로 비워둡니다. 위 주석을 참고하여 채워보세요. 
                pass # 이 부분을 수정하세요
                
                # [실습 정답용 코드 - 학생에게 제공하지 않음 / 실제 동작을 위해 아래 코드를 사용하지만, 학생 버전에서는 가려야 합니다]
                # 여기서는 '작성용' 파일을 요청했으므로 pass만 남겨두고 주석처리합니다.
                
                # session.sql(create_service_sql).collect()

                st.write(":material/looks_two: 인덱싱 완료 대기 중...")
                st.caption("100개의 리뷰에 대해 몇 분 정도 걸릴 수 있습니다...")
                
                status.update(label=":material/check_circle: 검색 서비스 생성됨!", state="complete", expanded=False)
            
            st.success(f":material/check_circle: 생성됨: `{st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH`")
            st.session_state.search_service = f"{st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH"
            
            st.balloons()
            
        except Exception as e:
            st.error(f"검색 서비스 생성 오류: {str(e)}")
            st.info(":material/lightbulb: 다음을 확인하세요:\n- 웨어하우스 이름이 올바른지\n- CREATE CORTEX SEARCH SERVICE 권한이 있는지\n- 테이블에 리뷰 청크가 존재하는지")

# 3단계: 검색 서비스 확인
with st.container(border=True):
    st.subheader("3단계: 검색 서비스 확인 (Verify Your Search Service)")
    
    st.markdown("""
    모든 Cortex Search 서비스를 나열하여 서비스가 성공적으로 생성되었는지 확인합니다:
    """)
    
    if st.button(":material/assignment: 나의 Cortex Search 서비스 목록 보기", use_container_width=True):
        try:
            # 현재 데이터베이스/스키마의 서비스 표시 시도
            result = session.sql(f"SHOW CORTEX SEARCH SERVICES IN SCHEMA {st.session_state.day19_database}.{st.session_state.day19_schema}").collect()
            if result:
                st.success(f":material/check_circle: `{st.session_state.day19_database}.{st.session_state.day19_schema}`에서 {len(result)}개의 Cortex Search 서비스 발견:")
                st.dataframe(result, use_container_width=True)
            else:
                st.info("이 스키마에서 Cortex Search 서비스를 찾을 수 없습니다. 2단계의 버튼을 사용하여 생성하세요!")
                
                # 모든 서비스 표시 시도
                st.caption("모든 스키마 확인 중...")
                all_results = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
                if all_results:
                    st.warning(f"다른 스키마에서 {len(all_results)}개의 서비스를 찾았습니다:")
                    st.dataframe(all_results, use_container_width=True)
                
        except Exception as e:
            st.error(f"오류: {str(e)}")
            st.info(":material/lightbulb: 서비스가 방금 생성된 경우 나타나는 데 잠시 시간이 걸릴 수 있습니다. 몇 초 후에 다시 시도하세요.")

st.divider()
st.caption("Day 19: 고객 리뷰를 위한 Cortex Search 생성 (Creating Cortex Search for Customer Reviews) | 30 Days of AI")
