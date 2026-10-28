"""2027 신년운세 리포트(50쪽 이상): 2027년 정미년 한 해의 흐름, 분야별 운, 1월~12월 월별 운세, 실천 계획.

목차 원본: /mnt/project-files/plan/newyear-report-toc.md (사장님 확정 2026-10-13, "새로운 일 ,"만 "새로운 일,"로 붙임)
주제 20가지: /mnt/project-files/plan/newyear-interview-topics.md
사이트 입력: 내 정보, 가장 궁금한 분야(focus: 일과 직장 / 돈과 재물 / 연애와 결혼 / 건강 / 한 해 전체), 질문(question, 선택).

다른 주제 사주와 달리 '주문한 날부터 12개월'이 아니라 2027년(TARGET_YEAR)을 본다.
- 세운: saju.luck.sewoon(fp, [2027]) → 정미(丁未)년. 입춘(2027-02-04)부터 2027년의 기운이에요.
- 월운: 달력 1월~12월에 맞춰 12달을 싣는다. 사주의 달은 절기(소한·입춘·경칩…)가 드는 날 바뀐다.
  1월은 2026년 운의 마지막 달(축월, 1/5 소한부터), 2월~12월은 saju.luck.wolwoon(fp, 2027)의 인월(2/4 입춘부터)~자월(12/7 대설부터).
  2028년 1월 소한부터는 다음 해 흐름이라 싣지 않는다(달마다 '2월(인월, 2/4~)'처럼 이름을 붙인다).
- 이 상품은 f["months"]를 2027년 12달로 바꿔 둔다(글쓰기 재료와 글 검사가 같은 달을 보게).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from . import knowledge as K
from . import theme as T
from .facts import luck_rater, month_row
from .outline import FULL, HALF, _slot
from ..constants import BRANCHES, STEMS

TARGET_YEAR = 2027
FINAL_SECTION = "12"

SECTIONS = [
    ("1", "내 사주 한눈에 보기", "나의 2027년 운명과 사주표"),
    ("2", "한눈에 보는 나의 2027년", "한마디 요약, 전체 점수, 좋은 운과 나쁜 운 정리"),
    ("3", "2027년 정미년과 내 사주", "새해 기운과의 궁합, 대운과 삼재 확인"),
    ("4", "일과 직장운", "평가와 승진, 이직과 새 일 시작하기 좋은 시기"),
    ("5", "재물운", "큰 돈이 들어오는 시기와 빠져 나가는 시기, 투자는 해야할까?"),
    ("6", "사업·부업운과 문서운", "새로운 일, 계약, 집과 부동산을 시작할 때"),
    ("7", "연애운과 결혼운", "새로운 사랑이 찾아오는 시기, 부부 관계"),
    ("8", "사람운과 조심할 일", "나를 도와줄 은인은 누구일까, 구설·손재·관재"),
    ("9", "건강운", "조심할 질병과 위험한 시기"),
    ("10", "이사·여행·시험운", "움직이기 좋은 시기, 공부와 자격증"),
    ("11", "1월~12월 월별 운세", "월별 해야할 일, 나에게 가장 좋은 달과 조심할 달"),
    ("12", "2027년 실천 계획과 마지막 조언", "행운의 색·방향·숫자, 꼭 해야 할 일과 피할 일, 놓치면 안되는 연초 계획"),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]

STATIC = {
    "ny_how_to_read": [
        "이 책은 태어난 날과 시간으로 계산한 사주에 2027년 정미(丁未)년의 기운을 맞춰 보고, 일, 돈, 연애, 사람, 건강, 이사와 시험까지 한 해의 흐름을 정리한 책이에요.",
        "가장 궁금한 내용은 2장 '한눈에 보는 나의 2027년'에 먼저 모아 두었어요. 1월부터 12월까지 달마다 할 일은 11장에, 바로 따라 할 실천 계획은 12장에 있어요.",
        "책에 나오는 점수와 좋은 달, 조심할 달은 모두 사주 글자로 계산한 값이에요. 좋은 시기에는 미뤄 둔 일을 시작하고, 조심할 시기에는 큰 결정을 한 번 더 확인하는 데 써 주세요.",
        "사주 용어는 쉬운 말과 생활 장면으로 자세히 풀었고, 쪽 끝 '기억할 한 줄'에 그 쪽의 핵심을 한 문장으로 정리했어요.",
    ],
    "ny_what_is_saju": [
        "사주(四柱)는 태어난 해, 달, 날, 시간의 네 기둥이에요. 기둥마다 위 글자(천간)와 아래 글자(지지)가 있어 모두 여덟 글자가 돼요. 태어난 날의 위 글자(일간)가 '나 자신'이에요.",
        "해마다 들어오는 운을 세운(歲運)이라고 해요. 2027년의 세운은 정미(丁未)예요. 정(丁)은 불(화)의 글자이고, 미(未)는 흙(토)의 글자이며 띠로는 양이에요.",
        "사주의 해는 1월 1일이 아니라 입춘(2027년 2월 4일)에 바뀌어요. 사주의 달도 매달 1일이 아니라 절기가 드는 날(대개 4일~8일)에 바뀌어요. 그래서 이 책의 '2월'은 2월 4일 입춘부터 3월 5일까지를 뜻해요.",
    ],
}

FOCUS = {"일과 직장": "4", "돈과 재물": "5", "연애와 결혼": "7", "건강": "9", "한 해 전체": "2"}
AREAS = [("work", "일·직장"), ("money", "재물"), ("biz", "사업·부업·문서"), ("love", "연애·결혼"),
         ("people", "사람·구설"), ("health", "건강"), ("move", "이사·여행·시험")]
AREA_NAME = dict(AREAS)

# 삼재: 띠(태어난 해 지지)의 삼합 무리 → 삼재가 드는 세 해의 지지(들삼재, 눌삼재, 날삼재 순서)
SAMJAE = {("해", "묘", "미"): ("사", "오", "미"), ("인", "오", "술"): ("신", "유", "술"),
          ("사", "유", "축"): ("해", "자", "축"), ("신", "자", "진"): ("인", "묘", "진")}
SAMJAE_KIND = ("들삼재", "눌삼재", "날삼재")
SAMJAE_TEXT = {"들삼재": "삼재가 들어오는 첫해예요. 새로 벌이는 일보다 지금 가진 것을 지키는 쪽이 좋아요.",
               "눌삼재": "삼재가 머무는 둘째 해예요. 무리한 확장과 큰 보증을 피하고 하던 일을 다지는 해예요.",
               "날삼재": "삼재가 나가는 셋째 해예요. 앞의 두 해보다 가볍게 보고, 마무리와 정리를 잘하면 되는 해예요."}

_SEASON = {"해": "겨울", "자": "겨울", "축": "겨울", "인": "봄", "묘": "봄", "진": "봄",
           "사": "여름", "오": "여름", "미": "여름", "신": "가을", "유": "가을", "술": "가을"}

# 전통 명리의 오행-몸 영역 짝(건강운 상품과 같은 기준, 진단이 아니라 생활 습관을 돌아보는 기준)
BODY = {
    "목": {"area": "간·담, 눈, 근육과 힘줄", "sign": "눈의 피로, 어깨·목 뻣뻣함, 참았던 화"},
    "화": {"area": "심장·혈액순환, 혀", "sign": "열감, 잠들기 어려움, 들뜬 마음"},
    "토": {"area": "위장·소화, 입과 피부", "sign": "더부룩함, 불규칙한 식사, 군것질"},
    "금": {"area": "폐·호흡, 대장, 피부", "sign": "건조함, 호흡이 얕아짐, 장 리듬 흐트러짐"},
    "수": {"area": "신장·방광, 귀, 허리와 뼈", "sign": "손발이 참, 쉽게 지침, 허리·무릎 뻐근함"},
}
K_NAME = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}


def year_branch(year: int) -> str:
    return BRANCHES[(year - 4) % 12]


def year_ganzhi(year: int) -> str:
    return STEMS[(year - 4) % 10] + year_branch(year)


def samjae(birth_branch: str, year: int) -> dict:
    """그 해가 이 띠에게 삼재인지. 띠의 삼합 무리에 정해진 세 해 지지로 판단한다(해묘미 띠 → 사·오·미 해 등)."""
    group = next(g for g in SAMJAE if birth_branch in g)
    trio = SAMJAE[group]
    yb = year_branch(year)
    kind = SAMJAE_KIND[trio.index(yb)] if yb in trio else ""
    # 가까운 삼재 세 해: 지금 지나는 삼재(this_run)와 다음 삼재(next_run). 삼재는 12년마다 돌아온다
    starts = [y for y in range(year - 11, year + 13) if year_branch(y) == trio[0]]
    prev = max(y for y in starts if y <= year) if any(y <= year for y in starts) else None
    nxt = min(y for y in starts if y > year)
    in_now = prev is not None and year - prev <= 2
    return {
        "is_samjae": bool(kind), "kind": kind, "text": SAMJAE_TEXT.get(kind, ""),
        "group": "·".join(group), "years_branches": "·".join(trio),
        "this_run": [prev, prev + 1, prev + 2] if in_now else [],
        "next_run": [nxt, nxt + 1, nxt + 2],
    }


def _hits(f: dict, an: dict) -> dict:
    """운의 지지가 이 글자면 그 신살의 글자가 들어오는 것(역마·도화는 태어난 해·날 지지 기준, 귀인은 일간 기준)."""
    from ..analysis import _CHEONEUL, _MUNCHANG
    yb, db = an["pillars"][0]["branch"], T.day_of(f)["branch"]
    ds = STEMS.index(f["day_master"]["stem"])
    return {"yeokma": sorted({T.YEOKMA[yb], T.YEOKMA[db]}), "peach": sorted({T.PEACH[yb], T.PEACH[db]}),
            "guiin": [BRANCHES[i] for i in _CHEONEUL[ds]], "munchang": BRANCHES[_MUNCHANG[ds]]}


def _roles(f: dict) -> dict:
    """오행마다 이 사주에서 맡은 역할(용신·희신·기신·넘치는 기운)."""
    cl = f.get("classics")
    yong = f["lucky"]["element"]
    hee = (cl["yongsin"].get("heesin") or []) if cl else [e for e in f["yongsin"].get("억부", []) if e != yong]
    gi = (cl["yongsin"].get("gisin") or []) if cl else []
    excess = f.get("elements_excess", [])
    out = {}
    for el in K.ELEMENT_ORDER:
        if el == yong:
            out[el] = "용신(나에게 가장 필요한 기운)"
        elif el in hee:
            out[el] = "희신(용신을 돕는 반가운 기운)"
        elif el in excess:
            out[el] = "넘치는 기운(이미 많아 덜어 낼 기운)"
        elif el in gi:
            out[el] = "기신(나에게 부담이 되는 기운)"
        else:
            out[el] = "보통(크게 돕지도 막지도 않는 기운)"
    return out


def _gz_elements(gz: str) -> list[str]:
    from .facts import _ganzhi_elements
    return _ganzhi_elements(gz)


def build(f: dict, result: dict, answers: dict, partner=None) -> dict:
    from .. import luck
    an = result["variants"][0]["analysis"]
    fp = T.fourpillars(result)
    rate = luck_rater(an)
    name = f["person"]["name"]
    male = f["person"]["sex"] == "male"
    strong = f["strength"]["label"] not in ("신약", "극신약")
    n_gwan, n_jae = T.count(f, "관성"), T.count(f, "재성")
    spouse = "재성" if male else "관성"
    hits = _hits(f, an)
    excess = [e["el"] for e in f["elements"] if e["status"] == "많음"]
    lacking = [e["el"] for e in f["elements"] if e["status"] == "부족"]
    good_el = {f["lucky"]["element"], *lacking}
    order_day = date.fromisoformat(f["order"]["date"])

    # 2027년 세운과 달력 1월~12월의 월운(1월은 2026년 운의 축월, 2월~12월은 2027년 운)
    sy = luck.sewoon(fp, [TARGET_YEAR])[0]
    year = {**sy, **rate(sy), "animal": K.BRANCH_ANIMAL[sy["ganzhi"][1]]}
    raw = [luck.wolwoon(fp, TARGET_YEAR - 1)[-1]] + luck.wolwoon(fp, TARGET_YEAR)
    raw = [m for m in raw if m["starts"][:4] == str(TARGET_YEAR)][:12] + [m for m in raw if m["starts"][:4] > str(TARGET_YEAR)][:1]
    months = []
    for i, m in enumerate(raw[:12]):
        row = month_row(m, rate)
        start = datetime.fromisoformat(m["starts"])
        end = datetime.fromisoformat(raw[i + 1]["starts"]) - timedelta(days=1) if i + 1 < len(raw) else None
        b = m["ganzhi"][1]
        row.update({
            "label": f"{start.month}월({b}월, {start.month}/{start.day}~)",
            "short_label": f"{start.month}월",
            "saju_month": f"{b}월",
            "period": f"{start.month}/{start.day}~" + (f"{'' if end.year == TARGET_YEAR else f'{end.year}/'}{end.month}/{end.day}" if end else ""),
            "year_energy": f"{TARGET_YEAR - 1}년 {year_ganzhi(TARGET_YEAR - 1)}년" if start < datetime.fromisoformat(sy["starts"]) else f"{TARGET_YEAR}년 {sy['ganzhi']}년",
            "past": start.date() < order_day,
        })
        months.append(row)

    def marks(x: dict) -> dict:
        gods = (x["stem_ten_god"], x["branch_ten_god"])
        g = lambda grp: T.has(x, grp)
        br = x["ganzhi"][1]
        c_day, c_mon = T.rel(x, "일주", T.CLASH), T.rel(x, "월주", T.CLASH)
        h_day = T.rel(x, "일주", T.HAP)
        harm_day = T.rel(x, "일주", ("형", "자형", "파", "해", "원진"))
        yeok, peach, gui, mun = br in hits["yeokma"], br in hits["peach"], br in hits["guiin"], br == hits["munchang"]
        gwan, ins, sik, jae, bi = g("관성"), g("인성"), g("식상"), g("재성"), g("비겁")
        sg = "상관" in gods and n_gwan > 0
        geob = "겁재" in gods
        leak = geob or (bi and n_jae > 0)
        els = _gz_elements(x["ganzhi"])
        fill, more = any(e in good_el for e in els), sum(e in excess for e in els)
        base = x["score"]

        def area(items, score):
            return {"score": T.clamp(score), "signs": [s for s, on in items if on]}
        a = {
            "work": area((("직장·승진 기운(관성)", gwan), ("문서·합격 기운(인성)", ins), ("실력 발휘(식상)", sik),
                          ("윗사람과 부딪힘(상관견관)", sg), ("일 자리 변동(월지 충)", c_mon), ("이동 기운(역마)", yeok)),
                         base + 8 * gwan + 5 * ins + 4 * sik - 6 * sg - 3 * c_mon),
            "money": area((("재물 별(재성)", jae), ("재능이 돈으로(식상)", sik), ("나가는 돈 주의(비겁·겁재)", leak),
                           ("돈의 자리 변동(월지 충)", c_mon)),
                          base + 10 * jae + (5 if strong else 2) * sik - 7 * leak - 4 * c_mon),
            "biz": area((("재능이 돈으로 이어짐(식상생재)", sik and (jae or n_jae > 0)), ("새 일 기운(식상)", sik),
                         ("계약·문서 기운(인성)", ins), ("동업·경쟁 주의(겁재)", geob), ("자리 변동(충)", c_day or c_mon)),
                        base + 5 * sik + 5 * (sik and (jae or n_jae > 0)) + 6 * ins - 6 * geob - 3 * (c_day or c_mon)),
            "love": area(((f"배우자 별({spouse})", g(spouse)), ("도화 글자", peach), ("배우자 자리 합(일지 합)", h_day),
                          ("배우자 자리 충(일지 충)", c_day), ("배우자 자리 마찰(형·파·해·원진)", harm_day)),
                         base + 9 * g(spouse) + 6 * peach + 6 * h_day - 7 * c_day - 3 * harm_day),
            "people": area((("귀인 글자(천을귀인)", gui), ("구설 주의(상관)", "상관" in gods), ("손재 주의(겁재)", geob),
                            ("관재 주의(편관과 충·형)", "편관" in gods and (c_day or c_mon or harm_day)), ("관재 주의(상관견관)", sg)),
                           base + 8 * gui - 4 * ("상관" in gods) - 5 * geob - 6 * ("편관" in gods and (c_day or c_mon or harm_day)) - 4 * sg),
            "health": area((("부족한 기운 채움", fill), ("넘치는 기운 더함", more > 0), ("몸의 자리 충(일지 충)", c_day),
                            ("생활 자리 충(월지 충)", c_mon)),
                           base + 4 * fill - 4 * more - 7 * c_day - 4 * c_mon),
            "move": area((("이동 기운(역마)", yeok), ("공부·시험 기운(인성)", ins), ("문창귀인 글자", mun),
                          ("자리 변동(충)", c_day or c_mon)),
                         base + 6 * yeok + 7 * ins + 5 * mun + 2 * (c_day or c_mon)),
        }
        overall = [s for s, on in (("귀인", gui), ("역마", yeok), ("도화", peach), ("일지 합", h_day),
                                   ("일지 충", c_day), ("월지 충", c_mon)) if on]
        score = base + 4 * gui + 3 * h_day - 5 * c_day - 3 * c_mon
        return {"t_score": T.clamp(score), "t_signs": overall, "areas": a}

    year.update(marks(year))
    for m in months:
        m.update(marks(m))
    T.reveal_fix(result, "newyear", months, replace=False)   # 제1조항: 결제 전 화면의 '돕는 달'·'조심할 달'과 같은 방향

    def avg(vals):
        return sum(vals) / len(vals)

    screen = T.screen_score(f, result, "newyear")   # 제1조항: 2027년 전체 점수는 결제 전 화면에서 본 점수 그대로
    year_score = screen["score"]
    label = lambda m: m["label"]
    areas = {}
    for key, title in AREAS:
        ms = [dict(m, t_score=m["areas"][key]["score"], t_signs=m["areas"][key]["signs"]) for m in months]
        areas[key] = {
            "name": title,
            "score": T.clamp((year["areas"][key]["score"] + avg([m["t_score"] for m in ms])) / 2),
            "year_signs": year["areas"][key]["signs"],
            "best_months": T.best(ms, 3, label),
            "careful_months": T.worst(ms, 2, label, limit=45),
            "sign_months": {s: [m["label"] for m in ms if s in m["t_signs"]]
                            for s in dict.fromkeys(x for m in ms for x in m["t_signs"])},
        }
    ranked = sorted(areas, key=lambda k: -areas[k]["score"])

    # 대운: 2027년에 지나는 대운, 2027년에 새 대운이 시작하는지
    periods = f["daewoon"]["periods"]
    cur = None
    for p in periods:
        if p["start_year"] <= TARGET_YEAR:
            cur = p
    starts_now = next((p for p in periods if p["start_year"] == TARGET_YEAR), None)
    nxt = next((p for p in periods if p["start_year"] > TARGET_YEAR), None)
    prev = periods[periods.index(cur) - 1] if cur and periods.index(cur) > 0 else None
    birth = date.fromisoformat(f["person"]["birth"])
    def kdate(iso: str) -> str:
        d = date.fromisoformat(iso)
        return f"{d.year}년 {d.month}월 {d.day}일"
    if starts_now:
        change = (f"{TARGET_YEAR}년에 대운이 바뀌어요. {kdate(starts_now['start_date'])}쯤까지는 {prev['ganzhi']} 대운이고, 그때부터 {starts_now['ganzhi']} 대운으로 넘어가요."
                  if prev else f"{TARGET_YEAR}년 {kdate(starts_now['start_date'])}쯤 첫 대운({starts_now['ganzhi']})이 시작해요.")
        in_year = (f"{prev['ganzhi']}({prev['hanja']}) → {starts_now['ganzhi']}({starts_now['hanja']}), {kdate(starts_now['start_date'])}쯤 바뀜"
                   if prev else f"{starts_now['ganzhi']}({starts_now['hanja']}), {kdate(starts_now['start_date'])}쯤 시작")
    elif cur:
        change = f"{TARGET_YEAR}년에는 대운이 바뀌지 않아요. {cur['ganzhi']} 대운이 한 해 내내 이어져요." + (
            f" 다음 대운({nxt['ganzhi']})은 {nxt['start_year']}년에 시작해요." if nxt else "")
        in_year = f"{cur['ganzhi']}({cur['hanja']}) · {cur['age_text']} · {cur['years_text']}"
    else:
        change = f"{TARGET_YEAR}년에는 아직 첫 대운이 시작되기 전이에요." + (f" 첫 대운({nxt['ganzhi']})은 {nxt['start_year']}년에 시작해요." if nxt else "")
        in_year = "첫 대운 전이에요"
    after = nxt
    daewoon = {
        "in_2027": in_year,
        "now": _period(cur) if cur else None,             # 2027년 말에 지나는 대운
        "changes_in_2027": bool(starts_now),
        "change_date": kdate(starts_now["start_date"]) if starts_now else "",
        "change_text": change,
        "before": _period(prev) if starts_now and prev else None,   # 2027년에 바뀌면 바뀌기 전 대운
        "next": _period(after) if after else None,
        "next_start_year": after["start_year"] if after else None,
    }

    sj = samjae(an["pillars"][0]["branch"], TARGET_YEAR)
    roles = _roles(f)
    stem_el, branch_el = _gz_elements(year["ganzhi"])
    rels = [{"kind": K.relation_kind(r["type"]), "type": r["type"], "level": r["level"],
             "with": _pillar_word(r["with"]),
             "meaning": K.RELATION.get(K.relation_kind(r["type"]), "")} for r in year["relations"]]
    fit_good = sum(1 for el in (stem_el, branch_el) if roles[el].startswith(("용신", "희신")))
    fit_bad = sum(1 for el in (stem_el, branch_el) if roles[el].startswith(("기신", "넘치는")))
    fit = "잘 맞는 편" if fit_good > fit_bad else "부담이 있는 편" if fit_bad > fit_good else "반반인 편"
    year_type = ("기회를 잡는 해" if year_score >= 68 else "차근차근 올라가는 해" if year_score >= 58
                 else "다지며 준비하는 해" if year_score >= 47 else "지키며 숨을 고르는 해")
    focus = answers.get("focus", "") or ""
    question = (f["order"].get("question") or str(answers.get("question") or "")).strip()[:1000]
    f["order"]["question"] = question
    lucky = f["lucky"]
    best = T.best(months, 3, label)
    careful = T.worst(months, 3, label, limit=45)
    health_body = [{"el": e, "name": K_NAME[e], **BODY[e]} for e in excess + [x for x in lacking if x not in excess]]
    health_basis = "넘치는 기운과 모자란 기운의 영역"
    if not health_body:   # 넘치거나 모자란 기운이 없으면 2027년에 크게 들어오는 기운(불·흙) 쪽을 본다
        health_body = [{"el": e, "name": K_NAME[e], **BODY[e]} for e in dict.fromkeys((stem_el, branch_el))]
        health_basis = f"오행이 고른 편이라 2027년에 들어오는 {K_NAME[stem_el]}({stem_el})과 {K_NAME[branch_el]}({branch_el})의 영역"

    data = {
        "target_year": TARGET_YEAR, "order_date": f["order"]["date"],
        "focus": focus, "focus_section": FOCUS.get(focus, ""), "question": question,
        "year": {"ganzhi": year["ganzhi"], "hanja": year["hanja"], "animal": year["animal"], "starts": year["starts"][:10],
                 "stem": {"char": year["ganzhi"][0], "element": stem_el, "element_name": K_NAME[stem_el], "ten_god": year["stem_ten_god"],
                          "ten_god_simple": K.TEN_GOD[year["stem_ten_god"]]["simple"], "role": roles[stem_el]},
                 "branch": {"char": year["ganzhi"][1], "element": branch_el, "element_name": K_NAME[branch_el], "ten_god": year["branch_ten_god"],
                            "ten_god_simple": K.TEN_GOD[year["branch_ten_god"]]["simple"], "role": roles[branch_el]},
                 "twelve_stage": year["twelve_stage"], "relations": rels, "gyeok_effect": year["gyeok_effect"],
                 "flow_score": year["score"], "signs": year["t_signs"]},
        "year_score": year_score, "screen_score": screen, "year_type": year_type, "fit": fit,
        "age_2027": TARGET_YEAR - birth.year, "age_text": f"{TARGET_YEAR}년 생일이 지나면 만 {TARGET_YEAR - birth.year}세",
        "zodiac": f["person"]["zodiac"], "samjae": sj, "daewoon": daewoon,
        "areas": {k: {kk: v[kk] for kk in ("name", "score", "year_signs", "best_months", "careful_months", "sign_months")} for k, v in areas.items()},
        "strong_areas": [areas[k]["name"] for k in ranked[:2]], "weak_areas": [areas[k]["name"] for k in ranked[-2:]],
        "best_months": best, "careful_months": careful,
        "yeokma_months": [m["label"] for m in months if "역마" in m["t_signs"]],
        "peach_months": [m["label"] for m in months if "도화" in m["t_signs"]],
        "guiin_months": [m["label"] for m in months if "귀인" in m["t_signs"]],
        "munchang_months": [m["label"] for m in months if m["ganzhi"][1] == hits["munchang"]],
        "hit_branches": {"역마 글자": hits["yeokma"], "도화 글자": hits["peach"], "천을귀인 글자": hits["guiin"], "문창귀인 글자": hits["munchang"]},
        "spouse_star": spouse, "excess": excess, "lacking": lacking, "health_body": health_body, "health_basis": health_basis,
        "lucky": {"element": lucky["element"], "element_name": lucky["element_name"], "color": lucky["color"],
                  "direction": lucky["direction"], "numbers": lucky["numbers"], "items": lucky["items"], "foods": lucky["foods"]},
        "first_month": months[0]["label"], "spring_months": [m["label"] for m in months[:3]],
    }
    month_digest = [{"label": m["label"], "period": m["period"], "term": m["term"], "ganzhi": m["ganzhi"],
                     "year_energy": m["year_energy"], "stem_ten_god": m["stem_ten_god"], "branch_ten_god": m["branch_ten_god"],
                     "relations_text": m["relations_text"], "score": m["score"], "t_score": m["t_score"], "t_signs": m["t_signs"],
                     "areas": {k: f"{v['score']}점 {', '.join(v['signs']) or '—'}" for k, v in m["areas"].items()},
                     **({"지난 달": True} if m["past"] else {})} for m in months]
    # 이 상품의 '월운'은 2027년 12달이다(글쓰기 재료와 글 검사가 같은 달을 보게)
    f["months"] = months
    return {"label": "신년운세 재료", "product": "newyear", "data": data,
            "digest": {**data, "달별": month_digest,
                       "점수 설명": ("year_score는 2027년 전체 점수: 세운(2027년 정미) 점수와 12달 점수의 평균을 반씩 섞었어요. "
                                  "t_score는 그 달의 전체 점수: 운의 흐름 점수(score)에 귀인 글자와 일지 합은 더하고, 일지·월지 충은 빼 계산해요. "
                                  "areas의 점수는 분야별 점수예요(관성·재성·식상·인성 같은 십신, 역마·도화·귀인 글자, 합·충을 더하고 빼 계산)."),
                       "달 이름 읽는 법": ("사주의 달은 절기가 드는 날 바뀌어요. '2월(인월, 2/4~)'은 2월 4일 입춘부터 3월 5일까지예요. "
                                     f"1월(축월)은 아직 {TARGET_YEAR - 1}년 {year_ganzhi(TARGET_YEAR - 1)}년의 기운이고, 2027년 정미년의 기운은 2월 4일 입춘부터 시작해요. "
                                     "'지난 달'이 있는 달은 주문한 날 이미 시작한 달이에요.")},
            "year": year, "months": months, "areas": areas}


PILLAR_WORD = {"년주": "태어난 해", "월주": "태어난 달", "일주": "태어난 날", "시주": "태어난 시간"}


def _pillar_word(p: str) -> str:
    return PILLAR_WORD.get(p, p)


def _period(p: dict | None) -> dict | None:
    if not p:
        return None
    return {k: p[k] for k in ("ganzhi", "hanja", "age_text", "years_text", "start_year", "start_date",
                              "stem_ten_god", "branch_ten_god", "score")}


STYLE = T.style("2027 신년운세", """
[2027 신년운세 규칙]
- 독자는 사주를 잘 모르는 20~50대예요. 새해 계획을 세우려고 이 책을 삽니다. 쉬운 말로, 바로 쓸 수 있게 씁니다.
- 이 책이 보는 해는 2027년(정미년) 하나입니다. '신년운세 재료'의 값(year, year_score, areas, 달별, samjae, daewoon, lucky)만 근거로 씁니다.
  재료에 없는 점수, 달, 날짜, 신살을 만들지 않습니다. 사주 계산 결과의 '세운'·'대운' 목록에서 2027년이 아닌 해는 비교할 때만 짧게 씁니다.
