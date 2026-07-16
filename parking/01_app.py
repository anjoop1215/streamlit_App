import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import plotly.express as px
import numpy as np

st.set_page_config(
    page_title="서울시 공영주차장 검색",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 서울시 공영주차장 검색 서비스")

st.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "CSV 업로드",
    type=["csv"]
)

DEFAULT_FILE = "서울시 공영주차장 안내 정보(1).csv"

@st.cache_data
def load_data(file):

    try:
        df = pd.read_csv(file, encoding="cp949")
    except:
        try:
            df = pd.read_csv(file, encoding="utf-8")
        except:
            df = pd.read_csv(file, encoding="euc-kr")

    return df

if uploaded_file is None:
    df = load_data(DEFAULT_FILE)
else:
    df = load_data(uploaded_file)

#########################################################################
# 컬럼 자동 인식
#########################################################################

def find_column(df, keywords):

    for c in df.columns:
        name = c.replace(" ", "")

        for k in keywords:
            if k in name:
                return c

    return None


lat_col = find_column(df, ["위도", "LAT"])
lon_col = find_column(df, ["경도", "LNG", "LON"])
name_col = find_column(df, ["주차장명", "주차장"])
addr_col = find_column(df, ["주소"])
basic_col = find_column(df, ["기본요금", "기본주차요금"])
add_col = find_column(df, ["추가요금"])
free_col = find_column(df, ["무료"])
weekday_col = find_column(df, ["평일"])
sat_col = find_column(df, ["토요일"])
holiday_col = find_column(df, ["공휴일"])
open_col = find_column(df, ["운영시간"])

#########################################################################
# 주소에서 자치구 추출
#########################################################################

def get_gu(address):

    try:

        return str(address).split()[0]

    except:

        return "기타"

df["자치구"] = df[addr_col].apply(get_gu)

#########################################################################
# 숫자 변환
#########################################################################

def to_number(x):

    try:

        x = str(x)

        x = x.replace(",", "")

        x = x.replace("원", "")

        return float(x)

    except:

        return np.nan


if basic_col:

    df["기본요금"] = df[basic_col].apply(to_number)

else:

    df["기본요금"] = np.nan


#########################################################################
# 사이드바
#########################################################################

st.sidebar.header("검색 옵션")

gu_list = ["전체"] + sorted(df["자치구"].unique())

selected_gu = st.sidebar.selectbox(
    "자치구 선택",
    gu_list
)

keyword = st.sidebar.text_input(
    "주차장 검색"
)

free_only = st.sidebar.checkbox(
    "무료만 보기"
)

price = st.sidebar.slider(
    "최대 기본요금",
    0,
    int(df["기본요금"].fillna(5000).max()),
    int(df["기본요금"].fillna(5000).max())
)

#########################################################################
# 필터
#########################################################################

filtered = df.copy()

if selected_gu != "전체":

    filtered = filtered[
        filtered["자치구"] == selected_gu
    ]

if keyword != "":

    filtered = filtered[
        filtered[name_col].str.contains(
            keyword,
            na=False
        )
    ]

filtered = filtered[
    filtered["기본요금"].fillna(0) <= price
]

if free_only and free_col is not None:

    filtered = filtered[
        filtered[free_col].astype(str).str.contains("무료|Y")
    ]
#########################################################################
# 지도 생성
#########################################################################

# 위도/경도 숫자로 변환
filtered[lat_col] = pd.to_numeric(filtered[lat_col], errors="coerce")
filtered[lon_col] = pd.to_numeric(filtered[lon_col], errors="coerce")

filtered = filtered.dropna(subset=[lat_col, lon_col])

if len(filtered) == 0:
    st.warning("조건에 맞는 주차장이 없습니다.")
    st.stop()

#########################################################################
# 지도 중심
#########################################################################

center_lat = filtered[lat_col].mean()
center_lon = filtered[lon_col].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=12,
    tiles="OpenStreetMap"
)

cluster = MarkerCluster().add_to(m)

#########################################################################
# 마커 색상
#########################################################################

def marker_color(price):

    try:

        if price == 0:
            return "green"

        elif price <= 1000:
            return "blue"

        elif price <= 3000:
            return "orange"

        else:
            return "red"

    except:

        return "gray"

#########################################################################
# 마커 생성
#########################################################################

for _, row in filtered.iterrows():

    name = row[name_col]

    addr = row[addr_col]

    basic = row.get("기본요금", "")

    add_fee = row[add_col]

    free = row[free_col]

    sat = row[sat_col]

    holiday = row[holiday_col]

    popup = f"""
    <b>{name}</b><br>

    주소 : {addr}<br>

    기본요금 : {basic}원<br>

    추가요금 : {add_fee}원<br>

    무료 : {free}<br>

    토요일 : {sat}<br>

    공휴일 : {holiday}<br>

    """

    folium.CircleMarker(

        location=[row[lat_col], row[lon_col]],

        radius=6,

        color=marker_color(row["기본요금"]),

        fill=True,

        fill_opacity=0.9,

        popup=popup,

        tooltip=name

    ).add_to(cluster)

#########################################################################
# 지도 출력
#########################################################################

st.subheader("🗺️ 공영주차장 지도")

