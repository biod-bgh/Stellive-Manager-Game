import streamlit as st
import random
import time
import pandas as pd
import os
from collections import Counter



# ==========================================
# 아이콘/이모지 매핑 설정
# ==========================================
GAME_ICONS = {
    # [캐릭터 특성]
    '신화': '💎', '전설': '🌟', '용': '🐲', '무희': '💃',
    '동물': '🦄', '탱커': '🛡️', '현대': '🏙️', '인간': '👤',
    '가희': '🎤', '우주': '🌌', '뱀파이어': '🧛', '이세계': '🪐',
    '보스': '👑',

    # [몬스터 아이콘]
    '바이러스': '👾',
    '오니' : '👺',
    '허수아비': '🎯',  # 허수아비
    '악플': '😈',  # 악플러
    'AI': '🤖️',  # 저작권 경찰
    '아침': '📅',  # 월요일
    '트로피': '🏆',  # 보스
    'TV': '📺',  # 방송 사고

    # [기타/기본]
    '기본': '🔹',
    '몬스터기본': '👾'
}

# 만약 매핑에 없는 단어가 나오면 기본으로 보여줄 아이콘
DEFAULT_ICON = '🔹'

# ==========================================
# QTE 발동시킬 특성조합 ( 아이콘, 특성이름 함께 써야 가능.)
# ==========================================
QTE_TRIGGER_TRAITS = ['🐲 용', '🌟 전설', '👑 보스', '🪐 이세계']


# ==========================================
# 데이터 매니저 (엑셀 .xlsx 버전 - 통합)
# ==========================================
@st.cache_data(show_spinner=False)
def load_game_data():
    """엑셀 파일 하나에서 캐릭터, 몬스터, 이벤트, 전투대사를 모두 읽어옴"""

    excel_path = "data/game_data.xlsx"

    if not os.path.exists(excel_path):
        st.error(f"🚨 데이터 파일이 없습니다: {excel_path}")
        st.stop()

    try:
        # 모든 시트 로딩
        xls = pd.read_excel(excel_path, sheet_name=None, engine='openpyxl')

        # ----------------------------------
        # A. 캐릭터 ('character_stat')
        # ----------------------------------
        df_char = xls['character_stat']
        char_db = {}
        for _, row in df_char.iterrows():
            traits_str = str(row['trait'])
            raw_traits = [t.strip() for t in traits_str.split(',')]
            fancy_traits = [f"{GAME_ICONS.get(t, GAME_ICONS['기본'])} {t}" for t in raw_traits]

            char_db[row['name']] = {
                'group': row['group'],
                'trait': fancy_traits,
                'atk': int(row['atk']),
                'desc': row['desc'],
                'color': row['color'],
                'type': row['type']
            }

        # ----------------------------------
        # B. 몬스터 ('monster_stat')
        # ----------------------------------
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

        # ----------------------------------
        # C. 일일 이벤트 ('event')
        # ----------------------------------
        df_evt = xls['event']
        evt_db = []
        for _, row in df_evt.iterrows():
            evt_db.append({
                'name': row['name'],
                'desc': row['desc'],
                'effect': row['effect']
            })

        # ----------------------------------
        # D. 전투 이벤트 ('battle_event')
        # ----------------------------------
        df_battle = xls['battle_event']
        battle_db = []
        for _, row in df_battle.iterrows():
            battle_db.append({
                'event': row['event'],
                'effect': row['effect'],
                'mult': float(row['mult'])  # 소수점이므로 float 변환
            })

        return char_db, mon_db, evt_db, battle_db

    except KeyError as e:
        st.error(f"🚨 엑셀 시트 이름을 확인하세요! (character_stat, monster_stat, event, battle_event)\n누락된 시트: {e}")
        st.stop()
    except Exception as e:
        st.error(f"🚨 엑셀 로딩 중 오류 발생: {e}")
        st.stop()


# ==========================================
# [핵심] 전역 변수에 4개 데이터 할당
# ==========================================
stellive_db, monster_db, event_db, battle_events = load_game_data()

