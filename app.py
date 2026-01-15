import streamlit as st
import pandas as pd
import random
import time

# ==========================================
# 1. 데이터베이스 (DB Layer)
# ==========================================

stellive_db = {
    # 1기생
    '아이리 칸나': {'group': '1기생', 'trait': '가희(Diva)', 'icon': '🎤', 'atk': 95, 'hp': 40, 'desc': '노래로 적을 제압',
               'color': '#3B82F6', 'type': 'outdoor'},
    '아야츠노 유니': {'group': '1기생', 'trait': '아기(Baby)', 'icon': '🍼', 'atk': 50, 'hp': 85, 'desc': '어그로 담당',
                'color': '#F472B6', 'type': 'indoor'},

    # 2기생
    '시라유키 히나': {'group': '2기생', 'trait': '게이머(Gamer)', 'icon': '🎧', 'atk': 85, 'hp': 50, 'desc': 'FPS 에임 고수',
                'color': '#A855F7', 'type': 'indoor'},
    '네네코 마시로': {'group': '2기생', 'trait': '치유(Healer)', 'icon': '☁️', 'atk': 30, 'hp': 90, 'desc': '팀원 보호',
                'color': '#FCD34D', 'type': 'indoor'},
    '아카네 리제': {'group': '2기생', 'trait': '피지컬(Muscle)', 'icon': '🍷', 'atk': 88, 'hp': 70, 'desc': '강력한 파괴력',
               'color': '#EF4444', 'type': 'outdoor'},
    '아라하시 타비': {'group': '2기생', 'trait': '용사(Hero)', 'icon': '🦈', 'atk': 60, 'hp': 80, 'desc': '기적의 용사',
                'color': '#06B6D4', 'type': 'outdoor'},

    # 사장/기타
    '강지': {'group': '사장', 'trait': '보스(Boss)', 'icon': '👑', 'atk': 99, 'hp': 99, 'desc': '스텔라이브 사장', 'color': '#111827',
           'type': 'outdoor'},
}

monster_db = [
    {"name": "악플러 군단", "hp_base": 300, "atk_base": 80, "icon": "😈", "desc": "멘탈 공격을 합니다."},
    {"name": "저작권 경찰", "hp_base": 500, "atk_base": 120, "icon": "👮‍♂️", "desc": "매우 단단하고 아픕니다."},
    {"name": "방송 송출 오류", "hp_base": 350, "atk_base": 100, "icon": "📺", "desc": "기습적인 공격을 합니다."},
    {"name": "월요일 아침", "hp_base": 800, "atk_base": 150, "icon": "📅", "desc": "직장인의 주적."},
    {"name": "대규모 업데이트", "hp_base": 1000, "atk_base": 200, "icon": "🔥", "desc": "버그가 속출합니다."},
]

weather_db = {
    '맑음': {'icon': '☀️', 'desc': '야외 활동하기 좋습니다.', 'buff': 'outdoor', 'debuff': 'indoor'},
    '비': {'icon': '☔', 'desc': '집에서 게임하기 좋습니다.', 'buff': 'indoor', 'debuff': 'outdoor'},
    '태풍': {'icon': '🌪️', 'desc': '피로도 소모 증가!', 'buff': None, 'debuff': 'all'},
    '오로라': {'icon': '✨', 'desc': '모두의 컨디션 상승.', 'buff': 'all', 'debuff': None},
}

event_db = [
    {'name': '평범한 하루', 'desc': '평화롭습니다.', 'effect': 'none'},
    {'name': '간식 배달', 'desc': '사장님의 간식! (피로도 소모 감소)', 'effect': 'stamina_save'},
    {'name': '장비 고장', 'desc': '장비 이슈 발생. (전투력 감소)', 'effect': 'atk_down'},
    {'name': '팬미팅', 'desc': '응원 버프! (전투력 대폭 상승)', 'effect': 'atk_up'},
]

# ==========================================
# 2. 게임 로직 (Logic Layer)
# ==========================================

st.set_page_config(page_title="스텔라이브 매니저", page_icon="📅", layout="wide")


def init_game():
    st.session_state['day'] = 1
    st.session_state['score'] = 0
    st.session_state['game_over'] = False
    st.session_state['game_phase'] = 'planning'
    st.session_state['battle_log'] = {}
    st.session_state['char_status'] = {name: {'fatigue': 100, 'condition': 0} for name in stellive_db}
    st.session_state['my_team'] = []

    # 타이밍 게임 변수 (Attack Version)
    st.session_state['qte_state'] = 'READY'
    st.session_state['qte_start_time'] = 0

    generate_daily_environment()


