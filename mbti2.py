import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os

st.set_page_config(page_title="MBTI 국가별 TOP10", layout="wide")
st.title("🌍 MBTI 유형별 국가 TOP 10 대시보드")

DATA_FILENAME = "countriesMBTI_16types.csv"

# -----------------------------
# 1) 데이터 로딩
# -----------------------------
@st.cache_data
def load_data():
    if os.path.exists(DATA_FILENAME):
        # 같은 폴더에 파일이 있으면 자동으로 읽기
        return pd.read_csv(DATA_FILENAME)
    else:
        return None

df = load_data()

if df is None:
    st.info("💡 같은 폴더에 CSV 파일이 없어요. 아래에서 직접 업로드 해주세요.")
    uploaded_file = st.file_uploader("CSV 파일 업로드 (.csv)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

if df is not None:
    # -----------------------------
    # 2) MBTI 컬럼 정규화
    # -----------------------------
    df.columns = [str(c).strip() for c in df.columns]

    MBTI_TYPES = [
        "INTJ","INTP","ENTJ","ENTP",
        "INFJ","INFP","ENFJ","ENFP",
        "ISTJ","ISFJ","ESTJ","ESFJ",
        "ISTP","ISFP","ESTP","ESFP",
    ]

    # 국가 컬럼 자동 탐지
    country_col = next((c for c in df.columns if any(k in c.upper() for k in ["COUNTRY","NATION","국가","나라"])), df.columns[0])

    mbti_cols = [c for c in df.columns if c.upper().replace("%","").replace("(","").replace(")","").replace(" ","") in MBTI_TYPES]

    # 숫자 변환 + % 처리
    for c in mbti_cols:
        df[c] = (
            df[c].astype(str)
                 .str.replace("%","", regex=False)
                 .str.replace(",","", regex=False)
                 .str.strip()
                 .replace({"": np.nan, "nan": np.nan})
                 .astype(float)
        )
    if mbti_cols:
        sample = pd.concat([df[c].dropna() for c in mbti_cols])
        if len(sample) > 0 and sample.quantile(0.95) <= 1.5:
            for c in mbti_cols:
                df[c] = df[c] * 100.0

    # -----------------------------
    # 3) UI - MBTI 유형 선택
    # -----------------------------
    selected_type = st.selectbox("분석할 MBTI 유형", options=MBTI_TYPES, index=0)
    top_n = st.slider("TOP N 국가 수", 5, 20, 10)

    val_col = next((c for c in mbti_cols if c.upper().replace("%","").replace("(","").replace(")","").replace(" ","") == selected_type), None)

    if val_col is None:
        st.error("선택한 유형에 맞는 데이터 컬럼이 없습니다.")
    else:
        work = df[[country_col, val_col]].dropna()
        work = work.rename(columns={country_col: "Country", val_col: "Share(%)"})
        work = work.sort_values("Share(%)", ascending=False).head(top_n)

        st.subheader(f"🧭 {selected_type} 비율 상위 {len(work)}개 국가")
        st.dataframe(work.reset_index(drop=True), use_container_width=True)

        highlight = alt.selection_point(on="mouseover", fields=["Country"], nearest=True, empty=False)

        base = alt.Chart(work).encode(
            x=alt.X("Share(%):Q", title="Share (%)", scale=alt.Scale(domain=[0, float(work["Share(%)"].max()) * 1.1])),
            y=alt.Y("Country:N", sort='-x', title=None),
            tooltip=["Country", alt.Tooltip("Share(%):Q", format=".2f")]
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

        st.download_button(
            "⬇️ CSV 저장",
            data=work.to_csv(index=False).encode("utf-8"),
            file_name=f"top_{top_n}_{selected_type}.csv",
            mime="text/csv",
        )
else:
    st.warning("CSV 데이터를 불러올 수 없습니다. 파일을 업로드하거나 같은 폴더에 넣어주세요.")
