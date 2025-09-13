# app.py
# ─────────────────────────────────────────────────────────────
# River Crossing Puzzle (Wolf-Goat-Cabbage) for Streamlit
# 규칙:
#  - 배에는 '사람 + 1개 객체'만 탑승 가능
#  - 사람이 없는 둑에서 늑대+양이 함께 있으면: 양이 먹힘 → 실패
#  - 사람이 없는 둑에서 양+양배추가 함께 있으면: 양배추가 먹힘 → 실패
#  - 모든 객체(늑대, 양, 양배추, 사람)가 오른쪽 둑에 도착하면 성공
# 조작:
#  - 객체 카드를 클릭해 '보트에 태우기/내리기'
#  - 반드시 사람이 배에 타 있어야 '이동' 가능
# ─────────────────────────────────────────────────────────────

import streamlit as st

st.set_page_config(page_title="강 건너기 퍼즐 🐺🐑🥬", page_icon="⛵", layout="wide")

# ---------------- 스타일 ----------------
st.markdown("""
<style>
.stApp { 
  background: radial-gradient(1200px 600px at 20% 10%, #fff7e6 0%, transparent 60%),
              radial-gradient(1200px 600px at 80% 20%, #e6f7ff 0%, transparent 60%),
              radial-gradient(1200px 600px at 50% 90%, #f6ffed 0%, transparent 60%);
}
.section { background: rgba(255,255,255,0.75); border:1px solid rgba(0,0,0,.06);
  border-radius: 16px; padding: 14px; box-shadow: 0 10px 20px rgba(0,0,0,.05); }
.title-chip { display:inline-block; padding:2px 10px; border-radius:999px; background:#f0f5ff; 
  color:#1d39c4; border:1px solid #adc6ff; font-size:13px; margin-bottom:8px;}
.card {
  display:flex; align-items:center; justify-content:space-between;
  border:1px solid rgba(0,0,0,0.08); border-radius:14px; padding:10px 12px; 
  margin:6px 0; background:#ffffffd9;
}
.card .left { display:flex; align-items:center; gap:10px; }
.badge { background:#fff7e6; color:#ad6800; border:1px solid #ffd591; padding:2px 8px; border-radius:999px; font-size:12px;}
.bank-title { text-align:center; font-weight:800; margin-bottom:6px; }
.boat-zone { text-align:center; font-weight:700; padding:10px; border-radius:14px; 
             border:2px dashed #91caff; background:#e6f4ffaa;}
.disabled { opacity: .5; pointer-events:none; }
hr.sep { border:none; border-top:1px dashed #d9d9d9; margin:10px 0; }
</style>
""", unsafe_allow_html=True)

# ---------------- 상태 ----------------
def reset_game():
    st.session_state.positions = {  # 'L'eft or 'R'ight
        "person": "L",
        "wolf":   "L",
        "goat":   "L",
        "cabbage":"L",
    }
    st.session_state.boat_side = "L"     # 'L' or 'R'
    st.session_state.boat_load = None    # None or one of ['wolf','goat','cabbage']
    st.session_state.running = True
    st.session_state.result = None       # 'win' | 'lose' | None
    st.session_state.view = "menu"       # 'menu' | 'game'

if "positions" not in st.session_state:
    reset_game()

EMOJI = {"person":"🧍", "wolf":"🐺", "goat":"🐑", "cabbage":"🥬"}
LABEL = {"person":"사람", "wolf":"늑대", "goat":"양", "cabbage":"양배추"}

# ---------------- 규칙 체크 ----------------
def check_fail():
    """사람이 없는 둑에서 금지 조합이 있으면 실패 반환."""
    pos = st.session_state.positions
    for side in ("L","R"):
        person_here = (pos["person"] == side)
        # 늑대+양
        if (pos["wolf"] == side) and (pos["goat"] == side) and (not person_here):
            return "늑대가 양을 먹어버렸어요! 🐺➡️🐑"
        # 양+양배추
        if (pos["goat"] == side) and (pos["cabbage"] == side) and (not person_here):
            return "양이 양배추를 먹어버렸어요! 🐑➡️🥬"
    return None

def check_win():
    pos = st.session_state.positions
    return all(pos[k] == "R" for k in pos)

