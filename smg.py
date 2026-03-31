import streamlit as st
import random
import time
import pandas as pd
import os
from collections import Counter
## 수정

# ==========================================
# 🎨 아이콘/이모지 매핑 설정
# ==========================================
GAME_ICONS = {
    '신화': '💎', '전설': '🌟', '용': '🐲', '무희': '💃',
    '동물': '🦄', '탱커': '🛡️', '현대': '🏙️', '인간': '👤',
    '가희': '🎤', '우주': '🌌', '뱀파이어': '🧛', '이세계': '🪐',
    '보스': '👑',
    '바이러스': '👾', '오니': '👺', '허수아비': '🎯',
    '악플': '😈', 'AI': '🤖️', '월요일 아침': '📅',
    '트로피': '🏆', 'TV': '📺',
    '기본': '🔹', '몬스터기본': '👾'
}

DEFAULT_ICON = '🔹'

# ==========================================
# ⚙️ 게임 밸런스 & 시너지 설정 (마음대로 수정하세요!)
# ==========================================

# 1. QTE 발동 키워드 (2개 이상 모이면 발동)
QTE_KEYWORDS = ['용', '전설', '보스', '이세계']

# 2. 특성 시너지 설정
SYNERGY_CONFIG = {
    '무희': {2: 1.3, 3: 2.0},
    '탱커': {2: 1.3},
    '가희': {2: 1.3, 3: 2.0},
    '전설': {2: 1.3, 3: 2.0},
    '용': {1: 1.5},
    '인간': {2: 1.3, 3: 2.0},
    '이세계': {2: 1.3, 3: 2.0},
    '현대': {2: 1.3, 3: 2.0},
    '보스': {1: 2.0},
}

# 3. 각종 배율 설정
BALANCE_CONFIG = {
    'MAX_TEAM_SIZE': 4,
    'MAX_STAR_LEVEL': 4,
    'MERGE_REQUIRE_COUNT': 3,  # 승급에 필요한 동일 캐릭터 카드 수
    'DAILY_DRAW_COUNT': 4,
    'STARTER_CANDIDATE_COUNT': 3,
    'MAX_DAYS': 7,
    'STAR_BONUS_PER_LEVEL': 0.5,
    'WEATHER_BUFF': 1.2,
    'WEATHER_DEBUFF': 0.8,
    'EVENT_BUFF': 1.3,
    'EVENT_DEBUFF': 0.8,
    'QTE': {
        'PERFECT_TIME': 0.35, 'GREAT_TIME': 0.80,
        'PERFECT_MULT': 2.0, 'GREAT_MULT': 1.5, 'NORMAL_MULT': 1.0
    }
}


# ==========================================
# 📂 데이터 매니저 (엑셀 로딩)
# ==========================================
@st.cache_data(show_spinner=False)
def load_game_data():
    excel_path = "data/game_data.xlsx"

    if not os.path.exists(excel_path):
        st.error(f"🚨 데이터 파일이 없습니다: {excel_path}")
        st.stop()

    try:
        xls = pd.read_excel(excel_path, sheet_name=None, engine='openpyxl')

        # A. 캐릭터
        df_char = xls['character_stat']
        char_db = {}
        for _, row in df_char.iterrows():
            traits_str = str(row['trait'])
            raw_traits = [t.strip() for t in traits_str.split(',')]
            fancy_traits = [f"{GAME_ICONS.get(t, GAME_ICONS['기본'])} {t}" for t in raw_traits]

            char_db[row['name']] = {
                'group': row['group'],
                'traits': raw_traits,  # 순수 특성
                'fancy_traits': fancy_traits,  # 표시용 특성
                'atk': int(row['atk']),
                'desc': row['desc'],
                'color': row['color'],
                'type': row['type']
            }

        # B. 몬스터
        df_mon = xls['monster_stat']
        mon_db = []
        for _, row in df_mon.iterrows():
            icon_key = str(row['icon']).strip()
            mon_db.append({
                'name': row['name'],
                'target_score': int(row['target_score']),
                'icon': GAME_ICONS.get(icon_key, GAME_ICONS['몬스터기본']),
                'desc': row['desc']
            })

        # C. 일일 이벤트
        df_evt = xls['event']
        evt_db = []
        for _, row in df_evt.iterrows():
            evt_db.append({
                'name': row['name'],
                'desc': row['desc'],
                'effect': row['effect']
            })

        # D. 전투 이벤트
        df_battle = xls['battle_event']
        battle_db = []
        for _, row in df_battle.iterrows():
            battle_db.append({
                'event': row['event'],
                'effect': row['effect'],
                'mult': float(row['mult'])
            })

        return char_db, mon_db, evt_db, battle_db

    except Exception as e:
        st.error(f"🚨 엑셀 로딩 중 오류 발생: {e}")
        st.stop()


