"""주제 사주 6종(사업운은 13장)(재회·깊은 궁합·재물·직업·사업·건강): 목차, 쪽수, 두 사람 상품, 다른 상품 안내."""

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
    assert len(t["years"]) == 5 and len(t["months"]) == 12
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
