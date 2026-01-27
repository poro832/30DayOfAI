# 코르텍스 에이전트 (Cortex Agent)

# 0. 목표

<aside>
💡

**자율적으로 도구를 선택하고 실행하는 Cortex Agent 구현**

1. 비정형 데이터(영업 대화)와 정형 데이터(영업 지표) 준비
2. Cortex Search 및 Cortex Analyst(시맨틱 모델) 설정
3. 여러 도구를 통합하여 복합적인 질문에 답변하는 AI 에이전트 구축

</aside>

# 1. 개요 (Overview)

- **Cortex Agent**: 질문을 분석하여 계획을 세우고, 사용 가능한 도구를 선택하여 작업을 자율적으로 수행하는 AI 구동 어시스턴트입니다.
- **자율성**: 수동 RAG 시스템과 달리, 에이전트는 검색(Search)이나 분석(Analyst) 도구 중 무엇을 사용할지 스스로 결정합니다.
- **멀티 도구**: 텍스트 기반 검색(Cortex Search)과 SQL 기반 데이터 분석(Cortex Analyst)을 한 번에 활용할 수 있습니다.

# 2. 구현 내용 (Implementation)

## 2-1. 데이터 및 검색 서비스 설정 (Cortex Search)

영업 대화 내용을 저장하는 테이블을 만들고, 이를 검색할 수 있는 인덱스를 생성합니다.

```sql
-- 영업 대화 테이블 생성
CREATE TABLE SALES_CONVERSATIONS (
    conversation_id VARCHAR,
    transcript_text TEXT,
    customer_name VARCHAR,
    deal_stage VARCHAR,
    sales_rep VARCHAR,
    conversation_date TIMESTAMP,
    deal_value FLOAT,
    product_line VARCHAR
);

-- Cortex Search 서비스 생성
CREATE CORTEX SEARCH SERVICE SALES_CONVERSATION_SEARCH
  ON transcript_text
  ATTRIBUTES customer_name, deal_stage, sales_rep
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (SELECT * FROM SALES_CONVERSATIONS);
```

## 2-2. 정형 데이터 분석 설정 (Cortex Analyst)

영업 지표 테이블을 생성하고, AI가 데이터를 이해할 수 있도록 시맨틱 모델(YAML)을 준비합니다.

```yaml
# sales_metrics_model.yaml
name: sales_metrics
description: Sales metrics and analytics model
tables:
  - name: SALES_METRICS
    base_table:
      database: SALES_DB
      schema: DATA
      table: SALES_METRICS
    dimensions:
      - name: CUSTOMER_NAME
        synonyms: [client, buyer]
    measures:
      - name: DEAL_VALUE
        synonyms: [revenue, amount]
```

## 2-3. Cortex Agent 생성

여러 도구(Search, Analyst)를 정의하고 에이전트의 역할(Instructions)을 설정합니다.

```sql
CREATE OR REPLACE AGENT SALES_CONVERSATION_AGENT
  FROM SPECIFICATION
  $$
  models:
    orchestration: claude-sonnet-4-5
  instructions:
    response: '영업 데이터, 대화, 거래 및 지표에 관한 질문에만 답변하세요.'
  tools:
    - tool_spec:
        type: "cortex_search"
        name: "ConversationSearch"
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "SalesAnalyst"
  tool_resources:
    ConversationSearch:
      name: "SALES_CONVERSATION_SEARCH"
    SalesAnalyst:
      semantic_model_file: "@MODELS/sales_metrics_model.yaml"
  $$;
```

# 3. 활용 사례 (Use Cases)

1. **지능형 영업 지원**: 특정 고객과의 대화 내용 요약과 현재 영업 실적 지표를 동시에 확인
2. **복합 쿼리 처리**: "지난달 성사된 거래 중 가장 큰 계약의 주요 논의 내용은 무엇이었나요?"와 같은 질문 해결
3. **데이터 기반 의사결정**: 자율적으로 데이터를 추출하고 요약하여 보고서 초안 작성

# 4. 실행 결과

## 실행 코드

`python -m streamlit run app/day26.py`

## 결과

- **Data Setup**: 대화 내용 저장, 검색 서비스 생성, 시맨틱 모델 업로드가 단계별로 진행됩니다.
- **Create Agent**: 버튼을 클릭하면 Snowflake 내에 지능형 에이전트가 생성됩니다.
- 에이전트는 사용자의 질문에 맞춰 적절한 도구(Search 또는 Analyst)를 자동으로 호출하여 답변을 제공합니다.

---

# 💡 실습 과제 (Hands-on Practice)

Snowflake 내에 지능형 에이전트(Agent)를 생성하는 SQL 문을 실행해 봅니다.

1. `CREATE AGENT` 구문이 포함된 `create_sql` 변수를 실행하세요.
2. `session.sql().collect()`를 사용하여 에이전트 생성을 완료하세요.

# ✅ 정답 코드 (Solution)

```python
# Cortex Agent 생성 실습
# session.sql()과 .collect()를 사용하여 에이전트 생성 명령 실행
session.sql(create_sql).collect()
```
