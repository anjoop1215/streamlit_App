# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium

from utils import (
    load_data,
    preprocess_data,
    get_cheapest_parking,
    filter_data,
)

from map_utils import create_map

st.set_page_config(
    page_title="서울시 공영주차장 안내",
    page_icon="🅿️",
    layout="wide",
)

st.title("🅿️ 서울시 공영주차장 안내 시스템")

st.markdown(
"""
공영주차장 정보를 지도에서 확인하고
자치구별 가장 저렴한 주차장을 추천합니다.
"""
)

#######################################################
# Sidebar
#######################################################

st.sidebar.header("📂 데이터")

uploaded_file = st.sidebar.file_uploader(
    "CSV 업로드",
    type=["csv"]
)

if uploaded_file is not None:
    df = load_data(uploaded_file)

else:
    df = load_data("서울시 공영주차장 안내 정보(2).csv")

df = preprocess_data(df)

#######################################################
# 검색
#######################################################

keyword = st.sidebar.text_input(
    "🔍 주차장 검색"
)

#######################################################
# 자치구
#######################################################

districts = sorted(df["자치구"].dropna().unique())

selected_district = st.sidebar.selectbox(
    "자치구 선택",
    ["전체"] + districts
)

#######################################################
# 무료
#######################################################

free_only = st.sidebar.checkbox(
    "무료 주차장만"
)

#######################################################
# 주말운영
#######################################################

weekend_only = st.sidebar.checkbox(
    "주말 운영만"
)

#######################################################
# 필터
#######################################################

filtered = filter_data(
    df,
    district=selected_district,
    keyword=keyword,
    free_only=free_only,
    weekend_only=weekend_only,
)

#######################################################
# KPI
#######################################################

c1,c2,c3,c4 = st.columns(4)

with c1:
    st.metric(
        "전체",
        len(filtered)
    )

with c2:

    st.metric(
        "무료",
        len(filtered[
            filtered["무료"]
        ])
    )

with c3:

    st.metric(
        "주말 운영",
        len(filtered[
            filtered["주말운영"]
        ])
    )

with c4:

    cheapest = get_cheapest_parking(filtered)

    if cheapest is not None:

        st.metric(
            "최저요금",
            f"{cheapest['기본요금']}원"
        )

#######################################################
# 추천
#######################################################

st.subheader("💰 가장 저렴한 공영주차장")

cheapest = get_cheapest_parking(filtered)

if cheapest is not None:

    st.success(
        f"""
        추천 주차장 : {cheapest['주차장명']}

        주소 : {cheapest['주소']}

        기본요금 : {cheapest['기본요금']}원
        """
    )

else:

    st.warning("검색 결과가 없습니다.")

#######################################################
# 지도
#######################################################

st.subheader("🗺️ 지도")

m = create_map(filtered)

st_folium(
    m,
    width=None,
    height=650
)
#######################################################
# 통계
#######################################################

st.subheader("📊 자치구별 공영주차장 수")

district_count = (
    filtered.groupby("자치구")
    .size()
    .reset_index(name="개수")
)

