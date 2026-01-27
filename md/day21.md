이번 챌린지에서는 Cortex Search를 사용하여 완전한 RAG(Retrieval-Augmented Generation) 파이프라인을 구축하는 작업을 수행합니다. 관련 문서를 검색하고 이를 LLM 기반 답변의 문맥(context)으로 사용합니다. 앱은 3단계 RAG 프로세스를 보여주는 시각적 가이드를 표시한 다음, 질문을 하고 근거 있는 답변을 볼 수 있는 인터페이스를 제공합니다.

> :material/warning: **전제 조건:** 이 강의를 실행하기 전에 Cortex Search 서비스가 필요합니다. 아직 생성하지 않았다면 **Day 19**의 설정을 참조하세요. 서비스는 사이드바 드롭다운에 자동으로 나타납니다.

---

### :material/settings: 작동 방식: 단계별 설명

#### 1. 시각적 RAG 가이드

```python
st.subheader(":material/menu_book: How RAG Works")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("**:material/looks_one: Retrieve**")
        st.markdown("Cortex Search finds relevant document chunks based on your question.")

with col2:
    with st.container(border=True):
        st.markdown("**:material/looks_two: Augment**")
        st.markdown("Retrieved chunks are added to the prompt as context for the LLM.")

with col3:
    with st.container(border=True):
        st.markdown("**:material/looks_3: Generate**")
        st.markdown("The LLM generates an answer grounded in the retrieved documents.")
```

* **3개 컬럼 레이아웃**: 사용자가 앱과 상호 작용하기 전에 RAG 파이프라인을 시각적으로 보여줍니다.
* **테두리가 있는 컨테이너**: 각 단계를 자체 컨테이너에 담아 명확하게 구분합니다.
* **교육적 문맥**: 사용자가 "Search & Answer"를 클릭할 때 어떤 일이 일어날지 이해하도록 돕습니다.

#### 2. 스마트한 서비스 선택

```python
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

# Selectbox with manual option
search_service = st.selectbox("Search Service:", options=available_services)
```

* **명시적 기본값**: Day 19의 기본 서비스 이름을 `RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH`로 설정합니다.
* **자동 감지**: 계정 내의 모든 사용 가능한 Cortex Search 서비스를 찾도록 Snowflake에 쿼리합니다.
* **기본값 항상 최상단**: 기본 서비스가 항상 인덱스 0(기본 선택)에 오도록 보장합니다.
* **드롭다운 선택**: 선택 박스에 모든 사용 가능한 서비스를 보여줍니다.
* **수동 입력 옵션**: 필요한 경우 사용자가 커스텀 서비스 경로를 입력할 수도 있습니다.

#### 3. Cortex Search를 사용한 검색

```python
from snowflake.core import Root

root = Root(session)
parts = search_service.split(".")

svc = (root
    .databases[parts[0]]
    .schemas[parts[1]]
    .cortex_search_services[parts[2]])

search_results = svc.search(
    query=question,
    columns=["CHUNK_TEXT", "FILE_NAME"],
    limit=num_chunks
)

# Extract context with metadata
context_chunks = []
sources = []
for item in search_results.results:
    context_chunks.append(item.get("CHUNK_TEXT", ""))
    sources.append(item.get("FILE_NAME", "Unknown"))

context = "\n\n---\n\n".join(context_chunks)
```

* **동적 서비스 경로**: 서비스 경로를 나누고 Snowflake 계층 구조를 탐색합니다.
* **메타데이터 추출**: 소스 속성 표기를 위해 청크 텍스트와 파일명을 모두 캡처합니다.
* **구성 가능한 제한**: 사이드바의 `num_chunks` 슬라이더 값을 사용합니다.
* **문맥 조립**: 명확한 문맥 블록을 만들기 위해 청크를 구분 기호와 함께 조인합니다.

#### 4. RAG 프롬프트

```python
rag_prompt = f"""You are a helpful assistant. Answer based ONLY on the provided context.
If the context doesn't contain enough information, say so.

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}

Provide a clear, accurate answer based on the context."""
```

* **지시사항(Instruction)**: LLM에게 제공된 문맥만 사용하도록 지시합니다.
* **근거 강화(Grounding)**: 정보가 없는 경우 솔직하게 말하도록 지시합니다.
* **명확한 구분**: 문맥과 질문이 명확하게 라벨링되어 있습니다.

#### 5. Cortex LLM으로 생성

