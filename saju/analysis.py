"""원국 분석: 오행, 십신, 12운성, 합충형파해, 신살, 신강약, 격국, 용신 후보."""

from __future__ import annotations

from collections import Counter
from itertools import combinations

from .constants import (
    BRANCH_ELEMENT, BRANCHES, ELEMENTS, HIDDEN_STEMS, PILLAR_NAMES, STAGE_START, STEM_ELEMENT,
    STEM_YANG, STEMS, TEN_GOD_GROUP, TEN_GODS, TWELVE_STAGES, main_hidden_stem,
)
from .pillars import FourPillars, Pillar


# ── 십신 · 12운성 ────────────────────────────────────────────────

def ten_god(day_stem: int, other_stem: int) -> str:
    me, other = STEM_ELEMENT[day_stem], STEM_ELEMENT[other_stem]
    same_polarity = STEM_YANG[day_stem] == STEM_YANG[other_stem]
    rel = (other - me) % 5  # 0 같음, 1 내가 생함, 2 내가 극함, 3 나를 극함, 4 나를 생함
    return TEN_GODS[rel * 2 + (0 if same_polarity else 1)]


def branch_ten_god(day_stem: int, branch: int) -> str:
    return ten_god(day_stem, main_hidden_stem(branch))


def twelve_stage(stem: int, branch: int) -> str:
    start = STAGE_START[stem]
    step = (branch - start) % 12 if STEM_YANG[stem] else (start - branch) % 12
    return TWELVE_STAGES[step]


# ── 오행 분포 ───────────────────────────────────────────────────

def element_counts(fp: FourPillars) -> dict[str, int]:
    """여덟 글자(천간 + 지지 본 오행) 기준 개수."""
    c = Counter()
    for p in fp.as_list():
        if p is None:
            continue
        c[ELEMENTS[STEM_ELEMENT[p.stem]]] += 1
        c[ELEMENTS[BRANCH_ELEMENT[p.branch]]] += 1
    return {e: c.get(e, 0) for e in ELEMENTS}


# 자리별 가중치: 월지가 가장 크고, 일지·시지 순
_STEM_WEIGHT = [1.0, 1.0, 1.0, 1.0]
_BRANCH_WEIGHT = [1.0, 2.0, 1.5, 1.0]


def element_strength(fp: FourPillars) -> dict[str, float]:
    """지장간 비율과 자리별 가중치를 반영한 오행 세력(합계 100 기준)."""
    score = Counter()
    for i, p in enumerate(fp.as_list()):
        if p is None:
            continue
        score[STEM_ELEMENT[p.stem]] += _STEM_WEIGHT[i]
        total_days = sum(days for _, days in HIDDEN_STEMS[p.branch])
        for stem, days in HIDDEN_STEMS[p.branch]:
            score[STEM_ELEMENT[stem]] += _BRANCH_WEIGHT[i] * days / total_days
    total = sum(score.values())
    return {ELEMENTS[e]: round(score.get(e, 0) * 100 / total, 1) for e in range(5)}


def element_judgement(strength: dict[str, float]) -> dict[str, list[str]]:
    excess = [e for e, v in strength.items() if v >= 30]
    lacking = [e for e, v in strength.items() if v < 8]
    return {"과다": excess, "부족": lacking}


# ── 합 · 충 · 형 · 파 · 해 ──────────────────────────────────────

STEM_COMBINE = {frozenset({0, 5}): "토", frozenset({1, 6}): "금", frozenset({2, 7}): "수",
                frozenset({3, 8}): "목", frozenset({4, 9}): "화"}
STEM_CLASH = {frozenset({0, 6}), frozenset({1, 7}), frozenset({2, 8}), frozenset({3, 9})}

SIX_COMBINE = {frozenset({0, 1}): "토", frozenset({2, 11}): "목", frozenset({3, 10}): "화",
               frozenset({4, 9}): "금", frozenset({5, 8}): "수", frozenset({6, 7}): "화"}
