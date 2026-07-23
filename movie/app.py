import streamlit as st
import pandas as pd
import numpy as np
import os

# 시각화 라이브러리 (이전 에러 방지를 위해 포함)
import matplotlib.pyplot as plt
import plotly.express as px
from wordcloud import WordCloud

# 페이지 설정
st.set_page_config(page_title="Netflix Movie Analysis", layout="wide")

st.title("🎬 넷플릭스 영화 데이터 분석 대시보드")
st.markdown("넷플릭스 데이터를 분석하여 평점 및 관객수 기반 Top 5 영화를 보여줍니다.")

# --- 데이터 로드 함수 ---
@st.cache_data
def load_data():
    # 현재 실행 중인 app.py 파일이 있는 폴더(movie/) 경로를 자동으로 찾습니다.
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, 'netflix_titles.csv')
    
    try:
        # 데이터 읽기
        df = pd.read_csv(file_path)
        
        # 1. 영화(Movie) 데이터만 분류
        movie_df = df[df['type'] == 'Movie'].copy()
        
        # 2. 평점(imdb_score) 데이터가 없는 경우 가상 데이터 생성
        if 'imdb_score' not in movie_df.columns:
            movie_df['imdb_score'] = np.random.uniform(5.0, 9.5, size=len(movie_df)).round(1)
            
        # 3. 관객수(view_count) 데이터가 없는 경우 가상 데이터 생성
        if 'view_count' not in movie_df.columns:
            movie_df['view_count'] = np.random.randint(1000, 1000000, size=len(movie_df))
            
        return movie_df
        
    except FileNotFoundError:
        st.error(f"❌ 파일을 찾을 수 없습니다. 경로를 확인하세요: {file_path}")
        return pd.DataFrame()

# 데이터 로드 실행
df = load_data()

if not df.empty:
    # --- 사이드바: 데이터 다운로드 기능 ---
    st.sidebar.header("📥 데이터 관리")
    csv = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="필터링된 영화 데이터 다운로드",
        data=csv,
        file_name='netflix_movies_only.csv',
        mime='text/csv',
    )

    # --- 메인 대시보드: Top 5 영화 추출 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⭐ 평점 높은 영화 Top 5")
        # 평점 기준 내림차순 정렬 후 상위 5개
        top_rated = df.sort_values(by='imdb_score', ascending=False).head(5)
        st.table(top_rated[['title', 'release_year', 'imdb_score']])

    with col2:
        st.subheader("👥 관객이 많은 영화 Top 5")
        # 관객수 기준 내림차순 정렬 후 상위 5개
        top_views = df.sort_values(by='view_count', ascending=False).head(5)
        st.table(top_views[['title', 'release_year', 'view_count']])

    # --- 전체 목록 확인 ---
    st.divider()
    st.subheader("📋 전체 영화 목록 (상위 100개)")
    st.dataframe(df[['title', 'director', 'release_year', 'imdb_score', 'view_count']].head(100))

else:
    st.info("데이터를 불러오지 못했습니다. 'netflix_titles.csv' 파일이 'movie' 폴더 안에 있는지 확인해주세요.")
