"""SNS 게시물 공식 (사장님 2026-11-01 "전부 공식으로, 무한 발행"): 날짜만 넣으면 겹치지 않는 글이 엔진 계산대로 나온다."""

import datetime as dt
import itertools
import re

import pytest

from saju.marketing import rules
from saju.marketing.formula import text as T
from saju.marketing.ranking import rank

START = dt.date(2026, 11, 2)


@pytest.fixture(scope="module")
def plan90():
    return T.plan(START, 90)


def test_formats_rotate(plan90):
    fmts = [m.fmt for _, m, _ in plan90]
    assert all(a != b for a, b in itertools.pairwise(fmts))
    assert set(fmts) == {f["key"] for f in rules.slot("아침")["formats"]}
    styles = [e.style for _, _, e in plan90]
    assert {"jangin", "salgu", "dohwa"} <= set(styles)


def test_no_repeat_for_60_days(plan90):
    """두 달 동안 같은 재료를 다시 쓰지 않는다."""
    keys = [m.key for _, m, _ in plan90[:60]] + [e.key for _, _, e in plan90[:60]]
    assert len(keys) == len(set(keys))
    firsts = [e.parts[0] for _, _, e in plan90[:60]]
    assert len(firsts) == len(set(firsts))


def test_used_keys_are_skipped():
    day = START + dt.timedelta(days=1)   # 띠별 운세 표(날짜마다 새것)가 아닌 날
    _d, m, e = T.plan(day, 1)[0]
    _d2, m2, e2 = T.plan(day, 1, used={m.key, e.key})[0]
    assert m2.key != m.key and e2.key != e.key


def test_rankings_come_from_engine(plan90):
    """제1조항: 띠 순위는 엔진 계산 그대로."""
    for _, m, e in plan90:
        if m.rows:
            assert [r.ddi for r in m.rows] == [r.ddi for r in rank(m.kind, m.period)]
        if e.key.startswith("jangin-") and not e.key.startswith(("jangin-double", "jangin-stem")):
            kind = e.key.split("-")[1]
            p = next(p for p in T.periods(_) if e.key.endswith(p.key))
            top = [r.ddi for r in rank(kind, p)[:3]]
            listed = [ln.split(". ")[1].split("띠")[0] for ln in e.pages[0] if re.match(r"^\d\. ", ln)]
            assert listed == top


def test_jangin_shape(plan90):
    """사주장인식: 본글 1장 + 내 댓글로 이어 쓰기, 끝장은 '따로 봐야 알아요' + 프로필 안내."""
    js = [e for _, _, e in plan90 if e.style == "jangin"]
    assert js
    for e in js:
        assert 5 <= len(e.pages) <= 7
        assert any("따로 봐야 알아요" in x for x in e.pages[-1])
        assert "프로필 링크" in e.pages[-1][-1]


def test_text_rules(plan90):
    for d, m, e in plan90:
        txt = T.all_text(m, e)
        assert not [w for w in T.BANNED if w in txt], (d, m.key, e.key)
        assert all(len(p) <= 500 for p in e.parts)
        for y in re.findall(r"\b(19\d\d|20\d\d)년생", txt):
            assert T.Y_LO <= int(y) <= T.Y_HI
        if m.title:
            assert len(m.title) == 3
            assert "월급날 웃음" not in "".join(m.title)
        if m.fmt == "forceteller" and m.data["tpl"] in ("lack", "much"):
            assert m.data["say"][0].startswith("태어날 때 받은 여덟 글자 안에")


def test_years_only_to_2007():
    assert T.years("돼지")[0] == 2007 and T.years("쥐")[-1] == 1960
