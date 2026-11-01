"""SNS 게시물 공식 (사장님 2026-11-01 "전부 공식으로, 무한 발행"): 날짜만 넣으면 겹치지 않는 글이 엔진 계산대로 나온다."""

import datetime as dt
import itertools
import json
import re
from pathlib import Path

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
    styles = [e.style for d in plan90 for _, _, e in d.threads]
    assert {"jangin", "salgu", "dohwa"} <= set(styles)


def test_no_repeat_for_60_days(plan90):
    """두 달 동안 같은 재료를 다시 쓰지 않는다 (스레드 하루 6개 포함). 첫 장(본글)은 석 달 동안 겹치지 않는다."""
    keys = [m.key for _, m, _ in plan90[:60]] + [e.key for d in plan90[:60] for _, _, e in d.threads]
    assert len(keys) == len(set(keys))
    firsts = [e.parts[0] for d in plan90 for _, _, e in d.threads]
    assert len(firsts) == len(set(firsts))
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
    js = [e for d in plan90 for _, _, e in d.threads if e.style == "jangin"]
    assert js
    for e in js:
        one = e.key.startswith(("jone-", "jstem-"))   # 띠·일간 한 장 글: 본글 + 이유 + 끝장
        assert len(e.pages) == 3 if one else 5 <= len(e.pages) <= 7
        assert any("따로 봐야 알아요" in x for x in e.pages[-1])
        assert "프로필 링크" in e.pages[-1][-1]


def test_text_rules(plan90):
    for day in plan90:
        d, m, e = day
        es = [x for _, _, x in day.threads]
        txt = T.all_text(m, *es)
        assert not [w for w in T.BANNED if w in txt], (d, m.key, e.key)
        assert all(len(p) <= 500 for x in es for p in x.parts)
        for y in re.findall(r"\b(19\d\d|20\d\d)년생", txt):
            assert T.Y_LO <= int(y) <= T.Y_HI
        if m.title:
            assert len(m.title) == 3
            assert "월급날 웃음" not in "".join(m.title)
        if m.fmt == "forceteller" and m.data["tpl"] in ("lack", "much"):
            assert m.data["say"][0].startswith("태어날 때 받은 여덟 글자 안에")


def test_years_only_to_2007():
    assert T.years("돼지")[0] == 2007 and T.years("쥐")[-1] == 1960


def test_six_threads_a_day(plan90):
    """사장님 2026-11-01: 스레드 하루 6개, 사주장인식·도화도르식·살구식을 번갈아 두 번씩."""
    assert [(t, st) for _, t, st in T.THREAD_SLOTS] == [("07:30", "jangin"), ("12:00", "dohwa"), ("15:00", "salgu"),
                                                       ("18:00", "jangin"), ("21:00", "dohwa"), ("23:00", "salgu")]
    for d in plan90:
        assert [(t, e.style) for _, t, e in d.threads] == [(t, st) for _, t, st in T.THREAD_SLOTS]
        assert d.evening.key == next(e.key for s, _, e in d.threads if s == "저녁")


def test_salgu_bank_is_ours():
    """살구식 재료는 약 300개, 서로 겹치지 않고 금지어가 없다."""
    items = T.B["salgu"]
    assert len(items) >= 270 and len(set(items)) == len(items)
    assert not [x for x in items for w in T.BANNED if w in x]


def test_one_cards_use_engine_rank(plan90):
    """제1조항: 띠 한 장 글의 띠·근거는 엔진 순위 그대로 (앞 4개 또는 뒤 3개만)."""
    for d in plan90[:30]:
        for _, _, e in d.threads:
            if e.key.startswith("jone-"):
                _, kind, a, *pk = e.key.split("-")
                p = next(p for p in T.periods(d.date) if p.key == "-".join(pk))
                r = next(r for r in rank(kind, p) if r.ddi == a)
                assert r.rank <= 4 or r.rank >= 10
                assert f"{T.ddi(a)} ({T.years_full(a)})" in e.parts[0]


