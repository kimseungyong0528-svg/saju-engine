"""평생사주 리포트: 재료, 목차, 글 형식, PDF 쪽수."""

from datetime import date
from types import SimpleNamespace

import pytest

from saju.chart import analyze_person
from saju.report import OrderInfo, build_facts, build_outline, DraftWriter, ClaudeWriter
from saju.report.outline import all_pages, slots_by_section
from saju.report.render import render_html

SAMPLE = {"name": "홍길동", "sex": "male", "birth": "1990-05-15", "calendar": "solar", "timeAccuracy": "exact",
          "time": "10:30", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
ORDER = OrderInfo(date(2026, 10, 11), "올해 이직해도 될까요?", "직장")


@pytest.fixture(scope="module")
def facts():
    return build_facts(analyze_person(SAMPLE, current_year=2026), ORDER)


def test_facts_sample(facts):
    assert facts["person"]["age"] == 36
    assert [p["ganzhi"] for p in facts["pillars"]] == ["경오", "신사", "경진", "신사"]
    assert facts["lucky"]["element"] == "수"
    d = facts["daewoon"]
    assert d["periods"][d["current_index"]]["ganzhi"] == "갑신"
    assert [s["year"] for s in facts["sewoon"]] == list(range(2026, 2032))
    # 주문일(10/11)은 한로(10/8) 뒤라서 술월부터 12개월
    assert facts["months"][0]["ganzhi"] == "무술" and len(facts["months"]) == 12
    assert all(20 <= p["score"] <= 90 for p in d["periods"])


def test_outline_has_15_sections_and_plan_pages(facts):
    secs = build_outline(facts)
    assert [s["no"] for s in secs] == [str(i) for i in range(1, 16)] + ["더보기"]
    planned = sum(p["span"] for p in all_pages(secs))
    assert 104 <= planned <= 120
    ids = [p["id"] for p in all_pages(secs)]
    assert len(ids) == len(set(ids))


def test_draft_writer_fills_every_slot(facts):
    secs = build_outline(facts)
    texts = DraftWriter().write(facts, secs)
    for sl in slots_by_section(secs).values():
        for s in sl:
            assert s["id"] in texts
    html = render_html(facts, secs, texts)
    assert "홍길동 님" in html and "庚辰" in html


def test_claude_writer_request_shape(facts, monkeypatch):
    """API 키 없이 요청 모양만 확인한다: 장마다 한 번, 구조화 출력, 계산 결과는 캐시, 15장만 좋은 모델."""
    import json
    from saju.report.writer import FORMAT_SCHEMA, strict_schema
    calls = []

    def _fmt(schema):
        return next(k for k, v in FORMAT_SCHEMA.items() if strict_schema(v) == schema)

    class FakeStream:
        def __init__(self, kw):
            self.kw = kw

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get_final_message(self):
            props = self.kw["output_config"]["format"]["schema"]["properties"]
            data = {k: DraftWriter()._one(facts, {"id": k, "format": _fmt(v), "chars": 300}) for k, v in props.items()}
            usage = SimpleNamespace(input_tokens=10, output_tokens=20, cache_read_input_tokens=5, cache_creation_input_tokens=0)
            return SimpleNamespace(stop_reason="end_turn", usage=usage,
                                   content=[SimpleNamespace(type="text", text=json.dumps(data, ensure_ascii=False))])

    class FakeMessages:
        def stream(self, **kw):
            calls.append(kw)
            return FakeStream(kw)

    w = ClaudeWriter.__new__(ClaudeWriter)
    w.client, w.model, w.final_model, w.effort, w.max_workers, w.usage = (
        SimpleNamespace(messages=FakeMessages()), "cheap-model", "best-model", "medium", 2, [])
    secs = build_outline(facts)
    texts = w.write(facts, secs)
    # 초안 글은 검사에 걸릴 수 있어(긴 문장 등) 다시 쓰기 요청이 섞인다. 처음 쓰기는 장마다 한 번
    fixes = [c for c in calls if "[고쳐 쓰기]" in c["messages"][0]["content"]]
    assert len(calls) - len(fixes) == len(slots_by_section(secs))
    assert all("tool_choice" not in c and c["output_config"]["format"]["type"] == "json_schema" for c in calls)
    assert all(c["output_config"]["format"]["schema"]["additionalProperties"] is False for c in calls)
    assert all(c["system"][1].get("cache_control") for c in calls)
    assert set(texts) == {s["id"] for sl in slots_by_section(secs).values() for s in sl}
    # 마지막 장은 앞 장의 글을 받아 맨 나중에, 좋은 모델로 쓴다
    firsts = [c for c in calls if "[고쳐 쓰기]" not in c["messages"][0]["content"]]
    last = firsts[-1]
    assert "s15_qa" in last["output_config"]["format"]["schema"]["properties"]
    assert "앞 장에서 쓴 글" in last["messages"][0]["content"]
    assert last["model"] == "best-model" and all(c["model"] == "cheap-model" for c in calls if c is not last)
    assert len(w.usage) == len(calls)


def test_pdf_renders(tmp_path, facts):
    pytest.importorskip("weasyprint")
    from saju.report import make_lifetime_report
    out = make_lifetime_report(analyze_person(SAMPLE, current_year=2026), ORDER, tmp_path / "r.pdf")
    assert (tmp_path / "r.pdf").stat().st_size > 100_000
    assert 100 <= out["pages"] <= 120   # 화면 약속 "100장 이상"(P-PD-2)


def test_html_has_no_python_leaks(facts):
    texts = DraftWriter().write(facts, build_outline(facts))
    html = render_html(facts, build_outline(facts), texts)
    assert "built-in method" not in html and "object at 0x" not in html
    assert facts["lucky"]["items"] in html


def test_cross_sell_follows_site_order(facts):
    from saju.report.products import cross_sell
    items = cross_sell(facts, site="https://unmyeong.test")
    assert [p["id"] for p in items] == ["newyear", "romance", "intimate", "reunion", "wealth", "career", "business", "health"]
    assert items[1]["url"] == "https://unmyeong.test/#/f/romance/intro"
    assert all(p["hook"] for p in items)
    assert items[1]["price_text"] == "29,800원"
    # 판 적 없는 정가·할인율은 리포트에 보이지 않는다(표시광고법, P-12·P-16, 11-05)
    from pathlib import Path
    tpl = (Path(__file__).resolve().parents[1] / "saju/report/templates/report.html.j2").read_text(encoding="utf-8")
    assert "original_text" not in tpl and "p.discount" not in tpl
    assert "재성이 없어서" in next(p for p in items if p["id"] == "wealth")["hook"]
    # 재구매 할인 링크: 리포트 끝 링크로 들어가야만 10% 할인되므로 모든 상품 링크에 코드가 붙는다.
    coupon = cross_sell(facts, site="https://unmyeong.test", coupon="UNM-ABC234")
    assert coupon[1]["url"] == "https://unmyeong.test/?coupon=UNM-ABC234#/f/romance/intro"
    assert coupon[1]["rebuy_text"] == "26,820원"   # 서버 재구매 10%와 같은 금액
    assert cross_sell(facts, current="wealth", coupon="UNM-ABC234")[-1]["rebuy_text"] == "44,820원"
    assert all(p["rebuy_text"] is None for p in cross_sell(facts, site="https://unmyeong.test"))


def test_classics_page_and_luck_effect(facts):
    c = facts["classics"]
    assert c["verdict"] in ("성격", "성중유패", "파격", "상신 대기")
    assert facts["lucky"]["element"] == c["yongsin"]["element"]
    assert all(s["gyeok_effect"] in ("도움", "방해", "보통") for s in facts["sewoon"])
    ids = [p["id"] for p in all_pages(build_outline(facts))]
    assert "classics" in ids
