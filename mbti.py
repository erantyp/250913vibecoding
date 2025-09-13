# app.py
# ─────────────────────────────────────────────────────────────
# MBTI Study Coach: MBTI 유형별 최적 공부법 추천 웹앱
# by ChatGPT (Korean UI, Streamlit Community Cloud-ready)
# ─────────────────────────────────────────────────────────────
import streamlit as st
from datetime import datetime, timedelta
import random
import textwrap
from io import BytesIO

st.set_page_config(
    page_title="MBTI Study Coach 🎓✨",
    page_icon="📚",
    layout="wide"
)

# ---------- 스타일 (CSS 애니메이션 & 카드) ----------
st.markdown("""
<style>
/* 배경 그라데이션 느낌 */
.stApp {
  background: radial-gradient(1200px 600px at 20% 10%, #fff7e6 0%, transparent 60%),
              radial-gradient(1200px 600px at 80% 20%, #e6f7ff 0%, transparent 60%),
              radial-gradient(1200px 600px at 50% 90%, #f6ffed 0%, transparent 60%);
}

/* 반짝이는 이모지 효과 */
.sparkle {
  display: inline-block;
  animation: pop 1.2s ease-in-out infinite;
}
@keyframes pop {
  0% { transform: translateY(0) scale(1); filter: drop-shadow(0 0 0px rgba(255,215,0,0.0)); }
  50% { transform: translateY(-2px) scale(1.05); filter: drop-shadow(0 0 4px rgba(255,215,0,0.6)); }
  100% { transform: translateY(0) scale(1); filter: drop-shadow(0 0 0px rgba(255,215,0,0.0)); }
}

/* 카드 공통 */
.card {
  border-radius: 16px;
  padding: 16px 18px;
  margin: 8px 0;
  border: 1px solid rgba(0,0,0,0.06);
  box-shadow: 0 10px 20px rgba(0,0,0,0.06);
  transition: transform .15s ease, box-shadow .15s ease;
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(6px);
}
.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 28px rgba(0,0,0,0.08);
}
.badge {
  display:inline-block; font-size:12px; padding:2px 8px; border-radius:999px; 
  background:#f0f5ff; color:#1d39c4; border:1px solid #adc6ff; margin-right:6px;
}

/* 섹션 타이틀 밑줄 */
.section-title {
  font-weight: 800; font-size: 1.15rem; margin: 6px 0 10px 0;
  border-left: 6px solid #ffd666; padding-left: 10px;
}

/* 체크리스트 이쁜 불릿 */
ul.pretty > li { 
  margin: 6px 0;
}
ul.pretty > li::marker {
  content: "✅ ";
}
</style>
""", unsafe_allow_html=True)

# ---------- 데이터: MBTI별 추천 ----------
# 공통 템플릿 + 유형별 커스텀
TEMPERAMENT = {
    "Analysts": ["INTJ", "INTP", "ENTJ", "ENTP"],
    "Diplomats": ["INFJ", "INFP", "ENFJ", "ENFP"],
    "Sentinels": ["ISTJ", "ISFJ", "ESTJ", "ESFJ"],
    "Explorers": ["ISTP", "ISFP", "ESTP", "ESFP"]
}

