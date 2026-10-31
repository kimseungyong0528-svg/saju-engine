"""재회사주 리포트(50쪽 이상): 두 사람 사주 비교, 재회 신호, 연락 시기.

목차 원본: /mnt/project-files/plan/reunion-report-toc.md (2026-10-11, 인터뷰 주제 20가지 반영)
사이트 입력: 내 정보, 그 사람 정보(필수), 헤어진 기간(breakup), 있었던 일(question).
"""

from __future__ import annotations

from . import theme as T
from .outline import FULL, HALF, _slot
from ..pair import compare, pair_score

FINAL_SECTION = "12"

SECTIONS = [
    ("1", "내 사주 한눈에 보기", "두 사람의 사주표"),
    ("2", "한눈에 보는 우리의 재회", "재회 가능성, 시기, 방법"),
    ("3", "우리는 왜 헤어졌을까", "우리가 헤어진 진짜 이유"),
    ("4", "나도 몰랐던 나의 이별 패턴", "연애할 때 내가 반복하는 모습"),
    ("5", "그 사람은 어떤 사람이었을까", "성격, 연애 방식, 지금의 마음"),
    ("6", "우리 두 사람의 궁합", "끌림과 부딪힘"),
    ("7", "다시 만날 수 있을까", "재회의 가능성과 조건"),
    ("8", "연락은 언제, 어떻게", "나의 월별 재회운, 첫 연락 방법"),
    ("9", "다가갈까, 기다릴까", "나에게 맞는 선택"),
    ("10", "앞으로의 흐름", "연도별 재회운, 다시 만난 뒤"),
    ("11", "내가 남긴 질문에 대한 답", ""),
    ("12", "다시 시작하는 방법과 마지막 조언", ""),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

STATIC = {
    "rn_how_to_read": [
        "이 책은 두 사람의 태어난 날과 시간으로 계산한 사주를 나란히 놓고, 왜 헤어졌는지부터 다시 만날 수 있는지, 언제 어떻게 연락하면 좋은지까지 순서대로 풀어 놓은 책이에요.",
        "가장 궁금한 내용은 2장 '한눈에 보는 우리의 재회'에 먼저 모아 두었어요. 자세한 이유와 방법은 뒤의 장에서 하나씩 설명해요.",
        "사주는 그 사람의 마음을 대신 말해 주지 않아요. 두 사람이 타고난 성향과 지금 지나는 운의 흐름을 보여 줄 뿐이에요. 그래서 이 책은 '그 사람이 어떻게 할까'보다 '내가 언제, 무엇을 하면 좋을까'에 답하도록 썼어요.",
        "사주 용어는 쉬운 말과 생활 장면으로 자세히 풀었고, 쪽 끝 '기억할 한 줄'에 그 쪽의 핵심을 한 문장으로 정리했어요.",
    ],
    "rn_what_is_saju": [
        "사주(四柱)는 태어난 해, 달, 날, 시간의 네 기둥이에요. 기둥마다 위 글자(천간)와 아래 글자(지지)가 있어 모두 여덟 글자가 돼요.",
        "여덟 글자는 모두 오행(五行) 가운데 하나예요. 목(나무), 화(불), 토(흙), 금(쇠), 수(물)의 다섯 기운이 서로 돕고(상생) 누르며(상극) 균형을 이뤄요.",
        "태어난 날의 위 글자(일간)가 '나 자신'이고, 바로 아래 글자(일지)는 '배우자 자리'예요. 재회사주에서는 두 사람의 일간과 일지가 서로 손잡는지(합) 부딪히는지(충)를 가장 먼저 봐요.",
    ],
    "rn_pair": [
        "두 사람의 사주를 비교할 때는 네 가지를 봐요. 첫째, 나를 나타내는 글자(일간)끼리의 관계. 둘째, 배우자 자리(일지)끼리의 관계. 셋째, 서로 모자란 기운을 채워 주는지(오행 보완). 넷째, 두 사람의 여덟 글자 사이에 합과 충이 얼마나 있는지예요.",
    ],
}

_STATUS = {"3개월 이내예요": "3개월 이내", "3~6개월 정도예요": "3~6개월", "6개월~1년 정도예요": "6개월~1년",
           "1년 이상 지났어요": "1년 이상", "아직 헤어지지 않았어요": "아직 헤어지지 않음"}


def build(f: dict, result: dict, answers: dict, partner: dict) -> dict:
    o = f["partner"]
    me_day, o_day = T.day_of(f), T.day_of(o)
    cmp = compare(T.fourpillars(result), T.fourpillars(partner))
    group = "재성" if f["person"]["sex"] == "male" else "관성"

    def mark(x: dict) -> dict:
        rel_o = T.against(x["ganzhi"], o_day["stem"], o_day["branch"])
        star = T.has(x, group)
        my_hap = T.rel(x, "일주", T.HAP)
        their_hap = any(k in T.HAP for k in rel_o)
        stem_hap = "천간합" in rel_o
        clash = T.rel(x, "일주", T.CLASH)
        their_clash = "충" in rel_o
        signs = [s for s, on in (("배우자 별", star), ("내 배우자 자리와 합", my_hap), ("그 사람 일지와 합", their_hap),
                                 ("그 사람 일간과 합", stem_hap), ("내 배우자 자리와 충", clash), ("그 사람 일지와 충", their_clash)) if on]
        score = x["score"] + 8 * star + 8 * my_hap + 10 * their_hap + 8 * stem_hap - 8 * clash - 6 * their_clash
        return {"t_score": T.clamp(score), "t_signs": signs, "t_contact": their_hap or stem_hap or my_hap, "t_their": their_hap or stem_hap}

    years, _, periods = T.marked(f, mark)
    # 사장님 2026-10-30: 재회는 몇 달 안의 결과로, 길어야 2~3년. 결제 전 화면도 리포트도 앞으로 24개월 달마다 보고, 해는 3년만.
    years = years[:3]
    months = [dict(m, **mark(m)) for m in f["screen_months"]]
    T.reveal_fix(result, "reunion", months)   # 제1조항: 결제 전 화면의 24개월 지도와 같은 표시·방향
    for m in months:
        if m.get("t_their") and not m["r_good"] and not m["r_bad"]:
            m["t_score"] = max(m["t_score"], 55)   # 그 사람과 합이 드는 보통 달은 보통 달 안에서 높은 쪽(손님 테스트 3차: 합이 드는 달이 41점)
    harmony, tension = cmp["cross_relations"]["harmony"], cmp["cross_relations"]["tension"]
    strong = sum(1 for m in months[:12] if m["t_score"] >= 70)
    level_pts = (harmony - tension) + 2 * strong + (2 if cmp["spouse_palace"]["tone"] == "조화" else -2 if cmp["spouse_palace"]["tone"] == "긴장" else 0)
    # 제1조항: 결제 전 화면 STEP 3 제목(좋은 운을 타고났습니다 / 미리 알면 대비할 수 있습니다)과 반대로 쓰지 않는다
    from ..taster import area_view
    sign = area_view(T.fourpillars(result), f["person"]["name"], result["person"].get("sex", ""), "reunion")["sign"]
    level = ("강한 편" if level_pts >= 4 else "보통") if sign > 0 else ("약한 편" if level_pts < 0 else "보통")
    # '가장 좋은 달'은 24개월 가운데 점수도 가장 높다(표에서 '다시 이어짐' 달보다 낮게 나오지 않게)
    peak = max(m["t_score"] for m in months)
    for m in months:
        if "가장 좋은 달" in m["r_good"]:
            m["t_score"] = peak
    # 화면에서 '가장 좋은 달'(배우자 자리와 육합)로 본 달을 먼저 알리고, 연락하기 좋은 달은 화면의 좋은 표시 달을 모두 적는다
    top = [T.ym(m) for m in months if "가장 좋은 달" in m["r_good"]]
    best_months = [T.ym(m) for m in months if m["r_good"]] or T.best(months, 3, T.ym)
    first_best = next(i for i, m in enumerate(months) if T.ym(m) in best_months)
    approach = "먼저 다가가기" if T.count(f, "식상") >= 1 and first_best <= 3 else "기다리며 준비하기"
    o_now = o["sewoon"][0]
    o_group = "재성" if o["person"]["sex"] == "male" else "관성"
    o_years = [{"year": s["year"], "ganzhi": s["ganzhi"], "score": s["score"], "인연 별": T.has(s, o_group)} for s in T.screen_years(o)]

    screen = T.screen_score(f, result, "reunion")
    data = {
        "screen_score": screen,
        "breakup": _STATUS.get(answers.get("breakup", ""), answers.get("breakup", "")),
        "compare": cmp, "pair_score": pair_score(T.fourpillars(result), T.fourpillars(partner)),   # 결제 전 화면의 '두 사람 궁합 점수'와 같다
        "level": level, "approach": approach,
        "most_months": top,
        "best_years": [y for y in T.best(years, 1, lambda y: y["year"])],
        "best_months": best_months, "careful_months": T.bad_rows(months, 24, T.ym) or T.worst(months, 3, T.ym),   # 화면의 '엇갈림' 달
        "partner_now": {"year": o_now["year"], "ganzhi": o_now["ganzhi"], "score": o_now["score"],
                        "인연 별이 드는 해": T.has(o_now, o_group)},
        "partner_years": o_years,
    }
    return {
        "label": "재회 재료",
        "data": data,
        "digest": {**{k: v for k, v in data.items()}, "그 사람 사주": T.chart_brief(o), **T.digest_rows(years, months, T.near(f, periods, 30)),
                   "점수 설명": "t_score는 재회 점수: 운의 흐름 점수에 배우자 별, 두 사람 배우자 자리·일간과의 합을 더하고 충을 뺀 값"},
        "years": years, "months": months, "periods": periods,
    }


STYLE = T.style("재회사주", """
[재회사주 규칙]
- 독자는 헤어진 사람을 다시 만나고 싶거나, 연락할지 고민하는 사람입니다. 마음이 급하고 불안하다는 것을 알고, 차분하고 솔직하게 씁니다.
- 근거는 '재회 재료'(두 사람 비교 compare, 재회 점수 t_score와 표시 t_signs, 좋은 달·조심할 달, 그 사람 사주)를 먼저 씁니다.
- 상대방은 "그 사람"이라고 부르고, 그 사람의 사주 이름(이름)도 쓸 수 있습니다.
- 그 사람의 지금 마음, 새 연인 여부는 단정하지 않습니다. "그 사람 사주로 보면 ~하기 쉬운 사람이에요"처럼 성향과 운의 흐름으로만 씁니다.
- 재회를 장담하지 않고, 재회가 어려운 경우에도 나에게 좋은 선택이 무엇인지 함께 씁니다.
- 연락을 반복하거나 상대를 압박하는 행동(집 앞 찾아가기, 여러 번 연락하기)은 권하지 않습니다.
- 헤어진 기간(breakup)과 있었던 일(질문)에 맞춰 씁니다. 비어 있으면 경우를 나눠 씁니다.
""")


def build_outline(f: dict) -> list[dict]:
    t = f["theme"]["data"]
    name, oname = f["person"]["name"], f["partner"]["person"]["name"] or "그 사람"
    cmp = t["compare"]
    sections: list[dict] = []

    def section(no: str, pages: list[dict]) -> None:
        title, subtitle = next((a, b) for n, a, b in SECTIONS if n == no)
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": []})

    P, S = T.tpage, _slot
    th = f["theme"]
    section("1", [
        P("cover", "표지", figure="cover"),
        P("toc", "목차", figure="toc"),
        P("how_to_read", "이 책을 읽는 방법", static="rn_how_to_read", opener=True),
        P("rn_saju", "사주와 오행 짧게 알기", static="rn_what_is_saju", figure="element_cycle"),
        P("chart", "나의 사주표", figure="pillars",
          slot=S("chart", f"{name} 님의 여덟 글자와 일간이 연애·이별에서 어떤 성향으로 나타나는지 쉽게 설명해 주세요.", HALF)),
        P("rn_pair", "두 사람의 사주표", static="rn_pair", figure="pair_pillars",
          slot=S("rn_pair", f"두 사람의 일간({cmp['day_master']['me']}·{cmp['day_master']['other']})과 일지({cmp['spouse_palace']['me']}·{cmp['spouse_palace']['other']})를 짧게 소개해 주세요.", HALF - 220)),
    ])
    section("2", [
        P("rn_glance", "한눈에 보는 우리의 재회", figure="kv", opener=True, rows=[
            T.screen_row(t["screen_score"], t.get("seen", True)),
            ["결제 전에 보신 두 사람 궁합 점수" if t.get("seen", True) else "두 사람 궁합 점수", f"{t['pair_score']}점 ({oname} 님 사주와 함께 본 점수)"],
            ["재회 신호", t["level"]],
            ["다시 이어지기 가장 좋은 달", ", ".join(t["most_months"]) or "앞으로 24개월 안에는 뚜렷하지 않아요"],
            ["연락하기 좋은 달", ", ".join(t["best_months"])],
            ["피할 달", ", ".join(t["careful_months"]) or "크게 부딪히는 달은 없어요"],
            ["나에게 맞는 방법", t["approach"]],
            ["두 사람 배우자 자리", f"{cmp['spouse_palace']['me']}·{cmp['spouse_palace']['other']} ({cmp['spouse_palace']['tone']})"],
        ], slot=S("rn_glance", "표의 재회 신호, 좋은 달, 나에게 맞는 방법을 이어서 짧게 소개하고, 자세한 내용은 뒤 장에서 다룬다고 안내해 주세요.", HALF - 60)),
    ])
    section("3", [
        P("rn3_open", "두 사람이 부딪힌 지점", figure="kv", opener=True, rows=[
            ["일간끼리", f"{cmp['day_master']['me']}·{cmp['day_master']['other']} · {cmp['day_master']['element_relation']}"],
            ["일지끼리", f"{cmp['spouse_palace']['me']}·{cmp['spouse_palace']['other']} · {', '.join(cmp['spouse_palace']['relations']) or '특별한 합충 없음'}"],
            ["띠끼리", f"{cmp['zodiac']['me']}·{cmp['zodiac']['other']} · {', '.join(cmp['zodiac']['relations']) or '특별한 합충 없음'}"],
            ["합 · 충 개수", f"서로 손잡는 관계 {cmp['cross_relations']['harmony']}개 · 부딪히는 관계 {cmp['cross_relations']['tension']}개"],
        ], slot=S("rn3_open", "표를 근거로 두 사람이 어디서 부딪혔는지 핵심을 한 문장(lead)으로 말하고 설명해 주세요.", 420, "lead")),
        P("rn3_diff", "성격 차이가 만든 장면",
          slot=S("rn3_diff", "두 사람의 일간 오행과 십신 구성 차이가 연락, 약속, 표현 방식에서 어떤 엇갈림을 만들었는지 장면으로 써 주세요.")),
        P("rn3_fight", "다툼이 반복된 이유",
          slot=S("rn3_fight", "일지·띠의 합충과 두 사람의 넘치는 기운을 근거로 다툼이 반복된 이유와 그때 각자의 반응을 장면으로 쓰고, 다음에 다르게 할 방법을 붙여 주세요.")),
        P("rn3_when", "헤어짐이 온 흐름",
          slot=S("rn3_when", f"헤어진 기간({t['breakup'] or '모름'})과 최근 해·대운의 재회 점수와 표시(충 등)를 근거로 헤어짐이 온 운의 흐름을 설명하고, 그것이 누구의 잘못만은 아니라는 점을 근거와 함께 써 주세요.")),
    ])
    section("4", [
        P("rn4_open", "연애할 때 나의 모습", figure="opener", opener=True,
          slot=S("rn4_open", "연애할 때 내 모습을 한 문장으로 요약(lead)하고 사주 근거와 함께 설명해 주세요.", 600, "lead")),
        P("rn4_pattern", "내가 반복하는 이별 패턴",
          slot=S("rn4_pattern", "배우자 별의 개수·자리, 식상·비겁 구성, 배우자 자리의 합충을 근거로 이별이 반복되는 패턴(시작, 서운함, 이별의 순간)을 장면으로 써 주세요.")),
        P("rn4_fix", "패턴을 끊는 방법",
          slot=S("rn4_fix", "앞의 패턴마다 다음 연애(또는 재회)에서 바로 쓸 수 있는 보완법을 써 주세요. 말투, 연락 간격, 서운함을 말하는 법을 구체적으로 씁니다.")),
    ])
    o = f["partner"]
    section("5", [
        P("rn5_open", "그 사람의 사주", figure="kv", opener=True, rows=[
            ["나타내는 글자", f"{o['day_master']['stem']}({o['day_master']['hanja']}) · {o['day_master']['image']}"],
            ["강한 기운", ", ".join(e["name"] for e in o["elements"] if e["status"] == "많음") or "고른 편"],
            ["약한 기운", ", ".join(e["name"] for e in o["elements"] if e["status"] == "부족") or "고른 편"],
            ["사주의 틀", f"{o['strength']['label']} · {o['gyeokguk']['name']}"],
            ["나에게 그 사람은", f"{cmp['day_master']['other_as_my_ten_god']}의 기운"],
        ], slot=S("rn5_open", f"{oname} 님의 사주를 쉽게 소개하고, {name} 님에게 그 사람이 어떤 기운인지(other_as_my_ten_god) 설명해 주세요.", HALF - 60)),
        P("rn5_person", "그 사람의 성격",
          slot=S("rn5_person", "그 사람의 일간·강한 기운·십신 구성으로 성격의 장점과 약점을 장면으로 써 주세요. 단정하지 않고 '~하기 쉬운 사람'으로 씁니다.")),
        P("rn5_love", "그 사람의 연애 방식",
          slot=S("rn5_love", "그 사람이 연애할 때 표현하는 방식, 서운할 때 반응, 화해하는 방식을 사주 근거로 써 주세요.")),
        P("rn5_after", "그 사람이 이별을 정리하는 방식",
          slot=S("rn5_after", "그 사람의 사주 성향으로 이별 뒤 감정을 정리하는 방식(바로 끊는지, 시간이 걸리는지, 먼저 연락하는 편인지)을 쓰고, 그래서 내가 조심할 점을 써 주세요.")),
        P("rn5_now", "지금 그 사람이 지나는 운",
          slot=S("rn5_now", f"그 사람의 올해({t['partner_now']['year']}년 {t['partner_now']['ganzhi']}) 운의 흐름 점수와 인연 별 여부를 근거로 그 사람이 지금 어떤 시기를 지나는지 써 주세요. 새 연인 여부는 단정하지 않습니다.")),
    ])
    elem_rows = [[e["name"], f"{e['pct']}%", f"{oe['pct']}%"] for e, oe in zip(f["elements"], o["elements"])]
    section("6", [
        P("rn6_open", "두 사람의 오행 비교", figure="grid", opener=True,
          grid={"head": ["오행", name, oname], "rows": elem_rows, "hl": []},
          slot=S("rn6_open", "오행 표를 근거로 두 사람이 서로 채워 주는 기운과 둘 다 많은(또는 둘 다 없는) 기운을 설명해 주세요.", HALF - 40)),
        P("rn6_pull", "서로 끌렸던 이유",
          slot=S("rn6_pull", "오행 보완, 일간 관계, 합 관계를 근거로 두 사람이 처음에 끌린 이유를 장면으로 써 주세요.")),
        P("rn6_clash", "서로 힘들었던 이유",
          slot=S("rn6_clash", "충·형 관계와 둘 다 넘치는 기운을 근거로 함께 있을 때 힘들었던 지점을 장면으로 쓰고 각각 푸는 방법을 붙여 주세요.")),
        P("rn6_score", "우리 궁합 정리",
          slot=S("rn6_score", "두 사람 궁합의 좋은 점 3가지와 조심할 점 3가지를 근거와 함께 정리해 주세요.", FULL, "bullets")),
    ])
    section("7", [
        P("rn7_open", "재회 신호 읽기", figure="kv", opener=True, rows=[
            ["재회 신호", t["level"]],
            ["좋은 달 수", f"앞으로 24개월 가운데 좋은 표시가 붙은 달 {sum(1 for m in th['months'] if m.get('r_good'))}달"],   # 화면 지도와 같은 수(손님 테스트 3차)
            ["그 사람과 합이 드는 달", ", ".join(T.ym(m) for m in th["months"] if m.get("t_their") and not m.get("r_bad")) or "앞으로 24개월 안에는 없어요"],
        ], slot=S("rn7_open", "재회 신호가 왜 이 정도인지 근거를 들어 솔직하게 설명해 주세요.", HALF)),
        P("rn7_chance", "재회가 가능한 이유와 어려운 이유",
          slot=S("rn7_chance", "두 사람 비교와 다가오는 운을 근거로 재회가 가능한 이유와 어려운 이유를 나란히 쓰고, 어떤 경우에 가능성이 커지는지 써 주세요.")),
        P("rn7_cond", "다시 만나기 위한 조건",
          slot=S("rn7_cond", "재회하려면 먼저 바뀌어야 할 것(내 쪽 행동, 대화 방식, 시기)을 3~4가지로 구체적으로 써 주세요.")),
        P("rn7_open_heart", "그 사람의 마음이 열리기 쉬운 때",
          slot=S("rn7_open_heart", "그 사람 일지·일간과 합이 드는 달과 그 사람의 올해 운을 근거로 대화가 부드러워지기 쉬운 때를 쓰고, 그때 할 일을 써 주세요.")),
    ])
    section("8", [
        P("rn8_months", "앞으로 24개월 월별 재회운", figure="grid", opener=True, span=3, grid=T.month_grid(th["months"], "재회 점수"),
          note="표시: 결제 전에 보신 '가장 좋은 달'·'다시 이어짐'·'엇갈림'과 같은 달이에요.",
          slot=S("rn8_months", "결제 전 화면에서 고객이 본 '가장 좋은 달'·'다시 이어짐'·'엇갈림' 달을 표의 이름 그대로 하나도 빠짐없이 짚어 주세요. "
                     "좋은 달마다 며칠 무렵부터인지, 어떤 연락 수단(문자·전화·SNS·직접 만남)이 맞는지, 보낼 첫마디 예시, 어떤 타이밍과 상황(요일·시간대·그 사람의 상황)에 연락하는지를 쓰고, "
                     "엇갈림 달마다 피할 말, 멈출 연락 수단, 다시 연락해도 되는 다음 달을 써 주세요.", FULL * 3 - 1640)),
        P("rn8_when", "연락하기 좋은 시기, 피할 때",
          slot=S("rn8_when", "좋은 달과 피할 달을 근거와 함께 다시 정리하고, 하루 중 연락하기 좋은 상황(바쁜 때를 피하는 법 등)도 써 주세요.")),
        P("rn8_first", "첫 연락은 이렇게",
          slot=S("rn8_first", "두 사람 성향에 맞는 첫 연락의 방식(메시지 길이, 말투, 피할 말)을 쓰고, 보낼 수 있는 첫 문장 예시 3개를 써 주세요.")),
        P("rn8_talk", "다시 만났을 때 대화법",
          slot=S("rn8_talk", "다시 만나 이야기할 때 꺼낼 말과 피할 말, 지난 다툼을 이야기하는 순서를 두 사람 사주 근거로 써 주세요.")),
        P("rn8_sns", "SNS와 우연한 만남",
          slot=S("rn8_sns", "SNS 보기, 상태 메시지, 우연히 마주쳤을 때 어떻게 하면 좋은지 이 사주에 맞춰 써 주세요.")),
    ])
    section("9", [
        P("rn9_open", "나에게 맞는 선택", figure="kv", opener=True, rows=[
            ["나에게 맞는 방법", t["approach"]], ["가까운 좋은 달", t["best_months"][0]],
            ["표현의 힘(식상)", f"{T.count(f, '식상')}개"], ["기다리는 힘(인성)", f"{T.count(f, '인성')}개"],
        ], slot=S("rn9_open", "표를 근거로 왜 이 방법이 나에게 맞는지 설명해 주세요.", HALF)),
        P("rn9_go", "다가간다면 이렇게",
          slot=S("rn9_go", "먼저 다가갈 때의 순서(준비, 첫 연락, 만남, 관계 다시 정하기)를 시기와 함께 구체적으로 써 주세요.")),
        P("rn9_wait", "기다린다면 이렇게",
          slot=S("rn9_wait", "기다릴 때 하면 좋은 일과 하지 말아야 할 일을 쓰고, 기다리는 동안 마음을 다스리는 방법을 써 주세요.")),
        P("rn9_how_long", "얼마나 기다리면 될까",
          slot=S("rn9_how_long", "앞으로 24개월의 '가장 좋은 달'과 좋은 달을 근거로 기다리는 기간의 기준(몇 달)을 쓰고, 그때까지 다시 확인할 신호를 써 주세요.")),
        P("rn9_stop", "놓아야 할 때의 신호",
          slot=S("rn9_stop", "재회보다 나를 지키는 선택이 맞는 신호(행동으로 보이는 것)와 그때 마음을 정리하는 방법을 겁주지 않고 써 주세요.")),
    ])
    section("10", [
        P("rn10_years", "앞으로 3년 재회운", figure="grid", opener=True, span=2, grid=T.year_grid(th["years"], t["best_years"], "재회 점수"),
          slot=S("rn10_years", "표의 3년을 한 해씩 문단으로 써 주세요(그해 표시 근거, 두 사람 관계의 흐름, 할 일). 먼 해의 재회를 약속하지 않습니다.", FULL * 2 - 460)),
        P("rn10_graph", "나이별 인연 흐름", figure="theme_graph", note="대운(10년)마다 두 사람의 인연 글자가 들어오면 점수가 올라가요.",
          slot=S("rn10_graph", "그래프에서 인연이 강하게 들어오는 대운과 조용한 대운을 나이로 짚어 주세요.", HALF - 40)),
        P("rn10_after", "다시 만나면 오래 갈까",
          slot=S("rn10_after", "두 사람 배우자 자리 관계와 궁합을 근거로 다시 만났을 때 관계가 오래 가는 조건과 결혼까지 이어질 때 확인할 점을 써 주세요.")),
        P("rn10_again", "같은 이유로 또 헤어지지 않으려면",
          slot=S("rn10_again", "3장에서 본 부딪힘이 다시 생기지 않도록 두 사람이 정할 약속 5가지를 이유와 함께 써 주세요.", FULL, "checklist")),
    ])
    q = f["order"]["question"]
    section("11", [
        P("rn11_q", "질문에 대한 답", figure="question", opener=True,
          slot=S("rn11_q", (f"고객이 남긴 이야기: \"{q}\". 두 사람 사주 근거를 들어 솔직하고 구체적으로 답해 주세요." if q else
                             "질문이 없으니, 재회를 고민하는 사람이 가장 궁금해할 '그 사람이 다시 연락할까'에 답해 주세요."), FULL - 200)),
        P("rn11_more", "함께 생각해 볼 것",
          slot=S("rn11_more", "질문과 이어지는 고민 2~3가지를 묻고 답해 주세요.", FULL, "qa")),
    ])
    section("12", [
        P("rn12_key", "재회 사주 핵심 정리", opener=True,
          slot=S("rn12_key", "이 책에서 가장 중요한 세 가지(헤어진 이유, 재회 신호와 시기, 내가 바꿀 것)를 한 문장 요약(lead)과 함께 정리해 주세요.", 640, "lead")),
        P("rn12_lucky", "마음을 돕는 색·장소·행동", figure="lucky",
          slot=S("rn12_lucky", "용신 기운을 근거로 연락 전후 마음을 안정시키는 색, 장소, 행동을 써 주세요.", HALF)),
        P("rn12_two_roads", "다시 만난다면, 정리한다면",
          slot=S("rn12_two_roads", "재회하는 경우와 정리하는 경우 각각 앞으로 6개월 동안 할 일을 시기 순서로 써 주세요. 6개월 안에 '가장 좋은 달'이 없으면 가장 좋은 달까지 이어서 씁니다. 달을 적을 때는 24개월 표의 표시와 같은 방향으로만 씁니다('가장 좋은 달'·'다시 이어짐' 달은 연락과 만남의 달, '엇갈림' 달은 연락을 멈추는 달).", 680, "plan")),
        P("rn12_todo", "오늘부터 할 일 목록", figure="habits",
          slot=S("rn12_todo", "오늘부터 실천할 일 10가지를 체크리스트로 써 주세요. 한 줄에 한 가지, 바로 할 수 있는 행동으로 씁니다.", 560, "checklist")),
        P("rn12_heart", "불안한 마음을 다루는 법", span=2,
          slot=S("rn12_heart", "재회를 기다리며 드는 걱정(연락이 안 오면, 새 사람이 생겼으면, 내가 잘못했으면)마다 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'를 함께 답해 주세요.", FULL * 2 - 60)),
        P("rn12_last", "마지막 조언",
          slot=S("rn12_last", f"{name} 님에게 전하는 마지막 조언을 담백하게 써 주세요. 결과와 상관없이 {name} 님이 사랑받을 이유를 사주 근거로 말해 주고, 지금 할 수 있는 일에 집중하게 해 주세요.", FULL - 120)),
    ])
    section("더보기", [P("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True)])
    return sections


def cross_sell_order(f: dict) -> list[str]:
    return ["intimate", "romance"]