weather_db = {
    '맑음': {'icon': '☀️', 'desc': '야외 활동하기 좋습니다.', 'buff': 'outdoor', 'debuff': 'indoor'},
    '비': {'icon': '☔', 'desc': '집에서 게임하기 좋습니다.', 'buff': 'indoor', 'debuff': 'outdoor'},
    '태풍': {'icon': '🌪️', 'desc': '날씨가 험합니다.', 'buff': None, 'debuff': 'all'},
    '오로라': {'icon': '🌌', 'desc': '모두의 컨디션 상승.', 'buff': 'all', 'debuff': None},
}

# ==========================================
#  게임 밸런스 설정
# ==========================================
BALANCE_CONFIG = {
    # 1. 성급(Star) 보너스
    # 예: 1성(1.0) -> 2성(1.5) -> 3성(2.0)
    'STAR_BONUS_PER_LEVEL': 0.5,

    # 2. 날씨(Weather) 배율
    'WEATHER_BUFF': 1.2,  # 상성 맞음 (20% 증가)
    'WEATHER_DEBUFF': 0.8,  # 상성 안맞음 (20% 감소)

    # 3. 이벤트(Event) 배율
    'EVENT_BUFF': 1.3,  # 팬미팅 등 (30% 증가)
    'EVENT_DEBUFF': 0.8,  # 장비 고장 등 (20% 감소)

    # 4. QTE 미니게임 판정 기준 (초 단위) 및 배율
    'QTE': {
        'PERFECT_TIME': 0.35,  # 이 시간 안에 누르면 퍼펙트
        'GREAT_TIME': 0.80,  # 이 시간 안에 누르면 그레이트

        'PERFECT_MULT': 2.0,  # 퍼펙트 시 데미지 배율 (2배)
        'GREAT_MULT': 1.2,  # 그레이트 시 데미지 배율 (1.2배)
        'NORMAL_MULT': 1.0  # 일반/실패 시 데미지 배율
    }
}

# ==========================================
# 2. 게임 로직 (Logic Layer)
# ==========================================

st.set_page_config(page_title="스텔라이브 스코어 어택", page_icon="🏆", layout="wide")


def draw_new_characters(count=4):
    """(2일차 이후) 캐릭터를 랜덤하게 뽑아서 인벤토리에 추가 (중복 가능)"""
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

    # [변경] 초기 페이즈를 'starter_selection'으로 설정
    st.session_state['game_phase'] = 'starter_selection'
    st.session_state['battle_log'] = {}

    st.session_state['char_status'] = {
        name: {'condition': 0, 'count': 0, 'star': 1}
        for name in stellive_db
    }

    st.session_state['my_team'] = []
    st.session_state['qte_state'] = 'READY'
    st.session_state['qte_start_time'] = 0

    # 스타팅 멤버 후보 3명 미리 추첨
    st.session_state['starter_candidates'] = random.sample(list(stellive_db.keys()), 3)

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

        if len(team) < 4:
            team.append(name)
        else:
            st.toast("🚫 파티는 최대 4명까지만 가능합니다!", icon="⚠️")


def merge_member(name):
    """3개를 소모하여 성급(Star)을 올림"""
    status = st.session_state['char_status'][name]
    if status['count'] >= 3:
        status['count'] -= 2
        status['star'] += 1
        st.toast(f"🎉 {name} {status['star']}성으로 승급 완료! (공격력 대폭 상승)", icon="🆙")
        st.rerun()


