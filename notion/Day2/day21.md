# RAG with Cortex Search (Cortex Search를 활용한 RAG)

# 0. 목표

<aside>
💡

**검색 결과와 LLM 생성을 결합하여 근거 있는 답변 제공**

1. 사용자 질문으로 관련 리뷰 검색 (Retrieve)
2. 검색된 리뷰를 프롬프트에 추가 (Augment)
3. LLM으로 근거 있는 답변 생성 (Generate)

</aside>

# 1. 개요 (Overview)

- **RAG (Retrieval-Augmented Generation)**의 완전한 구현입니다.
- 단순히 LLM만 사용하는 것이 아니라, 실제 데이터(고객 리뷰)를 기반으로 답변합니다.
- Week 3의 **최종 단계**로, Day 16-20에서 구축한 모든 요소를 통합합니다.

## RAG 작동 방식

```
┌─────────────┐
│  1. Retrieve │  Cortex Search로 관련 문서 찾기
│  (검색)      │  예: "열 장갑이 충분히 따뜻한가요?"
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  2. Augment  │  검색된 리뷰를 프롬프트에 추가
│  (증강)      │  "다음 고객 리뷰를 참고하세요: ..."
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  3. Generate │  LLM이 근거를 바탕으로 답변
│  (생성)      │  "고객 리뷰에 따르면 열 장갑은..."
└─────────────┘
```

# 2. Streamlit 앱 구현 (Implementation)

## 2-1. 사이드바 설정

```python
import streamlit as st

# Snowflake 연결
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except:
    from snowflake.snowpark import Session
    session = Session.builder.configs(st.secrets["connections"]["snowflake"]).create()

# 사이드바 구성
with st.sidebar:
    st.header(":material/settings: Settings")
    
    # Day 19의 기본 검색 서비스
    default_service = 'RAG_DB.RAG_SCHEMA.CUSTOMER_REVIEW_SEARCH'
    
    # 검색 서비스 선택
    search_service = st.selectbox(
        "Search Service:",
        options=available_services,
        index=0
    )
    
    num_chunks = st.slider("Context chunks:", 1, 10, 3,
                           help="Number of relevant chunks to retrieve")
    
    model = st.selectbox(
        "LLM Model:",
        ["claude-3-5-sonnet", "mistral-large", "llama3.1-8b"],
        help="Model to generate the answer"
    )
    
    show_context = st.checkbox("Show retrieved context", value=True)
```

- 검색 서비스, 컨텍스트 청크 수, LLM 모델 선택
- 검색된 컨텍스트 표시 여부 토글

## 2-2. 질문 입력

```python
# 메인 인터페이스
question = st.text_input(
    "Your question:",
    value="Are the thermal gloves warm enough for winter?",
    placeholder="e.g., Which products have durability issues?"
)

if st.button(":material/search: Search & Answer", type="primary"):
    # RAG 파이프라인 시작
```

- 기본 질문: "열 장갑이 겨울에 충분히 따뜻한가요?"
- 사용자가 자유롭게 질문 입력 가능

## 2-3. 1단계: Cortex Search에서 컨텍스트 검색

```python
if question and search_service:
    with st.status("Processing...", expanded=True) as status:
        # 1단계: Cortex Search에서 컨텍스트 검색
        st.write(":material/search: **Step 1:** Searching documents...")
        
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
        
        # 메타데이터와 함께 컨텍스트 추출
        context_chunks = []
        sources = []
        for item in search_results.results:
            context_chunks.append(item.get("CHUNK_TEXT", ""))
            sources.append(item.get("FILE_NAME", "Unknown"))
        
        context = "\n\n---\n\n".join(context_chunks)
        
        st.write(f"   :material/check_circle: Found {len(context_chunks)} relevant chunks")
```

- 사용자 질문으로 Cortex Search 실행
- 가장 관련성 높은 N개 청크 검색 (기본 3개)
- 청크 텍스트와 출처 파일명 추출
- `"\n\n---\n\n"`로 청크 구분하여 하나의 컨텍스트로 결합

## 2-4. 2단계: LLM으로 답변 생성

```python
        # 2단계: LLM으로 답변 생성
        st.write(":material/smart_toy: **Step 2:** Generating answer...")
        
        rag_prompt = f"""You are a helpful assistant. Answer the user's question based ONLY on the provided context.
If the context doesn't contain enough information to answer, say "I don't have enough information to answer that based on the available documents."

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}

Provide a clear, accurate answer based on the context. If you use information from the context, mention it naturally."""
        
        # LLM 호출
        response_sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{model}',
            '{rag_prompt.replace("'", "''")}'
        ) as response
        """
        
        response = session.sql(response_sql).collect()[0][0]
        
        st.write("   :material/check_circle: Answer generated")
```

