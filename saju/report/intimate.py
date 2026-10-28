"""깊은 궁합 리포트(50쪽 이상): 두 사람 사주 비교, 끌림과 부딪힘, 관계의 흐름, 결혼.

목차 원본: /mnt/project-files/plan/intimate-report-toc.md (2026-10-11, 인터뷰 주제 20가지 반영)
사이트 입력: 관계 상태(status), 알고 지낸 기간(duration, 필수), 내 정보, 그 사람 정보, 질문.
"""

from __future__ import annotations

from . import theme as T
from .outline import FULL, HALF, _slot
from ..pair import compare

FINAL_SECTION = "12"

SECTIONS = [
    ("1", "두 사람 사주 한눈에 보기", "나와 그 사람의 사주표"),
    ("2", "한눈에 보는 우리의 궁합", "우리의 궁합 점수와 핵심"),
    ("3", "그 사람 눈에 보이는 나", "그 사람이 느끼는 나의 매력과 단점"),
    ("4", "내가 몰랐던 그 사람", "성격, 속마음, 사랑 표현"),
    ("5", "우리가 서로 끌리는 이유", "오행으로 보는 매력과 궁합"),
    ("6", "우리가 자주 다투는 이유", "다툼이 반복되는 이유와 화해법"),
    ("7", "우리가 가까워지는 속도와 거리", "친밀함과 혼자만의 시간"),
    ("8", "돈과 일상", "돈 쓰는 방식, 생활 습관, 가족"),
    ("9", "우리 관계의 흐름", "월별 궁합운, 연도별 궁합운"),
    ("10", "결혼과 그 이후 우리", "우리의 결혼 시기와 부부가 된 모습"),
    ("11", "지금 우리 사이와 질문에 대한 답", ""),
    ("12", "우리가 오랫동안 함께하는 방법", "마지막 조언"),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

STATIC = {
    "im_how_to_read": [
        "이 책은 두 사람의 태어난 날과 시간으로 계산한 사주를 나란히 놓고, 서로 끌리는 이유와 부딪히는 지점, 돈과 일상, 앞으로의 흐름과 결혼까지 순서대로 풀어 놓은 책이에요.",
        "가장 궁금한 내용은 2장 '한눈에 보는 우리 궁합'에 먼저 모아 두었어요. 자세한 이유와 방법은 뒤의 장에서 하나씩 설명해요.",
        "궁합은 좋고 나쁨을 가르는 시험이 아니에요. 두 사람이 어디서 잘 맞고 어디서 다른지 알면, 다른 부분은 미리 대비하고 맞는 부분은 더 키울 수 있어요.",
        "사주 용어는 쉬운 말과 생활 장면으로 자세히 풀었고, 쪽 끝 '기억할 한 줄'에 그 쪽의 핵심을 한 문장으로 정리했어요.",
    ],
    "im_what_is_saju": [
        "사주(四柱)는 태어난 해, 달, 날, 시간의 네 기둥이에요. 기둥마다 위 글자(천간)와 아래 글자(지지)가 있어 모두 여덟 글자가 돼요.",
        "여덟 글자는 모두 오행(五行) 가운데 하나예요. 목(나무), 화(불), 토(흙), 금(쇠), 수(물)의 다섯 기운이 서로 돕고(상생) 누르며(상극) 균형을 이뤄요.",
        "궁합에서는 두 사람의 일간(나를 나타내는 글자)끼리, 일지(배우자 자리)끼리의 관계와, 서로 모자란 기운을 채워 주는지를 가장 먼저 봐요.",
    ],
    "im_pair": [
        "궁합 점수는 두 사람의 일간 관계, 배우자 자리 관계, 오행 보완, 여덟 글자 사이의 합과 충을 더하고 빼서 계산한 점수가 낮아도 다른 점을 알고 맞춰 가면 충분히 좋은 관계가 될 수 있어요.",
    ],
}

_STATUS = {"연애 중이에요": "연애 중", "혼자 좋아하고 있어요": "짝사랑", "서로 알아가는 중이에요": "썸",
           "결혼한 사이예요": "부부", "헤어진 사이예요": "헤어짐"}


def _score(cmp: dict) -> int:
    s = 62 + 4 * cmp["cross_relations"]["harmony"] - 3 * cmp["cross_relations"]["tension"]
    s += 6 * (len(cmp["elements"]["상대가_채워주는_나의_부족"]) + len(cmp["elements"]["내가_채워주는_상대의_부족"]))
    s += {"조화": 8, "긴장": -8, "복합": 2}.get(cmp["spouse_palace"]["tone"], 0)
    s += {"상대가 나를 생함": 5, "내가 상대를 생함": 5, "같은 기운": 3}.get(cmp["day_master"]["element_relation"], 0)
    s += 4 if any(r.startswith("천간합") for r in cmp["day_master"]["relations"]) else 0
    return max(48, min(96, s))


def build(f: dict, result: dict, answers: dict, partner: dict) -> dict:
    o = f["partner"]
    cmp = compare(T.fourpillars(result), T.fourpillars(partner))
    my_group = "재성" if f["person"]["sex"] == "male" else "관성"
    o_group = "재성" if o["person"]["sex"] == "male" else "관성"
    o_day = T.day_of(o)

    def pair_mark(x: dict, ox: dict) -> dict:
        me_star, o_star = T.has(x, my_group), T.has(ox, o_group)
        hap_me, hap_o = T.rel(x, "일주", T.HAP), T.rel(ox, "일주", T.HAP)
        clash_me, clash_o = T.rel(x, "일주", T.CLASH), T.rel(ox, "일주", T.CLASH)
        signs = [s for s, on in (("나의 배우자 별", me_star), ("그 사람의 배우자 별", o_star), ("내 배우자 자리와 합", hap_me),
                                 ("그 사람 배우자 자리와 합", hap_o), ("내 배우자 자리와 충", clash_me), ("그 사람 배우자 자리와 충", clash_o)) if on]
        score = (x["score"] + ox["score"]) / 2 + 6 * me_star + 6 * o_star + 6 * hap_me + 6 * hap_o - 7 * clash_me - 7 * clash_o
        return {"t_score": T.clamp(score), "t_signs": signs}

    years = [dict(x, **pair_mark(x, ox)) for x, ox in zip(T.screen_years(f), T.screen_years(o))]
    months = [dict(x, **pair_mark(x, ox)) for x, ox in zip(f["months"], o["months"])]
    T.reveal_fix(result, "intimate", years)   # 제1조항: 결제 전 화면의 12년 지도와 같은 표시·방향
    T.reveal_fix(result, "intimate", months)

    def my_mark(p: dict) -> dict:
        star, hap = T.has(p, my_group), T.rel(p, "일주", T.HAP)
        clash = T.rel(p, "일주", T.CLASH)
        rel_o = T.against(p["ganzhi"], o_day["stem"], o_day["branch"])
        o_hap = any(k in T.HAP + ("천간합",) for k in rel_o)
        signs = [s for s, on in (("배우자 별", star), ("배우자 자리와 합", hap), ("그 사람 일주와 합", o_hap), ("배우자 자리와 충", clash)) if on]
        return {"t_score": T.clamp(p["score"] + 8 * star + 8 * hap + 8 * o_hap - 8 * clash), "t_signs": signs}

    periods = [dict(p, **my_mark(p)) for p in f["daewoon"]["periods"]]

    def marriage(fx: dict, group: str) -> list[dict]:
        return [{"age_text": p["age_text"], "years_text": p["years_text"], "ganzhi": p["ganzhi"]}
                for p in fx["daewoon"]["periods"] if p["state"] != "지난" and (T.has(p, group) or T.rel(p, "일주", T.HAP))][:3]

    screen = T.screen_score(f, result, "intimate")
    data = {
        "screen_score": screen,
        "status": _STATUS.get(answers.get("status", ""), answers.get("status", "")),
        "duration": answers.get("duration", ""),
        "compare": cmp, "score": _score(cmp),
        "best_years": T.best(years, 12, lambda y: y["year"]),
        "best_months": T.best(months, 3, T.ym), "careful_months": T.worst(months, 3, T.ym),
        "money": {"나": {"재성": T.count(f, "재성"), "비겁": T.count(f, "비겁"), "식상": T.count(f, "식상")},
                  "그 사람": {"재성": T.count(o, "재성"), "비겁": T.count(o, "비겁"), "식상": T.count(o, "식상")}},
        "marriage_me": marriage(f, my_group), "marriage_partner": marriage(o, o_group),
    }
    return {
        "label": "궁합 재료", "data": data,
        "digest": {**data, "그 사람 사주": T.chart_brief(o), **T.digest_rows(years, months, T.near(f, periods, 30)),
                   "점수 설명": "score는 궁합 점수. t_score는 그해·그달 두 사람 관계의 흐름 점수(두 사람 운의 흐름 평균에 배우자 별·배우자 자리 합을 더하고 충을 뺀 값)"},
        "years": years, "months": months, "periods": periods,
    }


STYLE = T.style("깊은 궁합", """
[깊은 궁합 규칙]
- 독자는 연인, 썸, 짝사랑, 부부 등 한 사람과의 관계가 궁금한 사람입니다. 두 사람을 모두 존중하며 씁니다.
- 근거는 '궁합 재료'(compare, 궁합 점수 score, 해·달별 t_score와 표시 t_signs, 그 사람 사주)를 먼저 씁니다.
- 상대방은 "그 사람" 또는 이름으로 부릅니다. 성별 고정관념으로 쓰지 않습니다.
- 그 사람의 마음, 진심, 바람기 등은 단정하지 않습니다. 사주로 보이는 성향과 표현 방식으로만 씁니다.
- 관계 상태(status)와 알고 지낸 기간(duration)에 맞춰 씁니다. 짝사랑·썸이면 다가가는 법, 연애 중이면 오래 가는 법, 부부면 함께 사는 법을 중심으로 씁니다.
- 친밀함은 마음의 거리, 연락, 함께하는 시간 중심으로 점잖게 씁니다.
""")


def build_outline(f: dict) -> list[dict]:
    th = f["theme"]
    t = th["data"]
    cmp = t["compare"]
    o = f["partner"]
    name, oname = f["person"]["name"], o["person"]["name"] or "그 사람"
    sections: list[dict] = []

    def section(no: str, pages: list[dict]) -> None:
        title, subtitle = next((a, b) for n, a, b in SECTIONS if n == no)
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": []})

    P, S = T.tpage, _slot
    section("1", [
        P("cover", "표지", figure="cover"),
        P("toc", "목차", figure="toc"),
        P("how_to_read", "이 책을 읽는 방법", static="im_how_to_read", opener=True),
        P("im_saju", "사주와 오행 짧게 알기", static="im_what_is_saju", figure="element_cycle"),
        P("chart", "두 사람의 사주표", figure="pair_pillars",
          slot=S("chart", f"{name}님과 {oname}님의 일간({cmp['day_master']['me']}·{cmp['day_master']['other']})과 일지를 소개하고, 두 사람이 한눈에 어떤 조합인지 쉽게 설명해 주세요.", HALF - 120)),
    ])
    section("2", [
        P("im_glance", "한눈에 보는 우리 궁합", static="im_pair", figure="kv", opener=True, rows=[
            T.screen_row(t["screen_score"]),
            ["두 사람 궁합 점수(두 사람 사주를 함께 본 점수)", f"{t['score']}점 "],
            ["일간끼리", f"{cmp['day_master']['me']}·{cmp['day_master']['other']} · {cmp['day_master']['element_relation']}"],
            ["배우자 자리끼리", f"{cmp['spouse_palace']['me']}·{cmp['spouse_palace']['other']} · {cmp['spouse_palace']['tone']}"],
            ["합 · 충", f"손잡는 관계 {cmp['cross_relations']['harmony']}개 · 부딪히는 관계 {cmp['cross_relations']['tension']}개"],
            ["관계가 깊어지는 달", ", ".join(t["best_months"])],
            ["두 사람에게 좋은 해", ", ".join(f"{y}년" for y in t["best_years"]) or "앞으로 12년 안에는 뚜렷하지 않아요"],
        ], slot=S("im_glance", "표를 이어서 두 사람 궁합의 핵심을 짧게 소개하고, 자세한 내용은 뒤 장에서 다룬다고 안내해 주세요.", HALF - 200)),
    ])
    section("3", [
        P("im3_open", "그 사람에게 나는 어떤 기운일까", figure="kv", opener=True, rows=[
            ["그 사람에게 나는", f"{cmp['day_master']['me_as_other_ten_god']}의 기운"],
            ["나에게 그 사람은", f"{cmp['day_master']['other_as_my_ten_god']}의 기운"],
        ], slot=S("im3_open", f"{oname}님에게 {name}님이 어떤 기운(me_as_other_ten_god)인지 한 문장으로 요약(lead)하고, 그 십신이 관계에서 어떤 느낌을 주는지 설명해 주세요.", 520, "lead")),
        P("im3_charm", "그 사람이 느끼는 나의 매력",
          slot=S("im3_charm", "그 사람 사주 쪽에서 본 나의 매력 포인트를 오행 보완과 십신 근거로 장면과 함께 써 주세요.")),
        P("im3_hurt", "그 사람이 서운해하기 쉬운 나의 모습",
          slot=S("im3_hurt", "그 사람이 나에게 서운함을 느끼기 쉬운 순간을 근거와 함께 장면으로 쓰고, 각각 보완법을 붙여 주세요.")),
        P("im3_love", "그 사람에게 더 사랑받는 방법",
          slot=S("im3_love", "그 사람의 용신과 약한 기운을 근거로, 그 사람이 특히 고마워하고 마음을 여는 말과 행동을 장면과 함께 써 주세요.")),
    ])
    section("4", [
        P("im4_open", "그 사람의 사주", figure="kv", opener=True, rows=[
            ["나타내는 글자", f"{o['day_master']['stem']}({o['day_master']['hanja']}) · {o['day_master']['image']}"],
            ["강한 기운", ", ".join(e["name"] for e in o["elements"] if e["status"] == "많음") or "고른 편"],
            ["약한 기운", ", ".join(e["name"] for e in o["elements"] if e["status"] == "부족") or "고른 편"],
            ["사주의 틀", f"{o['strength']['label']} · {o['gyeokguk']['name']}"],
        ], slot=S("im4_open", f"{oname}님의 사주를 쉽게 소개해 주세요.", HALF - 40)),
        P("im4_person", "그 사람의 성격",
          slot=S("im4_person", "그 사람의 일간·강한 기운·십신으로 성격의 장점과 약점을 장면으로 써 주세요.")),
        P("im4_heart", "그 사람의 속마음과 사랑 표현",
          slot=S("im4_heart", "그 사람이 좋아하는 마음을 표현하는 방식, 겉과 속이 다른 지점, 마음이 진심일 때 보이는 행동 신호를 사주 근거로 써 주세요. 단정하지 않습니다.")),
        P("im4_need", "그 사람이 힘들 때 필요한 것",
          slot=S("im4_need", "그 사람의 약한 기운과 용신을 근거로 그 사람이 지치거나 힘들 때 필요한 말과 행동, 피해야 할 말을 써 주세요.")),
    ])
    elem_rows = [[e["name"], f"{e['pct']}%", f"{oe['pct']}%"] for e, oe in zip(f["elements"], o["elements"])]
    section("5", [
        P("im5_open", "두 사람의 오행 비교", figure="grid", opener=True, grid={"head": ["오행", name, oname], "rows": elem_rows, "hl": []},
          slot=S("im5_open", "오행 표를 근거로 두 사람이 서로 채워 주는 기운과 겹치는 기운을 설명해 주세요.", HALF - 40)),
        P("im5_pull", "서로 끌리는 이유",
          slot=S("im5_pull", "오행 보완, 일간 관계, 합 관계를 근거로 두 사람이 끌리는 이유를 장면으로 써 주세요.")),
        P("im5_fill", "서로 채워 주는 것",
          slot=S("im5_fill", "각자 상대에게 채워 주는 기운이 생활에서 어떤 도움으로 나타나는지(결정, 감정, 일, 휴식) 장면으로 쓰고, 그 장점을 키우는 방법을 써 주세요.")),
    ])
    section("6", [
        P("im6_open", "부딪히는 글자", figure="kv", opener=True, rows=[
            ["배우자 자리끼리", ", ".join(cmp["spouse_palace"]["relations"]) or "특별한 합충 없음"],
            ["띠끼리", f"{cmp['zodiac']['me']}·{cmp['zodiac']['other']} · {', '.join(cmp['zodiac']['relations']) or '특별한 합충 없음'}"],
            ["태어난 달끼리", ", ".join(cmp["month_branch"]["relations"]) or "특별한 합충 없음"],
            ["부딪히는 관계", f"{cmp['cross_relations']['tension']}개"],
        ], slot=S("im6_open", "표를 근거로 두 사람이 어디서 부딪히기 쉬운지 핵심을 한 문장(lead)으로 말하고 설명해 주세요.", 470, "lead")),
        P("im6_fight", "다툼이 반복되는 장면",
          slot=S("im6_fight", "충·형 관계와 두 사람의 넘치는 기운을 근거로 다툼이 반복되기 쉬운 장면 3가지를 쓰고, 각각 그 순간의 두 사람 반응을 써 주세요.")),
        P("im6_talk", "연락과 표현 방식의 차이",
          slot=S("im6_talk", "두 사람의 식상(표현)·인성(받아들임) 개수와 일간 오행으로 연락 빈도, 답장 속도, 애정 표현 방식이 어떻게 다른지 쓰고 맞추는 방법을 써 주세요.")),
        P("im6_makeup", "우리에게 맞는 화해법",
          slot=S("im6_makeup", "두 사람 사주에 맞는 화해의 순서와 말, 각자 진정하는 데 필요한 시간과 방법을 구체적으로 써 주세요.")),
    ])
    section("7", [
        P("im7_open", "가까워지는 속도", figure="opener", opener=True,
          slot=S("im7_open", "두 사람이 가까워지는 속도가 어떻게 다른지 한 문장(lead)으로 요약하고 사주 근거로 설명해 주세요.", 620, "lead")),
        P("im7_space", "혼자만의 시간이 필요한 순간",
          slot=S("im7_space", "각자에게 혼자만의 시간이 필요한 때와 이유를 쓰고, 서운하지 않게 거리를 두는 방법을 써 주세요.")),
        P("im7_jealous", "질투와 서운함 다루기",
          slot=S("im7_jealous", "이 조합에서 질투나 서운함이 생기기 쉬운 상황과 다루는 방법을 근거와 함께 써 주세요.")),
        P("im7_lean", "서로에게 기대는 방식",
          slot=S("im7_lean", "힘든 일이 생겼을 때 두 사람이 위로를 주고받는 방식이 어떻게 다른지 인성·식상 근거로 쓰고, 서로에게 맞는 위로법을 써 주세요.")),
    ])
    m = t["money"]
    section("8", [
        P("im8_open", "두 사람의 돈 기운", figure="grid", opener=True, grid={"head": ["", "재성(재물)", "비겁(나·동료)", "식상(표현·재능)"],
                                                                     "rows": [[name, f"{m['나']['재성']}개", f"{m['나']['비겁']}개", f"{m['나']['식상']}개"],
                                                                              [oname, f"{m['그 사람']['재성']}개", f"{m['그 사람']['비겁']}개", f"{m['그 사람']['식상']}개"]], "hl": []},
          slot=S("im8_open", "표를 근거로 두 사람의 돈 버는 방식과 쓰는 방식이 어떻게 다른지 설명해 주세요.", HALF)),
        P("im8_money", "함께 돈을 관리하는 법",
          slot=S("im8_money", "데이트 비용, 저축, 큰 지출을 정할 때 부딪히기 쉬운 지점과 이 조합에 맞는 돈 관리 규칙을 구체적으로 써 주세요.")),
        P("im8_daily", "생활 습관과 일상",
          slot=S("im8_daily", "두 사람의 오행과 조후(따뜻함·차가움)로 생활 리듬(아침형·저녁형, 쉬는 방식, 여행 취향)의 차이와 맞추는 방법을 써 주세요.")),
        P("im8_family", "서로의 가족과 친구",
          slot=S("im8_family", "두 사람의 인성(부모)·비겁(친구) 구성과 년주·월주 관계를 근거로 서로의 가족·친구와 지낼 때 조심할 점과 좋은 방법을 써 주세요.")),
    ])
    section("9", [
        P("im9_months", "앞으로 12개월 월별 궁합운", figure="grid", opener=True, span=2, grid=T.month_grid(th["months"], "관계 점수"),
          note="표시: 그 달의 글자가 두 사람의 배우자 별·배우자 자리와 맺는 관계예요.",
          slot=S("im9_months", "표의 12개월 가운데 관계가 깊어지는 달과 조심할 달을 골라 달마다 함께 하면 좋은 일을 써 주세요.", FULL * 2 - 820)),
        P("im9_careful", "다투기 쉬운 달 미리 대비하기",
          slot=S("im9_careful", "조심할 달마다 왜 부딪히기 쉬운지 근거를 쓰고, 그달에 미리 할 일(약속, 일정, 말투)을 써 주세요.")),
        P("im9_years", "앞으로 12년 궁합운", figure="grid", span=3, grid=T.year_grid(th["years"], t["best_years"], "관계 점수"),
          slot=S("im9_years", "표의 12년을 한 해씩 짧은 문단으로 써 주세요(두 사람 각각의 표시 근거, 관계의 흐름, 함께 할 일).", FULL * 3 - 460)),
        P("im9_graph", "나이별 인연의 흐름", figure="theme_graph", note="대운(10년)마다 배우자 별과 그 사람과의 합이 들어오면 점수가 올라가요.",
          slot=S("im9_graph", f"{name}님의 대운 그래프에서 이 관계에 힘이 실리는 시기와 조심할 시기를 나이로 짚어 주세요.", HALF - 40)),
    ])
    mm = lambda xs: ", ".join(f"{p['age_text']}({p['years_text']})" for p in xs) or "뚜렷한 시기 없음"
    section("10", [
        P("im10_open", "두 사람의 결혼 인연 시기", figure="kv", opener=True, rows=[
            [name, mm(t["marriage_me"])], [oname, mm(t["marriage_partner"])],
            ["두 사람에게 좋은 해", ", ".join(f"{y}년" for y in t["best_years"]) or "앞으로 12년 안에는 뚜렷하지 않아요"],
        ], slot=S("im10_open", "표를 근거로 두 사람의 결혼 인연이 겹치는 시기를 설명해 주세요.", HALF)),
        P("im10_can", "결혼까지 갈 수 있을까",
          slot=S("im10_can", "배우자 자리 관계, 궁합 점수, 결혼 인연 시기를 근거로 결혼까지 이어지는 조건과 걸림돌을 솔직하게 써 주세요.")),
        P("im10_couple", "결혼하면 어떤 부부가 될까",
          slot=S("im10_couple", "두 사람이 함께 살 때의 모습(집안일, 돈, 대화, 쉬는 날)을 장면으로 쓰고, 부딪히는 지점의 보완법을 붙여 주세요.")),
        P("im10_check", "결혼 전에 함께 확인할 것",
          slot=S("im10_check", "이 조합에서 결혼 전에 꼭 이야기해 둘 것 6가지를 이유와 함께 써 주세요.", FULL, "checklist")),
    ])
    q = f["order"]["question"]
    section("11", [
        P("im11_status", "지금 우리 사이에 맞는 조언", opener=True,
          slot=S("im11_status", f"관계 상태는 '{t['status'] or '알 수 없음'}', 알고 지낸 기간은 '{t['duration'] or '알 수 없음'}'이에요. 이 상황에서 할 일과 하지 말 일을 사주 근거와 함께 구체적으로 써 주세요.", FULL - 120)),
        P("im11_q", "질문에 대한 답", figure="question",
          slot=S("im11_q", (f"고객 질문: \"{q}\". 두 사람 사주 근거를 들어 솔직하고 구체적으로 답해 주세요." if q else
                             "질문이 없으니, 이 관계 상태의 사람이 가장 궁금해할 한 가지에 답해 주세요."), FULL - 200)),
        P("im11_more", "함께 생각해 볼 것", slot=S("im11_more", "질문과 이어지는 고민 2~3가지를 묻고 답해 주세요.", FULL, "qa")),
    ])
    section("12", [
        P("im12_key", "우리 궁합 핵심 정리", opener=True,
          slot=S("im12_key", "이 책에서 가장 중요한 세 가지(잘 맞는 점, 조심할 점, 앞으로의 시기)를 한 문장 요약(lead)과 함께 정리해 주세요.", 640, "lead")),
        P("im12_promise", "우리만의 약속", slot=S("im12_promise", "두 사람이 오래 함께하기 위해 정할 약속 10가지를 체크리스트로 써 주세요. 한 줄에 한 가지, 바로 할 수 있는 행동으로 씁니다.", 600, "checklist")),
        P("im12_plan", "좋은 시기와 조심할 시기에 할 일",
          slot=S("im12_plan", "앞으로 1년을 시기별로 나눠 함께 할 일과 피할 일을 정리해 주세요.", FULL, "plan")),
        P("im12_lucky", "함께하면 좋은 색·장소·데이트", figure="lucky",
          slot=S("im12_lucky", "두 사람의 용신 기운을 근거로 함께하면 좋은 색, 장소, 데이트, 여행지를 써 주세요.", HALF)),
        P("im12_worry", "두 사람의 걱정에 대한 답", span=2,
          slot=S("im12_worry", "이 관계에서 들기 쉬운 걱정(마음이 식으면, 크게 싸우면, 가족이 반대하면, 미래가 다르면)마다 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'를 함께 답해 주세요.", FULL * 2 - 60)),
        P("im12_last", "마지막 조언",
          slot=S("im12_last", f"{name}님에게 전하는 마지막 조언을 담백하게 써 주세요. 두 사람이 함께일 때 가장 빛나는 점을 사주 근거로 말해 주세요.", FULL - 120)),
    ])
    section("더보기", [P("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True)])
    return sections


def cross_sell_order(f: dict) -> list[str]:
    return ["reunion"] if f["theme"]["data"]["status"] == "헤어짐" else ["romance"]
