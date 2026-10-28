"""무료 맛보기 계산기(site/public/assets/free/engine.mjs)가 파이썬 엔진과 같은 답을 내는지
비교할 정답표를 만든다(정확 시간·모름 400건 + 대략 시간 100건 + 절기 날 시간 모름 100건) → site/tests/fixtures/taster-parity.json

예) python site/tools/make_taster_fixture.py
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

from saju.chart import analyze_person
from saju import astro, reveal, taster
from saju.timeutil import SEOUL_TZ
from saju.regions import REGIONS

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "taster-parity.json"


def main() -> None:
    rnd = random.Random(20261025)
    codes = [c for c in REGIONS if not c.startswith("legacy")]
    cases = []
    arnd = random.Random(20261028)   # 대략 시간 100건(앞의 400건은 그대로 둔다)
    srnd = random.Random(20261029)   # 절기 날 + 시간 모름 100건: 사이트·리포트 모두 낮 12시 명식
    while len(cases) < 600:
        approx = 400 <= len(cases) < 500
        term = len(cases) >= 500
        g = srnd if term else arnd if approx else rnd
        d = date(1940, 1, 1) + timedelta(days=g.randrange(365 * 86))
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
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cases, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(cases)}건 → {OUT}")


if __name__ == "__main__":
    main()
