"""결제 전 이야기 화면에서 고객이 본 '해마다 들어오는 별' 지도.

사이트는 site/public/assets/free/reveal.mjs 가 브라우저에서 계산한다. 결제 리포트를 쓸 때
고객이 결제 전에 본 해·달과 어긋나지 않도록 같은 규칙을 여기서 파이썬으로 다시 돌린다.
두 쪽이 같은 답을 내는지는 site/tests/taster.test.mjs 가 확인한다(정답표: site/tools/make_taster_fixture.py).
"""

from __future__ import annotations

from . import analysis as A
from . import taster
from .constants import BRANCHES, BRANCHES_HANJA, ELEMENTS, STEMS, STEMS_HANJA, TEN_GOD_GROUP
from .pillars import FourPillars

STEM_EL = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
BRANCH_EL = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]
FIRST_YEAR = 2027
REUNION_MONTHS = 24   # 재회사주 지도: 앞으로 24개월(사장님 2026-10-30: 몇 달 안, 길어야 2~3년)
# 태어난 날 지지의 삼합 무리마다 정해진 도화(桃花) 글자: 인오술→묘, 신자진→유, 사유축→오, 해묘미→자
PEACH_OF = {2: 3, 6: 3, 10: 3, 8: 9, 0: 9, 4: 9, 5: 6, 9: 6, 1: 6, 11: 0, 3: 0, 7: 0}


def _pillar(stem: int, branch: int) -> dict:
    return {"stem": stem, "branch": branch, "ko": STEMS[stem] + BRANCHES[branch], "hanja": STEMS_HANJA[stem] + BRANCHES_HANJA[branch]}


def _year_pillar(y: int) -> dict:
    return _pillar((y - 4) % 10, (y - 4) % 12)


# 2027년 달력 1월~12월(신년운세 리포트와 같은 열두 달): 1월은 병오년의 마지막 달 신축(소한부터), 2월~12월은 임인~임자.
MONTHS_2027 = [{**_pillar(7, 1), "label": "1월"}] + [{**_pillar((8 + k) % 10, (2 + k) % 12), "label": f"{k + 2}월"} for k in range(11)]


def _weakest(elements: dict) -> str:
    """가장 모자란 기운(같으면 뒤 순서). 사이트 reveal.mjs weakest 와 같다."""
    ordered = sorted(ELEMENTS, key=lambda e: -elements[e])   # 안정 정렬: 같은 값은 원래 순서
    return ordered[-1]


def _marker(fp: FourPillars, sex: str):
    ds, db = fp.day.stem, fp.day.branch
    st = A.strength(fp)["score"]
    weak = ELEMENTS.index(_weakest(A.element_strength(fp)))
    gods = lambda p: [A.ten_god(ds, p["stem"]), A.branch_ten_god(ds, p["branch"])]
    has = lambda p, names: any(g in names for g in gods(p))
    group = lambda p, gs: any(TEN_GOD_GROUP[g] in gs for g in gods(p))
    rel = lambda p: {r.split("(")[0] for r in A.branch_relation(db, p["branch"])}
    helpful = ["식상", "재성", "관성"] if st >= 55 else ["인성", "비겁"] if st <= 45 else None
    rule = {
        "money": lambda p: group(p, ["재성"]),
        "rob": lambda p: has(p, ["겁재"]),
        "job": lambda p: group(p, ["관성"]),
        "boss": lambda p: has(p, ["상관"]),
        "bigmoney": lambda p: has(p, ["편재"]),
        "make": lambda p: has(p, ["식신"]),
        "love": lambda p: group(p, ["관성" if sex == "female" else "재성"]),
        # 연애사주(사장님 2026-10-30): '인연의 별' 하나로 묶지 않고 배우자 별·도화·합을 따로 짚는다
        "spouse": lambda p: has(p, ["정관" if sex == "female" else "정재"]),
        "peach": lambda p: p["branch"] == PEACH_OF[db],
        # 재회사주: 배우자 자리와 육합하는 달이 가장 좋은 달, 반합하는 달이 다시 이어지기 쉬운 달
        "best_re": lambda p: "육합" in rel(p),
        "hap_re": lambda p: "반합" in rel(p) and "육합" not in rel(p),
        "hap": lambda p: bool(rel(p) & {"육합", "반합"}),
        "clash": lambda p: "충" in rel(p),
        "fill": lambda p: STEM_EL[p["stem"]] == weak or BRANCH_EL[p["branch"]] == weak,
        "help": lambda p: (TEN_GOD_GROUP[A.branch_ten_god(ds, p["branch"])] in helpful) if helpful else BRANCH_EL[p["branch"]] == weak,
    }

    def rule_of(key: str):
        if key in rule:
            return rule[key]
        for prefix in ("clash", "hap", "love", "spouse"):
            if key.startswith(prefix):
                return rule[prefix]
        return rule[key]
    return ELEMENTS[weak], rule_of


