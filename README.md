# 30 Days Of AI with Streamlit 🎈

**#30DaysOfAI**에 오신 것을 환영합니다 — [Streamlit](https://streamlit.io) 및 [Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)를 사용하여 AI 기반 애플리케이션을 배우고 구축 및 배포하는 포괄적인 30일 챌린지입니다.

## 🎯 무엇을 만들게 되나요?

챗봇부터 프로덕션 배포 가능한 RAG 시스템 및 지능형 에이전트까지 AI 앱 개발을 마스터하세요.

## 📏 챌린지 규칙

1. **매일 챌린지 접속하기**
   - 💻 코드: [github.com/streamlit/30daysofai](https://github.com/streamlit/30daysofai)
   - 🕹️ 지침: [30daysofai.streamlit.app](https://30daysofai.streamlit.app)

2. **앱 만들기** 매일 지침에 따라 앱을 만듭니다.

3. **진행 상황 공유하기** 소셜 미디어에 **#30DaysOfAI**와 함께 공유하세요.

4. **30일 모두 완료하기** 완료 후 [Chanin Nantasenamat](https://www.linkedin.com/in/chanin-nantasenamat/) 또는 [Jessica Smith](https://www.linkedin.com/in/jessica-s-095a861b3/)에게 DM을 보내세요.

5. **명예의 전당 등극** 🏆 (그리고 굿즈와 스티커를 받을 수도 있습니다!)

## 🚀 시작하기

### 필수 조건

- Python 3.11, 3.12 (3.13은 `llvmlite`, `numba`가 설치된 경우 작동)
- [Snowflake 무료 체험판](https://signup.snowflake.com/) (120일 크레딧 제공)
- 기본적인 Python 지식
- AI에 대한 열정! 🧠

### 로컬 환경

1. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   # 또는 uv 사용 시:
   uv pip install -e .
   ```

   `requirements.txt`:
   ```
   streamlit==1.52.0
   snowflake-ml-python==1.20.0
   snowflake-snowpark-python==1.44.0
   ```

2. **Snowflake 시크릿 구성**

   프로젝트 루트에 `.streamlit/secrets.toml` 파일을 생성하세요:
   ```toml
   [connections.snowflake]
   account = "your_account_identifier"
   user = "your_username"
   password = "your_password"
   role = "ACCOUNTADMIN"
   warehouse = "COMPUTE_WH"
   database = "your_database"
   schema = "your_schema"
   ```

   **중요:** `.streamlit/secrets.toml`을 `.gitignore`에 추가하세요 — 시크릿은 절대 커밋하지 마세요!

3. **앱 실행**
   ```bash
   cd app
   streamlit run day1.py
   ```

### Snowflake 환경

**프로덕션 환경 권장** — 시크릿 설정이 필요 없습니다!

1. Snowsight 탐색 → Streamlit
2. 새 Streamlit 앱 생성
3. `app/dayX.py`의 코드를 복사
4. Snowflake에서 실행

**장점:**
- ✅ 자동 인증
- ✅ 기본적으로 프로덕션 준비 완료
- ✅ Snowflake 보안 상속

## 📁 저장소 구조

```
30days-genai-master/
├── app/               # Streamlit 애플리케이션 (day1.py - day30.py)
├── md/                # 상세 레슨 문서 (day1.md - day30.md)
├── toml/              # 특정 레슨을 위한 설정 파일
├── pyproject.toml     # Python 의존성
└── README.md          # 이 파일
```

매일 포함되는 내용:
- **📱 앱 파일** (`app/dayX.py`) - 실행 가능한 전체 코드
- **📖 문서** (`md/dayX.md`) - 단계별 설명
- **💡 핵심 개념** - 배우게 될 내용과 중요한 이유


## 🛠️ 기술

- **[Streamlit](https://streamlit.io)** - ML 및 데이터 과학을 위한 빠르고 아름다운 웹 앱
- **[Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)** - LLM 함수 및 AI 서비스
- **[Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)** - 시맨틱 검색 서비스
- **[Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)** - 자연어를 SQL로 변환
- **[Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)** - 자율 AI 에이전트
- **[TruLens](https://www.trulens.org/)** - LLM 평가 및 관측 가능성

## 📚 리소스

### 공식 문서
- [Streamlit 문서](https://docs.streamlit.io/)
- [Streamlit 치트 시트](https://docs.streamlit.io/library/cheatsheet)
- [Snowflake Cortex AI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)
- [Cortex Agents 가이드](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [TruLens 문서](https://www.trulens.org/trulens_eval/getting_started/)

### 커뮤니티
- [Streamlit 갤러리](https://streamlit.io/gallery) - 영감 및 템플릿
- [Streamlit 커뮤니티 포럼](https://discuss.streamlit.io/) - 질문하기
- [Snowflake 커뮤니티](https://community.snowflake.com/) - 다른 사람들과 소통하기

## 🤝 기여하기

문제를 발견하셨나요? 기여는 언제나 환영합니다!

1. 이 저장소 포크하기
2. 기능 브랜치 생성 (`git checkout -b feature/improvement`)
3. 변경 사항 적용
4. 풀 리퀘스트 제출

---

# 시작할 준비가 되셨나요?

1. 🔧 **[연결 설정하기](md/day1.md)** - Snowflake 구성
2. 🚀 **[Day 1 시작하기](app/day1.py)** - 첫 번째 앱 만들기
3. 🎉 **진행 상황 공유하기** 소셜 미디어에 **#30DaysOfAI** 태그와 함께

**질문이 있으신가요?** 이슈를 열거나 [Streamlit 커뮤니티 포럼](https://discuss.streamlit.io/)에 참여하세요.
