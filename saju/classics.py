"""고전 명리 판단: 자평진전(격국의 성패·상신)과 적천수(기세·종격·화기격·조후·통관), 물상 단서.

뼈대는 자평진전으로 세운다. 월지로 정한 격이 제대로 섰는지(성격), 깨졌는지(파격),
격을 살리는 글자(상신)와 해치는 글자(기신)가 무엇인지 본다.
흐름은 적천수로 읽는다. 기운이 한쪽으로 몰려 따라가야 하는지(종격·화기격),
계절의 춥고 더움·마르고 젖음(조후), 부딪히는 두 기운을 이어 주는 기운(통관)을 본다.

학파마다 갈리는 부분은 다음 기준을 따른다(바꿀 때는 이 주석도 함께 고친다).
- 글자가 "있다"는 것은 천간에 드러났거나(투출) 지지의 정기(본기)인 경우만 센다.
- 종격은 일간이 매우 약하고(25점 이하) 천간과 지지 정기에 비겁·인성이 하나도 없을 때만 본다(진종 위주).
  종강·종왕은 80점 이상이고 천간과 지지 정기에 관성이 없을 때만 본다.
- 화기격은 일간이 월간이나 시간과 합하고, 월지가 합해서 된 오행일 때만 본다.
- 최종 용신 순서: 화기격 → 종격 → 급한 조후 → 통관 → 격국의 상신(억부 방향과 맞을 때) → 억부.
"""

from __future__ import annotations

from collections import Counter

from .analysis import (
    STEM_COMBINE, branch_ten_god, element_strength, gyeokguk, natal_relations, ten_god, strength as day_strength,
)
from .constants import BRANCH_ELEMENT, ELEMENTS, STEM_ELEMENT, STEMS
from .pillars import FourPillars

GROUP_GODS = {"비겁": ("비견", "겁재"), "식상": ("식신", "상관"), "재성": ("편재", "정재"),
              "관성": ("편관", "정관"), "인성": ("편인", "정인")}
GROUP_OFFSET = {"비겁": 0, "식상": 1, "재성": 2, "관성": 3, "인성": 4}   # 일간 오행 기준 몇 칸 뒤인가

SEASON = {2: "봄", 3: "봄", 4: "봄", 5: "여름", 6: "여름", 7: "여름",
          8: "가을", 9: "가을", 10: "가을", 11: "겨울", 0: "겨울", 1: "겨울"}


def _j(word: str, with_batchim: str, without: str) -> str:
    """받침에 맞는 조사(예: 금과/토와, 금이/토가)."""
    code = ord(word[-1]) - 0xAC00
    return word + (with_batchim if 0 <= code <= 11171 and code % 28 else without)


def group_element(day_stem: int, group: str) -> str:
    return ELEMENTS[(STEM_ELEMENT[day_stem] + GROUP_OFFSET[group]) % 5]


def _gods(fp: FourPillars) -> Counter:
    """천간(일간 제외)과 지지 정기의 십신 개수."""
    ds = fp.day.stem
    c = Counter()
    for i, p in enumerate(fp.as_list()):
        if p is None:
            continue
        if i != 2:
            c[ten_god(ds, p.stem)] += 1
        c[branch_ten_god(ds, p.branch)] += 1
    return c


def _n(c: Counter, *gods: str) -> int:
    return sum(c[g] for g in gods)


# ── 자평진전: 격국의 성패와 상신 ─────────────────────────────────

