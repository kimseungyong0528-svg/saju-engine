"""평생사주 목차(114쪽 기준)를 쪽 단위로 만든다.

목차 원본: /mnt/project-files/plan/lifetime-report-toc.md (2026-10-11 확정)
각 쪽은 제목, 그림(figure), 고정 글(static), AI가 쓸 글 칸(slot)으로 이뤄진다.
slot의 chars는 A4·14pt 한 쪽에 들어가는 글자 수를 기준으로 잡았다(글만 있는 쪽 약 760자).
"""

from __future__ import annotations

from . import knowledge as K

FULL = 760      # 글만 있는 한 쪽 (14pt 실제 문장 기준 한 쪽 약 860자. 8% 넘쳐도 들어가게)
HALF = 380      # 그림과 함께 쓰는 쪽

SECTIONS = [
    ("1", "내 사주 한눈에 보기", "사주와 오행, 나의 사주표"),
    ("2", "타고난 기질과 사주의 구성", "오행, 십신, 신살"),
    ("3", "나는 어떤 사람일까?", "성격의 장점과 단점, 겉모습과 속마음"),
    ("4", "나도 모르게 반복하는 행동", "반복되는 생각과 행동 패턴"),
    ("5", "나에게 잘 맞는 일과 이직 시기", "어울리는 직업, 커리어 변화"),
    ("6", "내 돈은 어떻게 들어오고 나갈까?", "돈 버는 방식, 재물운이 드는 시기"),
    ("7", "연애와 결혼, 나의 인연", "배우자의 특징, 결혼 시기"),
    ("8", "가족과 사람들 사이에서", "가족운과 인간관계"),
    ("9", "건강을 위해 살펴볼 점", "건강 흐름과 주의할 점"),
    ("10", "앞으로 10년씩 달라지는 운", "10년 단위 대운"),
    ("11", "해마다 살펴보는 운세", "앞으로 6년의 연도별 흐름"),
    ("12", "12개월 운세 달력", "한 달씩 보는 올해의 흐름"),
    ("13", "내가 남긴 질문에 대한 답", ""),
    ("14", "나에게 좋은 색·숫자·방향", ""),
    ("15", "문제 해결 방법과 마지막 조언", ""),
    ("부록", "부록", "용어 사전과 계산 기준"),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

# 모든 고객에게 같은 설명(사주 기초)
STATIC = {
    "how_to_read": [
        "이 책은 태어난 날과 시간으로 계산한 사주를 바탕으로, 성격부터 일, 돈, 연애, 건강, 앞으로의 운까지 순서대로 풀어 놓은 책이에요.",
        "처음부터 순서대로 읽어도 좋고, 궁금한 장부터 펼쳐 봐도 괜찮아요. 1장과 2장은 사주를 처음 보는 분을 위한 기초 설명이에요. 이 부분을 먼저 읽으면 뒤의 내용이 훨씬 쉽게 이해돼요.",
        "어려운 사주 용어가 나오면 바로 옆에 쉬운 말로 풀어 두었어요. 각 장 마지막 쪽에는 그 장에 나온 용어를 다시 정리했고, 책 맨 뒤에는 용어 사전이 있어요.",
        "사주는 정해진 운명을 알려 주는 것이 아니라, 내가 타고난 기운과 흐름을 알려 주는 지도에 가까워요. 좋은 시기에는 더 힘을 내고, 조심할 시기에는 한 번 더 살피는 데 이 책을 써 주세요.",
    ],
    "what_is_saju": [
        "사주(四柱)는 '네 개의 기둥'이라는 뜻이에요. 태어난 해, 달, 날, 시간을 각각 하나의 기둥으로 봐요.",
        "기둥 하나는 위 글자(천간)와 아래 글자(지지) 두 글자로 이뤄져요. 기둥이 네 개이니 모두 여덟 글자가 되고, 그래서 '사주팔자(四柱八字)'라고 불러요.",
        "이 여덟 글자 가운데 가장 중요한 글자는 태어난 날의 위 글자예요. 이 글자를 '일간(日干)'이라고 하고, 사주에서 '나 자신'을 뜻해요. 나머지 일곱 글자가 일간과 어떤 관계인지를 보고 성격, 일, 돈, 사람 관계를 읽어요.",
        "사주의 해와 달은 달력의 1월 1일이나 매달 1일이 아니라 절기(입춘, 경칩 등)를 기준으로 바뀌어요. 그래서 1월이나 2월 초에 태어난 분은 띠가 앞 해의 띠일 수 있어요.",
    ],
    "five_elements": [
        "오행(五行)은 세상을 이루는 다섯 가지 기운이에요. 목(나무), 화(불), 토(흙), 금(쇠), 수(물)예요. 사주의 여덟 글자는 모두 이 다섯 가지 중 하나에 속해요.",
        "오행은 서로 돕기도 하고(상생), 누르기도 해요(상극). 나무는 불을 키우고, 불은 재가 되어 흙을 만들고, 흙에서 쇠가 나오고, 쇠에 물방울이 맺히고, 물은 나무를 키워요. 반대로 나무는 흙을, 흙은 물을, 물은 불을, 불은 쇠를, 쇠는 나무를 눌러요.",
        "사주에서는 다섯 기운이 고르게 있을수록 안정적이라고 봐요. 어떤 기운이 너무 많거나 없으면 그 기운에 맞는 성격과 생활 습관이 두드러져요.",
    ],
    "stems_branches": [
        "천간(天干)은 각 기둥의 위 글자로 10가지가 있어요. 겉으로 드러나는 생각과 태도를 보여 줘요.",
        "지지(地支)는 각 기둥의 아래 글자로 12가지가 있어요. 우리가 아는 12띠와 같아요. 실제 생활과 환경, 속마음을 보여 줘요.",
    ],
    "symbols": [
        ["● ○", "점 하나가 글자 하나예요. ○는 그 기운이 없다는 뜻이에요."],
        ["밑줄 친 용어", "그 장 마지막 쪽 '용어 풀이'에서 다시 설명해요."],
        ["점수 그래프", "운의 흐름을 20~90점으로 나타낸 참고용 점수예요. 높을수록 나에게 필요한 기운이 들어오는 시기예요."],
        ["지금", "현재 지나고 있는 대운이나 해를 뜻해요."],
        ["합 · 충 · 형", "글자끼리 손잡고(합), 부딪히고(충), 마찰을 일으키는(형) 관계예요."],
    ],
    "tengod_intro": [
        "십신(十神)은 일간(나)과 다른 글자의 관계를 열 가지 이름으로 부른 것이에요. 오행이 서로 돕고 누르는 관계를 사람 사이의 관계에 빗대어 정리했어요.",
    ],
    "stage_intro": [
        "12운성은 일간(나)의 힘이 각 지지에서 얼마나 센지를 사람이 태어나서 늙고 다시 태어나는 12단계로 나타낸 것이에요. 단계가 좋고 나쁜 것이 아니라 힘을 쓰는 방식이 다르다는 뜻이에요.",
    ],
    "relation_intro": [
        "사주의 글자들은 서로 손을 잡기도 하고 부딪히기도 해요. 이런 관계를 합(合)과 충(沖) 등으로 불러요. 합은 협력과 인연, 충은 변화와 이동을 뜻해요. 충이 있다고 나쁜 사주가 아니라, 변화가 많고 활동적인 사주라는 뜻이에요.",
    ],
    "shinsal_intro": [
        "신살(神煞)은 사주에 붙는 특별한 기운이에요. 좋은 기운을 '귀인', 조심할 기운을 '살'이라고 불러요. 살이라는 이름이 붙어도 무조건 나쁜 것은 아니에요. 요즘은 대부분 재능이나 개성으로 풀이해요.",
    ],
    "daewoon_intro": [
        "대운(大運)은 10년마다 바뀌는 큰 운의 흐름이에요. 타고난 사주가 '나'라면, 대운은 내가 10년 동안 지나가는 환경이에요.",
        "같은 사람이라도 어떤 대운을 지나느냐에 따라 일이 잘 풀리기도 하고, 쉬어 가야 할 때도 있어요. 대운의 글자가 나에게 필요한 기운이면 힘이 실리고, 넘치는 기운이면 조절이 필요해요.",
    ],
    "health_notice": "이 장은 사주의 오행으로 본 생활 습관 안내예요. 의학적인 진단이 아니니, 몸이 불편하면 꼭 병원 진료를 받으세요.",
}


def _slot(sid: str, guide: str, chars: int = FULL, fmt: str = "paragraphs") -> dict:
    return {"id": sid, "guide": guide, "chars": chars, "format": fmt}


def page(pid: str, title: str, *, figure: str | None = None, slot: dict | None = None,
         static: str | None = None, span: int = 1, opener: bool = False) -> dict:
    return {"id": pid, "title": title, "figure": figure, "slot": slot, "static": static,
            "span": span, "opener": opener}


def _rel_len(luck: dict) -> int:
    """운세 카드 아래 '내 사주와의 관계' 줄이 차지하는 만큼 글을 줄인다."""
    n = len(", ".join(luck["relations_text"]))
    return 0 if n == 0 else 40 + n


def _wrap(section_no: str, chapter_terms: list[str]) -> dict:
    """장 마지막 쪽: 용어 풀이 + 정리."""
    return page(f"s{section_no}_wrap", "용어 풀이와 정리", figure="wrap",
                slot=_slot(f"s{section_no}_wrap",
                           "이 장의 핵심을 3줄로 정리하고(bullets), 마지막에 짧은 조언 한 문장(word)을 써 주세요.",
                           220, "summary"))


def build_outline(f: dict) -> list[dict]:
    """facts → 장(section) 목록. 각 장은 pages를 가진다."""
    dm = f["day_master"]
    name = f["person"]["name"]
    sections: list[dict] = []

    def section(no: str, pages: list[dict], terms: list[str] | None = None) -> None:
        title, subtitle = next((t, s) for n, t, s in SECTIONS if n == no)
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": terms or []})

    # 1. 내 사주 한눈에 보기 (1~10쪽)
    section("1", [
        page("cover", "표지", figure="cover"),
        page("toc", "목차", figure="toc", span=2),
        page("how_to_read", "이 책을 읽는 방법", static="how_to_read", opener=True),
        page("what_is_saju", "사주란 무엇인가", static="what_is_saju", figure="four_pillars_diagram"),
        page("five_elements", "오행(나무·불·흙·쇠·물)이란", static="five_elements", figure="element_cycle"),
        page("stems_branches", "천간과 지지(띠)란", static="stems_branches", figure="stems_branches"),
        page("chart", "나의 사주표", figure="pillars",
             slot=_slot("chart", f"{name}님의 사주팔자 여덟 글자를 소개하고, 일간이 {dm['stem']}({dm['element_name']})이라는 것과 그 뜻을 쉽게 설명해 주세요.", HALF)),
        page("chart_detail", "나의 사주 상세표", figure="pillars_detail",
             slot=_slot("chart_detail", "상세표의 각 줄(십신, 지장간, 12운성)이 무엇을 보여 주는지 이 사람의 실제 글자를 예로 들어 설명해 주세요.", HALF)),
    ])

    # 2. 타고난 기질과 사주의 구성 (11~22쪽)
    section("2", [
        page("el_ratio", "내 사주의 오행 비율", figure="elements_bar", opener=True,
             slot=_slot("el_ratio", "오행 비율 그래프를 읽어 주고, 가장 많은 기운과 가장 적은 기운이 무엇인지 말해 주세요.", HALF)),
        page("el_many_few", "많은 오행과 부족한 오행",
             slot=_slot("el_many_few", "많은 오행과 부족한 오행이 성격과 생활에 어떻게 나타나는지, 부족한 기운을 채우는 생활 습관까지 자세히 써 주세요.")),
        page("tg_intro", "십신이란", static="tengod_intro", figure="tengod_table"),
        page("tg_mine", "내 사주의 십신", figure="tengod_dots",
             slot=_slot("tg_mine", "많은 십신과 없는 십신이 이 사람에게 어떤 의미인지 써 주세요.", HALF)),
        page("stage_intro", "12운성이란", static="stage_intro", figure="stage_table"),
        page("stage_mine", "내 사주의 12운성", figure="my_stages",
             slot=_slot("stage_mine", "네 기둥의 12운성이 각각 인생의 어느 부분(어린 시절, 사회생활, 나 자신, 노년·자녀)에 어떤 힘으로 나타나는지 써 주세요.", HALF)),
        page("hidden", "지장간(숨은 글자)", figure="hidden",
             slot=_slot("hidden", "지장간이 무엇인지 설명하고, 이 사람의 지지 속에 숨은 글자가 보여 주는 속마음과 잠재력을 써 주세요.", HALF)),
        page("rel_intro", "합·충이란", static="relation_intro", figure="relation_table"),
        page("rel_mine", "내 사주의 합·충", figure="my_relations",
             slot=_slot("rel_mine", "이 사람 사주 안의 합·충·형 관계를 하나씩 풀어 주세요. 관계가 없으면 그것이 무슨 뜻인지 설명해 주세요.",
                            max(150, HALF - 45 * max(0, len(f["relations"]) - 2)))),
        page("ss_intro", "신살이란", static="shinsal_intro", figure="shinsal_table"),
        page("ss_mine", "내 사주의 신살", figure="my_shinsal",
             slot=_slot("ss_mine", "이 사람에게 있는 신살을 하나씩, 생활에서 어떻게 나타나고 어떻게 살리면 좋은지 써 주세요.",
                            max(150, HALF - 45 * max(0, len(f["shinsal"]) - 2)))),
        page("strength", "신강·신약, 격국, 용신", figure="strength",
             slot=_slot("strength", "신강/신약 점수, 격국, 용신이 각각 무엇이고 이 사람에게 어떤 의미인지 써 주세요.", HALF)),
    ], ["오행", "십신", "12운성", "지장간", "합", "충", "신살", "신강", "격국", "용신"])

    # 3. 나는 어떤 사람일까? (23~32쪽)
    section("3", [
        page("s3_open", "성격 한 줄 요약", figure="opener", opener=True,
             slot=_slot("s3_open", "이 사람의 성격을 한 문장으로 요약(lead)하고, 짧게 이유를 설명해 주세요.", 420, "lead")),
        page("s3_basic", "기본 성격", span=2, slot=_slot("s3_basic", f"일간 {dm['stem']}({dm['image']})을 중심으로 기본 성격, 말투, 첫인상, 일하는 태도를 자세히 써 주세요.", FULL * 2 - 60)),
        page("s3_inout", "겉모습과 속마음", span=2, slot=_slot("s3_inout", "천간(겉)과 지지·지장간(속)의 차이로 남들이 보는 모습과 실제 속마음을 비교해 주세요.", FULL * 2 - 60)),
        page("s3_good", "장점", slot=_slot("s3_good", "타고난 장점 3가지를 사주 근거와 함께 써 주세요.")),
        page("s3_bad", "단점과 보완법", slot=_slot("s3_bad", "단점 2~3가지와 각각의 구체적인 보완 방법을 써 주세요.")),
        page("s3_stress", "스트레스 받을 때", slot=_slot("s3_stress", "어떤 상황에서 스트레스를 받는지, 그때 어떻게 행동하는지, 회복하는 방법을 써 주세요.")),
        _wrap("3", []),
    ], ["일간", "천간", "지지", "지장간"] + [dm["stem"]])

    # 4. 나도 모르게 반복하는 행동 (33~38쪽)
    section("4", [
        page("s4_open", "패턴 한 줄 요약", figure="opener", opener=True,
             slot=_slot("s4_open", "이 사람이 반복하는 행동 패턴을 한 문장으로 요약(lead)하고 짧게 설명해 주세요.", 420, "lead")),
        page("s4_decide", "결정할 때의 습관", slot=_slot("s4_decide", "중요한 결정을 할 때 반복되는 습관을 써 주세요.")),
        page("s4_people", "인간관계에서 반복되는 문제", slot=_slot("s4_people", "인간관계에서 자주 반복되는 장면과 문제를 써 주세요.")),
        page("s4_why", "이 패턴이 생기는 이유", slot=_slot("s4_why", "이 패턴이 사주의 어떤 글자·관계에서 오는지 쉽게 설명해 주세요.")),
        page("s4_change", "바꾸는 방법", slot=_slot("s4_change", "패턴을 바꾸는 구체적인 방법 3가지를 써 주세요.")),
        _wrap("4", []),
    ], ["십신"])

    # 5. 일과 이직 시기 (39~46쪽)
    section("5", [
        page("s5_open", "직업운 한 줄 요약", figure="opener", opener=True,
             slot=_slot("s5_open", "직업운을 한 문장으로 요약(lead)하고 짧게 설명해 주세요.", 420, "lead")),
        page("s5_style", "일하는 스타일", slot=_slot("s5_style", "일하는 방식, 속도, 강점을 써 주세요.")),
        page("s5_jobs", "잘 맞는 직업", slot=_slot("s5_jobs", "잘 맞는 분야와 구체적인 직업 예시 8~10개를 이유와 함께 써 주세요.")),
        page("s5_type", "직장인형? 사업가형?", slot=_slot("s5_type", "직장, 프리랜서, 사업 중 어느 쪽이 맞는지 근거와 함께 써 주세요.")),
        page("s5_coworker", "잘 맞는 동료·상사", slot=_slot("s5_coworker", "잘 맞는 동료와 상사의 성향, 부딪히기 쉬운 성향을 써 주세요.")),
        page("s5_timing", "승진·이직하기 좋은 시기", figure="career_years",
             slot=_slot("s5_timing", "대운과 세운을 근거로 승진·이직·독립에 좋은 시기(연도)를 써 주세요.", HALF)),
        page("s5_caution", "직장에서 주의할 점", slot=_slot("s5_caution", "직장 생활에서 주의할 점을 써 주세요.")),
        _wrap("5", []),
    ], ["관성", "식상", "격국"])

    # 6. 돈 (47~54쪽)
    section("6", [
        page("s6_open", "재물운 한 줄 요약", figure="opener", opener=True,
             slot=_slot("s6_open", "재물운을 한 문장으로 요약(lead)하고 짧게 설명해 주세요.", 420, "lead")),
        page("s6_size", "타고난 재물운 크기", slot=_slot("s6_size", "신강약과 재성으로 본 타고난 재물운의 크기를 쉽게 설명해 주세요.")),
        page("s6_earn", "잘 맞는 돈 버는 방법", slot=_slot("s6_earn", "월급, 사업, 투자, 부업 중 맞는 방식과 이유를 써 주세요.")),
        page("s6_spend", "소비 습관", slot=_slot("s6_spend", "돈을 쓰는 습관과 돈이 새는 곳을 써 주세요.")),
        page("s6_save", "돈 모으는 방법", slot=_slot("s6_save", "이 사람에게 맞는 저축·관리 방법을 구체적으로 써 주세요.")),
        page("s6_in", "돈이 들어오는 시기", figure="money_years",
             slot=_slot("s6_in", "재물이 들어오는 대운과 연도를 근거와 함께 써 주세요.", HALF)),
        page("s6_out", "돈 조심해야 할 시기", slot=_slot("s6_out", "손실·보증·큰 지출을 조심할 시기와 대처법을 써 주세요.")),
        _wrap("6", []),
    ], ["재성", "편재", "정재"])

    # 7. 연애와 결혼 (55~64쪽)
    section("7", [
        page("s7_open", "연애운 한 줄 요약", figure="opener", opener=True,
             slot=_slot("s7_open", "연애운을 한 문장으로 요약(lead)하고 짧게 설명해 주세요.", 420, "lead")),
        page("s7_style", "연애 스타일", slot=_slot("s7_style", "연애할 때의 모습과 표현 방식을 써 주세요.")),
        page("s7_attract", "끌리는 사람 vs 잘 맞는 사람", slot=_slot("s7_attract", "끌리는 사람과 실제로 잘 맞는 사람을 비교해 주세요.")),
        page("s7_fight", "연애할 때 싸우는 이유", slot=_slot("s7_fight", "연인과 자주 부딪히는 이유와 푸는 방법을 써 주세요.")),
        page("s7_spouse", "배우자 모습", span=2, slot=_slot("s7_spouse", "일지(배우자 자리)와 배우자를 뜻하는 십신으로 배우자의 성격, 외모 분위기, 만나는 경로를 자세히 써 주세요.", FULL * 2 - 60)),
        page("s7_timing", "연애·결혼하기 좋은 시기", figure="love_years",
             slot=_slot("s7_timing", "인연이 오는 해와 결혼하기 좋은 해를 근거와 함께 써 주세요.", HALF)),
        page("s7_married", "결혼 생활", slot=_slot("s7_married", "결혼 생활의 모습과 주의할 점을 써 주세요.")),
        page("s7_keep", "지금 연인·배우자와 잘 지내는 법", slot=_slot("s7_keep", "지금 함께하는 사람과 관계를 오래 지키는 구체적인 방법을 써 주세요.")),
        _wrap("7", []),
    ], ["도화살", "홍염살", "재성", "관성"])

    # 8. 가족과 인간관계 (65~68쪽)
    section("8", [
        page("s8_parents", "부모님과의 관계", opener=True, slot=_slot("s8_parents", "부모님과의 관계, 받은 영향을 써 주세요.")),
        page("s8_siblings", "형제·친구와의 관계", slot=_slot("s8_siblings", "형제, 친구, 동료와의 관계를 써 주세요.")),
        page("s8_children", "자녀와의 관계", slot=_slot("s8_children", "자녀(또는 후배·아랫사람)와의 관계를 써 주세요.")),
        _wrap("8", []),
    ], ["비견", "겁재", "정인"])

    # 9. 건강 (69~72쪽)
    section("9", [
        page("s9_weak", "약하기 쉬운 곳", opener=True, figure="health_notice",
             slot=_slot("s9_weak", "오행 균형으로 볼 때 신경 쓰면 좋은 몸의 부분을 생활 습관 중심으로 써 주세요. 질병을 단정하지 마세요.", FULL - 260)),
        page("s9_season", "계절별 주의할 점", slot=_slot("s9_season", "봄·여름·가을·겨울 계절별 생활 팁을 써 주세요.")),
        page("s9_rest", "나에게 맞는 휴식·운동", slot=_slot("s9_rest", "이 사람에게 맞는 휴식, 잠, 운동 방법을 써 주세요.")),
        _wrap("9", []),
    ], ["오행"])

    # 10. 대운 (73~86쪽)
    dw = f["daewoon"]
    ci = max(dw["current_index"], 0)
    dpages = [
        page("dw_intro", "대운이란", static="daewoon_intro", figure="daewoon_info", opener=True),
        page("dw_graph", "인생 전체 운세 그래프", figure="life_graph",
             slot=_slot("dw_graph", "인생 그래프에서 운이 오르는 시기와 쉬어 가는 시기를 짚어 주세요.", HALF)),
    ]
    tail = [p for i, p in enumerate(dw["periods"]) if i > ci + 4]
    for i, p in enumerate(dw["periods"]):
        if i > ci + 4:
            continue
        now = " (지금)" if p["state"] == "지금" else ""
        dpages.append(page(f"dw_{i}", f"{p['age_text']} 대운{now}", figure="daewoon_card", span=p["pages"],
                           slot=_slot(f"dw_{i}", f"{p['age_text']} {p['ganzhi']}({p['hanja']}) 대운을 요약, 일, 돈, 연애, 건강, 조언 순서로 써 주세요.",
                                      FULL * p["pages"] - 330 - _rel_len(p), "fortune")))
        dpages[-1]["period_index"] = i
    if tail:
        dpages.append(page("dw_tail", f"{tail[0]['age_from']}세 이후 대운", figure="daewoon_tail",
                           slot=_slot("dw_tail", "이후 대운들을 각각 2~3문장씩 요약해 주세요.", FULL - 200)))
    section("10", dpages, ["대운", "대운수", "순행·역행", "간지"])

    # 11. 연도별 (87~94쪽)
    spages = []
    for i, s in enumerate(f["sewoon"]):
        spages.append(page(f"sw_{s['year']}", f"{s['year']}년 운세", figure="sewoon_card", span=s["pages"], opener=(i == 0),
                           slot=_slot(f"sw_{s['year']}", f"{s['year']}년 {s['ganzhi']}({s['hanja']})년의 운세를 요약, 좋은 점, 주의할 점, 일, 돈, 연애, 좋은 달 순서로 써 주세요.",
                                      FULL * s["pages"] - (400 if i == 0 else 330) - _rel_len(s), "fortune")))
        spages[-1]["year"] = s["year"]
    section("11", spages, ["세운"])

    # 12. 월별 (95~98쪽)
    mpages = []
    for q in range(4):
        ms = f["months"][q * 3:q * 3 + 3]
        if not ms:
            break
        label = f"{ms[0]['year']}년 {ms[0]['month']}월 ~ {ms[-1]['year']}년 {ms[-1]['month']}월" if ms[0]["year"] != ms[-1]["year"] else f"{ms[0]['year']}년 {ms[0]['month']}월 ~ {ms[-1]['month']}월"
        mpages.append(page(f"mw_{q}", f"{label} 운세", figure="months3", opener=(q == 0),
                           slot=_slot(f"mw_{q}", "세 달 각각의 운세를 요약, 좋은 일, 주의할 일 순서로 짧게 써 주세요. 한 달에 각 항목 1~2문장입니다.", 230 if q == 0 else 290, "months")))
        mpages[-1]["month_range"] = [q * 3, q * 3 + len(ms)]
    section("12", mpages, ["월운", "절기"])

    # 13. 질문 (99~102쪽)
    q = f["order"]["question"]
    section("13", [
        page("s13_answer", "주문할 때 남긴 질문에 대한 답", span=2, opener=True, figure="question",
             slot=_slot("s13_answer", (f"고객 질문: \"{q}\". 사주 근거를 들어 솔직하고 구체적으로 답해 주세요." if q else
                                       f"질문이 없으니 고객의 요즘 일상({f['order']['daily'] or '알 수 없음'})에 맞춰 지금 가장 궁금해할 고민에 답해 주세요."), FULL * 2 - 200)),
        page("s13_decide", "중요한 결정(이사·이직·결혼·창업)하기 좋은 시기",
             slot=_slot("s13_decide", "이사, 이직, 결혼, 창업 각각에 좋은 시기(연도)를 근거와 함께 써 주세요.")),
        page("s13_careful", "조심해야 할 시기", slot=_slot("s13_careful", "조심해야 할 시기와 그때 할 일을 써 주세요.")),
    ])

    # 14. 행운 (103~106쪽)
    section("14", [
        page("s14_yong", "나에게 필요한 기운(용신)", figure="yongsin", opener=True,
             slot=_slot("s14_yong", "용신이 무엇인지와 왜 이 사람에게 이 기운이 필요한지 써 주세요.", HALF)),
        page("s14_lucky", "행운의 색·숫자·방향", figure="lucky",
             slot=_slot("s14_lucky", "행운의 색·숫자·방향을 생활에서 쓰는 구체적인 방법을 써 주세요.", HALF)),
        page("s14_items", "도움 되는 음식·물건", figure="lucky_items",
             slot=_slot("s14_items", "도움 되는 음식과 물건, 공간을 생활에서 쓰는 방법을 써 주세요.", HALF)),
        page("s14_animals", "잘 맞는 띠", figure="animals",
             slot=_slot("s14_animals", "잘 맞는 띠와 조심할 띠를 설명하고, 띠는 참고만 하라는 말을 덧붙여 주세요.", HALF)),
    ])

    # 15. 해결 방법과 마지막 조언 (107~110쪽)
    section("15", [
        page("s15_key", "지금 내 사주에서 가장 중요한 세 가지", opener=True,
             slot=_slot("s15_key", "이 책 전체에서 가장 중요한 세 가지(타고난 힘, 지금 운의 흐름, 꼭 고칠 습관)를 한 문장 요약(lead)과 함께 정리해 주세요.", 600, "lead")),
        page("s15_work", "일·직업 해결 방법",
             slot=_slot("s15_work", "일과 직업 고민에 대한 해결 방법을 모두 모아 주세요. 앞 장의 보완법을 빠짐없이 포함하고, 언제 무엇을 할지까지 구체적으로 써 주세요.")),
        page("s15_money", "돈 해결 방법",
             slot=_slot("s15_money", "돈 고민에 대한 해결 방법을 모두 모아 주세요. 버는 법, 지키는 법, 조심할 해와 그때 할 일까지 구체적으로 써 주세요.")),
        page("s15_love", "연애·결혼·사람 관계 해결 방법",
             slot=_slot("s15_love", "연애, 결혼, 가족, 인간관계 고민에 대한 해결 방법을 모두 모아 주세요. 미혼과 기혼 모두에게 맞게 경우를 나눠 써 주세요.")),
        page("s15_health", "건강·마음 해결 방법",
             slot=_slot("s15_health", "몸과 마음을 지키는 방법을 모두 모아 주세요. 스트레스 대처, 잠, 계절별 습관을 생활 습관 중심으로 써 주세요. 병명은 쓰지 않습니다.")),
        page("s15_plan", "시기별 행동 계획", figure="plan",
             slot=_slot("s15_plan", "먼저 앞으로 6년의 큰 흐름과 대운이 바뀌는 시점을 설명하는 문단(notes, 약 250자)을 쓰고, 해마다 할 일(do)과 피할 일(avoid)을 한 줄씩 정리해 주세요.", 680, "plan")),
        page("s15_qa", "걱정을 덜어 주는 문답", span=2,
             slot=_slot("s15_qa", "이 사주를 가진 사람이 가장 많이 할 걱정 6~8가지를 질문(q)으로 쓰고, 사주 근거와 현실적인 대처법으로 불안을 풀어 주는 답(a)을 써 주세요. 주문 때 남긴 질문과 관련된 걱정을 먼저 다룹니다.", FULL * 2 - 150, "qa")),
        page("s15_habits", "운을 키우는 생활 습관", figure="habits",
             slot=_slot("s15_habits", "용신과 이 사주의 약한 점을 바탕으로 매일·매주·매달 실천할 습관 10가지를 체크리스트로 써 주세요. 한 줄에 한 가지, 바로 할 수 있는 행동으로 씁니다.", 520, "checklist")),
        page("s15_last", "마지막 조언", figure="summary_table",
             slot=_slot("s15_last", f"{name}님에게 전하는 마지막 조언을 따뜻하지만 담백하게 써 주세요. 걱정보다 할 수 있는 일에 집중하게 해 주세요.", FULL - 250)),
    ])

    # 부록 (111~114쪽)
    section("부록", [
        page("glossary", "용어 사전", figure="glossary", span=3, opener=True),
        page("method", "계산 기준 안내", figure="method"),
    ])

    # 다른 사주 안내 (사이트 순서) · 책의 마지막
    section("더보기", [
        page("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True),
    ])

    return sections


def all_pages(sections: list[dict]) -> list[dict]:
    return [p for s in sections for p in s["pages"]]


def slots_by_section(sections: list[dict]) -> dict[str, list[dict]]:
    out = {}
    for s in sections:
        sl = [dict(p["slot"], title=p["title"]) for p in s["pages"] if p.get("slot")]
        if sl:
            out[s["no"]] = sl
    return out
