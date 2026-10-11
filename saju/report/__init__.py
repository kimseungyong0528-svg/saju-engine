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


__all__ = ["OrderInfo", "build_facts", "build_outline", "make_lifetime_report", "ClaudeWriter", "DraftWriter"]