def _rule(gname: str, c: Counter, strong: bool) -> dict:
    """격 하나의 성패 규칙. good/bad는 근거 문장, helps/hurts는 운에서 오면 격을 돕거나 해치는 십신."""
    gwan, sal = _n(c, "정관"), _n(c, "편관")
    jae, in_ = _n(c, "정재", "편재"), _n(c, "정인", "편인")
    sik, sang = _n(c, "식신"), _n(c, "상관")
    bi = _n(c, "비견", "겁재")
    good, bad = [], []

    if gname == "정관격":
        if jae:
            good.append("재성이 정관을 살려 줘요(재생관). 일한 만큼 인정과 자리가 따라와요.")
        if in_:
            good.append("인성이 정관의 힘을 나에게 이어 줘요(관인상생). 배움과 자격이 지위로 이어져요.")
        if sang and not in_:
            bad.append("상관이 정관을 쳐요(상관견관). 윗사람·규칙과 부딪히기 쉬워요.")
        if sal:
            bad.append("정관과 편관이 섞여 있어요(관살혼잡). 책임과 압박이 여러 갈래로 와요.")
        if not strong and not in_:
            bad.append("나의 힘이 약한데 정관을 받쳐 줄 인성이 없어 책임이 무겁게 느껴져요.")
        sangsin = "재성" if jae and strong else "인성" if in_ else ("재성" if strong else "인성")
        helps = {"정재", "편재", "정인", "편인"} if strong else {"정인", "편인"}
        hurts = {"상관", "편관"}
    elif gname == "편관격":
        if sik or sang:
            good.append("식상이 편관을 다스려요(식신제살). 압박을 실력으로 바꿔 내는 힘이 있어요.")
        if in_ and not strong:
            good.append("인성이 편관의 힘을 나에게 이어 줘요(살인상생). 어려움을 겪을수록 단단해져요.")
        if jae and strong and not (sik or sang):
            good.append("나의 힘이 넉넉해 재성이 편관을 받쳐도 감당해요. 큰 책임을 맡을수록 돈과 자리가 함께 커져요.")
        if jae and not strong and not (sik or sang or in_):
            bad.append("재성이 편관을 키우는데 막아 줄 글자가 없어요(재생살). 돈 문제가 압박으로 번지기 쉬워요.")
        if not strong and not (sik or sang or in_):
            bad.append("나의 힘이 약한데 편관을 다스릴 글자가 없어 압박을 정면으로 받아요.")
        if gwan:
            bad.append("편관과 정관이 섞여 있어요(관살혼잡). 해야 할 일과 책임이 겹쳐요.")
        # 신강하면 식상으로 다스리거나 재성으로 키워 쓰고, 신약하면 인성으로 이어 받는다
        sangsin = ("식상" if sik or sang else "재성") if strong else ("인성" if in_ or not (sik or sang) else "식상")
        helps = {"식신", "상관", "정재", "편재"} if strong else {"정인", "편인", "비견", "겁재", "식신"}
        hurts = {"정관"} | ({"정인", "편인"} if strong else {"정재", "편재"})
    elif gname in ("정재격", "편재격"):
        if strong and (gwan or sal):
            good.append("나의 힘이 넉넉하고 재성이 관성을 살려요(재왕생관). 번 돈이 자리와 신용으로 이어져요.")
        if strong and (sik or sang):
            good.append("식상이 재성을 만들어 줘요(식상생재). 재주와 노력이 돈으로 바뀌어요.")
        if strong and not (gwan or sal or sik or sang):
            good.append("나의 힘이 넉넉해 재물을 감당할 수 있어요.")
        if bi >= 2 and not (gwan or sal):
            bad.append("비겁이 재성을 나눠 가져가요(군겁쟁재). 동업·보증·지출로 돈이 새기 쉬워요.")
        if not strong:
            bad.append("재성에 비해 나의 힘이 약해요(재다신약). 돈이 보여도 다 쥐기 어려워 힘을 길러야 해요.")
        sangsin = ("식상" if sik or sang else "관성") if strong else "비겁"
        helps = {"식신", "상관", "정관", "편관", "정재", "편재"} if strong else {"비견", "겁재", "정인", "편인"}
        hurts = {"비견", "겁재"} if strong else {"정관", "편관", "식신", "상관"}
    elif gname in ("정인격", "편인격"):
        if gwan or sal:
            good.append("관성이 인성을 살려 줘요(관인상생). 공부·자격이 일과 지위로 이어져요.")
        if strong and (sik or sang):
            good.append("인성으로 쌓은 힘을 식상으로 풀어 내요. 배운 것을 밖으로 보여 줄 수 있어요.")
        if jae >= 2 and not (gwan or sal):
            bad.append("재성이 인성을 깨요(탐재괴인). 눈앞의 돈 때문에 공부·신용을 잃기 쉬워요.")
        if gname == "편인격" and sik and not jae:
            bad.append("편인이 식신을 막아요(편인도식). 생각만 많고 실행이 끊기기 쉬워요.")
        if strong and not (sik or sang or jae):
            bad.append("돕는 기운이 많은데 풀어 낼 곳이 없어 생각이 고이기 쉬워요.")
        sangsin = "관성" if gwan or sal else ("식상" if strong else "관성")
        helps = ({"정관", "편관", "식신", "상관"} if strong else {"정관", "편관", "정인", "편인", "비견", "겁재"})
        hurts = {"정재", "편재"} if not strong else {"정인", "편인"}
    elif gname == "식신격":
        if jae:
            good.append("식신이 재성을 만들어 줘요(식신생재). 좋아하는 일이 돈이 되는 구조예요.")
        if sal:
            good.append("식신이 편관을 다스려요(식신제살). 어려운 상황을 실력으로 풀어 내요.")
        if _n(c, "편인") and not jae:
            bad.append("편인이 식신을 막아요(편인도식). 하던 일이 자주 끊기거나 의욕이 꺾이기 쉬워요.")
        if not strong:
            bad.append("식신이 나의 힘을 빼는데 나의 힘이 약해 쉽게 지쳐요.")
        sangsin = "재성" if jae or not sal else "식상"
        helps = {"정재", "편재"} | ({"비견", "겁재"} if not strong else {"식신"})
        hurts = {"편인"}
    elif gname == "상관격":
        if jae:
            good.append("상관이 재성을 만들어 줘요(상관생재). 말솜씨와 아이디어가 돈이 돼요.")
        if in_ and not strong:
            good.append("인성이 상관을 다듬어 줘요(상관패인). 재능에 실력과 자격이 붙어요.")
        if sal and strong:
            good.append("상관이 편관을 다스려요(상관가살). 경쟁과 위기에서 오히려 빛나요.")
        if gwan and not (in_ or jae):
            bad.append("상관이 정관을 쳐요(상관견관). 조직·윗사람과 부딪히거나 말로 손해 보기 쉬워요.")
        if not strong and not in_:
            bad.append("상관이 나의 힘을 많이 빼는데 받쳐 줄 인성이 없어요.")
        sangsin = "재성" if strong else "인성"
        helps = {"정재", "편재", "편관"} if strong else {"정인", "편인"}
        hurts = {"정관"} | ({"정인", "편인"} if strong else set())
    elif gname == "건록격":
        if gwan or sal:
            good.append("녹이 관성을 써요(녹겁용관). 자기 힘으로 자리를 얻어요.")
        if jae and (sik or sang):
            good.append("식상이 재성을 이어 줘요(녹겁용재). 스스로 벌어 스스로 모아요.")
        elif sik or sang:
            good.append("넘치는 힘을 식상으로 풀어요. 재주와 활동으로 길을 열어요.")
        if not (gwan or sal or jae or sik or sang):
            bad.append("힘은 강한데 쓸 곳(관성·재성·식상)이 없어요. 힘이 안으로 고이기 쉬워요.")
        if jae and bi >= 2 and not (sik or sang or gwan or sal):
            bad.append("비겁이 재성을 나눠 가져가요(군겁쟁재).")
        sangsin = "관성" if gwan or sal else "재성" if jae else "식상"
        helps = {"정관", "편관", "정재", "편재", "식신", "상관"}
        hurts = {"비견", "겁재", "정인", "편인"}
    else:  # 양인격
        if sal:
            good.append("편관이 양인을 다스려요(양인가살). 강한 힘이 큰 책임과 권한으로 쓰여요.")
        if gwan:
            good.append("정관이 양인을 다스려요. 강한 힘이 규칙 안에서 쓰여요.")
        if not (gwan or sal):
            bad.append("양인을 다스릴 관성이 없어요. 힘이 넘쳐 다툼과 무리수로 번지기 쉬워요.")
        if sal and (sik or sang):
            bad.append("양인을 다스리는 편관을 식상이 다시 쳐서 다스림이 약해져요.")
        sangsin = "관성"
        helps = {"정관", "편관", "정재", "편재"}
        hurts = {"비견", "겁재", "정인", "편인", "식신", "상관"} if sal else {"비견", "겁재", "정인", "편인"}

    return {"good": good, "bad": bad, "sangsin": sangsin, "helps": sorted(helps), "hurts": sorted(hurts)}