stellive_db, monster_db, event_db, battle_events = load_game_data()

weather_db = {
    '맑음': {'icon': '☀️', 'desc': '야외 활동하기 좋습니다.', 'buff': 'outdoor', 'debuff': 'indoor'},
    '비': {'icon': '☔', 'desc': '집에서 게임하기 좋습니다.', 'buff': 'indoor', 'debuff': 'outdoor'},
    '태풍': {'icon': '🌪️', 'desc': '날씨가 험합니다.', 'buff': None, 'debuff': 'all'},
    '오로라': {'icon': '🌌', 'desc': '모두의 컨디션 상승.', 'buff': 'all', 'debuff': None},
}

# ==========================================
# 🛠️ 핵심 로직 함수
# ==========================================
st.set_page_config(page_title="스텔맨, 최고가 되어라", page_icon="🏆", layout="wide")


# 시너지별 공격력
def get_active_synergies(team_list):
    keyword_counts = Counter()
    for name in team_list:
        char = stellive_db[name]
        keyword_counts[char['group']] += 1
        for trait in char['traits']:
            keyword_counts[trait] += 1

    active = {}
    for key, tiers in SYNERGY_CONFIG.items():
        count = keyword_counts[key]

        # 🌟 [핵심 추가] QTE 발동(1명 이상) 키워드라면 공격력 시너지에서 제외!
        if key in QTE_KEYWORDS and count >= 1:
            continue

        best_mult = 1.0

        # 설정된 단계(필요 인원)를 내림차순(가장 높은 숫자부터)으로 검사
        for req_count in sorted(tiers.keys(), reverse=True):
            if count >= req_count:
                best_mult = tiers[req_count]
                break  # 가장 높은 단계를 찾았으므로 중단

        if best_mult > 1.0:
            active[key] = best_mult

    return active


def calculate_base_stats(team_list):
    total_atk = 0
    logs = []
    event = st.session_state['today_event']
    active_synergies = get_active_synergies(team_list)  # [NEW] 시너지 불러오기

    for name in team_list:
        char = stellive_db[name]
        stat = st.session_state['char_status'][name]
        atk = char['atk']

        # 1. 성급 보너스
        star_multiplier = 1.0 + (stat['star'] - 1) * BALANCE_CONFIG['STAR_BONUS_PER_LEVEL']
        atk = int(atk * star_multiplier)
        if stat['star'] > 1:
            logs.append(f"⭐ **{name}**: {stat['star']}성 위력 (x{star_multiplier})")

        # 2. 날씨 보정
        if stat['condition'] > 0:
            atk = int(atk * BALANCE_CONFIG['WEATHER_BUFF'])
            logs.append(f"🙂 **{name}**: 날씨 버프 (x{BALANCE_CONFIG['WEATHER_BUFF']})")
        elif stat['condition'] < 0:
            atk = int(atk * BALANCE_CONFIG['WEATHER_DEBUFF'])
            logs.append(f"🌧️ **{name}**: 날씨 디버프 (x{BALANCE_CONFIG['WEATHER_DEBUFF']})")

        # 3. [NEW] 시너지 보정 (조건 충족한 본인만 버프 받음)
        char_syn_mult = 1.0
        applied_syns = []
        for syn_key, mult in active_synergies.items():
            # 그룹이 일치하거나, 특성에 포함되어 있다면
            if char['group'] == syn_key or syn_key in char['traits']:
                char_syn_mult *= mult
                applied_syns.append(syn_key)

        if char_syn_mult > 1.0:
            atk = int(atk * char_syn_mult)
            logs.append(f"🔗 **{name}**: 시너지 적용 ({','.join(applied_syns)} x{char_syn_mult:.2f})")

        total_atk += atk

    # 4. 이벤트 보정
    if event['effect'] == 'atk_up':
        total_atk = int(total_atk * BALANCE_CONFIG['EVENT_BUFF'])
        logs.append(f"🔥 이벤트 버프 (x{BALANCE_CONFIG['EVENT_BUFF']})")
    elif event['effect'] == 'atk_down':
        total_atk = int(total_atk * BALANCE_CONFIG['EVENT_DEBUFF'])
        logs.append(f"📉 이벤트 디버프 (x{BALANCE_CONFIG['EVENT_DEBUFF']})")

    return int(total_atk), logs


