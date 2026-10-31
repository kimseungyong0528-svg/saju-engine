"""무료 맛보기 계산기(site/public/assets/free/engine.mjs)가 파이썬 엔진과 같은 답을 내는지
비교할 정답표를 만든다(정확 시간·모름 400건 + 대략 시간 100건 + 절기 날 시간 모름 100건) → site/tests/fixtures/taster-parity.json

예) python site/tools/make_taster_fixture.py
"""

import json
import random
from datetime import datetime, date, timedelta
from pathlib import Path

from saju.chart import analyze_person
from saju import astro, reveal, taster
from saju.pair import pair_score
from saju.timeutil import SEOUL_TZ
from saju.regions import REGIONS

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "taster-parity.json"


def _boundary(r: dict) -> list[str]:
    """리포트 사주표에 나오는 '태어난 시각이 N분만 … 달라지는 경계예요' 줄(결제 전 화면 STEP 1에도 같은 줄이 나온다)."""
    from saju.report import _BOUNDARY, _merge_boundary
    f = {"uncertainties": [w for w in r["warnings"] if _BOUNDARY.fullmatch(w)]}
    _merge_boundary(f)
    return f["uncertainties"]


def main() -> None:
    rnd = random.Random(20261025)
    codes = [c for c in REGIONS if not c.startswith("legacy")]
    cases = []
    arnd = random.Random(20261028)   # 대략 시간 100건(앞의 400건은 그대로 둔다)
    srnd = random.Random(20261029)   # 절기 날 + 시간 모름 100건: 사이트·리포트 모두 낮 12시 명식
    brnd = random.Random(20261031)   # 경계 근처 정확 시간 100건(명식 후보가 둘이어도 넣는다): 화면과 리포트의 경계 안내가 같은지
    while len(cases) < 700:
        approx = 400 <= len(cases) < 500
        term = 500 <= len(cases) < 600
        edge = len(cases) >= 600
        g = brnd if edge else srnd if term else arnd if approx else rnd
        d = date(1940, 1, 1) + timedelta(days=g.randrange(365 * 86))
        if edge:
            code = g.choice(codes)
            if g.random() < 0.6:   # 절입 시각 ±15분
                tt = g.choice(astro.solar_terms(g.randrange(1941, 2025)))[0].astimezone(SEOUL_TZ) + timedelta(minutes=g.randrange(-15, 16))
            else:                  # 시주가 바뀌는 시각 근처(홀수 시 30분 무렵, 경도 보정 포함)
                tt = datetime.combine(d, datetime.min.time()) + timedelta(hours=g.randrange(1, 24, 2), minutes=g.randrange(15, 60))
            person = {"name": "하늘", "sex": g.choice(["male", "female"]), "birth": tt.date().isoformat(), "calendar": "solar",
                      "timeAccuracy": "exact", "time": tt.strftime("%H:%M"),
                      "birthPlace": {"status": "known", "regionChoice": code}}
            r = analyze_person(person)
            cases.append({"person": person, "key": r["variants"][0]["key"], "boundary": _boundary(r), "edge": True})
            continue
        if term:
            y = g.randrange(1941, 2025)
            d = g.choice(astro.solar_terms(y))[0].astimezone(SEOUL_TZ).date()
        known = approx or (not term and g.random() < 0.8)
        t = f"{g.randrange(24):02d}:{g.randrange(60):02d}" if known else None
        code = g.choice(codes)
        person = {"name": "하늘", "sex": g.choice(["male", "female"]), "birth": d.isoformat(), "calendar": "solar",
                  "timeAccuracy": "exact" if known else "unknown", "time": t,
                  "birthPlace": {"status": "known", "regionChoice": code}}
        if approx:
            # 대략 시간: 리포트는 범위 첫 명식(시작 시각)으로 풀고, 화면도 같은 시주를 써야 한다(제1조항)
            h, mi = map(int, t.split(":"))
            e = h * 60 + mi + g.randrange(30, 240)
            person.update(timeAccuracy="approximate", time=None,
                          timeRange={"start": t, "end": f"{e // 60 % 24:02d}:{e % 60:02d}", "endDayOffset": int(e >= 1440)})
        r = analyze_person(person)
        if r["variant_count"] != 1 and not (approx or term):
            continue
        an = r["variants"][0]["analysis"]
        cases.append({
            "person": person,
            "key": r["variants"][0]["key"],
            "elements": an["elements"]["strength"],
            "groups": an["ten_god_groups"],
            "strength": an["strength"]["score"],
            "gyeokguk": an["gyeokguk"]["name"],
            "shinsal": sorted(f"{s['name']}|{s['pillar']}" for s in an["shinsal"]),
            "reading": taster.reading(taster.pillars_from_result(r), "하늘", person["sex"]),
            # 결제 전 이야기 화면(reveal.mjs): 상품별 점수 글과 해·달 지도
            "areas": {a: {k: v for k, v in taster.area_view(taster.pillars_from_result(r), "하늘", person["sex"], a).items()
                          if k in ("id", "score", "reason", "text", "hook", "sign")} for a in taster.AREA_ORDER},
            "parts": {a: taster.area_parts(taster.pillars_from_result(r), "하늘", person["sex"], a) for a in taster.AREA_ORDER},
            "maps": {pid: reveal.luck_map(taster.pillars_from_result(r), person["sex"], pid)
                     for pid in taster.texts()["REVEAL"]["PRODUCTS"]},
            "_fp": taster.pillars_from_result(r),
            "boundary": _boundary(r),
        })
    # 깊은 궁합·재회사주 결제 전 화면의 '두 사람 궁합 점수': 손님 i와 손님 i+7을 짝지어 본다
    edges = [c for c in cases if c.get("edge")]
    cases = [c for c in cases if not c.get("edge")]
    for i, c in enumerate(cases):
        j = (i + 7) % len(cases)
        c["pair"] = {"with": j, "score": pair_score(c["_fp"], cases[j]["_fp"])}
    for c in cases:
        del c["_fp"]
    cases += edges
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cases, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(cases)}건 → {OUT}")


if __name__ == "__main__":
    main()
