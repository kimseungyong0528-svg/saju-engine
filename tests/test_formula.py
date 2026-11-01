"""SNS 게시물 공식 (사장님 2026-11-01 "전부 공식으로, 무한 발행"): 날짜만 넣으면 겹치지 않는 글이 엔진 계산대로 나온다."""

import collections
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
    """사주장인식: 본글 1장 + 내 댓글로 이어 쓰기, 끝장은 '따로 봐야 알아요' + 팔로우 안내."""
    js = [e for d in plan90 for _, _, e in d.threads if e.style == "jangin"]
    assert js
    for e in js:
        one = e.key.startswith(("jone-", "jstem-"))   # 띠·일간 한 장 글: 본글 + 이유 + 끝장
        assert len(e.pages) == 5 if one else 5 <= len(e.pages) <= 7
        assert any("따로 봐야 알아요" in x for x in e.pages[-1])
        assert any("팔로우" in x for x in e.pages[-1])
        assert all(pg[0].startswith("※ ") for pg in e.pages[-1:] if not e.key.startswith("jangin-double-"))


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
        head, *why = "\n".join(e.pages[0]).split("\n\n")
        body = [x for x in head.split("\n") if x.strip()]
        assert len(body) <= 2, e.key
        assert not why or (why[0].split("\n")[0] in T.DOHWA_WHY_HEAD and len(why[0].split("\n")) <= 4), e.key   # 근거 1~3줄
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


# ── 심사원 30명 + 상위 레퍼런스 90개 (사주장인·도화도르·살구, 사장님 2026-11-01) ──
def test_judges_rubric_fixed():
    J = RULES["judges"]
    assert J["pass"] == 97 and J["per_criterion"] == 5   # 사장님 2026-11-01: 50명, 10항목, 97점, 냉정하게
    assert [c["id"] for c in J["criteria"]] == ["natural", "hook", "click", "trust", "follow", "reference", "expert", "easy", "concrete", "comment"]
    assert all(c["name"] and c["minus"] for c in J["criteria"])
    assert len(J["criteria"]) * J["per_criterion"] == 50
    assert any("냉정" in s for s in J["strict"]) and any("이유" in s for s in J["strict"])
    assert [r["id"] for r in RULES["reference_rules"]] == ["question_heads", "term_date", "year_pain", "next_year", "ending",
                                                           "teaser", "week_variety", "dohwa_voice", "salgu_long", "follow_all"]


def test_reference_structure(plan90):
    """question_heads·term_date·ending: 사주장인식 댓글 장은 ※ 질문 머리, 기간은 절기 날짜, 끝장은 팔로우 말."""
    for e in _threads(plan90):
        if e.style != "jangin" or e.key.startswith("jangin-double-"):
            continue
        assert all(pg[0].startswith("※ ") for pg in e.pages[1:]), e.key
        assert re.search(r"(입춘|경칩|청명|입하|망종|소서|입추|백로|한로|입동|대설|소한)\(\d+/\d+\)", e.parts[1]), e.key
        assert any("팔로우" in x for x in e.pages[-1])


def test_term_date_from_engine():
    from saju.marketing.ranking import month_period, year_period
    assert T.start_label(month_period(2026, 11)) == "입동(11/7)"
    assert T.start_label(month_period(2026, 12)) == "대설(12/7)"
    assert T.start_label(year_period(2027)) == "입춘(2/4)"


def test_next_year_from_engine(plan90):
    """next_year: 내년 순위 줄은 엔진 순위 그대로."""
    from saju.marketing.ranking import year_period
    for e in _threads(plan90)[:120]:
        if not (e.key.startswith("jangin-") and e.kind and "-20" in e.key and len(e.key.split("-")[-1]) == 2):
            continue
        for pg in e.pages:
            if pg[0].startswith("※ 2027") or pg[0].startswith("※ 2028"):
                y = int(pg[0][2:6])
                for i, x in enumerate(pg):
                    m = re.match(r"^- (\d{4}) .+? (12띠|10일간) 중 (\d+)위", x)
                    if not m:
                        continue
                    who = pg[i - 1]
                    if who.endswith(" 일간"):
                        s = next(k for k in range(10) if T.STEM_NAMES[k].startswith(who.split(" ")[0][:2]))
                        place = [r.stem for r in T.stem_rank(e.kind, year_period(y))].index(s) + 1
                    else:
                        place = next(r.rank for r in rank(e.kind, year_period(y)) if T.ddi(r.ddi) == who)
                    assert int(m.group(3)) == place, (e.key, who, x)


def test_week_variety(plan90):
    """week_variety: 한 주 안에 같은 목록 주제·같은 대상·같은 약속 줄이 되풀이되지 않는다 (첫 주)."""
    week = plan90[:7]
    lists = [(i, e.kind) for i, d in enumerate(week) for _, _, e in d.threads if e.is_list and e.kind]
    for (i, k), (j, k2) in itertools.pairwise(lists):
        assert not (k == k2 and j - i == 1), lists
    assert sum(1 for _, k in lists if k == "care") <= 1
    ones = [e.facts[0][0] for d in week for _, _, e in d.threads if e.key.startswith(("jone-", "jstem-", "dohwa-d-", "dohwa-s-"))]
    assert len(ones) == len(set(ones)), ones
    tops = [e.topic for d in week for _, _, e in d.threads if e.topic]
    assert len(tops) == len(set(tops)), tops
    proms = {x for v in T.LB["promise"].values() for x in v}
    used = [x for d in week for _, _, e in d.threads for x in e.pages[0] if x in proms]
    assert len(used) == len(set(used)), used


