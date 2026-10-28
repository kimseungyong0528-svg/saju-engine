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


def _pillar(stem: int, branch: int) -> dict:
    return {"stem": stem, "branch": branch, "ko": STEMS[stem] + BRANCHES[branch], "hanja": STEMS_HANJA[stem] + BRANCHES_HANJA[branch]}


def _year_pillar(y: int) -> dict:
    return _pillar((y - 4) % 10, (y - 4) % 12)


# 2027년(정미년) 열두 달: 인월(2월, 입춘부터) ~ 축월(2028년 1월).
MONTHS_2027 = [{**_pillar((8 + k) % 10, (2 + k) % 12), "label": "2028년 1월" if k == 11 else f"{k + 2}월"} for k in range(12)]


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
        "hap": lambda p: bool(rel(p) & {"육합", "반합"}),
        "clash": lambda p: "충" in rel(p),
        "fill": lambda p: STEM_EL[p["stem"]] == weak or BRANCH_EL[p["branch"]] == weak,
        "help": lambda p: (TEN_GOD_GROUP[A.branch_ten_god(ds, p["branch"])] in helpful) if helpful else BRANCH_EL[p["branch"]] == weak,
    }

    def rule_of(key: str):
        for prefix in ("clash", "hap", "love"):
            if key.startswith(prefix):
                return rule[prefix]
        return rule[key]
    return ELEMENTS[weak], rule_of


def _mark_key(key: str, sex: str) -> str:
    return ("love_f" if sex == "female" else "love_m") if key == "love" else key


def luck_map(fp: FourPillars, sex: str, product: str, start_year: int = FIRST_YEAR) -> dict:
    """사이트 reveal.mjs luckMap 과 같은 지도."""
    conf = taster.texts()["REVEAL"]["PRODUCTS"][product]
    weak, rule_of = _marker(fp, sex)
    unit = "month" if product == "newyear" else "year"
    base = MONTHS_2027 if unit == "month" else [{**_year_pillar(start_year + i), "label": str(start_year + i)} for i in range(12)]
    good: dict[str, list[str]] = {}
    bad: dict[str, list[str]] = {}
    cells = []
    for p in base:
        cell = {"label": p["label"], "ko": p["ko"], "hanja": p["hanja"], "good": [], "bad": []}
        for kind, keys, into in (("good", conf["good"], good), ("bad", conf["bad"], bad)):
            for k in keys:
                if rule_of(k)(p):
                    key = _mark_key(k, sex)
                    cell[kind].append(key)
                    into.setdefault(key, []).append(p["label"])
        cells.append(cell)
    return {"unit": unit, "cells": cells, "good": good, "bad": bad, "weak": weak}


def months_of(year: int) -> list[dict]:
    """그 해(입춘부터)의 열두 달 간지. 갑·기년의 첫 달은 병인, 을·경년은 무인 … (연간으로 첫 달 천간이 정해진다)."""
    first = ((year - 4) % 10 % 5 * 2 + 2) % 10
    return [{**_pillar((first + k) % 10, (2 + k) % 12), "label": f"{year + 1}년 1월" if k == 11 else f"{k + 2}월"} for k in range(12)]


def months_in_year(fp: FourPillars, sex: str, key: str, year: int) -> list[str]:
    """화면에 보인 해 안에서 같은 규칙의 기운이 실제로 들어오는 달(절기 기준). 리포트가 '몇 월'을 이 계산으로 쓴다."""
    _, rule_of = _marker(fp, sex)
    base = "love" if key.startswith("love") else key
    return [mp["label"] for mp in months_of(year) if rule_of(base)(mp)]


def shown_labels(fp: FourPillars, sex: str, product: str, order_year: int) -> list[str]:
    """화면에 보인 해·달 이름(리포트에 빠짐없이 나와야 하는 것). 해는 '2034년', 달은 '4월'처럼."""
    m = luck_map(fp, sex, product, start_year(order_year))
    labels = [lb for d in (m["good"], m["bad"]) for lbs in d.values() for lb in lbs]
    return list(dict.fromkeys(lb if m["unit"] == "month" else f"{lb}년" for lb in labels))


def side_score(n: int, kind: str) -> int:
    """근거가 한쪽에만 있을 때 다른 쪽 점수: 12년(12달) 중 그런 해(달)가 몇 번인지로 매긴다. 사이트 reveal_page.js 와 같은 식."""
    step = int(50 * n / 12 + 0.5)   # 자바스크립트 Math.round 와 같게(반올림)
    return min(95, 50 + step) if kind == "good" else max(5, 50 - step)


def start_year(order_year: int) -> int:
    return max(FIRST_YEAR, order_year)


def digest(fp: FourPillars, name: str, sex: str, product: str, order_year: int) -> dict:
    """리포트 글쓰기에 넘길 '결제 전 이야기 화면에서 본 내용'."""
    T = taster.texts()["REVEAL"]
    name = (name or "").strip() or "고객"
    m = luck_map(fp, sex, product, start_year(order_year))
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
                  + f"화면에 나온 {unit_obj} 하나도 빠뜨리지 않고 '{'4월' if m['unit'] == 'month' else '2034년'}'처럼 이름을 그대로 적습니다."),
        "리포트에 나와야 하는 해·달": shown_labels(fp, sex, product, order_year),
        f"좋은 {unit}": rows(m["good"]),
        f"조심할 {unit}": rows(m["bad"]),
    }
    if product != "lifetime":
        pt = taster.area_parts(fp, name, sex, product)
        title = taster.texts()["AREAS"][product]["title"]
        out["화면에서 본 점수"] = {
            "운": title, "전체 점수": pt["score"],
            "좋은 점": {"점수": pt["good"]["score"], "글": pt["good"]["text"]} if pt["good"] else
                     {"점수": side_score(len({lb for ls in m["good"].values() for lb in ls}), "good"), "글": f"앞으로 운이 들어오는 {unit}(아래 '좋은 {unit}')로 매긴 점수"},
            "조심할 점": {"점수": pt["bad"]["score"], "글": pt["bad"]["text"]} if pt["bad"] else
                      {"점수": side_score(len({lb for ls in m["bad"].values() for lb in ls}), "bad"), "글": f"앞으로 조심할 {unit}(아래 '조심할 {unit}')로 매긴 점수"},
            "쓸 점": "화면은 이 운의 좋은 점과 조심할 점을 모두 짚었습니다. 리포트는 두 가지 모두를 더 깊게 풀고, "
                    "좋은 점은 크게 받는 시기와 방법을, 조심할 점은 막는 시기와 방법을 씁니다.",
        }
    return out