def ziping(fp: FourPillars, gyeok: dict, st: dict) -> dict:
    """자평진전 방식의 격국 평가."""
    c = _gods(fp)
    strong = st["score"] >= 50
    r = _rule(gyeok["name"], c, strong)
    month_clash = [x for x in natal_relations(fp) if x["type"] == "충" and "월주" in x.get("between", [])]
    if month_clash:
        r["bad"].append(f"태어난 달의 지지가 충을 받아요({month_clash[0]['chars']}). 격의 뿌리가 흔들려 변동이 잦아요.")
    if r["good"] and not r["bad"]:
        verdict = "성격"
    elif r["good"]:
        verdict = "성중유패"
    elif r["bad"]:
        verdict = "파격"
    else:
        verdict = "상신 대기"
    present = _n(c, *GROUP_GODS[r["sangsin"]]) > 0
    return {
        "gyeok": gyeok["name"], "verdict": verdict, "good": r["good"], "bad": r["bad"],
        "sangsin": r["sangsin"], "sangsin_element": group_element(fp.day.stem, r["sangsin"]),
        "sangsin_present": present,
        "helps": r["helps"], "hurts": r["hurts"],
    }


# ── 적천수: 기세(종격·화기격), 조후, 통관 ───────────────────────

def _jong(fp: FourPillars, st: dict, el: dict) -> dict | None:
    ds = fp.day.stem
    c = _gods(fp)
    me = STEM_ELEMENT[ds]
    help_n = _n(c, "비견", "겁재", "정인", "편인")
    if st["score"] <= 25 and help_n == 0:
        shares = {g: el[group_element(ds, g)] for g in ("식상", "재성", "관성")}
        top = max(shares, key=shares.get)
        total = sum(shares.values()) or 1
        if shares[top] / total >= 0.5:
            name = {"식상": "종아격", "재성": "종재격", "관성": "종살격"}[top]
            follow = {"식상": ("식상", ["재성"], ["인성", "관성"]),
                      "재성": ("재성", ["식상", "관성"], ["비겁", "인성"]),
                      "관성": ("관성", ["재성"], ["식상", "비겁"])}[top]
        else:
            name, follow = "종세격", ("재성", ["식상", "관성"], ["인성", "비겁"])
        return {"name": name, "use": follow[0], "hee": follow[1], "gi": follow[2],
                "why": "나를 돕는 글자가 하나도 없고 다른 기운이 사주를 가득 채워, 버티기보다 그 기운을 따라가는 사주예요."}
    if st["score"] >= 80 and _n(c, "정관", "편관") == 0:
        bi = el[ELEMENTS[me]]
        in_ = el[group_element(ds, "인성")]
        if bi >= in_:
            return {"name": "종왕격", "use": "비겁", "hee": ["인성", "식상"], "gi": ["관성", "재성"],
                    "why": "나와 같은 기운이 사주를 거의 다 차지해, 누르기보다 그 힘을 그대로 밀고 나가는 사주예요."}
        return {"name": "종강격", "use": "인성", "hee": ["비겁"], "gi": ["재성", "식상"],
                "why": "나를 돕는 기운이 사주를 거의 다 차지해, 그 힘을 따라 배움과 후원을 키우는 사주예요."}
    return None


