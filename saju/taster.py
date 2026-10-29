"""무료 사주 맛보기와 같은 결과(좋은 운 3개, 조심할 운 3개).

사이트 맛보기 화면은 site/public/assets/free/taster.mjs 가 브라우저에서 계산한다.
결제 리포트를 쓸 때 고객이 맛보기에서 본 내용과 어긋나지 않도록, 같은 규칙과 같은 글
(site/public/assets/free/texts.json)을 여기서 파이썬으로 다시 돌린다.
두 쪽이 같은 답을 내는지는 site/tests/taster.test.mjs 가 확인한다(정답표: site/tools/make_taster_fixture.py).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from . import analysis as A
from .constants import BRANCHES, BRANCHES_HANJA, ELEMENTS, STEM_ELEMENT, TEN_GOD_GROUP
from .pillars import FourPillars

TEXTS = Path(__file__).resolve().parents[1] / "site" / "public" / "assets" / "free" / "texts.json"
AREA_ORDER = ["newyear", "romance", "intimate", "reunion", "wealth", "career", "business", "health"]
PREFIX = {"newyear": "ny", "romance": "ro", "intimate": "im", "reunion": "re", "wealth": "we",
          "career": "ca", "business": "bu", "health": "he"}
WHERE = {"년주": "태어난 해", "월주": "태어난 달", "일주": "태어난 날", "시주": "태어난 시"}
HANJA_GOD = {"비견": "比肩", "겁재": "劫財", "식신": "食神", "상관": "傷官", "편재": "偏財", "정재": "正財",
             "편관": "偏官", "정관": "正官", "편인": "偏印", "정인": "正印"}
GROUPS = ["비겁", "식상", "재성", "관성", "인성"]
Y2027 = (3, 7)  # 정미(丁未)


@lru_cache(maxsize=1)
def texts() -> dict:
    return json.loads(TEXTS.read_text(encoding="utf-8"))


def _josa(word: str, pair: str) -> str:
    plain = re.sub(r"\(.*\)$", "", str(word))
    ch = ord(plain[-1]) - 0xAC00
    batchim = 0 <= ch <= 11171 and ch % 28 != 0
    with_b, without = {"이": ("이", "가"), "은": ("은", "는"), "을": ("을", "를"), "와": ("과", "와")}.get(pair, (pair, pair))
    return str(word) + (with_b if batchim else without)


def ieyo(word) -> str:
    """'갑(甲)이에요' / '기(己)예요'처럼 받침에 맞춘 '이에요·예요'(괄호 안은 보지 않는다)."""
    plain = re.sub(r"\(.*\)$", "", str(word))
    ch = ord(plain[-1]) - 0xAC00
    return str(word) + ("이에요" if 0 <= ch <= 11171 and ch % 28 != 0 else "예요")


def _num(v) -> str:
    """자바스크립트와 같은 숫자 글자(4.0 → 4, 4.2 → 4.2)."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def fill(text: str, values: dict) -> str:
    def rep(m):
        k, p = m.group(1), m.group(2)
        if k not in values:
            raise KeyError(f"빈칸 값 없음: {k}")
        v = _num(values[k])
        return _josa(v, p) if p else v
    return re.sub(r"\{(\w+)(?:\|(\S))?\}", rep, text)


def _rels(a: int, b: int) -> set[str]:
    return {r.split("(")[0] for r in A.branch_relation(a, b)}


def _facts(fp: FourPillars, sex: str) -> dict:
    ds, db = fp.day.stem, fp.day.branch
    me = STEM_ELEMENT[ds]
    elements = A.element_strength(fp)
    groups = A.ten_god_counts(fp)
    st = A.strength(fp)
    sh = A.shinsal(fp)
    pillars = [p for p in fp.as_list() if p is not None]
    branches = [p.branch for p in pillars]
    others = [p.branch for p in (fp.year, fp.month, fp.hour) if p is not None]
    day_rel = set().union(*[_rels(db, b) for b in others]) if others else set()
    all_rel = set()
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            all_rel |= _rels(branches[i], branches[j])
    gods = set()
    for i, p in enumerate(fp.as_list()):
        if p is None:
            continue
        if i != 2:
            gods.add(A.ten_god(ds, p.stem))
        gods.add(A.branch_ten_god(ds, p.branch))
    return {"fp": fp, "ds": ds, "db": db, "me": me, "elements": elements, "groups": groups, "st": st["score"],
            "st_label": st["label"], "shinsal": sh, "names": {s["name"] for s in sh}, "day_rel": day_rel,
            "all_rel": all_rel, "gods": gods, "sex": sex, "gyeok": A.gyeokguk(fp)["name"],
            "pct": lambda g: elements[ELEMENTS[(me + GROUPS.index(g)) % 5]]}