def test_sns_post_runs_every_slot():
    import pathlib

    from saju.marketing import meta
    y = pathlib.Path(__file__).resolve().parents[1].joinpath(".github/workflows/sns-post.yml").read_text(encoding="utf-8")
    assert meta.SLOTS == [s for s, _, _ in T.THREAD_SLOTS]
    assert all(f"SLOT={s}" in y for s in meta.SLOTS)


# ── 스레드 이용자 30명 피드백 (사장님 2026-11-01 "그대로 이행하는 것으로 프로그램에 못박아") ──
RULES = json.loads((Path(T.__file__).parent / "thread_rules.json").read_text())


def _threads(plan90):
    return [e for d in plan90 for _, _, e in d.threads]


def test_thread_rules_fixed():
    assert [r["id"] for r in RULES["feedback"]] == ["heart_first", "no_scary_tag", "dohwa_short_good", "short_phrase",
                                                     "salgu_one_theme", "salgu_no_memo", "reason_short", "keep_basis"]


def test_heart_first(plan90):
    """heart_first·no_scary_tag: 사주장인식 한 장 글은 마음·장면으로 시작, 조심 글 본글엔 꼬리표 없음."""
    for e in _threads(plan90):
        if e.key.startswith(("jone-", "jstem-")):
            p1 = e.pages[0]
            assert "띠" not in p1[0] and "일간" not in p1[0] and not p1[0].startswith(("축하", "죄송", "그거 아세요"))
            assert any(x.endswith("분들") for x in p1[:2])
            if any(x.endswith(B_BAD_ENDS) for x in p1):
                assert not [x for x in p1 if x.startswith("- ")]


B_BAD_ENDS = tuple(v["bl"] for v in T.B["one_lines"].values())


def test_dohwa_short_good(plan90):
    for e in _threads(plan90):
        if e.style != "dohwa":
            continue
        body = [x for x in e.pages[0] if x.strip()]
        assert len(body) <= 2, e.key
        assert not [w for w in ("조심", "과열", "주의", "서두르", "위험") if w in " ".join(body)], e.key


def test_dohwa_uses_top_ranks():
    """dohwa_short_good: 띠 4위 안, 일간 3위 안만 (엔진 순위 그대로)."""
    day = T.dt.date(2026, 11, 1)
    for p in T.periods(day):
        for kind in T.DOHWA_KINDS:
            for a in T.ZODIAC_ANIMALS:
                ev = T.dohwa_ddi(kind, p, a, 1)
                if ev:
                    assert next(r for r in T._rank(kind, p) if r.ddi == a).rank <= 4
            for s in range(10):
                ev = T.dohwa_stem(kind, p, s, 1)
                if ev:
                    assert [r.stem for r in T.stem_rank(kind, p)].index(s) < 3


def test_short_phrase(plan90):
    """short_phrase: '많은 분'은 짧게, '부족'은 제1조항 문구를 붙인다."""
    for e in _threads(plan90):
        for x in [ln for pg in e.pages for ln in pg]:
            if "많은 분" in x:
                assert "태어날 때 받은 여덟 글자" not in x, x
            if "부족한 분" in x:
                assert x.startswith(("태어날 때 받은 여덟 글자 안에", "(제발부탁)👏🏻 태어날 때 받은 여덟 글자 안에")), x


def test_salgu_one_theme(plan90):
    tans = [e for e in _threads(plan90) if e.style == "salgu"]
    love = 0
    for e in tans:
        items = [x.split(". ", 1)[1] for x in e.pages[0] if re.match(r"^\d\. ", x)]
        th = {T.salgu_theme(x) for x in items}
        assert th == {"love"} or th == {"self"} or th <= {"money", "flow"}, (e.key, th)
        love += th == {"love"}
    assert love * 2 >= len(tans)


def test_salgu_no_memo():
    assert not [x for x in T.B["salgu"] if re.search(r"자·오|인·신|진·술|갑진·|경진·|쥐-양", x)]


def test_reason_short(plan90):
    for e in _threads(plan90):
        if e.key.startswith("jangin-double-"):
            assert e.pages[1][0] == "겹경사인 이유" and len([x for x in e.pages[1][1:] if x.strip()]) <= 3
