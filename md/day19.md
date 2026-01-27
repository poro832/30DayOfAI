오늘의 챌린지 목표는 Snowflake Cortex Search를 사용하여 고객 리뷰를 위한 시맨틱 검색 서비스를 만드는 것입니다. Cortex Search는 의미를 이해하고(단순 키워드 매칭이 아님), 데이터를 자동으로 인덱싱하며, 테이블과 동기화 상태를 유지하고, Snowflake의 보안 및 거버넌스를 상속받는 Snowflake의 관리형 시맨틱 검색 서비스입니다. 데이터베이스 설정을 구성하고, 검색 가능한 뷰를 생성하고, Cortex Search 서비스를 구축하고, 그 존재를 확인할 것입니다. 완료되면 20일차에 쿼리할 준비가 된 작동하는 검색 서비스를 갖게 됩니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 무엇을 하는지 분석해 보겠습니다.

#### 1. 데이터베이스 구성 및 세션 상태

```python
import streamlit as st
from snowflake.core import Root
import pandas as pd

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize session state for database configuration
if 'day19_database' not in st.session_state:
    if 'embeddings_database' in st.session_state:
        st.session_state.day19_database = st.session_state.embeddings_database
        st.session_state.day19_schema = st.session_state.embeddings_schema
    else:
        st.session_state.day19_database = "RAG_DB"
        st.session_state.day19_schema = "RAG_SCHEMA"

# Database Configuration UI
with st.container(border=True):
    st.subheader(":material/analytics: Database Configuration")
    
    database = st.text_input("Database", value=st.session_state.day19_database)
    schema = st.text_input("Schema", value=st.session_state.day19_schema)
    table_name = st.text_input("Source Table", value="REVIEW_CHUNKS")
```

* **자동 감지**: 18일차의 임베딩을 사용할 수 있는 경우 데이터베이스와 스키마를 자동으로 감지합니다.
* **기본값**: 18일차 데이터를 찾을 수 없는 경우 `RAG_DB.RAG_SCHEMA`를 사용합니다.
* **세션 상태 지속성**: 앱 전체에서 사용할 구성을 저장합니다.
* **테두리가 있는 컨테이너**: 데이터베이스 구성 입력을 깔끔하고 정리된 인터페이스로 그룹화합니다.
* **소스 테이블**: 청크 텍스트와 메타데이터가 있는 17일차의 `REVIEW_CHUNKS` 테이블을 예상합니다.

#### 2. Cortex Search란 무엇인가요?

**Cortex Search**는 다음과 같은 기능을 제공하는 Snowflake의 관리형 시맨틱 검색 서비스입니다:

- :material/psychology: 단순 키워드가 아닌 **의미 이해**
- :material/flash_on: 데이터 **자동 인덱싱**
- :material/sync: 테이블과 **동기화 유지**
- 🔐 **Snowflake 보안** 및 거버넌스 상속

**고객 리뷰의 예:**
- "warm gloves" 검색 → "toasty hands", "cold fingers"를 언급한 리뷰를 찾음
- "durability issues" 검색 → "broke after 2 weeks", "lasted 3 seasons"를 찾음
- "comfortable helmet" 검색 → "all-day wear", "no pressure points"를 찾음

**수동 방식보다 Cortex Search를 사용하는 이유는 무엇인가요?**

| 수동 방식 | Cortex Search |
|-----------------|---------------|
| 임베딩 직접 생성 | :material/check_circle: 18일차에 이미 완료됨 |
| 수동 인덱싱 | :material/check_circle: 자동 인덱싱 |
| 수동 동기화 | :material/check_circle: 자동 새로 고침 |
| 유사도 검색 구축 | :material/check_circle: 내장된 시맨틱 검색 |
| 인프라 관리 | :material/check_circle: 완전 관리형 |

#### 3. 검색 뷰 생성

```python
if st.button(":material/build: Create Search View", type="primary"):
    create_view_sql = f"""
    CREATE OR REPLACE VIEW {database}.{schema}.REVIEW_SEARCH_VIEW AS
    SELECT 
        rc.CHUNK_ID,
        rc.CHUNK_TEXT,
        rc.FILE_NAME,
        rc.DOC_ID,
        rc.CHUNK_TYPE
    FROM {database}.{schema}.REVIEW_CHUNKS rc
    WHERE rc.CHUNK_TEXT IS NOT NULL
    """
    session.sql(create_view_sql).collect()
    st.success(f":material/check_circle: Created view: `{database}.{schema}.REVIEW_SEARCH_VIEW`")
```

* **`CREATE OR REPLACE VIEW`**: 청크 텍스트와 메타데이터를 결합하는 뷰를 생성합니다. 뷰는 기본 테이블이 변경될 때 자동으로 업데이트됩니다.
* **`WHERE rc.CHUNK_TEXT IS NOT NULL`**: 인덱싱 오류를 방지하기 위해 텍스트가 없는 청크를 필터링합니다.
* **왜 뷰를 사용하나요?**: Cortex Search 서비스는 테이블이 아닌 뷰를 쿼리합니다. 이는 여러 테이블을 조인하거나 필터링 로직을 추가할 수 있는 유연성을 제공합니다.
* **테두리가 있는 컨테이너**: 버튼과 SQL 코드는 테두리가 있는 컨테이너(앱의 단계 1)에 그룹화됩니다.