def _mark_key(key: str, sex: str) -> str:
    return key + ("_f" if sex == "female" else "_m") if key in ("love", "spouse") else key


def ny_verdict(fp: FourPillars, sex: str) -> tuple[str, int]:
    """무료 풀이 '2027년 운'이 좋은 쪽인지 조심할 쪽인지와 그 점수. 맛보기 TOP3에 든 쪽을 따르고, 들지 않았으면 50점 이상이 좋은 쪽.
    평생사주 12년 지도의 2027년 칸과 리포트의 2027년 점수가 이것을 그대로 따른다(제1조항: 한 고객에게 2027년이 좋다·나쁘다를 엇갈리게 말하지 않는다)."""
    r = taster.reading(fp, "", sex)
    score = r["scores"]["newyear"]
    if any(a["id"] == "newyear" for a in r["good"]):
        return "good", score
    if any(a["id"] == "newyear" for a in r["bad"]):
        return "bad", score
    return ("good" if score >= 50 else "bad"), score


def year_marks(fp: FourPillars, sex: str, product: str, label: str, good: list[str], bad: list[str]) -> tuple[list[str], list[str]]:
    """한 칸에 붙일 표시. 평생사주의 2027년 칸은 무료 풀이 '2027년 운'과 같은 쪽 표시만 남긴다(없으면 '2027년 좋은 흐름'·'2027년 조심' 표시).
    신년운세의 한 달에는 좋은 표시와 조심할 표시를 함께 붙이지 않는다."""
    if product == "newyear" and good and bad:   # 한 달에 '돕는 달'과 '조심할 달'을 함께 붙이지 않는다: 부딪힘(충)이 있으면 조심할 달
        return [], bad
    if product != "lifetime" or label != "2027":
        return good, bad
    side, _ = ny_verdict(fp, sex)
    return (good or ["ny_good"], []) if side == "good" else ([], bad or ["ny_bad"])


def month_pillar_of(year: int, month: int) -> dict:
    """달력 year년 month월에 시작하는 달(절기 기준, 매달 4~8일 무렵 시작)의 간지. 1월은 앞 해의 마지막 달(축월)."""
    return months_of(year - 1)[11] if month == 1 else months_of(year)[month - 2]


def reunion_months(start: tuple[int, int]) -> list[dict]:
    """재회사주 지도: start(해, 달)부터 24개월. 이름은 '2027년 3월'처럼."""
    y, m = start
    out = []
    for _ in range(REUNION_MONTHS):
        out.append({**month_pillar_of(y, m), "label": f"{y}년 {m}월"})
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def start_month(when, shown: str = "") -> tuple[int, int]:
    """재회사주 지도의 첫 달: 주문(화면을 본) 날이 15일까지면 그 달, 16일부터는 다음 달. 사이트 reveal_page.js 와 같다.
    shown('2026-11'): 손님이 결제 전 화면에서 실제로 본 첫 달(주문에 함께 온다). 주문한 달 앞뒤 한 달 안이면 그 달을 그대로 쓴다
    (15일 밤에 화면을 보고 16일에 결제해도 화면과 리포트가 같은 24개월을 본다 — 제1조항).
    해만 주어지면 그 해(2027년보다 이르면 2027년) 1월."""
    if isinstance(when, int):
        return (start_year(when), 1)
    s = when if isinstance(when, str) else when.isoformat()
    y, m, d = int(s[:4]), int(s[5:7]), int(s[8:10])
    if isinstance(shown, str) and len(shown) == 7 and shown[4] == "-" and shown[:4].isdigit() and shown[5:].isdigit():
        sy, sm = int(shown[:4]), int(shown[5:])
        if 1 <= sm <= 12 and abs((sy * 12 + sm) - (y * 12 + m)) <= 1:
            return (sy, sm)
    return (y, m) if d <= 15 else ((y + 1, 1) if m == 12 else (y, m + 1))


