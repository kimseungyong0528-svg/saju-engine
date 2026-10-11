"""평생사주 PDF 만들기.

예) python -m saju.report --name 홍길동 --sex male --birth 1990-05-15 --time 10:30 --region 1100000000 --out report.pdf
    ANTHROPIC_API_KEY가 있으면 Claude가 본문을 쓰고, 없거나 --draft면 초안 글로 만든다.
"""

import argparse
import json
import os
from datetime import date

from ..chart import analyze_person
from . import OrderInfo, make_lifetime_report, make_romance_report, make_product_report, THEME_PRODUCTS, ClaudeWriter, DraftWriter


def main() -> None:
    ap = argparse.ArgumentParser(description="운명서재 사주 PDF 만들기")
    ap.add_argument("--product", choices=["lifetime", "romance", *THEME_PRODUCTS], default="lifetime")
    ap.add_argument("--name", default="")
    ap.add_argument("--sex", choices=["male", "female"], required=True)
    ap.add_argument("--birth", required=True)
    ap.add_argument("--calendar", choices=["solar", "lunar", "unknown"], default="solar")
    ap.add_argument("--leap", action="store_true")
    ap.add_argument("--time")
    ap.add_argument("--region")
    ap.add_argument("--question", default="")
    ap.add_argument("--daily", default="")
    ap.add_argument("--relationship", default="", help="연애·결혼 상태(솔로/연애 중/결혼/이혼·사별). 연애사주는 사이트 선택지 그대로")
    ap.add_argument("--experience", default="", help="연애사주: 연애 경험 횟수(사이트 선택지 그대로)")
    ap.add_argument("--answer", action="append", default=[], metavar="키=값",
                    help="상품별 사이트 선택지(예: breakup=3~6개월 정도예요, status=연애 중이에요, concern=이직을 고민해요)")
    ap.add_argument("--partner-name", default="")
    ap.add_argument("--partner-sex", choices=["male", "female"])
    ap.add_argument("--partner-birth")
    ap.add_argument("--partner-calendar", choices=["solar", "lunar", "unknown"], default="solar")
    ap.add_argument("--partner-time")
    ap.add_argument("--partner-region")
    ap.add_argument("--use-texts", help="미리 써 둔 글(JSON)로 만들기")
    ap.add_argument("--order-date", default=date.today().isoformat())
    ap.add_argument("--out", required=True)
    ap.add_argument("--html", help="중간 HTML도 저장")
    ap.add_argument("--texts", help="쓴 글을 JSON으로 저장")
    ap.add_argument("--draft", action="store_true", help="AI 없이 초안 글로 만들기")
    a = ap.parse_args()

    od = date.fromisoformat(a.order_date)
    person = {
        "name": a.name, "sex": a.sex, "birth": a.birth, "calendar": a.calendar,
        "leap": a.leap if a.calendar == "lunar" else None,
        "timeAccuracy": "exact" if a.time else "unknown", "time": a.time,
        "birthPlace": {"status": "known", "regionChoice": a.region} if a.region else {"status": "unknown"},
    }
    result = analyze_person(person, current_year=od.year)
    writer = DraftWriter() if a.draft or not os.environ.get("ANTHROPIC_API_KEY") else ClaudeWriter()
    order = OrderInfo(od, a.question, a.daily, a.relationship, a.experience)
    if a.product in THEME_PRODUCTS:
        partner = None
        if a.partner_birth:
            partner = analyze_person({
                "name": a.partner_name, "sex": a.partner_sex, "birth": a.partner_birth, "calendar": a.partner_calendar,
                "timeAccuracy": "exact" if a.partner_time else "unknown", "time": a.partner_time,
                "birthPlace": {"status": "known", "regionChoice": a.partner_region} if a.partner_region else {"status": "unknown"},
            }, current_year=od.year)
        answers = dict(x.split("=", 1) for x in a.answer)
        texts = json.load(open(a.use_texts, encoding="utf-8")) if a.use_texts else None
        r = make_product_report(a.product, result, order, a.out, writer, a.html, answers, partner, texts)
        if texts is not None:
            writer = "미리 쓴 글"
    else:
        make = make_romance_report if a.product == "romance" else make_lifetime_report
        r = make(result, order, a.out, writer, a.html)
    if a.texts:
        with open(a.texts, "w", encoding="utf-8") as fp:
            json.dump(r["texts"], fp, ensure_ascii=False, indent=2)
    print(f"{a.out}: {r['pages']}쪽 ({writer if isinstance(writer, str) else type(writer).__name__})")


if __name__ == "__main__":
    main()
