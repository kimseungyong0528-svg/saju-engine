"""선물 메시지 (2026-11-05): 손님이 쓴 말은 글쓰기 AI에 가지 않고, 선물 주문 PDF 표지 다음 쪽에만 실린다."""

from datetime import datetime
from pathlib import Path

from saju.order import KST, clean_note, order_info
from saju.report.facts import OrderInfo, gift_card

WHEN = datetime(2026, 11, 5, 12, tzinfo=KST)


def test_gift_message_is_kept_out_of_answers():
    o, ans = order_info("wealth", {"answers": {"revealGift": "1", "giftMessage": "엄마\n\n  사랑해요\x07", "giftFrom": "큰딸 지은",
                                                "occupation": "직장에 다니고 있어요"}}, WHEN)
    assert o.gift and o.gift_message == "엄마\n사랑해요" and o.gift_from == "큰딸 지은"
    assert "giftMessage" not in ans and "giftFrom" not in ans and ans["occupation"] == "직장에 다니고 있어요"


def test_message_without_gift_is_dropped():
    o, ans = order_info("career", {"answers": {"giftMessage": "안녕", "giftFrom": "나"}}, WHEN)
    assert not o.gift and o.gift_message == "" and "giftMessage" not in ans
    o, _ = order_info("lifetime", {"answers": {"revealGift": "1", "giftMessage": "건강하세요"}}, WHEN)
    assert o.gift_message == "건강하세요"


def test_clean_note_limits():
    assert clean_note("가" * 200, 80) == "가" * 80
    assert clean_note("a\nb\nc\nd", 80) == "a\nb\nc"
    assert clean_note("이름\n둘째 줄", 20, lines=1) == "이름"


def test_gift_card_only_for_gift_with_message():
    assert gift_card(OrderInfo(gift=True, gift_message="  ")) is None
    assert gift_card(OrderInfo(gift=False, gift_message="안녕")) is None
    assert gift_card(OrderInfo(gift=True, gift_message="안녕", gift_from="딸")) == {"message": "안녕", "sender": "딸"}


def test_template_prints_gift_page_after_cover():
    tpl = (Path(__file__).resolve().parents[1] / "saju" / "report" / "templates" / "report.html.j2").read_text(encoding="utf-8")
    cover_end = tpl.index("운명서재 · 금월선녀</div>\n</section>")
    assert tpl.index("{% if f.gift_card %}") > cover_end
    assert "{{ f.gift_card.message }}" in tpl
