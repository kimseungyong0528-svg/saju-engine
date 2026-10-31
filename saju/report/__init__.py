"""평생사주 리포트: 사주 계산 결과 → 목차별 글 → PDF."""

from __future__ import annotations

import re
from pathlib import Path

from . import unity
from .facts import OrderInfo, build_facts
from .outline import build_outline
from .render import render_html, render_pdf
from .writer import FINAL_SECTION, ClaudeWriter, DraftWriter


def check_texts(facts: dict, sections: list[dict], texts: dict, final_section: str) -> list[dict]:
    """PDF를 만들기 전에 늘 글을 검사한다(없는 신살, 틀린 개수, 계산에 없는 점수·연도, 지나친 반복).
    글 분량도 본다. ClaudeWriter는 쓰는 중에 걸린 칸을 이미 고쳤고, 여기서는 남은 문제를 돌려준다."""
    from . import verify as V
    from .outline import slots_by_section
    jobs = slots_by_section(sections)
    final_ids = {s["id"] for s in jobs.get(final_section, [])}
    return V.check(facts, texts, final_ids) + V.lengths(texts, [s for sl in jobs.values() for s in sl])


def make_lifetime_report(result: dict, order: OrderInfo, out_pdf: str | Path, writer=None,
                         html_out: str | Path | None = None, taster: dict | None = None, taster_view: dict | None = None,
                        rebuy: dict | None = None, owned=(), bundled: bool = False) -> dict:
    """analyze_person() 결과로 평생사주 PDF를 만든다. 쪽수와 사용한 글을 돌려준다."""
    facts = build_facts(result, order)
    _merge_boundary(facts)   # 경계 안내는 결제 전 화면처럼 한 줄(손님 테스트 3차)
    from .theme import reveal_fix
    for rows in (facts["sewoon"], facts["sewoon_all"]):   # 제1조항: 결제 전 화면의 12년 지도와 같은 표시·방향
        reveal_fix(result, "lifetime", rows, score="score", signs="r_signs")
    unity.require("lifetime", result, facts)
    if taster:
        facts["taster"] = taster   # 무료 맛보기에서 고객이 본 6개(saju/taster.py). 리포트에서 더 자세히 푼다.
    if taster_view:
        facts["taster_view"] = taster_view   # 책 맨 끝 '무료 분석 다시 보기' 쪽에 그대로 싣는다.
    if rebuy:
        facts["rebuy"] = rebuy   # 그 쪽의 재구매 10% 할인 코드(주문 서버가 만든 것)
    facts["owned"], facts["bundled"] = list(owned), bundled   # 같은 주문에서 함께 산 상품(다시 권하지 않는다)
    sections = build_outline(facts)
    texts = (writer or DraftWriter()).write(facts, sections)
    issues = check_texts(facts, sections, texts, FINAL_SECTION)
    html = render_html(facts, sections, texts)
    if html_out:
        Path(html_out).write_text(html, encoding="utf-8")
    pages = render_pdf(html, out_pdf)
    return {"pages": pages, "texts": texts, "facts": facts, "issues": issues}


def make_romance_report(result: dict, order: OrderInfo, out_pdf: str | Path, writer=None,
                        html_out: str | Path | None = None, taster: dict | None = None, taster_view: dict | None = None,
                        rebuy: dict | None = None, owned=(), bundled: bool = False) -> dict:
    """analyze_person() 결과로 연애사주 PDF(약 50쪽)를 만든다. 평생사주와 같은 엔진·도안·글쓰기 방식을 쓴다."""
    from . import romance as R
    from .outline import STATIC
    facts = build_facts(result, order)
    _merge_boundary(facts)   # 경계 안내는 결제 전 화면처럼 한 줄(손님 테스트 3차: 5쪽에 13분·14분·15분 세 줄)
    facts["romance"] = R.build_romance(facts, result, order)
    unity.require("romance", result, facts)
    if taster:
        facts["taster"] = taster
    if taster_view:
        facts["taster_view"] = taster_view
    if rebuy:
        facts["rebuy"] = rebuy
    facts["owned"], facts["bundled"] = list(owned), bundled
    sections = R.build_outline(facts)
    writer = writer or DraftWriter()
    if isinstance(writer, ClaudeWriter):
        writer.style, writer.final_section = R.ROMANCE_STYLE, R.FINAL_SECTION
    texts = writer.write(facts, sections)
    issues = check_texts(facts, sections, texts, R.FINAL_SECTION)
    html = render_html(facts, sections, texts, product="romance", static={**STATIC, **R.STATIC},
                       first=R.cross_sell_order(facts["romance"]["status"]))
    if html_out:
        Path(html_out).write_text(html, encoding="utf-8")
    pages = render_pdf(html, out_pdf)
    return {"pages": pages, "texts": texts, "facts": facts, "issues": issues}


THEME_PRODUCTS = ("reunion", "intimate", "wealth", "career", "business", "health", "newyear")
PAIR_PRODUCTS = ("reunion", "intimate")


