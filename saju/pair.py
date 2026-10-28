"""두 사람 비교(깊은 궁합 · 재회사주).

한 가지 점수로 단정하지 않고, 관계를 이루는 요소별 근거를 돌려준다.
"""

from __future__ import annotations

from .analysis import branch_relation, element_strength, stem_relation, ten_god
from .constants import BRANCHES, ELEMENTS, STEM_ELEMENT, STEMS, ZODIAC_ANIMALS
from .pillars import FourPillars

_GOOD = {"육합", "반합", "천간합", "삼합"}
_HARD = {"충", "형", "자형", "파", "해", "원진", "천간충"}


def _tone(relations: list[str]) -> str:
    kinds = {r.split("(")[0] for r in relations}
    if kinds & _GOOD and not kinds & _HARD:
        return "조화"
    if kinds & _HARD and not kinds & _GOOD:
        return "긴장"
    if kinds:
        return "복합"
    return "중립"


def _element_relation(a: int, b: int) -> str:
    d = (b - a) % 5
    return ["같은 기운", "내가 상대를 생함", "내가 상대를 극함", "상대가 나를 극함", "상대가 나를 생함"][d]


def compare(me: FourPillars, other: FourPillars) -> dict:
    ea, eb = element_strength(me), element_strength(other)
    my_lack = [e for e, v in ea.items() if v < 10]
    their_lack = [e for e, v in eb.items() if v < 10]
    complement = {
        "상대가_채워주는_나의_부족": [e for e in my_lack if eb[e] >= 20],
        "내가_채워주는_상대의_부족": [e for e in their_lack if ea[e] >= 20],
    }

    day_stem = stem_relation(me.day.stem, other.day.stem)
    day_branch = branch_relation(me.day.branch, other.day.branch)
    year_branch = branch_relation(me.year.branch, other.year.branch)
    month_branch = branch_relation(me.month.branch, other.month.branch)

    cross = []
    pa = [p for p in me.as_list() if p]
    pb = [p for p in other.as_list() if p]
    for x in pa:
        for y in pb:
            cross += stem_relation(x.stem, y.stem) + branch_relation(x.branch, y.branch)
    good = sum(1 for r in cross if r.split("(")[0] in _GOOD)
    hard = sum(1 for r in cross if r.split("(")[0] in _HARD)

    return {
        "day_master": {
            "me": STEMS[me.day.stem], "other": STEMS[other.day.stem],
            "element_relation": _element_relation(STEM_ELEMENT[me.day.stem], STEM_ELEMENT[other.day.stem]),
            "other_as_my_ten_god": ten_god(me.day.stem, other.day.stem),
            "me_as_other_ten_god": ten_god(other.day.stem, me.day.stem),
            "relations": day_stem,
        },
        "spouse_palace": {  # 일지(배우자 자리)끼리
            "me": BRANCHES[me.day.branch], "other": BRANCHES[other.day.branch],
            "relations": day_branch, "tone": _tone(day_branch),
        },
        "zodiac": {
            "me": ZODIAC_ANIMALS[me.year.branch], "other": ZODIAC_ANIMALS[other.year.branch],
            "relations": year_branch, "tone": _tone(year_branch),
        },
        "month_branch": {"relations": month_branch, "tone": _tone(month_branch)},
        "elements": {"me": ea, "other": eb, **complement},
        "cross_relations": {"harmony": good, "tension": hard},
    }


def pair_score(me: FourPillars, other: FourPillars) -> int:
    """두 사람 궁합 점수(48~96). 결제 전 이야기 화면(사이트 reveal.mjs pairScore)과 깊은 궁합·재회사주 리포트가 같은 점수를 쓴다(제1조항)."""
    cmp = compare(me, other)
    s = 62 + 4 * cmp["cross_relations"]["harmony"] - 3 * cmp["cross_relations"]["tension"]
    s += 6 * (len(cmp["elements"]["상대가_채워주는_나의_부족"]) + len(cmp["elements"]["내가_채워주는_상대의_부족"]))
    s += {"조화": 8, "긴장": -8, "복합": 2}.get(cmp["spouse_palace"]["tone"], 0)
    s += {"상대가 나를 생함": 5, "내가 상대를 생함": 5, "같은 기운": 3}.get(cmp["day_master"]["element_relation"], 0)
    s += 4 if any(r.startswith("천간합") for r in cmp["day_master"]["relations"]) else 0
    return max(48, min(96, s))
