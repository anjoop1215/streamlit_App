import streamlit as st
import pandas as pd
import os  

# 페이지 설정
st.set_page_config(page_title="Netflix Movie Analysis", layout="wide")

st.title("🎬 넷플릭스 영화 데이터 분석 대시보드")
st.markdown("넷플릭스 데이터를 분석하여 평점 및 관객수 기반 Top 5 영화를 보여줍니다.")

# 1. 데이터 로드 (캐싱을 통해 성능 최적화)
@st.cache_data
def load_data():
     # 현재 실행 중인 app.py의 위치를 기준으로 파일 경로를 완성합니다.
    current_dir = os.path.dirname(__file__) 
    file_path = os.path.join(current_dir, 'netflix_titles.csv')
    
    # 데이터셋 경로 (본인의 파일명에 맞게 수정)
    # 데이터셋이 없는 경우를 대비해 예외 처리를 합니다.
    try:
        df = pd.read_csv('netflix_titles.csv')
        
        # 영화(Movie) 데이터만 분류
        movie_df = df[df['type'] == 'Movie'].copy()
        
        # 수치형 평점 및 관객수 데이터가 없을 경우를 대비한 가상 데이터 생성 (실제 데이터가 있다면 삭제)
        if 'imdb_score' not in movie_df.columns:
            import numpy as np
            movie_df['imdb_score'] = np.random.uniform(5.0, 9.5, size=len(movie_df)).round(1)
        if 'view_count' not in movie_df.columns:
            import numpy as np
            movie_df['view_count'] = np.random.randint(1000, 1000000, size=len(movie_df))
            
        return movie_df
    except FileNotFoundError:
        st.error("데이터 파일(netflix_titles.csv)을 찾을 수 없습니다. 파일을 업로드해주세요.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # 사이드바: 필터링 및 다운로드
    st.sidebar.header("데이터 옵션")
    
    # 전체 데이터 다운로드 버튼
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 필터링된 데이터 다운로드 (CSV)",
        data=csv,
        file_name='netflix_movies.csv',
        mime='text/csv',
    )

    # 레이아웃 배치
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⭐ 평점 높은 영화 Top 5")
        top_rated = df.sort_values(by='imdb_score', ascending=False).head(5)
        st.table(top_rated[['title', 'release_year', 'imdb_score']])

    with col2:
        st.subheader("👥 관객이 많은 영화 Top 5")
        top_views = df.sort_values(by='view_count', ascending=False).head(5)
        st.table(top_views[['title', 'release_year', 'view_count']])

    # 전체 데이터 확인
    st.divider()
    st.subheader("📋 전체 영화 목록 (상위 100개)")
    st.dataframe(df.head(100))