def calculate_base_stats(team_list):
    total_atk = 0
    logs = []
    event = st.session_state['today_event']

    for name in team_list:
        char = stellive_db[name]
        stat = st.session_state['char_status'][name]
        atk = char['atk']

        # [설정값 적용] 성급 보너스
        bonus_per_star = BALANCE_CONFIG['STAR_BONUS_PER_LEVEL']
        star_multiplier = 1.0 + (stat['star'] - 1) * bonus_per_star
        atk = int(atk * star_multiplier)

        if stat['star'] > 1:
            logs.append(f"⭐ **{name}**: {stat['star']}성 위력 (x{star_multiplier})")

        # [설정값 적용] 날씨 보정
        if stat['condition'] > 0:
            buff = BALANCE_CONFIG['WEATHER_BUFF']
            atk = int(atk * buff)
            logs.append(f"🙂 **{name}**: 날씨 버프 (x{buff})")
        elif stat['condition'] < 0:
            debuff = BALANCE_CONFIG['WEATHER_DEBUFF']
            atk = int(atk * debuff)
            logs.append(f"🌧️ **{name}**: 날씨 디버프 (x{debuff})")

        total_atk += atk

    # [설정값 적용] 이벤트 보정
    if event['effect'] == 'atk_up':
        buff = BALANCE_CONFIG['EVENT_BUFF']
        total_atk = int(total_atk * buff)
        logs.append(f"🔥 이벤트 버프 (x{buff})")
    elif event['effect'] == 'atk_down':
        debuff = BALANCE_CONFIG['EVENT_DEBUFF']
        total_atk = int(total_atk * debuff)
        logs.append(f"📉 이벤트 디버프 (x{debuff})")

    return int(total_atk), logs


def get_character_card_html(name, info, status, is_selected):
    count = status['count']
    star = status['star']
    is_not_owned = count <= 0

    if is_not_owned:
        bg_color, text_color = "#F5F5F5", "#AAAAAA"
        border_style = "1px dashed #CCCCCC"
        trait_bg = "#EEEEEE"
    elif is_selected:
        bg_color, text_color = "#3C3CAC", "white"
        trait_bg = "rgba(255, 255, 255, 0.2)"
        border_style = "2px solid #3B82F6"
    else:
        bg_color, text_color = "#FFFFFF", "black"
        trait_bg = "#f0f2f6"
        border_style = "1px solid #e0e0e0"

    traits_html = ""
    for t in info['trait']:
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


def process_battle_start(team_list):
    atk, logs = calculate_base_stats(team_list)

    current_monster = monster_db[(st.session_state['day'] - 1) % len(monster_db)]
    target_score = current_monster['target_score']

    st.session_state['battle_temp'] = {
        'base_atk': atk,
        'logs': logs,
        'monster': current_monster,
        'target_score': target_score
    }

    all_traits = []
    for name in team_list:
        all_traits.extend(stellive_db[name]['trait'])

    trait_counts = Counter(all_traits)

    synergy_trait = None
    for trait, count in trait_counts.items():
        if count >= 2 and trait in QTE_TRIGGER_TRAITS:
            synergy_trait = trait
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

    total_damage = 0
    detailed_logs = []

    for name in team_list:
        char_info = stellive_db[name]
        status = st.session_state['char_status'][name]

        # [설정값 적용] 성급 보너스 (위와 동일 로직)
        bonus_per_star = BALANCE_CONFIG['STAR_BONUS_PER_LEVEL']
        star_multiplier = 1.0 + (status['star'] - 1) * bonus_per_star
        base_atk = int(char_info['atk'] * star_multiplier)

        # [설정값 적용] 날씨 보정
        if status['condition'] > 0:
            base_atk = int(base_atk * BALANCE_CONFIG['WEATHER_BUFF'])
        elif status['condition'] < 0:
            base_atk = int(base_atk * BALANCE_CONFIG['WEATHER_DEBUFF'])

        action = random.choice(battle_events)
        mult = action['mult']

        # 최종 데미지 = 기본공격력 * 랜덤이벤트배율 * QTE배율
        final_char_atk = int(base_atk * mult * multiplier)

        total_damage += final_char_atk

        # (로그 출력 부분은 기존 유지)
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
        log_msg = f"""
        <div style="{style} margin-bottom: 5px;">
            {prefix} <b>{name}{star_str}</b>: {action['effect']} (DMG: {final_char_atk})
        </div>
        """
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

    crit_log = ""
    qte_cfg = BALANCE_CONFIG['QTE']

    # QTE 배율에 따라 메시지 출력
    if multiplier >= qte_cfg['PERFECT_MULT']:
        crit_log = f"⚡ **PERFECT QTE!** (반응: {reaction_time:.3f}초) 데미지 {multiplier}배!"
    elif multiplier >= qte_cfg['GREAT_MULT']:
        crit_log = f"✨ **GREAT QTE!** (반응: {reaction_time:.3f}초) 데미지 {multiplier}배!"
    else:
        crit_log = f"💨 **NORMAL QTE** (반응: {reaction_time:.3f}초) 기본 데미지로 공격."

    st.session_state['battle_log'] = {
        'damage': total_damage,
        'logs': temp['logs'],
        'detailed_logs': detailed_logs,
        'crit_log': crit_log,
        'result_msg': result_msg,
        'grade': grade,
        'ratio': ratio,
        'team': team_list,
        'monster': temp['monster']
    }

    st.session_state['log_animated'] = False
    st.session_state['game_phase'] = 'result'
    st.rerun()