st_folium(
    m,
    width=None,
    height=650
)

#########################################################################
# 추천 주차장
#########################################################################

st.markdown("---")

st.subheader("🏆 추천 주차장")

cheap = filtered.sort_values(
    "기본요금"
)

top5 = cheap.head(5)

for i, (_, row) in enumerate(top5.iterrows(), start=1):

    with st.expander(f"{i}위 : {row[name_col]}"):

        st.write("주소 :", row[addr_col])

        st.write("기본요금 :", row["기본요금"], "원")

        st.write("추가요금 :", row[add_col], "원")

        st.write("총 주차면 :", row["총 주차면"])

        st.write("무료 :", row[free_col])

        st.write("야간 무료 :", row["야간무료개방여부명"])

#########################################################################
# 데이터 테이블
#########################################################################

st.markdown("---")

st.subheader("📄 검색 결과")

st.dataframe(
    filtered,
    use_container_width=True
)
#########################################################################
# 통계
#########################################################################

st.markdown("---")
st.header("📊 통계")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "총 주차장",
    len(filtered)
)

col2.metric(
    "평균 기본요금",
    f"{filtered['기본요금'].mean():.0f} 원"
)

col3.metric(
    "최저요금",
    f"{filtered['기본요금'].min():.0f} 원"
)

col4.metric(
    "최고요금",
    f"{filtered['기본요금'].max():.0f} 원"
)

#########################################################################
# 자치구별 평균요금
#########################################################################

st.markdown("---")

st.subheader("자치구별 평균 기본요금")

gu_price = (
    filtered
    .groupby("자치구")["기본요금"]
    .mean()
    .reset_index()
)

fig = px.bar(
    gu_price,
    x="자치구",
    y="기본요금",
    color="기본요금",
    text_auto=".0f"
)

fig.update_layout(
    height=500
)

st.plotly_chart(
    fig,
    use_container_width=True
)

#########################################################################
# 요금 분포
#########################################################################

st.subheader("기본요금 분포")

fig2 = px.histogram(
    filtered,
    x="기본요금",
    nbins=20
)

fig2.update_layout(
    height=400
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

#########################################################################
# 무료 주차장 개수
#########################################################################

if free_col is not None:

    st.subheader("무료 여부")

    free_count = (
        filtered[free_col]
        .astype(str)
        .str.contains("무료|Y")
        .value_counts()
    )

    fig3 = px.pie(
        names=["유료", "무료"][:len(free_count)],
        values=free_count.values
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

#########################################################################
# 가장 추천하는 주차장
#########################################################################

st.markdown("---")

st.header("⭐ AI 추천")

recommend = filtered.sort_values(
    "기본요금"
).iloc[0]

st.success(
    f"""
추천 주차장

🏆 {recommend[name_col]}

📍 {recommend[addr_col]}

💰 기본요금 : {recommend['기본요금']}원
"""
)

#########################################################################
# CSV 다운로드
#########################################################################

csv = filtered.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    "📥 검색 결과 다운로드",
    csv,
    "parking_result.csv",
    "text/csv"
)

#########################################################################
# Footer
#########################################################################

st.markdown("---")

st.caption(
    "서울시 공영주차장 검색 서비스 | Streamlit + Folium + Plotly"
)
#########################################################################
# 지도 범례
#########################################################################

st.markdown("---")
st.subheader("🗺️ 지도 범례")

c1, c2, c3, c4 = st.columns(4)

c1.markdown("🟢 **무료**")
c2.markdown("🔵 **1000원 이하**")
c3.markdown("🟠 **3000원 이하**")
c4.markdown("🔴 **3000원 초과**")

#########################################################################
# 운영시간 정보
#########################################################################

if open_col is not None:

    st.markdown("---")

    st.subheader("운영시간")

    open_df = (
        filtered[[name_col, open_col]]
        .rename(columns={
            name_col: "주차장",
            open_col: "운영시간"
        })
    )

    st.dataframe(
        open_df,
        use_container_width=True,
        hide_index=True
    )

#########################################################################
# 주소 검색 결과
#########################################################################

st.markdown("---")

st.subheader("주소")

address_df = filtered[
    [name_col, addr_col]
]

st.dataframe(
    address_df,
    use_container_width=True,
    hide_index=True
)

#########################################################################
# 요금 순위
#########################################################################

st.markdown("---")

st.subheader("💰 요금 순위 TOP10")

rank = (
    filtered
    .sort_values("기본요금")
    [[name_col, addr_col, "기본요금"]]
    .head(10)
)

rank.columns = [
    "주차장",
    "주소",
    "기본요금"
]

st.table(rank)

#########################################################################
# 전체 데이터 보기
#########################################################################

with st.expander("전체 데이터 보기"):

    st.dataframe(
        filtered,
        use_container_width=True
    )

#########################################################################
# 검색 결과 개수
#########################################################################

st.info(
    f"검색 결과 : {len(filtered)}개"
)

#########################################################################
# 개발 정보
#########################################################################

st.markdown("---")

st.caption(
"""
서울시 공영주차장 검색 서비스

• Streamlit

• Folium

• Plotly

• Pandas

데이터 : 서울 열린데이터광장
"""
)