THREE_COMBINE = {(8, 0, 4): "수", (11, 3, 7): "목", (2, 6, 10): "화", (5, 9, 1): "금"}  # 생지·왕지·고지
DIRECTION_COMBINE = {(2, 3, 4): "목", (5, 6, 7): "화", (8, 9, 10): "금", (11, 0, 1): "수"}
CLASH = {frozenset({0, 6}), frozenset({1, 7}), frozenset({2, 8}), frozenset({3, 9}),
         frozenset({4, 10}), frozenset({5, 11})}
PUNISH_GROUPS = [({2, 5, 8}, "인사신 삼형"), ({1, 10, 7}, "축술미 삼형")]
PUNISH_PAIR = {frozenset({0, 3}): "자묘 상형"}
SELF_PUNISH = {4, 6, 9, 11}
BREAK = {frozenset({0, 9}), frozenset({1, 4}), frozenset({2, 11}), frozenset({3, 6}),
         frozenset({5, 8}), frozenset({7, 10})}
HARM = {frozenset({0, 7}), frozenset({1, 6}), frozenset({2, 5}), frozenset({3, 4}),
        frozenset({8, 11}), frozenset({9, 10})}
WONJIN = {frozenset({0, 7}), frozenset({1, 6}), frozenset({2, 9}), frozenset({3, 8}),
          frozenset({4, 11}), frozenset({5, 10})}


def stem_relation(a: int, b: int) -> list[str]:
    out = []
    pair = frozenset({a, b})
    if pair in STEM_COMBINE:
        out.append(f"천간합({STEM_COMBINE[pair]})")
    if pair in STEM_CLASH:
        out.append("천간충")
    return out


def branch_relation(a: int, b: int) -> list[str]:
    out = []
    pair = frozenset({a, b})
    if pair in SIX_COMBINE:
        out.append(f"육합({SIX_COMBINE[pair]})")
    for trio, el in THREE_COMBINE.items():
        if a != b and {a, b} <= set(trio) and trio[1] in (a, b):
            out.append(f"반합({el})")
    if pair in CLASH:
        out.append("충")
    if pair in PUNISH_PAIR:
        out.append("형")
    for group, _ in PUNISH_GROUPS:
        if a != b and {a, b} <= group:
            out.append("형")
    if a == b and a in SELF_PUNISH:
        out.append("자형")
    if pair in BREAK:
        out.append("파")
    if pair in HARM:
        out.append("해")
    if pair in WONJIN:
        out.append("원진")
    return out


def natal_relations(fp: FourPillars) -> list[dict]:
    """원국 안의 천간·지지 관계 목록."""
    pillars = [(PILLAR_NAMES[i], p) for i, p in enumerate(fp.as_list()) if p is not None]
    out = []
    for (na, a), (nb, b) in combinations(pillars, 2):
        for r in stem_relation(a.stem, b.stem):
            out.append({"type": r, "between": [na, nb], "chars": STEMS[a.stem] + STEMS[b.stem], "level": "천간"})
        for r in branch_relation(a.branch, b.branch):
            out.append({"type": r, "between": [na, nb], "chars": BRANCHES[a.branch] + BRANCHES[b.branch], "level": "지지"})
    branches = {p.branch for _, p in pillars}
    for trio, el in THREE_COMBINE.items():
        if set(trio) <= branches:
            out.append({"type": f"삼합({el})", "chars": "".join(BRANCHES[b] for b in trio), "level": "지지"})
    for trio, el in DIRECTION_COMBINE.items():
        if set(trio) <= branches:
            out.append({"type": f"방합({el})", "chars": "".join(BRANCHES[b] for b in trio), "level": "지지"})
    for group, name in PUNISH_GROUPS:
        if group <= branches:
            out.append({"type": name, "chars": "".join(BRANCHES[b] for b in sorted(group)), "level": "지지"})
    return out


# ── 신살 ───────────────────────────────────────────────────────

def _samhap_group(branch: int) -> int:
    return {8: 0, 0: 0, 4: 0, 2: 1, 6: 1, 10: 1, 5: 2, 9: 2, 1: 2, 11: 3, 3: 3, 7: 3}[branch]


_DOHWA = [9, 3, 6, 0]     # 신자진→유, 인오술→묘, 사유축→오, 해묘미→자
_YEOKMA = [2, 8, 11, 5]
_HWAGAE = [4, 10, 1, 7]
_CHEONEUL = {0: (1, 7), 4: (1, 7), 6: (1, 7), 1: (0, 8), 5: (0, 8), 2: (11, 9), 3: (11, 9),
             7: (2, 6), 8: (5, 3), 9: (5, 3)}
