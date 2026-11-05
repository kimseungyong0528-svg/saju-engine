"""사이트 주문 → 사주 PDF.

사이트(넷리파이 주문 서버)에 저장된 주문을 받아 PDF를 만들고, 다시 주문 서버로 보낸다.
이메일은 주문 서버가 보낸다. 이 모듈은 깃허브 Actions에서 돌아간다(.github/workflows/order.yml).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import reveal, taster
from ..chart import analyze_person
from ..report import (OrderInfo, THEME_PRODUCTS, PAIR_PRODUCTS, make_lifetime_report, make_romance_report,
                      make_product_report)

KST = timezone(timedelta(hours=9))
PRODUCTS = ("lifetime", "romance", *THEME_PRODUCTS)

# 이 문제가 남으면 사람이 보기 전에는 보내지 않는다(사주 계산과 다른 내용).
# '화면 연도': 손님이 결제 전 화면에서 본 해·달이 리포트에 빠짐 = 제1조항(화면과 리포트 일치) 위반이라 보내지 않고 다시 쓴다(P-29).
BLOCKING_KINDS = {"없는 신살", "개수", "점수", "연도", "삼재", "대운", "화면 연도"}


def order_date(paid_at: str | None) -> datetime:
    if paid_at:
        return datetime.fromisoformat(paid_at.replace("Z", "+00:00")).astimezone(KST)
    return datetime.now(KST)


def order_info(product: str, payload: dict, when: datetime) -> tuple[OrderInfo, dict]:
    """사이트 답(질문 단계 id → 선택지)을 프로그램 칸으로 옮긴다. 주제 상품은 답을 그대로 넘긴다."""
    answers = dict(payload.get("answers") or {})
    reveal_start = str(answers.pop("revealStart", "") or "")[:7]   # 재회사주 화면의 첫 달(제1조항)
    gift = answers.pop("revealGift", "") == "1"   # 선물 주문(사이트 결제 전 화면에서 '선물'을 고름)
    # 선물 메시지(2026-11-05): 손님이 쓴 글이라 글쓰기 AI에는 넘기지 않는다(answers 에서 뺀다). PDF 표지 다음 쪽에만 싣는다.
    gift_message = clean_note(answers.pop("giftMessage", ""), 80) if gift else ""
    gift_from = clean_note(answers.pop("giftFrom", ""), 20, lines=1) if gift else ""
    answers.pop("giftMessage", None); answers.pop("giftFrom", None)
    question = str(payload.get("question") or "")[:1000]
    d = when.date()
    if product == "lifetime":
        return OrderInfo(d, question, daily=answers.get("occupation", ""), relationship=answers.get("relationship", ""), gift=gift, gift_message=gift_message, gift_from=gift_from), {}
    if product == "romance":
        return OrderInfo(d, question, relationship=answers.get("status", ""), experience=answers.get("experience", ""), gift=gift, gift_message=gift_message, gift_from=gift_from), {}
    if product == "newyear" and not question:   # 신년운세는 질문을 answers.question으로 받는다(선택)
        question = str(answers.get("question") or "")[:1000]
    pinfo = payload.get("partner") or {}
    solo = product == "reunion" and bool(pinfo.get("birthUnknown"))   # 상대 생일 없이 보는 재회사주(2026-11-05)
    return OrderInfo(d, question, reveal_start=reveal_start, gift=gift, gift_message=gift_message, gift_from=gift_from,
                     partner_unknown=solo, partner_name=clean_note(pinfo.get("name", ""), 30, lines=1) if solo else ""), answers


def clean_note(value, limit: int, lines: int = 3) -> str:
    """손님이 쓴 짧은 글: 제어 문자를 빼고, 줄은 lines 줄까지, 글자는 limit 자까지."""
    import re
    s = re.sub(r"[\x00-\x09\x0b-\x1f\x7f]", "", str(value or ""))
    rows = [re.sub(r"\s+", " ", r).strip() for r in s.split("\n")]
    return "\n".join([r for r in rows if r][:lines])[:limit]


def make_pdf(job: dict, out_pdf: str | Path, writer=None) -> dict:
    """주문 서버가 준 주문(job)으로 PDF를 만든다."""
    product, payload = job["productId"], job["payload"]
    if product not in PRODUCTS:
        raise ValueError(f"알 수 없는 상품: {product}")
    when = order_date(job.get("paidAt"))
    me = analyze_person(payload["self"], current_year=when.year)
    order, answers = order_info(product, payload, when)
    # 고객이 무료 맛보기에서 본 좋은 운·조심할 운(같은 사주 계산)을 글쓰기에 넘겨, 고객이 기대하는 내용을 더 깊게 풀게 한다.
    # 같은 6가지는 책 맨 끝 '무료 분석에서 본 나의 좋은 운과 조심할 운' 쪽에도 그대로 싣는다(2026-10-27 사장님).
    # 재구매 10% 할인 코드도 그 쪽에 크게 싣는다(주문 서버가 주문마다 만들어 job["rebuy"]로 준다).
    view = taster.reading_for_person(me)
    seen = taster.digest(view, product)
    # 결제 직전 이야기 화면에서 본 '내 점수'와 해·달 지도(같은 계산)도 넘겨, 리포트가 그 해·달의 몇 월·방법까지 풀게 한다(2026-10-28 사장님).
    # 묶음으로 함께 산 상품(job["parentId"])은 손님이 그 상품의 결제 전 이야기 화면을 보지 않았다: '화면에서 보신'이라고 쓰지 않는다.
    bundled = bool(job.get("parentId"))
    if bundled:
        seen["결제 전 이야기 화면"] = ("이 상품은 다른 상품과 함께 묶음으로 사서, 고객이 이 상품의 결제 전 이야기 화면을 보지 않았습니다. "
                                "'화면에서 보신', '결제 전에 보신' 같은 말을 쓰지 않습니다.")
    else:
        seen["결제 전 이야기 화면에서 본 내용"] = reveal.digest(taster.pillars_from_result(me), me["person"].get("name", ""),
                                                    me["person"].get("sex", ""), product, when.date().isoformat() if hasattr(when, "date") else when,
                                                    str((payload.get("answers") or {}).get("revealStart") or "")[:7])
    # 같은 주문에서 함께 산 상품은 책 끝에서 다시 권하지 않는다.
    extra = {"rebuy": job.get("rebuy"), "owned": [p for p in job.get("together") or [] if p != product], "bundled": bundled}
    if product == "lifetime":
        return make_lifetime_report(me, order, out_pdf, writer, taster=seen, taster_view=view, **extra)
    if product == "romance":
        return make_romance_report(me, order, out_pdf, writer, taster=seen, taster_view=view, **extra)
    partner = analyze_person(payload["partner"], current_year=when.year) if product in PAIR_PRODUCTS and not order.partner_unknown else None
    return make_product_report(product, me, order, out_pdf, writer, answers=answers, partner=partner, taster=seen, taster_view=view, **extra)


def blocking(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i.get("kind") in BLOCKING_KINDS]
