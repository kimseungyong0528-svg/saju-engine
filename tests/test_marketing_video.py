import datetime as dt
from datetime import datetime, timezone

from saju.marketing.checks import check_rank
from saju.marketing.content import ddi_posts, topic_posts
from saju.marketing.ranking import month_period, rank, rank_post, rank_posts, year_period, youtube_rank
from saju.marketing.video import voice
from saju.marketing.video.render import talk_plan
from saju.pillars import month_pillar, year_pillar


def test_money_2027_ranking_from_engine():
    rows = rank("money", year_period(2027))
    assert [r.ddi for r in rows[:3]] == ["토끼", "호랑이", "말"]
    assert rows[-1].ddi == "소" and sorted(r.rank for r in rows) == list(range(1, 13))
    assert rows[0].good[0] == "돈 기운이 들어와요"


def test_care_puts_clash_first():
    assert rank("care", year_period(2027))[0].ddi == "소"          # 축미충 + 형


def test_month_period_matches_engine():
    for y, m in [(2026, 11), (2026, 12), (2027, 1), (2027, 2), (2027, 8)]:
        u = datetime(y, m, 15, 3, tzinfo=timezone.utc)
        mp = month_pillar(u, year_pillar(u))
        p = month_period(y, m)
        assert (p.stem, p.branch) == (mp.stem, mp.branch), (y, m)


def test_rank_posts_pass_checks():
    pool = rank_posts(dt.date(2026, 10, 19))
    assert len({p.key for p in pool}) == len(pool) == 10
    assert pool[-1].period.key == "2026-11"
    for p in pool:
        assert check_rank(p, youtube_rank(p)) == [], p.key
        assert len(p.lines) == 14 and p.lines[-1].startswith("더 궁금한 사주는")


def test_voice_clean_reads_plain_korean():
    assert voice.clean("말띠의 오(午)와 미(未)는 '육합'이에요.") == "말띠의 오와 미는 육합이에요."
    assert voice.clean("1. 모임에 나가세요.") == "모임에 나가세요."


def test_talk_plan_scenes_and_lines():
    for p in [ddi_posts()[0], topic_posts()[0]]:
        texts, plan = talk_plan(p)
        types = [s["type"] for s in plan["scenes"]]
        assert types[0] == "cover" and types[-2:] == ["remember", "end"] and types.count("point") == len(p.slides)
        assert len(texts) == len(plan["caps"]) and texts[-1].startswith("더 궁금한 사주는")
        assert all(0 <= sc < len(plan["scenes"]) for _, sc in plan["caps"])
