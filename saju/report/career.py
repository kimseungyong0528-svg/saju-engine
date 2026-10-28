"""직업·이직운 리포트(50쪽 이상): 일하는 스타일, 맞는 직무, 조직 성향, 이직·승진 시기.

목차 원본: /mnt/project-files/plan/career-report-toc.md (2026-10-11, 인터뷰 주제 20가지 반영)
사이트 입력: 내 정보, 가장 큰 고민(concern), 질문.
"""

from __future__ import annotations

from . import theme as T
from .outline import FULL, HALF, _slot

FINAL_SECTION = "12"

SECTIONS = [
    ("1", "내 사주 한눈에 보기", "나의 사주표와 일의 운명"),
    ("2", "한눈에 보는 나의 직업운", "나에게 맞는 일, 이직해야 할 때"),
    ("3", "나는 어떻게 일하는 사람일까", "나의 일하는 스타일과 강점"),
    ("4", "나에게 맞는 일", "어울리는 직무와 분야"),
    ("5", "나는 어떤 곳에서 일하게 될까", "회사, 공공기관, 프리랜서, 창업"),
    ("6", "함께 일하는 사람들", "상사, 동료, 후배"),
    ("7", "이직과 움직일 때", "연도별 직업운, 월별 직업운"),
    ("8", "승진과 인정", "실력이 빛나는 시기와 연봉"),
    ("9", "공부와 자격", "나를 키우는 배움"),
    ("10", "나이별 직업운", "10년마다 달라지는 커리어"),
    ("11", "지금 나의 고민과 질문에 대한 답", ""),
    ("12", "나의 다음 선택과 마지막 조언", ""),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

STATIC = {
    "c_how_to_read": [
        "이 책은 태어난 날과 시간으로 계산한 사주를 바탕으로, 일하는 스타일부터 맞는 직무, 일하기 좋은 곳, 이직과 승진에 좋은 시기까지 순서대로 풀어 놓은 책이에요.",
        "가장 궁금한 내용은 2장 '한눈에 보는 나의 직업운'에 먼저 모아 두었어요. 자세한 이유와 방법은 뒤의 장에서 하나씩 설명해요.",
        "사주는 직업을 하나로 정해 주지 않아요. 내가 힘을 쓰기 쉬운 방식과 환경, 움직이기 좋은 때를 알려 줘요. 같은 직업 안에서도 맞는 자리를 고르는 데 써 주세요.",
        "사주 용어는 쉬운 말과 생활 장면으로 자세히 풀었고, 쪽 끝 '기억할 한 줄'에 그 쪽의 핵심을 한 문장으로 정리했어요.",
    ],
    "c_what_is_saju": [
        "사주(四柱)는 태어난 해, 달, 날, 시간의 네 기둥이에요. 기둥마다 위 글자(천간)와 아래 글자(지지)가 있어 모두 여덟 글자가 돼요.",
        "태어난 날의 위 글자(일간)가 '나 자신'이에요. 일은 다섯 가지 십신 무리로 봐요. 관성은 직장과 책임, 식상은 기술과 표현, 재성은 성과와 돈, 인성은 공부와 자격, 비겁은 독립과 경쟁이에요.",
        "태어난 달의 기둥은 사회생활의 자리예요. 운에서 이 자리를 흔드는 글자(충)가 들어오면 일의 자리가 바뀌기 쉬워요.",
    ],
}

_FIELD = {
    "목": "교육, 출판, 기획, 디자인, 복지·상담, 식물·환경",
    "화": "미디어, 마케팅·광고, IT 서비스, 뷰티, 공연·방송, 에너지",
    "토": "부동산, 행정·관리, 중개, 건설, 식품·농업, 인사",
    "금": "금융, 법·감사, 엔지니어링, 의료기기, 품질관리, 군·경찰",
    "수": "무역·물류, 연구, 데이터·IT 개발, 여행, 상담, 유통",
}
_ROLE = {
    "관성": "관리·행정, 공공 업무, 조직 운영, 규정·품질",
    "식상": "기획, 콘텐츠·디자인, 기술·개발, 강의·서비스",
    "재성": "영업, 재무·회계, 구매·유통, 사업 관리",
    "인성": "연구, 교육, 전문 자격 업무, 문서·법무",
    "비겁": "독립 전문직, 현장 리더, 스포츠·체력 쓰는 일, 프리랜서",
}

_CONCERN = {"첫 취업을 준비해요": "첫 취업", "이직을 고민해요": "이직", "다시 일을 시작하고 싶어요": "재취업",
            "창업을 생각해요": "창업", "지금 일이 맞는지 궁금해요": "적성 확인"}


def _style(f: dict) -> tuple[str, str]:
    c = {g: T.count(f, g) for g in T.GODS}
    if c["관성"] >= 1 and c["인성"] >= 1:   # 맛보기·결제 전 화면의 '관인상생'(saju/taster.py ca_flow)과 같은 기준(제1조항)
        return "조직에서 인정받는 형", "직장과 책임(관성)을 배움과 자격(인성)이 받쳐 주는 구조(관인상생)라서, 체계 있는 조직에서 단계를 밟아 올라갈 때 힘이 나요."
    if c["식상"] >= 2:
        return "기술과 표현으로 승부하는 형", "재능과 표현(식상)이 강해서, 내 손과 머리로 만든 결과물이 평가받는 일에서 힘이 나요."
    if c["비겁"] >= 3:
        return "내 판을 짜는 독립형", "나와 같은 기운(비겁)이 강해서, 남의 지시보다 내가 정한 방식으로 일할 때 힘이 나요."
    if c["재성"] >= 2:
        return "성과로 움직이는 형", "재물과 결과(재성)의 기운이 강해서, 숫자로 성과가 보이는 일에서 힘이 나요."
    if c["인성"] >= 2:
        return "배우고 가르치는 전문가형", "배움과 자격(인성)의 기운이 강해서, 깊이 아는 분야의 전문가가 될 때 힘이 나요."
    return "균형형", "십신이 고르게 있어서 여러 역할을 소화하는 편이에요. 경험을 쌓으며 가장 손에 맞는 역할을 좁혀 가면 좋아요."


def build(f: dict, result: dict, answers: dict, partner=None) -> dict:
    an = result["variants"][0]["analysis"]
    yeokma = {T.YEOKMA[an["pillars"][0]["branch"]], T.YEOKMA[T.day_of(f)["branch"]]}

    def mark(x: dict) -> dict:
        gwan, sik, ins = T.has(x, "관성"), T.has(x, "식상"), T.has(x, "인성")
        seat = T.rel(x, "월주", T.CLASH)
        move = x["ganzhi"][1] in yeokma
        signs = [s for s, on in (("직장·승진 기운", gwan), ("기술·성과 기운", sik), ("합격·문서 기운", ins),
                                 ("일 자리 변동", seat), ("이동 기운(역마)", move)) if on]
        score = x["score"] + 8 * gwan + 5 * sik + 5 * ins - 3 * seat
        return {"t_score": T.clamp(score), "t_signs": signs, "t_move": seat or move}

    years, months, periods = T.marked(f, mark)
    T.reveal_fix(result, "career", years)   # 제1조항: 결제 전 화면의 12년 지도와 같은 표시·방향
    T.reveal_fix(result, "career", months)
    style, style_text = _style(f)
    top_group = max(("관성", "식상", "재성", "인성", "비겁"), key=lambda g: T.count(f, g))
    move_years = T.good_rows(years, 12, lambda y: y["year"])   # 화면의 '자리의 별' 해
    screen = T.screen_score(f, result, "career")
    data = {
        "screen_score": screen,
        "concern": _CONCERN.get(answers.get("concern", ""), answers.get("concern", "")),
        "style": style, "style_text": style_text,
        "counts": {g: T.count(f, g) for g in T.GODS},
        "month_pillar": {k: next(p for p in f["pillars"] if p["pillar"] == "월주").get(k) for k in ("ganzhi", "stem_ten_god", "branch_ten_god")},
        "yeokma": "역마살" in f["shinsal_names"],
        "fields": _FIELD[f["lucky"]["element"]], "roles": _ROLE[top_group], "top_group": top_group,
        "org": "조직형(회사·공공기관)" if (T.count(f, "관성") >= 1 and T.count(f, "인성") >= 1)
               or T.count(f, "관성") >= max(T.count(f, "식상"), T.count(f, "비겁")) else "독립형(전문직·프리랜서·작은 조직)",
        "move_years": move_years, "best_years": T.best(years, 12, lambda y: y["year"]),
        "best_months": T.best(months, 3, T.ym), "careful_months": T.worst(months, 3, T.ym),
    }
    return {"label": "직업 재료", "data": data,
            "digest": {**data, **T.digest_rows(years, months, T.near(f, periods)),
                       "점수 설명": "t_score는 일의 흐름 점수: 운의 흐름 점수에 관성·식상·인성이 들어오면 더하고 일 자리(월지) 충은 조금 빼 계산. t_signs의 '일 자리 변동', '이동 기운'은 이직 신호"},
            "years": years, "months": months, "periods": periods}


STYLE = T.style("직업·이직운", """
[직업·이직운 규칙]
- 독자는 취업, 이직, 재취업, 창업, 적성을 고민하는 사람입니다. 현실적인 직무 이름과 장면으로 씁니다.
- 근거는 '직업 재료'(일하는 형 style, 십신 개수, 맞는 분야 fields와 역할 roles, 일의 흐름 점수 t_score와 표시 t_signs, 이직하기 좋은 해)를 먼저 씁니다.
- 직업은 하나로 단정하지 않고 '이런 조건의 일'과 예시 여러 개로 씁니다.
- 회사 이름, 연봉 액수, 합격을 장담하지 않습니다.
- 고객의 고민(concern)에 맞춰 씁니다(첫 취업, 이직, 재취업, 창업, 적성 확인).
""")


def build_outline(f: dict) -> list[dict]:
    th = f["theme"]
    t = th["data"]
    c = t["counts"]
    name = f["person"]["name"]
    concern = t["concern"] or "알 수 없음"
    sections: list[dict] = []

    def section(no: str, pages: list[dict]) -> None:
        title, subtitle = next((a, b) for n, a, b in SECTIONS if n == no)
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": []})

    P, S = T.tpage, _slot
    mp = t["month_pillar"]
    section("1", [
        P("cover", "표지", figure="cover"),
        P("toc", "목차", figure="toc"),
        P("how_to_read", "이 책을 읽는 방법", static="c_how_to_read", opener=True),
        P("c_saju", "사주와 일 짧게 알기", static="c_what_is_saju", figure="element_cycle"),
        P("chart", "나의 사주표", figure="pillars",
          slot=S("chart", f"{name}님의 여덟 글자를 소개하고, 일간이 일하는 태도에서 어떻게 나타나는지 쉽게 설명해 주세요.", HALF)),
        P("c_letters", "일을 보는 글자", figure="kv", rows=[
            ["관성(직장·책임)", f"{c['관성']}개"], ["식상(기술·표현)", f"{c['식상']}개"], ["재성(성과·돈)", f"{c['재성']}개"],
            ["인성(공부·자격)", f"{c['인성']}개"], ["비겁(독립·경쟁)", f"{c['비겁']}개"],
            ["일 자리(월주)", f"{mp['ganzhi']} · {mp['stem_ten_god']} · {mp['branch_ten_god']}"],
        ], slot=S("c_letters", "표의 글자가 일에서 각각 무엇을 뜻하는지, 이 사주에서는 어떻게 있는지 설명해 주세요.", HALF - 80)),
    ])
    section("2", [
        P("c_glance", "한눈에 보는 나의 직업운", figure="kv", opener=True, rows=[
            T.screen_row(t["screen_score"], t.get("seen", True)),
            ["일하는 형", t["style"]], ["어울리는 역할", t["roles"]], ["어울리는 분야", t["fields"]],
            ["맞는 환경", t["org"]], ["움직이기 좋은 해", ", ".join(f"{y}년" for y in t["move_years"]) or "앞으로 12년 안에는 뚜렷하지 않아요"],
            ["가까운 좋은 달", ", ".join(t["best_months"])],
        ], slot=S("c_glance", "표를 이어서 직업운의 핵심을 짧게 소개하고, 자세한 내용은 뒤 장에서 다룬다고 안내해 주세요.", HALF - 120)),
    ])
    section("3", [
        P("c3_open", "나의 일하는 형", figure="opener", opener=True,
          slot=S("c3_open", f"{name}님의 일하는 형을 '{t['style']}'로 한 문장 요약(lead)하고, 근거({t['style_text']})를 쉽게 풀어 주세요.", 570, "lead")),
        P("c3_team", "혼자 할까, 함께 할까",
          slot=S("c3_team", "비겁·관성·식상 구성으로 혼자 일할 때와 팀으로 일할 때 각각의 모습을 장면으로 쓰고, 이 사람에게 맞는 일 방식을 써 주세요.")),
        P("c3_lead", "앞에 설까, 뒤에서 받칠까",
          slot=S("c3_lead", "격국과 신강·신약을 근거로 리더 역할과 참모 역할 가운데 어디서 더 빛나는지 장면과 함께 써 주세요.")),
        P("c3_good_bad", "일할 때 나의 강점과 약점",
          slot=S("c3_good_bad", "일할 때 강점 3가지와 약점 2~3가지를 근거와 함께 쓰고, 약점마다 보완법을 붙여 주세요.")),
    ])
    section("4", [
        P("c4_open", "어울리는 역할과 분야", figure="kv", opener=True, rows=[
            ["가장 강한 십신 무리", T.GROUP_WORD[t["top_group"]]], ["어울리는 역할", t["roles"]],
            ["도움 되는 기운", f"{f['lucky']['element_name']}({f['lucky']['element']})"], ["어울리는 분야", t["fields"]],
        ], slot=S("c4_open", "표의 역할과 분야가 왜 맞는지 근거를 설명해 주세요.", HALF)),
        P("c4_top", "잘 맞는 직무 다섯 가지",
          slot=S("c4_top", "역할과 분야를 조합해 잘 맞는 직무 5가지를 골라, 각각 왜 맞는지와 그 일에서의 하루 장면을 짧게 써 주세요.", FULL, "bullets")),
        P("c4_field", "분야별로 보는 나의 자리",
          slot=S("c4_field", "어울리는 분야마다 이 사람이 맡으면 좋은 자리(예: 같은 IT라도 기획/개발/운영)를 구체적으로 써 주세요.")),
        P("c4_avoid", "피하면 좋은 일과 환경",
          slot=S("c4_avoid", "넘치는 기운과 약한 기운을 근거로 힘이 빠지기 쉬운 일과 환경(업무 방식, 조직 문화, 근무 형태)을 쓰고, 어쩔 수 없이 해야 할 때의 방법을 써 주세요.")),
    ])
    section("5", [
        P("c5_open", "조직형일까 독립형일까", figure="opener", opener=True,
          slot=S("c5_open", f"이 사람이 '{t['org']}'에 가까운 이유를 한 문장(lead)으로 말하고 근거를 설명해 주세요.", 620, "lead")),
        P("c5_where", "회사의 크기와 문화",
          slot=S("c5_where", "대기업, 공공기관, 중소기업, 스타트업, 프리랜서 가운데 이 사주에 맞는 순서와 이유, 회사 문화(체계, 속도, 자율)를 고르는 기준을 써 주세요.")),
        P("c5_own", "창업은 해도 될까",
          slot=S("c5_own", "재성·식상·비겁 구성과 다가오는 운으로 창업이나 독립에 맞는지, 한다면 언제 어떤 방식이 맞는지 쓰고, 자세한 내용은 사업운에서 본다고 한 줄 안내해 주세요.")),
    ])
    section("6", [
        P("c6_open", "직장에서 나는 어떤 사람으로 보일까", figure="opener", opener=True,
          slot=S("c6_open", "직장에서 다른 사람 눈에 비치는 모습을 한 문장(lead)으로 요약하고 근거를 설명해 주세요.", 620, "lead")),
        P("c6_boss", "상사와 지내는 법",
          slot=S("c6_boss", "관성(윗사람)과의 관계를 근거로 상사와 부딪히기 쉬운 장면과 인정받는 보고·소통 방법을 써 주세요.")),
        P("c6_peer", "동료와 후배와 지내는 법",
          slot=S("c6_peer", "비겁(동료)·식상(후배) 관계를 근거로 동료와 경쟁할 때, 후배를 이끌 때의 모습과 방법을 써 주세요.")),
        P("c6_credit", "내 성과를 인정받는 법",
          slot=S("c6_credit", "이 사람이 성과를 내고도 인정받지 못하기 쉬운 이유와, 일의 결과를 보이게 만드는 구체적인 방법을 써 주세요.")),
    ])
    section("7", [
        P("c7_open", "이직 신호 읽기", figure="kv", opener=True, rows=[
            ["움직이기 좋은 해", ", ".join(f"{y}년" for y in t["move_years"]) or "앞으로 12년 안에는 뚜렷하지 않아요"],
            ["일 자리 변동이 드는 달", ", ".join(T.ym(m) for m in th["months"] if "일 자리 변동" in m["t_signs"]) or "없음"],
            ["이동 기운(역마)", "타고난 사주에 있어요" if t["yeokma"] else "운에서 들어올 때 움직임이 커져요"],
        ], slot=S("c7_open", "표를 근거로 이 사람에게 이직 신호가 언제 드는지 설명해 주세요.", HALF)),
        P("c7_years", "앞으로 12년 직업운", figure="grid", span=3, grid=T.year_grid(th["years"], t["move_years"], "일의 흐름"),
          slot=S("c7_years", "표의 12년을 한 해씩 짧은 문단으로 써 주세요(그해 표시 근거, 일의 흐름, 이직·승진·공부 가운데 할 일).", FULL * 3 - 460)),
        P("c7_months", "앞으로 12개월 월별 직업운", figure="grid", span=2, grid=T.month_grid(th["months"], "일의 흐름"),
          note="표시: 그 달에 들어오는 직장·기술·문서·이동의 기운이에요.",
          slot=S("c7_months", "표의 12개월 가운데 지원·면접·이직 제안에 좋은 달과 조심할 달을 골라 달마다 할 일을 써 주세요.", FULL * 2 - 820)),
        P("c7_stay", "남을까 떠날까, 판단 기준",
          slot=S("c7_stay", "이 사주에 맞는 '지금 회사에 남을 때'와 '떠날 때'의 기준을 각각 5가지로 써 주세요. 사주 근거를 함께 씁니다.", FULL, "qa")),
    ])
    section("8", [
        P("c8_open", "실력이 빛나는 시기", figure="opener", opener=True,
          slot=S("c8_open", "관성·인성이 들어오는 해와 대운을 근거로 승진과 인정이 오기 쉬운 시기를 한 문장(lead)으로 요약하고 설명해 주세요.", 620, "lead")),
        P("c8_promo", "승진과 평가를 잡는 법",
          slot=S("c8_promo", "승진 시기 전에 준비할 일과 평가 시즌에 할 일을 이 사주에 맞춰 구체적으로 써 주세요.")),
        P("c8_pay", "연봉 협상과 돈",
          slot=S("c8_pay", "재성·식상 구성을 근거로 연봉 협상에 유리한 때와 말하는 방법, 일과 돈의 균형을 써 주세요. 금액은 쓰지 않습니다.")),
        P("c8_exam", "면접과 시험운",
          slot=S("c8_exam", "인성·관성이 드는 달과 해를 근거로 면접·시험에 좋은 때를 쓰고, 이 사주에 맞는 면접 태도와 준비법을 써 주세요.")),
    ])
    section("9", [
        P("c9_open", "나에게 도움 되는 배움", figure="opener", opener=True,
          slot=S("c9_open", f"인성 {c['인성']}개와 용신을 근거로 이 사람에게 도움이 되는 배움의 방향을 한 문장(lead)으로 요약하고 설명해 주세요.", 560, "lead")),
        P("c9_cert", "도움 되는 공부와 자격",
          slot=S("c9_cert", "어울리는 역할과 분야에 맞춰 도움 되는 공부·자격·경력 쌓기 예시를 5가지 이상 쓰고, 언제 시작하면 좋은지 써 주세요.")),
        P("c9_how", "나에게 맞는 공부 방법",
          slot=S("c9_how", "이 사주에 맞는 공부 방식(혼자/함께, 짧게/길게, 시간대, 기록법)을 장면과 함께 써 주세요.")),
    ])
    section("10", [
        P("c10_graph", "나이별 직업운 그래프", figure="theme_graph", opener=True, note="대운(10년)마다 관성·식상·인성이 들어오면 점수가 올라가요.",
          slot=S("c10_graph", "그래프에서 커리어가 크게 움직이는 시기와 쌓아 가는 시기를 나이로 짚어 주세요.", HALF - 80)),
        P("c10_now", "지금 지나는 10년의 직업운",
          slot=S("c10_now", "지금 대운의 글자를 근거로 이 10년 동안의 커리어 흐름과 할 일을 써 주세요.")),
        P("c10_next", "다음 10년의 직업운",
          slot=S("c10_next", "다음 대운의 글자를 근거로 그 10년의 커리어 흐름을 미리 쓰고, 지금부터 준비할 것을 써 주세요.")),
        P("c10_burnout", "지칠 때의 신호와 쉬어 갈 때",
          slot=S("c10_burnout", "넘치는 기운과 점수가 낮은 시기를 근거로 번아웃 신호와 쉬어 갈 때, 쉬는 동안 할 일을 써 주세요.")),
    ])
    q = f["order"]["question"]
    section("11", [
        P("c11_concern", "지금 내 고민에 맞는 조언", opener=True,
          slot=S("c11_concern", f"고객의 고민은 '{concern}'이에요. 이 고민에 맞춰 앞으로 1년 동안 할 일을 사주 근거와 함께 순서대로 써 주세요.", FULL - 120)),
        P("c11_q", "질문에 대한 답", figure="question",
          slot=S("c11_q", (f"고객 질문: \"{q}\". 사주 근거를 들어 솔직하고 구체적으로 답해 주세요." if q else
                            "질문이 없으니, 이 고민을 가진 사람이 가장 궁금해할 한 가지에 답해 주세요."), FULL - 200)),
        P("c11_more", "함께 생각해 볼 것", slot=S("c11_more", "고민과 이어지는 질문 2~3가지를 묻고 답해 주세요.", FULL, "qa")),
    ])
    section("12", [
        P("c12_key", "내 직업운 핵심 정리", opener=True,
          slot=S("c12_key", "이 책에서 가장 중요한 세 가지(나에게 맞는 일, 움직일 때, 키울 힘)를 한 문장 요약(lead)과 함께 정리해 주세요.", 640, "lead")),
        P("c12_pitch", "나의 강점을 보여 주는 법",
          slot=S("c12_pitch", "자기소개서, 면접, 포트폴리오, 평가 면담에서 이 사주의 강점을 보여 주는 문장 예시와 방법을 써 주세요.")),
        P("c12_plan", "1년 커리어 계획", slot=S("c12_plan", "앞으로 1년을 시기별로 나눠 할 일과 피할 일을 정리해 주세요.", FULL, "plan")),
        P("c12_lucky", "일에 힘을 주는 색·방향·공간", figure="lucky",
          slot=S("c12_lucky", "용신 기운을 근거로 면접 옷차림 색, 책상 방향, 일하는 공간 정리법을 써 주세요.", HALF)),
        P("c12_todo", "오늘부터 할 일 목록", slot=S("c12_todo", "오늘부터 실천할 일 10가지를 체크리스트로 써 주세요. 한 줄에 한 가지입니다.", 600, "checklist")),
        P("c12_worry", "일 걱정에 대한 답", span=2,
          slot=S("c12_worry", "이 사람이 가지기 쉬운 일 걱정(늦은 건 아닐까, 이 길이 맞을까, 또 실패하면, 나이가 많은데)마다 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'를 함께 답해 주세요.", FULL * 2 - 60)),
        P("c12_last", "마지막 조언",
          slot=S("c12_last", f"{name}님에게 전하는 마지막 조언을 담백하게 써 주세요. 이 사주가 일에서 빛날 이유를 근거로 말해 주고, 가장 먼저 할 한 가지를 짚어 주세요.", FULL - 120)),
    ])
    section("더보기", [P("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True)])
    return sections


def cross_sell_order(f: dict) -> list[str]:
    return ["business", "wealth"] if f["theme"]["data"]["concern"] == "창업" else ["wealth", "business"]
