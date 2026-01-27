# 3-Day Intensive AI Course: From Zero to RAG & Vision (Revised)

# 0. 과정 개요 (Course Overview)

**"One Data, One Flow" 전략**
30일 분량을 3일로 압축하며 발생할 수 있는 학습 격차를 줄이기 위해, **하나의 데이터셋(예: 신제품 리뷰)**을 3일 내내 사용하여 논리적 연속성을 확보합니다. Day 2에 RAG 챗봇을 완성하여 성취감을 극대화합니다.

| 일정 | 주제 | 핵심 목표 |
| :--- | :--- | :--- |
| **Day 1** | **AI Fundamentals & Python Connection** | Cortex 기능 실습 및 **Python(Snowpark) 연결**로 앱 개발 준비 |
| **Day 2** | **End-to-End RAG Pipeline** | 데이터 파이프라인(오전)부터 **챗봇 완성(오후)**까지 "죽음의 조" 정면 돌파 |
| **Day 3** | **Multimodal & Advanced Ops** | 이미지 분석(Vision) 및 품질 평가, 고급 기능 확장 |

---

# Day 1: AI Fundamentals & Python Connection (기초 및 연결)

> **전략 (Bridge)**: SQL 워크시트에서 기능만 테스트하는 것이 아니라, **반드시 Python 코드**로 이를 실행해봐야 Day 2의 Streamlit 실습과 자연스럽게 연결됩니다.

### 📂 [Part 1] Fundamentals (기초 다지기)
- **Morning: Cortex AI Core (SQL)** (Day 1-9)
  - **Concept**: 벡터와 임베딩 이해하기 (Vector/Embedding)
  - **Setup**: Snowflake 환경 설정 & `AI_COMPLETE` 첫 호출
  - **Functions**: `TRANSLATE`, `SENTIMENT_SCORE`, `SUMMARIZE`
  - **Practice**: "제품 리뷰 데이터"를 로드하여 번역하고 감성 점수 매기기 (SQL)
- **Afternoon: Python & Snowpark (Bridge)** (Day 10 + New)
  - **Transition**: SQL 로직을 Python `session.sql()`로 변환하는 방법 학습
  - **Practice**: 오전의 감성 분석 로직을 Jupyter/Python 스크립트로 실행해보기
  - **Outcome**: "아, 앱 개발은 이 Python 코드를 웹에 붙이는 거구나"라는 감각 익히기

---

# Day 2: End-to-End RAG Pipeline (완결형 RAG 구축)

> **전략 (Focus)**: 가장 중요한 날입니다. **오전(백엔드) -> 오후(프론트/통합)** 순서로 진행하여, 교육 종료 시점에 **"동작하는 RAG 챗봇"**을 손에 쥐게 합니다. UI 코딩은 복사/붙여넣기(Skeleton Code)로 시간을 절약하고 로직에 집중합니다.

### 📂 [Part 2] RAG Pipeline (파이프라인 & 챗봇)
- **Morning: RAG Backend Pipeline** (Day 16-19)
  - **Goal**: "문서가 답변이 되기까지"의 데이터 흐름 완성
  - **Step 1 (File)**: PDF/텍스트 문서 스테이지 업로드
  - **Step 2 (Process)**: 텍스트 추출(Extract) 및 청킹(Chunking)
  - **Step 3 (Vector)**: 임베딩(Embed) 생성 및 벡터 테이블 저장
  - **Step 4 (Search)**: Cortex Search 서비스 생성 및 검색 테스트
- **Afternoon 1: Streamlit Basics** (Day 11-15)
  - **Goal**: 챗봇 껍데기(UI) 빠르게 만들기
  - **Action**: `st.chat_input`, `st.write` 등 핵심 UI 요소 실습 (스켈레톤 코드 활용)
  - **Compare**: 간단한 모델 비교 앱 실습
- **Afternoon 2: RAG Integration** (Day 20-22) **[★중요]**
  - **Goal**: 오전에 만든 **Backend**와 오후에 만든 **UI** 연결
  - **Integration**: `Cortex Search` 결과를 프롬프트에 넣어 LLM 답변 생성
  - **Outcome**: **"내 문서와 대화하는 챗봇" v1.0 완성**

---

# Day 3: Multimodal & Advanced Ops (확장 및 고도화)

> **전략 (Expand)**: Day 2에서 챗봇을 완성하지 못한 수강생을 위해 **"완성된 Day 2 코드(Checkpoint)"**를 제공하고 시작합니다. 평가는 개념/데모 위주로 진행하고, 흥미로운 Vision AI 실습 비중을 높입니다.

### 📂 [Part 3] Advanced Applications (고급 기능)
- **Morning: Quality & Evaluation** (Day 23 + Checkpoint)
  - **Recovery**: Day 2 미완성자를 위한 Checkpoint 코드 배포
  - **Concept**: RAG 3대 지표 (관련성, 근거성, 답변 품질) 이해
  - **Action**: TruLens/Evaluation 데모 시연 및 자동 평가 파이프라인 이해
- **Afternoon: Multimodal (Vision AI)** (Day 24)
  - **Goal**: 텍스트를 넘어 이미지로 확장
  - **Practice**: 제품 사진을 업로드하고 "이 제품의 특징 설명해줘" 기능 구현
  - **Integration**: 챗봇에 이미지 업로드 기능 추가 (선택 사항)
- **Closing: Future Roadmap** (Day 25-30 Plan)
  - **Roadmap**: Text-to-SQL (Analysts), Fine-tuning, AI Agents 등 심화 학습 방향 제시
