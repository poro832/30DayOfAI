이번 챌린지에서는 사용자가 본인의 문서와 대화할 수 있는 완전한 대화형 RAG 챗봇을 구축하는 작업을 수행합니다. 단일 질문/답변 패턴이었던 Day 21과 달리, Day 22는 전체 대화 히스토리를 유지하여 후속 질문과 맥락 있는 대화가 가능합니다. 이 앱은 메시지 히스토리가 있는 채팅 인터페이스, 각 질문에 대한 시맨틱 검색, 검색된 문맥을 사용한 근거 있는 답변, 확장 가능한 소스 속성 표시, 그리고 히스토리 지우기 기능을 갖추고 있습니다.

> :material/warning: **전제 조건:** 이 강의를 실행하기 전에 Cortex Search 서비스가 필요합니다. 아직 생성하지 않았다면 **Day 19**의 설정을 참조하세요. 서비스는 사이드바 드롭다운에 자동으로 나타납니다.

---

### :material/settings: 작동 방식: 단계별 설명

코드의 각 부분이 어떤 역할을 하는지 살펴보겠습니다.

#### 1. 대화 상태 초기화

```python
import streamlit as st

st.title(":material/chat: Chat with Your Documents")
st.write("A conversational RAG chatbot powered by Cortex Search.")

# Connect to Snowflake
try:
    # Works in Streamlit in Snowflake
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    # Works locally and on Streamlit Community Cloud
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# Initialize state
if "doc_messages" not in st.session_state:
    st.session_state.doc_messages = []
```

* **`st.session_state.doc_messages`**: 전체 대화 히스토리(사용자 질문 및 어시스턴트 응답)를 저장합니다.
* **초기화 확인**: 리스트가 존재하지 않는 경우에만 생성하여, 재실행 시에도 히스토리가 유지되도록 합니다.
* **지속적인 히스토리**: 이것이 Day 21과의 핵심적인 차이점입니다 - 상호 작용 전반에 걸쳐 대화가 보존됩니다.

#### 2. 사이드바의 스마트한 서비스 선택

```python
with st.sidebar:
    st.header(":material/settings: Settings")
    
    # Check for search service from Day 19
    default_service = st.session_state.get('search_service', 'RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH')
    
    # Try to get available services
    try:
        services_result = session.sql("SHOW CORTEX SEARCH SERVICES").collect()
        available_services = [f"{row['database_name']}.{row['schema_name']}.{row['name']}" 
                            for row in services_result] if services_result else []
    except:
        available_services = []
    
    # Ensure default service is always first in the list
    if default_service:
        # Remove it if it exists elsewhere in the list
        if default_service in available_services:
            available_services.remove(default_service)
        # Add it at the beginning
        available_services.insert(0, default_service)
    
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
                st.caption(":material/check_circle: Using service from Day 19")
    else:
        # Fallback to text input if no services found
        search_service = st.text_input(
            "Cortex Search Service:",
            value=default_service,
            placeholder="database.schema.service_name"
        )
    
    num_chunks = st.slider("Context chunks:", 1, 5, 3,
                           help="Number of relevant chunks to retrieve per question")
    
    st.divider()
    
    if st.button(":material/delete: Clear Chat", use_container_width=True):
        st.session_state.doc_messages = []
        st.rerun()
```

* **보장된 기본값**: 다른 서비스가 있더라도 `RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH`가 드롭다운의 항상 첫 번째에 오도록 보장합니다.
* **중복 방지**: 리스트 상단에 추가하기 전에 다른 위치에 있는 기본값을 제거합니다.
* **자동 감지**: 계정 내의 모든 사용 가능한 Cortex Search 서비스를 자동으로 찾습니다.
* **유연한 입력**: 사용 가능한 서비스에 대한 드롭다운 또는 수동 텍스트 입력 옵션을 제공합니다.
* **오류 처리**: 서비스를 감지할 수 없는 경우 텍스트 입력으로 부드럽게 전환(fallback)합니다.
* **시각적 피드백**: Day 19 서비스를 사용할 때 체크표시를 보여줍니다.
* **구성 가능한 청크**: 질문당 검색할 문서 청크 수(1-5, 기본값 3)를 슬라이더로 제어합니다.
* **Clear Chat 버튼**: 대화 히스토리를 재설정하고 앱을 재실행하여 깨끗한 상태를 보여줍니다.
* **`st.rerun()`**: 히스토리 삭제 후 즉시 앱을 새로고침하도록 강제합니다.

#### 3. 검색 함수

```python
def search_documents(query, service_path, limit):
    from snowflake.core import Root
    root = Root(session)
    parts = service_path.split(".")
    
    if len(parts) != 3:
        raise ValueError("Service path must be in format: database.schema.service_name")
    
    svc = root.databases[parts[0]].schemas[parts[1]].cortex_search_services[parts[2]]
    results = svc.search(query=query, columns=["CHUNK_TEXT", "FILE_NAME"], limit=limit)
    
    chunks_data = []
    for item in results.results:
        chunks_data.append({
            "text": item.get("CHUNK_TEXT", ""),
            "source": item.get("FILE_NAME", "Unknown")
        })
    return chunks_data
```

