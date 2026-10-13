"""사주 계산 결과를 리포트 재료(facts)로 정리한다.

여기서 만드는 값은 모두 계산으로 정해지는 것들이다(글자, 개수, 날짜, 점수).
문장은 writer가 이 재료를 보고 쓴다. 숫자와 글자는 facts에서만 가져와야 틀리지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from . import knowledge as K
from . import mulsang as M
from ..classics import luck_effect

PILLAR_LABEL = {"년주": "태어난 해", "월주": "태어난 달", "일주": "태어난 날", "시주": "태어난 시간"}


@dataclass
class OrderInfo:
    """주문할 때 받은 정보."""
    order_date: date = field(default_factory=date.today)
    question: str = ""          # 고객이 남긴 질문(없을 수 있음)
    daily: str = ""             # 요즘 일상: 직장/사업/프리랜서/공부/휴식
    relationship: str = ""      # 연애·결혼 상태(사이트에 항목이 생기면 받는다): 솔로/연애 중/결혼/이혼·사별
    experience: str = ""        # 연애사주: 연애 경험 횟수(사이트 선택지 그대로)


def _age_on(birth: date, on: date) -> int:
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def pick_yongsin(an: dict) -> str:
    """행운 아이템 기준으로 쓸 오행 하나. 고전 판단(classics)의 최종 용신을 쓰고, 없으면 조후·억부로 고른다."""
    if an.get("classics"):
        return an["classics"]["yongsin"]["element"]
    ys = an["yongsin"]
    for el in ys["조후"]:
        if el in ys["억부"]:
            return el
    if ys["억부"]:
        return ys["억부"][0]
    if ys["조후"]:
        return ys["조후"][0]
    st = an["elements"]["strength"]
    return min(st, key=st.get)


def _ganzhi_elements(ganzhi: str) -> list[str]:
    from ..constants import STEMS, BRANCHES, STEM_ELEMENT, BRANCH_ELEMENT, ELEMENTS
    return [ELEMENTS[STEM_ELEMENT[STEMS.index(ganzhi[0])]], ELEMENTS[BRANCH_ELEMENT[BRANCHES.index(ganzhi[1])]]]


def luck_score(ganzhi: str, relations: list[dict], good: list[str], bad: list[str], gyeok: str = "보통",
               weights: dict[str, float] | None = None) -> int:
    """운의 흐름 점수(20~90). 필요한 기운이 오면 오르고, 넘치는 기운이 더해지거나 부딪히면 내려간다.
    격을 돕는 십신이 오면 조금 더 오르고, 격을 해치는 십신이 오면 조금 더 내려간다(자평진전의 행운 판단)."""
    score = 55 + {"도움": 4, "방해": -4}.get(gyeok, 0)
    if weights is None:
        weights = {**{e: -1.0 for e in bad}, **{e: 1.0 for e in good}}
    for i, el in enumerate(_ganzhi_elements(ganzhi)):
        weight = 10 if i == 0 else 14   # 지지가 실제 생활에 더 크게 작용한다고 본다
        score += weight * weights.get(el, 0)
    for r in relations:
        kind = K.relation_kind(r["type"])
        if kind in ("천간합", "육합", "반합", "삼합"):
            score += 3
        elif kind in ("충", "천간충"):
            score -= 5
        elif kind in ("형", "자형", "파", "해", "원진"):
            score -= 3
    return max(20, min(90, round(score)))


def _wa(word: str) -> str:
    """받침이 있으면 '과', 없으면 '와'."""
    if not word:
        return "와"
    code = ord(word[-1]) - 0xAC00
    return "과" if 0 <= code <= 11171 and code % 28 else "와"


def _relations_text(relations: list[dict]) -> list[str]:
    out = []
    for r in relations:
        kind = K.relation_kind(r["type"])
        target = PILLAR_LABEL.get(r.get("with", ""), r.get("with", ""))
        out.append(f"{target}{_wa(target)} {kind}")
    return sorted(set(out))


def _classics_text(cl: dict, day_stem: str) -> dict:
    """고전 판단을 리포트에서 쓸 쉬운 말로 정리."""
    zp, ms = cl["ziping"], cl["mulsang"]
    img = M.SEASON.get((day_stem, ms["season"]))
    special = cl["hwagi"] or cl["jong"]
    return {
        "gyeok": zp["gyeok"], "verdict": zp["verdict"], "verdict_text": K.VERDICT[zp["verdict"]],
        "good": zp["good"], "bad": zp["bad"],
        "sangsin": zp["sangsin"], "sangsin_element": zp["sangsin_element"], "sangsin_present": zp["sangsin_present"],
        "helps": zp["helps"], "hurts": zp["hurts"],
        "special": {"name": special["name"], "why": special["why"]} if special else None,
        "johu": cl["johu"], "tonggwan": cl["tonggwan"],
        "yongsin": cl["yongsin"],
        "image": {"title": img[0], "text": img[1]} if img else None,
        "pairs": [{"key": k, "title": M.PAIR[k][0], "text": M.PAIR[k][1]} for k in ms["pairs"]],
    }


def _luck_weights(an: dict) -> tuple[list[str], list[str], dict | None]:
    """운 점수에 쓰는 좋은 기운(good), 넘치는 기운(excess), 가중치(weights)."""
    yong = pick_yongsin(an)
    cl = an.get("classics")
    if cl:
        # 용신은 온전히, 희신은 절반 남짓 더하고, 넘치는 오행은 온전히, 그 밖의 기신은 절반 남짓 뺀다
        good = [yong] + [e for e in cl["yongsin"]["heesin"] if e != yong]
        over = [e for e in an["elements"]["judgement"]["과다"] if e not in good]
        excess = list(dict.fromkeys(over + [e for e in cl["yongsin"]["gisin"] if e not in good]))
        weights = {**{e: -0.6 for e in excess}, **{e: -1.0 for e in over}, **{e: 0.6 for e in good}, yong: 1.0}
    else:
        weights = None
        excess = an["elements"]["judgement"]["과다"]
        good = [yong] + [e for e in an["yongsin"]["억부"] if e != yong]
    return good, excess, weights


def _effect(cl: dict | None, stem_god: str, branch_god: str) -> str:
    return luck_effect(cl, stem_god, branch_god)["effect"] if cl else "보통"


def luck_rater(an: dict):
    """운(세운·월운 한 줄) → 격국 효과, 흐름 점수, 관계 글. build_facts와 같은 계산(신년운세처럼 다른 해를 볼 때 쓴다)."""
    good, excess, weights = _luck_weights(an)
    cl = an.get("classics")

    def rate(x: dict) -> dict:
        eff = _effect(cl, x["stem_ten_god"], x["branch_ten_god"])
        return {"gyeok_effect": eff, "score": luck_score(x["ganzhi"], x["relations"], good, excess, eff, weights),
                "relations_text": _relations_text(x["relations"])}
    return rate


def month_row(m: dict, rate) -> dict:
    """월운 한 줄을 리포트 재료로."""
    d = datetime.fromisoformat(m["starts"])
    return {**m, "start_text": f"{d.year}년 {d.month}월 {d.day}일",
            "short": f"{d.month}/{d.day}", "month": d.month, "year": d.year, **rate(m)}


def build_facts(result: dict, order: OrderInfo | None = None) -> dict:
    """analyze_person() 결과 → 리포트 재료."""
    order = order or OrderInfo()
    variant = result["variants"][0]
    an = variant["analysis"]
    birth = date.fromisoformat(result["input"]["solar_dates"][0]["date"])
    age = _age_on(birth, order.order_date)

    dm = an["day_master"]
    dm_info = K.STEM[dm["stem"]]

    # 사주표
    pillars = []
    for p in an["pillars"]:
        if p.get("unknown"):
            pillars.append({"pillar": p["pillar"], "label": PILLAR_LABEL[p["pillar"]], "unknown": True})
            continue
        pillars.append({
            **p,
            "label": PILLAR_LABEL[p["pillar"]],
            "stem_hanja": p["hanja"][0], "branch_hanja": p["hanja"][1],
            "animal": K.BRANCH_ANIMAL[p["branch"]],
            "hidden_text": " · ".join(f"{h['stem']}({h['ten_god']})" for h in p["hidden_stems"]),
            "stage_text": K.TWELVE_STAGE[p["twelve_stage"]],
        })

    # 오행
    strength = an["elements"]["strength"]
    total = sum(strength.values()) or 1
    elements = []
    for el in K.ELEMENT_ORDER:
        info = K.ELEMENT[el]
        pct = round(strength[el] / total * 100)
        status = "많음" if el in an["elements"]["judgement"]["과다"] else "부족" if el in an["elements"]["judgement"]["부족"] else "보통"
        elements.append({"el": el, "hanja": info["hanja"], "name": info["name"], "count": an["elements"]["count"][el],
                         "pct": pct, "status": status, "trait": info["trait"],
                         "note": info["many"] if status == "많음" else info["few"] if status == "부족" else ""})

    # 십신
    groups = []
    for g in K.TEN_GOD_GROUP_ORDER:
        n = an["ten_god_groups"][g]
        info = K.TEN_GOD_GROUP[g]
        groups.append({"group": g, "label": info["label"], "members": info["members"], "n": n,
                       "meaning": info["meaning"],
                       "note": info["none"] if n == 0 else info["many"] if n >= 3 else ""})
    missing_groups = [g["group"] for g in groups if g["n"] == 0]

    # 용신·행운
    yong = pick_yongsin(an)
    cl = an.get("classics")
    good, excess, weights = _luck_weights(an)
    year_branch = an["pillars"][0]["branch"]
    samhap = next(t for t in K.SAMHAP if year_branch in t)
    good_animals = [K.BRANCH_ANIMAL[b] for b in samhap if b != year_branch] + [K.BRANCH_ANIMAL[K.YUKHAP[year_branch]]]
    yinfo = K.ELEMENT[yong]
    lucky = {
        "element": yong, "element_name": yinfo["name"], "hanja": yinfo["hanja"],
        "color": yinfo["color"], "numbers": yinfo["numbers"], "direction": yinfo["direction"],
        "foods": yinfo["foods"], "items": yinfo["items"], "season": yinfo["season"],
        "animals": good_animals, "careful_animal": K.BRANCH_ANIMAL[K.CLASH_BRANCH[year_branch]],
        "basis": cl["yongsin"]["basis"] if cl else an["yongsin"]["억부_근거"],
    }

    def effect(stem_god: str, branch_god: str) -> str:
        return _effect(cl, stem_god, branch_god)

    # 대운
    dw = an["daewoon"]
    periods = []
    current_idx = 0
    for i, p in enumerate(dw["periods"]):
        if p["age_from"] <= age:
            current_idx = i
    if age < dw["periods"][0]["age_from"]:
        current_idx = -1
    for i, p in enumerate(dw["periods"]):
        state = "지금" if i == current_idx else "지난" if i < current_idx else "앞으로"
        periods.append({
            **p,
            "state": state,
            "years_text": f"{p['start_year']}~{p['start_year'] + 9}",
            "age_text": f"{p['age_from']}~{p['age_to']}세",
            "gyeok_effect": effect(p["stem_ten_god"], p["branch_ten_god"]),
            "score": luck_score(p["ganzhi"], p["relations"], good, excess, effect(p["stem_ten_god"], p["branch_ten_god"]), weights),
            "relations_text": _relations_text(p["relations"]),
            # 지금 대운과 다음 두 대운은 2쪽, 나머지는 1쪽
            "pages": 2 if 0 <= i - max(current_idx, 0) <= 2 else 1,
        })

    # 세운: 주문한 해부터 6년
    sewoon = [dict(s, gyeok_effect=effect(s["stem_ten_god"], s["branch_ten_god"]),
                   score=luck_score(s["ganzhi"], s["relations"], good, excess, effect(s["stem_ten_god"], s["branch_ten_god"]), weights),
                   relations_text=_relations_text(s["relations"]),
                   animal=K.BRANCH_ANIMAL[s["ganzhi"][1]],
                   pages=2 if i == 0 else 1)
              for i, s in enumerate(x for x in an["sewoon"] if x["year"] >= order.order_date.year)][:6]

    # 월운: 주문한 날이 속한 달부터 12개월
    order_dt = datetime(order.order_date.year, order.order_date.month, order.order_date.day, 12).isoformat()
    span = an.get("wolwoon_span") or an["wolwoon"]
    start = 0
    for i, m in enumerate(span):
        if m["starts"][:16] <= order_dt[:16]:
            start = i
    rate = luck_rater(an)
    months = [month_row(m, rate) for m in span[start:start + 12]]

    shinsal = [{**s, "label": PILLAR_LABEL[s["pillar"]], "text": K.SHINSAL.get(s["name"], "")} for s in an["shinsal"]]
    seen_names = []
    for s in shinsal:
        if s["name"] not in seen_names:
            seen_names.append(s["name"])

    relations = [{**r, "kind": K.relation_kind(r["type"]), "text": K.RELATION.get(K.relation_kind(r["type"]), "")}
                 for r in an["relations"]]

    sex_word = "남성" if result["person"]["sex"] == "male" else "여성"
    time_text = result["input"]["time"] or "모름"
    return {
        "person": {
            "name": result["person"]["name"] or "고객",
            "sex": result["person"]["sex"], "sex_word": sex_word,
            "birth": birth.isoformat(),
            "birth_text": f"{birth.year}년 {birth.month}월 {birth.day}일",
            "calendar": result["input"]["calendar"],
            "time_text": time_text, "place": result["input"]["place"],
            "age": age, "zodiac": an["zodiac"],
        },
        "order": {"date": order.order_date.isoformat(), "year": order.order_date.year,
                  "question": order.question.strip(), "daily": order.daily,
                  "relationship": order.relationship},
        "uncertainties": [u["message"] for u in result["uncertainties"]] + result["warnings"],
        "variant_count": result["variant_count"],
        "variants": [v["key"] for v in result["variants"]],
        "pillars": pillars,
        "day_master": {**dm, "hanja": dm_info["hanja"], "image": dm_info["image"], "basic": dm_info["basic"],
                       "strengths": dm_info["strengths"], "weaknesses": dm_info["weaknesses"],
                       "element_name": K.ELEMENT[dm["element"]]["name"],
                       "yin_yang": "양" if dm["yang"] else "음"},
        "elements": elements,
        "elements_excess": excess,
        "elements_lacking": an["elements"]["judgement"]["부족"],
        "ten_god_groups": groups,
        "missing_groups": missing_groups,
        "strength": {**an["strength"], "text": K.STRENGTH.get(an["strength"]["label"], "")},
        "gyeokguk": {**an["gyeokguk"], "text": K.GYEOKGUK.get(an["gyeokguk"]["name"], "")},
        "yongsin": {**an["yongsin"], "chosen": yong},
        "lucky": lucky,
        "classics": _classics_text(cl, dm["stem"]) if cl else None,
        "relations": relations,
        "shinsal": shinsal,
        "shinsal_names": seen_names,
        "daewoon": {"direction": dw["direction"], "number": dw["start"]["number"],
                    "current_index": current_idx, "periods": periods},
        "sewoon": sewoon,
        "months": months,
        "version": result["version"],
        "options": result["options"],
    }
