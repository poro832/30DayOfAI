오늘의 챌린지 목표는 6일차의 앱을 기반으로 하되 이번에는 **테마와 레이아웃**에 중점을 둡니다. **Streamlit의 구성 및 레이아웃 도구를 사용하여 표준 기능 인터페이스를 세련되고 브랜드화된 경험으로 변환**해야 합니다. 완료되면 깔끔한 사이드바 탐색 및 사용자 지정 색상이 있는 "다크 모드" 앱을 갖게 되어 더 전문적인 모양과 느낌을 줍니다.

---

### :material/settings: 작동 방식: 단계별 설명

시각적 디자인 및 구조와 관련된 특정 변경 사항을 분석해 보겠습니다.

#### 1. 전역 스타일링 (테마)

CSS를 작성하지 않고 전체 앱에 사용자 지정 모양을 적용하려면 앱의 작업 디렉토리에 `.streamlit/config.toml` 파일을 생성하여 Streamlit의 기본 테마 지원을 사용할 수 있습니다.
```toml
# .streamlit/config.toml
[server]
enableStaticServing = true

[theme]
base = "dark"
primaryColor = "#1ed760"
backgroundColor = "#2a2a2a"
secondaryBackgroundColor = "#121212"
codeBackgroundColor = "#121212"
textColor = "#ffffff"
linkColor = "#1ed760"
borderColor = "#7c7c7c"
showWidgetBorder = true
baseRadius = "0.3rem"
buttonRadius = "full"
headingFontWeights = [600, 500, 500, 500, 500, 500]
headingFontSizes = ["3rem", "2.5rem", "2.25rem", "2rem", "1.5rem"]
chartCategoricalColors = ["#ffc862", "#2d46b9", "#b49bc8"]

[theme.sidebar]
backgroundColor = "#121212"
secondaryBackgroundColor = "#000000"
codeBackgroundColor = "#2a2a2a"
borderColor = "#696969"
```

* **`base = "dark"`**: 애플리케이션을 다크 모드로 즉시 전환하여 텍스트 및 배경의 기본값을 눈에 편하게 변경합니다.
* **`primaryColor`**: 상호작용 요소("Generate" 버튼 및 링크 등)의 강조 색상을 설정합니다. 여기서는 화려한 녹색(`#1ed760`)으로 설정됩니다.
* **`buttonRadius = "full"`**: 버튼의 형태를 표준 직사각형에서 완전히 둥근 알약 모양 버튼으로 변경합니다.
* **`[theme.sidebar]`**: 메인 본문과 다르게 사이드바를 스타일링할 수 있는 특정 하위 섹션으로 시각적 분리를 만듭니다.

#### 2. 레이아웃 구조: 사이드바

6일차에서 했던 것처럼 모든 것을 메인 페이지에 수직으로 쌓는 대신 구성 옵션을 사이드바로 이동합니다.
```python
# Input widgets for the main area
st.subheader(":material/input: Input content")
content = st.text_input("Content URL:", "https://docs.snowflake.com/en/user-guide/views-semantic/overview")

# Configuration widgets moved to the sidebar
with st.sidebar:
    st.title(":material/post: LinkedIn Post Generator v3")
    st.success("An app for generating LinkedIn post using content from input link.")
    tone = st.selectbox("Tone:", ["Professional", "Casual", "Funny"])
    word_count = st.slider("Approximate word count:", 50, 300, 100)
```

* **`with st.sidebar:`**: 이 컨텍스트 관리자는 내부에 정의된 모든 위젯(제목, 톤, 슬라이더)을 축소 가능한 측면 패널로 이동하여 메인 작업 영역을 깨끗하게 유지합니다.
* **`:material/post:`**: Streamlit은 문자열에서 직접 Material Design 아이콘을 지원합니다. 이렇게 하면 이미지 파일 없이도 제목 옆에 관련 아이콘을 추가할 수 있습니다.

#### 3. 상태 컨테이너를 사용한 진행 피드백

API 호출이나 시간이 많이 걸리는 작업을 처리할 때 사용자에게 정보를 제공하는 것이 중요합니다. `st.status()`를 사용하여 실시간 진행 상황 업데이트를 표시하는 확장 가능한 컨테이너를 만듭니다.
```python
with st.status("Starting engine...", expanded=True) as status:
    
    # Step 1: Construct Prompt
    st.write(":material/psychology: Thinking: Analyzing constraints and tone...")
    time.sleep(2)
    
    prompt = f"""..."""
    
    # Step 2: Call API
    st.write(":material/flash_on: Generating: contacting Snowflake Cortex...")
    time.sleep(2)
    
    response = call_cortex_llm(prompt)
    
    # Step 3: Update Status to Complete
    st.write(":material/check_circle: Post generation completed!")
    status.update(label="Post Generated Successfully!", state="complete", expanded=False)
```

* **`st.status()`**: 여러 진행 단계를 표시할 수 있는 애니메이션 상태 컨테이너를 생성합니다. `expanded=True` 매개변수는 사용자가 실시간으로 진행 상황을 볼 수 있도록 합니다.
* **`status.update()`**: 처리가 완료되면 상태 라벨을 업데이트하고 `state="complete"`로 설정하여 녹색 체크 표시를 보여주고, `expanded=False`로 세부 정보를 축소하여 인터페이스를 깔끔하게 유지합니다.
* **`time.sleep(2)`**: 단계 사이에 2초의 짧은 지연을 추가합니다. 실제 API 호출은 빠르게 발생할 수 있지만(특히 캐싱의 경우), 이러한 일시 중지는 각 단계를 표시하여 더 투명하고 이해하기 쉬운 경험을 만듭니다. 이러한 지연이 없으면 상태 업데이트가 너무 빨리 지나가서 읽을 수 없을 수 있습니다. 프로덕션 앱에서는 이를 제거해도 됩니다.

상태 업데이트와 의도적인 지연의 조합은 불투명한 "로딩" 경험을 사용자 신뢰를 구축하는 유익한 단계별 프로세스로 변환합니다.

#### 4. 출력 그룹화 및 시각적 계층 구조

입력 및 처리 상태와 출력을 구별하기 위해 결과를 구성합니다.
```python
# Display Result
with st.container(border=True):
    st.subheader(":material/output: Generated post:")
    st.markdown(response)
```

* **`st.container(border=True)`**: 콘텐츠를 표시되는 테두리가 있는 상자로 래핑합니다. 이렇게 하면 "결과"를 별도의 카드로 시각적으로 그룹화하여 처리 로그나 입력 필드와 분리합니다.
* **`st.subheader(":material/output: ...")`**: 이 섹션에 최종 결과물이 포함되어 있음을 사용자에게 알리기 위해 고유한 아이콘을 사용합니다.

이 코드가 실행되면 컨트롤이 사이드바에 숨겨져 있고, 처리 중에 진행 상황 업데이트가 계속 정보를 제공하며, 최종 AI 출력이 깨끗한 테두리 카드로 표시되는 세련된 다크 테마 애플리케이션이 표시됩니다.

---

### :material/library_books: 리소스
- [Streamlit 테마 가이드](https://docs.streamlit.io/develop/concepts/configuration/theming)
- [config.toml 구성](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
- [st.sidebar 문서](https://docs.streamlit.io/develop/api-reference/layout/st.sidebar)
- [Streamlit의 Material 아이콘](https://docs.streamlit.io/develop/api-reference/media/st.image#using-material-icons)