def _hwagi(fp: FourPillars) -> dict | None:
    ds = fp.day.stem
    for i in (1, 3):
        p = fp.as_list()[i]
        if p is None:
            continue
        pair = frozenset({ds, p.stem})
        if pair in STEM_COMBINE:
            el = STEM_COMBINE[pair]
            e = ELEMENTS.index(el)
            if BRANCH_ELEMENT[fp.month.branch] != e:
                continue
            breaker = (e + 3) % 5   # 합해서 된 오행을 극하는 오행
            stems = [q.stem for j, q in enumerate(fp.as_list()) if q is not None and j not in (2, i)]
            if any(STEM_ELEMENT[s] == breaker for s in stems):
                continue
            name = f"{STEMS[min(pair)]}{STEMS[max(pair)]} 합화{el}격"
            return {"name": name, "element": el, "hee": ELEMENTS[(e - 1) % 5], "gi": ELEMENTS[breaker],
                    "why": f"일간이 {('월간' if i == 1 else '시간')}과 합해 {el}의 기운으로 바뀌었고, 태어난 달도 {_j(el, '이라', '라')} 그 기운을 따라가요."}
    return None


def johu(fp: FourPillars, el: dict) -> dict:
    mb = fp.month.branch
    season = SEASON[mb]
    hwa, su = el["화"], el["수"]
    if season == "겨울" or (mb == 2 and hwa < 10):
        state, need, urgent = "한", ["화"], hwa < 8
        text = "추운 계절에 태어났어요. 몸과 마음을 데워 주는 화(불)의 기운이 있어야 움직임이 살아나요."
    elif season == "여름":
        state, need, urgent = "난", ["수"], su < 8
        text = "더운 계절에 태어났어요. 열을 식혀 주는 수(물)의 기운이 있어야 지치지 않고 오래 가요."
    elif mb == 10 or (el["화"] + el["토"] >= 60 and su < 10):
        state, need, urgent = "조", ["수"], su < 8
        text = "기운이 메마른 편이에요. 촉촉하게 적셔 주는 수(물)의 기운이 있어야 결과가 자라요."
    elif mb in (1, 4) and el["수"] + el["금"] >= 50 and hwa < 10:
        state, need, urgent = "습", ["화"], True
        text = "기운이 축축하고 무거운 편이에요. 말려 주는 화(불)의 기운이 있어야 일이 가볍게 풀려요."
    else:
        state, need, urgent = "평", [], False
        text = "계절의 기운이 크게 치우치지 않았어요. 온도보다 힘의 균형을 먼저 봐요."
    return {"season": season, "state": state, "need": need, "urgent": urgent, "text": text}