def generate_daily_environment():
    weather_key = random.choice(list(weather_db.keys()))
    event = random.choice(event_db)
    st.session_state['today_weather'] = weather_db[weather_key]
    st.session_state['today_weather']['name'] = weather_key
    st.session_state['today_event'] = event

    for name, stat in st.session_state['char_status'].items():
        char_type = stellive_db[name]['type']
        buff = st.session_state['today_weather']['buff']
        debuff = st.session_state['today_weather']['debuff']
        stat['condition'] = 0
        if buff == 'all' or buff == char_type:
            stat['condition'] = 1
        elif debuff == 'all' or debuff == char_type:
            stat['condition'] = -1


def toggle_member(name):
    team = st.session_state['my_team']
    if name in team:
        team.remove(name)
    else:
        if len(team) < 4:
            team.append(name)
        else:
            st.toast("🚫 파티는 최대 4명까지만 가능합니다!", icon="⚠️")


def calculate_base_stats(team_list):
    total_atk, total_hp = 0, 0
    logs = []
    event = st.session_state['today_event']

    for name in team_list:
        char = stellive_db[name]
        stat = st.session_state['char_status'][name]
        atk, hp = char['atk'], char['hp']

        if stat['condition'] > 0:
            atk *= 1.2;
            hp *= 1.1
            logs.append(f"🙂 **{name}**: 날씨 버프 (+20%)")
        elif stat['condition'] < 0:
            atk *= 0.8;
            hp *= 0.9
            logs.append(f"🌧️ **{name}**: 날씨 디버프 (-20%)")

        if stat['fatigue'] < 30:
            atk *= 0.5
            logs.append(f"😫 **{name}**: 지침 (공격력 -50%)")

        total_atk += atk;
        total_hp += hp

    if event['effect'] == 'atk_up':
        total_atk *= 1.3;
        logs.append(f"🔥 이벤트 버프 (+30%)")
    elif event['effect'] == 'atk_down':
        total_atk *= 0.8;
        logs.append(f"📉 이벤트 디버프 (-20%)")

    return int(total_atk), int(total_hp), logs


def process_battle_start(team_list):
    atk, hp, logs = calculate_base_stats(team_list)

    current_monster = monster_db[(st.session_state['day'] - 1) % len(monster_db)]
    monster_hp = current_monster['hp_base'] + (st.session_state['day'] * 50)
    monster_atk = current_monster.get('atk_base', 100) + (st.session_state['day'] * 20)

    st.session_state['battle_temp'] = {
        'base_atk': atk, 'hp': hp, 'logs': logs,
        'monster': current_monster, 'monster_hp': monster_hp, 'monster_atk': monster_atk
    }

    st.session_state['qte_state'] = 'READY'
    st.session_state['game_phase'] = 'attack_minigame'
    st.rerun()


def finalize_battle(multiplier, reaction_time):
    temp = st.session_state['battle_temp']

    final_atk = int(temp['base_atk'] * multiplier)
    remaining_monster_hp = temp['monster_hp'] - final_atk

    crit_log = ""
    if multiplier >= 2.0:
        crit_log = f"⚡ **CRITICAL HIT!** (반응: {reaction_time:.3f}초) 데미지 2배 폭발! 💥"
    elif multiplier > 1.0:
        crit_log = f"✨ **NICE SHOT!** (반응: {reaction_time:.3f}초) 데미지 1.2배 증가"
    else:
        crit_log = f"💨 **일반 공격** (반응: {reaction_time:.3f}초)"

    win = False
    result_msg = ""
    final_hp = temp['hp']
    counter_log = ""

    if remaining_monster_hp <= 0:
        win, result_msg = True, "SUCCESS"
        remaining_monster_hp = 0
        counter_log = "몬스터가 쓰러졌습니다! 반격받지 않습니다."
    else:
        monster_dmg = temp['monster_atk']
        final_hp -= monster_dmg
        counter_log = f"😡 몬스터가 버텨냈습니다! 반격 데미지 -{monster_dmg}"

        if final_hp > 0:
            win, result_msg = True, "DRAW"
        else:
            win, result_msg = False, "FAIL"

    st.session_state['battle_log'] = {
        'atk': final_atk, 'hp': final_hp,
        'monster_hp': remaining_monster_hp,
        'logs': temp['logs'], 'crit_log': crit_log, 'counter_log': counter_log,
        'win': win, 'result_msg': result_msg,
        'team': st.session_state['my_team'], 'monster': temp['monster']
    }

    st.session_state['game_phase'] = 'result'
    st.rerun()


