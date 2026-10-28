"""제1조항(모순 금지): 여러 손님 × 8개 상품에서 결제 전 화면과 리포트 재료가 같은지(saju/report/unity.py).

정확한 시간·대략 시간·시간 모름, 출생지 앎·모름을 섞어 본다. 이 검사가 깨지면 올리지 않는다.
"""

import random
from datetime import date, timedelta

import pytest

from saju.chart import analyze_person
from saju.regions import REGIONS
from saju.report import OrderInfo, PAIR_PRODUCTS, THEME_PRODUCTS, prepare_product, unity
from saju.report.facts import build_facts
from saju.report import romance as R
from saju.report.theme import reveal_fix

ORDER = OrderInfo(date(2026, 10, 28), "")


def _people(n: int, seed: int) -> list[dict]:
    g = random.Random(seed)
    codes = [c for c in REGIONS if not c.startswith("legacy")]
    out = []
    while len(out) < n:
        d = date(1950, 1, 1) + timedelta(days=g.randrange(365 * 55))
        h, mi = g.randrange(24), g.randrange(60)
        acc = ["exact", "approximate", "unknown"][len(out) % 3]
        p = {"name": "하늘", "sex": g.choice(["male", "female"]), "birth": d.isoformat(), "calendar": "solar",
             "timeAccuracy": acc, "time": f"{h:02d}:{mi:02d}" if acc == "exact" else None,
             "birthPlace": {"status": "known", "regionChoice": g.choice(codes)} if g.random() < 0.8 else {"status": "unknown"}}
        if acc == "approximate":
            e = h * 60 + mi + g.randrange(30, 240)
            p["timeRange"] = {"start": f"{h:02d}:{mi:02d}", "end": f"{e // 60 % 24:02d}:{e % 60:02d}", "endDayOffset": int(e >= 1440)}
        out.append(analyze_person(p, current_year=2026))
    return out


PEOPLE = _people(120, 20261028)


@pytest.mark.parametrize("pid", THEME_PRODUCTS)
def test_theme_products_match_screen(pid):
    for i, me in enumerate(PEOPLE):
        partner = PEOPLE[-1 - i] if pid in PAIR_PRODUCTS else None
        prepare_product(pid, me, ORDER, {}, partner)   # 어긋나면 UnityError


def test_lifetime_and_romance_match_screen():
    for me in PEOPLE:
        f = build_facts(me, ORDER)
        for rows in (f["sewoon"], f["sewoon_all"]):
            reveal_fix(me, "lifetime", rows, score="score", signs="r_signs")
        assert unity.problems("lifetime", me, f) == []
        f = build_facts(me, ORDER)
        f["romance"] = R.build_romance(f, me, ORDER)
        assert unity.problems("romance", me, f) == []


def test_guard_stops_a_report_that_differs_from_screen():
    me = PEOPLE[0]
    _, f, _ = prepare_product("wealth", me, ORDER, {}, None)
    f["theme"]["years"][0]["year"] += 1
    with pytest.raises(unity.UnityError):
        unity.require("wealth", me, f)
    _, f, _ = prepare_product("wealth", me, ORDER, {}, None)
    f["theme"]["data"]["screen_score"]["score"] += 1
    with pytest.raises(unity.UnityError):
        unity.require("wealth", me, f)
