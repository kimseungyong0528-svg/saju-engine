"""연애사주 리포트(약 50쪽): 연애 재료, 목차, 글쓰기 규칙.

목차 원본: /mnt/project-files/plan/romance-report-toc.md (2026-10-11 확정, 인터뷰 주제 20가지 반영)
평생사주와 같은 엔진·도안·글쓰기 방식을 쓰고, 이 파일은 연애사주에만 필요한 것만 더한다.
평생사주 모듈(outline.py 등)의 결과는 바꾸지 않는다.
"""

from __future__ import annotations

from . import knowledge as K
from .facts import PILLAR_LABEL
from .outline import FULL, HALF, _slot, page
from .writer import STYLE_RULES

FINAL_SECTION = "10"

SECTIONS = [
    ("1", "내 사주 한눈에 보기", "나의 사주표와 연애에서 보이는 운명"),
    ("2", "한눈에 보는 나의 인연", "운명의 시기, 사람, 만나는 곳"),
    ("3", "연애할 때 나는 어떤 사람일까", "나의 첫인상, 매력, 이성이 보는 내 모습"),
    ("4", "내 연애는 왜 엇갈릴까", "나도 몰랐던 나의 연애 패턴"),
    ("5", "다음 연인은 어떤 사람일까", "배우자 자리로 보는 그 사람"),
    ("6", "잘 맞는 사람과 조심할 사람", "사주로 보는 궁합"),
    ("7", "다음 연인은 언제 올까", "올해, 5년, 12개월"),
    ("8", "짝사랑, 고백, 지난 인연", ""),
    ("9", "결혼운", "나의 운명의 상대에 대한 모든 것"),
    ("10", "인연을 찾는 방법과 마지막 조언", ""),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

STATIC = {
    "r_how_to_read": [
        "이 책은 태어난 날과 시간으로 계산한 사주를 바탕으로, 연애할 때의 내 모습부터 다음 인연이 오는 시기, 그 사람의 모습, 결혼운까지 순서대로 풀어 놓은 책이에요.",
        "가장 궁금한 내용은 7쪽 '한눈에 보는 나의 인연'에 먼저 모아 두었어요. 자세한 이유와 방법은 뒤의 장에서 하나씩 설명해요.",
        "어려운 사주 용어가 나오면 바로 옆 괄호 안에 쉬운 말로 풀어 두었어요.",
        "사주는 정해진 운명이 아니라 내가 타고난 기운과 흐름을 알려 주는 지도예요. 인연이 들어오는 때를 알고 준비하면, 같은 기회도 더 잘 잡을 수 있어요.",
    ],
    "r_what_is_saju": [
        "사주(四柱)는 태어난 해, 달, 날, 시간의 네 기둥이에요. 기둥마다 위 글자(천간)와 아래 글자(지지)가 있어 모두 여덟 글자가 돼요.",
        "여덟 글자는 모두 오행(五行) 가운데 하나예요. 목(나무), 화(불), 토(흙), 금(쇠), 수(물)의 다섯 기운이 서로 돕고(상생) 누르며(상극) 균형을 이뤄요.",
        "태어난 날의 위 글자(일간)가 '나 자신'이에요. 연애사주에서는 나와 다른 글자의 관계로 이성을 대하는 모습을 보고, 운에서 들어오는 글자로 인연이 오는 때를 봐요.",
    ],
    "r_spouse_seat": [
        "태어난 날 기둥의 아래 글자를 '일지(日支)'라고 해요. 나(일간) 바로 아래에 붙어 있는 글자라서, 사주에서는 이 자리를 '배우자 자리'로 봐요.",
        "일지에 어떤 글자가 있는지, 그 글자가 다른 글자와 손잡는지(합) 부딪히는지(충)를 보면 오래 함께할 사람의 성향과 함께 사는 모습을 짐작할 수 있어요.",
    ],
}

# 도화(桃花): 띠·일지의 삼합 무리마다 정해진 글자
_PEACH = {"인": "묘", "오": "묘", "술": "묘", "신": "유", "자": "유", "진": "유",
          "사": "오", "유": "오", "축": "오", "해": "자", "묘": "자", "미": "자"}

# 배우자 별이 놓인 자리로 보는 만남의 경로와 나이 차이 경향(고전의 궁위론, 참고용)
_SEAT_HINT = {
    "년주": ("집안·고향·어릴 적 인연이나 먼 곳에서 온 사람", "나보다 나이가 많은 사람과 인연이 닿기 쉬운 경향"),
    "월주": ("직장·학교·모임처럼 매일 오가는 사회생활 속 사람", "나이가 비슷하거나 조금 많은 사람과 인연이 닿기 쉬운 경향"),
    "일주": ("내 생활권 가까이에서 자연스럽게 알게 된 사람", "나이 차이가 크지 않은 사람과 인연이 닿기 쉬운 경향"),
    "시주": ("취미·공부·후배 관계처럼 나중에 시작한 활동에서 만난 사람", "나보다 나이가 적은 사람과 인연이 닿기 쉬운 경향"),
}

STATUS_TEXT = {
    "썸을 타고 있어요": "썸", "연애 중이에요": "연애 중", "지금은 솔로예요": "솔로",
    "최근에 헤어졌어요": "최근 이별", "오랫동안 혼자였어요": "오래 혼자", "짝사랑 중이에요": "짝사랑",
}


def _spouse(sex: str) -> tuple[str, set[str]]:
    return ("재성", {"편재", "정재"}) if sex == "male" else ("관성", {"편관", "정관"})


def _day_rel(relations: list[dict]) -> tuple[bool, bool]:
    """운의 글자가 배우자 자리(일지)와 합하는지, 부딪히는지."""
    hap = any(r.get("with") == "일주" and r.get("level") == "지지" and K.relation_kind(r["type"]) in ("육합", "삼합", "반합")
              for r in relations)
    clash = any(r.get("with") == "일주" and r.get("level") == "지지" and K.relation_kind(r["type"]) == "충" for r in relations)
    return hap, clash


def _love_mark(x: dict, gods: set[str], peach: set[str], raw: list[dict]) -> dict:
    star = x["stem_ten_god"] in gods or x["branch_ten_god"] in gods
    hap, clash = _day_rel(raw)
    peach_in = x["ganzhi"][1] in peach
    # 인연 점수(참고용): 운의 흐름 점수에 배우자 별, 배우자 자리와의 합, 도화를 더하고 배우자 자리와의 충을 뺀다
    score = x["score"] + 10 * star + 8 * hap + 6 * peach_in - 8 * clash
    signs = [s for s, on in (("배우자 별", star), ("배우자 자리와 합", hap), ("도화", peach_in), ("배우자 자리와 충", clash)) if on]
    return {"love_star": star, "love_hap": hap, "love_peach": peach_in, "love_clash": clash,
            "love_score": max(20, min(95, score)), "love_signs": signs}


def build_romance(f: dict, result: dict, order) -> dict:
    """facts에 연애사주 재료(f['romance'])를 더한다. 값은 모두 계산으로 정해진다."""
    an = result["variants"][0]["analysis"]
    sex = f["person"]["sex"]
    group, gods = _spouse(sex)
    day = next(p for p in f["pillars"] if p["pillar"] == "일주")
    # 배우자 별이 놓인 자리(천간·지지·숨은 글자)
    seats = []
    for p in f["pillars"]:
        if p.get("unknown"):
            continue
        where = [w for w, g in (("천간", p["stem_ten_god"]), ("지지", p["branch_ten_god"])) if g in gods]
        where += [f"숨은 글자 {h['stem']}" for h in p["hidden_stems"] if h["ten_god"] in gods and h["ten_god"] != p["branch_ten_god"]]
        if where:
            seats.append({"pillar": p["pillar"], "label": p["label"], "where": where,
                          "route": _SEAT_HINT[p["pillar"]][0], "age_gap": _SEAT_HINT[p["pillar"]][1]})
    visible = [s for s in seats if any(not w.startswith("숨은") for w in s["where"])]
    main_seat = (visible or seats or [None])[0]

    peach = {_PEACH[an["pillars"][0]["branch"]], _PEACH[day["branch"]]}
    years = [dict(s, **_love_mark(s, gods, peach, s["relations"])) for s in f["sewoon"][:5]]
    months = [dict(m, **_love_mark(m, gods, peach, m["relations"])) for m in f["months"]]
    periods = [dict(p, **_love_mark(p, gods, peach, p["relations"])) for p in f["daewoon"]["periods"]]
    marriage = [p for p in periods if p["state"] != "지난" and (p["love_star"] or p["love_hap"])]

    natal_day = [r for r in f["relations"] if "일주" in r.get("between", [])]
    status = STATUS_TEXT.get(order.relationship, order.relationship)
    return {
        "spouse_group": group, "spouse_gods": sorted(gods),
        "spouse_count": next(g["n"] for g in f["ten_god_groups"] if g["group"] == group),
        "spouse_seats": seats, "main_seat": main_seat,
        "day_branch": {"branch": day.get("branch"), "hanja": day.get("branch_hanja"), "element": day.get("branch_element"),
                       "ten_god": day.get("branch_ten_god"), "hidden": day.get("hidden_text"), "stage": day.get("twelve_stage"),
                       "animal": day.get("animal")},
        "day_branch_relations": [{"type": r["type"], "kind": r["kind"], "with": PILLAR_LABEL[next(b for b in r["between"] if b != "일주")],
                                  "text": r["text"]} for r in natal_day],
        "peach": [s for s in f["shinsal_names"] if s in ("도화살", "홍염살")],
        "peach_branches": sorted(peach),
        "years": years, "months": months, "periods": periods,
        "best_years": sorted(y["year"] for y in sorted(years, key=lambda y: -y["love_score"])[:2]),
        "best_months": [f"{m['year']}년 {m['month']}월" for m in months if m in sorted(months, key=lambda m: -m["love_score"])[:3]],
        "careful_months": [f"{m['year']}년 {m['month']}월" for m in months if m["love_clash"] or m["love_score"] <= 35][:3],
        "marriage_periods": [{"age_text": p["age_text"], "years_text": p["years_text"], "ganzhi": p["ganzhi"],
                              "signs": p["love_signs"]} for p in marriage[:3]],
        "status": status, "experience": getattr(order, "experience", "") or "",
    }


ROMANCE_STYLE = STYLE_RULES.replace("사주 리포트 '평생사주'", "사주 리포트 '연애사주'").replace(
    "- 물상 그림은 한 장에 한두 번만 씁니다. 고전 이름(자평진전, 적천수)은 2장의 '사주의 뼈대와 흐름' 쪽에서만 소개합니다.",
    "- 물상 그림은 한 장에 한두 번만 씁니다. 고전 이름(자평진전, 적천수)은 쓰지 않습니다.") + """
[연애사주 규칙]
- 독자는 다음 인연을 기다리며 연애에 관심이 많은 사람입니다. 설레는 마음을 존중하되, 비유 대신 구체적인 장면으로 씁니다.
- 근거는 '연애 재료'(배우자 별, 배우자 자리=일지, 도화, 연도·달별 인연 표시와 인연 점수)를 먼저 씁니다.
- 상대는 성별을 정하지 않고 "그 사람"이라고 부릅니다.
- 그 사람의 직업, 나이 차이, 외모 분위기는 '경향'으로만 씁니다. "~일 가능성이 높아요", "~한 사람과 인연이 닿기 쉬워요"처럼 씁니다.
- 고객이 고른 연애 상태(status)와 연애 경험(experience)에 맞춰 씁니다. 비어 있으면 경우를 나눠 씁니다.
- 특정 사람과 잘될지, 상대의 마음은 이 책에서 단정하지 않습니다. 상대 생일을 알면 '깊은 궁합'에서 볼 수 있다고 안내할 수 있습니다.
"""


def build_outline(f: dict) -> list[dict]:
    """연애사주 목차(약 50쪽)."""
    r = f["romance"]
    name = f["person"]["name"]
    dm = f["day_master"]
    sections: list[dict] = []

    def section(no: str, pages: list[dict], terms: list[str] | None = None) -> None:
        title, subtitle = next((t, s) for n, t, s in SECTIONS if n == no)
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": terms or []})

    status = r["status"] or "알 수 없음"

    # 1. 내 사주 한눈에 보기 (1~6쪽)
    section("1", [
        page("cover", "표지", figure="cover"),
        page("toc", "목차", figure="toc"),
        page("how_to_read", "이 책을 읽는 방법", static="r_how_to_read", opener=True),
        page("r_saju", "사주와 오행 짧게 알기", static="r_what_is_saju", figure="element_cycle"),
        page("chart", "나의 사주표", figure="pillars",
             slot=_slot("chart", f"{name}님의 여덟 글자를 소개하고, 일간 {dm['stem']}({dm['element_name']})이 연애할 때 어떤 성향으로 나타나는지 쉽게 설명해 주세요.", HALF)),
        page("r_letters", "연애에서 보는 글자", figure="love_letters",
             slot=_slot("r_letters", f"표의 배우자 자리(일지), 배우자 별({r['spouse_group']}), 도화가 각각 무엇이고 {name}님에게 어떻게 있는지 설명해 주세요.", HALF)),
    ])

    # 2. 한눈에 보는 나의 인연 (7쪽)
    section("2", [
        page("r_glance", "한눈에 보는 나의 인연", figure="love_glance", opener=True,
             slot=_slot("r_glance", "표에 정리된 인연이 오는 시기, 그 사람의 모습, 만나기 쉬운 곳을 설레게 읽히도록 짧게 이어서 소개해 주세요. 자세한 내용은 뒤 장에서 다룬다고 안내합니다.", HALF - 60)),
    ])

    # 3. 연애할 때 나는 어떤 사람일까 (8~12쪽)
    section("3", [
        page("r3_open", "연애 성격 한 줄 요약", figure="opener", opener=True,
             slot=_slot("r3_open", "연애할 때의 성격을 한 문장으로 요약(lead)하고, 사주 근거와 함께 짧게 설명해 주세요.", 520, "lead")),
        page("r3_first", "내 첫인상과 이성에게 보이는 매력",
             slot=_slot("r3_first", "처음 만난 사람에게 보이는 첫인상과, 이성이 끌리는 매력 포인트를 일간·도화·식상 근거로 장면과 함께 써 주세요.")),
        page("r3_change", "좋아하면 내가 어떻게 변할까",
             slot=_slot("r3_change", "누군가를 좋아하게 되면 나타나는 말투·연락·행동의 변화(밀당, 집착, 희생 등 해당하는 것)를 장면으로 쓰고 보완법을 붙여 주세요.")),
        page("r3_good", "연애할 때 나의 장점",
             slot=_slot("r3_good", "연애할 때 장점 3가지를 사주 근거와 데이트·연락 장면으로 써 주세요.")),
        page("r3_bad", "연애할 때 나의 단점과 보완법",
             slot=_slot("r3_bad", "연애할 때 단점 2~3가지와 각각의 구체적인 보완법을 써 주세요.")),
    ])

    # 4. 내 연애는 왜 엇갈릴까 (13~16쪽)
    exp = r["experience"] or "알 수 없음"
    section("4", [
        page("r4_open", "반복되는 연애 패턴", figure="opener", opener=True,
             slot=_slot("r4_open", f"연애 경험({exp})을 반영해 반복되는 연애 패턴을 한 문장으로 요약(lead)하고, 그 패턴이 사주의 어떤 글자·관계에서 오는지 설명해 주세요.", 620, "lead")),
        page("r4_start", "시작할 때와 사귈 때 반복되는 일",
             slot=_slot("r4_start", "관계를 시작할 때와 사귀는 동안 반복되기 쉬운 장면을 쓰고 각각 방법을 붙여 주세요.")),
        page("r4_end", "다툴 때와 헤어질 때 반복되는 일",
             slot=_slot("r4_end", "다툴 때와 헤어질 때 반복되기 쉬운 장면을 쓰고 각각 방법을 붙여 주세요.")),
        page("r4_last", "사귀면 얼마나 갈까, 오래 가려면",
             slot=_slot("r4_last", "배우자 자리의 안정성(합·충)과 비겁 등을 근거로 관계가 오래 가는 조건과 고비가 오는 때를 쓰고, 오래 가는 구체적인 방법을 써 주세요.")),
    ])

    # 5. 다음 연인은 어떤 사람일까 (17~23쪽)
    section("5", [
        page("r5_seat", "배우자 자리(일지)란", static="r_spouse_seat", figure="spouse_seat", opener=True,
             slot=_slot("r5_seat", f"{name}님의 일지 글자({r['day_branch']['branch']})와 그 안의 숨은 글자가 그 사람에 대해 무엇을 알려 주는지 써 주세요.", HALF - 120)),
        page("r5_mood", "그 사람의 분위기와 성격",
             slot=_slot("r5_mood", "배우자 자리와 배우자 별의 오행·십신으로 그 사람의 분위기, 말투, 성격, 외모 분위기의 경향을 장면으로 써 주세요.")),
        page("r5_job", "그 사람이 하는 일",
             slot=_slot("r5_job", "배우자 별과 배우자 자리의 오행·십신으로 그 사람이 하기 쉬운 일의 성향과 분야 예시 5~6개를 경향으로 써 주세요.")),
        page("r5_age", "그 사람과의 나이 차이",
             slot=_slot("r5_age", "'연애 재료'의 배우자 별 자리(main_seat의 age_gap)와 인연이 오는 대운을 근거로 나이 차이의 경향을 쓰고, 단정이 아니라는 점과 나이보다 중요한 기준을 함께 써 주세요.")),
        page("r5_where", "어디서, 어떻게 만날까",
             slot=_slot("r5_where", "배우자 별이 놓인 자리(route)와 십신 구성으로 만나기 쉬운 곳과 경로(소개, 직장, 모임, 취미, 우연 등)를 구체적으로 쓰고, 그곳에서 인연을 늘리는 방법을 써 주세요.")),
        page("r5_know", "운명인 사람을 알아보는 방법",
             slot=_slot("r5_know", "배우자 자리와 합하는 글자, 용신 기운을 근거로 그 사람을 만났을 때 느끼기 쉬운 감정과 신호, 놓치지 않는 방법을 써 주세요.")),
        page("r5_scene", "우리의 첫 만남 장면",
             slot=_slot("r5_scene", "앞의 근거(만나는 곳, 그 사람의 성격, 인연이 오는 시기의 계절)를 모아 첫 만남 장면을 구체적으로 그려 주세요. 사주 근거를 문장 사이에 함께 밝힙니다.")),
    ])

    # 6. 잘 맞는 사람과 조심할 사람 (24~26쪽)
    section("6", [
        page("r6_good", "나와 잘 맞는 사람", figure="love_match", opener=True,
             slot=_slot("r6_good", "용신 오행과 잘 맞는 띠, 배우자 자리와 합하는 글자를 근거로 잘 맞는 사람의 성향을 장면과 함께 써 주세요.", HALF + 40)),
        page("r6_clash", "나와 자주 부딪히는 사람",
             slot=_slot("r6_clash", "넘치는 오행, 배우자 자리와 충하는 띠를 근거로 자주 부딪히는 사람의 성향과 부딪히는 장면, 푸는 방법을 써 주세요.")),
        page("r6_hurt", "나에게 상처 줄 사람 알아보는 법",
             slot=_slot("r6_hurt", "이 사주가 끌리기 쉬운 상처 주는 관계의 신호를 행동으로 쓰고(예: 연락 패턴, 약속 태도), 초반에 알아보는 체크 방법을 써 주세요. 겁주지 않습니다.")),
    ])

    # 7. 다음 연인은 언제 올까 (27~34쪽)
    section("7", [
        page("r7_graph", "나이별 연애운 흐름", figure="love_graph", opener=True,
             slot=_slot("r7_graph", "대운별 인연 점수 그래프에서 인연이 많이 들어오는 시기와 조용한 시기를 나이로 짚어 주세요.", HALF - 80)),
        page("r7_now", "지금 지나고 있는 10년의 연애운",
             slot=_slot("r7_now", "지금 대운(10년)의 글자가 배우자 별·배우자 자리·도화와 어떤 관계인지 근거로, 이 10년의 연애 흐름과 할 일을 써 주세요.")),
        page("r7_year", f"{f['order']['year']}년 연애운",
             slot=_slot("r7_year", f"{f['order']['year']}년 세운의 인연 표시와 인연 점수를 근거로 올해 연애운을 쓰고, 남은 달에 할 일을 써 주세요.")),
        page("r7_5y", "앞으로 5년 연애운", figure="love_years5", span=2,
             slot=_slot("r7_5y", "표의 5년을 한 해씩 문단으로 써 주세요(해마다 인연 표시 근거, 그해 연애 흐름, 할 일).", FULL * 2 - 420)),
        page("r7_12m", "앞으로 12개월 월별 연애운", figure="love_months", span=2,
             slot=_slot("r7_12m", "표의 12개월 가운데 인연 점수가 높은 달과 조심할 달을 골라, 달마다 무엇을 하면 좋은지 써 주세요.", FULL * 2 - 760)),
        page("r7_contact", "연락하기 좋은 때, 조심할 때",
             slot=_slot("r7_contact", "앞으로 12개월 가운데 연락·고백·데이트 신청에 좋은 달과 말실수·오해를 조심할 달을 근거와 함께 쓰고, 연락 방법 팁을 써 주세요.")),
    ])

    # 8. 짝사랑, 고백, 지난 인연 (35~39쪽)
    q = f["order"]["question"]
    section("8", [
        page("r8_status", "지금 내 상황에 맞는 조언", opener=True,
             slot=_slot("r8_status", f"고객의 지금 연애 상태는 '{status}'예요. 이 상황에서 할 일과 하지 말 일을 사주 근거와 함께 구체적으로 써 주세요.", FULL - 120)),
        page("r8_confess", "고백은 먼저 해도 될까, 기다려야 할까",
             slot=_slot("r8_confess", "식상(표현)과 관성(기다림), 다가오는 달의 인연 점수를 근거로 먼저 다가가는 쪽이 맞는지 기다리는 쪽이 맞는지 쓰고, 고백 방법과 때를 써 주세요.")),
        page("r8_crush", "짝사랑할 때 내 쪽에서 가능성을 높이는 법",
             slot=_slot("r8_crush", "이 사주로 짝사랑할 때 빠지기 쉬운 모습과, 내 쪽에서 가능성을 높이는 행동을 써 주세요. 상대 마음은 단정하지 않고, 상대 생일을 알면 깊은 궁합으로 볼 수 있다고 한 줄 안내합니다.")),
        page("r8_ex", "전 애인이 다시 연락 올까",
             slot=_slot("r8_ex", "다가오는 해·달 가운데 배우자 자리와 합하는 때(지난 인연이 다시 떠오르기 쉬운 때)를 근거로 쓰고, 다시 만날지 정리할지 판단하는 기준을 써 주세요. 자세한 재회는 재회사주에서 본다고 안내합니다.")),
        page("r8_answer", "질문에 대한 답", figure="question",
             slot=_slot("r8_answer", (f"고객 질문: \"{q}\". 사주 근거를 들어 솔직하고 구체적으로 답해 주세요." if q else
                                      "질문이 없으니, 이 연애 상태의 사람이 가장 궁금해할 한 가지에 답해 주세요."), FULL - 200)),
    ])

    # 9. 결혼운 (40~42쪽)
    section("9", [
        page("r9_when", "몇 살쯤 결혼할까", figure="marriage_years", opener=True,
             slot=_slot("r9_when", "표의 대운(배우자 별이나 배우자 자리와의 합이 들어오는 10년)을 근거로 결혼 인연이 들어오는 나이대를 쓰고, 그때 준비할 것을 써 주세요.", HALF)),
        page("r9_happy", "결혼하면 행복할까, 부딪히는 지점은",
             slot=_slot("r9_happy", "배우자 자리와 재성·관성 균형으로 결혼 생활의 모습, 부딪히기 쉬운 지점(돈, 집안일, 가족, 말투 등)과 보완법을 써 주세요.")),
        page("r9_check", "결혼 전에 꼭 확인할 것",
             slot=_slot("r9_check", "이 사주에게 특히 중요한 결혼 전 확인 항목 5~6가지를 이유와 함께 써 주세요.")),
    ])

    # 10. 인연을 부르는 방법과 마지막 조언 (43~50쪽) · 좋은 모델
    section("10", [
        page("r10_key", "내 연애 사주 핵심 정리", opener=True,
             slot=_slot("r10_key", "이 책에서 가장 중요한 세 가지(연애할 때 나의 힘, 인연이 오는 때, 꼭 바꿀 습관)를 한 문장 요약(lead)과 함께 정리해 주세요.", 640, "lead")),
        page("r10_lucky", "인연을 부르는 색·장소·행동", figure="lucky",
             slot=_slot("r10_lucky", "용신 기운과 도화를 근거로 인연을 부르는 색, 장소, 옷차림, 행동을 생활에서 바로 쓸 수 있게 써 주세요.", HALF)),
        page("r10_good", "좋은 시기에 인연 늘리는 법",
             slot=_slot("r10_good", "인연 점수가 높은 해와 달에 무엇을 하면 인연을 최대로 늘릴 수 있는지, 앞 장의 방법을 모아 언제 무엇을 할지까지 써 주세요.")),
        page("r10_care", "조심할 시기에 상처 줄이는 법",
             slot=_slot("r10_care", "배우자 자리와 충하거나 점수가 낮은 시기에 상처를 줄이는 방법(큰 결정 미루기, 말 조심, 혼자 시간)을 앞 장의 보완법을 모아 구체적으로 써 주세요.")),
        page("r10_todo", "오늘부터 할 일 목록", figure="habits",
             slot=_slot("r10_todo", "용신과 이 사주의 연애 습관을 바탕으로 매일·매주·매달 실천할 일 10가지를 체크리스트로 써 주세요. 한 줄에 한 가지, 바로 할 수 있는 행동으로 씁니다.", 560, "checklist")),
        page("r10_wait", "그 사람이 올 때까지 내가 할 일", span=2,
             slot=_slot("r10_wait", "다음 인연을 기다리는 동안 이 사람이 할 일을 시기 순서로 써 주세요(지금부터, 좋은 달 전, 좋은 달, 그 뒤). 불안한 마음이 풀리도록 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'를 함께 씁니다.", FULL * 2 - 60)),
        page("r10_last", "마지막 조언", figure="love_summary",
             slot=_slot("r10_last", f"{name}님에게 전하는 마지막 조언을 따뜻하지만 담백하게 써 주세요. 사랑받을 이유를 사주 근거로 말해 주고, 걱정보다 할 수 있는 일에 집중하게 해 주세요.", FULL - 260)),
    ])

    section("더보기", [page("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True)])
    return sections


def cross_sell_order(status: str) -> list[str]:
    """짝사랑·썸이면 깊은 궁합, 이별 후면 재회사주를 맨 위에 둔다."""
    if status in ("짝사랑", "썸"):
        return ["intimate"]
    if status in ("최근 이별",):
        return ["reunion"]
    return []
