"""결제 전 이야기 화면(saju/reveal.py)과 리포트 검사."""

from saju import reveal, taster
from saju.chart import analyze_person
from saju.report.verify import shown_checks

ME = {"name": "김민준", "sex": "male", "birth": "1990-04-15", "calendar": "solar", "timeAccuracy": "exact", "time": "08:00",
      "birthPlace": {"status": "known", "regionChoice": "11110"}}


def _fp():
    return taster.pillars_from_result(analyze_person(ME))


def test_month_pillars_follow_year_stem():
    assert [m["ko"] for m in reveal.months_of(2027)][:2] == ["임인", "계묘"]
    assert reveal.months_of(2034)[0]["ko"] == "병인"   # 갑년의 첫 달은 병인


def test_digest_gives_computed_months_for_every_shown_year():
    d = reveal.digest(_fp(), "김민준", "male", "wealth", 2026)
    assert d["리포트에 나와야 하는 해·달"] == ["2034년", "2035년", "2029년", "2031년"]
    good = d["좋은 해"][0]
    months = good["그 해 안에서 같은 기운이 들어오는 달(절기 기준, 매달 4~8일 무렵 시작)"]
    assert set(months) == {"2034년", "2035년"} and all(months.values())


def test_shown_years_missing_from_report_are_sent_back_to_final_chapter():
    seen = {"결제 전 이야기 화면에서 본 내용": {"리포트에 나와야 하는 해·달": ["2034년", "2029년"]}}
    texts = {"a1": "2034년 3월에 돈이 들어옵니다.", "z9": "마지막 정리입니다."}
    issues = shown_checks({"taster": seen}, texts, {"z9"})
    assert len(issues) == 1 and issues[0]["slot"] == "z9" and "2029년" in issues[0]["detail"] and "2034년" not in issues[0]["detail"]
    assert shown_checks({"taster": seen}, {**texts, "z9": "2029년에는 돈을 지킵니다."}, {"z9"}) == []
