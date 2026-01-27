# 내 문서와 채팅하기 (Chat with Your Documents)

# 0. 목표

<aside>
💡

**대화형 인터페이스로 문서 기반(RAG) 챗봇 구현**

1. Streamlit 채팅 UI 구성 (st.chat_input, st.chat_message)
2. 대화 기록 관리 (Session State)
3. RAG 파이프라인과 채팅 인터페이스 통합

</aside>

# 1. 개요 (Overview)

- **대화형 RAG**: 단일 질문-답변을 넘어, 채팅 형식으로 문서에 대해 질문할 수 있는 인터페이스입니다.
- **통합**: Day 19-21에서 구축한 검색 및 생성 기능을 친숙한 채팅 UI로 제공합니다.
- **프롬프트 엔지니어링**: 챗봇의 페르소나와 제약 조건을 설정하여 문서 범위 내에서만 답변하도록 유도합니다.

# 2. Streamlit 앱 구현 (Implementation)

## 2-1. 채팅 기록 관리

```python
# 상태 초기화
if "doc_messages" not in st.session_state:
    st.session_state.doc_messages = []

# ...

# 채팅 기록 표시
for msg in st.session_state.doc_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
```

- `st.session_state.doc_messages`: 대화 내역을 저장하는 리스트입니다.
- `st.chat_message`: 저장된 메시지를 사용자(user)와 어시스턴트(assistant) 역할에 따라 표시합니다.

## 2-2. 검색 함수 모듈화

```python
def search_documents(query, service_path, limit):
    from snowflake.core import Root
    # ... (Cortex Search 연결 설정) ...
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

- 검색 로직을 별도 함수로 분리하여 코드 재사용성을 높였습니다.
- 검색 결과에서 텍스트와 출처(파일명)를 추출하여 반환합니다.

## 2-3. 채팅 입력 및 RAG 실행

```python
if prompt := st.chat_input("문서에 대해 질문하세요..."):
    # 1. 사용자 질문 표시 및 저장
    st.session_state.doc_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. 어시스턴트 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("검색 및 생각 중..."):
            # 검색
            chunks_data = search_documents(prompt, search_service, num_chunks)
            context = "\n\n---\n\n".join([c["text"] for c in chunks_data])
            
            # 프롬프트 구성 (가드레일 포함)
            rag_prompt = f"""You are a customer review analysis assistant.
STRICT GUIDELINES:
1. ONLY use information from the provided customer review context
2. If context doesn't contain info, say "I don't have enough information"
...
CONTEXT: {context}
QUESTION: {prompt}
"""
            # LLM 호출
            sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', '{rag_prompt_escaped}')"
            response = session.sql(sql).collect()[0][0]
            
            # 답변 표시 및 저장
            st.markdown(response)
            st.session_state.doc_messages.append({"role": "assistant", "content": response})
```

- `st.chat_input`: 사용자의 입력을 받습니다. Walrus 연산자(`:=`)를 사용하여 변수 할당과 조건 확인을 동시에 수행합니다.
- **엄격한 프롬프트 가이드라인**: 사용자가 문서와 무관한 질문을 하거나(예: 일반 상식), 환각(Hallucination)을 일으키지 않도록 제약 조건을 명시합니다.

# 3. 핵심 포인트

## UI/UX 요소

- **출처 표시**: `st.expander`를 사용하여 답변에 사용된 문서 출처를 깔끔하게 표시합다. 신뢰성을 높이는 중요한 요소입니다.
- **채팅 지우기**: 사이드바에 버튼을 두어 세션 상태를 초기화하고 대화를 새로 시작할 수 있게 합니다.

## 프롬프트 전략

- **역할 부여**: "Customer review analysis assistant"로 역할을 한정합니다.
- **제약 조건**: "ONLY use information from context"와 같은 강력한 어조로 외부 지식 사용을 차단합니다.
- **예외 처리**: 정보가 없을 때 솔직하게 모른다고 대답하도록 지시합니다.

# 4. 실행 결과

## 실행 코드

`python -m streamlit run app/day22.py`

## 결과

- 사용자는 채팅 창을 통해 자연스럽게 연속적인 질문을 할 수 있습니다.
- 봇은 검색된 리뷰 데이터에 기반해서만 답변하며, 출처를 함께 제공합니다.

---

# 💡 실습 과제 (Hands-on Practice)

문서 검색 로직을 별도의 함수로 모듈화하여 챗봇에서 호출할 수 있게 만들어 봅니다.

1. `svc.search()` 메서드를 사용하여 쿼리를 실행하세요.
2. 결과에서 `CHUNK_TEXT`와 `FILE_NAME` 컬럼을 가져오도록 설정하세요.
3. 검색 결과를 `chunks_data` 리스트 형식으로 반환하세요.

# ✅ 정답 코드 (Solution)

```python
# 문서 검색 함수 구현 실습
def search_documents(query, service_path, limit):
    # ... (Root 및 서비스 연결 코드 생략) ...
    
    # 1. Cortex Search 실행
    results = svc.search(
        query=query, 
        columns=["CHUNK_TEXT", "FILE_NAME"], 
        limit=limit
    )
    
    # 2. 데이터 추출 및 반환
    chunks_data = []
    for item in results.results:
        chunks_data.append({
            "text": item.get("CHUNK_TEXT", ""),
            "source": item.get("FILE_NAME", "Unknown")
        })
    return chunks_data
```
