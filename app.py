import streamlit as st
import random
import time
from collections import Counter

# ==========================================
# 1. 데이터베이스 (DB Layer)
# ==========================================
QTE_TRIGGER_TRAITS = ['🐲 용', '🎧 전설', '👑 보스', '🪐 이세계']
stellive_db = {
    # 1기생
    # '아이리 칸나': {
    #     'group': '1기생',
    #     'trait': ['💎 신화', '🐲 용', '💃 무희'],
    #     'atk': 95, 'hp': 40,
    #     'desc': '노래로 적을 제압',
    #     'color': '#3B82F6', 'type': 'outdoor'
    # },
    '아야츠노 유니': {
        'group': '1기생',
        'trait': ['✨ 전설', '🦄 동물', '💃 무희'],
        'atk': 50, 'hp': 85,
        'desc': '어그로 담당',
        'color': '#F472B6', 'type': 'outdoor'
    },
    '사키하네 후야': {
        'group': '1기생',
        'trait': ['✨ 전설', '용', '🛡️ 탱커'],
        'atk': 50, 'hp': 85,
        'desc': '다시태어난마룡',
        'color': '#F472B6', 'type': 'indoor'
    },

    # 2기생
    '시라유키 히나': {
        'group': '2기생',
        'trait': ['🏙️ 현대','👤 인간', '🎤 가희'],
        'icon': '🎧', 'atk': 85, 'hp': 50,
        'desc': 'SIUUUUU',
        'color': '#A855F7', 'type': 'outdoor'
    },

    '네네코 마시로': {
        'group': '2기생',
        'trait': ['🌌 우주', '🦄 동물', '🎤 가희'],
        'atk': 30, 'hp': 90,
        'desc': '밍',
        'color': '#FCD34D', 'type': 'indoor'
    },
    '아카네 리제': {
        'group': '2기생',
        'trait': ['✨ 전설', '🧛 뱀파이어', '💃 무희'],
        'atk': 88, 'hp': 70,
        'desc': '강력한 파괴력',
        'color': '#EF4444', 'type': 'indoor'
    },
    '아라하시 타비': {
        'group': '2기생',
        'trait': ['🪐 이세계', '👤 인간', '🛡️ 탱커'],
        'atk': 60, 'hp': 80,
        'desc': '기적의 용사',
        'color': '#06B6D4', 'type': 'outdoor'
    },

    # 3기생
    '텐코 시부키': {
        'group': '3기생',
        'trait': ['✨ 전설', '동물', '무희'],
        'atk': 60, 'hp': 80,
        'desc': '기적의 용사',
        'color': '#06B6D4', 'type': 'outdoor'
    },

    '하나코 나나': {
        'group': '3기생',
        'trait': ['🏙️ 현대', '👤 인간', '🎤 가희'],
        'atk': 60, 'hp': 80,
        'desc': '기적의 용사',
        'color': '#06B6D4', 'type': 'outdoor'
    },

    '유즈하 리코': {
        'group': '3기생',
        'trait': ['🪐 이세계', '👤 인간', '🎤 가희'],
        'atk': 60, 'hp': 80,
        'desc': '기적의 용사',
        'color': '#06B6D4', 'type': 'outdoor'
    },

    '아오쿠모 린': {
        'group': '3기생',
        'trait': ['🏙️ 현대', '👤 인간', '🛡️ 탱커'],
        'atk': 60, 'hp': 80,
        'desc': '기적의 용사',
        'color': '#06B6D4', 'type': 'outdoor'
    },


    # 사장/기타
    '강지': {
        'group': '사장',
        'trait': ['👑 보스', '🎤 가희'],
        'atk': 99, 'hp': 99,
        'desc': '별의 주인',
        'color': '#111827',
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
    '오로라': {'icon': '🌌', 'desc': '모두의 컨디션 상승.', 'buff': 'all', 'debuff': None},
}

event_db = [
    {'name': '평범한 하루', 'desc': '평화롭습니다.', 'effect': 'none'},
    {'name': '간식 배달', 'desc': '사장님의 간식! (피로도 소모 감소)', 'effect': 'stamina_save'},
    {'name': '장비 고장', 'desc': '장비 이슈 발생. (전투력 감소)', 'effect': 'atk_down'},
    {'name': '팬미팅', 'desc': '응원 버프! (전투력 대폭 상승)', 'effect': 'atk_up'},
]

# {event: 겪은 일, effect: 결과 멘트, mult: 데미지 배율}
battle_events = [
    {"event": "화려한 고음을 질러", "effect": "음파 데미지가 폭발했습니다!", "mult": 1.5},
    {"event": "실수로 마이크를 떨어뜨렸지만", "effect": "오히려 적이 당황했습니다.", "mult": 2.0},
    {"event": "팬들의 응원을 받고", "effect": "초인적인 힘을 발휘했습니다!", "mult": 2.0},
    {"event": "평소 연습한 콤보를", "effect": "완벽하게 성공시켰습니다.", "mult": 2.2},
    {"event": "귀여운 표정을 지어", "effect": "적을 방심하게 만들었습니다.", "mult": 1.1},
    {"event": "넘어질 뻔했지만 자연스럽게", "effect": "회전 회오리 킥을 날렸습니다!", "mult": 1.4},
    {"event": "갑자기 방송 텐션이 올라", "effect": "미친듯한 딜을 넣었습니다.", "mult": 1.2},
    {"event": "방송이 갑자기 꺼지며", "effect": "울기 시작했습니다....", "mult": 0.5},
    {"event": "방종 후에 마이크가 켜지고", "effect": "자기야~ 나 방종했어...어?!", "mult": 0.3},
    {"event": "팬들의 응원에 힘입어", "effect": "아무 일도 없었습니다.", "mult": 1.0},
    {"event": "화려한 음악이 나를 감싸고", "effect": "딱히 별 일은 아니었네요.", "mult": 1.0},
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

# UI 렌더링용 도우미 함수 (카드 HTML 생성)
def get_character_card_html(name, info, status, is_selected):
    # 피로도 확인
    fatigue = status['fatigue']
    is_exhausted = fatigue <= 0

    # 1. 배경/글자 색상 설정
    if is_selected:
        if is_exhausted:
            # 선택되어 있는데 피로도 0 진한 빨강
            bg_color = "#B91C1C"  # Dark Red
            text_color = "white"
            border_style = "2px solid #EF4444"
            trait_bg = "rgba(255, 255, 255, 0.2)"
        else:
            # 팀편성되고, 선택 가능한 상태
            bg_color = "#3C3CAC"
            text_color = "white"
            trait_bg = "rgba(255, 255, 255, 0.2)"
            border_style = "2px solid #3B82F6"
    else:
        if is_exhausted:
            #선택 안 됨 + 탈진 (선택 불가) -> 연한 빨강
            bg_color = "#FEF2F2"  # Very Light Red
            text_color = "#991B1B"  # Dark Red Text
            border_style = "2px dashed #EF4444"  # 빨간 점선 테두리
            trait_bg = "#FECACA"  # 붉은색 특성 배경
        else:
            # 팀편성되지 않고, 선택 가능 상태
            bg_color = "#FFFFFF"
            text_color = "black"
            trait_bg = "#f0f2f6"
            border_style = "1px solid #e0e0e0"

    # 2. 피로도 색상 설정
    if fatigue >= 80: f_col = "#4CAF50" # Green
    elif fatigue >= 40: f_col = "#FFC107" # Orange
    elif fatigue > 0: f_col = "#FF5252"
    else: f_col = "#991B1B" # Red

    # 3. 특성 배지 HTML 생성
    traits_html = ""
    for t in info['trait']:
        traits_html += f"<span style='display:inline-block; background:{trait_bg}; padding:2px 6px; margin:2px; border-radius:4px; font-size:11px;'>{t}</span>"

    # 4. 최종 HTML 반환
    opacity = "0.6" if (is_exhausted and not is_selected) else "1.0"

    return f"""
    <div style="border:{border_style}; background-color:{bg_color}; color:{text_color}; padding:12px 5px; border-radius:12px; margin-bottom:10px; text-align:center; height:100%; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <div style="font-weight:bold; font-size:18px; margin-bottom:8px;">{name}</div>
        <div style="margin-bottom:10px; line-height:1.4;">{traits_html}</div>
        <div style="font-size:12px; opacity:0.8; margin-bottom: 5px;">{info['desc']}</div>
        <div style="font-weight:bold; color:{f_col}; font-size:13px;">피로도 {fatigue}</div>
    </div>
    """

def toggle_member(name):
    team = st.session_state['my_team']
    status = st.session_state['char_status'][name]  # 캐릭터 상태 가져오기

    if name in team:
        # [제외는 언제나 가능]
        team.remove(name)
    else:
        # [추가 시 검사 로직]
        # 1. 피로도 체크: 0 이하면 추가 불가
        if status['fatigue'] <= 0:
            st.toast(f"🚫 {name}님은 탈진 상태(HP 0)라 선택할 수 없습니다! 휴식이 필요합니다.", icon="🏥")
            return  # 함수 강제 종료 (추가 안 됨)

        # 2. 인원수 체크
        if len(team) < 4:
            team.append(name)
        else:
            st.toast("🚫 파티는 최대 4명까지만 가능합니다!", icon="⚠️")

def process_battle_start(team_list):
    atk, hp, logs = calculate_base_stats(team_list)

    current_monster = monster_db[(st.session_state['day'] - 1) % len(monster_db)]
    monster_hp = current_monster['hp_base'] + (st.session_state['day'] * 50)
    monster_atk = current_monster.get('atk_base', 100) + (st.session_state['day'] * 20)

    st.session_state['battle_temp'] = {
        'base_atk': atk, 'hp': hp, 'logs': logs,
        'monster': current_monster, 'monster_hp': monster_hp, 'monster_atk': monster_atk
    }

    # 1. 팀원들의 모든 특성을 하나의 리스트로 모으기
    all_traits = []
    for name in team_list:
        all_traits.extend(stellive_db[name]['trait'])

    # 2. 특성별 개수 세기
    trait_counts = Counter(all_traits)

    # 3. 2개 이상 겹치는 특성이 있는지 확인
    synergy_trait = None
    for trait, count in trait_counts.items():
        if count >= 2 and trait in QTE_TRIGGER_TRAITS:
            synergy_trait = trait
            break

    if synergy_trait:
        # 시너지 있음 -> QTE(미니게임) 발동!
        st.session_state['synergy_name'] = synergy_trait  # UI에 보여주기 위해 저장
        st.toast(f"✨ '{synergy_trait}' 특성 공명 발동! 연계 공격 기회!", icon="⚔️")

        st.session_state['qte_state'] = 'READY'
        st.session_state['game_phase'] = 'attack_minigame'
        st.rerun()
    else:
        # 시너지 없음 -> 미니게임 없이 일반 공격 (배율 1.0)
        st.session_state['game_phase'] = 'calculating'
        # if any(c >= 2 for c in trait_counts.values()):
        #     st.toast("시너지가 발생했지만 전투 특성이 아닙니다. 일반 공격으로 전환합니다.", icon="💬")
        # else:
        #     st.toast("발동된 시너지가 없습니다.", icon="☁️")

        st.rerun()


def finalize_battle(multiplier, reaction_time):
    temp = st.session_state['battle_temp']

    # [MODIFIED] 개별 전투 로그 생성을 위한 로직 변경
    team_list = st.session_state['my_team']

    total_atk = 0
    detailed_logs = []  # 여기에 HTML 스타일이 적용된 로그가 저장됩니다.

    # 1. 각 멤버별로 전투 시뮬레이션 진행
    for name in team_list:
        char_info = stellive_db[name]
        status = st.session_state['char_status'][name]

        # 기본 공격력 계산
        base_atk = char_info['atk']
        if status['condition'] > 0:
            base_atk *= 1.2
        elif status['condition'] < 0:
            base_atk *= 0.8
        if status['fatigue'] < 30: base_atk *= 0.5

        # 랜덤 이벤트 뽑기
        action = random.choice(battle_events)
        mult = action['mult']  # 현재 이벤트의 배율

        # 최종 데미지 계산
        final_char_atk = int(base_atk * mult * multiplier)
        total_atk += final_char_atk

        # [NEW] 배율에 따른 동적 스타일링 로직
        if mult > 1.2:
            # 대성공 (배율이 1.2 초과): 크고 주황색, 강조됨
            style = "font-size: 1.2em; color: #ff8c00; font-weight: bold; padding: 5px;"
            prefix = "💥 SUPER:"
        elif mult < 1.0:
            # 실패/패널티 (배율이 1.0 미만): 작고 회색, 힘빠짐
            style = "font-size: 0.9em; color: #808080; font-style: italic; padding: 2px;"
            prefix = "💧 BAD:"
        else:
            # 평타 (1.0 ~ 1.2): 기본 스타일
            style = "font-size: 1.0em; color: #ffffff; padding: 3px;"
            prefix = "NORMAL:"

        # HTML 태그로 감싼 로그 메시지 생성
        log_msg = f"""
        <div style="{style} margin-bottom: 5px;">
            {prefix} <b>{name}</b> 이(가) {action['event']}, {action['effect']} (DMG: {final_char_atk})
        </div>
        """
        detailed_logs.append(log_msg)

    # 2. 몬스터 체력 및 결과 계산
    remaining_monster_hp = temp['monster_hp'] - total_atk

    # QTE 결과 메시지
    crit_log = ""
    if multiplier >= 2.0:
        crit_log = f"⚡ **PERFECT QTE!** (반응: {reaction_time:.3f}초) 전체 데미지 2배 적용!"
    elif multiplier > 1.0:
        crit_log = f"✨ **GREAT QTE!** (반응: {reaction_time:.3f}초) 전체 데미지 1.2배 적용!"
    else:
        crit_log = f"💨 **NORMAL QTE** (반응: {reaction_time:.3f}초) 기본 데미지로 공격."

    # 승패 판정
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

    # 5. 결과 저장
    st.session_state['battle_log'] = {
        'atk': total_atk, 'hp': final_hp,
        'monster_hp': remaining_monster_hp,
        'logs': temp['logs'],
        'detailed_logs': detailed_logs,  # HTML 로그 저장
        'crit_log': crit_log,
        'counter_log': counter_log,
        'win': win, 'result_msg': result_msg,
        'team': team_list, 'monster': temp['monster']
    }

    # 애니메이션 상태 초기화
    st.session_state['log_animated'] = False

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
                status = st.session_state['char_status'][char_name]  # status 가져오기

                # [개선] 함수 호출로 대체!
                card_html = get_character_card_html(char_name, char_info, status, True)  # True는 선택됨 의미

                st.markdown(card_html, unsafe_allow_html=True)

                if st.button("제외", key=f"remove_{i}", use_container_width=True):
                    toggle_member(char_name)
                    st.rerun()
            else:
                st.markdown(
                    "<div style='border: 2px dashed #ccc; border-radius:10px; height: 150px; display:flex; align-items:center; justify-content:center; color:#ccc;'>EMPTY</div>",
                    unsafe_allow_html=True)

    if len(my_team) > 0:
        st.write("")  # 여백

        # 1. 현재 팀의 모든 특성 수집
        current_traits = []
        for name in my_team:
            current_traits.extend(stellive_db[name]['trait'])

        # 2. 개수 세기
        trait_counts = Counter(current_traits)

        # 3. 발동된 시너지 필터링
        active_synergies = []
        possible_synergies = []

        for trait, count in trait_counts.items():
            if count >= 2:
                active_synergies.append((trait, count))
            else:
                possible_synergies.append(trait)

        # 4. UI 렌더링
        with st.container(border=True):
            st.markdown("##### 🔗 현재 발동 시너지")

            if not active_synergies:
                st.caption("아직 발동된 시너지가 없습니다. 같은 특성을 가진 멤버를 배치해보세요!")
            else:
                # 시너지 배지를 가로로 나열
                # [수정] columns 개수를 유동적으로 조절하여 가로 배치 최적화
                syn_cols = st.columns(len(active_synergies))

                for idx, (trait, count) in enumerate(active_synergies):
                    is_qte = trait in QTE_TRIGGER_TRAITS

                    if is_qte:
                        badge_bg = "linear-gradient(45deg, #FF416C, #FF4B2B)"
                        badge_icon = "⚔️"
                        effect_text = "QTE 발동!"
                    else:
                        badge_bg = "#555"
                        badge_icon = "🔹"
                        effect_text = "스탯 UP"

                    with syn_cols[idx]:
                        st.markdown(f"""
                            <div style="background: {badge_bg}; padding: 8px; border-radius: 8px; color: white; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                <div style="font-size: 14px; font-weight: bold;">{badge_icon} {trait} Lv.{count}</div>
                                <div style="font-size: 11px; opacity: 0.9;">{effect_text}</div>
                            </div>
                            """, unsafe_allow_html=True)

            # 힌트 (여백이 남을 때만 표시)
            if possible_synergies and len(my_team) < 4:
                st.write("")
                st.caption(f"💡 힌트: **{', '.join(possible_synergies[:3])}** 등을 더 모아보세요!")

    exhausted_members = []
    for m_name in my_team:
        if st.session_state['char_status'][m_name]['fatigue'] <= 0:
            exhausted_members.append(m_name)

    btn_disabled = len(my_team) != 4

    if st.button("🔥 전투 출격 (MISSION START)", type="primary", use_container_width=True, disabled=btn_disabled):
        if len(exhausted_members) > 0:
            # [차단] 탈진 멤버가 있으면 경고 메시지 출력하고 함수 실행 안 함
            st.error(f"🚫 출격 불가! 다음 멤버의 피로도가 0입니다: {', '.join(exhausted_members)}")
            st.toast("팀원을 교체하거나 휴식을 취해야 합니다.", icon="🏥")
        else:
            # [통과] 모두 건강하면 전투 시작
            process_battle_start(my_team)

    st.divider()

    # 대기실
    st.subheader("👥 대기실 (멤버 선택)")
    tab_titles = ["ALL", "1기생", "2기생", "3기생","사장/기타"]
    tabs = st.tabs(tab_titles)

    filter_groups = {"ALL": None,
                     "1기생": "1기생",
                     "2기생": "2기생",
                     "3기생": "3기생",
                     "사장/기타": "사장"
                     }

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
                border_style = "2px solid #3B82F6" if is_selected else "1px solid #e0e0e0"

                # [색상 로직]
                if is_selected:
                    bg_color = "#3C3CAC"
                    text_color = "white"
                    trait_bg = "rgba(255, 255, 255, 0.2)"  # 선택됐을 땐 반투명 흰색 배경
                else:
                    bg_color = "#FFFFFF"
                    text_color = "black"
                    trait_bg = "#f0f2f6"  # 평소엔 회색 배경

                btn_label = "해제" if is_selected else "선택"
                btn_type = "secondary" if is_selected else "primary"

                # 피로도 색상
                if fatigue >= 80:
                    f_col = "#4CAF50"  # Green
                elif fatigue >= 40:
                    f_col = "#FFC107"  # Orange
                else:
                    f_col = "#FF5252"  # Red

                # [핵심 변경] 특성을 HTML 태그로 감싸서 '배지' 형태로 만듦
                traits_html = ""
                for t in info['trait']:
                    # 특성 하나하나를 둥근 네모 박스에 넣음
                    traits_html += f"<span style='display:inline-block; background:{trait_bg}; padding:2px 6px; margin:2px; border-radius:4px; font-size:11px;'>{t}</span>"

                with row_cols[idx % 4]:
                    # [개선] 함수 호출로 대체!
                    card_html = get_character_card_html(name, info, status, is_selected)

                    st.markdown(card_html, unsafe_allow_html=True)

                    if st.button(btn_label, key=f"btn_{title}_{name}", type=btn_type, use_container_width=True):
                        toggle_member(name)
                        st.rerun()
                idx += 1

# --- [Phase 1.5: 공격 타이밍 미니게임] ---
elif st.session_state['game_phase'] == 'attack_minigame':

    # [MODIFIED] 어떤 시너지가 발동했는지 표시
    synergy = st.session_state.get('synergy_name', '알 수 없음')

    st.markdown(f"## ⚔️ '{synergy}' 특성 연계 공격 발동!")
    st.info(f"파티원들의 **[{synergy}]** 특성이 공명하여 강력한 스킬을 준비합니다!")
    st.write("신호가 오면 **발사**하여 데미지를 증폭시키세요!")

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

# [화면 전환용 단계]
# 대기실 -> 결과 화면 전환 방식 통일
elif st.session_state['game_phase'] == 'calculating':
    st.markdown("## ⚔️ 일반 공격 준비")
    st.info("특별한 시너지가 발견되지 않았습니다. 기본 전술로 공격을 수행합니다.")

    st.write("")  # 여백
    st.write("")

    col_spacer1, col_center, col_spacer2 = st.columns([1, 2, 1])

    with col_center:
        st.markdown("<h3 style='text-align:center;'>명령 대기 중...</h3>", unsafe_allow_html=True)

        # 유저가 직접 눌러야 넘어감
        if st.button("⚔️ 공격 개시 (ENGAGE)", type="primary", use_container_width=True):
            # 일반 공격이므로 배율 1.0, 반응속도 0.0으로 처리
            finalize_battle(1.0, 0.0)
    pass

# --- [Phase 2: 결과 단계] ---
elif st.session_state['game_phase'] == 'result':
    st.subheader("📊 작전 결과 보고")
    log = st.session_state['battle_log']
    monster = log['monster']

    # [MODIFIED] 타자기 효과 + HTML 스타일링 적용
    with st.container(border=True):
        st.markdown("### ⚔️ 전투 상세 기록")
        st.info(log['crit_log'])

        # 1. 애니메이션 출력 (타자기 효과)
        if not st.session_state.get('log_animated', False):
            placeholder = st.empty()
            accumulated_logs = []

            for line in log['detailed_logs']:
                accumulated_logs.append(line)
                # [중요] HTML 태그가 포함되어 있으므로 unsafe_allow_html=True 필수
                placeholder.markdown("".join(accumulated_logs), unsafe_allow_html=True)
                time.sleep(0.5)  # 속도 조절

            st.session_state['log_animated'] = True

        # 2. 정적 출력 (깜빡임 방지)
        else:
            for line in log['detailed_logs']:
                # 여기도 마찬가지로 HTML 허용
                st.markdown(line, unsafe_allow_html=True)

    st.divider()

    # (이 아래 승패 결과, 스탯 표시 등 나머지 코드는 기존과 동일하게 유지)
    if log['result_msg'] == 'SUCCESS':
        st.success("🎉 작전 성공! 적을 물리쳤습니다.")
        #st.balloons()
    elif log['result_msg'] == 'DRAW':
        st.warning("⚠️ 작전 무승부. 적을 처치하진 못했지만 생존했습니다.")
    else:
        st.error("💀 작전 실패. 아군이 전멸했습니다.")

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