def end_day():
    team_list = st.session_state['battle_log']['team']
    win = st.session_state['battle_log']['win']

    cost = 30
    if st.session_state['today_weather']['name'] == '태풍': cost = 50
    if st.session_state['today_event']['effect'] == 'stamina_save': cost = 10

    for name in stellive_db:
        status = st.session_state['char_status'][name]
        if name in team_list:
            status['fatigue'] = max(0, status['fatigue'] - cost)
        else:
            status['fatigue'] = min(100, status['fatigue'] + 20)

    if win: st.session_state['score'] += 100 * st.session_state['day']
    st.session_state['day'] += 1

    if st.session_state['day'] > 7:
        st.session_state['game_over'] = True
    else:
        generate_daily_environment()

    st.session_state['game_phase'] = 'planning'
    st.rerun()


# ==========================================
# 3. UI 렌더링 (View Layer)
# ==========================================

if 'day' not in st.session_state: init_game()

# --- 엔딩 화면 ---
if st.session_state['game_over']:
    st.balloons()
    st.title("🏆 매니지먼트 최종 결과")
    st.metric("최종 점수", st.session_state['score'])
    if st.button("🔄 처음부터 다시 하기"):
        init_game()
        st.rerun()
    st.stop()

# --- 메인 게임 화면 ---
c1, c2, c3 = st.columns([1, 2, 2])
with c1: st.markdown(f"### 📅 Day {st.session_state['day']}")
with c2:
    w = st.session_state['today_weather']
    st.info(f"날씨: {w['name']} {w['icon']} ({w['desc']})")
with c3:
    e = st.session_state['today_event']
    st.warning(f"이벤트: {e['name']} ({e['desc']})")

st.divider()