# ---------------- 보트 조작 ----------------
def can_board(name):
    """해당 객체를 보트에 태울 수 있는지: 보트와 같은 둑에 있고, 빈 자리(사람은 항상 탑승)"""
    if name == "person":
        # 사람은 별도 슬롯: 배가 있는 둑에 사람 있어야 '이동' 가능
        return st.session_state.positions["person"] == st.session_state.boat_side
    else:
        return (st.session_state.positions[name] == st.session_state.boat_side) and (st.session_state.boat_load in (None, name))

def toggle_board(name):
    """객체 보트 탑승/하차 토글"""
    if not can_board(name): 
        st.toast("그 객체는 지금 보트에 태울 수 없어요.", icon="🛶")
        return
    if name == "person":
        # 사람은 탑승/하차 개념 없이 항상 둑에 있고, 이동 시 함께 이동
        st.toast("사람은 배 이동에 자동으로 탑니다. (보트와 같은 둑에만 있으면 돼요)", icon="🧍")
        return
    # 승객 슬롯 토글
    if st.session_state.boat_load == name:
        st.session_state.boat_load = None
    else:
        st.session_state.boat_load = name

def move_boat():
    """보트 이동(좌<->우). 조건: 사람이 보트와 같은 둑에 있어야 함."""
    if st.session_state.positions["person"] != st.session_state.boat_side:
        st.toast("사람이 보트에 타 있어야 움직일 수 있어요! 🧍⛵", icon="⛔")
        return
    # 이동 수행: 사람과 보트, 그리고 승객(있다면) 위치 반대쪽으로
    new_side = "R" if st.session_state.boat_side == "L" else "L"
    st.session_state.boat_side = new_side
    st.session_state.positions["person"] = new_side
    if st.session_state.boat_load:
        st.session_state.positions[st.session_state.boat_load] = new_side
        # 도착하면 자동 하선
        st.session_state.boat_load = None

    # 상태 판정
    fail_reason = check_fail()
    if fail_reason:
        st.session_state.result = ("lose", fail_reason)
        st.session_state.running = False
        st.snow()
        st.toast("실패! 다시 도전해보세요.", icon="💥")
    elif check_win():
        st.session_state.result = ("win", "모두 무사히 건넜습니다! 🎉")
        st.session_state.running = False
        st.balloons()
        st.toast("성공!", icon="🏆")

# ---------------- 공통 UI 위젯 ----------------
def item_card(name, side):
    here = (st.session_state.positions[name] == side)
    on_boat_side = (st.session_state.boat_side == side)
    is_load = (st.session_state.boat_load == name)
    disabled = not (here and on_boat_side and (name=="person" or st.session_state.boat_load in (None, name)))

    with st.container():
        cl = "card" + (" disabled" if disabled else "")
        st.markdown(f"""
<div class="{cl}">
  <div class="left">
    <span style="font-size:22px">{EMOJI[name]}</span>
    <div><b>{LABEL[name]}</b><br><span style="font-size:12px; color:#666">위치: {'보트 옆' if on_boat_side else '반대 둑'}</span></div>
  </div>
  <div>
    {"<span class='badge'>보트 탑승 중</span>" if is_load else ""}
  </div>
</div>
""", unsafe_allow_html=True)
        btn_label = "보트에 태우기" if not is_load else "보트에서 내리기"
        if st.button(btn_label, key=f"btn-{name}-{side}", disabled=disabled, use_container_width=True):
            toggle_board(name)