- 프롬프트 구성: 컨텍스트 + 사용자 질문
- **중요 지시사항**: "제공된 컨텍스트만 기반으로 답변"
- 컨텍스트에 정보가 없으면 모른다고 말하도록 지시
- `SNOWFLAKE.CORTEX.COMPLETE()`로 LLM 호출
- `.replace("'", "''")`: SQL 인젝션 방지를 위한 이스케이프

## 2-5. 결과 표시

```python
        # 결과 표시
        st.divider()
        
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

- 생성된 답변을 큰 컨테이너에 표시
- "Show retrieved context" 체크박스가 활성화되어 있으면:
  - 사용된 모든 청크 표시
  - 각 청크의 출처 파일명 표시
  - Expander로 접어서 표시 (깔끔한 UI)

## 2-6. RAG 답변 예시

### 질문: "Are the thermal gloves warm enough for winter?"

**검색된 컨텍스트 (3개 청크):**
1. review-042.txt: "These gloves are amazing! Kept my hands toasty warm even in -20°C..."
2. review-087.txt: "Great warmth and insulation. Perfect for cold winter days..."
3. review-015.txt: "Hands stayed warm throughout the ski trip..."

**생성된 답변:**
```
Based on customer reviews, the thermal gloves are highly effective for winter use. 
Multiple customers reported that the gloves kept their hands warm in extremely cold 
conditions, including temperatures as low as -20°C. Customers specifically mentioned 
"toasty warm hands" and "excellent heat retention" during winter activities like 
skiing. The consensus is that these gloves provide great warmth and insulation for 
cold weather.
```

# 3. 핵심 포인트 및 고려사항

## RAG의 장점

- **근거 있는 답변**: 실제 고객 리뷰를 기반으로 답변
- **환각(Hallucination) 방지**: LLM이 만들어낸 정보가 아닌 실제 데이터 사용
- **출처 추적**: 어떤 리뷰에서 정보를 가져왔는지 확인 가능

## 프롬프트 엔지니어링

```python
rag_prompt = f"""Answer based ONLY on the provided context.
If the context doesn't contain enough information, say "I don't have enough information."

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}
"""
```

- "ONLY on the provided context": LLM이 외부 지식 사용 방지
- 정보 부족 시 명확히 말하도록 지시
- 컨텍스트와 질문을 명확히 구분

## Week 3 RAG 파이프라인 완성

```
Day 16: 문서 업로드 및 텍스트 추출
   ↓
Day 17: 청크로 분할
   ↓
Day 18: 임베딩 생성 (벡터화)
   ↓
Day 19: Cortex Search 서비스 생성
   ↓
Day 20: 검색 쿼리 실행
   ↓
Day 21: LLM으로 답변 생성 ✓
```

# 실행 결과

## 실행 코드

Streamlit 실행 코드 = python -m streamlit run 파일명.py

예시 : `python -m streamlit run app/day21.py`

## 결과

- 사용자 질문에 대한 근거 있는 답변 제공
- 실제 고객 리뷰 데이터를 기반으로 답변 생성
- 출처 추적 가능 (어떤 리뷰에서 정보를 가져왔는지)
- 환각 방지 (LLM이 만들어낸 정보가 아닌 실제 데이터 사용)

## Week 3 완료!

이제 완전한 RAG 시스템이 구축되었습니다:
- ✅ 문서 추출 (Day 16)
- ✅ 청크 분할 (Day 17)
- ✅ 임베딩 생성 (Day 18)
- ✅ 검색 서비스 (Day 19)
- ✅ 검색 쿼리 (Day 20)
- ✅ 검색 쿼리 (Day 20)
- ✅ RAG 답변 생성 (Day 21)

---

# 💡 실습 과제 (Hands-on Practice)

검색된 컨텍스트와 사용자의 질문을 결합하여 LLM에게 전달할 RAG 프롬프트를 작성해 봅니다.

1. f-string을 사용하여 `context`와 `question`이 포함된 프롬프트를 만드세요.
2. LLM이 제공된 컨텍스트**만**을 사용하여 답변하도록 지시사항을 포함하세요.

# ✅ 정답 코드 (Solution)

```python
# RAG 프롬프트 작성 실습
rag_prompt = f"""당신은 유능한 어시스턴트입니다. 오직 아래 제공된 컨텍스트(CONTEXT)만을 바탕으로 사용자의 질문에 답하세요.
만약 컨텍스트에 답변할 내용이 없다면, "제공된 문서에는 관련 정보가 없습니다."라고 답변하세요.

[CONTEXT]
{context}

[USER QUESTION]
{question}
"""
```