- 달은 재료의 이름(label) 그대로 씁니다. 예: "2월(인월, 2/4~)". 사주의 달은 절기가 드는 날 바뀐다는 점을 처음 나올 때 한 번 풀어 줍니다.
  1월(축월)은 아직 2026년 병오년의 기운이고, 정미년의 기운은 2월 4일 입춘부터라는 점을 틀리지 않습니다.
- 삼재는 samjae 값 그대로 씁니다. is_samjae가 false이면 "2027년은 삼재가 아니에요"라고만 쓰고 겁주지 않습니다.
  삼재이면 kind(들삼재·눌삼재·날삼재)를 그대로 쓰고, 무엇을 조심하고 무엇을 하면 되는지 함께 씁니다. 부적, 굿, 비싼 물건은 권하지 않습니다.
- 대운은 daewoon 값 그대로 씁니다. changes_in_2027이 false이면 2027년에 대운이 바뀐다고 쓰지 않습니다.
- 사주 용어(세운, 대운, 십신, 용신, 합, 충, 역마, 도화, 귀인, 삼재 등)는 위 [용어 풀이] 규칙대로 쉬운 말과 생활 장면으로 자세히 풉니다.
- 주어와 목적어가 분명한 짧은 문장으로 씁니다. 비유, 지어낸 표현, 시 같은 문장은 쓰지 않습니다.
- '좋은 때' 대신 '좋은 시기'라고 씁니다. "참고용", "참고만", "재미로" 같은 말은 쓰지 않습니다.
- "보완법:", "방법:", "조심할 점:" 같은 이름표는 문단 첫머리에 두거나 문장이 끝난 뒤에 씁니다(인쇄할 때 새 줄에서 시작해요).
- 쪽마다 '사주 근거(어떤 글자, 어떤 달) → 생활 속 장면 → 바로 할 수 있는 방법'으로 채웁니다. 칸의 chars를 채워 쪽이 90% 이상 차게 씁니다.
- 고객이 고른 궁금한 분야(focus)가 있으면 그 장을 더 자세히 씁니다. 다른 장에서도 그 분야와 이어지는 내용이 있으면 한 줄씩 이어 줍니다.
- 건강운은 진단이 아닙니다. 병명을 쓰지 않고, 전통 명리에서 오행과 짝지어 본 몸의 영역(health_body)과 생활 습관으로 씁니다.
  걱정되는 증상이 있으면 병원 진료를 받으라는 안내를 건강운 장에 한 번 넣습니다.