def _year_of(when) -> int:
    return when if isinstance(when, int) else int((when if isinstance(when, str) else when.isoformat())[:4])


def luck_map(fp: FourPillars, sex: str, product: str, start_year: int = FIRST_YEAR, start: tuple[int, int] | None = None) -> dict:
    """사이트 reveal.mjs luckMap 과 같은 지도. 재회사주는 start(해, 달)부터 24개월(없으면 start_year년 1월부터)."""
    conf = taster.texts()["REVEAL"]["PRODUCTS"][product]
    weak, rule_of = _marker(fp, sex)
    unit = "month" if product in ("newyear", "reunion") else "year"
    base = (reunion_months(start or (start_year, 1)) if product == "reunion" else MONTHS_2027) if unit == "month" else \
        [{**_year_pillar(start_year + i), "label": str(start_year + i)} for i in range(12)]
    good: dict[str, list[str]] = {}
    bad: dict[str, list[str]] = {}
    cells = []
    for p in base:
        cell = {"label": p["label"], "ko": p["ko"], "hanja": p["hanja"]}
        cell["good"], cell["bad"] = year_marks(fp, sex, product, p["label"],
                                               [_mark_key(k, sex) for k in conf["good"] if rule_of(k)(p)],
                                               [_mark_key(k, sex) for k in conf["bad"] if rule_of(k)(p)])
        for kind, into in (("good", good), ("bad", bad)):
            for key in cell[kind]:
                into.setdefault(key, []).append(p["label"])
        cells.append(cell)
    return {"unit": unit, "cells": cells, "good": good, "bad": bad, "weak": weak}


def months_of(year: int) -> list[dict]:
    """그 해(입춘부터)의 열두 달 간지. 갑·기년의 첫 달은 병인, 을·경년은 무인 … (연간으로 첫 달 천간이 정해진다)."""
    first = ((year - 4) % 10 % 5 * 2 + 2) % 10
    return [{**_pillar((first + k) % 10, (2 + k) % 12), "label": f"{year + 1}년 1월" if k == 11 else f"{k + 2}월"} for k in range(12)]


def months_in_year(fp: FourPillars, sex: str, key: str, year: int) -> list[str]:
    """화면에 보인 해 안에서 같은 규칙의 기운이 실제로 들어오는 달(절기 기준). 리포트가 '몇 월'을 이 계산으로 쓴다."""
    if key.startswith("ny_"):   # 2027년 좋은 흐름·조심: 신년운세 열두 달 지도에서 같은 쪽 표시가 붙은 달
        m = luck_map(fp, sex, "newyear")
        return [c["label"] for c in m["cells"] if c["good" if key == "ny_good" else "bad"]] if year == 2027 else []
    _, rule_of = _marker(fp, sex)
    base = key[:-2] if key.endswith(("_m", "_f")) and key[:-2] in ("love", "spouse") else key
    return [mp["label"] for mp in months_of(year) if rule_of(base)(mp)]


def screen_map(fp: FourPillars, sex: str, product: str, when, shown: str = "") -> dict:
    """주문한 날(또는 해)에 고객이 결제 전 화면에서 본 지도. shown: 재회사주 화면의 첫 달(주문에 함께 온 값)."""
    return luck_map(fp, sex, product, start_year(_year_of(when)), start_month(when, shown))


def shown_labels(fp: FourPillars, sex: str, product: str, order_year, shown: str = "") -> list[str]:
    """화면에 보인 해·달 이름(리포트에 빠짐없이 나와야 하는 것). 해는 '2034년', 달은 '4월'(재회사주는 '2027년 4월')처럼."""
    m = screen_map(fp, sex, product, order_year, shown)
    labels = [lb for d in (m["good"], m["bad"]) for lbs in d.values() for lb in lbs]
    return list(dict.fromkeys(lb if m["unit"] == "month" else f"{lb}년" for lb in labels))


