"""명령줄에서 사주를 계산해 보기.

예) python -m saju --name 홍길동 --sex male --birth 1990-05-15 --time 10:30 --region 1100000000
"""

import argparse
import json

from .chart import analyze_person
from .pillars import PillarOptions


def main() -> None:
    ap = argparse.ArgumentParser(description="사주 명식 계산")
    ap.add_argument("--name", default="")
    ap.add_argument("--sex", choices=["male", "female"], required=True)
    ap.add_argument("--birth", required=True, help="YYYY-MM-DD")
    ap.add_argument("--calendar", choices=["solar", "lunar", "unknown"], default="solar")
    ap.add_argument("--leap", action="store_true", help="음력 윤달")
    ap.add_argument("--time", help="HH:MM (생략하면 시간 미상)")
    ap.add_argument("--region", help="시·도 코드 (예: 1100000000 서울). 생략하면 지역 미상")
    ap.add_argument("--solar-time", choices=["mean", "apparent", "none"], default="mean")
    ap.add_argument("--zi-rule", choices=["23", "midnight"], default="23")
    ap.add_argument("--json", action="store_true", help="전체 결과를 JSON으로 출력")
    a = ap.parse_args()

    person = {
        "name": a.name, "sex": a.sex, "birth": a.birth, "calendar": a.calendar,
        "leap": a.leap if a.calendar == "lunar" else None,
        "timeAccuracy": "exact" if a.time else "unknown", "time": a.time,
        "birthPlace": {"status": "known", "regionChoice": a.region} if a.region else {"status": "unknown"},
    }
    r = analyze_person(person, PillarOptions(a.solar_time, a.zi_rule))
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    print(f"{r['person']['name'] or '이름 없음'} · {r['input']['place']} · 명식 후보 {r['variant_count']}개")
    for w in r["warnings"] + [u["message"] for u in r["uncertainties"]]:
        print("  ※", w)
    for v in r["variants"]:
        an = v["analysis"]
        print(f"\n[{v['key']}]  {v['civil_from']} ~ {v['civil_to']}")
        print("  일간:", an["day_master"]["stem"], an["day_master"]["element"], "· 띠:", an["zodiac"])
        print("  오행 세력:", an["elements"]["strength"])
        print("  십신 분포:", an["ten_god_groups"])
        print("  신강약:", an["strength"]["label"], an["strength"]["score"], "· 격국:", an["gyeokguk"]["name"])
        print("  신살:", ", ".join(f"{s['name']}({s['pillar']})" for s in an["shinsal"]) or "없음")
        dw = an["daewoon"]
        print(f"  대운({dw['direction']}, 대운수 {dw['start']['number']}):",
              " ".join(f"{p['age_from']}{p['ganzhi']}" for p in dw["periods"]))


if __name__ == "__main__":
    main()