def end_day():
    st.session_state['day'] += 1

    if st.session_state['day'] > 7:
        st.session_state['game_over'] = True
    else:
        generate_daily_environment()
        draw_new_characters(4)

    st.session_state['game_phase'] = 'planning'
    st.rerun()


# ==========================================
# 3. UI 렌더링 (View Layer)
# ==========================================

if 'day' not in st.session_state: init_game()

# --- 엔딩 화면 ---
if st.session_state['game_over']:
    st.balloons()
    st.title("🏆 시즌 종료: 최종 성적표")
    st.metric("최종 누적 점수", st.session_state['total_score'])
    st.write("7일간의 활동이 모두 끝났습니다! 수고하셨습니다.")

    if st.button("🔄 새로운 시즌 시작하기"):
        init_game()
        st.rerun()
    st.stop()

# --- [Phase 0: 스타팅 멤버 선택] (NEW) ---
if st.session_state['game_phase'] == 'starter_selection':
    st.markdown("## 🌟 파트너 선택")
    st.write("이번 시즌을 함께할 메인 멤버를 선택해주세요.")
    st.caption("선택한 멤버 외에 **3명의 추가 멤버(중복 없음)**가 지급되어 바로 4인 파티를 꾸릴 수 있습니다.")

    candidates = st.session_state['starter_candidates']
    cols = st.columns(3)

    for i, name in enumerate(candidates):
        info = stellive_db[name]
        with cols[i]:
            # 카드 보여주기
            card_html = get_character_card_html(name, info, {'count': 1, 'fatigue': 100, 'star': 1}, False)
            st.markdown(card_html, unsafe_allow_html=True)

            if st.button(f"👉 {name} 선택", key=f"start_{name}", use_container_width=True):
                # 1. 스타팅 멤버 지급
                st.session_state['char_status'][name]['count'] += 1

                # 2. 나머지 3명 지급 (무조건 중복되지 않게)
                all_names = list(stellive_db.keys())
                # 스타팅 멤버 제외한 리스트
                remaining_pool = [n for n in all_names if n != name]
                # 3명 랜덤 추출
                others = random.sample(remaining_pool, 4)

                for other in others:
                    st.session_state['char_status'][other]['count'] += 1

                msg = f"🎉 {name} + {', '.join(others)} 영입 완료!"
                st.toast(msg, icon="🎁")

                # 게임 시작
                st.session_state['game_phase'] = 'planning'
                st.rerun()

    st.stop()  # 스타팅 선택 중에는 아래 UI 렌더링 안 함

# --- 메인 게임 화면 ---
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

