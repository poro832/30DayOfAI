이번 챌린지에서는 Day 19에서 생성한 Cortex Search 서비스를 쿼리하여 관련 있는 고객 리뷰를 찾는 작업을 수행합니다. Python SDK를 사용하여 시맨틱 검색을 수행하고, 단순한 키워드가 아닌 의미에 기반하여 관련 문서를 검색하며, 그 결과를 깔끔한 인터페이스에 표시해야 합니다. 이 작업이 완료되면 자연어 쿼리를 이해하는 작동하는 문서 검색 기능을 갖게 됩니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 어떤 역할을 하는지 살펴보겠습니다.

#### 1. 라이브러리 임포트 및 연결 설정

```python
import streamlit as st
from snowflake.core import Root

st.title(":material/search: Querying Cortex Search")
st.write("Search and retrieve relevant text chunks using Cortex Search Service.")

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()
```

* **`from snowflake.core import Root`**: Cortex Search 서비스에 액세스하기 위한 Python API를 임포트합니다. 이는 SQL 문자열을 사용하는 것보다 훨씬 깔끔합니다.
* **`st.title(...)`**: 시각적 효과를 위해 이모지 아이콘과 함께 페이지 제목을 설정합니다.
* **`try/except` 블록**: 환경을 자동으로 감지하고 적절하게 연결합니다(SiS vs 로컬/커뮤니티 클라우드).
* **`session`**: 검색 서비스를 쿼리하는 데 사용할 설정된 Snowflake 연결입니다.

#### 2. 입력 컨테이너: 서비스 구성

```python
with st.container(border=True):
    st.subheader(":material/search: Search Configuration and Query")
    
    # Default search service from Day 19
    default_service = 'RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH'
    
    # Try to get available services
    try:
        services_result = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
        available_services = [f"{row['database_name']}.{row['schema_name']}.{row['name']}" 
                            for row in services_result] if services_result else []
    except:
        available_services = []
    
    # Ensure default service is always first
    if default_service in available_services:
        available_services.remove(default_service)
    available_services.insert(0, default_service)
```

* **테두리가 있는 컨테이너**: 더 나은 구성을 위해 모든 입력 요소를 함께 그룹화합니다.
* **`default_service`**: Day 19에서 생성한 기본 서비스 이름을 `RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH`로 명시적으로 설정합니다.
* **`SHOW CORTEX SEARCH SERVICES`**: 계정에서 사용 가능한 모든 검색 서비스를 나열하도록 Snowflake에 쿼리합니다.
* **리스트 컴프리헨션**: 발견된 각 서비스에 대해 `database.schema.service_name` 형식으로 서비스 경로 리스트를 빌드합니다.
* **기본 서비스를 최상단에**: 리스트에 기본 서비스가 있으면 제거한 다음 인덱스 0에 삽입하여 항상 첫 번째 옵션이 되도록 합니다.
* **Try/except**: 쿼리가 실패하는 경우(서비스가 존재하지 않음) 빈 리스트를 설정합니다.

#### 3. 스마트한 서비스 선택

```python
# Add manual entry option
if available_services:
    available_services.append("-- Enter manually --")
    
    search_service_option = st.selectbox(
        "Search Service:",
        options=available_services,
        index=0,
        help="Select your Cortex Search service from Day 19"
    )
    
    # If manual entry selected, show text input
    if search_service_option == "-- Enter manually --":
        search_service = st.text_input(
            "Enter service path:",
            placeholder="database.schema.service_name"
        )
    else:
        search_service = search_service_option
        
        # Show status if this is the Day 19 service
        if search_service == st.session_state.get('search_service'):
            st.success(":material/check_circle: Using service from Day 19")
else:
    # Fallback to text input if no services found
    search_service = st.text_input(
        "Search Service:",
        value=default_service,
        placeholder="database.schema.service_name",
        help="Full path to your Cortex Search service"
    )

st.code(search_service, language="sql")
st.caption(":material/lightbulb: This should point to your CUSTOMER_REVIEW_SEARCH service from Day 19")
```

