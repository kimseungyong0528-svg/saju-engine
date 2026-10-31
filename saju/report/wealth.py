"""재물운 리포트(50쪽 이상): 재물 그릇, 돈 버는 방식, 새는 곳, 투자 성향, 대운·연도·월별 재물운.

목차 원본: /mnt/project-files/plan/wealth-report-toc.md (2026-10-11, 인터뷰 주제 20가지 반영)
사이트 입력: 내 정보, 현재 상황(occupation, 필수). 질문 칸은 없다.
"""

from __future__ import annotations

from . import theme as T
from .outline import FULL, HALF, _slot

FINAL_SECTION = "12"

SECTIONS = [
    ("1", "내 사주 한눈에 보기", "나의 사주표와 재물의 운명"),
    ("2", "한눈에 보는 나의 재물운", "재물 그릇, 돈 버는 방식, 좋은 해"),
    ("3", "나의 재물 그릇", "타고난 돈복의 크기와 모양"),
    ("4", "내가 돈을 버는 방식", "직장, 사업, 재능"),
    ("5", "돈이 빠져나가는 곳", "나도 몰랐던 나의 소비 습관과 손실"),
    ("6", "내가 몰랐던 돈이 들어오는 방법", "투자와 부업, 나에게 맞는 돈 불리기"),
    ("7", "나이별 재물운", "10년마다 달라지는 돈의 흐름"),
    ("8", "연도별 재물운", "앞으로 12년, 큰돈이 오가는 해"),
    ("9", "월별 재물운", "앞으로 12개월, 돈을 쓸 달과 아낄 달"),
    ("10", "집과 노후", "집 장만, 가족과 돈, 말년의 재물"),
    ("11", "지금 내 상황에 맞는 돈 전략", "자주 묻는 질문"),
    ("12", "재물운을 키우는 방법과 마지막 조언", ""),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

STATIC = {
    "w_how_to_read": [
        "이 책은 태어난 날과 시간으로 계산한 사주를 바탕으로, 타고난 재물 그릇부터 돈 버는 방식, 돈이 새는 곳, 투자 성향, 나이별·연도별·월별 재물운까지 순서대로 풀어 놓은 책이에요.",
        "가장 궁금한 내용은 2장 '한눈에 보는 나의 재물운'에 먼저 모아 두었어요. 자세한 이유와 방법은 뒤의 장에서 하나씩 설명해요.",
        "이 책은 특정 투자 상품이나 종목, 금액을 권하지 않아요. 내 사주에 맞는 돈의 흐름과 습관, 시기를 알려 드리는 책이에요. 큰돈이 오가는 결정은 꼭 전문가와 함께 확인하세요.",
        "사주 용어는 쉬운 말과 생활 장면으로 자세히 풀었고, 쪽 끝 '기억할 한 줄'에 그 쪽의 핵심을 한 문장으로 정리했어요.",
    ],
    "w_what_is_saju": [
        "사주(四柱)는 태어난 해, 달, 날, 시간의 네 기둥이에요. 기둥마다 위 글자(천간)와 아래 글자(지지)가 있어 모두 여덟 글자가 돼요.",
        "태어난 날의 위 글자(일간)가 '나 자신'이에요. 내가 누르는(극하는) 오행을 '재성(財星)'이라고 하고, 사주에서는 이 글자를 돈과 재물로 봐요.",
        "재물운은 재성 하나로만 보지 않아요. 돈을 만들어 내는 재능(식상), 돈을 지킬 힘(신강·신약), 돈을 나눠 가져가는 사람(비겁), 문서와 집(인성)을 함께 봐요.",
    ],
}


def _money_type(f: dict) -> tuple[str, str]:
    jae, sik, bi = T.count(f, "재성"), T.count(f, "식상"), T.count(f, "비겁")
    weak = f["strength"]["label"] in ("신약", "극신약")
    if jae >= 3 and weak:
        return "체력이 먼저인 형", "재물 글자는 많지만 나를 돕는 힘이 약해서(재다신약), 돈을 쫓기보다 몸과 실력을 먼저 키울 때 돈이 남아요."
    if jae == 0:
        return "운에서 들어오는 돈형", "태어날 때 받은 여덟 글자 안에는 재성이 없어서, 재성이 바깥에서 들어오는 해와 대운을 잡는 것이 가장 중요해요."
    if sik >= 2:
        return "재능이 돈이 되는 형", "재능과 표현(식상)이 재물(재성)을 낳는 구조(식상생재)라서, 잘하는 일을 키울수록 돈이 따라와요."
    if T.god_count(f, "편재") > T.god_count(f, "정재"):
        return "큰 흐름을 잡는 형", "움직이는 돈(편재)이 강해서 기회를 잡고 판을 키울 때 돈이 들어와요. 대신 나가는 돈도 커지기 쉬워요."
    return "꾸준히 쌓는 형", "고정된 돈(정재)의 기운이 중심이라 월급, 저축처럼 꾸준히 쌓을 때 재물이 커져요."


def _risk(f: dict) -> str:
    bold = T.god_count(f, "편재") + T.god_count(f, "상관") + T.god_count(f, "겁재")
    safe = T.god_count(f, "정재") + T.god_count(f, "정관") + T.count(f, "인성")
    return "도전형" if bold > safe + 1 else "안정형" if safe > bold + 1 else "균형형"


def build(f: dict, result: dict, answers: dict, partner=None) -> dict:
    strong = f["strength"]["label"] not in ("신약", "극신약")
    has_jae = T.count(f, "재성") > 0

    def mark(x: dict) -> dict:
        jae, sik, bi = T.has(x, "재성"), T.has(x, "식상"), T.has(x, "비겁")
        move = T.rel(x, "월주", T.CLASH)
        signs = [s for s, on in (("재물 별", jae), ("재능이 돈으로", sik), ("나가는 돈 주의", bi and has_jae), ("돈의 자리 변동", move)) if on]
        score = x["score"] + 10 * jae + (5 if strong else 2) * sik - 7 * (bi and has_jae) - 4 * move
        return {"t_score": T.clamp(score), "t_signs": signs}

    years, months, periods = T.marked(f, mark)
    T.reveal_fix(result, "wealth", years)   # 제1조항: 결제 전 화면의 12년 지도와 같은 표시·방향
    T.reveal_fix(result, "wealth", months)
    # 대운 표도 화면과 같은 규칙의 표시·방향(손님 테스트 3차: '나가는 돈 주의' 대운이 72점으로 가장 높았다)
    T.reveal_fix(result, "wealth", periods)
    mtype, mtext = _money_type(f)
    # 지금과 앞으로의 대운 중 80세 전에 시작하는 것에서 재물 점수가 높은 셋(재성이 드는 대운 우선), 나이순
    ahead = [p for p in T.near(f, periods) if p["state"] != "지난"]
    # '나가는 돈 주의' 대운이나 점수가 낮은 대운은 '큰돈이 들어오는 대운'에 넣지 않는다(같은 책 대운 표와 모순 금지)
    ahead = [p for p in ahead if p["t_score"] >= 55 and not p["r_bad"]]
    big = sorted(sorted(ahead, key=lambda p: (not T.has(p, "재성"), -p["t_score"]))[:3], key=lambda p: periods.index(p))
    screen = T.screen_score(f, result, "wealth")
    data = {
        "screen_score": screen,
        "occupation": answers.get("occupation", ""),
        "type": mtype, "type_text": mtext, "risk": _risk(f),
        "counts": {g: T.count(f, g) for g in T.GODS},
        "편재": T.god_count(f, "편재"), "정재": T.god_count(f, "정재"),
        "seats": T.seats(f, "재성"),
        "best_years": (best := T.best(years, 12, lambda y: y["year"])),
        "leak_years": T.bad_rows(years, 12, lambda y: y["year"]),   # 화면의 '돈이 샘'(겁재) 해
        "best_months": T.best(months, 3, T.ym), "careful_months": T.worst(months, 3, T.ym),
        "big_periods": [{"age_text": p["age_text"], "years_text": p["years_text"], "ganzhi": p["ganzhi"]} for p in big[:3]],
    }
    return {"label": "재물 재료", "data": data,
            "digest": {**data, **T.digest_rows(years, months, T.near(f, periods)),
                       "점수 설명": "t_score는 재물 점수: 운의 흐름 점수에 재성·식상이 들어오면 더하고, 비겁(나눠 가져가는 기운)과 월지 충을 빼 계산"},
            "years": years, "months": months, "periods": periods}


STYLE = T.style("재물운", """
[재물운 규칙]
- 독자는 돈을 모으고 싶거나, 언제 나아질지 궁금한 사람입니다. 현실적이고 구체적으로 씁니다.
- 근거는 '재물 재료'(돈 버는 형 type, 재성·식상·비겁 개수, 재물 점수 t_score와 표시 t_signs, 좋은 해·달)를 먼저 씁니다.
- 특정 투자 상품, 종목, 코인, 금액, 수익률을 권하거나 예측하지 않습니다. "목돈을 한곳에 몰지 않기"처럼 습관과 원칙으로 씁니다.
- 현재 상황(occupation)에 맞춰 씁니다(직장, 프리랜서, 사업, 쉬는 중, 언제 나아질지 궁금함).
- 돈 액수를 지어내지 않습니다. 비율(예: 수입의 3분의 1)과 순서로 씁니다.
""")


def build_outline(f: dict) -> list[dict]:
    th = f["theme"]
    t = th["data"]
    c = t["counts"]
    name = f["person"]["name"]
    sections: list[dict] = []

    def section(no: str, pages: list[dict]) -> None:
        title, subtitle = next((a, b) for n, a, b in SECTIONS if n == no)
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": []})

    P, S = T.tpage, _slot
    section("1", [
        P("cover", "표지", figure="cover"),
        P("toc", "목차", figure="toc"),
        P("how_to_read", "이 책을 읽는 방법", static="w_how_to_read", opener=True),
        P("w_saju", "사주와 재물 짧게 알기", static="w_what_is_saju", figure="element_cycle"),
        P("chart", "나의 사주표", figure="pillars",
          slot=S("chart", f"{name} 님의 여덟 글자를 소개하고, 일간이 돈을 대하는 태도에서 어떻게 나타나는지 쉽게 설명해 주세요.", HALF)),
        P("w_letters", "재물을 보는 글자", figure="kv", rows=[
            ["재성(재물)", f"{c['재성']}개 · 편재 {t['편재']} · 정재 {t['정재']}"
             + (f" · {', '.join(x for x in t['seats'] if '숨은 글자' not in x)}" if any('숨은 글자' not in x for x in t["seats"]) else "")
             + (f" (개수에 넣지 않은 숨은 글자: {', '.join(x for x in t['seats'] if '숨은 글자' in x)})" if any('숨은 글자' in x for x in t["seats"]) else "")],
            ["식상(재능·표현)", f"{c['식상']}개"], ["비겁(나·동료)", f"{c['비겁']}개"],
            ["인성(문서·집)", f"{c['인성']}개"], ["신강·신약", f"{f['strength']['label']} ({int(f['strength']['score'] + 0.5)}점)"],
        ], slot=S("w_letters", "표의 글자가 각각 돈과 어떤 관계인지, 이 사주에서는 어떻게 있는지 설명해 주세요.", HALF - 40)),
    ])
    section("2", [
        P("w_glance", "한눈에 보는 나의 재물운", figure="kv", opener=True, rows=[
            T.screen_row(t["screen_score"], t.get("seen", True)),
            ["돈 버는 형", t["type"]], ["투자 성향", t["risk"]],
            ["재물운이 좋은 해", ", ".join(f"{y}년" for y in t["best_years"]) or "앞으로 12년 안에는 뚜렷하지 않아요"],
            ["나가는 돈 주의할 해", ", ".join(f"{y}년" for y in t["leak_years"]) or "앞으로 12년 안에는 뚜렷하지 않아요"],
            ["돈 쓰기 좋은 달", ", ".join(t["best_months"])], ["아낄 달", ", ".join(t["careful_months"]) or "크게 아껴야 할 달은 없어요"],
            ["큰돈이 들어오는 대운", ", ".join(p["age_text"] for p in t["big_periods"]) or "운에서 재성이 드는 해를 잡아요"],
        ], slot=S("w_glance", "표를 이어서 재물운의 핵심을 짧게 소개하고, 자세한 내용은 뒤 장에서 다룬다고 안내해 주세요.", HALF - 120)),
    ])
    section("3", [
        P("w3_open", "타고난 재물 그릇", figure="opener", opener=True,
          slot=S("w3_open", f"{name} 님의 재물 그릇을 '{t['type']}'로 한 문장 요약(lead)하고, 근거({t['type_text']})를 쉽게 풀어 주세요.", 540, "lead")),
        P("w3_size", "돈복의 크기를 정하는 것",
          slot=S("w3_size", "재성 개수, 신강·신약, 격국 성패를 근거로 이 사람이 다룰 수 있는 돈의 크기와 그 그릇을 키우는 방법을 써 주세요.")),
        P("w3_shape", "돈복의 모양",
          slot=S("w3_shape", "재성이 놓인 자리(seats)와 고전 판단(물상)을 근거로 돈이 들어오는 모양(한 번에 크게, 조금씩 꾸준히, 사람을 통해 등)을 장면으로 써 주세요.")),
        P("w3_good_bad", "재물에서 나의 강점과 약점",
          slot=S("w3_good_bad", "돈을 다룰 때의 강점 3가지와 약점 2~3가지를 근거와 함께 쓰고, 약점마다 보완법을 붙여 주세요.")),
    ])
    occ = t["occupation"] or "알 수 없음"
    section("4", [
        P("w4_open", "나에게 맞는 돈 버는 방식", figure="kv", opener=True, rows=[
            ["월급(정관·정재)", f"정관 {T.god_count(f, '정관')} · 정재 {t['정재']}"], ["사업·거래(편재)", f"편재 {t['편재']}"],
            ["재능·기술(식상)", f"{c['식상']}개"], ["지금 상황", occ],
        ], slot=S("w4_open", "표를 근거로 월급, 사업, 재능 가운데 어느 쪽이 돈이 되기 쉬운지 설명해 주세요.", HALF)),
        P("w4_way", "돈이 되는 일의 조건",
          slot=S("w4_way", "용신과 격국, 식상·재성 구성을 근거로 이 사람에게 돈이 되는 일의 조건(혼자/함께, 고정/변동, 사람/물건/지식)과 분야 예시를 써 주세요.")),
        P("w4_now", "지금 상황에서 수입을 늘리는 법",
          slot=S("w4_now", f"현재 상황 '{occ}'에 맞춰 수입을 늘리는 현실적인 방법 3~4가지를 사주 근거와 순서대로 써 주세요.")),
        P("w4_people", "돈을 가져다주는 사람",
          slot=S("w4_people", "인성·관성 구성(귀인 신살이 있으면 그것도)을 근거로 돈과 기회를 연결해 주기 쉬운 사람의 유형과 그런 사람을 만나는 곳을 써 주세요.")),
    ])
    section("5", [
        P("w5_open", "돈이 새는 구조", figure="opener", opener=True,
          slot=S("w5_open", "이 사주에서 돈이 새는 가장 큰 이유를 한 문장(lead)으로 말하고 근거를 설명해 주세요.", 620, "lead")),
        P("w5_spend", "나의 소비 습관",
          slot=S("w5_spend", "넘치는 오행과 십신 구성을 근거로 돈을 쓰기 쉬운 상황(스트레스, 사람, 기분, 체면 등)을 장면으로 쓰고 각각 막는 방법을 써 주세요.")),
        P("w5_people", "사람 때문에 나가는 돈",
          slot=S("w5_people", f"비겁 {c['비겁']}개와 합충을 근거로 빌려주기, 보증, 동업, 경조사 등 사람 때문에 나가는 돈의 위험과 거절하는 방법을 써 주세요.")),
        P("w5_when", "돈이 새기 쉬운 시기",
          slot=S("w5_when", "재물 점수가 낮거나 '나가는 돈 주의' 표시가 있는 해와 달을 근거로 돈이 새기 쉬운 시기와 그때의 대비법을 써 주세요.")),
    ])
    section("6", [
        P("w6_open", "나의 투자 성향", figure="kv", opener=True, rows=[
            ["투자 성향", t["risk"]], ["움직이는 돈(편재)", f"{t['편재']}개"], ["고정된 돈(정재)", f"{t['정재']}개"],
            ["모험의 기운(상관·겁재)", f"{T.god_count(f, '상관') + T.god_count(f, '겁재')}개"],
        ], slot=S("w6_open", "표를 근거로 이 사람의 투자 성향을 설명해 주세요. 특정 상품은 권하지 않습니다.", HALF)),
        P("w6_invest", "나에게 맞는 돈 불리기 원칙",
          slot=S("w6_invest", "투자 성향에 맞는 돈 불리기 원칙(나눠 넣기, 기간, 확인 순서, 멈출 기준)을 구체적으로 써 주세요. 상품명과 수익률은 쓰지 않습니다.")),
        P("w6_side", "부업과 두 번째 수입",
          slot=S("w6_side", "식상·재성 구성과 용신으로 이 사람에게 맞는 부업의 성향과 예시, 시작하기 좋은 시기를 써 주세요.")),
        P("w6_debt", "빚과 대출을 다루는 법",
          slot=S("w6_debt", "이 사주에 맞는 빚·대출 원칙과 조심할 시기, 갚는 순서를 써 주세요.")),
    ])
    section("7", [
        P("w7_graph", "나이별 재물운 그래프", figure="theme_graph", opener=True, note="대운(10년)마다 재성과 식상이 들어오면 점수가 올라가고, 비겁이 들어오면 내려가요.",
          slot=S("w7_graph", "그래프에서 재물운이 강한 시기와 약한 시기를 나이로 짚어 주세요.", HALF - 80)),
        P("w7_past", "지난 10년 돌아보기",
          slot=S("w7_past", "바로 앞 대운(지난 10년)의 글자와 재물 점수를 근거로 그때 돈이 어떻게 움직였기 쉬운지 돌아보고, 그 경험에서 지금 가져갈 교훈을 써 주세요.")),
        P("w7_now", "지금 지나는 10년의 재물운",
          slot=S("w7_now", "지금 대운의 글자(십신, 재물 표시, 점수)를 근거로 이 10년 동안의 돈의 흐름과 할 일을 써 주세요.")),
        P("w7_next", "다음 10년의 재물운",
          slot=S("w7_next", "다음 대운의 글자를 근거로 그 10년의 돈의 흐름을 미리 쓰고, 지금부터 준비할 것을 써 주세요.")),
        P("w7_table", "큰돈이 들어오는 시기", figure="grid", grid=T.period_grid(T.near(f, th["periods"]), "재물 점수"),
          slot=S("w7_table", "표에서 재물 점수가 높은 대운을 골라 그때 무엇을 하면 좋은지 써 주세요.", HALF - 160)),
    ])
    section("8", [
        P("w8_years", "앞으로 12년 재물운", figure="grid", opener=True, span=3, grid=T.year_grid(th["years"], t["best_years"], "재물 점수"),
          slot=S("w8_years", "표의 12년을 한 해씩 짧은 문단으로 써 주세요(그해 표시 근거, 돈의 흐름, 할 일과 피할 일).", FULL * 3 - 460)),
        P("w8_this", f"{f['order']['year']}년 재물운",
          slot=S("w8_this", "올해 세운의 재물 표시와 점수를 근거로 올해 남은 기간의 돈 관리법을 써 주세요.")),
        P("w8_big", "큰돈이 오가는 해 대비하기",
          slot=S("w8_big", "앞으로 12년 가운데 큰돈이 들어오기 쉬운 해와 큰돈이 나가기 쉬운 해(계약, 이사, 보증)를 근거와 함께 쓰고 각각 준비할 것을 써 주세요.")),
    ])
    section("9", [
        P("w9_months", "앞으로 12개월 월별 재물운", figure="grid", opener=True, span=2, grid=T.month_grid(th["months"], "재물 점수"),
          note="표시: 그 달에 들어오는 재물 별, 재능, 나가는 돈 기운이에요.",
          slot=S("w9_months", "표의 12개월 가운데 돈이 들어오기 좋은 달과 아낄 달을 골라 달마다 할 일을 써 주세요.", FULL * 2 - 820)),
        P("w9_use", "쓸 달과 아낄 달",
          slot=S("w9_use", "큰 지출, 계약, 쇼핑, 투자 결정을 하기 좋은 달과 미룰 달을 근거와 함께 표처럼 정리해 주세요.", FULL, "plan")),
        P("w9_habit", "달마다 지킬 돈 습관",
          slot=S("w9_habit", "월급날·카드 결제일·한 달 마감에 맞춰 이 사주에 맞는 돈 습관을 구체적으로 써 주세요.")),
    ])
    section("10", [
        P("w10_home", "집과 문서의 운", opener=True,
          slot=S("w10_home", f"인성(문서·집) {c['인성']}개와 대운·세운을 근거로 집 장만이나 큰 문서 계약에 좋은 시기와 조심할 점을 써 주세요.", FULL - 120)),
        P("w10_family", "가족과 돈",
          slot=S("w10_family", "배우자·부모·자녀와 돈이 얽힐 때 생기기 쉬운 일과 원칙을 근거와 함께 써 주세요. 가족 상황은 가정하지 않고 경우를 나눠 씁니다.")),
        P("w10_old", "말년의 재물과 노후 준비",
          slot=S("w10_old", "시주와 말년 대운을 근거로 노후의 재물 흐름을 쓰고, 지금부터 할 노후 준비를 단계별로 써 주세요.")),
    ])
    section("11", [
        P("w11_now", "지금 내 상황에 맞는 돈 전략", opener=True,
          slot=S("w11_now", f"현재 상황은 '{occ}'이에요. 이 상황에서 앞으로 1년 동안의 돈 전략을 사주 근거와 함께 순서대로 써 주세요.", FULL - 120)),
        P("w11_qa", "자주 묻는 질문",
          slot=S("w11_qa", "이 사주를 가진 사람이 돈에 대해 가장 많이 물을 질문 3가지(예: 언제 나아질까, 지금 투자해도 될까, 왜 모이지 않을까)를 묻고 근거와 함께 답해 주세요.", FULL, "qa")),
    ])
    section("12", [
        P("w12_key", "내 재물운 핵심 정리", opener=True,
          slot=S("w12_key", "이 책에서 가장 중요한 세 가지(나의 돈 버는 방식, 좋은 시기, 꼭 막을 새는 돈)를 한 문장 요약(lead)과 함께 정리해 주세요.", 640, "lead")),
        P("w12_lucky", "재물을 부르는 색·숫자·방향", figure="lucky",
          slot=S("w12_lucky", "용신 기운을 근거로 지갑, 통장, 일하는 자리에 쓸 색과 숫자, 방향, 공간 정리법을 써 주세요.", HALF)),
        P("w12_plan", "1년 돈 계획",
          slot=S("w12_plan", "앞으로 1년을 시기별로 나눠 할 일과 피할 일을 정리해 주세요.", FULL, "plan")),
        P("w12_todo", "오늘부터 할 돈 습관", slot=S("w12_todo", "오늘부터 실천할 돈 습관 10가지를 체크리스트로 써 주세요. 한 줄에 한 가지입니다.", 600, "checklist")),
        P("w12_worry", "돈 걱정에 대한 답", span=2,
          slot=S("w12_worry", "이 사람이 가지기 쉬운 돈 걱정(평생 이렇게 살까, 남들보다 늦었나, 큰돈을 잃으면, 노후가 걱정돼)마다 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'를 함께 답해 주세요.", FULL * 2 - 60)),
        P("w12_last", "마지막 조언",
          slot=S("w12_last", f"{name} 님에게 전하는 마지막 조언을 담백하게 써 주세요. 이 사주가 돈을 모을 수 있는 이유를 근거로 말해 주고, 가장 먼저 할 한 가지를 짚어 주세요.", FULL - 120)),
    ])
    section("더보기", [P("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True)])
    return sections


def cross_sell_order(f: dict) -> list[str]:
    occ = f["theme"]["data"]["occupation"]
    return ["business", "career"] if "사업" in occ else ["career", "business"]