# --- [Phase 1: 계획 단계] ---
if st.session_state['game_phase'] == 'planning':

    today_monster = monster_db[(st.session_state['day'] - 1) % len(monster_db)]
    target_score = today_monster['target_score']

    with st.expander(f"🎯 금일의 목표: {today_monster['name']}", expanded=True):
        mc1, mc2 = st.columns([1, 4])
        with mc1: st.markdown(f"<div style='font-size:50px; text-align:center;'>{today_monster['icon']}</div>",
                              unsafe_allow_html=True)
        with mc2:
            st.write(f"**목표 점수:** {target_score:,} | **특징:** {today_monster['desc']}")
            st.caption("최고의 조합으로 목표 점수를 돌파하여 S등급을 노리세요!")

    st.write("")

    # 파티 편성
    st.subheader("🚩 멤버 배치 (4명)")
    my_team = st.session_state['my_team']
    cols_team = st.columns(4)

    for i in range(4):
        with cols_team[i]:
            if i < len(my_team):
                char_name = my_team[i]
                char_info = stellive_db[char_name]
                status = st.session_state['char_status'][char_name]

                card_html = get_character_card_html(char_name, char_info, status, True)
                st.markdown(card_html, unsafe_allow_html=True)

                if st.button("제외", key=f"remove_{i}", use_container_width=True):
                    toggle_member(char_name)
                    st.rerun()
            else:
                st.markdown(
                    "<div style='border: 2px dashed #ccc; border-radius:10px; height: 150px; display:flex; align-items:center; justify-content:center; color:#ccc;'>EMPTY</div>",
                    unsafe_allow_html=True)

    if len(my_team) > 0:
        st.write("")
        current_traits = []
        for name in my_team:
            current_traits.extend(stellive_db[name]['trait'])
        trait_counts = Counter(current_traits)
        active_synergies = [(t, c) for t, c in trait_counts.items() if c >= 2]

        with st.container(border=True):
            st.markdown("##### 🔗 현재 발동 시너지")
            if not active_synergies:
                st.caption("시너지가 없습니다. 특성을 맞춰보세요!")
            else:
                syn_cols = st.columns(len(active_synergies))
                for idx, (trait, count) in enumerate(active_synergies):
                    badge_bg = "linear-gradient(45deg, #FF416C, #FF4B2B)" if trait in QTE_TRIGGER_TRAITS else "#555"
                    effect_text = "QTE 발동!" if trait in QTE_TRIGGER_TRAITS else "스탯 UP"
                    with syn_cols[idx]:
                        st.markdown(f"""
                            <div style="background: {badge_bg}; padding: 8px; border-radius: 8px; color: white; text-align: center;">
                                <div style="font-size: 14px; font-weight: bold;">{trait} Lv.{count}</div>
                                <div style="font-size: 11px;">{effect_text}</div>
                            </div>
                            """, unsafe_allow_html=True)

    btn_disabled = len(my_team) != 4

    if st.button("🔥 공연 시작 (START)", type="primary", use_container_width=True, disabled=btn_disabled):
        process_battle_start(my_team)

    st.divider()

    # 대기실
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

                    if status['count'] >= 3:
                        if st.button(f"⬆️ MERGE (3개 소모)", key=f"merge_{title}_{name}", type="primary",
                                     use_container_width=True):
                            merge_member(name)
                idx += 1

# --- [Phase 1.5: 미니게임 / 계산] ---
elif st.session_state['game_phase'] == 'attack_minigame':
    synergy = st.session_state.get('synergy_name', '알 수 없음')
    st.markdown(f"## ⚔️ '{synergy}' 시너지 발동!")
    st.write("타이밍에 맞춰 클릭하여 최고 점수를 노리세요!")

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
                    multiplier = 2.0 if reaction < 0.35 else (1.2 if reaction < 0.8 else 1.0)
                    qte = BALANCE_CONFIG['QTE']

                    if reaction < qte['PERFECT_TIME']:
                        multiplier = qte['PERFECT_MULT']
                    elif reaction < qte['GREAT_TIME']:
                        multiplier = qte['GREAT_MULT']

                    finalize_battle(multiplier, reaction)

elif st.session_state['game_phase'] == 'calculating':
    st.markdown("## ⚔️ 일반 공격")
    st.write("특별한 시너지가 없습니다. 기본 공격을 수행합니다.")
    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])
    with col_center:
        if st.button("⚔️ 공격 시작", type="primary", use_container_width=True):
            finalize_battle(1.0, 0.0)