def process_battle_start(team_list):
    atk, logs = calculate_base_stats(team_list)
    current_monster = monster_db[(st.session_state['day'] - 1) % len(monster_db)]

    st.session_state['battle_temp'] = {
        'base_atk': atk,
        'logs': logs,
        'monster': current_monster,
        'target_score': current_monster['target_score']
    }

    # 키워드 기준으로 그룹/특성 수집 (이모지 무시)
    keyword_counts = Counter()
    for name in team_list:
        char = stellive_db[name]
        keyword_counts[char['group']] += 1
        for trait in char['traits']:
            keyword_counts[trait] += 1

    # QTE 시너지 발동 여부 확인
    synergy_trait = None
    for qte_key in QTE_KEYWORDS:
        if keyword_counts[qte_key] >= 2:
            synergy_trait = qte_key
            break

    if synergy_trait:
        st.session_state['synergy_name'] = synergy_trait
        st.toast(f"✨ '{synergy_trait}' 특성 공명 발동! 연계 공격 기회!", icon="⚔️")
        st.session_state['qte_state'] = 'READY'
        st.session_state['game_phase'] = 'attack_minigame'
        st.rerun()
    else:
        st.session_state['game_phase'] = 'calculating'
        st.rerun()


def finalize_battle(multiplier, reaction_time):
    temp = st.session_state['battle_temp']
    team_list = st.session_state['my_team']
    base_total_atk = temp['base_atk']

    total_damage = 0
    detailed_logs = []

    for name in team_list:
        status = st.session_state['char_status'][name]
        action = random.choice(battle_events)
        final_char_atk = int(base_total_atk / len(team_list) * action['mult'] * multiplier)
        total_damage += final_char_atk

        if mult > 1.2:
            style = "font-size: 1.2em; color: #ff8c00; font-weight: bold; padding: 5px;"
            prefix = "💥 CRITICAL:"
        elif mult < 1.0:
            style = "font-size: 0.9em; color: #808080; font-style: italic; padding: 2px;"
            prefix = "💧 WEAK:"
        else:
            style = "font-size: 1.0em; color: #ffffff; padding: 3px;"
            prefix = "HIT:"

        star_str = "⭐" * status['star']
        log_msg = f"<div style='{style} margin-bottom: 5px;'>{prefix} <b>{name}{star_str}</b>: {action['effect']} (DMG: {final_char_atk})</div>"
        detailed_logs.append(log_msg)

    st.session_state['total_score'] += total_damage
    target_score = temp['target_score']
    ratio = (total_damage / target_score) * 100

    grade = "C"
    if ratio >= 200:
        grade = "SSS"
    elif ratio >= 150:
        grade = "SS"
    elif ratio >= 120:
        grade = "S"
    elif ratio >= 100:
        grade = "A"
    elif ratio >= 80:
        grade = "B"

    grade_color = "#FFD700" if "S" in grade else "#FFFFFF"
    result_msg = f"<h2 style='color:{grade_color}; text-align:center;'>GRADE: {grade}</h2>"

    qte_cfg = BALANCE_CONFIG['QTE']
    if multiplier >= qte_cfg['PERFECT_MULT']:
        crit_log = f"⚡ **PERFECT QTE!** (반응: {reaction_time:.3f}초) 데미지 {multiplier}배!"
    elif multiplier >= qte_cfg['GREAT_MULT']:
        crit_log = f"✨ **GREAT QTE!** (반응: {reaction_time:.3f}초) 데미지 {multiplier}배!"
    else:
        crit_log = f"💨 **NORMAL QTE** (반응: {reaction_time:.3f}초) 기본 데미지로 공격."

    st.session_state['battle_log'] = {
        'damage': total_damage, 'logs': temp['logs'],
        'detailed_logs': detailed_logs, 'crit_log': crit_log,
        'result_msg': result_msg, 'grade': grade, 'ratio': ratio,
        'team': team_list, 'monster': temp['monster']
    }
    st.session_state['log_animated'] = False
    st.session_state['game_phase'] = 'result'
    st.rerun()


