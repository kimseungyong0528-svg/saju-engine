"""평생사주 리포트: 사주 계산 결과 → 목차별 글 → PDF."""

from __future__ import annotations

from pathlib import Path

from .facts import OrderInfo, build_facts
from .outline import build_outline
from .render import render_html, render_pdf
from .writer import ClaudeWriter, DraftWriter


def make_lifetime_report(result: dict, order: OrderInfo, out_pdf: str | Path, writer=None,
                         html_out: str | Path | None = None) -> dict:
    """analyze_person() 결과로 평생사주 PDF를 만든다. 쪽수와 사용한 글을 돌려준다."""
    facts = build_facts(result, order)
    sections = build_outline(facts)
    texts = (writer or DraftWriter()).write(facts, sections)
    html = render_html(facts, sections, texts)
    if html_out:
        Path(html_out).write_text(html, encoding="utf-8")
    pages = render_pdf(html, out_pdf)
    return {"pages": pages, "texts": texts, "facts": facts}


def make_romance_report(result: dict, order: OrderInfo, out_pdf: str | Path, writer=None,
                        html_out: str | Path | None = None) -> dict:
    """analyze_person() 결과로 연애사주 PDF(약 50쪽)를 만든다. 평생사주와 같은 엔진·도안·글쓰기 방식을 쓴다."""
    from . import romance as R
    from .outline import STATIC
    facts = build_facts(result, order)
    facts["romance"] = R.build_romance(facts, result, order)
    sections = R.build_outline(facts)
    writer = writer or DraftWriter()
    if isinstance(writer, ClaudeWriter):
        writer.style, writer.final_section = R.ROMANCE_STYLE, R.FINAL_SECTION
    texts = writer.write(facts, sections)
    html = render_html(facts, sections, texts, product="romance", static={**STATIC, **R.STATIC},
                       first=R.cross_sell_order(facts["romance"]["status"]))
    if html_out:
        Path(html_out).write_text(html, encoding="utf-8")
    pages = render_pdf(html, out_pdf)
    return {"pages": pages, "texts": texts, "facts": facts}


THEME_PRODUCTS = ("reunion", "intimate", "wealth", "career", "business", "health")
PAIR_PRODUCTS = ("reunion", "intimate")


def prepare_product(product: str, result: dict, order: OrderInfo, answers: dict | None = None,
                    partner: dict | None = None) -> tuple:
    """주제 사주의 재료(facts)와 목차(sections)를 만든다. 두 사람 상품은 partner(상대방 analyze_person 결과)가 필요하다."""
    import importlib
    if product not in THEME_PRODUCTS:
        raise ValueError(f"알 수 없는 상품: {product}")
    if product in PAIR_PRODUCTS and partner is None:
        raise ValueError(f"{product}는 상대방 정보가 필요해요")
    M = importlib.import_module(f".{product}", __name__)
    facts = build_facts(result, order)
    if partner is not None:
        facts["partner"] = build_facts(partner, order)
    facts["theme"] = M.build(facts, result, answers or {}, partner)
    return M, facts, M.build_outline(facts)


def make_product_report(product: str, result: dict, order: OrderInfo, out_pdf: str | Path, writer=None,
                        html_out: str | Path | None = None, answers: dict | None = None, partner: dict | None = None,
                        texts: dict | None = None) -> dict:
    """재회·깊은 궁합·재물·직업·사업·건강 PDF(50쪽 이상). 평생사주와 같은 엔진·도안·글쓰기 방식을 쓴다.
    texts를 주면 글을 새로 쓰지 않고 그 글로 만든다(미리 써 둔 글 확인용)."""
    from .outline import STATIC
    M, facts, sections = prepare_product(product, result, order, answers, partner)
    if texts is None:
        writer = writer or DraftWriter()
        if isinstance(writer, ClaudeWriter):
            writer.style, writer.final_section = M.STYLE, M.FINAL_SECTION
        texts = writer.write(facts, sections)
    html = render_html(facts, sections, texts, product=product, static={**STATIC, **M.STATIC},
                       first=M.cross_sell_order(facts))
    if html_out:
        Path(html_out).write_text(html, encoding="utf-8")
    pages = render_pdf(html, out_pdf)
    return {"pages": pages, "texts": texts, "facts": facts, "sections": sections}


__all__ = ["OrderInfo", "build_facts", "build_outline", "make_lifetime_report", "make_romance_report",
           "make_product_report", "prepare_product", "THEME_PRODUCTS", "ClaudeWriter", "DraftWriter"]
