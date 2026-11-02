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
    keys = [e.key for d in plan90[:60] for _, _, e in d.threads]
    assert len(keys) == len(set(keys))
    # 영상은 그 달 순위만 쓰므로(사장님 "12월껀 12월에 해") 두 달이 아니라 한 주 안에서 겹치지 않는다
    # 12월 재료는 아직 모자라서(사장님께 알림, 2026-11-03) 지금은 11월 네 주만 본다. 12월 재료를 늘리면 56으로 되돌린다.
    for i in range(0, 28, 7):
        week = [m.key for d in plan90[i:i + 7] for m in (d.morning, d.video2)]
        assert len(week) == len(set(week)), week
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
    assert [s for s in meta.SLOTS if s not in ("아침영상", "저녁영상", "점심글", "밤글")] == [s for s, _, _ in T.THREAD_SLOTS]
    assert all(f"SLOT={s}" in y for s in meta.SLOTS if s not in ("밤", "밤글")) and 'SLOT="밤 밤글"' in y


# ── 스레드 이용자 30명 피드백 (사장님 2026-11-01 "그대로 이행하는 것으로 프로그램에 못박아") ──
RULES = json.loads((Path(T.__file__).parent / "thread_rules.json").read_text())


def _threads(plan90):
    return [e for d in plan90 for _, _, e in d.threads]


def test_thread_rules_fixed():
    assert [r["id"] for r in RULES["feedback"]] == ["heart_first", "no_scary_tag", "dohwa_short_good", "short_phrase",
                                                     "salgu_one_theme", "salgu_no_memo", "reason_short", "keep_basis",
                                                     "long_list_spacing", "emoji_marks", "weekly_popular_topics",
                                                     "sipsin_fact"]


# 1탄 댓글에서 잡힌 실수(인성·식상 뒤바뀜) 같은 짝을 문장 재료 전체에서 막는다 (sipsin_fact).
SIPSIN_WRONG = [("인성", ("연하", "챙겨 주는 걸 좋아", "베풀")), ("식상", ("연상", "보살핌을 받")),
                ("편인", ("연하", "챙겨 주는 걸 좋아")), ("정인", ("연하", "챙겨 주는 걸 좋아"))]


