"""사이트 주문 → 사주 PDF.

사이트(넷리파이 주문 서버)에 저장된 주문을 받아 PDF를 만들고, 다시 주문 서버로 보낸다.
이메일은 주문 서버가 보낸다. 이 모듈은 깃허브 Actions에서 돌아간다(.github/workflows/order.yml).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from .. import taster
from ..chart import analyze_person
from ..report import (OrderInfo, THEME_PRODUCTS, PAIR_PRODUCTS, make_lifetime_report, make_romance_report,
                      make_product_report)

KST = timezone(timedelta(hours=9))
PRODUCTS = ("lifetime", "romance", *THEME_PRODUCTS)

# 이 문제가 남으면 사람이 보기 전에는 보내지 않는다(사주 계산과 다른 내용).
BLOCKING_KINDS = {"없는 신살", "개수", "점수", "연도", "삼재", "대운"}


def order_date(paid_at: str | None) -> datetime:
    if paid_at:
        return datetime.fromisoformat(paid_at.replace("Z", "+00:00")).astimezone(KST)
    return datetime.now(KST)


def order_info(product: str, payload: dict, when: datetime) -> tuple[OrderInfo, dict]:
    """사이트 답(질문 단계 id → 선택지)을 프로그램 칸으로 옮긴다. 주제 상품은 답을 그대로 넘긴다."""
    answers = dict(payload.get("answers") or {})
    question = str(payload.get("question") or "")[:1000]
    d = when.date()
    if product == "lifetime":
        return OrderInfo(d, question, daily=answers.get("occupation", ""), relationship=answers.get("relationship", "")), {}
    if product == "romance":
        return OrderInfo(d, question, relationship=answers.get("status", ""), experience=answers.get("experience", "")), {}
    if product == "newyear" and not question:   # 신년운세는 질문을 answers.question으로 받는다(선택)
        question = str(answers.get("question") or "")[:1000]
    return OrderInfo(d, question), answers


def make_pdf(job: dict, out_pdf: str | Path, writer=None) -> dict:
    """주문 서버가 준 주문(job)으로 PDF를 만든다."""
    product, payload = job["productId"], job["payload"]
    if product not in PRODUCTS:
        raise ValueError(f"알 수 없는 상품: {product}")
    when = order_date(job.get("paidAt"))
    me = analyze_person(payload["self"], current_year=when.year)
    order, answers = order_info(product, payload, when)
    if product == "lifetime":
        return make_lifetime_report(me, order, out_pdf, writer)
    # 고객이 사이트 무료 맛보기에서 본 좋은 운·조심할 운과 리포트가 어긋나지 않게, 같은 결과를 글쓰기에 넘긴다.
    seen = taster.digest(taster.reading_for_person(me))
    if product == "romance":
        return make_romance_report(me, order, out_pdf, writer, taster=seen)
    partner = analyze_person(payload["partner"], current_year=when.year) if product in PAIR_PRODUCTS else None
    return make_product_report(product, me, order, out_pdf, writer, answers=answers, partner=partner, taster=seen)


def blocking(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i.get("kind") in BLOCKING_KINDS]