def draw_new_characters(count=4):
    all_names = list(stellive_db.keys())
    drawn_list = []
    for _ in range(count):
        pick = random.choice(all_names)
        st.session_state['char_status'][pick]['count'] += 1
        drawn_list.append(pick)
    drawn_counter = Counter(drawn_list)
    msg_list = [f"{k} x{v}" if v > 1 else k for k, v in drawn_counter.items()]
    st.toast(f"🎁 멤버 영입! {', '.join(msg_list)}", icon="✨")


def init_game():
    st.session_state['day'] = 1
    st.session_state['total_score'] = 0
    st.session_state['game_over'] = False
    st.session_state['game_phase'] = 'starter_selection'
    st.session_state['battle_log'] = {}
    st.session_state['char_status'] = {name: {'condition': 0, 'count': 0, 'star': 1} for name in stellive_db}
    st.session_state['my_team'] = []
    st.session_state['qte_state'] = 'READY'
    st.session_state['qte_start_time'] = 0
    st.session_state['starter_candidates'] = random.sample(list(stellive_db.keys()),
                                                           BALANCE_CONFIG['STARTER_CANDIDATE_COUNT'])
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
    status = st.session_state['char_status'][name]
    if name in team:
        team.remove(name)
    else:
        if status['count'] <= 0:
            st.toast(f"🚫 {name} 멤버를 보유하고 있지 않습니다!", icon="🔒")
            return
        if len(team) < BALANCE_CONFIG['MAX_TEAM_SIZE']:
            team.append(name)
        else:
            st.toast("🚫 파티는 최대 4명까지만 가능합니다!", icon="⚠️")


def merge_member(name):
    status = st.session_state['char_status'][name]

    if status['star'] >= BALANCE_CONFIG['MAX_STAR_LEVEL']:
        st.toast(f"🚫 {name} 멤버는 이미 최고 레벨({BALANCE_CONFIG['MAX_STAR_LEVEL']}성)입니다!", icon="⭐")
        return

    if status['count'] >= BALANCE_CONFIG['MERGE_REQUIRE_COUNT']:
        status['count'] -= (BALANCE_CONFIG['MERGE_REQUIRE_COUNT'] - 1)
        status['star'] += 1
        st.toast(f"🎉 {name} {status['star']}성으로 승급 완료! (공격력 대폭 상승)", icon="🆙")
        st.rerun()


def end_day():
    st.session_state['day'] += 1
    if st.session_state['day'] > BALANCE_CONFIG['MAX_DAYS']:
        st.session_state['game_over'] = True
    else:
        generate_daily_environment()
        draw_new_characters(BALANCE_CONFIG['DAILY_DRAW_COUNT'])
    st.session_state['game_phase'] = 'planning'
    st.rerun()


def get_character_card_html(name, info, status, is_selected):
    count = status['count']
    star = status['star']
    is_not_owned = count <= 0

    if is_not_owned:
        bg_color, text_color = "#F9F9F9", "#BBBBBB"
        border_style = "1px dashed #DDDDDD"
        trait_bg = "#EEEEEE"
    elif is_selected:
        bg_color, text_color = "#5B5B96", "white"
        trait_bg = "rgba(255, 255, 255, 0.2)"
        border_style = "2px solid #3B82F6"
    else:
        bg_color, text_color = "#FFFFFF", "black"
        trait_bg = "#f0f2f6"
        border_style = "1px solid #e0e0e0"

    traits_html = ""
    for t in info['fancy_traits']:
        traits_html += f"<span style='display:inline-block; background:{trait_bg}; padding:2px 6px; margin:2px; border-radius:4px; font-size:11px;'>{t}</span>"

    stars_html = "⭐" * star
    count_badge = ""
    if count > 0:
        count_color = "#555" if not is_selected else "white"
        count_badge = f"<div style='margin-top:5px; font-weight:bold; font-size:14px; color:{count_color};'>x {count}</div>"

    opacity = "0.6" if is_not_owned else "1.0"
    return f"""
    <div style="border:{border_style}; background-color:{bg_color}; color:{text_color}; padding:12px 5px; border-radius:12px; margin-bottom:10px; text-align:center; height:100%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); opacity: {opacity};">
        <div style="font-size:12px; margin-bottom:2px;">{stars_html}</div>
        <div style="font-weight:bold; font-size:18px; margin-bottom:8px;">{name}</div>
        <div style="margin-bottom:10px; line-height:1.4;">{traits_html}</div>
        <div style="font-size:12px; opacity:0.8; margin-bottom: 5px;">{info['desc']}</div>
        {count_badge}
    </div>
    """