```python
with st.status("Processing...", expanded=True) as status:
    st.write(":material/search: **Step 1:** Searching documents...")
    # ... search code ...
    st.write(f"   :material/check_circle: Found {len(context_chunks)} relevant chunks")
    
    st.write(":material/smart_toy: **Step 2:** Generating answer...")
    
    response_sql = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{model}',
        '{rag_prompt.replace("'", "''")}'
    ) as response
    """
    
    response = session.sql(response_sql).collect()[0][0]
    
    st.write("   :material/check_circle: Answer generated")
    status.update(label="Complete!", state="complete", expanded=True)
```

* **`st.status(...)`**: 두 단계를 통한 진행 상황을 보여주는 확장 가능한 상태 표시기를 생성합니다.
* **`expanded=True`**: 완료 후에도 상태 컨테이너를 열어두어 사용자가 어떤 일이 일어났는지 확인할 수 있게 합니다.
* **단계별 피드백**: 체크표시와 함께 "Searching documents..."에 이어 "Generating answer..."를 보여줍니다.
* **SQL 이스케이프**: 프롬프트(검색된 텍스트 포함) 내의 작은따옴표를 이스케이프하기 위해 `.replace("'", "''")`를 사용합니다.
* **모델 선택**: 사이드바에서 선택한 모델(claude-3-5-sonnet, mistral-large, 또는 llama3.1-8b)을 사용합니다.

> :material/lightbulb: **왜 여기서 SQL `COMPLETE`를 사용할까요?** RAG 애플리케이션의 경우 Python `Complete()` API 대신 SQL `SNOWFLAKE.CORTEX.COMPLETE()` 함수를 사용합니다. 이 방식은 검색된 문서에서 프롬프트에 특수 문자가 포함된 경우(SQL을 통한 이스케이프가 더 쉬움) 더 잘 작동합니다.

#### 6. 소스 속성 표시와 함께 결과 표시

```python
st.subheader(":material/lightbulb: Answer")
with st.container(border=True):
    st.markdown(response)

if show_context:
    st.subheader(":material/library_books: Retrieved Context")
    st.caption(f"Used {len(context_chunks)} chunks from customer reviews")
    for i, (chunk, source) in enumerate(zip(context_chunks, sources), 1):
        with st.expander(f":material/description: Chunk {i} - {source}"):
            st.write(chunk)
```

* **답변 표시**: 테두리가 있는 컨테이너에 LLM 응답을 보여줍니다.
* **선택적 문맥 뷰어**: 사이드바에서 "Show retrieved context"를 선택한 경우 모든 청크를 표시합니다.
* **소스 속성 표시(Source attribution)**: 각 청크는 파일명을 보여주므로 정보의 출처를 사용자가 알 수 있습니다.
* **익스팬더(Expanders)**: 인터페이스를 깔끔하게 유지하기 위해 청크는 기본적으로 접혀 있습니다.

#### 7. RAG가 일반 LLM보다 나은 이유

| Plain LLM | RAG with Cortex Search |
|-----------|----------------------|
| 학습 데이터 사용 | 사용자 본인의 문서 사용 |
| 할루시네이션(환각) 가능성 있음 | 실제 콘텐츠에 근거함 |
| 지식 컷오프(제한) 존재 | 항상 최신 데이터 반영 |
| 일반적인 답변 제공 | 사용자의 문맥에 특화된 답변 |

#### 8. RAG 품질 튜닝

| 매개변수 | 효과 |
|-----------|--------|
| 더 많은 청크 | 더 많은 문맥 제공, 관련성이 희석될 수 있음 |
| 더 적은 청크 | 더 집중된 문맥, 정보를 놓칠 수 있음 |
| 더 나은 질문 | 더 나은 검색 결과 도출 |
| 명확한 프롬프트 | 더 나은 답변 품질 도출 |

* **`num_chunks` 슬라이더**: 사이드바에서 검색할 문맥 청크 수(1-10, 기본값 3)를 제어합니다.
* **모델 선택**: 모델마다 강점이 다릅니다(품질을 위한 claude-3-5-sonnet, 속도를 위한 llama3.1-8b).
* **문맥 보기 토글**: LLM에 어떤 문맥이 정확히 전송되었는지 보여줌으로써 디버깅을 돕습니다.

이 앱이 실행되면 Cortex Search에서 관련 문서를 검색하고, 과정을 단계별로 시각화하며, 소스 근거와 함께 답변을 생성하는 작동하는 RAG 시스템을 갖게 됩니다. 상단의 시각적 가이드는 사용자가 파이프라인과 상호 작용하기 전에 RAG 파이프라인을 이해하도록 도와줍니다.

---

### :material/library_books: 리소스
- [Cortex Search for RAG](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Cortex Complete Function](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [RAG with Cortex Search Quickstart](https://www.snowflake.com/en/developers/guides/ask-questions-to-your-own-documents-with-snowflake-cortex-search/)
