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


__all__ = ["OrderInfo", "build_facts", "build_outline", "make_lifetime_report", "make_romance_report",
           "ClaudeWriter", "DraftWriter"]