* **수동 입력 옵션이 있는 선택 박스**: 서비스를 찾은 경우 드롭다운 메뉴를 생성합니다. 커스텀 경로를 위해 마지막 옵션으로 "-- Enter manually --"를 추가합니다.
* **`index=0`**: 기본 서비스(`RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH`)를 기본 선택으로 설정합니다.
* **`help` 매개변수**: 이것이 Day 19의 서비스여야 함을 설명하는 툴팁을 추가합니다.
* **조건부 입력**: "Enter manually"가 선택된 경우 텍스트 입력란을 보여줍니다. 그렇지 않으면 선택된 서비스를 사용합니다.
* **상태 표시기**: 선택된 서비스가 세션 상태에 저장된 Day 19의 서비스와 일치하면 초록색 성공 메시지를 보여줍니다.
* **대체 방법(Fallback)**: 서비스를 찾지 못한 경우 기본 경로가 미리 채워진 텍스트 입력란만 보여줍니다.
* **`st.code(...)`**: 명확성을 위해 전체 서비스 경로를 코드 블록에 표시합니다.
* **캡션(Caption)**: 이것이 `CUSTOMER_REVIEW_SEARCH` 서비스를 가리켜야 함을 다시 한번 상기시켜 줍니다.

#### 4. 검색 쿼리 입력

```python
st.divider()

# Search query input
query = st.text_input(
    "Enter your search query:",
    value="warm thermal gloves",
    placeholder="e.g., durability issues, comfortable helmet"
)

num_results = st.slider("Number of results:", 1, 20, 5)

search_clicked = st.button(":material/search: Search", type="primary", use_container_width=True)
```

* **`st.divider()`**: 서비스 구성 섹션과 쿼리 입력 섹션 사이에 시각적 구분선을 만듭니다.
* **텍스트 입력**: 사용자에게 어떤 종류의 입력을 제공해야 하는지 보여주기 위해 기본 쿼리("warm thermal gloves")가 있는 검색 상자를 생성합니다.
* **`placeholder`**: 입력란이 비어 있을 때 예시 쿼리를 보여주어 사용자에게 검색 아이디어를 제공합니다.
* **슬라이더**: 반환할 결과 수(1-20, 기본값 5)를 사용자가 제어할 수 있게 합니다.
* **검색 버튼**: 검색을 트리거하는 전체 너비의 기본 버튼입니다. 클릭 상태를 `search_clicked`에 저장하여 출력 컨테이너에서 사용합니다.

#### 5. 출력 컨테이너: 초기화 및 버튼 클릭 확인

```python
with st.container(border=True):
    st.subheader(":material/analytics: Search Results")
    
    if search_clicked:
        if query and search_service:
            try:
                root = Root(session)
                parts = search_service.split(".")
                
                if len(parts) != 3:
                    st.error("Service path must be in format: database.schema.service_name")
```

* **별도의 테두리가 있는 컨테이너**: 출력을 입력과 시각적으로 구별되도록 자체 컨테이너에 담습니다.
* **`if search_clicked:`**: 버튼을 클릭했을 때만 검색 로직을 실행합니다.
* **`if query and search_service:`**: 두 필수 필드가 모두 채워졌는지 검증합니다.
* **`Root(session)`**: Python API를 위한 엔트리 포인트를 생성합니다.
* **`.split(".")`**: 전체 경로를 데이터베이스, 스키마 및 서비스 이름으로 나눕니다.
* **검증**: 경로가 정확히 3개 부분으로 구성되어 있는지 확인합니다.

#### 6. 시맨틱 검색 실행

```python
if len(parts) != 3:
    st.error("Service path must be in format: database.schema.service_name")
else:
    svc = (root
        .databases[parts[0]]
        .schemas[parts[1]]
        .cortex_search_services[parts[2]])
    
    with st.spinner("Searching..."):
        results = svc.search(
            query=query,
            columns=["CHUNK_TEXT", "FILE_NAME", "CHUNK_TYPE", "CHUNK_ID"],
            limit=num_results
        )
    
    st.success(f":material/check_circle: Found {len(results.results)} result(s)!")
```