def ny_sides(fp: FourPillars, sex: str) -> dict:
    """2027년 정미년의 불(丁)·흙(未)이 이 사주를 돕는지("help")·부담인지("hurt")·어느 쪽도 아닌지(None). 맛보기 '2027년 운' 글과 같은 판단.
    신년운세 리포트가 2027년 두 기운의 역할을 이것으로 쓴다(제1조항: 화면은 '돕는 기운', 리포트는 '기신'처럼 엇갈리지 않게)."""
    f = _facts(fp, sex)
    helpful = ["식상", "재성", "관성"] if f["st"] >= 55 else ["인성", "비겁"] if f["st"] <= 45 else []
    g1 = TEN_GOD_GROUP[A.ten_god(f["ds"], Y2027[0])]
    g2 = TEN_GOD_GROUP[A.branch_ten_god(f["ds"], Y2027[1])]
    return {el: (("help" if g in helpful else "hurt") if helpful else None) for g, el in ((g1, "화"), (g2, "토"))}


def _newyear(f, T):
    out = []
    el_name = lambda e: f"{T['ELEMENT_WORD'][e]}({e})"
    helpful = ["식상", "재성", "관성"] if f["st"] >= 55 else ["인성", "비겁"] if f["st"] <= 45 else []
    g1 = TEN_GOD_GROUP[A.ten_god(f["ds"], Y2027[0])]
    g2 = TEN_GOD_GROUP[A.branch_ten_god(f["ds"], Y2027[1])]
    good, bad = [], []
    for g, el in ((g1, "화"), (g2, "토")):
        if not helpful:
            continue
        (good if g in helpful else bad).append(el)
    if len(good) == 2:
        out.append(("ny_help2", 28, {}))
    elif len(good) == 1:
        out.append(("ny_help1", 14, {"good": el_name(good[0])}))
    if bad:
        out.append(("ny_hurt", -11 * len(bad), {"bad": "과 ".join(el_name(e) for e in bad)}))
    if not helpful:
        out.append(("ny_balance", 6, {}))
    rel = _rels(f["db"], Y2027[1])
    day_branch = f"{BRANCHES[f['db']]}({BRANCHES_HANJA[f['db']]})"
    if "충" in rel:
        out.append(("ny_clash", -16, {}))
    if "육합" in rel or "반합" in rel:
        out.append(("ny_combine", 9, {"dayBranch": day_branch}))
    if "형" in rel:
        out.append(("ny_punish", -8, {"dayBranch": day_branch}))
    if "원진" in rel:
        out.append(("ny_wonjin", -7, {}))
    mb = f["fp"].month.branch
    if mb in (11, 0, 1):
        out.append(("ny_warm", 8, {}))
    if mb in (5, 6, 7):
        out.append(("ny_hot", -7, {}))
    return out


def _romance(f, T):
    out = []
    dohwa = [s for s in f["shinsal"] if s["name"] == "도화살"]
    if dohwa:
        near = next((s for s in dohwa if s["pillar"] in ("일주", "시주")), dohwa[0])
        out.append(("ro_dohwa", 14 + (4 if near["pillar"] in ("일주", "시주") else 0), {"where": WHERE[near["pillar"]]}))
    if "홍염살" in f["names"]:
        out.append(("ro_hongyeom", 8, {}))
    key = "female" if f["sex"] == "female" else "male"
    star = T["STAR"][key]
    sg = "관성" if key == "female" else "재성"
    n = f["groups"][sg]
    heavy = f["pct"](sg) >= 30 and f["st"] <= 45   # 재물운 '재다신약'·직업운 '관성 과다'인 사주에 '딱 맞게'라고 쓰지 않는다(제1조항)
    if n == 0:
        out.append(("ro_nostar", -14, star))
    elif n <= 2 and not heavy:
        out.append(("ro_star", 8, {**star, "count": n}))
    elif n >= 4:
        out.append(("ro_manystar", -10, {**star, "count": n}))
    out.append(("ro_express", 4, {}) if f["groups"]["식상"] >= 1 else ("ro_shy", -7, {}))
    if "충" in f["day_rel"]:
        out.append(("ro_dayclash", -10, {}))
    if "화개살" in f["names"]:
        out.append(("ro_hwagae", -4, {}))
    return out