_BOUNDARY = re.compile(r"출생 시각 (\d+)분 (이후|이전)에 (\S+)가 바뀌는 경계예요\.")


def _merge_boundary(facts: dict) -> None:
    """주제 사주: '출생 시각 N분 이후에 시주가 바뀌는 경계예요'가 분마다 여러 줄 나오면 방향·기둥별로 가장 가까운 한 줄만 남긴다."""
    near, rest = {}, []
    for u in facts.get("uncertainties", []):
        m = _BOUNDARY.fullmatch(u)
        if not m:
            rest.append(u)
            continue
        key = (m[2], m[3])
        near[key] = min(near.get(key, 99), int(m[1]))
    # 같은 분, 같은 방향이면 한 줄로 묶는다('일주와 시주가', 손님 테스트 3차: 거의 같은 말 두 줄). 사이트 reveal.mjs boundaryLines 와 같다.
    groups: dict[tuple[str, int], list[str]] = {}
    for (d, pillar), n in sorted(near.items()):
        groups.setdefault((d, n), []).append(pillar)
    lines = [f"태어난 시각이 {n}분만 {'늦었다면' if d == '이후' else '빨랐다면'} {'와 '.join(ps)}가 달라지는 경계예요. 시각이 정확한지 한 번 더 확인해 주세요."
             for (d, n), ps in groups.items()]
    facts["uncertainties"] = lines + rest


def prepare_product(product: str, result: dict, order: OrderInfo, answers: dict | None = None,
                    partner: dict | None = None, bundled: bool = False) -> tuple:
    """주제 사주의 재료(facts)와 목차(sections)를 만든다. 두 사람 상품은 partner(상대방 analyze_person 결과)가 필요하다."""
    import importlib
    if product not in THEME_PRODUCTS:
        raise ValueError(f"알 수 없는 상품: {product}")
    if product in PAIR_PRODUCTS and partner is None:
        raise ValueError(f"{product}는 상대방 정보가 필요해요")
    M = importlib.import_module(f".{product}", __name__)
    facts = build_facts(result, order)
    _merge_boundary(facts)
    if partner is not None:
        facts["partner"] = build_facts(partner, order)
        _merge_boundary(facts["partner"])
    facts["theme"] = M.build(facts, result, answers or {}, partner)
    unity.require(product, result, facts, partner)   # 제1조항: 화면과 다르면 여기서 멈춘다
    facts["theme"]["data"]["seen"] = not bundled   # 묶음으로 산 상품은 결제 전 이야기 화면을 보지 않았다
    return M, facts, M.build_outline(facts)


def make_product_report(product: str, result: dict, order: OrderInfo, out_pdf: str | Path, writer=None,
                        html_out: str | Path | None = None, answers: dict | None = None, partner: dict | None = None,
                        texts: dict | None = None, taster: dict | None = None, taster_view: dict | None = None,
                        rebuy: dict | None = None, owned=(), bundled: bool = False) -> dict:
    """재회·깊은 궁합·재물·직업·사업·건강·2027 신년운세 PDF(50쪽 이상). 평생사주와 같은 엔진·도안·글쓰기 방식을 쓴다.
    texts를 주면 글을 새로 쓰지 않고 그 글로 만든다(미리 써 둔 글 확인용)."""
    from .outline import STATIC
    M, facts, sections = prepare_product(product, result, order, answers, partner, bundled)
    facts["answers"] = dict(answers or {})   # 손님이 고른 답 그대로(보너스 쪽 '지금 상황' 한 줄에 쓴다)
    if taster:
        facts["taster"] = taster   # 고객이 무료 맛보기에서 본 내용(saju/taster.py). 리포트가 이와 어긋나지 않게 쓴다.
    if taster_view:
        facts["taster_view"] = taster_view   # 책 맨 끝 '무료 분석 다시 보기' 쪽에 그대로 싣는다.
    if rebuy:
        facts["rebuy"] = rebuy   # 그 쪽의 재구매 10% 할인 코드(주문 서버가 만든 것)
    facts["owned"], facts["bundled"] = list(owned), bundled   # 같은 주문에서 함께 산 상품(다시 권하지 않는다)
    if texts is None:
        writer = writer or DraftWriter()
        if isinstance(writer, ClaudeWriter):
            writer.style, writer.final_section = M.STYLE, M.FINAL_SECTION
        texts = writer.write(facts, sections)
    issues = check_texts(facts, sections, texts, M.FINAL_SECTION)
    html = render_html(facts, sections, texts, product=product, static={**STATIC, **M.STATIC},
                       first=M.cross_sell_order(facts))
    if html_out:
        Path(html_out).write_text(html, encoding="utf-8")
    pages = render_pdf(html, out_pdf)
    return {"pages": pages, "texts": texts, "facts": facts, "sections": sections, "issues": issues}


__all__ = ["OrderInfo", "build_facts", "build_outline", "make_lifetime_report", "make_romance_report",
           "make_product_report", "prepare_product", "check_texts", "THEME_PRODUCTS", "ClaudeWriter", "DraftWriter"]
