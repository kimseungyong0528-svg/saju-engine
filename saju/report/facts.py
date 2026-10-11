"""사주 계산 결과를 리포트 재료(facts)로 정리한다.

여기서 만드는 값은 모두 계산으로 정해지는 것들이다(글자, 개수, 날짜, 점수).
문장은 writer가 이 재료를 보고 쓴다. 숫자와 글자는 facts에서만 가져와야 틀리지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from . import knowledge as K

PILLAR_LABEL = {"년주": "태어난 해", "월주": "태어난 달", "일주": "태어난 날", "시주": "태어난 시간"}


@dataclass
class OrderInfo:
    """주문할 때 받은 정보."""
    order_date: date = field(default_factory=date.today)
    question: str = ""          # 고객이 남긴 질문(없을 수 있음)
    daily: str = ""             # 요즘 일상: 직장/사업/프리랜서/공부/휴식


def _age_on(birth: date, on: date) -> int:
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def pick_yongsin(an: dict) -> str:
    """행운 아이템 기준으로 쓸 오행 하나. 조후와 억부가 겹치면 그것, 아니면 억부 첫째, 아니면 가장 약한 오행."""
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


def luck_score(ganzhi: str, relations: list[dict], good: list[str], bad: list[str]) -> int:
    """운의 흐름 점수(참고용, 20~90). 필요한 기운이 오면 오르고, 넘치는 기운이 더해지거나 부딪히면 내려간다."""
    score = 55
    for i, el in enumerate(_ganzhi_elements(ganzhi)):
        weight = 10 if i == 0 else 14   # 지지가 실제 생활에 더 크게 작용한다고 본다
        if el in good:
            score += weight
        if el in bad:
            score -= weight
    for r in relations:
        kind = K.relation_kind(r["type"])
        if kind in ("천간합", "육합", "반합", "삼합"):
            score += 3
        elif kind in ("충", "천간충"):
            score -= 5
        elif kind in ("형", "자형", "파", "해", "원진"):
            score -= 3
    return max(20, min(90, score))


def _relations_text(relations: list[dict]) -> list[str]:
    out = []
    for r in relations:
        kind = K.relation_kind(r["type"])
        target = PILLAR_LABEL.get(r.get("with", ""), r.get("with", ""))
        out.append(f"{target}와 {kind}")
    return sorted(set(out))


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
    excess = an["elements"]["judgement"]["과다"]
    good = [yong] + [e for e in an["yongsin"]["억부"] if e != yong]
    year_branch = an["pillars"][0]["branch"]
    samhap = next(t for t in K.SAMHAP if year_branch in t)
    good_animals = [K.BRANCH_ANIMAL[b] for b in samhap if b != year_branch] + [K.BRANCH_ANIMAL[K.YUKHAP[year_branch]]]
    yinfo = K.ELEMENT[yong]
    lucky = {
        "element": yong, "element_name": yinfo["name"], "hanja": yinfo["hanja"],
        "color": yinfo["color"], "numbers": yinfo["numbers"], "direction": yinfo["direction"],
        "foods": yinfo["foods"], "items": yinfo["items"], "season": yinfo["season"],
        "animals": good_animals, "careful_animal": K.BRANCH_ANIMAL[K.CLASH_BRANCH[year_branch]],
        "basis": an["yongsin"]["억부_근거"],
    }

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
            "score": luck_score(p["ganzhi"], p["relations"], good, excess),
            "relations_text": _relations_text(p["relations"]),
            # 지금 대운과 다음 세 대운은 2쪽, 나머지는 1쪽
            "pages": 2 if 0 <= i - max(current_idx, 0) <= 3 else 1,
        })

    # 세운: 주문한 해부터 6년
    sewoon = [dict(s, score=luck_score(s["ganzhi"], s["relations"], good, excess),
                   relations_text=_relations_text(s["relations"]),
                   animal=K.BRANCH_ANIMAL[s["ganzhi"][1]],
                   pages=2 if i < 2 else 1)
              for i, s in enumerate(x for x in an["sewoon"] if x["year"] >= order.order_date.year)][:6]

    # 월운: 주문한 날이 속한 달부터 12개월
    order_dt = datetime(order.order_date.year, order.order_date.month, order.order_date.day, 12).isoformat()
    span = an.get("wolwoon_span") or an["wolwoon"]
    start = 0
    for i, m in enumerate(span):
        if m["starts"][:16] <= order_dt[:16]:
            start = i
    months = []
    for m in span[start:start + 12]:
        d = datetime.fromisoformat(m["starts"])
        months.append({**m, "start_text": f"{d.year}년 {d.month}월 {d.day}일",
                       "short": f"{d.month}/{d.day}", "month": d.month, "year": d.year,
                       "score": luck_score(m["ganzhi"], m["relations"], good, excess),
                       "relations_text": _relations_text(m["relations"])})

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
                  "question": order.question.strip(), "daily": order.daily},
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