# --- [Phase 2: 결과 단계] ---
elif st.session_state['game_phase'] == 'result':
    st.subheader("📊 공격 결과")
    log = st.session_state['battle_log']
    monster = log['monster']

    with st.container(border=True):
        st.markdown(log['result_msg'], unsafe_allow_html=True)  # 등급 표시
        st.info(log['crit_log'])

        if not st.session_state.get('log_animated', False):
            placeholder = st.empty()
            accumulated_logs = []
            for line in log['detailed_logs']:
                accumulated_logs.append(line)
                placeholder.markdown("".join(accumulated_logs), unsafe_allow_html=True)
                time.sleep(0.05)
            st.session_state['log_animated'] = True
        else:
            for line in log['detailed_logs']:
                st.markdown(line, unsafe_allow_html=True)

    st.divider()

    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.metric("🔥 총 데미지", f"{log['damage']:,}")
        st.caption(f"목표 점수 달성률: {log['ratio']:.1f}%")
        with st.expander("버프 로그"):
            for l in log['logs']: st.write(l)
    with c_res2:
        st.metric("🎯 목표 점수", f"{monster['target_score']:,}")
        st.write(f"**상대:** {monster['name']}")

    st.write("---")

    if st.button("🌙 정산 및 다음 날로", type="primary"):
        end_day()

# # ==========================================
# # [DEV TOOL] 밸런스 시뮬레이터 (개발용)
# # ==========================================
# with st.sidebar.expander("🛠️ 기획자용 밸런스 계산기", expanded=True):
#     st.write("캐릭터 조합별 데미지 범위를 계산합니다.")
#
#     # 1. 시뮬레이션 설정
#     sim_star = st.slider("평균 성급(Star)", 1, 3, 1)
#     sim_members = st.multiselect("테스트 멤버 (4명)", list(stellive_db.keys()), default=list(stellive_db.keys())[:4])
#
#     if len(sim_members) < 4:
#         st.warning("4명을 선택해주세요.")
#     else:
#         # 2. 계산 로직
#         total_base_atk = sum([stellive_db[m]['atk'] for m in sim_members])
#         star_mult = 1.0 + (sim_star - 1) * 0.5
#         adj_atk = int(total_base_atk * star_mult)  # 성급 반영 기본공격력
#
#         # 시나리오별 배율 정의
#         # Min: 날씨(0.8) * 이벤트(0.8) * 배틀이벤트(0.3) * QTE(1.0) = 0.192
#         # Avg: 날씨(1.0) * 이벤트(1.0) * 배틀이벤트(1.2) * QTE(1.2) = 1.44
#         # Max: 날씨(1.2) * 이벤트(1.3) * 배틀이벤트(2.2) * QTE(2.0) = 6.86
#
#         min_dmg = int(adj_atk * 0.8 * 0.8 * 0.3 * 1.0)
#         avg_dmg = int(adj_atk * 1.0 * 1.0 * 1.2 * 1.2)  # 평균적인 이벤트 배율 1.2 가정
#         max_dmg = int(adj_atk * 1.2 * 1.3 * 2.2 * 2.0)
#
#         # 3. 시각화
#         st.markdown("### 💥 예상 데미지 범위")
#         st.metric("최소 데미지 (운 나쁨)", f"{min_dmg:,}")
#         st.metric("평균 데미지 (보통)", f"{avg_dmg:,}")
#         st.metric("최대 데미지 (운 대박)", f"{max_dmg:,}")
#
#         # 그래프 데이터 생성
#         chart_data = {
#             "Scenario": ["Min", "Avg", "Max"],
#             "Damage": [min_dmg, avg_dmg, max_dmg]
#         }
#         st.bar_chart(chart_data, x="Scenario", y="Damage", color="#FF4B4B")
#
#         # 4. 현재 몬스터 체력과 비교
#         st.markdown("### 👾 현재 몬스터 설정 비교")
#         for m in monster_db:
#             diff = m['target_score'] - avg_dmg
#             diff_text = "쉬움" if diff < 0 else "어려움"
#             diff_color = "blue" if diff < 0 else "red"
#             st.caption(f"**{m['name']}** (목표: {m['target_score']:,}) : :{diff_color}[{diff_text}]")