#### 4. Cortex Search 서비스 생성

```python
warehouse = st.text_input("Warehouse Name", value="COMPUTE_WH", 
                          help="Enter your Snowflake warehouse name")

if st.button(":material/rocket_launch: Create Search Service", type="primary"):
    with st.status("Creating Cortex Search Service...", expanded=True) as status:
        st.write(":material/looks_one: Creating service...")
        create_service_sql = f"""
        CREATE OR REPLACE CORTEX SEARCH SERVICE {database}.{schema}.CUSTOMER_REVIEW_SEARCH
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
            FROM {database}.{schema}.REVIEW_SEARCH_VIEW
        )
        """
        session.sql(create_service_sql).collect()
        
        st.write(":material/looks_two: Waiting for indexing to complete...")
        st.caption("This may take a few minutes for 100 reviews...")
        
        status.update(label=":material/check_circle: Search service created!", state="complete", expanded=False)
    
    st.session_state.search_service = f"{database}.{schema}.CUSTOMER_REVIEW_SEARCH"
    st.balloons()
```

* **웨어하우스 입력**: 검색 서비스는 인덱싱을 위해 웨어하우스가 필요합니다. 사용자는 여기에 웨어하우스 이름을 입력합니다.
* **`ON CHUNK_TEXT`**: 검색 가능한 텍스트가 포함된 열을 지정합니다. 이것이 사용자가 검색할 대상입니다.
* **`ATTRIBUTES FILE_NAME, CHUNK_TYPE`**: 컨텍스트 및 필터링을 위해 검색 결과에 포함할 추가 열입니다.
* **`TARGET_LAG = '1 hour'`**: 새 데이터를 포함하기 위해 인덱스가 새로 고쳐지는 빈도입니다. 이 예제에서는 1시간으로 설정합니다.
* **`st.status(...)`**: 생성 단계를 통한 진행 상황을 보여주는 확장 가능한 상태 표시기를 생성합니다.
* **인덱싱 시간**: 생성 후 Snowflake는 100개의 리뷰 청크를 인덱싱하는 데 1-2분이 필요합니다. 서비스는 즉시 존재하지만 인덱싱이 완료될 때까지 검색할 수 없습니다.
* **`st.balloons()`**: 서비스가 성공적으로 생성되었을 때 축하 애니메이션을 보여줍니다.
* **테두리가 있는 컨테이너**: 전체 서비스 생성 인터페이스는 테두리가 있는 컨테이너(앱의 단계 2)에 그룹화됩니다.

#### 5. 검색 서비스 확인

```python
if st.button(":material/assignment: List My Cortex Search Services"):
    try:
        result = session.sql(f"SHOW CORTEX SEARCH SERVICES IN SCHEMA {database}.{schema}").collect()
        if result:
            st.success(f":material/check_circle: Found {len(result)} Cortex Search service(s) in `{database}.{schema}`:")
            st.dataframe(result, use_container_width=True)
        else:
            st.info("No Cortex Search services found. Create one in Step 2!")
    except Exception as e:
        st.error(f"Error: {str(e)}")
```

* **`SHOW CORTEX SEARCH SERVICES`**: 지정된 스키마의 모든 검색 서비스를 나열합니다.
* **확인**: 서비스가 생성되었는지 확인하고 상태(INDEXING 또는 READY)를 보여줍니다.
* **상태 열**: 검색하기 전에 서비스가 "READY"로 표시되는지 확인하세요. "INDEXING"으로 표시되면 몇 분 기다리세요.
* **20일차와의 통합**: 서비스가 확인되고 준비되면 Python API를 사용하여 쿼리하는 방법을 배우는 20일차로 진행할 수 있습니다.
* **테두리가 있는 컨테이너**: 확인 인터페이스는 테두리가 있는 컨테이너(앱의 단계 3)에 그룹화됩니다.

이 코드가 실행되면 사용할 준비가 된 Cortex Search 서비스를 생성하고 확인하게 됩니다. 이 서비스는 고객 리뷰 청크를 인덱싱하고 단순한 키워드가 아닌 의미를 기반으로 검색 가능하게 만듭니다. Cortex Search는 단순한 키워드가 아닌 의미를 이해합니다. 예를 들어 "warm gloves"를 검색하면 정확한 단어가 없더라도 "toasty hands" 또는 "cold fingers"를 언급한 리뷰를 찾을 수 있습니다. 20일차에서는 이 서비스를 쿼리하여 관련 리뷰를 찾는 방법을 배웁니다.

---

### :material/library_books: 리소스
- [Cortex Search 문서](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Python API: snowflake.core](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/api/snowflake.core)
- [CREATE CORTEX SEARCH SERVICE](https://docs.snowflake.com/en/sql-reference/sql/create-cortex-search-service)