* **재사용 가능한 함수**: 깔끔한 코드를 위해 검색 로직을 캡슐화합니다.
* **경로 검증**: 서비스 경로가 정확히 3개 부분(database.schema.service)으로 되어 있는지 확인합니다.
* **메타데이터 추출**: 소스 속성 표시를 위해 청크 텍스트와 파일명을 모두 반환합니다.
* **딕셔너리 구조**: 나중에 쉽게 표시할 수 있도록 각 청크를 `{"text": ..., "source": ...}` 형태로 저장합니다.

#### 4. 채팅 입력 및 프로세싱

```python
# Main interface
if not search_service:
    st.info(":material/arrow_back: Configure a Cortex Search service to start chatting!")
    st.caption(":material/lightbulb: **Need a search service?**\n- Complete Day 19 to create `CUSTOMER_REVIEW_SEARCH`\n- The service will automatically appear in the dropdown above")
else:
    # Display chat history
    for msg in st.session_state.doc_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your documents..."):
        st.session_state.doc_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                with st.spinner("Searching and thinking..."):
                    # Retrieve context
                    chunks_data = search_documents(prompt, search_service, num_chunks)
                    context = "\n\n---\n\n".join([c["text"] for c in chunks_data])
                    
                    # Generate response with guardrails
                    rag_prompt = f"""You are a customer review analysis assistant. Your role is to ONLY answer questions about customer reviews and feedback.

STRICT GUIDELINES:
1. ONLY use information from the provided customer review context below
2. If asked about topics unrelated to customer reviews (e.g., general knowledge, coding, math, news), respond: \"I can only answer questions about customer reviews. Please ask about product feedback, customer experiences, or review insights.\"
3. If the context doesn't contain relevant information, say: \"I don't have enough information in the customer reviews to answer that.\"
4. Stay focused on: product features, customer satisfaction, complaints, praise, quality, pricing, shipping, or customer service mentioned in reviews
5. Do NOT make up information or use knowledge outside the provided reviews

CONTEXT FROM CUSTOMER REVIEWS:
{context}

USER QUESTION: {prompt}

Provide a clear, helpful answer based ONLY on the customer reviews above. If you cite information, mention it naturally."""
                    
                    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', '{rag_prompt.replace(chr(39), chr(39)+chr(39))}')"
                    response = session.sql(sql).collect()[0][0]
                
                st.markdown(response)
                
                # Show sources with file names
                with st.expander(f":material/library_books: Sources ({len(chunks_data)} reviews used)"):
                    for i, chunk_info in enumerate(chunks_data, 1):
                        st.caption(f"**[{i}] {chunk_info['source']}**")
                        st.write(chunk_info['text'][:200] + "..." if len(chunk_info['text']) > 200 else chunk_info['text'])
                
                st.session_state.doc_messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info(":material/lightbulb: **Troubleshooting:**\n- Make sure the search service exists (check Day 19)\n- Verify the service has finished indexing\n- Check your permissions")
```

* **서비스 검증**: 채팅 인터페이스를 보여주기 전에 검색 서비스가 구성되었는지 확인합니다.
* **유용한 지침**: 서비스가 선택되지 않은 경우 안내 메시지를 보여줍니다.
* **`:=` walrus 연산자**: 사용자가 엔터를 눌렀을 때 `prompt`를 할당하고 그 값이 참인지 확인하는 것을 한 줄로 수행합니다.
* **`st.chat_input(...)`**: 앱 하단에 고정된 입력 바를 제공합니다(`st.text_input`보다 뛰어난 UX).
* **즉각적인 표시**: 사용자 메시지를 즉시 보여준 다음, 어시스턴트 메시지를 그 아래에 표시합니다.
* **`st.spinner(...)`**: 검색 및 생성 중에 로딩 표시기를 보여줍니다.
* **시스템 프롬프트의 가드레일(Guardrails)**: LLM이 고객 리뷰 이외의 질문(일반 지식, 코딩, 수학 등)에 답변하는 것을 방지합니다.
* **엄격한 범위 강제**: 답변하는 어시스턴트를 "고객 리뷰 분석 어시스턴트"로 정의하고 명확한 경계를 설정합니다.
* **근거(Grounding) 강화**: 제공된 문맥만 사용하고 할루시네이션(환각)을 일으키지 않도록 여러 지시를 추가합니다.
* **정중한 거절**: 사용자가 리뷰 범위를 벗어난 질문을 할 때 정중하게 다른 방향으로 안내합니다.
* **문자열 이스케이프**: 검색된 텍스트 내의 작은따옴표를 처리하기 위해 `chr(39)`을 사용합니다(SQL 인젝션 방지).
* **오류 처리**: 예외를 포착하고 유용한 문제 해결 팁을 제공합니다.
* **소스 표시**: 응답 직후에 확장 가능한 소스들을 보여줍니다.
* **히스토리에 추가**: 다음 재실행을 위해 사용자 질문과 어시스턴트 응답을 모두 저장합니다.

