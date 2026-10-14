"""건강운 리포트(50쪽 이상): 오행 체질, 돌볼 곳, 잠·휴식·마음·음식·운동, 계절·나이·연도·월별 흐름, 한 주 실천표.

목차 원본: /mnt/project-files/plan/health-report-toc.md (2026-10-11, 인터뷰 주제 20가지 반영)
사이트 입력: 내 정보, 생활 리듬(rhythm, 필수), 돌아볼 습관(focus, 필수), 질문.
사이트 안내처럼 사주로 성향을 읽고 생활 습관을 돌아보는 책이다. 의학적 진단처럼 쓰지 않는다.
"""

from __future__ import annotations

from . import theme as T
from .facts import _ganzhi_elements
from .outline import FULL, HALF, _slot

FINAL_SECTION = "12"

SECTIONS = [
    ("1", "내 사주 한눈에 보기", "나의 사주표와 오행 균형"),
    ("2", "한눈에 보는 나의 건강운", "체질, 위험한 곳, 조심할 때"),
    ("3", "타고난 체질과 기운", "오행으로 보는 나의 몸"),
    ("4", "오행별로 조심할 곳", "생활 속 신호와 습관"),
    ("5", "지금의 생활 리듬", "하루와 일주일, 일과 활동의 균형"),
    ("6", "잠과 휴식", "수면과 쉬어 가는 시간"),
    ("7", "마음 돌보기", "스트레스와 감정 습관"),
    ("8", "먹고 움직이기", "음식과 운동"),
    ("9", "계절과 나이별 건강운", "계절 돌봄, 10년 흐름"),
    ("10", "연도별·월별 건강운", "조심할 해와 달"),
    ("11", "지금의 건강 습관과 질문에 대한 답", ""),
    ("12", "한 주 실천표와 마지막 조언", ""),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

STATIC = {
    "h_how_to_read": [
        "이 책은 태어난 날과 시간으로 계산한 사주의 오행 균형을 바탕으로, 나에게 맞는 생활 리듬과 잠, 휴식, 마음, 음식, 운동 습관을 돌아보는 책이에요.",
        "가장 궁금한 내용은 2장 '한눈에 보는 나의 건강운'에 먼저 모아 두었어요. 마지막 장에는 바로 따라 할 수 있는 한 주 실천표를 넣었어요.",
        "이 책은 사주로 타고난 성향을 읽고 생활 습관을 돌아보는 책이에요. 병을 진단하거나 치료법을 알려 주지 않아요. 몸이 불편하거나 걱정되는 증상이 있으면 꼭 병원 진료를 받으세요.",
        "사주 용어는 쉬운 말과 생활 장면으로 자세히 풀었고, 쪽 끝 '기억할 한 줄'에 그 쪽의 핵심을 한 문장으로 정리했어요.",
    ],
    "h_what_is_saju": [
        "사주(四柱)는 태어난 해, 달, 날, 시간의 네 기둥이에요. 여덟 글자는 모두 목(나무), 화(불), 토(흙), 금(쇠), 수(물)의 오행 가운데 하나예요.",
        "전통 명리에서는 오행마다 몸과 생활의 영역을 짝지어 봤어요. 넘치는 기운은 덜어 내고, 모자란 기운은 채우는 습관을 들이면 생활의 균형을 잡기 쉬워요.",
        "태어난 계절도 함께 봐요(조후). 추운 계절에 태어나면 따뜻함이, 더운 계절에 태어나면 시원함과 촉촉함이 필요하다고 봐요.",
    ],
}

# 전통 명리의 오행-몸 영역 짝(생활 습관을 돌아보는 기준)
BODY = {
    "목": {"area": "간·담, 눈, 근육과 힘줄", "sign": "눈의 피로, 어깨·목 뻣뻣함, 참았던 화", "mind": "답답함과 분노"},
    "화": {"area": "심장·혈액순환, 혀", "sign": "열감, 잠들기 어려움, 들뜬 마음", "mind": "조급함과 들뜸"},
    "토": {"area": "위장·소화, 입과 피부", "sign": "더부룩함, 불규칙한 식사, 군것질", "mind": "걱정과 생각 많음"},
    "금": {"area": "폐·호흡, 대장, 피부", "sign": "건조함, 호흡이 얕아짐, 장 리듬 흐트러짐", "mind": "슬픔과 서운함"},
    "수": {"area": "신장·방광, 귀, 허리와 뼈", "sign": "손발이 참, 쉽게 지침, 허리·무릎 뻐근함", "mind": "불안과 두려움"},
}

_SEASON = {"해": "겨울", "자": "겨울", "축": "겨울", "인": "봄", "묘": "봄", "진": "봄",
           "사": "여름", "오": "여름", "미": "여름", "신": "가을", "유": "가을", "술": "가을"}


def build(f: dict, result: dict, answers: dict, partner=None) -> dict:
    excess = [e["el"] for e in f["elements"] if e["status"] == "많음"]
    lacking = [e["el"] for e in f["elements"] if e["status"] == "부족"]
    good = {f["lucky"]["element"], *lacking}

    def mark(x: dict) -> dict:
        els = _ganzhi_elements(x["ganzhi"])
        fill = any(e in good for e in els)
        more = sum(e in excess for e in els)
        body = T.rel(x, "일주", T.CLASH)
        life = T.rel(x, "월주", T.CLASH)
        signs = [s for s, on in (("부족한 기운 채움", fill), ("넘치는 기운 더함", more > 0), ("몸의 자리 충", body), ("생활 자리 충", life)) if on]
        score = x["score"] + 4 * fill - 4 * more - 7 * body - 4 * life
        return {"t_score": T.clamp(score), "t_signs": signs}

    years, months, periods = T.marked(f, mark)
    month_branch = next(p for p in f["pillars"] if p["pillar"] == "월주")["branch"]
    season = _SEASON[month_branch]
    temp = {"겨울": "차가운 사주", "여름": "뜨거운 사주"}.get(season, "따뜻함과 서늘함 사이의 사주")
    data = {
        "rhythm": answers.get("rhythm", ""), "focus": answers.get("focus", ""),
        "body_type": f"{f['strength']['label']} · {temp}", "season": season, "temperature": temp,
        "excess": [{"el": e, **BODY[e]} for e in excess], "lacking": [{"el": e, **BODY[e]} for e in lacking],
        "care_years": [y["year"] for y in sorted(years, key=lambda y: y["t_score"])[:2]],
        "good_years": T.best(years, 2, lambda y: y["year"]),
        "best_months": T.best(months, 3, T.ym), "careful_months": T.worst(months, 3, T.ym),
        "body_map": BODY,
    }
    return {"label": "건강 재료", "data": data,
            "digest": {**data, **T.digest_rows(years, months, T.near(f, periods)),
                       "점수 설명": "t_score는 생활 리듬 점수: 높을수록 몸과 마음이 편안하기 쉬운 때. 부족한 기운이 들어오면 더하고, 넘치는 기운이 더해지거나 일지(몸의 자리)·월지(생활 자리)와 충하면 빼 계산"},
            "years": years, "months": months, "periods": periods}


STYLE = T.style("건강운", """
[건강운 규칙]
- 이 책은 사주로 성향을 읽고 생활 습관을 돌아보는 책입니다. 병명, 진단, 치료, 약, 영양제를 쓰지 않습니다.
- "~병에 걸린다", "~가 나쁘다"처럼 단정하지 않고 "~을 돌보면 좋아요", "~ 신호가 오면 쉬어 가세요"처럼 생활 습관으로 씁니다.
- 오행-몸 영역 짝(body_map)은 '전통 명리에서 짝지어 본 영역'이라고 밝히고 씁니다.
- 걱정되는 증상이 있으면 병원 진료를 받으라는 안내를 장마다 한 번 이하로 자연스럽게 넣습니다.
- 근거는 '건강 재료'(넘치는·부족한 오행, 조후 temperature, 생활 리듬 점수 t_score와 표시 t_signs)를 먼저 씁니다.
- 생활 리듬(rhythm)과 돌아보고 싶은 습관(focus)에 맞춰 씁니다.
""")


def build_outline(f: dict) -> list[dict]:
    th = f["theme"]
    t = th["data"]
    name = f["person"]["name"]
    sections: list[dict] = []

    def section(no: str, pages: list[dict]) -> None:
        title, subtitle = next((a, b) for n, a, b in SECTIONS if n == no)
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": []})

    P, S = T.tpage, _slot
    els = lambda xs: ", ".join(f"{K_NAME[x['el']]}({x['el']})" for x in xs) or "고른 편"
    section("1", [
        P("cover", "표지", figure="cover"),
        P("toc", "목차", figure="toc"),
        P("how_to_read", "이 책을 읽는 방법", static="h_how_to_read", opener=True),
        P("h_saju", "사주와 오행 짧게 알기", static="h_what_is_saju", figure="element_cycle"),
        P("chart", "나의 사주표", figure="pillars",
          slot=S("chart", f"{name}님의 여덟 글자를 소개하고, 일간이 몸과 마음을 쓰는 방식에서 어떻게 나타나는지 쉽게 설명해 주세요.", HALF)),
        P("h_bar", "나의 오행 균형", figure="elements_bar",
          slot=S("h_bar", "오행 막대에서 넘치는 기운과 모자란 기운을 짚고, 생활에서 어떤 모습으로 나타나기 쉬운지 써 주세요.", HALF - 40)),
    ])
    section("2", [
        P("h_glance", "한눈에 보는 나의 건강운", figure="kv", opener=True, rows=[
            ["타고난 체질", t["body_type"]], ["넘치는 기운", els(t["excess"])], ["모자란 기운", els(t["lacking"])],
            ["돌볼 영역", " / ".join(x["area"] for x in t["excess"] + t["lacking"]) or "고른 편이라 전체 리듬을 지켜요"],
            ["편안한 해", ", ".join(f"{y}년" for y in t["good_years"])], ["쉬어 갈 해", ", ".join(f"{y}년" for y in t["care_years"])],
            ["조심할 달", ", ".join(t["careful_months"]) or "—"],
        ], slot=S("h_glance", "표를 이어서 건강운의 핵심을 짧게 소개하고, 자세한 내용은 뒤 장에서 다룬다고 안내해 주세요.", HALF - 160)),
    ])
    section("3", [
        P("h3_open", "나의 체질 한 줄 요약", figure="opener", opener=True,
          slot=S("h3_open", f"{name}님의 체질을 '{t['body_type']}'를 바탕으로 한 문장 요약(lead)하고 근거를 쉽게 설명해 주세요.", 640, "lead")),
        P("h3_strong", "넘치는 기운이 만드는 습관",
          slot=S("h3_strong", "넘치는 오행이 생활에서 만드는 습관(과로, 열, 긴장 등)을 장면으로 쓰고 덜어 내는 방법을 붙여 주세요.")),
        P("h3_weak", "모자란 기운이 보내는 신호",
          slot=S("h3_weak", "모자란 오행이 생활에서 보내는 신호를 장면으로 쓰고 채우는 습관을 붙여 주세요.")),
        P("h3_temp", "차가움과 따뜻함",
          slot=S("h3_temp", f"태어난 계절({t['season']})과 조후({t['temperature']})를 근거로 체온, 옷차림, 실내 온도, 물 마시기 습관을 써 주세요.")),
    ])
    rows = [[f"{K_NAME[x['el']]}({x['el']})", f"{x['area']} · 신호: {x['sign']}"] for x in t["excess"] + t["lacking"]]
    section("4", [
        P("h4_open", "오행별로 돌볼 곳", figure="kv", opener=True, rows=rows or [["오행", "고르게 있어 한 곳보다 전체 리듬을 돌봐요"]],
          note="전통 명리에서 오행과 짝지어 본 몸의 영역이에요. 진단이 아니라 생활 습관을 돌아보는 참고예요.",
          slot=S("h4_open", "표의 영역을 왜 돌보면 좋은지 근거를 설명해 주세요. 진단처럼 쓰지 않습니다.", HALF - 80)),
        P("h4_fill", "모자란 기운 채우기",
          slot=S("h4_fill", "모자란 오행을 채우는 생활 습관(색, 음식, 활동, 공간, 시간대)을 구체적으로 써 주세요.")),
        P("h4_reduce", "넘치는 기운 덜어 내기",
          slot=S("h4_reduce", "넘치는 오행을 덜어 내는 생활 습관을 구체적으로 써 주세요.")),
        P("h4_check", "생활 속 신호 점검표",
          slot=S("h4_check", "이 사주에서 '쉬어 가세요' 신호로 볼 생활 속 변화 10가지를 체크리스트로 써 주세요. 걱정되면 병원 진료를 받으라는 말을 마지막 줄에 넣습니다.", 620, "checklist")),
    ])
    section("5", [
        P("h5_open", "지금 나의 생활 리듬", figure="health_notice", opener=True,
          slot=S("h5_open", f"고객이 고른 생활 리듬은 '{t['rhythm'] or '알 수 없음'}'이에요. 이 리듬이 이 사주와 어떻게 맞고 어긋나는지 한 문장(lead)으로 요약하고 설명해 주세요.", 440, "lead")),
        P("h5_day", "나에게 맞는 하루",
          slot=S("h5_day", "일간과 용신, 조후를 근거로 아침형·저녁형 경향과 하루 중 힘이 나는 시간, 쉬어야 하는 시간을 써 주세요.")),
        P("h5_balance", "일과 활동의 균형",
          slot=S("h5_balance", "십신 구성(관성=책임, 식상=활동, 비겁=체력)을 근거로 일과 활동, 휴식의 비율을 정하는 방법을 써 주세요.")),
        P("h5_care", "다른 사람 돌봄과 나 돌봄",
          slot=S("h5_care", "가족이나 일 때문에 나를 뒤로 미루기 쉬운 사주인지 근거로 쓰고, 나를 돌보는 시간을 지키는 방법을 써 주세요.")),
    ])
    section("6", [
        P("h6_open", "나의 잠", figure="opener", opener=True,
          slot=S("h6_open", "이 사주의 잠의 경향을 한 문장(lead)으로 요약하고 오행·조후 근거로 설명해 주세요.", 620, "lead")),
        P("h6_sleep", "잘 자는 습관",
          slot=S("h6_sleep", "잠들기 전 1시간 습관, 침실 환경(색, 온도, 빛), 아침에 일어나는 법을 이 사주에 맞춰 써 주세요.")),
        P("h6_rest", "나에게 맞는 쉬는 법",
          slot=S("h6_rest", "이 사주가 진짜로 쉬는 방법(혼자/함께, 움직이며/가만히, 자연/실내)과 짧은 휴식 방법을 써 주세요.")),
    ])
    section("7", [
        P("h7_open", "스트레스를 받는 방식", figure="opener", opener=True,
          slot=S("h7_open", "이 사주가 스트레스를 받는 방식을 한 문장(lead)으로 요약하고, 넘치는 오행의 감정(body_map의 mind)을 근거로 설명해 주세요.", 530, "lead")),
        P("h7_trigger", "마음이 흔들리는 순간",
          slot=S("h7_trigger", "합충과 십신 구성을 근거로 마음이 흔들리기 쉬운 상황(관계, 일, 돈)을 장면으로 써 주세요.")),
        P("h7_release", "마음을 푸는 방법",
          slot=S("h7_release", "용신 기운을 근거로 이 사주에 맞는 마음 푸는 방법 5가지를 구체적으로 써 주세요.")),
        P("h7_record", "감정 기록과 말하기 연습",
          slot=S("h7_record", "감정을 쌓아 두지 않도록 하루 5분 감정 기록법과 가까운 사람에게 마음을 말하는 연습을 써 주세요.")),
    ])
    section("8", [
        P("h8_open", "나에게 맞는 음식", figure="lucky_items", opener=True,
          slot=S("h8_open", "용신 기운의 음식과 조후를 근거로 평소 식단에서 늘릴 것과 줄일 것을 써 주세요. 약이나 영양제는 권하지 않습니다.", HALF)),
        P("h8_eat", "식사 습관",
          slot=S("h8_eat", "식사 시간, 속도, 야식·군것질 습관을 이 사주에 맞춰 장면과 함께 써 주세요.")),
        P("h8_move", "나에게 맞는 운동",
          slot=S("h8_move", "오행과 신강·신약을 근거로 맞는 운동의 종류(강도, 혼자/함께, 실내/야외)와 시작하는 방법을 써 주세요.")),
        P("h8_daily", "일상에서 몸 쓰기",
          slot=S("h8_daily", "운동할 시간이 없을 때 일상에서 할 수 있는 몸 쓰기 습관(걷기, 스트레칭, 자세)을 이 사주에 맞춰 써 주세요.")),
    ])
    section("9", [
        P("h9_season", "계절별 돌봄", opener=True,
          slot=S("h9_season", "봄·여름·가을·겨울마다 이 사주가 조심할 점과 돌봄 습관을 오행 근거로 써 주세요.", FULL - 120)),
        P("h9_graph", "나이별 건강운 그래프", figure="theme_graph", note="대운(10년)마다 모자란 기운이 들어오면 점수가 오르고, 넘치는 기운이나 충이 들어오면 내려가요.",
          slot=S("h9_graph", "그래프에서 몸과 마음이 편안한 시기와 쉬어 갈 시기를 나이로 짚어 주세요.", HALF - 80)),
        P("h9_now", "지금 지나는 10년",
          slot=S("h9_now", "지금 대운의 글자를 근거로 이 10년 동안 생활 리듬에서 돌볼 점과 할 일을 써 주세요.")),
        P("h9_next", "다음 10년",
          slot=S("h9_next", "다음 대운의 글자를 근거로 그 10년의 생활 리듬을 미리 쓰고, 지금부터 들일 습관을 써 주세요.")),
    ])
    section("10", [
        P("h10_years", "앞으로 5년 건강운", figure="grid", opener=True, span=2, grid=T.year_grid(th["years"], t["good_years"], "리듬 점수"),
          slot=S("h10_years", "표의 5년을 한 해씩 문단으로 써 주세요(그해 표시 근거, 생활 리듬, 돌볼 점).", FULL * 2 - 460)),
        P("h10_months", "앞으로 12개월 월별 건강운", figure="grid", span=2, grid=T.month_grid(th["months"], "리듬 점수"),
          note="표시: 그 달에 들어오는 기운이 내 오행 균형에 주는 영향이에요.",
          slot=S("h10_months", "표의 12개월 가운데 편안한 달과 쉬어 갈 달을 골라 달마다 생활 습관을 써 주세요.", FULL * 2 - 820)),
        P("h10_check", "쉬어 갈 때와 검진 챙길 때",
          slot=S("h10_check", "쉬어 갈 해와 달을 근거로 일정을 줄이는 방법과, 정기 건강검진을 챙기기 좋은 때를 써 주세요. 진단처럼 쓰지 않습니다.")),
    ])
    q = f["order"]["question"]
    section("11", [
        P("h11_focus", "돌아보고 싶은 습관에 대한 조언", opener=True,
          slot=S("h11_focus", f"고객이 돌아보고 싶은 습관은 '{t['focus'] or '알 수 없음'}'이에요. 이 습관을 바꾸는 방법을 사주 근거와 함께 단계별로 써 주세요.", FULL - 120)),
        P("h11_q", "질문에 대한 답", figure="question",
          slot=S("h11_q", (f"고객 질문: \"{q}\". 사주 근거와 생활 습관 중심으로 솔직하고 구체적으로 답해 주세요. 진단처럼 쓰지 않습니다." if q else
                            "질문이 없으니, 이 생활 리듬의 사람이 가장 궁금해할 한 가지에 답해 주세요."), FULL - 200)),
        P("h11_more", "함께 생각해 볼 것", slot=S("h11_more", "생활 습관에 관한 질문 2~3가지를 묻고 답해 주세요.", FULL, "qa")),
    ])
    section("12", [
        P("h12_key", "내 건강운 핵심 정리", opener=True,
          slot=S("h12_key", "이 책에서 가장 중요한 세 가지(나의 체질, 돌볼 곳, 쉬어 갈 때)를 한 문장 요약(lead)과 함께 정리해 주세요.", 640, "lead")),
        P("h12_week", "한 주의 작은 실천표",
          slot=S("h12_week", "월요일부터 일요일까지 하루 한 가지씩 할 일과 피할 일을 정리해 주세요(when=요일).", 650, "plan")),
        P("h12_habit", "오늘부터 할 돌봄 습관", slot=S("h12_habit", "오늘부터 실천할 돌봄 습관 10가지를 체크리스트로 써 주세요. 한 줄에 한 가지입니다.", 600, "checklist")),
        P("h12_lucky", "나를 돕는 색·방향·공간", figure="lucky",
          slot=S("h12_lucky", "용신 기운을 근거로 옷, 침실, 책상에 쓸 색과 방향, 공간 정리법을 써 주세요.", HALF)),
        P("h12_worry", "몸과 마음 걱정에 대한 답", span=2,
          slot=S("h12_worry", "이 사람이 가지기 쉬운 걱정(늘 피곤해, 잠을 못 자, 나이 들수록 걱정돼, 나를 돌볼 시간이 없어)마다 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'를 함께 답해 주세요.", FULL * 2 - 60)),
        P("h12_last", "마지막 조언",
          slot=S("h12_last", f"{name}님에게 전하는 마지막 조언을 따뜻하지만 담백하게 써 주세요. 이 사주의 회복하는 힘을 근거로 말해 주고, 가장 먼저 할 한 가지를 짚어 주세요.", FULL - 120)),
    ])
    section("더보기", [P("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True)])
    return sections


K_NAME = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}


def cross_sell_order(f: dict) -> list[str]:
    return ["lifetime"]
