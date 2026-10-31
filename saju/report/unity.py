"""제1조항(모순 금지) 검사: 고객이 사이트에서 본 것과 리포트 재료가 한 글자도 어긋나지 않는지.

리포트를 만들기 전에 반드시 이 검사를 지나야 한다. 어긋나면 UnityError 로 멈춘다
(어긋난 리포트를 고객에게 보내느니 보내지 않는다 — 2026-10-28 사장님: "모든 곳에서의 통일성을 제 1원칙으로 못 박아").

검사하는 것
- 해·달 지도: 결제 전 화면의 12년(신년운세는 2027년 12달, 재회사주는 앞으로 24개월)과 리포트 표가 같은 해·달, 같은 좋은/조심 표시
- 점수 방향: 좋은 표시만 있는 해는 60점 이상, 조심 표시만 있는 해는 40점 이하
- 점수: 결제 전 화면 '내 점수'(전체·좋은 점·조심할 점)가 리포트 첫 요약에 그대로
- 두 사람 궁합 점수(깊은 궁합·재회사주): 결제 전 화면과 리포트가 같은 점수
"""

from .. import reveal as RV
from .. import taster


class UnityError(RuntimeError):
    """화면과 리포트가 어긋난다(제1조항)."""


def _rows(product: str, facts: dict) -> tuple[list[dict], str]:
    if product == "lifetime":
        from .theme import screen_years
        return screen_years(facts), "score"
    if product == "romance":
        return facts["romance"]["years"], "love_score"
    th = facts["theme"]
    return (th["months"] if product in ("newyear", "reunion") else th["years"]), "t_score"


