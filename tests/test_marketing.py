from saju.marketing.__main__ import schedule
from saju.marketing.checks import check_post, x_weight
from saju.marketing.content import (caption_facebook, caption_instagram, ddi_facts, ddi_posts, text_shorts,
                                    text_threads, text_x)


def _texts(p):
    return {"인스타": caption_instagram(p), "페북": caption_facebook(p), "스레드": text_threads(p),
            "X": text_x(p), "쇼츠": text_shorts(p)}


def test_ddi_facts_match_engine():
    assert ddi_facts("말")["relations"] == ["육합"]
    assert set(ddi_facts("소")["relations"]) == {"충", "형"}
    assert ddi_facts("토끼")["samjae"] == "날삼재"
    assert ddi_facts("호랑이")["relations"] == [] and ddi_facts("호랑이")["samjae"] == ""
    assert ddi_facts("쥐")["years"][-1] == 2008


def test_all_posts_pass_checks():
    for pair in schedule():
        for p in pair:
            if p is not None:
                assert check_post(p, _texts(p)) == [], p.key


def test_check_catches_wrong_basis_and_hype():
    p = ddi_posts()[0]                     # 말띠
    p.slides[0]["body"] = p.slides[0]["body"].replace("'육합'", "'충'")
    issues = check_post(p, _texts(p))
    assert any("엔진 계산과 다릅니다" in i for i in issues)
    p.sub = "돈벼락 맞는 해예요"
    assert any("과장" in i for i in check_post(p, _texts(p)))


def test_x_weight_counts_hangul_double_and_links():
    assert x_weight("가나") == 4
    assert x_weight("ab https://unmyeong-saju.com") == 2 + 1 + 23


def test_schedule_two_posts_a_day():
    plan = schedule()
    assert len(plan) == 14
    assert sum(p is not None for pair in plan for p in pair) == 27