# ==========================================
# 3. UI 렌더링 (View Layer)
# ==========================================
if 'day' not in st.session_state: init_game()

if st.session_state['game_over']:
    st.balloons()
    st.title("🏆 시즌 종료: 최종 성적표")
    st.metric("최종 누적 점수", st.session_state['total_score'])
    st.write("7일간의 활동이 모두 끝났습니다! 수고하셨습니다.")
    if st.button("🔄 새로운 시즌 시작하기"):
        init_game()
        st.rerun()
    st.stop()

if st.session_state['game_phase'] == 'starter_selection':
    st.markdown("## 🌟 파트너 선택")
    st.write("이번 시즌을 함께할 메인 멤버를 선택해주세요.")
    st.caption("선택한 멤버 외에 **3명의 추가 멤버(중복 없음)**가 지급되어 바로 4인 파티를 꾸릴 수 있습니다.")
    candidates = st.session_state['starter_candidates']
    cols = st.columns(3)
    for i, name in enumerate(candidates):
        info = stellive_db[name]
        with cols[i]:
            card_html = get_character_card_html(name, info, {'count': 1, 'fatigue': 100, 'star': 1}, False)
            st.markdown(card_html, unsafe_allow_html=True)
            if st.button(f"👉 {name} 선택", key=f"start_{name}", use_container_width=True):
                st.session_state['char_status'][name]['count'] += 1
                all_names = list(stellive_db.keys())
                remaining_pool = [n for n in all_names if n != name]
                others = random.sample(remaining_pool, BALANCE_CONFIG['STARTER_BONUS_MEMBERS'])
                for other in others:
                    st.session_state['char_status'][other]['count'] += 1
                st.toast(f"🎉 {name} + {', '.join(others)} 영입 완료!", icon="🎁")
                st.session_state['game_phase'] = 'planning'
                st.rerun()
    st.stop()

c1, c2, c3 = st.columns([1, 2, 2])
with c1:
    st.markdown(f"### 📅 Day {st.session_state['day']}")
    st.caption(f"누적 점수: {st.session_state['total_score']:,}")
with c2:
    w = st.session_state['today_weather']
    st.info(f"날씨: {w['name']} {w['icon']} ({w['desc']})")
with c3:
    e = st.session_state['today_event']
    st.warning(f"이벤트: {e['name']} ({e['desc']})")
st.divider()

