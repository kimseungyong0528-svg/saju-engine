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


def test_hedge_words_flagged():
    from saju.report import verify
    assert verify.HEDGE.search("이 점수는 참고용이에요.")
    assert verify.HEDGE.search("띠는 재미로 보세요.")
    assert not verify.HEDGE.search("이 표를 참고해 계획을 세워 보세요.")