_MUNCHANG = {0: 5, 1: 6, 2: 8, 3: 9, 4: 8, 5: 9, 6: 11, 7: 0, 8: 2, 9: 3}
_YANGIN = {0: 3, 2: 6, 4: 6, 6: 9, 8: 0}
_HONGYEOM = {0: 6, 1: 6, 2: 2, 3: 7, 4: 4, 5: 4, 6: 10, 7: 9, 8: 0, 9: 8}
_GOEGANG = {"경진", "경술", "임진", "임술", "무술"}
_BAEKHO = {"갑진", "을미", "병술", "정축", "무진", "임술", "계축"}


def void_branches(day: Pillar) -> tuple[int, int]:
    """일주 기준 공망 두 지지."""
    start = day.index - day.index % 10  # 그 순(旬)의 갑X
    first_branch = start % 12
    return ((first_branch + 10) % 12, (first_branch + 11) % 12)


def shinsal(fp: FourPillars) -> list[dict]:
    day = fp.day
    pillars = [(PILLAR_NAMES[i], p) for i, p in enumerate(fp.as_list()) if p is not None]
    out: list[dict] = []

    def add(name, where, basis):
        out.append({"name": name, "pillar": where, "basis": basis})

    for basis_name, basis in (("년지", fp.year.branch), ("일지", day.branch)):
        g = _samhap_group(basis)
        for where, p in pillars:
            if where in ("년주",) and basis_name == "년지":
                continue
            if p.branch == _DOHWA[g]:
                add("도화살", where, basis_name)
            if p.branch == _YEOKMA[g]:
                add("역마살", where, basis_name)
            if p.branch == _HWAGAE[g]:
                add("화개살", where, basis_name)
    for where, p in pillars:
        if p.branch in _CHEONEUL[day.stem]:
            add("천을귀인", where, "일간")
        if p.branch == _MUNCHANG[day.stem]:
            add("문창귀인", where, "일간")
        if _YANGIN.get(day.stem) == p.branch:
            add("양인살", where, "일간")
        if _HONGYEOM[day.stem] == p.branch:
            add("홍염살", where, "일간")
        if p.korean in _BAEKHO:
            add("백호살", where, "간지")
    if day.korean in _GOEGANG:
        add("괴강살", "일주", "간지")
    void = void_branches(day)
    for where, p in pillars:
        if where != "일주" and p.branch in void:
            add("공망", where, "일주")
    # 같은 이름·자리 중복 제거
    seen, uniq = set(), []
    for s in out:
        k = (s["name"], s["pillar"])
        if k not in seen:
            seen.add(k)
            uniq.append(s)
    return uniq


# ── 신강·신약, 격국, 용신 후보 ─────────────────────────────────

def _supports(day_stem: int, element: int) -> bool:
    me = STEM_ELEMENT[day_stem]
    return element == me or element == (me - 1) % 5  # 비겁 또는 인성


def strength(fp: FourPillars) -> dict:
    """일간의 힘. 득령(월지)·득지(일지)·득세(나머지)를 점수화."""
    ds = fp.day.stem
    support = drain = 0.0
    weights_stem = {"년주": 10, "월주": 10, "시주": 10}
    weights_branch = {"년주": 10, "월주": 30, "일주": 15, "시주": 10}
    detail = {}
    for i, p in enumerate(fp.as_list()):
        if p is None:
            continue
        name = PILLAR_NAMES[i]
        if name in weights_stem:
            w = weights_stem[name]
            if _supports(ds, STEM_ELEMENT[p.stem]):
                support += w
            else:
                drain += w
        w = weights_branch[name]
        total_days = sum(d for _, d in HIDDEN_STEMS[p.branch])
        s = sum(d for st, d in HIDDEN_STEMS[p.branch] if _supports(ds, STEM_ELEMENT[st])) / total_days
        support += w * s
        drain += w * (1 - s)
        if name == "월주":
            detail["득령"] = _supports(ds, STEM_ELEMENT[main_hidden_stem(p.branch)])
        if name == "일주":
            detail["득지"] = _supports(ds, STEM_ELEMENT[main_hidden_stem(p.branch)])
    score = round(support / (support + drain) * 100, 1)
    if score >= 70:
        label = "극신강"
    elif score >= 55:
        label = "신강"
    elif score > 45:
        label = "중화"
    elif score > 30:
        label = "신약"
    else:
        label = "극신약"
    return {"score": score, "label": label, **detail}


