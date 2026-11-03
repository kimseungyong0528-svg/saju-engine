"""연애사주 리포트: 재료, 목차, 쪽수, 다른 상품 순서."""

from datetime import date

from saju.chart import analyze_person
from saju.report import OrderInfo, ClaudeWriter, DraftWriter, make_romance_report
from saju.report import romance as R
from saju.report.facts import build_facts
from saju.report.outline import all_pages
from saju.report.products import cross_sell

SAMPLE = {"name": "이수아", "sex": "female", "birth": "2002-04-17", "calendar": "solar", "timeAccuracy": "exact",
          "time": "08:40", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
ORDER = OrderInfo(date(2026, 10, 11), "다음 연애는 언제 시작될까요?", "", "지금은 솔로예요", "1~2번")


def _facts():
    result = analyze_person(SAMPLE, current_year=2026)
    f = build_facts(result, ORDER)
    f["romance"] = R.build_romance(f, result, ORDER)
    return f


def test_romance_facts():
    r = _facts()["romance"]
    assert r["spouse_group"] == "관성" and r["status"] == "솔로" and r["experience"] == "1~2번"
    assert len(r["years"]) == 12 and len(r["months"]) == 12
    assert all(20 <= m["love_score"] <= 95 for m in r["months"])
    assert r["best_years"] == sorted(r["best_years"])


def test_romance_outline_about_50_pages():
    secs = R.build_outline(_facts())
    assert [s["no"] for s in secs] == [str(i) for i in range(1, 11)] + ["더보기"]
    planned = sum(p["span"] for p in all_pages(secs))
    assert 48 <= planned <= 54
    ids = [p["id"] for p in all_pages(secs)]
    assert len(ids) == len(set(ids))


def test_romance_pdf_and_writer_settings(tmp_path):
    r = make_romance_report(analyze_person(SAMPLE, current_year=2026), ORDER, tmp_path / "r.pdf", DraftWriter())
    assert 48 <= r["pages"] <= 56
    # 평생사주 글쓰기 기본값은 그대로
    assert ClaudeWriter.final_section == "15" and "'평생사주'" in ClaudeWriter.style
    assert "'연애사주'" in R.ROMANCE_STYLE and "{name}" in R.ROMANCE_STYLE


def test_cross_sell_follows_site_category_order_lifetime_last():
    f = _facts()
    ids = [p["id"] for p in cross_sell(f, current="romance", first=R.cross_sell_order("썸"))]
    assert ids == ["newyear", "intimate", "reunion", "wealth", "career", "business", "health", "lifetime"]


def test_cover_color_and_toc_without_links():
    from saju.report.render import COVER, PRODUCT, render_html
    f = _facts()
    secs = R.build_outline(f)
    html = render_html(f, secs, DraftWriter().write(f, secs), product="romance")
    assert COVER["romance"]["glow_out"] in html and PRODUCT["lifetime"]["cover"] is COVER["lifetime"]
    assert 'href="#sec-' not in html and 'data-target="#sec-1"' in html