- 투자는 상품, 종목, 금액, 수익률을 권하지 않습니다. 시기와 원칙(나눠서, 확인하고, 멈출 기준)으로 씁니다.
- 연애·결혼은 연애·결혼 상태를 모르므로 '혼자인 경우', '연애 중인 경우', '결혼한 경우'로 나눠 씁니다.
""")


def build_outline(f: dict) -> list[dict]:
    th = f["theme"]
    t = th["data"]
    y = t["year"]
    a = t["areas"]
    sj = t["samjae"]
    dw = t["daewoon"]
    name = f["person"]["name"]
    months = th["months"]
    sections: list[dict] = []
    focus_no = t["focus_section"]

    def section(no: str, pages: list[dict]) -> None:
        title, subtitle = next((x, s) for n, x, s in SECTIONS if n == no)
        if no == focus_no:   # 고객이 고른 분야의 장에 한 쪽을 더한다
            pages.insert(len(pages) - 1 if len(pages) > 2 else len(pages), P(
                f"ny{no}_focus", f"{t['focus']}을 가장 궁금해하신 {name}님께" if t["focus"] != "한 해 전체" else f"한 해 전체를 더 깊이 보기",
                slot=S(f"ny{no}_focus", f"고객이 가장 궁금해한 분야는 '{t['focus']}'이에요. 이 분야의 2027년 흐름을 달 이름과 사주 근거로 한 번 더 깊게 쓰고, "
                                        "고객이 바로 할 일 세 가지를 순서대로 써 주세요.")))
        sections.append({"no": no, "title": title, "subtitle": subtitle, "pages": pages, "terms": []})

    P, S = T.tpage, _slot
    short = lambda sg: sg.split("(")[0]
    yrow = f"{y['ganzhi']}({y['hanja']})년 · {y['animal']}띠 해"
    gods = f"{y['stem']['char']}: {y['stem']['ten_god']}({y['stem']['ten_god_simple']}) · {y['branch']['char']}: {y['branch']['ten_god']}({y['branch']['ten_god_simple']})"
    rel_txt = ", ".join(f"{r['with']}{'과' if (ord(r['with'][-1]) - 0xAC00) % 28 else '와'} {r['kind']}" for r in y["relations"]) or "특별히 합치거나 부딪히는 글자가 없어요"
    sj_txt = (f"{sj['kind']}예요 ({t['zodiac']}띠, {sj['years_branches']} 해가 삼재)" if sj["is_samjae"]
              else f"삼재가 아니에요 ({t['zodiac']}띠의 삼재는 {sj['years_branches']} 해)")
    dw_txt = dw["change_text"]
    # 표 안에서는 달 이름을 짧게: "4월(진월, 4/5~)" → "4월(진월)"
    join = lambda xs, empty="뚜렷한 달이 없어요": ", ".join(x.split(",")[0] + ")" if "," in x else x for x in xs) or empty

    section("1", [
        P("cover", "표지", figure="cover"),
        P("toc", "목차", figure="toc"),
        P("how_to_read", "이 책을 읽는 방법", static="ny_how_to_read", opener=True),
        P("ny_saju", "사주와 2027년 짧게 알기", static="ny_what_is_saju", figure="element_cycle"),
        P("chart", "나의 사주표", figure="pillars",
          slot=S("chart", f"{name}님의 여덟 글자를 소개하고, 일간(나를 나타내는 글자)이 어떤 사람인지 쉽게 설명해 주세요. 2027년을 볼 때 어느 글자가 중요한지 한 문장으로 이어 주세요.", HALF)),
        P("ny_fate", "나의 2027년 운명", figure="kv", rows=[
            ["2027년의 기운", yrow], ["나에게 들어오는 십신", gods],
            ["내 사주와의 관계", rel_txt], ["나에게 필요한 기운(용신)", f"{f['lucky']['element_name']}({f['lucky']['element']})"],
            ["삼재", sj_txt], ["대운", dw_txt],
        ], slot=S("ny_fate", "표를 바탕으로 2027년이 이 사람에게 어떤 해인지 처음 읽는 사람도 알게 소개해 주세요. 십신, 용신, 삼재, 대운이 무슨 뜻인지 괄호로 풀어 주세요.", HALF - 50)),
    ])
    area_rows = [[v["name"], f"{v['score']}점", ", ".join(short(x) for x in v["year_signs"]) or "—", ", ".join(m.split("(")[0] for m in v["best_months"][:2])]
                 for v in a.values()]
    section("2", [
        P("ny_glance", "한눈에 보는 나의 2027년", figure="kv", opener=True, rows=[
            ["한마디로", t["year_type"]], T.screen_row(t["screen_score"]),
            ["강한 분야", ", ".join(t["strong_areas"])], ["약한 분야", ", ".join(t["weak_areas"])],
            ["가장 좋은 달", join(t["best_months"])], ["조심할 달", join(t["careful_months"], "크게 조심할 달은 없어요")],
            ["삼재", "아니에요" if not sj["is_samjae"] else sj["kind"]],
            ["대운", "2027년에 바뀌어요" if dw["changes_in_2027"] else "2027년에는 바뀌지 않아요"],
        ], slot=S("ny_glance", f"표를 이어서 2027년을 한 문장으로 요약하고('{t['year_type']}'), 그 까닭을 세운 글자와 점수로 짧게 설명해 주세요.", HALF - 80)),
        P("ny_scores", "분야별 점수", figure="grid",
          grid={"head": ["분야", "점수", "2027년 표시", "좋은 달"], "rows": area_rows, "widths": ["24%", "12%", "40%", "24%"],
                "hl": [i for i, v in enumerate(a.values()) if v["name"] in t["strong_areas"]], "left": [2]},
          note="분야별 점수는 2027년 세운 점수와 12달 점수의 평균을 반씩 섞어 계산했어요. 높을수록 그 분야에 힘이 실리는 해예요.",
          slot=S("ny_scores", "표에서 점수가 높은 분야와 낮은 분야를 짚고, 각 분야의 표시가 무슨 뜻인지 쉬운 말로 설명해 주세요.", HALF - 60)),
        P("ny_goodbad", "좋은 운과 나쁜 운 정리",
          slot=S("ny_goodbad", "2027년에 들어오는 좋은 운 세 가지와 조심할 운 세 가지를 근거(글자, 달)와 함께 정리해 주세요. 조심할 운마다 '보완법:'을 붙여 주세요.")),
    ])
    section("3", [
        P("ny3_open", "2027년 정미년은 어떤 해일까", figure="kv", opener=True, rows=[
            ["정(丁)", f"{y['stem']['element_name']}({y['stem']['element']}) · {y['stem']['ten_god']} · {y['stem']['role']}"],
            ["미(未)", f"{y['branch']['element_name']}({y['branch']['element']}) · {y['branch']['ten_god']} · {y['branch']['role']}"],
            ["새해 기운과의 궁합", t["fit"]], ["2027년 시작", f"{y['starts'][5:7].lstrip('0')}월 {y['starts'][8:].lstrip('0')}일 입춘부터"],
        ], slot=S("ny3_open", "정화(丁)와 미토(未)가 이 사람의 용신·희신·기신 가운데 무엇인지(role)를 근거로 새해 기운과의 궁합을 한 문장(lead)으로 요약하고 풀어 주세요.", HALF - 40, "lead")),
        P("ny3_rel", "내 사주 글자와 만나는 방식",
          slot=S("ny3_rel", f"2027년 글자가 내 사주 글자와 맺는 관계({rel_txt})를 하나씩 풀어 주세요. 합(손잡음)과 충(부딪힘)이 생활에서 어떤 일로 나타나기 쉬운지 장면과 방법을 붙여 주세요.")),
        P("ny3_daewoon", "2027년의 대운", figure="kv", rows=[
            ["2027년의 대운", dw["in_2027"]],
            ["2027년에 바뀌나요", f"네, {dw['change_date']}쯤 바뀌어요" if dw["changes_in_2027"] else "아니요"],
            ["다음 대운", f"{dw['next']['ganzhi']}({dw['next']['hanja']}) · {dw['next']['start_year']}년부터" if dw["next"] else "—"],
            ["나이", t["age_text"]],
        ], slot=S("ny3_daewoon", "대운(10년마다 바뀌는 큰 운)이 무엇인지 쉽게 풀고, 2027년의 대운과 2027년 세운이 어떻게 겹치는지 써 주세요. 대운이 바뀌는 해인지 분명히 말해 주세요.", HALF + 130)),
        P("ny3_samjae", "삼재 확인", figure="kv", rows=[
            ["나의 띠", f"{t['zodiac']}띠 ({sj['group']} 띠 무리)"], ["삼재가 드는 해", f"{sj['years_branches']} 해"],
            ["2027년(미년)은", sj_txt],
            ["가까운 삼재", "·".join(f"{x}년" for x in (sj["this_run"] or sj["next_run"]))],
        ], slot=S("ny3_samjae", "삼재(띠마다 12년에 한 번, 3년 동안 조심하라고 본 해)를 쉽게 설명하고, 이 사람의 2027년 삼재 여부를 표 그대로 써 주세요. 삼재이면 할 일과 피할 일을, 아니면 왜 마음을 놓아도 되는지 근거를 써 주세요.", HALF + 100)),
    ])

    def area_grid(no: str, key: str) -> dict:
        v = a[key]
        rows = [[m["short_label"], f"{m['saju_month']} {m['period'].split('~')[0]}~", ", ".join(short(x) for x in m["areas"][key]["signs"]) or "—",
                 f"{m['areas'][key]['score']}"] for m in months]
        legend = list(dict.fromkeys(x for m in months for x in m["areas"][key]["signs"] if "(" in x))
        return P(f"ny{no}_months", f"2027년 월별 {v['name']}운", figure="grid",
                 grid={"head": ["달", "사주 달", "표시", "점수"], "rows": rows, "widths": ["13%", "23%", "50%", "14%"],
                       "hl": [i for i, m in enumerate(months) if m["label"] in v["best_months"]], "left": [2]},
                 note=("표시 풀이: " + ", ".join(f"{short(x)}={x[len(short(x)) + 1:-1]}" for x in legend) + ". " if legend else "")
                 + "사주의 달은 절기가 드는 날 바뀌어요.",
                 slot=S(f"ny{no}_months", f"표에서 {v['name']}운이 좋은 달과 조심할 달을 골라 그 까닭(표시)과 할 일을 짧게 써 주세요.", 220))

    def area_chapter(no: str, key: str, opener_title: str, guide: str, pages: list[dict], note: str = "") -> None:
        v = a[key]
        head = P(f"ny{no}_open", opener_title, figure="kv", opener=True, rows=[
            [f"{v['name']} 점수", f"{v['score']}점"], ["2027년 표시", ", ".join(short(x) for x in v["year_signs"]) or "—"],
            ["좋은 달", join(v["best_months"])], ["조심할 달", join(v["careful_months"], "크게 조심할 달은 없어요")],
        ], note=note, slot=S(f"ny{no}_open", guide, HALF - 20, "lead"))
        section(no, [head, area_grid(no, key), *pages])

    area_chapter("4", "work", "2027년 나의 일과 직장", "2027년 일·직장운을 한 문장(lead)으로 요약하고, 관성(직장·평가)·인성(문서·합격)·식상(실력 발휘) 표시를 근거로 풀어 주세요.", [
        P("ny4_rank", "평가와 승진",
          slot=S("ny4_rank", "관성과 인성이 드는 달을 근거로 평가, 승진, 인정받기 좋은 시기를 쓰고, 회사에서 바로 할 행동을 써 주세요. 상관견관 표시가 있으면 윗사람과 부딪히지 않는 방법도 써 주세요.")),
        P("ny4_move", "이직과 새 일 시작하기 좋은 시기",
          slot=S("ny4_move", "역마(이동 기운)·월지 충(일 자리 변동)·식상 표시가 있는 달을 근거로 이직, 새 일, 부서 이동에 좋은 시기와 피할 시기를 순서대로 써 주세요.")),
    ])
    area_chapter("5", "money", "2027년 나의 재물", "2027년 재물운을 한 문장(lead)으로 요약하고, 재성(재물)·식상(재능)·비겁(나가는 돈) 표시를 근거로 풀어 주세요.", [
        P("ny5_in", "큰 돈이 들어오는 시기",
          slot=S("ny5_in", "재성과 식상이 드는 달을 근거로 돈이 들어오기 좋은 시기와, 그 시기에 할 일(협상, 부업, 정산)을 써 주세요.")),
        P("ny5_out", "돈이 빠져 나가는 시기",
          slot=S("ny5_out", "'나가는 돈 주의' 표시가 있는 달과 조심할 달을 근거로 돈이 새기 쉬운 상황(빌려주기, 충동구매, 모임)을 장면으로 쓰고 막는 방법을 써 주세요.")),
        P("ny5_invest", "투자는 해야 할까?",
          slot=S("ny5_invest", "2027년 재물 점수와 달별 표시를 근거로 투자를 늘릴 해인지 지킬 해인지 분명히 답하고, 원칙(나눠서, 확인 순서, 멈출 기준)을 써 주세요. 상품명과 수익률은 쓰지 않습니다.")),
    ])
    area_chapter("6", "biz", "2027년 사업·부업과 문서", "2027년 사업·부업·문서운을 한 문장(lead)으로 요약하고, 식상생재(재능이 돈으로 이어짐)와 인성(문서) 표시를 근거로 풀어 주세요.", [
        P("ny6_biz", "사업과 부업",
          slot=S("ny6_biz", "식상과 재성 표시가 있는 달을 근거로 새로운 일이나 부업을 시작하기 좋은 시기와 준비 순서를 써 주세요. 겁재(동업·경쟁) 표시가 있으면 동업할 때 조심할 점도 써 주세요.")),
        P("ny6_doc", "계약·문서와 집·부동산",
          slot=S("ny6_doc", "인성(문서·계약) 표시와 충(자리 변동) 표시가 있는 달을 근거로 계약서·서류를 다루기 좋은 시기, 집 계약·전세·월세 갱신·부동산을 알아보기 좋은 시기와 피할 시기, 확인 순서를 써 주세요. 금액과 지역은 권하지 않습니다.")),
    ])
    area_chapter("7", "love", "2027년 나의 연애와 결혼", f"2027년 연애·결혼운을 한 문장(lead)으로 요약하고, 배우자 별({t['spouse_star']})·도화 글자·배우자 자리(일지) 합충 표시를 근거로 풀어 주세요.", [
        P("ny7_new", "새로운 사랑이 찾아오는 시기",
          slot=S("ny7_new", "혼자인 경우를 기준으로 인연이 오기 좋은 달과 만나기 쉬운 곳, 다가가는 방법을 근거와 함께 써 주세요.")),
        P("ny7_couple", "연인과 부부 관계",
          slot=S("ny7_couple", "연애 중인 경우와 결혼한 경우로 나눠, 배우자 자리(일지)의 합·충이 드는 달을 근거로 가까워지는 시기와 다투기 쉬운 시기, 대화 방법을 써 주세요.")),
    ])
    area_chapter("8", "people", "2027년 나의 사람운", "2027년 사람운을 한 문장(lead)으로 요약하고, 귀인(천을귀인) 글자와 구설·손재·관재 표시를 근거로 풀어 주세요.", [
        P("ny8_helper", "나를 도와줄 은인은 누구일까",
          slot=S("ny8_helper", "귀인 글자가 드는 달과 사주의 인성·관성을 근거로 도와줄 사람의 유형(나이, 관계, 만나는 곳)과 그 사람을 알아보는 방법을 써 주세요.")),
        P("ny8_trouble", "구설·손재·관재",
          slot=S("ny8_trouble", "구설(말로 생기는 다툼), 손재(돈을 잃는 일), 관재(서류·법·관공서 문제)를 쉬운 말로 풀고, 표시가 있는 달을 근거로 각각 막는 방법을 써 주세요. 표시가 없는 것은 없다고 짧게 씁니다.")),
    ])
    section("9", [
        P("ny9_open", "2027년 나의 건강", figure="kv", opener=True, rows=[
            ["건강 점수", f"{a['health']['score']}점"], ["돌볼 몸의 영역", " / ".join(f"{x['name']}({x['el']}): {x['area']}" for x in t["health_body"])],
            ["좋은 달", join(a["health"]["best_months"])], ["쉬어 갈 달", join(a["health"]["careful_months"], "크게 조심할 달은 없어요")],
        ], note="전통 명리에서 오행과 짝지어 본 몸의 영역이에요. 진단이 아니라 생활 습관을 돌아보는 기준이에요. 걱정되는 증상이 있으면 병원 진료를 받으세요.",
          slot=S("ny9_open", "2027년 건강운을 한 문장(lead)으로 요약하고, 넘치는·모자란 오행과 2027년 글자(불·흙)를 근거로 풀어 주세요. 병명은 쓰지 않습니다.", HALF - 120, "lead")),
        area_grid("9", "health"),
        P("ny9_body", "조심할 몸의 영역과 신호",
          slot=S("ny9_body", "health_body의 영역과 신호를 근거로 2027년에 돌볼 몸의 영역과 생활 속 신호를 쓰고, 신호가 오면 할 일을 써 주세요. 병명과 진단은 쓰지 않습니다.")),
        P("ny9_when", "위험한 시기와 생활 습관",
          slot=S("ny9_when", "충 표시나 점수가 낮은 달을 근거로 무리하면 안 되는 시기, 다치지 않게 조심할 상황(운전, 운동, 계단), 그 시기의 생활 습관을 써 주세요. 걱정되면 병원 진료를 받으라는 안내를 한 번 넣습니다.")),
    ])
    area_chapter("10", "move", "2027년 이사·여행·시험", "2027년 이사·여행·시험운을 한 문장(lead)으로 요약하고, 역마(이동 기운)·인성(공부)·문창귀인 글자 표시를 근거로 풀어 주세요.", [
        P("ny10_move", "움직이기 좋은 시기",
          slot=S("ny10_move", "역마와 충 표시를 근거로 이사, 여행, 출장, 해외 일정에 좋은 시기와 피할 시기, 움직일 때 확인할 것을 써 주세요.")),
        P("ny10_study", "공부와 자격증",
          slot=S("ny10_study", "인성과 문창귀인 글자가 드는 달을 근거로 공부를 시작하기 좋은 시기, 시험 일정을 잡기 좋은 시기, 공부 방법을 써 주세요.")),
    ])

    mrows = [[f"{m['short_label']}({m['saju_month']})", m["period"], m["hanja"], ", ".join(m["t_signs"]) or "—", f"{m['t_score']}"] for m in months]
    pairs = [months[i:i + 2] for i in range(0, 12, 2)]
    month_pages = []
    for i, pr in enumerate(pairs):
        mp = P(f"ny11_m{i + 1}", f"{pr[0]['short_label']}과 {pr[1]['short_label']}", figure="kv", rows=[
            [m["label"], f"{m['hanja']} {m['ganzhi']} · {m['stem_ten_god']}·{m['branch_ten_god']} · {m['t_score']}점"
             + (f" · {', '.join(m['t_signs'])}" if m["t_signs"] else "")] for m in pr],
            slot=S(f"ny11_m{i + 1}", f"{pr[0]['label']}와 {pr[1]['label']}를 차례로 써 주세요. 달마다 그 달의 기운(십신, 표시, 점수)과 분야별 점수(areas)를 근거로 "
                                      "'해야 할 일'과 '조심할 일'을 구체적으로 씁니다. 달 이름으로 문단을 시작합니다.", FULL - 110))
        month_pages.append(mp)
    section("11", [
        P("ny11_all", "2027년 열두 달 한눈에 보기", figure="grid", opener=True,
          grid={"head": ["달", "기간", "간지", "표시", "점수"], "rows": mrows, "widths": ["22%", "21%", "13%", "30%", "14%"],
                "hl": [i for i, m in enumerate(months) if m["label"] in t["best_months"]], "left": [3]},
          note="사주의 달은 절기가 드는 날 바뀌어요. 1월(축월)은 아직 2026년 병오년의 기운이고, 정미년의 기운은 2월 4일 입춘부터예요.",
          slot=S("ny11_all", "표를 보는 법(달 이름, 기간, 점수)을 짧게 설명하고, 열두 달의 큰 흐름을 계절별로 정리해 주세요.", 150)),
        *month_pages,
        P("ny11_best", "나에게 가장 좋은 달과 조심할 달",
          slot=S("ny11_best", "가장 좋은 달(best_months)과 조심할 달(careful_months)을 근거와 함께 다시 정리하고, 좋은 달에 할 일과 조심할 달에 미룰 일을 짝지어 써 주세요.")),
    ])
    q = t["question"]
    last = [
        P("ny12_key", "2027년 핵심 정리", opener=True,
          slot=S("ny12_key", "이 책에서 가장 중요한 세 가지(2027년이 어떤 해인지, 가장 좋은 시기, 꼭 조심할 시기)를 한 문장 요약(lead)과 함께 정리해 주세요.", 580, "lead")),
        P("ny12_lucky", "행운의 색·방향·숫자", figure="lucky",
          slot=S("ny12_lucky", "용신 기운을 근거로 2027년에 쓸 행운의 색, 방향, 숫자를 옷, 지갑, 책상, 휴대폰처럼 생활에서 쓰는 방법으로 써 주세요.", HALF + 100)),
        P("ny12_dodont", "꼭 해야 할 일과 피할 일",
          slot=S("ny12_dodont", "앞 장의 내용을 모아 2027년에 꼭 해야 할 일 3가지와 피할 일 3가지를 정하고, 각각 근거(달, 글자)와 방법을 써 주세요.")),
        P("ny12_early", "놓치면 안 되는 연초 계획",
          slot=S("ny12_early", "1월(축월)부터 3월(묘월)까지 시기별로 할 일과 피할 일을 정리해 주세요. 첫 줄은 1월입니다.", 640, "plan")),
    ]
    if q:
        last.append(P("ny12_q", "질문에 대한 답", figure="question",
                      slot=S("ny12_q", f"고객 질문: \"{q}\". 2027년 세운과 달별 운을 근거로 솔직하고 구체적으로 답해 주세요. 언제(달 이름), 무엇을 하면 되는지 함께 씁니다.", FULL - 100)))
    last += [
        P("ny12_last", "마지막 조언",
          slot=S("ny12_last", f"{name}님에게 전하는 마지막 조언을 담백하게 써 주세요. 새해를 앞두고 가지기 쉬운 걱정 한두 가지에 '왜 괜찮은지(근거)'와 '무엇을 하면 되는지(행동)'로 답하고, "
                                 "2027년에 이 사주가 가진 힘을 근거로 말한 뒤 새해 첫 주에 할 한 가지를 짚어 주세요.", FULL - 20)),
    ]
    section("12", last)
    section("더보기", [P("more", "다른 사주도 궁금하다면", figure="cross_sell", span=2, opener=True)])
    return sections


def cross_sell_order(f: dict) -> list[str]:
    focus = f["theme"]["data"]["focus"]
    return {"일과 직장": ["career"], "돈과 재물": ["wealth"], "연애와 결혼": ["romance"], "건강": ["health"]}.get(focus, ["lifetime"])


def hook(f: dict) -> str:
    """다른 상품 끝에 붙는 신년운세 안내 문장(계산값만 사용)."""
    from ..analysis import branch_ten_god, ten_god
    name = f["person"]["name"]
    gz = year_ganzhi(TARGET_YEAR)
    ds = STEMS.index(f["day_master"]["stem"])
    sg, bg = ten_god(ds, STEMS.index(gz[0])), branch_ten_god(ds, BRANCHES.index(gz[1]))
    sj = samjae(f["pillars"][0]["branch"], TARGET_YEAR)
    return (f"2027년 정미년은 {name}님에게 {sg}({K.TEN_GOD[sg]['simple']}) 기운과 {bg}({K.TEN_GOD[bg]['simple']}) 기운이 들어오는 해예요. "
            + (f"{f['person']['zodiac']}띠라서 2027년은 {sj['kind']}예요. " if sj["is_samjae"] else f"{f['person']['zodiac']}띠는 2027년에 삼재가 아니에요. ")
            + "분야별 점수와 1월부터 12월까지 좋은 달, 조심할 달을 정리해 드려요.")
