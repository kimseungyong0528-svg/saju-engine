"""24절기 계산 (PyEphem의 VSOP87 태양 위치 사용)."""

from __future__ import annotations

import bisect
import math
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import ephem

TERM_NAMES = [
    "춘분", "청명", "곡우", "입하", "소만", "망종", "하지", "소서", "대서", "입추", "처서", "백로",
    "추분", "한로", "상강", "입동", "소설", "대설", "동지", "소한", "대한", "입춘", "우수", "경칩",
]  # 태양 황경 0°, 15°, ... 345° 순서


def _to_ephem(dt: datetime) -> ephem.Date:
    return ephem.Date(dt.astimezone(timezone.utc).replace(tzinfo=None))


def _from_ephem(d: ephem.Date) -> datetime:
    return ephem.Date(d).datetime().replace(tzinfo=timezone.utc)


def sun_longitude(dt: datetime) -> float:
    """해당 시각의 태양 겉보기 황경(도, 당일 춘분점 기준)."""
    d = _to_ephem(dt)
    sun = ephem.Sun(d)
    # g_ra/g_dec: 지구 중심 겉보기 적경·적위(당일 분점). 이를 당일 황도로 변환한다.
    ecl = ephem.Ecliptic(ephem.Equatorial(sun.g_ra, sun.g_dec, epoch=d), epoch=d)
    return math.degrees(ecl.lon) % 360.0


def _solve_longitude(target: float, guess: datetime) -> datetime:
    t = guess
    for _ in range(20):
        diff = (target - sun_longitude(t) + 180.0) % 360.0 - 180.0
        if abs(diff) < 1e-7:
            break
        t = t + timedelta(days=diff / 0.98565)  # 하루 평균 이동 각도
    return t.replace(microsecond=0) + timedelta(seconds=round(t.microsecond / 1e6))


@lru_cache(maxsize=512)
def solar_terms(year: int) -> tuple[tuple[datetime, int, str], ...]:
    """해당 양력 연도(UTC 기준)에 시작하는 24절기 (시각, 황경, 이름) 목록."""
    out = []
    for k in range(24):
        lon = (285 + 15 * k) % 360  # 소한(1월 초)부터 시작
        guess = datetime(year, 1, 6, tzinfo=timezone.utc) + timedelta(days=15.2 * k)
        out.append((_solve_longitude(lon, guess), lon, TERM_NAMES[lon // 15]))
    return tuple(out)


# 월을 나누는 12절(節): 황경 315(입춘)=인월 ... 285(소한)=축월
JIE_LONGITUDES = {315: 2, 345: 3, 15: 4, 45: 5, 75: 6, 105: 7, 135: 8, 165: 9, 195: 10, 225: 11, 255: 0, 285: 1}


@lru_cache(maxsize=256)
def _jie_list(year: int) -> tuple[tuple[datetime, int, str], ...]:
    items = []
    for y in (year - 1, year, year + 1):
        items.extend(t for t in solar_terms(y) if t[1] in JIE_LONGITUDES)
    return tuple(sorted(items))


def previous_and_next_jie(dt: datetime) -> tuple[tuple[datetime, int, str], tuple[datetime, int, str]]:
    """dt 직전과 직후의 절(節)."""
    jl = _jie_list(dt.astimezone(timezone.utc).year)
    times = [t[0] for t in jl]
    i = bisect.bisect_right(times, dt)
    return jl[i - 1], jl[i]


def ipchun(year: int) -> datetime:
    """해당 연도의 입춘 시각(UTC)."""
    return next(t[0] for t in solar_terms(year) if t[1] == 315)