def river_scene():
    # 좌/강/우 3단 레이아웃
    left, mid, right = st.columns([1.2, 1.4, 1.2])

    # 좌측 둑
    with left:
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("<div class='bank-title'>🌿 왼쪽 둑</div>", unsafe_allow_html=True)
        for k in ["person","wolf","goat","cabbage"]:
            if st.session_state.positions[k] == "L":
                item_card(k, "L")
        st.markdown("</div>", unsafe_allow_html=True)

    # 강/보트
    with mid:
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("<div class='bank-title'>🌊 강 가운데</div>", unsafe_allow_html=True)
        # 보트 상태
        boat_desc = f"⛵ 보트 위치: {'왼쪽 둑' if st.session_state.boat_side=='L' else '오른쪽 둑'}"
        load_desc = f"탑승객: {LABEL[st.session_state.boat_load]} {EMOJI[st.session_state.boat_load]}" if st.session_state.boat_load else "탑승객: (없음)"
        st.markdown(f"""
<div class="boat-zone">
  <div style="font-size:18px">{boat_desc}</div>
  <div style="margin-top:4px">{load_desc}</div>
  <div style="font-size:13px; color:#666; margin-top:6px">
    * 사람은 보트 이동 시 자동 탑승(보트와 같은 둑에 있어야 함)
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown("<hr class='sep'/>", unsafe_allow_html=True)
        cols = st.columns(3)
        with cols[0]:
            st.button("⬅️ 왼쪽으로", use_container_width=True, on_click=move_boat, disabled=not(st.session_state.running and st.session_state.boat_side=="R"))
        with cols[1]:
            st.button("⛵ 이동", type="primary", use_container_width=True, on_click=move_boot if False else move_boat, disabled=not st.session_state.running)
        with cols[2]:
            st.button("➡️ 오른쪽으로", use_container_width=True, on_click=move_boat, disabled=not(st.session_state.running and st.session_state.boat_side=="L"))

        st.markdown("</div>", unsafe_allow_html=True)

    # 우측 둑
    with right:
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("<div class='bank-title'>🏞️ 오른쪽 둑</div>", unsafe_allow_html=True)
        for k in ["person","wolf","goat","cabbage"]:
            if st.session_state.positions[k] == "R":
                item_card(k, "R")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- 메뉴 화면 ----------------
def menu_screen():
    st.markdown("## 강 건너기 퍼즐 ⛵")
    st.caption("‘늑대·양·양배추’를 모두 무사히 오른쪽 둑으로 옮겨보세요!")

    c1, c2 = st.columns([1,1])
    with c1:
        with st.expander("🎮 게임 설명", expanded=False):
            st.markdown("""
- 배에는 **사람 + 1개**만 탈 수 있어요.  
- 사람이 없는 둑에서 **늑대+양**이 같이 있으면 **양이 먹힘** → 실패.  
- 사람이 없는 둑에서 **양+양배추**가 같이 있으면 **양배추가 먹힘** → 실패.  
- 모든 객체를 **오른쪽 둑**으로 옮기면 성공!  
- **객체 카드를 클릭**해 보트에 태우거나 내릴 수 있어요.  
- **사람은 보트와 같은 둑에 있어야** 배가 이동합니다.
""")
    with c2:
        st.markdown("### ")
        if st.button("🚀 게임 실행", type="primary", use_container_width=True):
            reset_game()
            st.session_state.view = "game"
            st.toast("게임 시작!", icon="🎯")
            st.balloons()

# ---------------- 게임 화면 ----------------
def game_screen():
    st.markdown("### 🚣 게임 화면")
    river_scene()

    st.markdown("---")
    cols = st.columns([1,1,1,1])
    with cols[0]:
        if st.button("↩️ 초기화", use_container_width=True):
            reset_game()
            st.session_state.view = "game"
    with cols[1]:
        if st.button("📜 규칙 보기", use_container_width=True):
            st.info("사람+1개만 탑승 / 사람이 없는 둑에서 (늑대,양) 또는 (양,양배추) 함께 있으면 실패")
    with cols[2]:
        if st.button("🏠 메인으로", use_container_width=True):
            st.session_state.view = "menu"
    with cols[3]:
        st.empty()

    if st.session_state.result:
        kind, msg = st.session_state.result
        if kind == "win":
            st.success(f"🏆 성공! {msg}")
        else:
            st.error(f"❌ 실패! {msg}")
        r1, r2 = st.columns([1,3])
        with r1:
            if st.button("🔁 리플레이", type="primary", use_container_width=True):
                reset_game()
                st.session_state.view = "game"

# ---------------- 라우팅 ----------------
st.markdown("<span class='title-chip'>Wolf-Goat-Cabbage</span>", unsafe_allow_html=True)
st.title("강 건너기 퍼즐 🐺🐑🥬")

if st.session_state.view == "menu":
    menu_screen()
else:
    game_screen()