def _bank_lines(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _bank_lines(v)
    elif isinstance(x, list):
        for v in x:
            yield from _bank_lines(v)


def test_sipsin_fact():
    banks = json.loads((Path(T.__file__).parent / "banks.json").read_text())
    for line in _bank_lines(banks):
        for s in line.replace("...", ".").split(". "):
            for star, bad in SIPSIN_WRONG:
                assert not (star in s and any(b in s for b in bad)), line


def test_double_good_follows_sipsin():
    """사주 검수원 2026-11-01: 겹경사 카드의 좋은 일은 들어오는 위 글자가 그 해 천간에게 무슨 십신인지와 맞아야 한다."""
    from saju.marketing.ranking import month_period, year_period
    for p in (month_period(2026, 12), year_period(2027)):
        for x in T.double_years(p):
            want = T._god(T.STEM_ELEMENT["갑을병정무기경신임계".index(x["gz"][0])], T.STEM_ELEMENT[p.stem])
            assert x["god"] == want
    assert T.double_years(month_period(2026, 12))[0]["god"] == "관성"   # 경(庚)은 을(乙)에게 정관
    assert T.double_years(year_period(2027))[0]["god"] == "재성"      # 정(丁)은 임(壬)에게 정재
    assert "직함" not in " ".join(T.DOUBLE_GOOD["인성"])


def test_dohwa_list_uses_day_stem():
    """사주 검수원 2026-11-01: 십신은 일간 기준. 목록 글은 '사주에 토 많은 분'이 아니라 '토(무·기) 일간'으로 콕 집는다."""
    for x in range(5):
        e = T.dohwa_list(dt.date(2026, 11, 4), x, 0)
        assert "일간 분들 주목" in e.pages[0][0] and "일간에게" in e.pages[0][-2]


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
        if e.key.startswith(("dohwa-list-", "dohwa-ten-")):   # 원문 목록 글 (❶~❺, 10일간 스포): 심사원 레퍼런스 지적으로 한두 줄 규칙에서 뺀다
            body = e.pages[0]
            assert any("이에요" in x for x in body[-2:]), e.key   # 끝에 십신 뜻 풀이
            assert not [w for w in ("조심", "과열", "주의", "위험") if w in " ".join(body)], e.key
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
        if e.key.startswith("salgu-list-"):   # 정리본은 제목 하나가 주제 (레퍼런스 정리본 틀)
            assert "정리본" in e.pages[0][0] and e.topic.split("-")[-1] in ("love", "money", "flow", "self"), e.key
            love += e.topic.endswith("love")
            continue
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
    assert J["pass"] == 100 and J["per_criterion"] == 5   # 사장님 2026-11-01: 50명, 10항목, 100점(처음 97점), 냉정하게
    assert [c["id"] for c in J["criteria"]] == ["natural", "hook", "click", "trust", "follow", "reference", "expert", "easy", "concrete", "comment", "saju_fact"]
    assert all(c["name"] and c["minus"] for c in J["criteria"])
    assert len(J["criteria"]) * J["per_criterion"] == 55   # 사장님 2026-11-01: 사주 검수원 5명 추가
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
            if e.style == "dohwa" and not e.key.startswith(("dohwa-list-", "dohwa-ten-")):
                assert set(e.pages[0]) & set(T.DOHWA_WHY_HEAD), e.key
                n += 1
    assert n


def test_judges_authority_first():
    """사장님 2026-11-01: 심사원 피드백의 디테일과 권위가 1순위 (사장님 말·제1조항 다음), 레퍼런스는 원문과 나란히 비교."""
    j = json.loads((Path(T.__file__).parent / "thread_rules.json").read_text(encoding="utf-8"))["judges"]
    a = j["authority"]
    assert a["order"][:3] == ["사장님이 직접 한 말", "제1조항 (엔진 사실·통일성)", "심사원 피드백"]
    assert "인용" in a["detail"] and "무효" in a["detail"]
    assert "상위90-원문.txt" in j["references"] and any("원문" in s and "나란히" in s for s in j["strict"])


def test_judge_model_top_priority_pinned():
    """사장님 2026-11-01 '무조건 이 심사원 모델 1순위로 저장하고': 모델이 지워지거나 약해지면 실패."""
    j = json.loads((Path(T.__file__).parent / "thread_rules.json").read_text(encoding="utf-8"))["judges"]
    assert j["pass"] == 100
    assert "무조건" in j["authority"]["_must"] and "올리지 않는다" in j["authority"]["_must"]
    assert any("0부터" in s for s in j["strict"])
    assert any("글 하나하나" in s for s in j["strict"]) and any("사주 검수원 5명" in s for s in j["strict"])
    md = (Path(T.__file__).parents[3] / "CLAUDE.md").read_text(encoding="utf-8")
    assert "제2조항: 심사원 모델 1순위" in md and "상위90-원문.txt" in md


def test_video_fits_studio_upload():
    """넷리파이 함수는 6MB까지 받고, 영상은 글자(base64)로 바뀌어 4/3배가 된다. 2026-11-01 5MB 영상이 413으로 막혔다."""
    from saju.marketing.formula import render
    assert render.MAX_VIDEO * 4 / 3 < 5_000_000


def test_shift_threads_one_slot():
    """사장님 2026-11-01 '2탄은 내일 아침 7시반으로, 스레드는 한개씩 미루자': 번호는 그대로, 칸만 한 칸씩."""
    from saju.marketing.formula.__main__ import shift_threads
    def th(i, slot):
        return {"id": f"x{i}", "channel": "threads", "slot": slot, "time": "", "title": str(i)}
    man = {"days": [{"date": "2026-11-01", "weekday": "일", "items": [th(1, "오후"), th(2, "늦은밤"), {"id": "r", "channel": "youtube", "slot": "오전", "time": "07:00"}]},
                    {"date": "2026-11-02", "weekday": "월", "items": [th(3, "오전"), th(4, "늦은밤")]}]}
    assert shift_threads(man, "2026-11-01 늦은밤") == 3
    where = {it["id"]: (d["date"], it["slot"], it["time"]) for d in man["days"] for it in d["items"]}
    assert where["x1"] == ("2026-11-01", "오후", "")
    assert where["x2"] == ("2026-11-02", "오전", "07:30")
    assert where["x3"] == ("2026-11-02", "점심", "12:00")
    assert where["x4"] == ("2026-11-03", "오전", "07:30")
    assert where["r"][0] == "2026-11-01"


def test_move_one_item():
    """사장님 2026-11-01 '지우지 말고 내일 3탄 올릴 시간에 ... 못올리는거 그 중에서 괜찮은거 하나로 대체해'."""
    from saju.marketing.formula.__main__ import move_items
    man = {"days": [{"date": "2026-11-01", "weekday": "일", "items": [{"id": "a", "channel": "threads", "slot": "점심", "time": "12:00"}]},
                    {"date": "2026-11-02", "weekday": "월", "items": [{"id": "b", "channel": "threads", "slot": "저녁", "time": "18:00"}]}]}
    assert move_items(man, "a=2026-11-02 저녁") == 1
    assert man["days"][0]["items"] == []
    assert sorted((x["id"], x["time"]) for x in man["days"][1]["items"]) == [("a", "18:00"), ("b", "18:00")]   # 있던 글은 지우지 않는다
    with pytest.raises(SystemExit):
        move_items(man, "없음=2026-11-02 저녁")


def test_long_list_spacing():
    """사장님 2026-11-01: 긴 번호 목록은 번호 사이에 빈 줄, 짧은 번호 목록은 붙여 둔다. 만든 글 전부 검사."""
    spaced = 0
    for dd in T.plan(dt.date(2026, 11, 1), 8):
        for _, _, e in dd.threads:
            for raw, part in zip(["\n".join(p).strip() for p in e.shown], e.parts):
                assert T.space_long_lists(part) == part and part.replace("\n\n", "\n") == raw.replace("\n\n", "\n"), e.key
                spaced += part != raw
                lines = part.split("\n")
                for a, b in zip(lines, lines[1:]):
                    if T.NUM_LINE.match(a) and T.NUM_LINE.match(b):   # 붙어 있는 번호 목록은 짧은 것뿐
                        assert len(a) + len(b) <= 2 * T.LONG_ITEM + 20, (e.key, a)
    assert spaced >= 14  # 살구식 '흥미로운 사주 이야기들' 탄은 전부 띄운다
    assert "\n\n2." in T.space_long_lists("1. " + "가" * 40 + "\n2. " + "나" * 40)
    assert T.space_long_lists("1. 1985년생 소띠\n2. 1973년생 소띠") == "1. 1985년생 소띠\n2. 1973년생 소띠"


def test_emoji_marks():
    """사장님 2026-11-01: 숫자는 글자로, 띠 이름표엔 띠 이모지, 좋은·조심 신호는 🟢·🔴, 첫 줄 앞에 이모지 하나."""
    for dd in T.plan(dt.date(2026, 11, 1), 21):
        for _, _, e in dd.threads:
            text = "\n".join(e.parts)
            assert not re.search("[0-9]\ufe0f?\u20e3", text), e.key            # 1️⃣ 금지
            assert T._is_emoji(e.parts[0].lstrip()[0]), e.key                  # 첫 줄 이모지
            for line in text.split("\n"):
                mo = re.match(r"^(\d+\.\s|.*?년생\s)?(원숭이|호랑이|돼지|토끼|쥐|소|용|뱀|말|양|닭|개)띠", line)
                assert not mo, (e.key, line)                                    # 이름표 자리 띠는 전부 이모지가 붙었다
                if "신호" in line and line[:1] in "※🟢🔴":
                    assert line[0] in "🟢🔴", (e.key, line)
                    assert (line[0] == "🔴") == any(w in line for w in T.BAD_HEAD), (e.key, line)


def test_claude_approves_judged_threads(monkeypatch):
    """사장님 2026-11-01: 심사 통과한 주의 스레드는 /studio 승인 없이 시간 맞춰 올린다. 다른 채널은 여전히 승인이 있어야 한다."""
    from saju.marketing import meta, publish
    plan = {"week": "2026-11-01", "approved": {}, "posted": {}, "items": [
        {"id": "a", "slot": "오전", "channel": "threads", "approved_by": "claude", "title": "t", "texts": {}},
        {"id": "b", "slot": "오전", "channel": "threads", "title": "t", "texts": {}},
        {"id": "c", "slot": "오전", "channel": "instagram-reel", "title": "t", "texts": {}}]}
    monkeypatch.setattr(publish, "_call", lambda *a, **k: plan)
    out = []
    monkeypatch.setattr("builtins.print", lambda *a, **k: out.append(" ".join(map(str, a))))
    meta.run("오전", "2026-11-02", dry=True)
    assert "올릴 것: a t" in out and any("승인 안 됨): b" in x for x in out) and any("승인 안 됨): c" in x for x in out)


def test_follow_link_only_after_toss(monkeypatch):
    """사장님 2026-11-01: 토스 연동되면 팔로우 말 뒤에 사이트 링크까지. 그 전엔 링크 없음."""
    from saju.marketing import meta
    monkeypatch.delenv("SNS_SITE_LINK", raising=False)
    assert meta.with_link(["본글", "팔로우 해 두세요!"]) == ["본글", "팔로우 해 두세요!"]
    monkeypatch.setenv("SNS_SITE_LINK", "on")
    assert meta.with_link(["본글", "팔로우 해 두세요!"])[-1].endswith("https://unmyeong-saju.com")
    # 사장님 2026-11-02: 링크 문구는 '운명서재에서 정확한 내 사주 보기'
    assert "운명서재에서 정확한 내 사주 보기 👉 https://unmyeong-saju.com" in meta.with_link(["본글", "팔로우 해 두세요!"])[-1]
    assert meta.with_link(["본글", "팔로우 해 두세요!"])[-1] == "팔로우 해 두세요!\n\n운명서재에서 정확한 내 사주 보기 👉 https://unmyeong-saju.com"


def test_threads_only_without_video(tmp_path):
    """사장님 2026-11-01 '영상은 올리지마 확실히 될때까지 일단 스레드만': 영상 없이 만들면 영상 게시물은 묶음에 없다."""
    from saju.marketing.formula.__main__ import build
    r = build(dt.date(2026, 11, 2), 1, tmp_path, video=False)
    chans = {it["channel"] for d in r["manifest"]["days"] for it in d["items"]}
    assert chans == {"threads"}


def test_claude_approves_videos_only_when_asked(monkeypatch):
    """사장님 2026-11-01: 릴스·유튜브도 1주치씩. --approve-videos 를 준 주만 영상에 클로드 승인 표시가 붙는다."""
    from saju.marketing.formula import __main__ as fm
    assert set(fm.VIDEO_CHANNELS) == {"instagram-reel", "facebook-reel", "youtube"}
    src = Path(fm.__file__).read_text(encoding="utf-8")
    assert "if approve_videos:" in src and "--approve-videos" in src
    wf = (Path(__file__).parent.parent / ".github/workflows/marketing.yml").read_text(encoding="utf-8")
    assert "--approve-videos" in wf and "approve_videos:" in wf


def test_two_videos_and_moved_thread_post(plan90):
    """사장님 2026-11-01: 영상은 하루 2개(서로 다른 형식), 아침 8시·저녁 7시에 세 SNS 같이. 인스타 게시글·페북 글은 묶음에 넣지 않고 전날 인기 글을 고른다."""
    from saju.marketing.formula import __main__ as fm
    from saju.marketing import meta
    for d in plan90[:14]:
        assert d.video2 is not None and d.video2.fmt != d.morning.fmt and d.video2.key != d.morning.key
    assert (fm.VIDEO_AM, fm.VIDEO_PM) == ("08:00", "19:00")
    assert {k: meta.SLOT_TIME[k] for k in ("아침영상", "점심글", "저녁영상", "밤글")} == \
        {"아침영상": "08:00", "점심글": "12:30", "저녁영상": "19:00", "밤글": "21:00"}
    src = Path(fm.__file__).read_text(encoding="utf-8")
    assert '"channel": "instagram-cards"' not in src and '"channel": "facebook-post"' not in src


def test_bgm_six_tracks_random():
    """사장님 2026-11-01: 배경음악은 직접 만들지 말고 저작권 괜찮은 유행곡 10개를 랜덤으로, 그중 '5678은 빼 나머지만으로 돌려' → 6곡."""
    from saju.marketing.video import music
    meta = json.loads((music.BGM_DIR / "bgm.json").read_text(encoding="utf-8"))
    assert len(meta["tracks"]) == 6 and len(music.tracks()) == 6
    assert not {"shakuhachi.mp3", "oriental-skies.mp3", "mystical.mp3", "mystical-trap.mp3"} & {t["file"] for t in meta["tracks"]}
    assert all(t["source"].startswith("https://pixabay.com/music/") for t in meta["tracks"])
    assert "music.bgm(" in (Path(__file__).parent.parent / "saju/marketing/formula/render.py").read_text(encoding="utf-8")


def _pick_plan():
    T = {"1/1": "🔮 첫 줄\n본문"}
    items = [{"id": f"y_{s}-threads", "channel": "threads", "slot": s, "time": t, "material": m, "format": f,
              "images": [f"인스타/{m}_1.jpg"], "texts": T}
             for s, t, m, f in (("오전", "07:30", "jangin-a", "사주장인식"), ("점심", "12:00", "dohwa-b", "도화도르식"),
                                ("저녁", "18:00", "jangin-c", "사주장인식"), ("밤", "21:00", "salgu-d", "살구식"))]
    items.append({"id": "y_오전-reel", "channel": "instagram-reel", "slot": "아침영상", "time": "08:00", "material": "v"})
    posted = {it["id"]: {"ok": True, "url": f"https://www.threads.com/@u/post/{it['material']}"} for it in items}
    posted["y_밤-threads"] = {"ok": False}
    return {"week": "2026-11-02", "items": items, "approved": {}, "posted": posted}


def test_pick_yesterday_top_posts(monkeypatch):
    """사장님 2026-11-01: 인스타 게시글·페북 글은 어제 반응(좋아요+댓글+리포스트+인용) 좋은 스레드 글 2개. 못 읽으면 사주장인식."""
    from saju.marketing.formula import pick
    plan = _pick_plan()
    items = pick.candidates(plan)
    assert [it["material"] for it in items] == ["jangin-a", "dohwa-b", "jangin-c"]   # 안 올라간 글·영상은 뺀다
    assert [it["material"] for it in pick.rank(items, None)][:2] == ["jangin-a", "jangin-c"]
    assert pick.rank(items, {"y_점심-threads": 30, "y_오전-threads": 2, "y_저녁-threads": 9})[0]["material"] == "dohwa-b"

    calls = []

    def fake_call(method, path, body=None, content_type=""):
        calls.append((method, path, body))
        if body:
            b = json.loads(body)
            plan["posted"][b["id"]] = b
        return plan if "today" in path else {}
    monkeypatch.setattr(pick.publish, "_call", fake_call)
    monkeypatch.setattr(pick, "scores", lambda items, tok: {"y_점심-threads": 30, "y_저녁-threads": 9})
    sent = []
    monkeypatch.setitem(pick.meta.POSTERS, "instagram-cards", lambda w, it: sent.append(("ig", it["id"], it["images"])) or "ig")
    monkeypatch.setitem(pick.meta.POSTERS, "facebook-post", lambda w, it: sent.append(("fb", it["id"], it["texts"]["본문"])) or "fb")
    monkeypatch.delenv("SNS_PICK", raising=False)
    assert pick.run(0, "2026-11-03", tok="t") == 0 and sent == []          # 사장님 "올려" 전에는 꺼져 있다
    monkeypatch.setenv("SNS_PICK", "on")
    pick.run(0, "2026-11-03", tok="t")
    pick.run(1, "2026-11-03", tok="t")
    assert [s[1] for s in sent] == ["2026-11-03_pick-dohwa-b-cards", "2026-11-03_pick-dohwa-b-fbpost",
                                    "2026-11-03_pick-jangin-c-cards", "2026-11-03_pick-jangin-c-fbpost"]
    assert sent[0][2] == ["인스타/dohwa-b_1.jpg"] and "🔮 첫 줄" in sent[1][2]
    assert "today?date=2026-11-02" in calls[0][1]


def test_pick_slots_and_cards_in_build():
    """12:30 점심글·21:00 밤글이 고르기로 이어지고, 묶음을 만들 때 스레드 글마다 캡처를 찍어 둔다."""
    from saju.marketing import meta
    from saju.marketing.formula import __main__ as fm
    assert meta.PICK_SLOTS == {"점심글": 0, "밤글": 1}
    src = Path(fm.__file__).read_text(encoding="utf-8")
    assert "C.thread_cards(x" in src and 'it["images"]' in src
    wf = (Path(__file__).parent.parent / ".github/workflows/sns-post.yml").read_text(encoding="utf-8")
    assert '"17 3 * * *") SLOT=점심글' in wf and 'SLOT="밤 밤글"' in wf and "SNS_PICK" in wf


def test_video_scripts_follow_engine(plan90):
    """영상 (사장님 2026-11-01 "레퍼런스 그대로"): 7초, 대사는 화면 위 제목 한 줄 + '~ 알아보세요!/확인하세요!',
    밑에 글은 유튜브 구독 · 인스타 댓글 · 페북 팔로우로 곳마다 다르고 '나의 ○○' 로 내 이야기가 된다."""
    from saju.marketing.formula import script as S
    assert S.SECONDS == 7
    for d in plan90[:14]:
        for m in (d.morning, d.video2):
            ls = S.script(m)
            assert len(ls) == 1 and ls[0].endswith(("알아보세요!", "확인하세요!")), ls
            if m.fmt not in ("sinbi", "forceteller"):
                assert ls[0].startswith(S.top_title(m)), ls          # 화면 위 제목 그대로 읽는다
            c = S.cta(m)
            assert c["youtube"].startswith("나의 ") and c["youtube"].endswith("더 자세히 알고 싶다면 구독!")
            assert c["facebook-reel"] == c["youtube"].replace("구독!", "팔로우!")
            assert c["instagram-reel"] == c["facebook-reel"]   # 인스타도 팔로우 (사장님 2026-11-01)
            assert not any("미리 알고" in x for x in c.values())
    keys = [T._topic(m.key) for d in plan90[:7] for m in (d.morning, d.video2) if m.rows]
    assert len(keys) == len(set(keys))   # 같은 순위를 형식만 바꿔 한 주에 두 번 내지 않는다


def test_video_judges_pinned():
    """사장님 2026-11-01 "제 1원칙으로 못박아둬": 영상도 55명(11항목) + 행동 유도 5명, 100점. 지우거나 약하게 바꾸지 않는다."""
    j = RULES["judges"]
    v = j["video"]
    assert v["pass"] == 100 and v["per_criterion"] == 5 and len(j["criteria"]) == 11
    assert [c["id"] for c in v["extra_criteria"]] == ["action"]
    assert {"상단 제목", "영상 내용", "타입캐스트 대사", "밑에 글"} <= {x.split(" (")[0] for x in v["scope"]}
    assert v["format"]["seconds"] == 7
    md = (Path(T.__file__).parents[3] / "CLAUDE.md").read_text(encoding="utf-8")
    first = md.split("## 제2조항")[0]
    assert "영상도 스레드와 같은 심사" in first and "행동 유도 심사원 5명" in first


def test_videos_only_this_month():
    """사장님 2026-11-01 "12월껀 12월에 해": 영상 순위·운세는 올리는 달 것만 (스레드 글은 따로)."""
    for d in T.plan(dt.date(2026, 11, 20), 7, set()):
        for m in (d.morning, d.video2):
            if m.period is not None:
                assert m.period.key == f"{d.date:%Y-%m}", m.key