def test_teaser_is_true(plan90):
    """teaser: '다음엔 … 올려요'는 실제로 바로 다음에 잡힌 사주장인식 글이다 (시간·날짜는 쓰지 않는다)."""
    seq = [e for d in plan90[:14] for _, _, e in d.threads if e.style == "jangin"]
    for e, nxt in zip(seq, seq[1:]):
        line = next((x for x in e.pages[-1] if x.startswith("다음엔 ") and x.endswith(" 올려요")), None)
        if line and "'" in line:
            assert T.title_of(nxt) in line, (line, T.title_of(nxt))


def test_dohwa_reply_is_true():
    """dohwa_voice·follow_all: 답글·끝맺음에 올리는 시간·'매일' 약속이 없다 (사장님 2026-11-01 '내가 이때 올리냐?')."""
    for r in [*T.B["dohwa_reply"], *T.B["salgu_end"], *T.LB["find_me"], *T.FOLLOW_END.values()]:
        txt = " ".join(r)
        assert not re.search(r"\d+시|매일|내일", txt), txt
        assert "팔로우" in txt


def test_salgu_long_bank():
    items = T.B["salgu_long"]
    assert len(items) >= 80 and len(set(items)) == len(items)
    assert not [x for x in items for w in T.BANNED if w in x]
    assert not [x for x in items if ("없는" in x or "없으면" in x) and "여덟 글자 안에" not in x and "관성" in x]


def test_follow_everywhere(plan90):
    """follow_all (사장님 2026-11-01): 모든 스레드 글 마지막 장과 모든 아침 캡션에 팔로우(유튜브는 구독) 말. 프로필 링크 말은 어디에도 없다."""
    from saju.marketing.formula.text import morning_texts
    for day in plan90:
        m = day.morning
        for _, _, th in day.threads:
            assert any("팔로우" in x for x in th.pages[-1]), th.key
            assert sum("팔로우" in x for x in th.pages[-1]) == 1, th.key   # 두 번 조르지 않는다
            assert "프로필 링크" not in "\n".join(th.parts), th.key
            for x in th.pages[-1]:   # 올리는 시간·날짜 약속 금지 (사장님 2026-11-01 '내가 이때 올리냐?')
                assert not re.search(r"\d+시|매일|내일|오늘 (아침|낮|오후|저녁|밤)", x), (th.key, x)
        mt = morning_texts(m)
        assert "구독" in mt["youtube"]["설명"]
        for ch in ("instagram-reel", "facebook-reel"):
            assert "팔로우" in mt[ch]["캡션"]
        assert "프로필 링크" not in json.dumps(mt, ensure_ascii=False) + json.dumps(m.data, ensure_ascii=False)
        assert "매일" not in json.dumps(mt, ensure_ascii=False) + json.dumps(m.data, ensure_ascii=False)


def test_no_line_more_than_three_times_a_week():
    """judges.strict (사장님 2026-11-01 '냉정하게'): 고정 틀을 뺀 같은 줄이 7일 안에 세 번 넘게 나오지 않는다 (사람 말투).
    11/1~11/8 심사한 묶음 기준. 다음 주는 만들 때 같은 검사로 다시 본다."""
    frame = re.compile(r"^(같은 .+(라도|이라도)|나머지 .+ 글자에 따라|- 천간|- 지지|.+ 달라요|.*따로 봐야 알아요|흥미로운 사주 이야기들.*"
                       r"|태어난 해는 여덟 글자 중 두 글자예요|겹경사인 이유|태어난 해 두 글자와|둘 다 좋게 만나요|\d\. .*)$")
    P = T.plan(dt.date(2026, 11, 1), 8)
    for w in range(2):
        c = collections.Counter(x for d in P[w:w + 7] for _, _, e in d.threads for pg in e.pages for x in pg if x.strip() and not frame.match(x))
        assert not [(k, v) for k, v in c.items() if v > 3], [(k, v) for k, v in c.most_common(5)]


def test_negative_posts_limited():
    """조심 글은 7일에 두 번까지, 한 장 조심 글은 한 번까지 (심사 2026-11-01)."""
    P = T.plan(dt.date(2026, 11, 1), 8)
    for w in range(2):
        neg = [e for d in P[w:w + 7] for _, _, e in d.threads if e.style == "jangin" and T._negative(e)]
        assert len(neg) <= 2 and sum(e.key.startswith(("jone-", "jstem-")) for e in neg) <= 1


def test_no_sira_ending():
    """사장님 2026-11-01: '~시라'는 쓰지 않고 '~하세요!·~보세요!·~두세요!'로 쓴다."""
    import pathlib
    for f in ["banks.json", "text.py"]:
        assert "시라" not in (pathlib.Path(T.__file__).parent / f).read_text(encoding="utf-8"), f
    for day in T.plan(dt.date(2026, 11, 1), 8):
        for _, _, e in day.threads:
            assert "시라" not in "\n".join("\n".join(pg) for pg in e.pages), e.key


def test_dohwa_has_reason():
    """사장님 2026-11-01 "디테일한 설명 없어?": 도화도르식 본글엔 '사주로 보면' 근거가 붙는다."""
    n = 0
    for day in T.plan(dt.date(2026, 11, 1), 8):
        for _, _, e in day.threads:
            if e.style == "dohwa" and e.key.startswith(("dohwa-d-", "dohwa-s-")):
                assert set(e.pages[0]) & set(T.DOHWA_WHY_HEAD), e.key
                n += 1
    assert n
