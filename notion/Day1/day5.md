# Day 5: Build a Post Generator App

# 0. 목표

<aside>
💡 **사용자 입력(URL, 톤, 길이)을 받아 맞춤형 LinkedIn 포스트를 생성하는 앱 만들기**

1. `st.text_input`, `st.selectbox` 등 다양한 입력 위젯 사용법을 익힙니다.
2. 사용자의 입력을 LLM 프롬프트에 동적으로 반영하는 방법(Prompt Templates)을 배웁니다.
3. 페르소나(Persona)를 부여하여 원하는 어조의 글을 생성합니다.

</aside>

# 1. 개념 및 이론 (Theory)

### 동적 프롬프트 (Dynamic Prompting)
LLM에게 항상 똑같은 질문만 하는 것이 아니라, 프로그램의 변수 값을 문장 속에 끼워 넣어 상황에 맞는 질문을 만드는 기술입니다. 파이썬의 **f-string**(`f"..."`)을 사용하면 매우 직관적으로 구현할 수 있습니다.

### 페르소나 부여 (Persona Adoption)
프롬프트의 첫 문장에 "당신은 ~입니다(You are a...)"라고 역할을 정해주면, LLM은 그 역할에 맞는 전문 용어와 어투를 사용하게 되어 결과물의 품질이 높아집니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 기본 UI 구성

`day5.py`를 생성하고 앱의 골격을 잡습니다.

```python
import streamlit as st
from snowflake.cortex import Complete
# Snowflake 연결 설정 (Day 1~4 코드 참조)
# ...

st.title("LinkedIn Post Generator 🚀")

st.subheader("Create a post from any URL")
```

### Step 2: 입력 위젯 배치

사용자가 글의 재료를 넣을 수 있는 창을 만듭니다.

```python
# 1. 기사나 문서의 URL 입력
url = st.text_input("Content URL", "https://docs.snowflake.com/en")

# 2. 원하는 톤 앤 매너 선택
tone = st.selectbox("Tone", ["Professional", "Casual", "Funny", "Dramatic"])

# 3. 글 길이 조절 슬라이더
length = st.slider("Approximate word count", 50, 500, 150)
```

### Step 3: 프롬프트 생성 및 실행

버튼을 누르면 위에서 입력받은 변수들을 조합하여 프롬프트를 완성하고, LLM에게 보냅니다.

```python
if st.button("Generate Post"):
    # f-string을 활용한 프롬프트 템플릿
    prompt = f"""
    You are an expert social media manager.
    Create a LinkedIn post based on the content from this URL: {url}
    
    Requirements:
    - Tone: {tone}
    - Length: Approximately {length} words
    - Structure: Engaging hook + Key points + Call to action
    """
    
    with st.spinner("Generating content..."):
        # LLM 호출
        response = Complete("claude-3-5-sonnet", prompt, session=session)
        
        # 결과 표시
        st.subheader("Generated Content:")
        st.markdown(response)
```

# 3. 핵심 포인트 (Key Takeaways)

- **Input Widgets**: `text_input`, `selectbox`, `slider` 등 적절한 위젯을 조합하여 어떤 종류의 데이터든 사용자로부터 받을 수 있습니다.
- **Context Injection**: 인터넷에 있는 모든 정보를 LLM이 알지는 못합니다. URL 내용을 프롬프트에 포함시키거나(물론 여기서는 URL 텍스트만 줬지만, 실제로는 URL의 본문을 긁어서 주는 것이 더 정확합니다), 구체적인 지시사항을 줌으로써 LLM의 환각(Hallucination)을 줄이고 정확도를 높일 수 있습니다.

---

# 💡 실습 과제 (Hands-on Practice)

사용자가 선택한 옵션들이 프롬프트에 동적으로 반영되도록 작성해 봅니다.

1. 파이썬의 f-string을 사용하여 `tone`, `word_count`, `content` 변수를 포함하는 프롬프트를 만드세요.
2. LinkedIn 전문가로서 행동하도록 페르소나를 부여해 보세요.

# ✅ 정답 코드 (Solution)

```python
# f-string을 이용한 동적 프롬프트 생성
prompt = f"""
당신은 LinkedIn 전문 게시물 작성자입니다. 
다음 내용을 참고하여 게시물을 작성해 주세요: {content}

제약 사항:
- 어조: {tone}
- 단어 수: 약 {word_count} 단어 내외
"""
```
