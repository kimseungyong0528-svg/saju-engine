"""리포트 본문과 책 끝 보너스 쪽(무료 분석과 같은 6가지 운)이 같은 숫자·근거를 쓰는지 확인한다."""
import random

from saju import taster as T
from saju.chart import analyze_person
from saju.report.facts import build_facts


def test_report_facts_match_taster_basis():
    rnd = random.Random(2027)
    for _ in range(80):
        y, m, d = rnd.randint(1950, 2010), rnd.randint(1, 12), rnd.randint(1, 28)
        sex = rnd.choice(["male", "female"])
        raw = {"name": "가", "sex": sex, "birth": f"{y}-{m:02d}-{d:02d}", "calendar": "solar", "timeAccuracy": "exact",
               "time": f"{rnd.randint(0, 23):02d}:{rnd.choice([0, 30]):02d}",
               "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
        me = analyze_person(raw, current_year=2026)
        f = build_facts(me)
        tf = T._facts(T.pillars_from_result(me), sex)
        for e in f["elements"]:
            assert T._num(e["pct"]) == T._num(tf["elements"][e["el"]]), raw   # 오행 비율 글자까지 같게(예: 1.6%)
        for g in f["ten_god_groups"]:
            assert g["n"] == tf["groups"][g["group"]], raw
        assert f["gyeokguk"]["name"] == tf["gyeok"], raw
        assert (f["strength"]["score"], f["strength"]["label"]) == (tf["st"], tf["st_label"]), raw
        assert tf["names"] <= set(f["shinsal_names"]), raw
