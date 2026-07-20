import streamlit as st

st.set_page_config(page_title="YouTube 댓글 분석기", layout="wide")

st.title("🎬 YouTube 댓글 분석기")

st.info(
    "이 파일은 메인 app.py의 시작 템플릿입니다. "
    "이전 대화에서 설명한 전체 프로젝트(app.py, youtube_api.py, "
    "sentiment.py 등)가 함께 있어야 정상 동작합니다."
)

api_key = st.secrets.get("YOUTUBE_API_KEY")
if not api_key:
    st.error("Streamlit Secrets에 YOUTUBE_API_KEY가 설정되어 있지 않습니다.")
    st.stop()

url = st.text_input("유튜브 URL")
count = st.slider("댓글 개수", 100, 1000, 300, 100)

if url:
    st.video(url)

if st.button("분석 시작"):
    st.warning("이 템플릿만으로는 실행되지 않습니다. 나머지 모듈(youtube_api.py 등)이 필요합니다.")
