"""상대 생일 없이 보는 재회사주 (2026-11-05): 그 사람 사주 없이 내 사주로만 50쪽 이상, 그 사람을 단정하지 않는다."""

from datetime import date, datetime

import pytest

from saju.chart import analyze_person
from saju.order import KST, order_info
from saju.report import DraftWriter, OrderInfo, make_product_report, prepare_product
from saju.report.outline import all_pages

ME = {"name": "윤서진", "sex": "female", "birth": "1993-09-05", "calendar": "solar", "timeAccuracy": "exact",
      "time": "11:50", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
SOLO = OrderInfo(date(2026, 10, 11), "다시 연락해도 될까요?", partner_unknown=True, partner_name="정민호")


def test_solo_outline_has_no_partner_chart():
    me = analyze_person(ME, current_year=2026)
    M, facts, secs = prepare_product("reunion", me, SOLO, {"breakup": "3~6개월 정도예요"}, None)
    t = facts["theme"]["data"]
    assert t["solo"] and t["pair_score"] is None and "partner" not in facts and t["partner_name"] == "정민호"
    assert [s["no"] for s in secs] == [str(i) for i in range(1, 13)] + ["더보기"]
    pages = all_pages(secs)
    assert sum(p["span"] for p in pages) >= 50
    ids = [p["id"] for p in pages]
    assert len(ids) == len(set(ids))
    assert not any(p.get("figure") == "pair_pillars" for p in pages)
    titles = {s["no"]: s["title"] for s in secs}
    assert titles["5"] == "내가 끌리는 사람, 나와 맞는 사람" and titles["6"] == "그 사람과 나 사이에 반복된 것"
    slots = str([p.get("slot") for p in pages])
    assert "그 사람의 사주표" not in slots and "두 사람 비교" not in slots
    assert "단정하지 않습니다" in M.style_for(facts) and M.style_for(facts) != M.STYLE
    assert len(facts["theme"]["months"]) == 24


def test_reunion_without_flag_still_needs_partner():
    me = analyze_person(ME, current_year=2026)
    with pytest.raises(ValueError):
        prepare_product("reunion", me, OrderInfo(date(2026, 10, 11)), {}, None)
    with pytest.raises(ValueError):
        prepare_product("intimate", me, SOLO, {}, None)


def test_order_info_reads_unknown_partner():
    when = datetime(2026, 11, 5, 12, tzinfo=KST)
    o, _ = order_info("reunion", {"answers": {}, "partner": {"name": "정민호", "birthUnknown": True}}, when)
    assert o.partner_unknown and o.partner_name == "정민호"
    o, _ = order_info("intimate", {"answers": {}, "partner": {"name": "정민호", "birthUnknown": True}}, when)
    assert not o.partner_unknown


def test_solo_pdf_50_pages(tmp_path):
    me = analyze_person(ME, current_year=2026)
    r = make_product_report("reunion", me, SOLO, tmp_path / "s.pdf", DraftWriter(), answers={}, partner=None)
    assert r["pages"] >= 50
