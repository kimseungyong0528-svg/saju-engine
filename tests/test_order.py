"""사이트 주문 → PDF 연결 시험(API 없이 초안 글로)."""

from datetime import datetime

import pytest

from saju.order import KST, blocking, make_pdf, order_info

PLACE = {"status": "known", "countryCode": "KR", "countryName": "대한민국", "regionChoice": "1100000000",
         "regionCode": "1100000000", "districtCode": "1111000000", "city": "종로구", "inputMode": "list", "referenceEra": "unknown"}
SELF = {"name": "김테스트", "sex": "female", "birth": "1995-03-12", "calendar": "solar", "timeAccuracy": "exact",
        "time": "06:30", "birthPlace": PLACE}
PARTNER = {"name": "이상대", "sex": "male", "birth": "1993-11-02", "calendar": "solar", "timeAccuracy": "unknown",
           "birthPlace": {"status": "unknown", "countryCode": "KR", "countryName": "대한민국", "referenceEra": "unknown"}}
WHEN = datetime(2026, 10, 12, 20, 0, tzinfo=KST)


def test_lifetime_answers_go_to_order_info():
    o, answers = order_info("lifetime", {"answers": {"occupation": "직장에 다니고 있어요", "relationship": "연애하고 있어요"}, "question": "일은?"}, WHEN)
    assert (o.daily, o.relationship, o.question, o.order_date.isoformat()) == ("직장에 다니고 있어요", "연애하고 있어요", "일은?", "2026-10-12")
    assert answers == {}


def test_romance_answers_go_to_order_info():
    o, _ = order_info("romance", {"answers": {"status": "썸을 타고 있어요", "experience": "1~2번"}}, WHEN)
    assert (o.relationship, o.experience) == ("썸을 타고 있어요", "1~2번")


def test_theme_answers_pass_through():
    o, answers = order_info("reunion", {"answers": {"breakup": "3개월 이내예요"}, "question": "다시?"}, WHEN)
    assert answers == {"breakup": "3개월 이내예요"} and o.question == "다시?"


def test_blocking_only_fact_errors():
    issues = [{"kind": "반복"}, {"kind": "분량"}, {"kind": "문장"}, {"kind": "점수"}]
    assert blocking(issues) == [{"kind": "점수"}]


def test_shown_year_missing_blocks_sending():
    """손님이 결제 전 화면에서 본 해·달이 리포트에 빠지면 보내지 않고 다시 쓴다(제1조항, P-29)."""
    assert blocking([{"kind": "화면 연도"}, {"kind": "반복"}]) == [{"kind": "화면 연도"}]


@pytest.mark.parametrize("product,answers,partner", [
    ("lifetime", {"occupation": "직장에 다니고 있어요"}, None),
    ("reunion", {"breakup": "3개월 이내예요"}, PARTNER),
    ("newyear", {"focus": "연애와 결혼", "question": "내년에 결혼할 수 있을까요?"}, None),
])
def test_make_pdf_from_site_payload(tmp_path, product, answers, partner):
    job = {"orderId": "x", "productId": product, "paidAt": "2026-10-12T11:00:00.000Z",
           "payload": {"productId": product, "self": SELF, "partner": partner or {}, "answers": answers, "question": ""}}
    out = tmp_path / "r.pdf"
    r = make_pdf(job, out)
    assert out.read_bytes()[:4] == b"%PDF" and r["pages"] >= 30
    # 무료 맛보기에서 고객이 본 6개가 리포트 글쓰기 재료에 들어간다(8종 모두)
    from saju.report.writer import facts_digest
    seen = facts_digest(r["facts"])["무료 맛보기에서 고객이 본 내용"]
    assert len(seen["좋은 운"]) == 3 and len(seen["조심할 운"]) == 3
    # '이 상품을 산 이유'는 이 상품이 맛보기 6개(8개 운 중 위 3·아래 3)에 들었거나 평생사주일 때만 있다
    from saju import taster
    from saju.chart import analyze_person
    view = taster.reading_for_person(analyze_person(SELF, current_year=2026))
    shown = {a["id"] for a in view["good"] + view["bad"]}
    assert ("이 상품을 산 이유" in seen) == (product == "lifetime" or product in shown)


def test_hedge_words_flagged():
    from saju.report import verify
    assert verify.HEDGE.search("이 점수는 참고용이에요.")
    assert verify.HEDGE.search("띠는 재미로 보세요.")
    assert not verify.HEDGE.search("이 표를 참고해 계획을 세워 보세요.")
