"""만세력 계산을 독립 구현(sxtwl, 寿星万年历)과 대조한다."""

import random
from datetime import datetime, timedelta, timezone

import pytest
import sxtwl

from saju import astro
from saju.pillars import Pillar, compute_pillars, day_pillar_for_date
from saju.timeutil import civil_to_utc
from datetime import date, time


def test_solar_terms_match_reference_within_two_minutes():
    worst = 0.0
    for year in range(1940, 2051):
        for when, lon, name in astro.solar_terms(year):
            beijing = (when + timedelta(hours=8)).replace(tzinfo=None)
            diffs = []
            for shift in (-1, 0, 1):  # 자정 근처 절기는 하루 옆 날짜에 잡힐 수 있음
                d = beijing + timedelta(days=shift)
                day = sxtwl.fromSolar(d.year, d.month, d.day)
                if day.hasJieQi():
                    ref = sxtwl.JD2DD(day.getJieQiJD())
                    ref_dt = datetime(int(ref.Y), int(ref.M), int(ref.D), int(ref.h), int(ref.m)) + timedelta(seconds=float(ref.s))
                    diffs.append(abs((ref_dt - beijing).total_seconds()))
            assert diffs, (year, name)
            worst = max(worst, min(diffs))
    assert worst < 120


def test_known_ipchun_kst():
    kst = astro.ipchun(2024) + timedelta(hours=9)
    assert (kst.month, kst.day, kst.hour, kst.minute) == (2, 4, 17, 26) or (kst.hour, kst.minute) == (17, 27)


def test_day_pillar_known_value():
    assert day_pillar_for_date(date(2000, 1, 1)).korean == "무오"


def test_pillars_match_reference_random_sample():
    # 첫 화면 '계산 근거'의 "10,000개 모두 일치" 문구가 이 검사에 기대므로 줄이지 말 것.
    rng = random.Random(2027)
    checked = 0
    while checked < 10000:
        y, m, d = rng.randint(1940, 2049), rng.randint(1, 12), rng.randint(1, 28)
        h, mi = rng.randint(0, 22), rng.randint(0, 59)
        day = sxtwl.fromSolar(y, m, d)
        if day.hasJieQi():
            continue  # 절입일은 sxtwl의 일 단위 월주와 비교할 수 없음
        bj = datetime(y, m, d, h, mi)
        utc = (bj - timedelta(hours=8)).replace(tzinfo=timezone.utc)
        # 경도 120°의 평균태양시 = 중국 표준시
        fp = compute_pillars(utc, 120.0)
        exp = [Pillar(g.tg, g.dz) for g in (day.getYearGZ(), day.getMonthGZ(), day.getDayGZ(), day.getHourGZ(h))]
        assert fp.as_list() == exp, bj
        checked += 1


@pytest.mark.parametrize("d,t,offset", [
    (date(1957, 7, 1), time(12, 0), timedelta(hours=9, minutes=30)),   # UTC+8:30 + 서머타임
    (date(1958, 1, 1), time(12, 0), timedelta(hours=8, minutes=30)),
    (date(1988, 7, 1), time(12, 0), timedelta(hours=10)),              # 올림픽 서머타임
    (date(1990, 7, 1), time(12, 0), timedelta(hours=9)),
])
def test_korean_standard_time_history(d, t, offset):
    assert civil_to_utc(d, t).utc_offset == offset


def test_dst_end_is_ambiguous():
    # 1988-10-09 03:00 서머타임 해제 → 02:00~03:00이 두 번
    assert civil_to_utc(date(1988, 10, 9), time(2, 30)).ambiguous
