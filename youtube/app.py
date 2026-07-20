import re
import requests
import tempfile
from pathlib import Path

import streamlit as st


# -------------------------------------------------
# URL
# -------------------------------------------------

def extract_video_id(url: str):

    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"embed/([a-zA-Z0-9_-]{11})",
        r"shorts/([a-zA-Z0-9_-]{11})"
    ]

    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)

    return None


# -------------------------------------------------
# Font
# -------------------------------------------------

@st.cache_resource
def download_font():

    github_font = (
        "https://raw.githubusercontent.com/"
        "YOUR_GITHUB_NAME/"
        "YOUR_REPOSITORY/main/fonts/NanumGothic.ttf"
    )

    font_path = Path(tempfile.gettempdir()) / "NanumGothic.ttf"

    if not font_path.exists():

        r = requests.get(github_font, timeout=20)

        if r.status_code == 200:

            font_path.write_bytes(r.content)

    return str(font_path)


# -------------------------------------------------
# Text Cleaning
# -------------------------------------------------

def clean_text(text):

    text = re.sub(r"http\S+", "", text)

    text = re.sub(r"@[A-Za-z0-9_]+", "", text)

    text = re.sub(r"#", "", text)

    text = re.sub(r"[^\w\s가-힣]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# -------------------------------------------------
# Number
# -------------------------------------------------

def format_number(num):

    try:
        num = int(num)
    except:
        return num

    if num >= 100000000:
        return f"{num/100000000:.1f}억"

    if num >= 10000:
        return f"{num/10000:.1f}만"

    return f"{num:,}"


# -------------------------------------------------
# Progress
# -------------------------------------------------

def progress_message(msg):

    st.toast(msg, icon="📊")

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import streamlit as st
import pandas as pd


# -------------------------------------------------------
# YouTube API
# -------------------------------------------------------

@st.cache_resource
def get_youtube():

    return build(
        "youtube",
        "v3",
        developerKey=st.secrets["YOUTUBE_API_KEY"]
    )


youtube = get_youtube()
# -------------------------------------------------------
# Video Info
# -------------------------------------------------------

def get_video_info(video_id):

    response = youtube.videos().list(

        part="snippet,statistics",

        id=video_id

    ).execute()

    if len(response["items"]) == 0:

        return None

    item = response["items"][0]

    snippet = item["snippet"]

    statistics = item["statistics"]

    info = {

        "title":

            snippet.get("title",""),

        "channel":

            snippet.get("channelTitle",""),

        "published":

            snippet.get("publishedAt",""),

        "thumbnail":

            snippet["thumbnails"]["high"]["url"],

        "views":

            int(statistics.get("viewCount",0)),

        "likes":

            int(statistics.get("likeCount",0)),

        "comments":

            int(statistics.get("commentCount",0))

    }

    return info
  # -------------------------------------------------------
# Comment Page
# -------------------------------------------------------

def get_comment_page(

    video_id,

    page_token=None

):

    response = youtube.commentThreads().list(

        part="snippet",

        videoId=video_id,

        maxResults=100,

        pageToken=page_token,

        order="time",

        textFormat="plainText"

    ).execute()

    return response
  # -------------------------------------------------------
# Extract Comment
# -------------------------------------------------------

def extract_comment(item):

    snippet = item["snippet"]["topLevelComment"]["snippet"]

    return {

        "author":

            snippet.get("authorDisplayName",""),

        "comment":

            snippet.get("textDisplay",""),

        "like":

            snippet.get("likeCount",0),

        "published":

            snippet.get("publishedAt",""),

        "updated":

            snippet.get("updatedAt","")

    }
  # -------------------------------------------------------
# Safe Execute
# -------------------------------------------------------

def safe_execute(func,*args,**kwargs):

    try:

        return func(*args,**kwargs)

    except HttpError as e:

        st.error(f"YouTube API 오류\n\n{e}")

        return None

    except Exception as e:

        st.error(e)

        return None

# -------------------------------------------------------
# Get Comments
# -------------------------------------------------------

@st.cache_data(show_spinner=False)
def get_comments(video_id, max_comments=300):

    comments = []

    next_page = None

    progress = st.progress(0)

    status = st.empty()

    while len(comments) < max_comments:

        response = safe_execute(
            get_comment_page,
            video_id,
            next_page
        )

        if response is None:
            break

        items = response.get("items", [])

        if len(items) == 0:
            break

        for item in items:

            try:

                comment = extract_comment(item)

                comments.append(comment)

            except Exception:
                continue

            if len(comments) >= max_comments:
                break

        next_page = response.get("nextPageToken")

        progress.progress(
            min(
                len(comments) / max_comments,
                1.0
            )
        )

        status.write(
            f"댓글 수집 중... {len(comments)} / {max_comments}"
        )

        if next_page is None:
            break

    progress.empty()
    status.empty()

    df = pd.DataFrame(comments)

    if len(df) == 0:
        return df

    df["published"] = pd.to_datetime(
        df["published"]
    )

    df["updated"] = pd.to_datetime(
        df["updated"]
    )

    df["date"] = df["published"].dt.date

    df["hour"] = df["published"].dt.hour

    df["weekday"] = df["published"].dt.day_name()

    return df


# -------------------------------------------------------
# Statistics
# -------------------------------------------------------

def comment_statistics(df):

    if len(df) == 0:

        return {

            "count":0,

            "avg_like":0,

            "max_like":0

        }

    return {

        "count":len(df),

        "avg_like":round(df["like"].mean(),2),

        "max_like":df["like"].max()

    }


# -------------------------------------------------------
# Top Comments
# -------------------------------------------------------

def get_top_comments(

    df,

    top_n=20

):

    if len(df)==0:

        return df

    return (

        df

        .sort_values(

            "like",

            ascending=False

        )

        .head(top_n)

        .reset_index(drop=True)

    )

# -------------------------------------------------------
# Search Comments
# -------------------------------------------------------

def search_comments(df, keyword):

    if df.empty:
        return df

    if keyword is None or keyword.strip() == "":
        return df

    keyword = keyword.strip()

    return df[
        df["comment"].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]


# -------------------------------------------------------
# Filter by Date
# -------------------------------------------------------

def filter_by_date(

    df,

    start_date=None,

    end_date=None

):

    if df.empty:
        return df

    result = df.copy()

    if start_date is not None:
        result = result[
            result["published"].dt.date >= start_date
        ]

    if end_date is not None:
        result = result[
            result["published"].dt.date <= end_date
        ]

    return result


# -------------------------------------------------------
# Filter by Hour
# -------------------------------------------------------

def filter_by_hour(

    df,

    start_hour=0,

    end_hour=23

):

    if df.empty:
        return df

    return df[
        (df["hour"] >= start_hour)
        &
        (df["hour"] <= end_hour)
    ]


# -------------------------------------------------------
# CSV
# -------------------------------------------------------

def dataframe_to_csv(df):

    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    )


# -------------------------------------------------------
# Summary
# -------------------------------------------------------

def get_summary(df):

    if df.empty:

        return {

            "comments":0,

            "avg_like":0,

            "max_like":0,

            "first_comment":None,

            "last_comment":None

        }

    return {

        "comments":len(df),

        "avg_like":round(df["like"].mean(),2),

        "max_like":int(df["like"].max()),

        "first_comment":df["published"].min(),

        "last_comment":df["published"].max()

    }


# -------------------------------------------------------
# Check
# -------------------------------------------------------

def validate_video(video_id):

    info = safe_execute(
        get_video_info,
        video_id
    )

    return info is not None