def _intimate(f, T):
    out = []
    pg = A.branch_ten_god(f["ds"], f["db"])
    palace = f"{pg}({HANJA_GOD[pg]})"
    key = "female" if f["sex"] == "female" else "male"
    best = "정관" if key == "female" else "정재"
    if pg == best:
        out.append(("im_palace_good", 12, {"palaceGod": palace}))
    elif pg in ("정인", "식신"):
        out.append(("im_palace_soft", 6, {"palaceGod": palace}))
    elif pg in T["PALACE_ROUGH"]:
        out.append(("im_palace_rough", -8, {"palaceGod": palace, "palaceMeaning": T["PALACE_ROUGH"][pg]}))
    if "육합" in f["day_rel"]:
        out.append(("im_combine", 8, {}))
    if "충" in f["day_rel"]:
        out.append(("im_clash", -12, {}))
    if "원진" in f["day_rel"]:
        out.append(("im_wonjin", -8, {}))
    if f["sex"] == "male" and f["groups"]["비겁"] >= 3:
        out.append(("im_rival", -10, {"count": f["groups"]["비겁"]}))
    if f["sex"] == "female" and f["groups"]["식상"] >= 3:
        out.append(("im_sangwan", -10, {"count": f["groups"]["식상"]}))
    if best in f["gods"]:
        out.append(("im_steady", 6, T["STEADY"][key]))
    return out


def _reunion(f, T):
    out, g = [], f["groups"]
    if "육합" in f["all_rel"] or "반합" in f["all_rel"]:
        out.append(("re_combine", 8, {}))
    if "화개살" in f["names"]:
        out.append(("re_hwagae", 8, {}))
    if g["인성"] >= 2:
        out.append(("re_memory", 6, {"count": g["인성"]}))
    if "충" in f["all_rel"]:
        out.append(("re_clash", -10, {}))
    if "원진" in f["all_rel"]:
        out.append(("re_wonjin", -8, {}))
    if g["비겁"] >= 3:
        out.append(("re_pride", -6, {"count": g["비겁"]}))
    return out


def _wealth(f, T):
    out, g = [], f["groups"]
    jae = g["재성"]
    if g["식상"] >= 1 and jae >= 1:
        out.append(("we_flow", 14, {}))
    if f["gyeok"] in ("정재격", "편재격"):
        out.append(("we_gyeok", 10, {"gyeok": f["gyeok"], "gyeokMeaning": T["GYEOK_MEANING"][f["gyeok"]]}))
    if f["st"] >= 55 and jae >= 1:
        out.append(("we_strong", 8, {}))
    if jae == 0:
        out.append(("we_none", -12, {}))
    if f["pct"]("재성") >= 30 and f["st"] <= 45:
        out.append(("we_heavy", -14, {}))
    if g["비겁"] >= 3 and jae >= 1:
        out.append(("we_rival", -12, {"count": g["비겁"]}))
    return out


def _career(f, T):
    out, g = [], f["groups"]
    gwan = g["관성"]
    if gwan >= 1 and g["인성"] >= 1:
        out.append(("ca_flow", 14, {}))
    if f["gyeok"] in ("정관격", "편관격", "정인격", "편인격"):
        out.append(("ca_gyeok", 8, {"gyeok": f["gyeok"], "gyeokMeaning": T["GYEOK_MEANING"][f["gyeok"]]}))
    if "문창귀인" in f["names"]:
        out.append(("ca_munchang", 8, {}))
    if "천을귀인" in f["names"]:
        out.append(("ca_cheoneul", 6, {}))
    if "역마살" in f["names"]:
        out.append(("ca_yeokma", 4, {}))
    if gwan == 0:
        out.append(("ca_free", -8, {}))
    if f["pct"]("관성") >= 30 and f["st"] <= 45:
        out.append(("ca_pressure", -14, {}))
    if "상관" in f["gods"] and gwan >= 1 and g["식상"] >= 2:
        out.append(("ca_clash", -10, {}))
    return out


def _business(f, T):
    out, g = [], f["groups"]
    if g["식상"] >= 1 and g["재성"] >= 1:
        out.append(("bu_flow", 12, {}))
    if "편재" in f["gods"]:
        out.append(("bu_pyeonjae", 8, {}))
    if f["st"] >= 55:
        out.append(("bu_strong", 10, {}))
    if "양인살" in f["names"]:
        out.append(("bu_drive", 6, T["DRIVE"]["양인살"]))
    elif "괴강살" in f["names"]:
        out.append(("bu_drive", 6, T["DRIVE"]["괴강살"]))
    if f["st"] <= 30:
        out.append(("bu_weak", -14, {}))
    elif f["st"] <= 45:
        out.append(("bu_weak", -8, {}))
    if g["비겁"] >= 3:
        out.append(("bu_partner", -10, {"count": g["비겁"]}))
    if g["재성"] == 0:
        out.append(("bu_nomoney", -8, {}))
    return out