if len(district_count) > 0:

    fig = px.bar(
        district_count,
        x="자치구",
        y="개수",
        color="개수",
        title="자치구별 공영주차장 수",
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

#######################################################
# 평균 요금
#######################################################

st.subheader("💰 자치구별 평균 기본요금")

price_df = filtered.copy()

price_df = price_df[
    price_df["기본요금"] > 0
]

if len(price_df):

    avg_price = (
        price_df.groupby("자치구")["기본요금"]
        .mean()
        .reset_index()
    )

    fig2 = px.bar(
        avg_price,
        x="자치구",
        y="기본요금",
        color="기본요금",
        title="평균 기본요금"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

#######################################################
# 무료 / 유료 비율
#######################################################

st.subheader("🆓 무료 주차장 비율")

pie = (
    filtered["무료"]
    .replace({
        True: "무료",
        False: "유료"
    })
    .value_counts()
    .reset_index()
)

pie.columns = ["구분", "개수"]

fig3 = px.pie(
    pie,
    names="구분",
    values="개수",
    hole=0.45
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

#######################################################
# 데이터 테이블
#######################################################

st.subheader("📄 공영주차장 목록")

show_columns = [
    "주차장명",
    "자치구",
    "주소",
    "기본요금",
    "무료",
    "주말운영",
]

exist_cols = [
    c for c in show_columns
    if c in filtered.columns
]

st.dataframe(
    filtered[exist_cols],
    use_container_width=True,
    height=500
)

#######################################################
# 다운로드
#######################################################

csv = filtered.to_csv(
    index=False,
    encoding="utf-8-sig"
).encode("utf-8-sig")

st.download_button(
    label="📥 CSV 다운로드",
    data=csv,
    file_name="parking_result.csv",
    mime="text/csv"
)

#######################################################
# Footer
#######################################################

st.markdown("---")

st.caption(
    "서울시 공영주차장 정보 · Streamlit Dashboard"
)
import pandas as pd
import numpy as np
import re


# -----------------------------
# CSV 불러오기
# -----------------------------
def load_data(file):
    try:
        return pd.read_csv(file, encoding="cp949")
    except:
        try:
            return pd.read_csv(file, encoding="utf-8")
        except:
            return pd.read_csv(file, encoding="utf-8-sig")


# -----------------------------
# 컬럼 자동 찾기
# -----------------------------
def find_column(df, keywords):

    for col in df.columns:
        for key in keywords:
            if key in col:
                return col

    return None


# -----------------------------
# 숫자 변환
# -----------------------------
def to_number(x):

    if pd.isna(x):
        return 0

    x = str(x)

    x = re.sub(r"[^0-9]", "", x)

    if x == "":
        return 0

    return int(x)


# -----------------------------
# True False 변환
# -----------------------------
def yes_no(value):

    if pd.isna(value):
        return False

    value = str(value)

    yes = [
        "Y",
        "YES",
        "예",
        "가능",
        "운영",
        "무료",
        "O",
        "TRUE",
        "1"
    ]

    for y in yes:
        if y in value.upper():
            return True

    return False


# -----------------------------
# 전처리
# -----------------------------
def preprocess_data(df):

    parking = find_column(df, ["주차장"])
    address = find_column(df, ["주소"])
    district = find_column(df, ["자치구"])
    lat = find_column(df, ["위도"])
    lon = find_column(df, ["경도"])

    if lat is None:
        lat = find_column(df, ["Y"])

    if lon is None:
        lon = find_column(df, ["X"])

    fee = find_column(df, ["기본", "요금"])

    weekend = find_column(df, ["주말"])

    rename = {}

    if parking:
        rename[parking] = "주차장명"

    if address:
        rename[address] = "주소"

    if district:
        rename[district] = "자치구"

    if lat:
        rename[lat] = "위도"

    if lon:
        rename[lon] = "경도"

    if fee:
        rename[fee] = "기본요금"

    if weekend:
        rename[weekend] = "주말운영"

    df = df.rename(columns=rename)

    df["기본요금"] = df["기본요금"].apply(to_number)

    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

    df = df.dropna(subset=["위도", "경도"])

    df["무료"] = df["기본요금"] == 0

    if "주말운영" in df.columns:
        df["주말운영"] = df["주말운영"].apply(yes_no)
    else:
        df["주말운영"] = False

    df = df.reset_index(drop=True)

    return df


# -----------------------------
# 필터
# -----------------------------
def filter_data(
        df,
        district="전체",
        keyword="",
        free_only=False,
        weekend_only=False):

    result = df.copy()

    if district != "전체":
        result = result[
            result["자치구"] == district
        ]

    if keyword != "":

        result = result[
            result["주차장명"]
            .astype(str)
            .str.contains(keyword)
        ]

    if free_only:
        result = result[
            result["무료"]
        ]

    if weekend_only:
        result = result[
            result["주말운영"]
        ]

    return result


# -----------------------------
# 최저 요금
# -----------------------------
def get_cheapest_parking(df):

    if len(df) == 0:
        return None

    idx = df["기본요금"].idxmin()

    return df.loc[idx]

import folium
from folium.plugins import MarkerCluster


# ----------------------------------------
# 요금에 따른 마커 색상
# ----------------------------------------
def get_marker_color(fee):

    try:
        fee = int(fee)
    except:
        fee = 0

    if fee == 0:
        return "green"

    elif fee <= 1000:
        return "blue"

    elif fee <= 3000:
        return "orange"

    else:
        return "red"


# ----------------------------------------
# 지도 생성
# ----------------------------------------
def create_map(df):

    # 서울 중심
    center_lat = 37.5665
    center_lon = 126.9780

    if len(df):

        center_lat = df["위도"].mean()
        center_lon = df["경도"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        control_scale=True,
        tiles="OpenStreetMap"
    )

    marker_cluster = MarkerCluster().add_to(m)

    for _, row in df.iterrows():

        name = row.get("주차장명", "-")
        address = row.get("주소", "-")
        district = row.get("자치구", "-")
        fee = row.get("기본요금", 0)
        free = "무료" if row.get("무료", False) else "유료"
        weekend = "운영" if row.get("주말운영", False) else "미운영"

        tooltip = f"""
<b>{name}</b><br>
주소 : {address}<br>
기본요금 : {fee}원<br>
무료 : {free}<br>
주말 : {weekend}
"""

        popup = f"""
<h4>{name}</h4>

<table style="width:320px">

<tr>
<td><b>자치구</b></td>
<td>{district}</td>
</tr>

<tr>
<td><b>주소</b></td>
<td>{address}</td>
</tr>

<tr>
<td><b>기본요금</b></td>
<td>{fee}원</td>
</tr>

<tr>
<td><b>무료 여부</b></td>
<td>{free}</td>
</tr>

<tr>
<td><b>주말 운영</b></td>
<td>{weekend}</td>
</tr>

</table>
"""

        color = get_marker_color(fee)

        folium.Marker(
            location=[
                row["위도"],
                row["경도"]
            ],

            tooltip=folium.Tooltip(
                tooltip,
                sticky=True
            ),

            popup=folium.Popup(
                popup,
                max_width=350
            ),

            icon=folium.Icon(
                color=color,
                icon="car",
                prefix="fa"
            )

        ).add_to(marker_cluster)

    # 범례
    legend = """
<div style="
position: fixed;
bottom: 50px;
left: 50px;
width: 180px;
background:white;
border:2px solid grey;
z-index:9999;
padding:10px;
font-size:13px;
">

<b>요금 색상</b><br><br>

🟢 무료<br>

🔵 1,000원 이하<br>

🟠 3,000원 이하<br>

🔴 3,000원 초과

</div>
"""

    m.get_root().html.add_child(
        folium.Element(legend)
    )

    return m
# ==================================================
# 필터 적용
# ==================================================

filtered = df.copy()

# 자치구 필터
if selected_gu != "전체":
    filtered = filtered[
        filtered["자치구"] == selected_gu
    ]

# 검색
if keyword.strip() != "":
    filtered = filtered[
        filtered["주차장명"]
        .astype(str)
        .str.contains(keyword, case=False, na=False)
    ]

# 무료 필터
if free_only:
    filtered = filtered[
        filtered["무료"] == True
    ]

# 주말 운영 필터
if weekend_only:
    filtered = filtered[
        filtered["주말운영"] == True
    ]

# ==================================================
# KPI
# ==================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "주차장 수",
        len(filtered)
    )

with c2:
    st.metric(
        "무료",
        int(filtered["무료"].sum())
    )

with c3:
    st.metric(
        "주말 운영",
        int(filtered["주말운영"].sum())
    )

with c4:

    if len(filtered):

        st.metric(
            "최저요금",
            f"{filtered['기본요금'].min():,}원"
        )

    else:

        st.metric(
            "최저요금",
            "-"
        )

# ==================================================
# 지도 생성
# ==================================================

st.subheader("🗺️ 공영주차장 지도")

if len(filtered):

    center = [
        filtered["위도"].mean(),
        filtered["경도"].mean()
    ]

else:

    center = [
        37.5665,
        126.9780
    ]

m = folium.Map(
    location=center,
    zoom_start=11,
    control_scale=True
)

cluster = MarkerCluster().add_to(m)

# ==================================================
# 마커 색상
# ==================================================

def marker_color(fee):

    if fee == 0:
        return "green"

    elif fee <= 1000:
        return "blue"

    elif fee <= 3000:
        return "orange"

    return "red"

# ==================================================
# 마커 추가
# ==================================================

for _, row in filtered.iterrows():

    fee = int(row["기본요금"])

    tooltip = f"""
<b>{row['주차장명']}</b><br>
📍 {row['주소']}<br>
💰 기본요금 : {fee:,}원<br>
🆓 {'무료' if row['무료'] else '유료'}<br>
📅 {'주말 운영' if row['주말운영'] else '주말 미운영'}
"""

    popup = f"""
<h4>{row['주차장명']}</h4>

<table style='width:320px;'>

<tr>
<td><b>주소</b></td>
<td>{row['주소']}</td>
</tr>

<tr>
<td><b>자치구</b></td>
<td>{row['자치구']}</td>
</tr>

<tr>
<td><b>기본요금</b></td>
<td>{fee:,}원</td>
</tr>

<tr>
<td><b>무료</b></td>
<td>{"예" if row["무료"] else "아니오"}</td>
</tr>

<tr>
<td><b>주말운영</b></td>
<td>{"운영" if row["주말운영"] else "미운영"}</td>
</tr>

</table>
"""

    folium.Marker(

        location=[
            row["위도"],
            row["경도"]
        ],

        tooltip=folium.Tooltip(
            tooltip,
            sticky=True
        ),

        popup=folium.Popup(
            popup,
            max_width=350
        ),

        icon=folium.Icon(
            color=marker_color(fee),
            icon="car",
            prefix="fa"
        )

    ).add_to(cluster)

# ==================================================
# 범례
# ==================================================

legend = """
<div style="
position:fixed;
bottom:40px;
left:40px;
width:180px;
background:white;
border:2px solid gray;
padding:10px;
z-index:9999;
font-size:13px;
">

<b>요금 색상</b><br><br>

🟢 무료<br>

🔵 1,000원 이하<br>

🟠 3,000원 이하<br>

🔴 3,000원 초과

</div>
"""

m.get_root().html.add_child(
    folium.Element(legend)
)

st_folium(
    m,
    width=None,
    height=650
)
# ==================================================
# 가장 저렴한 주차장 추천
# ==================================================

st.subheader("🏆 추천 공영주차장")

if len(filtered):

    cheapest = filtered.sort_values(
        by="기본요금"
    ).iloc[0]

    st.success(
        f"""
### ✅ 추천 결과

**주차장명**

{cheapest['주차장명']}

**주소**

{cheapest['주소']}

**기본요금**

{cheapest['기본요금']:,}원

**무료**

{"예" if cheapest["무료"] else "아니오"}

**주말운영**

{"운영" if cheapest["주말운영"] else "미운영"}
"""
    )

else:

    st.warning("조건에 맞는 주차장이 없습니다.")

# ==================================================
# TOP5 추천
# ==================================================

st.subheader("🥇 가장 저렴한 TOP5")

if len(filtered):

    top5 = (
        filtered
        .sort_values("기본요금")
        .head(5)
    )

    st.dataframe(

        top5[
            [
                "주차장명",
                "자치구",
                "주소",
                "기본요금",
                "무료",
                "주말운영"
            ]
        ],

        use_container_width=True

    )

# ==================================================
# 자치구별 개수
# ==================================================

st.subheader("📊 자치구별 공영주차장 개수")

district = (

    filtered

    .groupby("자치구")

    .size()

    .reset_index(name="개수")

)

if len(district):

    fig = px.bar(

        district,

        x="자치구",

        y="개수",

        color="개수",

        title="자치구별 공영주차장 수"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )

# ==================================================
# 평균 요금
# ==================================================

st.subheader("💰 자치구별 평균 기본요금")

price = (

    filtered

    .groupby("자치구")["기본요금"]

    .mean()

    .reset_index()

)

if len(price):

    fig2 = px.bar(

        price,

        x="자치구",

        y="기본요금",

        color="기본요금",

        title="평균 기본요금"

    )

    st.plotly_chart(

        fig2,

        use_container_width=True

    )

# ==================================================
# 무료 비율
# ==================================================

st.subheader("🆓 무료 / 유료")

pie = (

    filtered["무료"]

    .replace(

        {

            True: "무료",

            False: "유료"

        }

    )

    .value_counts()

    .reset_index()

)

pie.columns = [

    "구분",

    "개수"

]

fig3 = px.pie(

    pie,

    names="구분",

    values="개수",

    hole=0.45

)

st.plotly_chart(

    fig3,

    use_container_width=True

)

# ==================================================
# 전체 데이터
# ==================================================

st.subheader("📄 공영주차장 목록")

columns = [

    "주차장명",

    "자치구",

    "주소",

    "기본요금",

    "무료",

    "주말운영"

]

st.dataframe(

    filtered[columns],

    use_container_width=True,

    height=500

)

# ==================================================
# CSV 다운로드
# ==================================================

csv = filtered.to_csv(

    index=False,

    encoding="utf-8-sig"

).encode("utf-8-sig")

st.download_button(

    "📥 CSV 다운로드",

    csv,

    file_name="parking_result.csv",

    mime="text/csv"

)

# ==================================================
# Footer
# ==================================================

st.markdown("---")

st.caption(

    "서울시 공영주차장 정보 서비스 | Streamlit"

)
