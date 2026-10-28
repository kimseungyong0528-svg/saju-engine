"""제1조항(모순 금지) 검사: 고객이 사이트에서 본 것과 리포트 재료가 한 글자도 어긋나지 않는지.

리포트를 만들기 전에 반드시 이 검사를 지나야 한다. 어긋나면 UnityError 로 멈춘다
(어긋난 리포트를 고객에게 보내느니 보내지 않는다 — 2026-10-28 사장님: "모든 곳에서의 통일성을 제 1원칙으로 못 박아").

검사하는 것
- 해·달 지도: 결제 전 화면의 12년(신년운세는 2027년 12달)과 리포트 표가 같은 해·달, 같은 좋은/조심 표시
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
    return (th["months"] if product == "newyear" else th["years"]), "t_score"


def problems(product: str, result: dict, facts: dict, partner: dict | None = None) -> list[str]:
    out = []
    fp = taster.pillars_from_result(result)
    sex = result["person"].get("sex", "")
    m = RV.luck_map(fp, sex, product, RV.start_year(int(facts["order"]["date"][:4])))
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
        if product == "lifetime" and c["label"] == "2027":
            ny = RV.ny_verdict(fp, sex)[1]
            if r[score] != ny:
                out.append(f"2027년: 무료 풀이 '2027년 운'은 {ny}점인데 리포트는 {r[score]}점")
            continue
        if c["good"] and not c["bad"] and r[score] < 60:
            out.append(f"{name}: 화면은 좋은 표시인데 리포트 점수 {r[score]}점")
        if c["bad"] and not c["good"] and r[score] > 40:
            out.append(f"{name}: 화면은 조심 표시인데 리포트 점수 {r[score]}점")
    if product not in ("lifetime", "romance"):
        seen = RV.digest(fp, facts["person"]["name"], sex, product, int(facts["order"]["date"][:4]))["화면에서 본 점수"]
        want = {"score": seen["전체 점수"], "good": seen["좋은 점"]["점수"], "bad": seen["조심할 점"]["점수"]}
        if facts["theme"]["data"].get("screen_score") != want:
            out.append(f"화면 점수 {want}와 리포트 점수 {facts['theme']['data'].get('screen_score')}가 다름")
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