def tips_for(mbti: str):
    base = {
        "focus": [
            "⏱️ **포모도로 25/5**: 25분 몰입 + 5분 리셋을 4세트(=2시간)로 묶기",
            "📵 **방해요소 차단**: 알림 끄기 + 공부 앱 전용 홈 화면 만들기",
            "🧠 **테스트 우선학습**: 읽기 전에 먼저 문제부터 풀어 약점 드러내기 (Active Recall)",
        ],
        "tools": [
            "🗺️ **개념 지도(마인드맵)**",
            "📑 **요약 카드(Anki/퀴즈카드)**",
            "🧩 **학습 루틴 자동화(체크리스트 & 타이머)**"
        ],
        "pitfalls": [
            "🐌 시작 지연(완벽주의/과도한 준비)",
            "📚 수동적 읽기만 반복",
            "📵 알림/메신저에 의한 잦은 맥락 전환"
        ],
        "mini_habits": [
            "📘 **2쪽만 읽기**로 시작 → 탄력 붙이면 확장",
            "✍️ **1개 핵심문장**만 요약",
            "🛎️ 공부 전 **의식 30초**(물 한 컵+심호흡 5회)"
        ],
    }

    custom = {
        "INTJ": dict(
            slogan="전략적 마스터플랜으로 조용히 1등하는 타입 🧩🧠",
            best=["🎯 목표 역산(시험일 → 주/일 단위 역스케줄)", "📈 취약파트 데이터화(오답률/시간)"],
            how=["개념 → 문제 → 오답 → 재정리의 **폐쇄 루프**", "깊게 파되 **마감시간 하드코어**로 둬 과몰입 방지"],
        ),
        "INTP": dict(
            slogan="원리 탐구와 가설 검증의 장인 🔬🌀",
            best=["왜?를 3번 묻는 **원인사슬 분석**", "개념 간 **연결 그래프** 만들기"],
            how=["공부한 걸 **블로그/노션 글**로 구조화", "문제를 **스스로 만들어 보기**"],
        ),
        "ENTJ": dict(
            slogan="목표를 쪼개고 밀어붙이는 실행가 🚀📊",
            best=["OKR/KR로 **측정 가능한 목표**", "매주 **리뷰 & 피벗**"],
            how=["타임블록으로 **공격적 일정**", "스터디 리딩하며 **가르치기 = 최강 복습**"],
        ),
        "ENTP": dict(
            slogan="아이디어 폭발, 변주와 실험의 플레이어 ⚡🧠",
            best=["**다중 전략 A/B 테스트**", "친구와 **토론-스파링**으로 기억 고착"],
            how=["새롭고 재밌는 포맷(카툰 요약/밈)으로 재해석", "**제한시간 퀴즈쇼**로 집중 부스팅"],
        ),
        "INFJ": dict(
            slogan="의미와 일관성에 강한 조용한 설계자 🌙📐",
            best=["**가치-목표 정렬**(왜 이걸 배우는가)", "조용한 **딥워크 슬롯** 확보"],
            how=["개념을 **스토리로 엮기**", "주 1회 **회고 저널링**"],
        ),
        "INFP": dict(
            slogan="몰입하면 끝까지 가는 감성형 딥다이버 🎨🌊",
            best=["작은 **시작 의식**으로 감정 시동", "좋아하는 **테마/사례**로 연결"],
            how=["**감정-동기 트래커**로 에너지 관리", "**음악·향** 등 환경 큐"],
        ),
        "ENFJ": dict(
            slogan="사람을 움직이고 학습을 조직하는 코치형 🤝🌟",
            best=["미니 클래스처럼 **가르치며 배우기**", "파트너와 **상호 책임**"],
            how=["**진도 공유 대시보드**", "칭찬·보상 **게이미피케이션**"],
        ),
        "ENFP": dict(
            slogan="흥미 스파크로 학습을 확장하는 탐험가 ✨🧭",
            best=["**퀘스트 보드**로 다양 과제 병렬", "시간 제한 **스프린트**"],
            how=["보상 스티커/이모지 **레벨업 시스템**", "지루해지면 **장소·방식 스위치**"],
        ),
        "ISTJ": dict(
            slogan="체계·규칙·성실의 정석형 📏🧱",
            best=["**체크리스트-템플릿** 기반 반복", "누적 복습 **스페이싱**"],
            how=["오답노트 표준 양식", "매일 같은 시간 **루틴 고정**"],
        ),
        "ISFJ": dict(
            slogan="차분한 돌봄형, 꾸준함이 무기 🌿📒",
            best=["작은 **성공경험** 쌓기", "친숙한 **예시-유추** 사용"],
            how=["조용한 공간 + **의식 루틴**", "응원 파트너와 **안부 체크**"],
        ),
        "ESTJ": dict(
            slogan="명확한 기준과 결과를 중시하는 실무형 🧭📈",
            best=["**목표-측정-피드백** 사이클", "타이머로 **산출물 우선**"],
            how=["일간 KPI(문제 수/요약 수)", "주간 **성과 리뷰**"],
        ),
        "ESFJ": dict(
            slogan="협력과 책임감의 팀 플레이어 🧡📋",
            best=["스터디 **배치 학습**", "타인에게 설명하며 **기억 강화**"],
            how=["**공유 노트**로 함께 완성", "서로 칭찬·보상 **사회적 강화**"],
        ),
        "ISTP": dict(
            slogan="문제 해결형 메이커, 손으로 이해하는 타입 🛠️🧩",
            best=["**실습/적용 문제** 우선", "시간 제한 **스피드런**"],
            how=["핵심 공식을 **치트시트**로", "**데모-케이스** 먼저 보고 이론 연결"],
        ),
        "ISFP": dict(
            slogan="감각·미감에 강한 섬세한 몰입가 🌸🎧",
            best=["미니멀 환경 + **감각 큐(플레이리스트)**", "예쁜 **비주얼 노트**"],
            how=["**감정 소요 기록**으로 과부하 방지", "짧고 잦은 **마이크로세션**"],
        ),
        "ESTP": dict(
            slogan="실전 감각과 승부욕의 스프린터 🏁⚡",
            best=["**모의고사/기출**로 바로 붙어보기", "랭킹/시간기록 **게임화**"],
            how=["**즉시 피드백** 장치", "스탠딩 데스크/짧은 **액티브 브레이크**"],
        ),
        "ESFP": dict(
            slogan="에너지·사교·경험 학습의 달인 🎉🎶",
            best=["**스터디 쇼케이스**(발표/퀴즈 진행)", "알록달록 **보상 시스템**"],
            how=["**음악 리듬 학습**(용어-박자 매칭)", "친구와 **역할놀이**로 개념 재연"],
        ),
    }

    return base, custom.get(mbti, dict(
        slogan="나만의 방식으로 꽃피우는 러너 🌱",
        best=["루틴을 작게, 꾸준히", "기록으로 나의 방법을 발견"],
        how=["작-실-기(작게→실행→기록)", "주 1회 회고로 미세 조정"],
    ))

