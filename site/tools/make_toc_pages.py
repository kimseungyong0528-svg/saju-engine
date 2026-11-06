"""결제 전 화면 목차의 장마다 '이 장에 들어 있는 쪽' 줄(사장님 2026-11-06 저녁 5-2).

목차 설명이 네 문장을 돌려 쓰는 것처럼 보였다(손님 20명 점검). 그래서 실제 리포트 목차(각 상품 build_outline)의
쪽 제목을 장마다 모아 site/public/assets/free/toc-pages.json 으로 쓴다. 화면은 이 파일만 읽는다(제1조항: 리포트와 같은 말).
tests/test_toc_pages.py 가 파일과 리포트 목차가 같은지 확인한다.

예) python site/tools/make_toc_pages.py
"""

import json
from datetime import date
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "public" / "assets" / "free" / "toc-pages.json"
ME = {"name": "윤서진", "sex": "female", "birth": "1993-09-05", "calendar": "solar", "timeAccuracy": "exact",
      "time": "11:50", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
PARTNER = {"name": "정민호", "sex": "male", "birth": "1991-02-14", "calendar": "solar", "timeAccuracy": "exact",
           "time": "07:20", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
SKIP = {"cover", "toc"}


def pages(secs: list[dict]) -> dict:
    return {s["no"]: [p["title"] for p in s["pages"] if p["id"] not in SKIP] for s in secs if s["no"] != "더보기"}


def build() -> dict:
    from saju.chart import analyze_person
    from saju.report import OrderInfo, build_facts, build_outline, prepare_product
    from saju.report import romance as R
    me = analyze_person(ME, current_year=2026)
    partner = analyze_person(PARTNER, current_year=2026)
    when = date(2026, 11, 6)
    out = {"lifetime": pages(build_outline(build_facts(me, OrderInfo(when, "", "직장"))))}
    ro = OrderInfo(when, "", "", "지금은 솔로예요", "1~2번")
    f = build_facts(me, ro)
    f["romance"] = R.build_romance(f, me, ro)
    out["romance"] = pages(R.build_outline(f))
    for pid in ("newyear", "wealth", "career", "business", "health", "intimate", "reunion"):
        _, _, secs = prepare_product(pid, me, OrderInfo(when), {}, partner if pid in ("intimate", "reunion") else None)
        out[pid] = pages(secs)
    _, _, secs = prepare_product("reunion", me, OrderInfo(when, partner_unknown=True, partner_name="그 사람"), {}, None)
    out["reunion-solo"] = pages(secs)
    return out


def main() -> None:
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("→", OUT)


if __name__ == "__main__":
    main()