#### 5. 가드레일: 대화를 주제에 맞게 유지하기

이 챗봇의 핵심적인 개선 사항 중 하나는 시스템 프롬프트에 **가드레일(guardrails)**을 구현한 것입니다. 이는 LLM이 고객 리뷰의 범위를 벗어난 질문에 답변하는 것을 방지합니다.

**가드레일이 방지하는 사항:**
- ❌ 일반 지식 질문 ("프랑스의 수도는 어디인가요?")
- ❌ 코딩 요청 ("Python 코드를 작성해 주세요")
- ❌ 수학 문제 ("47 × 83은 얼마인가요?")
- ❌ 시사 뉴스 ("최신 뉴스가 무엇인가요?")
- ❌ 고객 리뷰와 무관한 모든 주제

**상호 작용 예시:**

```
사용자: "고객들이 헬멧에 대해 뭐라고 말하나요?"
✅ 유효한 질문 → 리뷰 인사이트 반환

사용자: "리스트를 정렬하는 Python 코드를 작성해 줘"
❌ 주제 벗어남 → "저는 고객 리뷰에 대한 질문에만 답변할 수 있습니다. 제품 피드백, 고객 경험 또는 리뷰 인사이트에 대해 질문해 주세요."

사용자: "2+2는 뭐야?"
❌ 주제 벗어남 → 리뷰 관련 질문으로 정중하게 안내
```

**이것이 중요한 이유:**
- **분야(Scope) 이탈 방지**: 챗봇이 원래 목적에 집중하도록 유지합니다.
- **할루시네이션(환각) 방지**: 제공된 문맥 밖의 답변을 지어낼 수 없게 합니다.
- **더 나은 사용자 경험**: 사용자가 챗봇의 능력과 한계를 이해하도록 돕습니다.
- **신뢰성 및 신뢰도**: 답변은 항상 실제 고객 리뷰 데이터에 근거하게 됩니다.

가드레일은 시스템 프롬프트에 명시적인 지침을 추가하여 수용 가능한 주제(제품 기능, 만족도, 불만 사항, 품질 등)를 정의하고, 주제를 벗어난 질문에 대한 표준 거절 메시지를 제공함으로써 작동합니다.

#### 6. Day 21 vs Day 22: 주요 차이점

| 기능 | Day 21 (단일 턴 RAG) | Day 22 (대화형 RAG) |
|---------|--------------------------|------------------------------|
| **히스토리** | 히스토리 없음 | 전체 대화 저장됨 |
| **인터페이스** | 버튼 + 텍스트 입력 | `st.chat_input`을 사용한 채팅 인터페이스 |
| **후속 질문** | 각 질문이 독립적임 | 이전 주고받은 내용을 참조 가능 |
| **사용 사례** | 일회성 질문 | 멀티 턴 대화 |
| **복잡도** | 상대적으로 단순함 | 더 많은 상태(state) 관리가 필요함 |

#### 7. 대화 흐름 예시

```
사용자: "고객들이 써멀 장갑에 대해 뭐라고 하나요?"
어시스턴트: [리뷰 검색 → 3개 청크 추출 → 답변 생성]
"고객들은 일반적으로 써멀 장갑의 보온성을 칭찬합니다..."

사용자: "불만 사항은 없나요?"
어시스턴트: [다시 검색 → 이전 문맥 참조 가능]
"네, 일부 고객들은 장기간 사용 후의 내구성 문제를 언급했습니다..."

사용자: "어떤 제품이 가장 좋은 리뷰를 받나요?"
어시스턴트: [새로운 검색 수행 → 답변 제공]
"리뷰를 종합해 볼 때, 헬멧이 가장 높은 평가를 받습니다..."
```

* **각 질문이 새로운 검색을 트리거함**: 일부 대화형 시스템과 달리, 이 앱은 매 질문마다 검색을 수행합니다(처음에만 하는 것이 아님).
* **독립적인 검색**: 이를 통해 답변이 항상 각 특정 질문에 대해 가장 관련성이 높은 문서를 바탕으로 근거를 갖게 됩니다.
* **히스토리 유지**: 사용자는 위로 스크롤하여 대화 전체 내용을 검토할 수 있습니다.

이 앱이 실행되면 Cortex Search에서 관련 정보를 검색하고, 대화 히스토리를 유지하며, 소스 근거와 함께 답변을 생성하는 완전한 기능의 대화형 문서 Q&A 챗봇을 갖게 됩니다. 이것으로 문서 추출(Day 16), 청킹(Day 17), 임베딩(Day 18), 검색 서비스 생성(Day 19), 쿼리 수행(Day 20), 단일 턴 RAG(Day 21)를 거쳐 이 완전한 대화형 챗봇(Day 22)에 이르는 Week 3의 RAG 파이프라인 여정이 마무리됩니다.

---

### :material/library_books: 리소스
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Build Conversational Apps](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
- [Snowflake Cortex LLMs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
