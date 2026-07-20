# Compact Streamlit YouTube Comment Analyzer
import re,tempfile,requests
import streamlit as st
import pandas as pd
import plotly.express as px
from googleapiclient.discovery import build
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(page_title="YT 댓글 분석기",layout="wide")
API=st.secrets["YOUTUBE_API_KEY"]

def vid(u):
    for p in [r"v=([\w-]{11})",r"youtu\.be/([\w-]{11})",r"shorts/([\w-]{11})"]:
        m=re.search(p,u)
        if m:return m.group(1)
def yt(): return build("youtube","v3",developerKey=API)
def fetch(v,n):
    y=yt();rows=[];t=None
    while len(rows)<n:
        r=y.commentThreads().list(part="snippet",videoId=v,maxResults=min(100,n-len(rows)),pageToken=t,textFormat="plainText").execute()
        for i in r.get("items",[]):
            s=i["snippet"]["topLevelComment"]["snippet"]
            rows.append({"comment":s["textDisplay"],"time":s["publishedAt"]})
        t=r.get("nextPageToken")
        if not t:break
    df=pd.DataFrame(rows)
    if not df.empty:
        df["time"]=pd.to_datetime(df["time"]);df["hour"]=df["time"].dt.hour
    return df
st.title("🎬 YouTube 댓글 분석기")
u=st.text_input("URL");c=st.slider("댓글 수",100,300,200,100)
if u:st.video(u)
if st.button("분석"):
    v=vid(u)
    if not v: st.error("URL 오류"); st.stop()
    df=fetch(v,c)
    st.dataframe(df.head())
    if not df.empty:
        st.plotly_chart(px.bar(df.groupby("hour").size().reset_index(name="count"),x="hour",y="count"),use_container_width=True)
        font=Path(tempfile.gettempdir())/"NanumGothic.ttf"
        if not font.exists():
            rr=requests.get("https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Regular.ttf")
            font.write_bytes(rr.content)
        wc=WordCloud(font_path=str(font),background_color="white").generate(" ".join(df.comment.astype(str)))
        fig,ax=plt.subplots();ax.imshow(wc);ax.axis("off");st.pyplot(fig)
        pos=["좋","최고","추천"];neg=["싫","최악","별로"]
        df["sentiment"]=df.comment.apply(lambda x:"긍정" if sum(w in x for w in pos)>sum(w in x for w in neg) else ("부정" if sum(w in x for w in neg)>sum(w in x for w in pos) else "중립"))
        st.plotly_chart(px.pie(df,names="sentiment"),use_container_width=True)
        st.download_button("CSV",df.to_csv(index=False).encode("utf-8-sig"),"comments.csv")