def problems(product: str, result: dict, facts: dict, partner: dict | None = None) -> list[str]:
    out = []
    fp = taster.pillars_from_result(result)
    sex = result["person"].get("sex", "")
    m = RV.screen_map(fp, sex, product, facts["order"]["date"], facts["order"].get("reveal_start", ""))
    rows, score = _rows(product, facts)
    cells = m["cells"]
    if len(rows) != len(cells):
        out.append(f"화면은 {len(cells)}칸인데 리포트 표는 {len(rows)}칸")
    for r, c in zip(rows, cells):
        name = c["label"] if m["unit"] == "month" else f"{c['label']}년"
        if m["unit"] == "year" and r["year"] != int(c["label"]):
            out.append(f"{name}: 리포트 표는 {r['year']}년")
            continue
        if r["ganzhi"] != c["ko"]:
            out.append(f"{name}: 간지가 다름({r['ganzhi']} / 화면 {c['ko']})")
        if bool(r.get("r_good")) != bool(c["good"]) or bool(r.get("r_bad")) != bool(c["bad"]):
            out.append(f"{name}: 좋은/조심 표시가 화면과 다름")
        if c["label"] == "2027" and (product == "lifetime" or all(k.startswith("ny_") for k in c["good"] + c["bad"])):
            ny = RV.ny_verdict(fp, sex)[1]
            if r[score] != ny:
                out.append(f"2027년: 무료 풀이 '2027년 운'은 {ny}점인데 리포트는 {r[score]}점")
            continue
        if c["good"] and not c["bad"] and r[score] < 60:
            out.append(f"{name}: 화면은 좋은 표시인데 리포트 점수 {r[score]}점")
        if c["bad"] and not c["good"] and r[score] > 40:
            out.append(f"{name}: 화면은 조심 표시인데 리포트 점수 {r[score]}점")
    if product != "lifetime":
        seen = RV.digest(fp, facts["person"]["name"], sex, product, facts["order"]["date"], facts["order"].get("reveal_start", ""))["화면에서 본 점수"]
        want = {"score": seen["전체 점수"], "good": seen["좋은 점"]["점수"], "bad": seen["조심할 점"]["점수"]}
        got = facts["romance"].get("screen_score") if product == "romance" else facts["theme"]["data"].get("screen_score")
        if got != want:
            out.append(f"화면 점수 {want}와 리포트 점수 {got}가 다름")
    # 책끼리: 신년운세 결제 전 화면에서 '조심할 달'인 2027년 달을 다른 책이 좋은 달로 쓰지 않는다(묶음으로 함께 사는 책, 손님 테스트 3차)
    ny_bad = {c["ko"]: c["label"] for c in RV.luck_map(fp, sex, "newyear")["cells"] if c["bad"]}
    # 반대 방향도: '돕는 달'을 다른 책이 조심할 달로 쓰지 않는다. 신년운세 분야와 겹치는 책은 같은 달 점수가 신년운세 분야 점수와 같다(손님 테스트 4차).
    ny_good = {c["ko"] for c in RV.luck_map(fp, sex, "newyear")["cells"] if c["good"]}
    if product == "newyear":
        th = facts["theme"]
        for r in th["months"]:
            for k, ar in r["areas"].items():
                if r.get("r_bad") and ar["score"] >= 60:
                    out.append(f"신년운세 {r['label']}: 조심할 달인데 분야 '{k}'는 {ar['score']}점(좋은 달)")
                if r.get("r_good") and (ar["score"] <= 40 or ar.get("bad")):
                    out.append(f"신년운세 {r['label']}: 돕는 달인데 분야 '{k}'는 {ar['score']}점(조심할 달)")
        for k, v in (th["data"].get("areas") or {}).items():
            sc = {r["label"]: r["areas"][k]["score"] for r in th["months"]}
            for lb in v.get("best_months", []):
                if sc.get(lb, 0) < 60:
                    out.append(f"신년운세 {v['name']} '좋은 달' {lb}: 같은 분야 달 표는 {sc.get(lb)}점")
            for lb in v.get("careful_months", []):
                if sc.get(lb, 100) > 40 and not next(r for r in th["months"] if r["label"] == lb)["areas"][k].get("bad"):
                    out.append(f"신년운세 {v['name']} '조심할 달' {lb}: 같은 분야 달 표는 {sc.get(lb)}점")
    else:
        from .facts import NY_AREA
        if product == "romance":
            months, sc = facts["romance"]["months"], "love_score"
        elif product == "lifetime":
            months, sc = facts["months"], "score"
        else:
            months, sc = (facts.get("theme") or {}).get("months") or [], "t_score"
        for r in months:
            if r.get("year") != 2027 or "ganzhi" not in r:
                continue
            nm = f"2027년 {r['month']}월"
            if r["ganzhi"] in ny_bad and (r.get("r_good") or r.get(sc, 0) >= 60):
                out.append(f"{nm}: 신년운세 화면은 조심할 달인데 이 책은 좋은 달({r.get(sc)}점)")
            if r["ganzhi"] in ny_good and (r.get("r_bad") or r.get(sc, 100) <= 40):
                out.append(f"{nm}: 신년운세 화면은 돕는 달인데 이 책은 조심할 달({r.get(sc)}점)")
            ar = (r.get("ny_areas") or {}).get(NY_AREA.get(product, ""))
            if ar is not None and r.get(sc) != ar["score"]:
                out.append(f"{nm}: 신년운세 같은 분야는 {ar['score']}점인데 이 책은 {r.get(sc)}점")
    if partner is not None and product in ("intimate", "reunion"):
        from ..pair import pair_score
        want = pair_score(fp, taster.pillars_from_result(partner))
        got = facts["theme"]["data"].get("score" if product == "intimate" else "pair_score")
        if got != want:
            out.append(f"화면의 두 사람 궁합 점수 {want}점과 리포트 {got}점이 다름")
    return out


def require(product: str, result: dict, facts: dict, partner: dict | None = None) -> None:
    bad = problems(product, result, facts, partner)
    if bad:
        raise UnityError("제1조항 위반(화면과 리포트가 다름): " + " / ".join(bad[:8]))