def _health(f, T):
    out = []
    vals = [(e, f["elements"][e]) for e in ELEMENTS]
    if all(10 <= v <= 30 for _, v in vals):
        out.append(("he_balance", 16, {}))
    if 50 <= f["st"] < 70:
        out.append(("he_stamina", 6, {}))
    lack = sorted([x for x in vals if x[1] < 8], key=lambda x: x[1])
    if lack:
        e, v = lack[0]
        # 모자란 정도(8%에서 얼마나 모자란지)로 점수를 달리한다(손님마다 늘 34점이 되지 않게). taster.mjs 와 같은 식.
        gap = int(8 - v + 0.5)
        out.append(("he_lack", -(10 + gap) if len(lack) > 1 else -(6 + gap),
                    {"lack": e, "lackWord": T["ELEMENT_WORD"][e], "lackPct": v, "lackBody": T["ELEMENT_BODY"][e]}))
    many = sorted([x for x in vals if x[1] >= 35], key=lambda x: -x[1])
    if many:
        e, v = many[0]
        out.append(("he_excess", -8, {"many": e, "manyWord": T["ELEMENT_WORD"][e], "manyPct": v, "manyBody": T["ELEMENT_BODY"][e]}))
    if f["st"] <= 30:
        out.append(("he_weak", -8, {}))
    return out


RULES = {"newyear": _newyear, "romance": _romance, "intimate": _intimate, "reunion": _reunion,
         "wealth": _wealth, "career": _career, "business": _business, "health": _health}


def reading(fp: FourPillars, name: str, sex: str) -> dict:
    """맛보기 화면과 같은 좋은 운 3개·조심할 운 3개(이유와 글 포함)."""
    T = texts()
    name = (name or "").strip() or "고객"
    f = _facts(fp, sex)
    areas = []
    for order, aid in enumerate(AREA_ORDER):
        reasons = RULES[aid](f, T)
        score = max(5, min(95, 50 + sum(r[1] for r in reasons)))
        areas.append({"id": aid, "order": order, "score": score, "reasons": reasons})
    good = sorted(areas, key=lambda a: (-a["score"], a["order"]))[:3]
    bad = sorted([a for a in areas if a not in good], key=lambda a: (a["score"], a["order"]))[:3]

    def pick(a, sign):
        own = sorted([r for r in a["reasons"] if (r[1] > 0) - (r[1] < 0) == sign], key=lambda r: -abs(r[1]))
        key, _, values = own[0] if own else (f"{PREFIX[a['id']]}_base_{'good' if sign > 0 else 'bad'}", 0, {})
        return {**T["AREAS"][a["id"]], "id": a["id"], "score": a["score"], "reason": key,
                "text": fill(T["REASONS"][key], {"name": name, **values}),
                "hook": fill(T["HOOKS"][key], {"name": name, **values})}

    return {"good": [pick(a, 1) for a in good], "bad": [pick(a, -1) for a in bad],
            "scores": {a["id"]: a["score"] for a in areas}}