# --- [Phase 1: 계획 단계] ---
if st.session_state['game_phase'] == 'planning':

    today_monster = monster_db[(st.session_state['day'] - 1) % len(monster_db)]
    m_hp = today_monster['hp_base'] + (st.session_state['day'] * 50)
    m_atk = today_monster.get('atk_base', 100) + (st.session_state['day'] * 20)

    with st.expander(f"😈 금일 작전 목표: {today_monster['name']}", expanded=True):
        mc1, mc2 = st.columns([1, 4])
        with mc1: st.markdown(f"<div style='font-size:50px; text-align:center;'>{today_monster['icon']}</div>",
                              unsafe_allow_html=True)
        with mc2:
            st.write(f"**체력:** {m_hp} | **공격력:** {m_atk} | **특징:** {today_monster['desc']}")
            st.caption("공격 타이밍을 맞춰 데미지 2배(크리티컬)를 노리세요!")

    st.write("")

    # 파티 편성
    st.subheader("🚩 파티 편성 (4명)")
    my_team = st.session_state['my_team']
    cols_team = st.columns(4)

    for i in range(4):
        with cols_team[i]:
            if i < len(my_team):
                char_name = my_team[i]
                char_info = stellive_db[char_name]
                st.info(f"**{char_name}**")
                st.markdown(f"<div style='font-size:30px; text-align:center;'>{char_info['icon']}</div>",
                            unsafe_allow_html=True)
                if st.button("제외", key=f"remove_{i}"):
                    toggle_member(char_name)
                    st.rerun()
            else:
                st.markdown(
                    "<div style='border: 2px dashed #ccc; border-radius:10px; height: 100px; display:flex; align-items:center; justify-content:center; color:#ccc;'>EMPTY</div>",
                    unsafe_allow_html=True)

    btn_disabled = len(my_team) != 4
    if st.button("🔥 전투 출격 (MISSION START)", type="primary", use_container_width=True, disabled=btn_disabled):
        process_battle_start(my_team)

    st.divider()

    # 대기실
    st.subheader("👥 대기실 (멤버 선택)")
    tab_titles = ["ALL", "1기생", "2기생", "사장/기타"]
    tabs = st.tabs(tab_titles)

    filter_groups = {"ALL": None, "1기생": "1기생", "2기생": "2기생", "사장/기타": ["사장", "3기생"]}

    for tab, title in zip(tabs, tab_titles):
        with tab:
            target_group = filter_groups[title]
            row_cols = st.columns(4)
            idx = 0
            for name, info in stellive_db.items():
                if target_group:
                    if isinstance(target_group, list):
                        if info.get('group', '기타') not in target_group: continue
                    else:
                        if info.get('group', '기타') != target_group: continue

                status = st.session_state['char_status'][name]
                fatigue = status['fatigue']
                is_selected = name in my_team
                border_style = "2px solid #3B82F6" if is_selected else "1px solid #ddd"

                # [MODIFIED] 선택 상태에 따른 배경 및 글자 색상 로직 수정
                if is_selected:
                    bg_color = "#3C3CAC"  # 선택된 색상
                    text_color = "white"  # 선택 시 글자색은 흰색
                else:
                    bg_color = "#FFFFFF"  # 해제된 색상 (흰색)
                    text_color = "black"  # 해제 시 글자색은 검은색

                btn_label = "해제" if is_selected else "선택"
                btn_type = "secondary" if is_selected else "primary"

                if fatigue >= 80:
                    f_col = "blue"
                elif fatigue >= 40:
                    f_col = "green"
                elif fatigue >= 10:
                    f_col = "orange"
                else:
                    f_col = "red"

                with row_cols[idx % 4]:
                    # [MODIFIED] div 스타일에 color:{text_color} 추가하여 글자색 반영
                    st.markdown(f"""
                    <div style="border:{border_style}; background-color:{bg_color}; color:{text_color}; padding:10px; border-radius:10px; margin-bottom:10px; text-align:center;">
                        <div style="font-size:30px;">{info['icon']}</div>
                        <div style="font-weight:bold;">{name}</div>
                        <div style="color:{f_col}; font-weight:bold; font-size:14px;">피로도 {fatigue}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(btn_label, key=f"btn_{title}_{name}", type=btn_type, use_container_width=True):
                        toggle_member(name)
                        st.rerun()
                idx += 1

# --- [Phase 1.5: 공격 타이밍 미니게임] ---
elif st.session_state['game_phase'] == 'attack_minigame':

    st.markdown("## ⚔️ 아군 공격 턴!")
    st.write("스킬 에너지를 모으는 중입니다... 신호가 오면 **발사**하세요!")

    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])

    with col_center:
        placeholder = st.empty()

        # [단계 1] 에너지 충전 (READY)
        if st.session_state['qte_state'] == 'READY':
            with placeholder.container():
                st.info("파티원들이 자세를 잡습니다...")
                st.markdown("<h3 style='text-align:center;'>준비...</h3>", unsafe_allow_html=True)

                if st.button("🚀 공격 준비 (클릭)", type="primary", use_container_width=True):
                    st.session_state['qte_state'] = 'WAITING'
                    st.rerun()

        # [단계 2] 눈치 게임 (WAITING)
        elif st.session_state['qte_state'] == 'WAITING':
            with placeholder.container():
                st.warning("기회를 노리는 중...")
                st.markdown("<div style='text-align:center; font-size:40px;'>...</div>", unsafe_allow_html=True)

                time.sleep(random.uniform(2.0, 4.0))

                st.session_state['qte_start_time'] = time.time()
                st.session_state['qte_state'] = 'ACTION'
                st.rerun()

        # [단계 3] 발사 (ACTION)
        elif st.session_state['qte_state'] == 'ACTION':
            with placeholder.container():
                st.error("지금이야!!! 발사!!!")
                st.markdown("<h1 style='text-align:center; color:red; font-size:60px;'>💥 FIRE!!!</h1>",
                            unsafe_allow_html=True)

                if st.button("🔥 필살기 발동!! (CLICK)", type="primary", use_container_width=True, key="atk_btn"):
                    reaction = time.time() - st.session_state['qte_start_time']

                    multiplier = 1.0
                    if reaction < 0.35:
                        multiplier = 2.0  # 대성공
                    elif reaction < 0.8:
                        multiplier = 1.2  # 성공
                    else:
                        multiplier = 1.0  # 보통

                    finalize_battle(multiplier, reaction)

# --- [Phase 2: 결과 단계] ---
elif st.session_state['game_phase'] == 'result':
    st.subheader("📊 작전 결과 보고")
    log = st.session_state['battle_log']
    monster = log['monster']

    if log['result_msg'] == 'SUCCESS':
        st.success("🎉 작전 성공! 적을 물리쳤습니다.")
        st.balloons()
    elif log['result_msg'] == 'DRAW':
        st.warning("⚠️ 작전 무승부. 적을 처치하진 못했지만 생존했습니다.")
    else:
        st.error("💀 작전 실패. 아군이 전멸했습니다.")

    st.info(log['crit_log'])

    if log['counter_log']:
        st.warning(log['counter_log'])

    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.write(f"**아군 총 공격력:** {log['atk']}")
        st.write(f"**아군 남은 체력:** {log['hp']}")
        with st.expander("버프 로그 상세"):
            for l in log['logs']: st.write(l)
    with c_res2:
        st.write(f"**적 남은 체력:** {log['monster_hp']}")
        st.write(f"**적:** {monster['name']}")

    st.write("---")

    cost = 30
    if st.session_state['today_weather']['name'] == '태풍': cost = 50
    if st.session_state['today_event']['effect'] == 'stamina_save': cost = 10

    st.info(f"💡 **피로도 정산:** 전투 참여 멤버 -{cost} / 휴식 멤버 +20")

    if st.button("🌙 하루 마무리 (다음날로 이동)", type="primary"):
        end_day()