def side_score(n: int, kind: str, total: int = 12) -> int:
    """근거가 한쪽에만 있을 때 다른 쪽 점수: 12년(12달, 재회사주는 24개월) 중 그런 해(달)가 몇 번인지로 매긴다. 사이트 reveal_page.js 와 같은 식."""
    step = int(50 * n / total + 0.5)   # 자바스크립트 Math.round 와 같게(반올림)
    return min(95, 50 + step) if kind == "good" else max(5, 50 - step)


def start_year(order_year: int) -> int:
    return max(FIRST_YEAR, order_year)


def digest(fp: FourPillars, name: str, sex: str, product: str, order_year, shown: str = "") -> dict:
    """리포트 글쓰기에 넘길 '결제 전 이야기 화면에서 본 내용'."""
    T = taster.texts()["REVEAL"]
    name = (name or "").strip() or "고객"
    m = screen_map(fp, sex, product, order_year, shown)
    unit = "달" if m["unit"] == "month" else "해"
    unit_obj = "달을" if m["unit"] == "month" else "해를"

    def rows(d: dict) -> list[dict]:
        out = []
        for key, labels in d.items():
            mk = T["MARKS"][key]
            vals = {"name": name, "weak": f"{m['weak']}"}
            row = {unit: [lb if m["unit"] == "month" else f"{lb}년" for lb in labels],
                   "뜻": taster.fill(mk["line"], vals), "화면에서 본 설명": taster.fill(mk["meaning"], vals)}
            if m["unit"] == "year":
                row["그 해 안에서 같은 기운이 들어오는 달(절기 기준, 매달 4~8일 무렵 시작)"] = {
                    f"{lb}년": months_in_year(fp, sex, key, int(lb)) for lb in labels}
            out.append(row)
        return out
    out = {
        "읽는 법": (f"이 고객은 결제 직전 화면에서 아래 {unit_obj} 그대로 보았습니다. 화면은 그 {unit}에 "
                  f"{'무엇을, 어떻게' if m['unit'] == 'month' else '몇 월에, 무엇을, 어떻게'} 해야 하는지는 리포트에 있다고 안내했습니다. "
                  f"리포트는 이 {unit_obj} 빠짐없이 다시 꺼내, 좋은 표시는 그 운을 크게 받는 구체적인 시기와 방법을, "
                  "조심할 표시는 언제 조심하고 어떻게 막는지를 씁니다. 화면에서 본 것과 반대되는 해석은 쓰지 않습니다. "
                  + ("'몇 월'은 아래 '그 해 안에서 같은 기운이 들어오는 달'에 계산된 달만 씁니다. 다른 달을 지어내지 않습니다. "
                     if m["unit"] == "year" else "")
                  + f"화면에 나온 {unit_obj} 하나도 빠뜨리지 않고 '{m['cells'][3]['label'] if m['unit'] == 'month' else '2034년'}'처럼 이름을 그대로 적습니다."),
        "리포트에 나와야 하는 해·달": shown_labels(fp, sex, product, order_year, shown),
        f"좋은 {unit}": rows(m["good"]),
        f"조심할 {unit}": rows(m["bad"]),
    }
    if product != "lifetime":
        pt = taster.area_parts(fp, name, sex, product)
        title = taster.texts()["AREAS"][product]["title"]
        out["화면에서 본 점수"] = {
            "운": title, "전체 점수": pt["score"],
            "좋은 점": {"점수": pt["good"]["score"], "글": pt["good"]["text"]} if pt["good"] else
                     {"점수": side_score(len({lb for ls in m["good"].values() for lb in ls}), "good", len(m["cells"])), "글": f"앞으로 운이 들어오는 {unit}(아래 '좋은 {unit}')로 매긴 점수"},
            "조심할 점": {"점수": pt["bad"]["score"], "글": pt["bad"]["text"]} if pt["bad"] else
                      {"점수": side_score(len({lb for ls in m["bad"].values() for lb in ls}), "bad", len(m["cells"])), "글": f"앞으로 조심할 {unit}(아래 '조심할 {unit}')로 매긴 점수"},
            "쓸 점": "화면은 이 운의 좋은 점과 조심할 점을 모두 짚었습니다. 리포트는 두 가지 모두를 더 깊게 풀고, "
                    "좋은 점은 크게 받는 시기와 방법을, 조심할 점은 막는 시기와 방법을 씁니다.",
        }
    return out