def digest(r: dict, product: str | None = None) -> dict:
    """리포트 글쓰기에 넘길 맛보기 내용. 고객이 결제 전에 무엇을 봤고, 그래서 무엇을 더 알고 싶어 하는지 알려 준다."""
    items = [("좋은 운", a) for a in r["good"]] + [("조심할 운", a) for a in r["bad"]]
    mine = [{"구분": k, "운": a["title"], "맛보기에서 본 글": a["text"]} for k, a in items if a["id"] == product]
    out = {
        "읽는 법": "아래 6가지 운(좋은 운 3·조심할 운 3)은 같은 사주 계산에서 나왔고, 무료 분석 화면과 이 책 맨 끝 보너스 쪽에 글자 그대로 실립니다. "
                 "고객이 본문과 보너스 쪽을 함께 읽으므로, 본문에서 같은 운을 다룰 때는 아래 근거와 같은 결론을 더 깊고 구체적으로 씁니다. "
                 "맛보기에서 좋은 운이라고 한 것은 언제, 어디서, 어떻게 그 운을 크게 쓰는지까지 쓰고, "
                 "조심할 운이라고 한 것은 언제 조심하고 어떻게 막는지까지 씁니다. 아래 내용과 반대되거나 다른 결론은 쓰지 않습니다(예: 보너스 쪽에서 재성이 없다고 했으면 본문에서 재성이 있다고 쓰지 않습니다).",
        "좋은 운": [{"운": a["title"], "맛보기에서 본 글": a["text"]} for a in r["good"]],
        "조심할 운": [{"운": a["title"], "맛보기에서 본 글": a["text"]} for a in r["bad"]],
    }
    if product == "lifetime":
        out["이 상품을 산 이유"] = {"쓸 점": "평생사주는 사주 전체를 보는 상품입니다. 위 좋은 운 3개와 조심할 운 3개를 "
                                       "알맞은 장마다 빠짐없이 다시 꺼내, 맛보기보다 훨씬 자세히 풀고 강조합니다."}
    if mine:
        out["이 상품을 산 이유"] = {**mine[0], "쓸 점": "이 항목이 고객이 이 리포트를 산 가장 큰 이유입니다. 이 근거를 리포트 여러 장에 걸쳐 가장 자세히 풀어 줍니다."}
    return out


def pillars_from_result(result: dict) -> FourPillars:
    """analyze_person() 결과(첫 번째 명식)를 FourPillars로 되돌린다."""
    from .constants import STEMS
    from .pillars import Pillar
    parts = result["variants"][0]["key"].split()
    ps = [None if k == "??" else Pillar(STEMS.index(k[0]), BRANCHES.index(k[1])) for k in parts]
    return FourPillars(*ps)


def reading_for_person(result: dict) -> dict:
    """analyze_person() 결과로 맛보기 결과를 만든다(주문 처리용)."""
    p = result["person"]
    return reading(pillars_from_result(result), p.get("name", ""), p.get("sex", ""))


def area_view(fp: FourPillars, name: str, sex: str, product: str) -> dict:
    """한 상품의 운(결제 전 이야기 화면의 '내 점수'). site/public/assets/free/taster.mjs areaView 와 같은 결과."""
    r = reading(fp, name, sex)
    for sign, items in ((1, r["good"]), (-1, r["bad"])):
        for a in items:
            if a["id"] == product:
                return {**a, "sign": sign}
    T = texts()
    name = (name or "").strip() or "고객"
    score = r["scores"][product]
    sign = 1 if score >= 50 else -1
    own = sorted([x for x in RULES[product](_facts(fp, sex), T) if (x[1] > 0) - (x[1] < 0) == sign], key=lambda x: -abs(x[1]))
    key, _, values = own[0] if own else (f"{PREFIX[product]}_base_{'good' if sign > 0 else 'bad'}", 0, {})
    return {**T["AREAS"][product], "id": product, "score": score, "reason": key,
            "text": fill(T["REASONS"][key], {"name": name, **values}),
            "hook": fill(T["HOOKS"][key], {"name": name, **values}), "sign": sign}


def area_parts(fp: FourPillars, name: str, sex: str, product: str) -> dict:
    """한 상품의 운을 좋은 점과 조심할 점으로 나눈다. site/public/assets/free/taster.mjs areaParts 와 같은 결과."""
    T = texts()
    name = (name or "").strip() or "고객"
    reasons = RULES[product](_facts(fp, sex), T)

    def part(sign):
        own = sorted([x for x in reasons if (x[1] > 0) - (x[1] < 0) == sign], key=lambda x: -abs(x[1]))
        if not own:
            return None
        key, _, values = own[0]
        return {"score": max(5, min(95, 50 + sum(x[1] for x in own))), "reason": key,
                "text": fill(T["REASONS"][key], {"name": name, **values}),
                "hook": fill(T["HOOKS"][key], {"name": name, **values})}
    return {"id": product, "score": max(5, min(95, 50 + sum(x[1] for x in reasons))), "good": part(1), "bad": part(-1)}


def situation_note(area: str, answers) -> str:
    """손님이 답한 지금 상황(연애 중·결혼·쉬는 중…)에 맞춰 그 운이 어떻게 나타나는지 한 줄. 결제 전 화면(taster.mjs situationNote)과 같다."""
    S = texts()["SITUATION"]
    vals = {str(a) for a in answers if a}
    for key, opts in S["groups"].items():
        if vals & set(opts) and key in S["notes"].get(area, {}):
            return S["notes"][area][key]
    return ""
