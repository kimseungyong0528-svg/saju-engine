"""사업운 리포트(50쪽 이상, 13장): 사업 체질, 맞는 분야와 방식, 돈이 크게 들어오는 시기, 동업·직원, 확장과 지킬 때, 연도·월별 사업운.

목차 원본: /mnt/project-files/plan/business-report-toc.md (2026-10-11, 인터뷰 주제 20가지 반영)
사이트 입력: 내 정보, 사업 단계(stage, 필수), 먼저 볼 주제(priority, 필수), 질문.
"""

from __future__ import annotations

from . import theme as T
from .career import _FIELD
from .outline import FULL, HALF, _slot

FINAL_SECTION = "13"

SECTIONS = [
    ("1", "내 사주 한눈에 보기", "나의 사주표와 사업의 운명"),
    ("2", "한눈에 보는 나의 사업운", "나의 사업 체질, 맞는 방식, 좋은 시기"),
    ("3", "일을 시작하고 키우는 성향", "구체적인 나의 사업 체질과 흐름"),
    ("4", "나에게 맞는 사업", "분야, 운영 방식, 장소"),
    ("5", "혼자 또는 함께 일하는 방식", "동업, 직원, 거래처"),
    ("6", "손님과 돈", "고객을 모으고 이익을 남기는 법"),
    ("7", "돈이 크게 들어오는 시기", "재물운이 함께 들어오는 때와 나가는 때"),
    ("8", "운영과 확장 사이", "넓힐 때와 유지할 때"),
    ("9", "연도별 사업운", "앞으로 5년, 올해의 사업운"),
    ("10", "월별 사업운", "앞으로 12개월, 계약과 오픈에 좋은 달"),
    ("11", "나이별 사업운", "10년마다 달라지는 사업의 흐름"),
    ("12", "현재 나의 단계와 질문에 대한 답", ""),
    ("13", "나의 사업 계획 점검표와 마지막 조언", ""),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

STATIC = {
    "b_how_to_read": [
        "이 책은 태어난 날과 시간으로 계산한 사주를 바탕으로, 사업 체질부터 맞는 업종과 방식, 함께 일하는 사람, 확장할 때와 지킬 때, 연도별·월별 사업운까지 순서대로 풀어 놓은 책이에요.",
        "가장 궁금한 내용은 2장 '한눈에 보는 나의 사업운'에 먼저 모아 두었어요. 자세한 이유와 방법은 뒤의 장에서 하나씩 설명해요.",
        "이 책은 특정 업종이나 투자, 금액을 정해 주지 않아요. 내 사주가 힘을 쓰기 쉬운 방식과 시기를 알려 드려요. 계약, 대출, 세금처럼 큰 결정은 꼭 전문가와 함께 확인하세요.",
        "사주 용어는 쉬운 말과 생활 장면으로 자세히 풀었고, 쪽 끝 '기억할 한 줄'에 그 쪽의 핵심을 한 문장으로 정리했어요.",
    ],
    "b_what_is_saju": [
        "사주(四柱)는 태어난 해, 달, 날, 시간의 네 기둥이에요. 기둥마다 위 글자(천간)와 아래 글자(지지)가 있어 모두 여덟 글자가 돼요.",
        "사업은 세 가지 기운의 균형으로 봐요. 나 자신과 동료(비겁), 상품과 재능(식상), 돈과 손님(재성)이에요. 여기에 체계와 신용(관성), 문서와 자격(인성)을 더해 봐요.",
        "재능(식상)이 돈(재성)을 낳는 흐름이 이어지면 사업이 커지기 쉽고, 나와 같은 기운(비겁)이 돈을 나눠 가져가면 지출과 경쟁이 커지기 쉬워요.",
    ],
}

_STAGE = {"창업을 준비하고 있어요": "창업 준비", "처음 사업을 시작했어요": "초기", "사업을 운영하고 있어요": "운영 중",
          "새로운 확장을 고민해요": "확장 고민", "방향을 다시 정리하고 싶어요": "방향 정리"}


def _type(f: dict) -> tuple[str, str]:
    c = {g: T.count(f, g) for g in T.GODS}
    weak = f["strength"]["label"] in ("신약", "극신약")
    if weak and c["재성"] >= 2:
        return "작게 단단히 시작하는 형", "돈의 기운(재성)은 있지만 나를 받치는 힘이 약해서, 작게 시작해 체력과 사람을 먼저 갖출 때 오래가요."
    if c["식상"] >= 2 and c["재성"] >= 1:
        return "재능을 파는 형", "상품과 재능(식상)이 돈(재성)을 낳는 구조(식상생재)라서, 내가 잘 만드는 것을 파는 사업에서 힘이 나요."
    if c["재성"] >= 2:
        return "판을 키우는 확장형", "돈과 거래(재성)의 기운이 강해서, 사람과 물건을 움직여 판을 키울 때 힘이 나요."
    if c["비겁"] >= 3:
        return "혼자 끌고 가는 오너형", "나와 같은 기운(비겁)이 강해서, 내가 결정권을 쥐고 끌고 갈 때 힘이 나요. 대신 돈을 나눠 가져가는 사람을 조심해야 해요."
    if c["관성"] >= 2:
        return "체계로 운영하는 관리형", "체계와 신용(관성)의 기운이 강해서, 규칙과 시스템을 갖춰 운영할 때 힘이 나요."
    if c["인성"] >= 2:
        return "지식과 자격으로 하는 전문형", "문서와 자격(인성)의 기운이 강해서, 전문 지식과 신뢰를 파는 사업에서 힘이 나요."
    return "균형형", "십신이 고르게 있어서 여러 역할을 직접 해낼 수 있어요. 처음에는 한 가지 강점에 집중하는 것이 좋아요."


def _bi(x: dict) -> bool:
    return "경쟁·지출 주의" in x["t_signs"] or "힘을 보태는 기운" in x["t_signs"]


def build(f: dict, result: dict, answers: dict, partner=None) -> dict:
    weak = f["strength"]["label"] in ("신약", "극신약")
    has_jae = T.count(f, "재성") > 0

    def mark(x: dict) -> dict:
        jae, sik, bi, gwan = T.has(x, "재성"), T.has(x, "식상"), T.has(x, "비겁"), T.has(x, "관성")
        seat = T.rel(x, "월주", T.CLASH)
        signs = [s for s, on in (("재물 별", jae), ("상품·재능 기운", sik), ("경쟁·지출 주의", bi and has_jae),
                                 ("힘을 보태는 기운", bi and not has_jae), ("계약·체계 기운", gwan), ("사업 자리 변동", seat)) if on]
        score = x["score"] + 8 * jae + (3 if weak else 6) * sik + (-6 if has_jae else 3) * bi + 3 * gwan - 4 * seat
        return {"t_score": T.clamp(score), "t_signs": signs, "t_grow": jae and sik}

    years, months, periods = T.marked(f, mark)
    btype, btext = _type(f)
    bi, jae = T.count(f, "비겁"), T.count(f, "재성")
    partner_rule = ("동업은 역할과 돈을 문서로 나눌 때만" if bi >= 3 and jae >= 1 else
                    "혼자 버티기보다 믿을 파트너가 필요" if bi == 0 else "나와 역할이 다른 사람과 함께")
    grow = [y["year"] for y in years if y["t_grow"]][:2] or T.best(years, 2, lambda y: y["year"])
    keep = [y["year"] for y in sorted(years, key=lambda y: y["t_score"])[:2] if y["year"] not in grow]
    data = {
        "stage": _STAGE.get(answers.get("stage", ""), answers.get("stage", "")), "priority": answers.get("priority", ""),
        "type": btype, "type_text": btext, "partner_rule": partner_rule,
        "counts": {g: T.count(f, g) for g in T.GODS},
        "fields": _FIELD[f["lucky"]["element"]],
        "grow_years": grow, "keep_years": sorted(keep),
        "best_years": T.best(years, 2, lambda y: y["year"]),
        "best_months": T.best(months, 3, T.ym), "careful_months": T.worst(months, 3, T.ym),
        # 돈이 잘 풀리는 시기: 재물 별이 드는 때를 먼저, 그다음 사업 점수 높은 순. 새는 때: 비겁(경쟁·지출, 나눠 가져가는 기운)이 드는 때 가운데 점수 낮은 순
        "money_years": sorted(y["year"] for y in sorted(years, key=lambda y: ("재물 별" not in y["t_signs"], -y["t_score"]))[:2]),
        "leak_years": sorted(y["year"] for y in sorted(years, key=lambda y: (not _bi(y), y["t_score"]))[:2]),
        "money_months": [T.ym(m) for m in sorted(months, key=lambda m: ("재물 별" not in m["t_signs"], -m["t_score"]))[:3]],
        "leak_months": [T.ym(m) for m in sorted(months, key=lambda m: (not _bi(m), m["t_score"]))[:3]],
    }
    return {"label": "사업 재료", "data": data,
            "digest": {**data, **T.digest_rows(years, months, T.near(f, periods)),
                       "점수 설명": "t_score는 사업 점수: 운의 흐름 점수에 재성·식상·관성이 들어오면 더하고, 재성이 있는 사주에 비겁이 들어오면(경쟁·지출) 빼고, 월지 충은 조금 빼 계산"},
            "years": years, "months": months, "periods": periods}


STYLE = T.style("사업운", """
[사업운 규칙]
- '돈이 크게 들어오는 시기' 장은 사업 재료의 money_years, leak_years, money_months, leak_months를 근거로 씁니다.
- 독자는 창업을 준비하거나 사업을 운영하며 다음 선택을 고민하는 사람입니다. 현실적인 운영 장면(매출, 손님, 직원, 거래처, 계약)으로 씁니다.
- 근거는 '사업 재료'(사업 형 type, 십신 개수, 동업 원칙 partner_rule, 사업 점수 t_score와 표시 t_signs, 확장할 해 grow_years, 지킬 해 keep_years)를 먼저 씁니다.
- 특정 업종을 단정하지 않고 '이런 조건의 사업'과 예시 여러 개로 씁니다. 매출·금액·수익률은 지어내지 않습니다.
- 사업 단계(stage)와 먼저 볼 주제(priority)에 맞춰 씁니다.
""")


def build_outline(f: dict) -> list[dict]:
    th = f["theme"]
    t = th["data"]
    c = t["counts"]
    name = f["person"]["name"]
    stage = t["stage"] or "알 수 없음"
    sections: list[dict] = []

    def section(no: str, pages: list[dict]) -> None:
        title, subtitle = next((a, b) for n, a, b in SECTIONS if n == no)
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": []})

    P, S = T.tpage, _slot
    yrs = lambda xs: ", ".join(f"{y}년" for y in xs) or "—"
    section("1", [
        P("cover", "표지", figure="cover"),
        P("toc", "목차", figure="toc"),
        P("how_to_read", "이 책을 읽는 방법", static="b_how_to_read", opener=True),
        P("b_saju", "사주와 사업 짧게 알기", static="b_what_is_saju", figure="element_cycle"),
        P("chart", "나의 사주표", figure="pillars",
          slot=S("chart", f"{name}님의 여덟 글자를 소개하고, 일간이 일을 벌이고 결정하는 방식에서 어떻게 나타나는지 쉽게 설명해 주세요.", HALF)),
        P("b_letters", "사업을 보는 글자", figure="kv", rows=[
            ["비겁(나·동료)", f"{c['비겁']}개"], ["식상(상품·재능)", f"{c['식상']}개"], ["재성(돈·손님)", f"{c['재성']}개"],
            ["관성(체계·신용)", f"{c['관성']}개"], ["인성(문서·자격)", f"{c['인성']}개"],
            ["신강·신약", f"{f['strength']['label']} ({f['strength']['score']:.0f}점)"],
        ], slot=S("b_letters", "표의 글자가 사업에서 각각 무엇을 뜻하는지, 이 사주에서는 어떻게 있는지 설명해 주세요.", HALF - 80)),
    ])
    section("2", [
        P("b_glance", "한눈에 보는 나의 사업운", figure="kv", opener=True, rows=[
            ["사업 체질", t["type"]], ["함께 일하는 원칙", t["partner_rule"]], ["어울리는 분야", t["fields"]],
            ["넓히기 좋은 해", yrs(t["grow_years"])], ["지키며 다질 해", yrs(t["keep_years"])],
            ["가까운 좋은 달", ", ".join(t["best_months"])], ["조심할 달", ", ".join(t["careful_months"]) or "—"],
        ], slot=S("b_glance", "표를 이어서 사업운의 핵심을 짧게 소개하고, 자세한 내용은 뒤 장에서 다룬다고 안내해 주세요.", HALF - 160)),
    ])
    section("3", [
        P("b3_open", "나의 사업 체질", figure="opener", opener=True,
          slot=S("b3_open", f"{name}님의 사업 체질을 '{t['type']}'로 한 문장 요약(lead)하고, 근거({t['type_text']})를 쉽게 풀어 주세요.", 640, "lead")),
        P("b3_good", "사업할 때 나의 강점",
          slot=S("b3_good", "사업할 때 강점 3가지를 사주 근거와 운영 장면(손님 응대, 상품 만들기, 결정)으로 써 주세요.")),
        P("b3_bad", "사업할 때 나의 약점과 보완법",
          slot=S("b3_bad", "사업할 때 약점 2~3가지와 각각의 구체적인 보완법을 써 주세요.")),
        P("b3_decide", "결정하는 방식",
          slot=S("b3_decide", "격국과 신강·신약, 넘치는 기운을 근거로 이 사람이 결정을 내리는 방식(빠름/신중, 감/숫자)과 실수를 줄이는 결정 규칙을 써 주세요.")),
    ])
    section("4", [
        P("b4_open", "어울리는 분야", figure="kv", opener=True, rows=[
            ["도움 되는 기운", f"{f['lucky']['element_name']}({f['lucky']['element']})"], ["어울리는 분야", t["fields"]],
            ["사업 체질", t["type"]],
        ], slot=S("b4_open", "표의 분야가 왜 맞는지 근거를 설명해 주세요.", HALF)),
        P("b4_kind", "나에게 맞는 사업의 조건",
          slot=S("b4_kind", "이 사주에 맞는 사업의 조건(상품/서비스, 단골/새 손님, 고가/박리다매, 한 곳/여러 곳)과 예시를 써 주세요.")),
        P("b4_way", "운영 방식: 온라인, 매장, 혼자, 팀",
          slot=S("b4_way", "온라인·오프라인, 혼자·팀, 직접 운영·위탁 가운데 이 사주에 맞는 운영 방식과 이유를 써 주세요.")),
        P("b4_place", "사업장 위치와 공간",
          slot=S("b4_place", "용신의 방향과 기운을 근거로 사업장 방향, 공간 분위기, 간판·인테리어 색을 써 주세요.")),
    ])
    section("5", [
        P("b5_open", "함께 일하는 원칙", figure="kv", opener=True, rows=[
            ["비겁(동료·경쟁자)", f"{c['비겁']}개"], ["관성(체계·규칙)", f"{c['관성']}개"], ["원칙", t["partner_rule"]],
        ], slot=S("b5_open", "표를 근거로 이 사람이 다른 사람과 일할 때 지켜야 할 원칙을 설명해 주세요.", HALF)),
        P("b5_partner", "동업해도 될까",
          slot=S("b5_partner", "동업이 맞는지, 한다면 어떤 사람과 어떤 조건(역할, 돈, 결정권, 끝내는 방법)으로 해야 하는지 써 주세요.")),
        P("b5_staff", "직원과 함께 일하는 법",
          slot=S("b5_staff", "식상(아랫사람)·관성 구성(없으면 없는 대로)을 근거로 직원을 뽑을 때 볼 점, 일을 맡기는 법, 부딪히기 쉬운 장면과 방법을 써 주세요.")),
        P("b5_client", "거래처와 파트너",
          slot=S("b5_client", "합충과 사주에 실제로 있는 귀인 신살(없으면 인성·관성 구성)을 근거로 도움이 되는 거래처·파트너의 유형과 조심할 유형, 계약할 때 확인할 점을 써 주세요.")),
    ])
    section("6", [
        P("b6_open", "손님이 찾아오는 이유", figure="opener", opener=True,
          slot=S("b6_open", "이 사주의 사업에 손님이 찾아오는 가장 큰 이유를 한 문장(lead)으로 말하고 근거를 설명해 주세요.", 620, "lead")),
        P("b6_customer", "손님을 모으는 법",
          slot=S("b6_customer", "식상(표현)과 사주에 실제로 있는 신살(도화·홍염·귀인 등, 없으면 언급하지 않기)을 근거로 홍보, 단골 만들기, 소개 받기 방법을 구체적으로 써 주세요.")),
        P("b6_profit", "이익을 남기는 법",
          slot=S("b6_profit", "재성·비겁 구성을 근거로 매출보다 이익을 남기는 습관(가격, 비용, 현금 흐름, 재고)을 구체적으로 써 주세요.")),
        P("b6_price", "가격과 돈 관리 원칙",
          slot=S("b6_price", "이 사주에 맞는 가격 정하기와 사업 통장·개인 통장 나누기, 비상금 원칙을 써 주세요. 금액은 비율로 씁니다.")),
    ])
    section("7", [
        P("bm_open", "돈이 잘 풀리는 때와 새는 때", figure="kv", opener=True, rows=[
            ["돈이 잘 풀리는 해", yrs(t["money_years"])], ["돈이 새기 쉬운 해", yrs(t["leak_years"])],
            ["돈이 잘 풀리는 달", ", ".join(t["money_months"]) or "—"], ["지출을 조심할 달", ", ".join(t["leak_months"]) or "—"],
            ["재성(돈·손님)", f"{c['재성']}개"], ["비겁(나눠 가져가는 기운)", f"{c['비겁']}개"],
        ], note="재물 별(재성)이 드는 때와 사업 점수가 높은 때는 돈이 돌기 쉽고, 비겁(나와 같은 기운)이 드는 때는 경쟁과 지출이 커지기 쉬워요.",
          slot=S("bm_open", "표를 근거로 사업 자금이 잘 풀리는 시기와 새기 쉬운 시기를 쉽게 설명해 주세요.", HALF)),
        P("bm_in", "돈이 들어오는 길",
          slot=S("bm_in", "재성·식상 구성과 돈이 잘 풀리는 해·달을 근거로, 이 사업에서 돈이 들어오기 쉬운 길(단골, 새 상품, 거래처, 계약)과 그때 할 일을 써 주세요.")),
        P("bm_leak", "돈이 새는 때와 막는 법",
          slot=S("bm_leak", "돈이 새기 쉬운 해·달(비겁이 드는 때)과 비겁 구성을 근거로, 돈이 빠져나가기 쉬운 장면과 막는 방법을 써 주세요. 금액은 비율로 씁니다.")),
        P("bm_use", "돈이 들어올 때 쓰는 순서",
          slot=S("bm_use", "돈이 잘 풀리는 시기에 들어온 돈을 나누는 순서(비상금, 재투자, 빚 줄이기, 나에게 쓰기)를 이 사주에 맞춰 비율로 써 주세요.")),
    ])
    section("8", [
        P("b7_open", "넓힐 때와 지킬 때", figure="kv", opener=True, rows=[
            ["넓히기 좋은 해", yrs(t["grow_years"])], ["지키며 다질 해", yrs(t["keep_years"])],
            ["사업 자리 변동이 드는 달", ", ".join(T.ym(m) for m in th["months"] if "사업 자리 변동" in m["t_signs"]) or "없음"],
        ], slot=S("b7_open", "표를 근거로 확장과 유지의 시기를 설명해 주세요.", HALF)),
        P("b7_grow", "확장 신호와 확장하는 법",
          slot=S("b7_grow", "확장해도 되는 신호(사주와 현실 둘 다)와 확장 순서(사람, 공간, 상품, 지역)를 써 주세요.")),
        P("b7_keep", "지켜야 할 때 하는 일",
          slot=S("b7_keep", "지키며 다질 때 줄일 것과 늘릴 것, 위기 신호와 대비법을 근거와 함께 써 주세요.")),
        P("b7_contract", "계약, 대출, 투자 받기",
          slot=S("b7_contract", "관성·인성(문서)과 사업 점수를 근거로 큰 계약, 대출, 투자 유치에 좋은 시기와 조심할 점을 써 주세요.")),
    ])
    section("9", [
        P("b8_years", "앞으로 5년 사업운", figure="grid", opener=True, span=2, grid=T.year_grid(th["years"], t["grow_years"], "사업 점수"),
          slot=S("b8_years", "표의 5년을 한 해씩 문단으로 써 주세요(그해 표시 근거, 사업의 흐름, 할 일과 피할 일).", FULL * 2 - 460)),
        P("b8_this", f"{f['order']['year']}년 사업운",
          slot=S("b8_this", "올해 세운의 사업 표시와 점수를 근거로 올해 남은 기간의 운영법을 써 주세요.")),
        P("b8_risk", "위기가 오기 쉬운 해 대비하기",
          slot=S("b8_risk", "앞으로 5년 가운데 경쟁·지출이나 자리 변동 표시가 있는 해를 근거로 위기 대비(현금, 계약, 사람)를 써 주세요.")),
    ])
    section("10", [
        P("b9_months", "앞으로 12개월 월별 사업운", figure="grid", opener=True, span=2, grid=T.month_grid(th["months"], "사업 점수"),
          note="표시: 그 달에 들어오는 돈·상품·계약·경쟁의 기운이에요.",
          slot=S("b9_months", "표의 12개월 가운데 오픈·계약·홍보에 좋은 달과 조심할 달을 골라 달마다 할 일을 써 주세요.", FULL * 2 - 820)),
        P("b9_open", "오픈, 계약, 홍보에 좋은 달",
          slot=S("b9_open", "좋은 달과 조심할 달에 할 일과 피할 일을 시기별로 정리해 주세요.", FULL, "plan")),
        P("b9_season", "계절에 맞춘 운영",
          slot=S("b9_season", "용신의 계절과 조후를 근거로 계절마다 운영의 힘을 줄 곳과 쉬어 갈 곳을 써 주세요.")),
    ])
    section("11", [
        P("b10_graph", "나이별 사업운 그래프", figure="theme_graph", opener=True, note="대운(10년)마다 재성과 식상이 들어오면 점수가 올라가고, 경쟁·지출 기운이 들어오면 내려가요.",
          slot=S("b10_graph", "그래프에서 사업이 커지기 쉬운 시기와 다지는 시기를 나이로 짚어 주세요.", HALF - 80)),
        P("b10_now", "지금 지나는 10년의 사업운",
          slot=S("b10_now", "지금 대운의 글자를 근거로 이 10년 동안의 사업 흐름과 할 일을 써 주세요.")),
        P("b10_next", "다음 10년의 사업운",
          slot=S("b10_next", "다음 대운의 글자를 근거로 그 10년의 사업 흐름을 미리 쓰고, 지금부터 준비할 것을 써 주세요.")),
        P("b10_turn", "방향을 바꿀 때와 정리할 때",
          slot=S("b10_turn", "방향을 바꾸거나 정리하는 것이 나은 신호와 그때 손실을 줄이는 순서를 겁주지 않고 써 주세요.")),
    ])
    q = f["order"]["question"]
    section("12", [
        P("b11_stage", "지금 단계에 맞는 조언", opener=True,
          slot=S("b11_stage", f"사업 단계는 '{stage}', 먼저 보고 싶은 주제는 '{t['priority'] or '알 수 없음'}'이에요. 이 상황에서 앞으로 1년 동안 할 일을 사주 근거와 함께 순서대로 써 주세요.", FULL - 120)),
        P("b11_q", "질문에 대한 답", figure="question",
          slot=S("b11_q", (f"고객 질문: \"{q}\". 사주 근거를 들어 솔직하고 구체적으로 답해 주세요." if q else
                            "질문이 없으니, 이 단계의 사람이 가장 궁금해할 한 가지에 답해 주세요."), FULL - 200)),
        P("b11_more", "함께 생각해 볼 것", slot=S("b11_more", "질문과 이어지는 고민 2~3가지를 묻고 답해 주세요.", FULL, "qa")),
    ])
    section("13", [
        P("b12_key", "내 사업운 핵심 정리", opener=True,
          slot=S("b12_key", "이 책에서 가장 중요한 세 가지(사업 체질, 넓힐 때와 지킬 때, 꼭 지킬 원칙)를 한 문장 요약(lead)과 함께 정리해 주세요.", 640, "lead")),
        P("b12_check", "나의 사업 계획 점검표",
          slot=S("b12_check", "이 사주에 맞춰 사업 계획을 점검할 질문 10가지를 체크리스트로 써 주세요. 한 줄에 한 가지입니다.", 640, "checklist")),
        P("b12_plan", "1년 사업 계획", slot=S("b12_plan", "앞으로 1년을 시기별로 나눠 할 일과 피할 일을 정리해 주세요.", FULL, "plan")),
        P("b12_lucky", "사업을 돕는 색·숫자·방향", figure="lucky",
          slot=S("b12_lucky", "용신 기운을 근거로 간판·명함·로고 색, 숫자, 방향, 사업장 정리법을 써 주세요.", HALF)),
        P("b12_worry", "사업 걱정에 대한 답", span=2,
          slot=S("b12_worry", "이 사람이 가지기 쉬운 사업 걱정(망하면 어떡하지, 손님이 줄면, 사람이 떠나면, 지금 확장해도 될까)마다 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'를 함께 답해 주세요.", FULL * 2 - 60)),
        P("b12_last", "마지막 조언",
          slot=S("b12_last", f"{name}님에게 전하는 마지막 조언을 담백하게 써 주세요. 이 사주가 사업에서 오래 갈 수 있는 이유를 근거로 말해 주고, 가장 먼저 할 한 가지를 짚어 주세요.", FULL - 120)),
    ])
    section("더보기", [P("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True)])
    return sections


def cross_sell_order(f: dict) -> list[str]:
    return ["wealth", "career"]
