import streamlit as st

st.set_page_config(
    page_title="이름 궁합",
    page_icon="❤️",
)

st.title("❤️ 이름 궁합 계산기")
st.caption("교육용 한글 획수 기준으로 계산됩니다.")

# -----------------------------
# 획수표
# -----------------------------
CHO = {
    'ㄱ':2,'ㄲ':4,'ㄴ':2,'ㄷ':3,'ㄸ':6,'ㄹ':5,'ㅁ':4,'ㅂ':4,'ㅃ':8,
    'ㅅ':2,'ㅆ':4,'ㅇ':1,'ㅈ':3,'ㅉ':6,'ㅊ':4,'ㅋ':3,'ㅌ':4,'ㅍ':4,'ㅎ':3
}

JUNG = {
    'ㅏ':2,'ㅐ':3,'ㅑ':3,'ㅒ':4,'ㅓ':2,'ㅔ':3,'ㅕ':3,'ㅖ':4,
    'ㅗ':2,'ㅘ':4,'ㅙ':5,'ㅚ':3,'ㅛ':3,'ㅜ':2,'ㅝ':4,'ㅞ':5,
    'ㅟ':3,'ㅠ':3,'ㅡ':1,'ㅢ':2,'ㅣ':1
}

JONG = {
    '':0,
    'ㄱ':2,'ㄲ':4,'ㄳ':4,
    'ㄴ':2,'ㄵ':5,'ㄶ':5,
    'ㄷ':3,
    'ㄹ':5,'ㄺ':7,'ㄻ':9,'ㄼ':9,'ㄽ':7,'ㄾ':9,'ㄿ':9,'ㅀ':8,
    'ㅁ':4,
    'ㅂ':4,'ㅄ':6,
    'ㅅ':2,'ㅆ':4,
    'ㅇ':1,
    'ㅈ':3,
    'ㅊ':4,
    'ㅋ':3,
    'ㅌ':4,
    'ㅍ':4,
    'ㅎ':3
}

CHO_LIST = [
    'ㄱ','ㄲ','ㄴ','ㄷ','ㄸ','ㄹ','ㅁ','ㅂ','ㅃ',
    'ㅅ','ㅆ','ㅇ','ㅈ','ㅉ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'
]

JUNG_LIST = [
    'ㅏ','ㅐ','ㅑ','ㅒ','ㅓ','ㅔ','ㅕ','ㅖ',
    'ㅗ','ㅘ','ㅙ','ㅚ','ㅛ','ㅜ','ㅝ','ㅞ',
    'ㅟ','ㅠ','ㅡ','ㅢ','ㅣ'
]

JONG_LIST = [
    '',
    'ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ',
    'ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ',
    'ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ'
]


def stroke(ch):
    if not ('가' <= ch <= '힣'):
        return 0

    code = ord(ch) - ord('가')

    cho = code // 588
    jung = (code % 588) // 28
    jong = code % 28

    return (
        CHO[CHO_LIST[cho]]
        + JUNG[JUNG_LIST[jung]]
        + JONG[JONG_LIST[jong]]
    )


def cross_name(a, b):
    result = ""

    m = min(len(a), len(b))

    for i in range(m):
        result += a[i]
        result += b[i]

    result += a[m:]
    result += b[m:]

    return result


def compatibility(nums):
    history = []

    while len(nums) > 2:
        nums = [(nums[i] + nums[i+1]) % 10 for i in range(len(nums)-1)]
        history.append(nums.copy())

    return history, nums


name1 = st.text_input("이름 1")
name2 = st.text_input("이름 2")

if st.button("궁합 계산"):

    if not name1 or not name2:
        st.warning("두 이름을 모두 입력하세요.")
        st.stop()

    mixed = cross_name(name1.strip(), name2.strip())

    strokes = [stroke(c) for c in mixed]

    history, result = compatibility(strokes)

    st.subheader("교차된 이름")
    st.write(mixed)

    st.subheader("글자별 획수")

    for c, s in zip(mixed, strokes):
        st.write(f"{c} : {s}획")

    st.subheader("초기 숫자")

    st.code("".join(map(str, strokes)))

    st.subheader("계산 과정")

    for i, h in enumerate(history, 1):
        st.write(f"{i}단계")
        st.code("".join(map(str, h)))

    score = int("".join(map(str, result)))

    st.success(f"❤️ 궁합 {score}%")
