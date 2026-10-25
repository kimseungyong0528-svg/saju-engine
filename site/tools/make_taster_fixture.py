"""무료 맛보기 계산기(site/public/assets/free/engine.mjs)가 파이썬 엔진과 같은 답을 내는지
비교할 정답표를 만든다 → site/tests/fixtures/taster-parity.json

예) python site/tools/make_taster_fixture.py
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

from saju.chart import analyze_person
from saju import taster
from saju.regions import REGIONS

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "taster-parity.json"


def main() -> None:
    rnd = random.Random(20261025)
    codes = [c for c in REGIONS if not c.startswith("legacy")]
    cases = []
    while len(cases) < 400:
        d = date(1940, 1, 1) + timedelta(days=rnd.randrange(365 * 86))
        known = rnd.random() < 0.8
        t = f"{rnd.randrange(24):02d}:{rnd.randrange(60):02d}" if known else None
        code = rnd.choice(codes)
        person = {"name": "하늘", "sex": rnd.choice(["male", "female"]), "birth": d.isoformat(), "calendar": "solar",
                  "timeAccuracy": "exact" if known else "unknown", "time": t,
                  "birthPlace": {"status": "known", "regionChoice": code}}
        r = analyze_person(person)
        if r["variant_count"] != 1:
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
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cases, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"{len(cases)}건 → {OUT}")


if __name__ == "__main__":
    main()