if st.session_state['game_phase'] == 'planning':
    today_monster = monster_db[(st.session_state['day'] - 1) % len(monster_db)]

    with st.expander(f"🎯 금일의 목표: {today_monster['name']}", expanded=True):
        mc1, mc2 = st.columns([1, 4])
        with mc1: st.markdown(f"<div style='font-size:50px; text-align:center;'>{today_monster['icon']}</div>",
                              unsafe_allow_html=True)
        with mc2:
            st.write(f"**목표 점수:** {today_monster['target_score']:,} | **특징:** {today_monster['desc']}")
            st.caption("최고의 조합으로 목표 점수를 돌파하여 S등급을 노리세요!")

    st.subheader("🚩 멤버 배치 (4명)")
    my_team = st.session_state['my_team']
    cols_team = st.columns(4)

    for i in range(4):
        with cols_team[i]:
            if i < len(my_team):
                char_name = my_team[i]
                card_html = get_character_card_html(char_name, stellive_db[char_name],
                                                    st.session_state['char_status'][char_name], True)
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button("제외", key=f"remove_{i}", use_container_width=True):
                    toggle_member(char_name)
                    st.rerun()
            else:
                st.markdown(
                    "<div style='border: 2px dashed #ccc; border-radius:10px; height: 150px; display:flex; align-items:center; justify-content:center; color:#ccc;'>EMPTY</div>",
                    unsafe_allow_html=True)

    display_synergies = []

    # [NEW] 시너지 시각화 UI (다단계 적용)
    if len(my_team) > 0:
        keyword_counts = Counter()
        for name in my_team:
            char = stellive_db[name]
            keyword_counts[char['group']] += 1
            for trait in char['traits']:
                keyword_counts[trait] += 1

        # 1. 다단계 공격력 시너지 시각화
        for key, tiers in SYNERGY_CONFIG.items():
            count = keyword_counts[key]

            if key in QTE_KEYWORDS and count >= 1:
                continue

            best_mult = 1.0
            for req_count in sorted(tiers.keys(), reverse=True):
                if count >= req_count:
                    best_mult = tiers[req_count]
                    break

            if best_mult > 1.0:
                display_synergies.append({
                    'name': key, 'lv': count,  # 현재 모은 인원 수 표시
                    'effect': f"공격력 x{best_mult}",
                    'color': 'linear-gradient(45deg, #9393F5, #53538A)'
                })

        # 2. QTE 시너지
        for qte_key in QTE_KEYWORDS:
            if keyword_counts[qte_key] >= 2:
                display_synergies.append({
                    'name': qte_key, 'lv': keyword_counts[qte_key],
                    'effect': "QTE 발동!",
                    'color': 'linear-gradient(45deg, #FF416C, #FF4B2B)'
                })

    with st.container(border=True):
        st.markdown("##### 🔗 현재 발동 시너지")
        st.write("")  # 여백
        if not display_synergies:
            st.caption("발동된 시너지가 없습니다. 특성을 맞춰보세요!")
        else:
            syn_cols = st.columns(len(display_synergies))
            for idx, syn in enumerate(display_synergies):
                with syn_cols[idx % len(syn_cols)]:
                    st.markdown(f"""
                        <div style="background: {syn['color']}; padding: 8px; border-radius: 8px; color: white; text-align: center;">
                            <div style="font-size: 14px; font-weight: bold;">{syn['name']} Lv.{syn['lv']}</div>
                            <div style="font-size: 11px;">{syn['effect']}</div>
                        </div>
                        """, unsafe_allow_html=True)

    if st.button("🔥 전투 시작 (START)", type="primary", use_container_width=True,
                 disabled=len(my_team) != BALANCE_CONFIG['MAX_TEAM_SIZE']):
        process_battle_start(my_team)

    st.divider()
    st.subheader("👥 대기실 (멤버 선택)")
    tab_titles = ["ALL", "1기생", "2기생", "3기생", "사장/기타"]
    tabs = st.tabs(tab_titles)
    filter_groups = {"ALL": None, "1기생": "1기생", "2기생": "2기생", "3기생": "3기생", "사장/기타": "사장"}

    for tab, title in zip(tabs, tab_titles):
        with tab:
            target_group = filter_groups[title]
            row_cols = st.columns(4)
            idx = 0
            for name, info in stellive_db.items():
                if target_group and info.get('group', '기타') != target_group and target_group is not None: continue
                status = st.session_state['char_status'][name]
                is_selected = name in my_team
                is_owned = status['count'] > 0

                btn_label = "해제" if is_selected else "선택"
                btn_type = "secondary" if is_selected else "primary"
                if not is_owned: btn_label = "미보유"

                with row_cols[idx % 4]:
                    card_html = get_character_card_html(name, info, status, is_selected)
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button(btn_label, key=f"btn_{title}_{name}", type=btn_type, use_container_width=True,
                                 disabled=not is_owned):
                        toggle_member(name)
                        st.rerun()
                    if status['count'] >= BALANCE_CONFIG['MERGE_REQUIRE_COUNT']:
                        if status['star'] < BALANCE_CONFIG['MAX_STAR_LEVEL']:
                            # 아직 4성이 아니면 MERGE 버튼 표시
                            if st.button(f"MERGE", key=f"merge_{title}_{name}", type="primary",
                                         use_container_width=True):
                                merge_member(name)
                        else:
                            # 4성이면 누를 수 없는 MAX 버튼 표시
                            st.button(f"MAX ⭐", key=f"max_{title}_{name}", disabled=True, use_container_width=True)
                idx += 1