def gyeokguk(fp: FourPillars) -> dict:
    """월지 기준 내격 판단. 월지 지장간 중 천간에 드러난(투출) 것을 우선한다."""
    ds = fp.day.stem
    mb = fp.month.branch
    visible = {p.stem for i, p in enumerate(fp.as_list()) if p is not None and i != 2}
    chosen = main_hidden_stem(mb)
    reason = "월지 정기"
    if ten_god(ds, chosen) not in ("비견", "겁재"):
        for stem, _ in reversed(HIDDEN_STEMS[mb]):  # 정기 → 중기 → 여기
            # 비겁은 격으로 쓰지 않으므로 투출 후보에서 뺀다
            if stem in visible and ten_god(ds, stem) not in ("비견", "겁재"):
                chosen, reason = stem, ("월지 정기 투출" if stem == chosen else "월지 지장간 투출")
                break
    god = ten_god(ds, chosen)
    if god == "비견" or (god == "겁재" and not STEM_YANG[ds]):
        name = "건록격"
    elif god == "겁재":
        name = "양인격"
    else:
        name = f"{god}격"
    return {"name": name, "ten_god": god, "stem": STEMS[chosen], "reason": reason}


def yongsin_candidates(fp: FourPillars, st: dict) -> dict:
    """억부와 조후로 본 용신 후보(해석에 쓰는 후보)."""
    me = STEM_ELEMENT[fp.day.stem]
    names = lambda els: [ELEMENTS[e] for e in els]
    if st["score"] >= 55:
        eokbu = names([(me + 1) % 5, (me + 2) % 5, (me + 3) % 5])  # 식상·재성·관성
        basis = "신강하여 기운을 덜어주는 식상·재성·관성"
    elif st["score"] <= 45:
        eokbu = names([(me - 1) % 5, me])  # 인성·비겁
        basis = "신약하여 힘을 보태는 인성·비겁"
    else:
        eokbu, basis = [], "중화에 가까워 억부보다 조후와 흐름을 우선"
    mb = fp.month.branch
    johu = []
    if mb in (5, 6, 7):
        johu = ["수"]
    elif mb in (11, 0, 1):
        johu = ["화"]
    return {"억부": eokbu, "억부_근거": basis, "조후": johu}


def ten_god_table(fp: FourPillars) -> list[dict]:
    ds = fp.day.stem
    rows = []
    for i, p in enumerate(fp.as_list()):
        if p is None:
            rows.append({"pillar": PILLAR_NAMES[i], "unknown": True})
            continue
        rows.append({
            "pillar": PILLAR_NAMES[i],
            "ganzhi": p.korean,
            "hanja": p.hanja,
            "stem": STEMS[p.stem],
            "branch": BRANCHES[p.branch],
            "stem_element": ELEMENTS[STEM_ELEMENT[p.stem]],
            "branch_element": ELEMENTS[BRANCH_ELEMENT[p.branch]],
            "stem_ten_god": "일간" if i == 2 else ten_god(ds, p.stem),
            "branch_ten_god": branch_ten_god(ds, p.branch),
            "hidden_stems": [{"stem": STEMS[s], "ten_god": ten_god(ds, s), "days": d} for s, d in HIDDEN_STEMS[p.branch]],
            "twelve_stage": twelve_stage(ds, p.branch),
        })
    return rows


def ten_god_counts(fp: FourPillars) -> dict[str, int]:
    ds = fp.day.stem
    c = Counter()
    for i, p in enumerate(fp.as_list()):
        if p is None:
            continue
        if i != 2:
            c[TEN_GOD_GROUP[ten_god(ds, p.stem)]] += 1
        c[TEN_GOD_GROUP[branch_ten_god(ds, p.branch)]] += 1
    return {g: c.get(g, 0) for g in ("비겁", "식상", "재성", "관성", "인성")}