MBTIS = [
    "INTJ","INTP","ENTJ","ENTP",
    "INFJ","INFP","ENFJ","ENFP",
    "ISTJ","ISFJ","ESTJ","ESFJ",
    "ISTP","ISFP","ESTP","ESFP"
]

QUOTES = [
    "오늘의 1%가 내일의 100%를 바꾼다. ✨",
    "완벽보다 완료. Done is better than perfect. ✅",
    "기억은 테스트할수록 강해진다. 🧠",
    "작은 습관이 큰 차이를 만든다. 🌱",
]

# ---------- 사이드바 ----------
with st.sidebar:
    st.markdown("### 🎓 MBTI Study Coach")
    st.markdown("공부 타입에 맞춘 **맞춤 학습 전략**을 받아보세요!")
    st.markdown("---")
    mbti = st.selectbox("내 MBTI 선택하기", MBTIS, index=MBTIS.index("INTJ"))
    goal = st.text_input("이번 주 학습 목표(예: 확률 단원 끝내기)", "")
    hours = st.slider("하루 공부 가능 시간", 0.5, 8.0, 2.0, 0.5)
    start_btn = st.button("🚀 추천 받기")

# 첫 방문 재미 요소
if "celebrated" not in st.session_state:
    st.session_state.celebrated = False

# ---------- 헤더 ----------
st.markdown(f"""
# MBTI Study Coach {random.choice(['📚','🧠','✨','🚀','🎯'])}
<span class="sparkle">당신의 성향에 꼭 맞춘 공부 전략을 추천해드려요!</span>
""", unsafe_allow_html=True)

st.caption(random.choice(QUOTES))