elif st.session_state['game_phase'] == 'attack_minigame':
    synergy = st.session_state.get('synergy_name', '알 수 없음')
    st.markdown(f"## ⚔️ '{synergy}' 특성 공명!")
    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])
    with col_center:
        placeholder = st.empty()
        if st.session_state['qte_state'] == 'READY':
            with placeholder.container():
                st.info("준비...")
                if st.button("🚀 준비 완료", type="primary", use_container_width=True):
                    st.session_state['qte_state'] = 'WAITING'
                    st.rerun()
        elif st.session_state['qte_state'] == 'WAITING':
            with placeholder.container():
                st.warning("기다리세요...")
                time.sleep(random.uniform(2.0, 4.0))
                st.session_state['qte_start_time'] = time.time()
                st.session_state['qte_state'] = 'ACTION'
                st.rerun()
        elif st.session_state['qte_state'] == 'ACTION':
            with placeholder.container():
                st.error("지금!!!")
                if st.button("🔥 발사!!", type="primary", use_container_width=True, key="atk_btn"):
                    reaction = time.time() - st.session_state['qte_start_time']
                    qte = BALANCE_CONFIG['QTE']
                    multiplier = qte['PERFECT_MULT'] if reaction < qte['PERFECT_TIME'] else (
                        qte['GREAT_MULT'] if reaction < qte['GREAT_TIME'] else qte['NORMAL_MULT'])
                    finalize_battle(multiplier, reaction)

elif st.session_state['game_phase'] == 'calculating':
    st.markdown("## ⚔️ 일반 공격")
    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])
    with col_center:
        if st.button("⚔️ 공격 시작", type="primary", use_container_width=True):
            finalize_battle(1.0, 0.0)

# --- [Phase 2: 결과 단계] ---
elif st.session_state['game_phase'] == 'result':
    st.subheader("📊 공격 결과")
    log = st.session_state['battle_log']
    monster = log['monster']

    # 🌟 [NEW] 긴장감을 위한 자리 표시자(Placeholder) 세팅
    # 이 공간들에 순서대로 데이터가 채워집니다.
    grade_area = st.empty()
    qte_area = st.empty()
    battle_log_area = st.empty()

    st.divider()

    c_res1, c_res2 = st.columns(2)
    with c_res1:
        dmg_area = st.empty()
        with st.expander("버프 적용 상세 로그"):
            for l in log['logs']: st.write(l)
    with c_res2:
        st.metric("🎯 목표 점수", f"{monster['target_score']:,}")
        st.write(f"**상대:** {monster['name']}")

    st.write("---")
    btn_area = st.empty()  # 다음 날로 넘어가는 버튼 자리

    # 🌟 [NEW] 애니메이션 연출 로직
    if not st.session_state.get('log_animated', False):
        # 1. QTE 결과 먼저 출력 (반응 속도 확인!)
        qte_area.info(log['crit_log'])
        time.sleep(1.0)  # 1초 대기

        # 2. 멤버별 공격 로그를 0.8초 간격으로 한 명씩 출력
        accumulated_logs = []
        for line in log['detailed_logs']:
            accumulated_logs.append(line)
            # 로그를 예쁜 박스 안에 누적해서 그림
            battle_log_area.markdown(
                f"<div style='border:1px solid rgba(255,255,255,0.2); padding:15px; border-radius:10px; background:rgba(0,0,0,0.1);'>{''.join(accumulated_logs)}</div>",
                unsafe_allow_html=True)
            time.sleep(0.8)  # 다음 멤버 공격까지 긴장감 형성!

        # 3. 계산 중... (드럼롤 효과 🥁)
        dmg_area.metric("🔥 총 데미지", "집계 중... ⏳")
        time.sleep(1.5)  # 1.5초간 뜸 들이기

        # 4. 최종 데미지 & 등급 쾅!
        dmg_area.metric("🔥 총 데미지", f"{log['damage']:,}", f"달성률: {log['ratio']:.1f}%")
        grade_area.markdown(log['result_msg'], unsafe_allow_html=True)
        time.sleep(0.5)

        # 애니메이션이 끝났음을 저장하고 새로고침하여 버튼을 표시
        st.session_state['log_animated'] = True
        st.rerun()

    else:
        # 이미 애니메이션을 다 본 상태 (새로고침 시 대기시간 생략)
        grade_area.markdown(log['result_msg'], unsafe_allow_html=True)
        qte_area.info(log['crit_log'])
        battle_log_area.markdown(
            f"<div style='border:1px solid rgba(255,255,255,0.2); padding:15px; border-radius:10px; background:rgba(0,0,0,0.1);'>{''.join(log['detailed_logs'])}</div>",
            unsafe_allow_html=True)
        dmg_area.metric("🔥 총 데미지", f"{log['damage']:,}", f"달성률: {log['ratio']:.1f}%")

        # 결과 연출이 모두 끝난 후에만 '다음 날로' 버튼이 나타남
        if btn_area.button("🌙 정산 및 다음 날로", type="primary"):
            end_day()

