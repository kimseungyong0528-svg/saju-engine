"""2027 신년운세: 목차, 2027년 12달, 삼재·대운 계산, 사이트 답(focus·question), 글 검사, PDF 쪽수(API 없이)."""

from datetime import date, datetime

import pytest

from saju.chart import analyze_person
from saju.order import KST, order_info
from saju.report import OrderInfo, DraftWriter, make_product_report, prepare_product, verify
from saju.report import newyear as NY
from saju.report.outline import all_pages, slots_by_section
from saju.report.products import cross_sell

# 을해년(돼지띠, 해묘미 무리) 생 → 2027 미년은 날삼재, 2027-09에 새 대운이 시작한다
PIG = {"name": "한서연", "sex": "female", "birth": "1995-09-02", "calendar": "solar", "timeAccuracy": "exact",
       "time": "08:10", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
# 계유년(닭띠, 사유축 무리) 생 → 2027년은 삼재가 아니다
ROOSTER = {"name": "윤서진", "sex": "female", "birth": "1993-09-05", "calendar": "solar", "timeAccuracy": "exact",
           "time": "11:50", "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
OD = date(2026, 10, 13)

TOC = [
    ("1", "내 사주 한눈에 보기", "나의 2027년 운명과 사주표"),
    ("2", "한눈에 보는 나의 2027년", "한마디 요약, 전체 점수, 좋은 운과 나쁜 운 정리"),
    ("3", "2027년 정미년과 내 사주", "새해 기운과의 궁합, 대운과 삼재 확인"),
    ("4", "일과 직장운", "평가와 승진, 이직과 새 일 시작하기 좋은 시기"),
    ("5", "재물운", "큰 돈이 들어오는 시기와 빠져 나가는 시기, 투자는 해야할까?"),
    ("6", "사업·부업운과 문서운", "새로운 일, 계약, 집과 부동산을 시작할 때"),
    ("7", "연애운과 결혼운", "새로운 사랑이 찾아오는 시기, 부부 관계"),
    ("8", "사람운과 조심할 일", "나를 도와줄 은인은 누구일까, 구설·손재·관재"),
    ("9", "건강운", "조심할 질병과 위험한 시기"),
    ("10", "이사·여행·시험운", "움직이기 좋은 시기, 공부와 자격증"),
    ("11", "1월~12월 월별 운세", "월별 해야할 일, 나에게 가장 좋은 달과 조심할 달"),
    ("12", "2027년 실천 계획과 마지막 조언", "행운의 색·방향·숫자, 꼭 해야 할 일과 피할 일, 놓치면 안되는 연초 계획"),
    ("더보기", "다른 사주도 궁금하다면", "운명서재의 다른 리포트"),
]


def _prep(person=PIG, answers=None, question=""):
    me = analyze_person(person, current_year=OD.year)
    return me, prepare_product("newyear", me, OrderInfo(OD, question), answers or {}, None)


def test_toc_is_owner_fixed():
    assert NY.SECTIONS == TOC
    _, (M, f, secs) = _prep()
    assert [(s["no"], s["title"], s["subtitle"]) for s in secs] == TOC
    assert M.FINAL_SECTION == "12" and NY.TARGET_YEAR == 2027


def test_months_are_calendar_2027_from_solar_terms():
    _, (_, f, _) = _prep()
    ms = f["theme"]["months"]
    assert [m["month"] for m in ms] == list(range(1, 13)) and all(m["year"] == 2027 for m in ms)
    assert ms[0]["term"] == "소한" and ms[0]["saju_month"] == "축월" and ms[0]["year_energy"].startswith("2026년 병오")
    assert ms[1]["term"] == "입춘" and ms[1]["label"] == "2월(인월, 2/4~)" and ms[1]["year_energy"] == "2027년 정미년"
    assert ms[11]["saju_month"] == "자월" and ms[11]["period"].endswith("2028/1/5")
    assert f["months"] is ms   # 글쓰기 재료와 검사도 2027년 12달을 본다
    y = f["theme"]["data"]["year"]
    assert y["ganzhi"] == "정미" and y["stem"]["element"] == "화" and y["branch"]["element"] == "토"


@pytest.mark.parametrize("branch,year,kind", [
    ("해", 2027, "날삼재"), ("묘", 2025, "들삼재"), ("미", 2026, "눌삼재"),
    ("인", 2028, "들삼재"), ("오", 2030, "날삼재"), ("유", 2031, "들삼재"), ("자", 2022, "들삼재"), ("진", 2024, "날삼재"),
    ("인", 2027, ""), ("유", 2027, ""), ("자", 2027, ""), ("축", 2027, ""),
])
def test_samjae_rule(branch, year, kind):
    s = NY.samjae(branch, year)
    assert s["kind"] == kind and s["is_samjae"] == bool(kind)


def test_samjae_2027_only_haemyomi():
    hit = {b for b in "자축인묘진사오미신유술해" if NY.samjae(b, 2027)["is_samjae"]}
    assert hit == {"해", "묘", "미"}


def test_samjae_and_daewoon_facts():
    _, (_, f, _) = _prep()
    t = f["theme"]["data"]
    assert f["person"]["zodiac"] == "돼지" and t["samjae"]["kind"] == "날삼재" and t["samjae"]["this_run"] == [2025, 2026, 2027]
    starts = [p["start_year"] for p in f["daewoon"]["periods"]]
    assert t["daewoon"]["changes_in_2027"] == (2027 in starts)
    _, (_, g, _) = _prep(ROOSTER)
    assert not g["theme"]["data"]["samjae"]["is_samjae"]


def test_focus_and_question_pages():
    _, (_, f, secs) = _prep(answers={"focus": "연애와 결혼", "question": "언제 좋은 사람을 만날까요?"})
    pages = {s["no"]: [p["id"] for p in s["pages"]] for s in secs}
    assert "ny7_focus" in pages["7"] and "ny12_q" in pages["12"]
    assert f["order"]["question"] == "언제 좋은 사람을 만날까요?"
    _, (_, g, secs2) = _prep()
    ids = [p["id"] for p in all_pages(secs2)]
    assert "ny12_q" not in ids and not any(i.endswith("_focus") for i in ids)
    assert len(secs2) == len(TOC)   # 질문 쪽은 목차 줄을 더하지 않는다


def test_order_info_takes_question_from_answers():
    when = datetime(2026, 12, 20, 10, 0, tzinfo=KST)
    o, answers = order_info("newyear", {"answers": {"focus": "건강", "question": "내년에 이사해도 될까요?"}}, when)
    assert o.question == "내년에 이사해도 될까요?" and answers["focus"] == "건강"


def test_verify_newyear_facts():
    _, (_, f, _) = _prep(ROOSTER)
    bad = verify.check(f, {"x": ["2027년은 삼재예요.", "이직하기 좋은 때예요."]})
    kinds = [i["kind"] for i in bad]
    assert "삼재" in kinds and "문장" in kinds
    ok = verify.check(f, {"x": ["2027년은 삼재가 아니에요."]})
    assert not [i for i in ok if i["kind"] == "삼재"]


def test_cross_sell_newyear_first_with_hook():
    _, (_, f, _) = _prep()
    items = cross_sell(f, current="wealth")
    assert items[0]["id"] == "newyear" and items[0]["price_text"] == "29,800원" and "날삼재" in items[0]["hook"]
    assert "newyear" not in [p["id"] for p in cross_sell(f, current="newyear")]


def test_draft_pdf_50_to_60_pages(tmp_path):
    me = analyze_person(PIG, current_year=OD.year)
    r = make_product_report("newyear", me, OrderInfo(OD, ""), tmp_path / "n.pdf", DraftWriter(), html_out=tmp_path / "n.html",
                            answers={"focus": "돈과 재물", "question": "부업을 시작해도 될까요?"})
    assert 50 <= r["pages"] <= 62
    body = (tmp_path / "n.html").read_text()
    assert "新<br>年<br>運<br>勢" in body and "2월(인월, 2/4~)" in body and "다른 사주도 궁금하다면" in body
    slots = slots_by_section(r["sections"])
    assert set(slots) == {str(i) for i in range(1, 13)}
