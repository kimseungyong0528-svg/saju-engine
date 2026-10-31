"""주제 사주 7종(사업운은 13장)(재회·깊은 궁합·재물·직업·사업·건강·2027 신년운세): 목차, 쪽수, 두 사람 상품, 다른 상품 안내."""

from datetime import date
import importlib

import pytest

from saju.chart import analyze_person
from saju.report import OrderInfo, DraftWriter, THEME_PRODUCTS, PAIR_PRODUCTS, make_product_report, prepare_product
from saju.report.outline import all_pages
from saju.report.render import COVER, PRODUCT

ME = {"name": "윤서진", "sex": "female", "birth": "1993-09-05", "calendar": "solar", "timeAccuracy": "exact",
      "time": "11:50", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
PARTNER = {"name": "정민호", "sex": "male", "birth": "1995-03-11", "calendar": "solar", "timeAccuracy": "exact",
           "time": "22:10", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
ORDER = OrderInfo(date(2026, 10, 11), "앞으로 어떻게 하면 좋을까요?")


def _prep(pid):
    me = analyze_person(ME, current_year=2026)
    partner = analyze_person(PARTNER, current_year=2026) if pid in PAIR_PRODUCTS else None
    return me, partner, prepare_product(pid, me, ORDER, {}, partner)


@pytest.mark.parametrize("pid", THEME_PRODUCTS)
def test_outline_12_chapters_and_50_pages(pid):
    _, _, (M, facts, secs) = _prep(pid)
    n = len(M.SECTIONS) - 1
    assert [s["no"] for s in secs] == [str(i) for i in range(1, n + 1)] + ["더보기"]
    assert M.FINAL_SECTION == str(n) and n >= 12
    assert sum(p["span"] for p in all_pages(secs)) >= 50
    ids = [p["id"] for p in all_pages(secs)]
    assert len(ids) == len(set(ids))
    t = facts["theme"]
    assert len(t["months"]) == (24 if pid == "reunion" else 12)
    if pid == "reunion":   # 재회사주는 앞으로 24개월 달마다 본다(사장님 2026-10-30): 화면 지도와 같은 달, 같은 방향
        from saju import reveal as RV
        m = RV.screen_map(RV.taster.pillars_from_result(_prep(pid)[0]), ME["sex"], pid, facts["order"]["date"])
        assert [(r["ganzhi"], f"{r['year']}년 {r['month']}월") for r in t["months"]] == [(c["ko"], c["label"]) for c in m["cells"]]
        for r, c in zip(t["months"], m["cells"]):
            assert bool(r["r_good"]) == bool(c["good"]) and bool(r["r_bad"]) == bool(c["bad"])
    elif pid != "newyear":   # 신년운세는 2027년 한 해만 본다(tests/test_newyear.py)
        # 제1조항: 연도 표는 결제 전 화면의 12년 지도와 같은 해, 같은 방향(좋은 표시 해는 60점 이상, 조심 표시만 있는 해는 40점 이하)
        from saju import reveal as RV
        m = RV.luck_map(RV.taster.pillars_from_result(_prep(pid)[0]), ME["sex"], pid, 2027)
        assert [y["year"] for y in t["years"]] == [int(c["label"]) for c in m["cells"]]
        for y, c in zip(t["years"], m["cells"]):
            assert bool(y["r_good"]) == bool(c["good"]) and bool(y["r_bad"]) == bool(c["bad"])
            if c["label"] == "2027" and all(k.startswith("ny_") for k in c["good"] + c["bad"]):
                # 2027년 칸에 '2027년 좋은 흐름·조심'만 있으면 맛보기 '2027년 운' 점수 그대로
                assert y["t_score"] == RV.ny_verdict(RV.taster.pillars_from_result(_prep(pid)[0]), ME["sex"])[1]
            elif c["good"] and not c["bad"]:
                assert y["t_score"] >= 60
            elif c["bad"] and not c["good"]:
                assert y["t_score"] <= 40
    assert all(20 <= m["score"] <= 95 for m in t["months"])
    assert PRODUCT[pid]["cover"] is COVER[pid]


@pytest.mark.parametrize("pid", PAIR_PRODUCTS)
def test_pair_products_need_partner(pid):
    me = analyze_person(ME, current_year=2026)
    with pytest.raises(ValueError):
        prepare_product(pid, me, ORDER, {}, None)


@pytest.mark.parametrize("pid", ["reunion", "health"])
def test_pdf_50_pages_and_cross_sell(pid, tmp_path):
    me, partner, _ = _prep(pid)
    r = make_product_report(pid, me, ORDER, tmp_path / "r.pdf", DraftWriter(), answers={}, partner=partner)
    assert r["pages"] >= 50
    html = (tmp_path / "r.html")
    make_product_report(pid, me, ORDER, tmp_path / "r2.pdf", DraftWriter(), html_out=html, answers={}, partner=partner,
                        texts=r["texts"])
    body = html.read_text()
    assert "다른 사주도 궁금하다면" in body and 'href="#sec-' not in body


def test_lifetime_and_romance_writer_untouched():
    from saju.report import ClaudeWriter
    assert ClaudeWriter.final_section == "15" and "'평생사주'" in ClaudeWriter.style
    for pid in THEME_PRODUCTS:
        M = importlib.import_module(f"saju.report.{pid}")
        assert "{name}" in M.STYLE