# ==========================================
# [DEV TOOL] 기획자용 밸런스 시뮬레이터
# ==========================================
with st.sidebar.expander("🛠️ 기획자용 밸런스 계산기", expanded=True):
    st.write("캐릭터 조합과 시너지를 바탕으로 데미지 범위를 계산합니다.")

    # 1. 시뮬레이션 설정
    sim_star = st.slider("평균 성급(Star)", 1, 3, 1)

    # 캐릭터 목록이 4명 이상일 때만 기본값 4명 설정
    all_chars = list(stellive_db.keys())
    default_chars = all_chars[:4] if len(all_chars) >= 4 else all_chars

    sim_members = st.multiselect("테스트 멤버 (4명)", all_chars, default=default_chars)

    if len(sim_members) < 4:
        st.warning("정확한 테스트를 위해 4명을 선택해주세요.")
    else:
        # 2. 계산 로직 (새로운 시너지 시스템 반영)
        active_syns = get_active_synergies(sim_members)

        adj_atk = 0
        for name in sim_members:
            char = stellive_db[name]
            base = char['atk']

            # 성급 보너스 적용
            star_mult = 1.0 + (sim_star - 1) * BALANCE_CONFIG['STAR_BONUS_PER_LEVEL']
            base = int(base * star_mult)

            # 시너지 보너스 적용
            char_syn_mult = 1.0
            for syn_key, mult in active_syns.items():
                if char['group'] == syn_key or syn_key in char['traits']:
                    char_syn_mult *= mult

            if char_syn_mult > 1.0:
                base = int(base * char_syn_mult)

            adj_atk += base

        # 시나리오별 배율 정의 (날씨, 이벤트, QTE, 전투대사)
        # Min: 모두 디버프 + 최하 배율 콤보
        min_dmg = int(adj_atk * BALANCE_CONFIG['WEATHER_DEBUFF'] * BALANCE_CONFIG['EVENT_DEBUFF'] * 0.3 * 1.0)
        # Avg: 버프/디버프 없음 + 평균 콤보
        avg_dmg = int(adj_atk * 1.0 * 1.0 * 1.2 * 1.2)
        # Max: 모두 버프 + 최고 배율 콤보 (크리티컬 + 퍼펙트 QTE)
        max_dmg = int(adj_atk * BALANCE_CONFIG['WEATHER_BUFF'] * BALANCE_CONFIG['EVENT_BUFF'] * 2.2 * 2.0)

        # 3. 시각화
        st.markdown("### 💥 예상 데미지 범위")
        st.metric("최소 데미지 (운 나쁨)", f"{min_dmg:,}")
        st.metric("평균 데미지 (보통)", f"{avg_dmg:,}")
        st.metric("최대 데미지 (운 대박)", f"{max_dmg:,}")

        # 그래프 데이터 생성
        chart_data = {
            "Scenario": ["Min", "Avg", "Max"],
            "Damage": [min_dmg, avg_dmg, max_dmg]
        }
        st.bar_chart(chart_data, x="Scenario", y="Damage", color="#FF4B4B")

        # 4. 현재 몬스터 체력과 비교
        st.markdown("### 👾 몬스터 목표치 비교")
        for m in monster_db:
            diff = m['target_score'] - avg_dmg
            diff_text = "쉬움 (클리어 가능)" if diff < 0 else "어려움 (스펙 부족)"
            diff_color = "blue" if diff < 0 else "red"
            st.caption(f"**{m['name']}** (목표: {m['target_score']:,}) : :{diff_color}[{diff_text}]")