def tonggwan(el: dict) -> dict | None:
    best = None
    for a in range(5):
        b = (a + 2) % 5            # a가 b를 극한다
        va, vb = el[ELEMENTS[a]], el[ELEMENTS[b]]
        if va >= 25 and vb >= 25 and (best is None or min(va, vb) > best[0]):
            best = (min(va, vb), a, b)
    if not best:
        return None
    _, a, b = best
    bridge = ELEMENTS[(a + 1) % 5]
    have = el[bridge] >= 15
    return {"clash": [ELEMENTS[a], ELEMENTS[b]], "bridge": bridge, "present": have,
            "text": (f"{_j(ELEMENTS[a], '과', '와')} {_j(ELEMENTS[b], '이', '가')} 둘 다 강해서 서로 부딪혀요. "
                     f"{bridge}의 기운이 둘 사이를 이어 주면 싸움이 흐름으로 바뀌어요."
                     + (" 사주 안에 이미 그 기운이 있어요." if have else " 사주 안에는 그 기운이 약해 운에서 올 때 크게 풀려요."))}


# ── 물상: 일간이 태어난 계절, 천간 짝 ──────────────────────────

STEM_PAIRS = {
    frozenset({0, 6}): "벽갑", frozenset({2, 8}): "강휘상영", frozenset({1, 2}): "화목향양",
    frozenset({3, 0}): "유신유화", frozenset({4, 0}): "산림", frozenset({5, 2}): "옥토득양",
    frozenset({6, 3}): "단련", frozenset({7, 8}): "도세주옥", frozenset({8, 4}): "제방",
    frozenset({9, 7}): "금백수청",
}


def mulsang(fp: FourPillars) -> dict:
    ds = fp.day.stem
    pairs = []
    for i, p in enumerate(fp.as_list()):
        if p is None or i == 2:
            continue
        key = STEM_PAIRS.get(frozenset({ds, p.stem}))
        if key and key not in pairs:
            pairs.append(key)
    return {"stem": STEMS[ds], "season": SEASON[fp.month.branch], "pairs": pairs}


def stem_pair_key(day_stem: int, other_stem: int) -> str | None:
    return STEM_PAIRS.get(frozenset({day_stem, other_stem}))


# ── 종합 ──────────────────────────────────────────────────────

