# Day 7: Theming and Layout

# 0. 목표

<aside>
💡 **앱을 프로페셔널하게 디자인하기 (테마 & 레이아웃)**

1. `config.toml` 파일을 이용해 전역(Global) 스타일(다크 모드, 브랜드 컬러)을 적용합니다.
2. `st.sidebar`를 활용해 중요한 입력과 덜 중요한 설정을 분리합니다.
3. 시각적 계층 구조를 잡는 레이아웃 전략을 배웁니다.

</aside>

# 1. 개념 및 이론 (Theory)

### 설정 파일 (Configuration)
파이썬 코드 안에 색상 코드를 하드코딩하는 것은 좋지 않습니다. `.streamlit/config.toml`이라는 설정 파일을 만들면, 앱 전체의 폰트, 배경색, 버튼 스타일 등을 한 곳에서 관리할 수 있습니다.

### 레이아웃 디자인 (Sidebar Pattern)
화면 왼쪽의 사이드바는 보통 **"설정(Settings)"** 이나 **"네비게이션"** 용도로 쓰이고, 메인 화면은 **"콘텐츠"** 를 보여주는 것이 웹 앱의 표준 패턴입니다.

# 2. 단계별 구현 (Step-by-Step)

### Step 1: 테마 파일 생성

프로젝트 폴더 안에 `.streamlit` 폴더가 없다면 만들고, 그 안에 `config.toml` 파일을 생성합니다.

**File: `.streamlit/config.toml`**
```toml
[theme]
# 기본 테마를 다크 모드로 설정
base = "dark"

# 브랜드 포인트 컬러 (예: Spotify Green, Nvidia Green 등)
primaryColor = "#1ed760"

# 배경색 미세 조정 (완전 검정보다는 짙은 회색이 눈이 편합니다)
backgroundColor = "#191919"
secondaryBackgroundColor = "#262626"

# 폰트와 버튼 스타일
font = "sans serif" 
```
저장 후 앱을 새로고침하면 색상이 바뀐 것을 볼 수 있습니다.

### Step 2: 사이드바 레이아웃 적용

`day7.py` 파일을 만들고 기능을 사이드바로 옮깁니다.

```python
import streamlit as st

st.title("Day 7: Theming & Layout 🎨")

# 메인 화면에는 가장 중요한 입력만 둡니다.
st.subheader("Main Content Area")
url = st.text_input("Content URL")

# 부가적인 설정은 사이드바로 옮깁니다.
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 구분선
    st.divider()
    
    tone = st.selectbox("Tone", ["Professional", "Casual"])
    length = st.slider("Word count", 100, 500, 200)
    
    # 버튼도 사이드바에 넣을 수 있습니다.
    submit = st.button("Generate")

# 결과 출력은 다시 메인 화면에서
if submit:
    st.info(f"Generating post for {url} with {tone} tone...")
    # (LLM 호출 로직...)
```

### Step 3: 컨테이너와 컬럼

메인 화면을 더 짜임새 있게 만들기 위해 `st.container`나 `st.columns`를 쓸 수도 있습니다.

```python
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Expected Words", value=length)
with col2:
    st.metric(label="Estimated Cost", value="$0.02")
```

# 3. 핵심 포인트 (Key Takeaways)

- **Separation of Concerns**: 화면 레이아웃을 나눌 때도 "무엇이 사용자에게 가장 중요한가?"를 먼저 생각해야 합니다.
- **Config.toml**: 팀 프로젝트 시 모든 팀원이 같은 스타일을 유지하도록 도와주는 강력한 도구입니다.

---

# 💡 실습 과제 (Hands-on Practice)

메인 화면의 혼잡함을 줄이기 위해 설정을 사이드바로 이동시켜 봅니다.

1. `with st.sidebar:` 블록을 사용하여 사이드바 영역을 정의하세요.
2. `tone` 선택과 `word_count` 슬라이더, 그리고 `Generate` 버튼을 사이드바 안으로 옮기세요.

# ✅ 정답 코드 (Solution)

```python
# 사이드바 레이아웃 구현
with st.sidebar:
    st.header("⚙️ 설정 (Settings)")
    st.divider()
    
    # 설정 위젯들을 사이드바에 배치
    tone = st.selectbox("어조 (Tone):", ["Professional", "Casual", "Funny"])
    word_count = st.slider("단어 수:", 50, 300, 100)
    
    # 실행 버튼도 사이드바에 배치
    submit = st.button("게시물 생성", type="primary")

if submit:
    # 실행 로직...
```