# ---------- 추천 생성 ----------
if start_btn:
    base, spec = tips_for(mbti)

    # 가벼운 이펙트
    if not st.session_state.celebrated:
        st.balloons()
        st.session_state.celebrated = True
    st.toast("맞춤 추천을 생성했어요! 🎉", icon="🎯")

    # 상단 요약 카드
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        st.markdown(f"""
<div class="card">
  <div class="badge">{mbti}</div>
  <div class="badge">Study Fit</div>
  <div style="font-size:20px; font-weight:700; margin-top:4px;">{spec['slogan']}</div>
  <div style="margin-top:6px;">이번 주 목표: <b>{goal if goal else '목표를 입력해보세요'}</b></div>
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
<div class="card">
  <div class="section-title">🔥 집중 레시피</div>
  <ul class="pretty">
    <li>포모도로 4세트(2시간) 1라운드</li>
    <li>라운드마다 핵심 1문장 요약</li>
    <li>끝에 10분 오답·메모 정리</li>
  </ul>
</div>
""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
<div class="card">
  <div class="section-title">⏳ 하루 시간 설계</div>
  <ul class="pretty">
    <li>총 {hours:.1f}h = 25/5 x {int(hours*60/30)}세트</li>
    <li>세트 2~3개마다 10분 산책/스트레칭</li>
  </ul>
</div>
""", unsafe_allow_html=True)

    # 상세 추천
    st.markdown("### 🎯 가장 잘 맞는 전략")
    left, right = st.columns(2)
    with left:
        st.markdown("""
<div class="card">
  <div class="section-title">💡 핵심 학습 메커닉</div>
  <ul class="pretty">
""" + "".join([f"<li>{x}</li>" for x in spec["best"]]) + """
  </ul>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="card">
  <div class="section-title">🧠 집중 유지 스킬</div>
  <ul class="pretty">
""" + "".join([f"<li>{x}</li>" for x in base["focus"]]) + """
  </ul>
</div>
""", unsafe_allow_html=True)

    with right:
        st.markdown("""
<div class="card">
  <div class="section-title">🛠️ 도구/템 세팅</div>
  <ul class="pretty">
""" + "".join([f"<li>{x}</li>" for x in base["tools"]]) + """
  </ul>
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div class="card">
  <div class="section-title">⚠️ 나의 함정 피하기</div>
  <ul class="pretty">
""" + "".join([f"<li>{x}</li>" for x in base["pitfalls"]]) + """
  </ul>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="card">
  <div class="section-title">🌱 7일 미니 습관 플랜</div>
  <ul class="pretty">
""" + "".join([f"<li>{x}</li>" for x in base["mini_habits"]]) + """
  </ul>
</div>
""", unsafe_allow_html=True)

    # 스터디 모드 시뮬레이터
    st.markdown("### 🕹️ Study Mode 시뮬레이터")
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("▶️ 집중 세션 시작(가상)"):
            st.info("세션 부팅 중… 호흡 정렬 5회… 책상 정리… 타이머 준비…")
            prog = st.progress(0, text="세팅 중…")
            for i in range(0, 101, 5):
                prog.progress(i, text=f"집중력 충전 {i}%")
            st.success("준비 완료! 25분 스타트! ⏱️")
            if random.random() > 0.5:
                st.snow()

    with colB:
        st.markdown("""
<div class="card">
  <div class="section-title">🎵 추천 집중 환경</div>
  <ul class="pretty">
    <li>리듬 낮은 음악(로파이/화이트노이즈)</li>
    <li>스탠딩 1세트 + 좌식 2세트 번갈아</li>
    <li>휴대폰은 다른 방, 알림 전체 OFF</li>
  </ul>
</div>
""", unsafe_allow_html=True)

    # 다운로드용 텍스트
    plan_text = textwrap.dedent(f"""
    # MBTI Study Coach - {mbti}
    - 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    - 이번 주 목표: {goal if goal else '미입력'}
    - 하루 공부 가능 시간: {hours:.1f}시간

    ## 슬로건
    {spec['slogan']}

    ## 핵심 학습 메커닉
    {chr(10).join(['- ' + x for x in spec['best']])}

    ## 집중 유지 스킬
    {chr(10).join(['- ' + x for x in base['focus']])}

    ## 도구/템 세팅
    {chr(10).join(['- ' + x for x in base['tools']])}

    ## 나의 함정 피하기
    {chr(10).join(['- ' + x for x in base['pitfalls']])}

    ## 7일 미니 습관 플랜
    {chr(10).join(['- ' + x for x in base['mini_habits']])}

    ## 3줄 요약
    1) {mbti} 타입에 맞춘 전략으로 시작(완벽주의 금지, 작은 승리부터)
    2) 테스트 우선학습 + 오답 폐쇄루프
    3) 주 1회 회고로 미세 조정
    """).strip()

    buffer = BytesIO(plan_text.encode("utf-8"))
    st.download_button("📥 내 맞춤 플랜(.md) 다운로드", data=buffer, file_name=f"study_plan_{mbti}.md", mime="text/markdown")

# 푸터
st.markdown("---")
st.caption("💡 팁: 사이드바에서 MBTI와 목표, 시간을 설정하고 ‘추천 받기’를 눌러요. 첫 실행에 🎈가 터집니다!")