* **딕셔너리 스타일 탐색**: `[parts[0]]`, `[parts[1]]`, `[parts[2]]`를 사용하여 Snowflake 계층 구조를 탐색합니다.
* **`else` 블록**: 경로 검증을 통과한 경우에만 검색을 실행합니다.
* **`svc.search(...)`**: Python API를 사용한 핵심 검색 호출입니다.
* **`query`**: 사용자가 입력한 자연어 검색 쿼리입니다.
* **`columns`**: 반환할 필드(청크 텍스트, 파일명, 청크 유형, 청크 ID)를 지정합니다.
* **`limit`**: 슬라이더로 제어되는 최대 결과 수입니다.
* **`st.spinner(...)`**: 검색하는 동안 애니메이션 로딩 표시기를 보여줍니다.
* **성공 메시지**: 몇 개의 결과를 찾았는지 보여줍니다.

#### 7. 검색 결과 표시

```python
# Display results
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
        
        # Show relevance score if available
        if hasattr(item, 'score') or 'score' in item:
            score = item.get('score', item.score if hasattr(item, 'score') else None)
            if score is not None:
                st.caption(f"Relevance Score: {score:.4f}")
```

* **`enumerate(results.results, 1)`**: "Result 1", "Result 2" 등과 같이 나타내기 위해 카운터를 1부터 시작하여 결과 리스트를 루프합니다.
* **테두리가 있는 컨테이너**: 각 결과를 눈에 보이는 테두리가 있는 자체 컨테이너에 표시합니다.
* **3개 컬럼 레이아웃**: 첫 번째 컬럼(너비 2)은 결과 번호와 파일명을 보여줍니다. 두 번째와 세 번째 컬럼(각 너비 1)은 청크 유형과 ID를 보여줍니다.
* **`.get('FILE_NAME', 'N/A')`**: 값을 안전하게 가져옵니다. 필드가 없으면 "N/A"를 보여줍니다.
* **전체 텍스트 표시**: 메타데이터 아래에 전체 청크 텍스트를 보여줍니다.
* **관련성 점수**: 가능한 경우 시맨틱 유사성 점수(거리가 짧을수록 관련성이 높음)를 표시합니다.
* **자동 랭킹**: 결과는 관련성에 따라 정렬됩니다(쿼리와 가장 유사한 결과가 먼저 나타남).

#### 8. 오류 처리 및 빈 상태 관리

```python
except Exception as e:
    st.error(f"Error: {str(e)}")
    st.info(":material/lightbulb: **Troubleshooting:**\n- Make sure the search service exists (check Day 19)\n- Verify the service has finished indexing\n- Check that you have access permissions")
else:
    st.warning(":material/warning: Please enter a query and configure a search service.")
    st.info(":material/lightbulb: **Need a search service?**\n- Complete Day 19 to create `CUSTOMER_REVIEW_SEARCH`\n- The service will automatically appear in the dropdown above")
else:
    st.info(":material/arrow_upward: Configure your search service and enter a query above, then click Search to see results.")
```

* **예외 처리**: 검색 과정 중 발생하는 오류를 잡아내어 표시합니다.
* **문제 해결 팁**: 일반적인 문제(서비스가 존재하지 않음, 인덱싱 미완료, 권한 문제)에 대한 유용한 지침을 제공합니다.
* **경고 메시지**: 쿼리나 서비스가 누락된 경우 두 가지를 모두 구성하도록 사용자에게 상기시켜 줍니다.
* **유용한 정보**: 필요한 검색 서비스를 생성하기 위해 Day 19를 안내합니다.
* **빈 상태**: 검색이 아직 수행되지 않았을 때 입력 컨테이너를 안내하는 유용한 메시지를 보여줍니다.

이 코드가 실행되면 자연어 쿼리를 기반으로 관련 있는 고객 리뷰를 찾을 수 있는 시맨틱 검색 인터페이스를 갖게 됩니다. 사용자가 검색한 정확한 단어를 사용하지 않았더라도 "durability problems"를 검색하여 "broke after 2 weeks"나 "lasted 3 seasons"와 같은 내용이 포함된 리뷰를 어떻게 찾아내는지 확인해 보세요.

---

### :material/library_books: 리소스
- [Cortex Search Python SDK](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search#querying-a-cortex-search-service)
- [Python API: snowflake.core](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/api/snowflake.core)
- [Semantic Search Guide](https://www.snowflake.com/en/developers/guides/ask-questions-to-your-own-documents-with-snowflake-cortex-search/)
