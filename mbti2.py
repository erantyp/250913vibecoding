# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="MBTI 국가별 TOP10", layout="wide")

st.title("🌍 MBTI 유형별 국가 TOP 10 대시보드")
st.caption("CSV를 업로드하면, 선택한 MBTI 유형에서 비율이 가장 높은 국가 TOP 10을 인터랙티브 차트로 보여줍니다.")

# -----------------------------
# 1) 파일 업로드
# -----------------------------
file = st.file_uploader("CSV 파일 업로드 (.csv)", type=["csv"])

# -----------------------------
# 유틸: 컬럼/데이터 정리
# -----------------------------
MBTI_TYPES = [
    "INTJ","INTP","ENTJ","ENTP",
    "INFJ","INFP","ENFJ","ENFP",
    "ISTJ","ISFJ","ESTJ","ESFJ",
    "ISTP","ISFP","ESTP","ESFP",
]

def read_csv_safely(f):
    # 인코딩 가변 대응
    tried = []
    for enc in ["utf-8", "cp949", "euc-kr", "latin-1"]:
        try:
            df = pd.read_csv(f, encoding=enc)
            return df
        except Exception as e:
            tried.append(f"{enc}: {e}")
            f.seek(0)
    st.error("CSV를 읽는 데 실패했습니다. 파일 인코딩을 확인해 주세요.")
    st.stop()

def detect_country_col(cols):
    up = [str(c).upper().strip() for c in cols]
    # 후보 키워드
    for key in ["COUNTRY", "NATION", "국가", "나라", "STATE"]:
        for c, u in zip(cols, up):
            if key in u:
                return c
    return cols[0]  # 첫 열 fallback

def normalize_mbti_columns(df):
    # MBTI 컬럼 찾기 (공백/%/괄호 등 제거 후 매칭)
    mbti_cols = []
    for c in df.columns:
        cu = str(c).upper()
        cu2 = cu.replace("%","").replace("(","").replace(")","").replace(" ","")
        if cu in MBTI_TYPES or cu2 in MBTI_TYPES:
            mbti_cols.append(c)

    # 숫자 변환
    def to_num(s):
        return (
            s.astype(str)
             .str.replace("%","", regex=False)
             .str.replace(",","", regex=False)
             .str.strip()
             .replace({"": np.nan, "nan": np.nan})
             .astype(float)
        )

    for c in mbti_cols:
        try:
            df[c] = to_num(df[c])
        except Exception:
            pass

    # 값 스케일 판정(비율 0~1로 들어온 경우 %로 변환)
    if mbti_cols:
        sample = pd.concat([df[c].dropna() for c in mbti_cols], axis=0)
        if len(sample) > 0 and sample.quantile(0.95) <= 1.5:
            for c in mbti_cols:
                df[c] = df[c] * 100.0

    return mbti_cols

# -----------------------------
# 2) 본 처리
# -----------------------------
if file is not None:
    df = read_csv_safely(file)
    # 컬럼 공백 정리
    df.columns = [str(c).strip() for c in df.columns]

    country_col = detect_country_col(df.columns)
    mbti_cols = normalize_mbti_columns(df)

    if not mbti_cols:
        st.error("MBTI 유형(예: INTJ, ENFP 등) 컬럼을 찾지 못했습니다. 컬럼명이 16유형과 일치하도록 확인해 주세요.")
        st.stop()

    # 선택 UI
    selected_type = st.selectbox(
        "분석할 MBTI 유형을 선택하세요",
        options=sorted(set([c.upper().replace("%","").replace("(","").replace(")","").replace(" ","") for c in mbti_cols])),
        index=0
    )
    top_n = st.slider("TOP N 국가 수", min_value=5, max_value=20, value=10, step=1)

    # 실제 DF에서 선택 유형에 대응하는 원본 컬럼명 찾기
    # (대소문자/공백/기호 차이 보정)
    def col_match(name):
        target = name.upper()
        for c in mbti_cols:
            cu = str(c).upper().replace("%","").replace("(","").replace(")","").replace(" ","")
            if cu == target:
                return c
        return None

    val_col = col_match(selected_type)
    if val_col is None:
        st.error("선택한 유형에 해당하는 컬럼을 찾지 못했습니다.")
        st.stop()

    # 상위 N 추출
    work = df[[country_col, val_col]].copy()
    work = work.dropna(subset=[val_col])
    work = work.rename(columns={country_col: "Country", val_col: "Share(%)"})
    work = work.sort_values("Share(%)", ascending=False).head(top_n)

    # -----------------------------
    # 3) Altair 차트
    # -----------------------------
    st.subheader(f"🧭 {selected_type} 비율 상위 {len(work)}개 국가")
    st.dataframe(work.reset_index(drop=True), use_container_width=True)

    # 인터랙티브 요소: 막대 Hover/Select
    highlight = alt.selection_point(on="mouseover", fields=["Country"], nearest=True, empty=False)

    base = alt.Chart(work).encode(
        x=alt.X("Share(%):Q", title="Share (%)", scale=alt.Scale(domain=[0, float(work["Share(%)"].max()) * 1.1])),
        y=alt.Y("Country:N", sort='-x', title=None),
        tooltip=[alt.Tooltip("Country:N"), alt.Tooltip("Share(%):Q", format=".2f")]
    )

    bars = base.mark_bar().encode(
        color=alt.condition(highlight, alt.value("#1f77b4"), alt.value("#a6bddb"))
    ).add_params(highlight)

    text = base.mark_text(align="left", dx=4).encode(
        text=alt.Text("Share(%):Q", format=".2f")
    )

    chart = (bars + text).properties(
        height=40 * len(work) + 10,
        title=f"{selected_type} 비율이 높은 국가 TOP {len(work)}"
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

    # 데이터 다운로드(선택 사항)
    st.download_button(
        "⬇️ 이 표 CSV로 저장",
        data=work.to_csv(index=False).encode("utf-8"),
        file_name=f"top_{top_n}_{selected_type}.csv",
        mime="text/csv",
    )

else:
    st.info("왼쪽 상단의 **CSV 파일 업로드** 버튼으로 데이터를 올려주세요. (열에 MBTI 유형명(INTJ 등)이 있어야 합니다.)")
