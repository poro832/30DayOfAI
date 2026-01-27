# Creating Cortex Search for Customer Reviews (고객 리뷰를 위한 Cortex Search 생성)

# 0. 목표

<aside>
💡

**Day 16-18에서 준비한 데이터로 Cortex Search 서비스 생성**

1. 리뷰 청크의 검색 가능한 뷰 생성
2. Snowflake Cortex Search 서비스 생성
3. 검색 서비스 확인 및 Day 20에서 사용할 준비 완료

</aside>

# 1. 개요 및 필요성 (Overview)

- **Cortex Search**는 Snowflake에서 제공하는 의미 기반 검색 서비스입니다.
- 전통적인 키워드 검색과 달리, 의미를 이해하여 관련 문서를 찾습니다.
- RAG 파이프라인의 **네 번째 단계**로, 검색 인프라를 구축합니다.

## Cortex Search vs 전통적 검색

- **키워드 검색**: "따뜻한 장갑" → "따뜻한", "장갑" 키워드 포함 문서만 찾음
- **Cortex Search**: "따뜻한 장갑" → "손을 포근하게", "추위를 막아줌", "보온성" 등 의미적으로 유사한 모든 리뷰 찾음

# 2. Streamlit 앱 구현 (Implementation)

## 2-1. 데이터베이스 구성

```python
import streamlit as st
from snowflake.core import Root
import pandas as pd

# Snowflake 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Day 18의 임베딩 확인
if 'day19_database' not in st.session_state:
    if 'embeddings_database' in st.session_state:
        st.session_state.day19_database = st.session_state.embeddings_database
        st.session_state.day19_schema = st.session_state.embeddings_schema
    else:
        st.session_state.day19_database = "RAG_DB"
        st.session_state.day19_schema = "RAG_SCHEMA"
```

- Day 18의 `embeddings_database`와 `embeddings_schema`를 자동으로 감지
- 사용자가 데이터베이스와 스키마를 직접 입력할 수도 있음

## 2-2. 1단계: 데이터 뷰 준비

```python
# 뷰 생성 버튼
if st.button(":material/build: Create Search View", type="primary"):
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
    st.success(f":material/check_circle: Created view: REVIEW_SEARCH_VIEW")
```

- 검색 가능한 뷰 생성: 리뷰 청크와 메타데이터 결합
- `WHERE rc.CHUNK_TEXT IS NOT NULL`: 빈 텍스트가 있는 청크 제외
- `CREATE OR REPLACE`: 이미 존재하면 업데이트

## 2-3. 2단계: Cortex Search 서비스 생성

```python
# 웨어하우스 선택
warehouse = st.text_input("Warehouse Name", value="COMPUTE_WH", 
                          help="Enter your Snowflake warehouse name")

# 검색 서비스 생성 버튼
if st.button(":material/rocket_launch: Create Search Service", type="primary"):
    create_service_sql = f"""
    CREATE OR REPLACE CORTEX SEARCH SERVICE {st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH
        ON CHUNK_TEXT                        -- 리뷰 텍스트에서 검색
        ATTRIBUTES FILE_NAME, CHUNK_TYPE     -- 메타데이터로 반환
        WAREHOUSE = {warehouse}              -- 인덱싱에 사용할 웨어하우스
        TARGET_LAG = '1 hour'                -- 갱신 빈도
    AS (
        SELECT CHUNK_TEXT, FILE_NAME, CHUNK_TYPE, CHUNK_ID
        FROM {st.session_state.day19_database}.{st.session_state.day19_schema}.REVIEW_SEARCH_VIEW
    )
    """
    session.sql(create_service_sql).collect()
    
    st.success(f":material/check_circle: Created: CUSTOMER_REVIEW_SEARCH")
    st.session_state.search_service = f"{st.session_state.day19_database}.{st.session_state.day19_schema}.CUSTOMER_REVIEW_SEARCH"
```

### 주요 파라미터 설명

- **ON CHUNK_TEXT**: 검색 가능하게 만들 텍스트 컬럼 (리뷰 텍스트)
- **ATTRIBUTES FILE_NAME, CHUNK_TYPE**: 결과에 포함할 추가 컬럼 (파일명, 청크 타입)
- **WAREHOUSE**: 인덱싱을 위한 컴퓨팅 웨어하우스
- **TARGET_LAG**: 인덱스 갱신 빈도 (1시간마다 새 데이터 반영)

## 2-4. 3단계: 검색 서비스 확인

```python
if st.button(":material/assignment: List My Cortex Search Services"):
    # 현재 데이터베이스/스키마의 서비스 표시 시도
    result = session.sql(f"SHOW CORTEX SEARCH SERVICES IN SCHEMA {st.session_state.day19_database}.{st.session_state.day19_schema}").collect()
    
    if result:
        st.success(f":material/check_circle: Found {len(result)} Cortex Search service(s)")
        st.dataframe(result, use_container_width=True)
    else:
        st.info("No Cortex Search services found in this schema.")
        
        # 모든 서비스 표시 시도
        all_results = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
        if all_results:
            st.warning(f"Found {len(all_results)} service(s) in other schemas:")
            st.dataframe(all_results, use_container_width=True)
```

- 현재 스키마의 모든 Cortex Search 서비스 나열
- 서비스가 생성되었는지 확인
- 다른 스키마의 서비스도 확인 가능

# 3. 핵심 포인트 및 고려사항

## 검색 서비스 구조

```sql
CREATE CORTEX SEARCH SERVICE service_name
    ON text_column              -- 검색할 텍스트
    ATTRIBUTES metadata_columns -- 반환할 메타데이터
    WAREHOUSE = warehouse_name
    TARGET_LAG = '1 hour'
AS (SELECT query)
```

## 인덱싱 시간

- 100개 리뷰의 경우 몇 분 정도 소요
- 인덱싱이 완료되어야 검색 가능
- `TARGET_LAG`으로 자동 갱신 주기 설정

## Day 20과의 통합

```python
st.session_state.search_service = f"{database}.{schema}.CUSTOMER_REVIEW_SEARCH"
```

- Day 20이 이 검색 서비스를 사용하여 리뷰 검색

## 권한 요구사항

- `CREATE CORTEX SEARCH SERVICE` 권한 필요
- 웨어하우스 사용 권한 필요
- 스키마에 대한 CREATE 권한 필요

# 실행 결과

## 실행 코드

Streamlit 실행 코드 = python -m streamlit run 파일명.py

예시 : `python -m streamlit run app/day19.py`

## 결과

- `REVIEW_SEARCH_VIEW` 뷰 생성됨
- `CUSTOMER_REVIEW_SEARCH` 서비스 생성됨
- 100개 리뷰에 대한 의미 기반 검색 준비 완료
- Day 20에서 "따뜻한 장갑" 검색 시 관련 리뷰 찾기 가능