def _eokbu(fp: FourPillars, st: dict, sangsin: str) -> tuple[str, list[str], list[str], str]:
    """억부: 강하면 덜어 내고(식상·재성·관성), 약하면 보탠다(인성·비겁). 강할 때는 격의 상신 쪽을 먼저 쓴다."""
    g = lambda *gs: [group_element(fp.day.stem, x) for x in gs]
    if st["score"] >= 55:
        use = g(sangsin if sangsin in ("식상", "재성", "관성") else "식상")[0]
        return use, g("식상", "재성", "관성"), g("인성", "비겁"), "나의 힘이 강해 덜어 내는 기운(식상·재성·관성)이 필요해요."
    if st["score"] <= 45:
        return g("인성")[0], g("비겁"), g("재성", "관성"), "나의 힘이 약해 보태 주는 기운(인성·비겁)이 필요해요."
    return "", [], [], "나의 힘이 중간이라 억부보다 계절과 격국을 먼저 봐요."


def judge(fp: FourPillars) -> dict:
    """자평진전 + 적천수 종합 판단."""
    ds = fp.day.stem
    st = day_strength(fp)
    el = element_strength(fp)
    zp = ziping(fp, gyeokguk(fp), st)
    jo = johu(fp, el)
    tg = tonggwan(el)
    hwa = _hwagi(fp)
    jong = None if hwa else _jong(fp, st, el)
    eb_use, eb_hee, eb_gi, eb_why = _eokbu(fp, st, zp["sangsin"])

    if hwa:
        use, method, hee, gi, basis = hwa["element"], hwa["name"], [hwa["hee"]], [hwa["gi"]], hwa["why"]
    elif jong:
        use, method = group_element(ds, jong["use"]), jong["name"]
        hee = [group_element(ds, x) for x in jong["hee"]]
        gi = [group_element(ds, x) for x in jong["gi"]]
        basis = jong["why"]
    elif jo["urgent"]:
        use, method = jo["need"][0], "조후"
        hee = [e for e in eb_hee + ([eb_use] if eb_use else []) if e != use]
        gi = [e for e in eb_gi if e != use]
        basis = jo["text"] + " 계절의 온도를 맞추는 것이 가장 급해요."
    elif tg and not tg["present"]:
        use, method = tg["bridge"], "통관"
        hee = [e for e in eb_hee if e != use]
        gi = [e for e in eb_gi if e != use]
        basis = tg["text"]
    else:
        sang_el = zp["sangsin_element"]
        weak_side = {group_element(ds, "인성"), group_element(ds, "비겁")}
        agrees = (st["score"] > 45 and sang_el not in weak_side) or (st["score"] < 55 and sang_el in weak_side)
        if agrees:
            use, method = sang_el, "격국 상신"
            basis = f"{zp['gyeok']}을 살리는 글자(상신)가 {zp['sangsin']}이에요. 그 기운인 {sang_el}이 이 사주의 중심을 잡아 줘요."
        else:
            use, method, basis = (eb_use or sang_el), "억부", eb_why
        hee = [e for e in eb_hee if e != use]
        gi = [e for e in eb_gi if e != use]
    # 계절이 치우친 사주는 그 계절의 기운을 더 보태는 오행을 희신에서 뺀다(더운 사주에 화, 추운 사주에 수)
    too_much = {"난": "화", "조": "화", "한": "수", "습": "수"}.get(jo["state"])
    if too_much and too_much != use and (jo["urgent"] or method == "조후"):
        hee = [e for e in hee if e != too_much]
        gi = gi + [too_much]
    return {
        "ziping": zp, "johu": jo, "tonggwan": tg, "jong": jong, "hwagi": hwa,
        "mulsang": mulsang(fp),
        "yongsin": {"element": use, "method": method, "basis": basis,
                    "heesin": list(dict.fromkeys(hee)), "gisin": list(dict.fromkeys(e for e in gi if e != use))},
    }


def luck_effect(cl: dict, stem_god: str, branch_god: str) -> dict:
    """운의 간지가 격을 돕는지 해치는지(자평진전의 행운 판단)."""
    zp = cl["ziping"]
    gods = [stem_god, branch_god]
    helps = [g for g in gods if g in zp["helps"]]
    hurts = [g for g in gods if g in zp["hurts"]]
    if cl.get("jong") or cl.get("hwagi"):
        return {"effect": "보통", "gods": []}
    if len(helps) > len(hurts):
        return {"effect": "도움", "gods": helps}
    if len(hurts) > len(helps):
        return {"effect": "방해", "gods": hurts}
    return {"effect": "보통", "gods": helps + hurts}
