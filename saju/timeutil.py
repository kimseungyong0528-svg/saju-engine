"""한국 표준시 이력과 진태양시 보정.

Asia/Seoul 시간대 데이터(tzdata)에 다음 이력이 들어 있다.
- 1954-03-21 ~ 1961-08-09: UTC+8:30
- 1948~1951, 1955~1960, 1987~1988: 서머타임(+1시간)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import ephem

SEOUL_TZ = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True)
class CivilTime:
    """입력된 현지 시각을 UTC로 바꾼 결과와 서머타임 모호성."""
    utc: datetime
    utc_offset: timedelta
    ambiguous: bool       # 서머타임 해제 때 같은 시각이 두 번 있었음
    nonexistent: bool     # 서머타임 시작 때 건너뛴 시각
    alternative_utc: datetime | None = None


def civil_to_utc(d: date, t: time) -> CivilTime:
    naive = datetime.combine(d, t)
    a = naive.replace(tzinfo=SEOUL_TZ, fold=0)
    b = naive.replace(tzinfo=SEOUL_TZ, fold=1)
    ua, ub = a.astimezone(timezone.utc), b.astimezone(timezone.utc)
    roundtrip = ua.astimezone(SEOUL_TZ).replace(tzinfo=None)
    nonexistent = roundtrip != naive
    ambiguous = (ua != ub) and not nonexistent
    return CivilTime(
        utc=ua,
        utc_offset=a.utcoffset(),
        ambiguous=ambiguous,
        nonexistent=nonexistent,
        alternative_utc=ub if (ambiguous or nonexistent) else None,
    )


def equation_of_time_minutes(utc: datetime) -> float:
    """균시차(분). 진태양시 = 평균태양시 + 균시차."""
    d = ephem.Date(utc.astimezone(timezone.utc).replace(tzinfo=None))
    sun = ephem.Sun(d)
    # 그리니치 평균태양시와 태양 시각의 차이로 계산
    obs = ephem.Observer()
    obs.lon, obs.lat, obs.date, obs.pressure = "0", "0", d, 0
    gast = obs.sidereal_time()
    hour_angle = (gast - sun.g_ra) % (2 * math.pi)
    apparent_solar_hours = (math.degrees(hour_angle) / 15.0 + 12.0) % 24.0
    u = utc.astimezone(timezone.utc)
    mean_hours = u.hour + u.minute / 60 + u.second / 3600
    diff = (apparent_solar_hours - mean_hours + 12) % 24 - 12
    return diff * 60.0


def local_solar_time(utc: datetime, longitude: float, mode: str = "mean") -> datetime:
    """출생지 경도의 태양시(시간대 정보 없는 datetime).

    mode
    - "mean": 평균태양시(경도 보정만, 국내 만세력의 일반적인 방식)
    - "apparent": 진태양시(경도 보정 + 균시차)
    - "none": 보정 없이 입력 시각(표준시) 그대로 사용
    """
    u = utc.astimezone(timezone.utc).replace(tzinfo=None)
    if mode == "none":
        return utc.astimezone(SEOUL_TZ).replace(tzinfo=None)
    solar = u + timedelta(minutes=longitude * 4.0)
    if mode == "apparent":
        solar += timedelta(minutes=equation_of_time_minutes(utc))
    elif mode != "mean":
        raise ValueError(f"알 수 없는 태양시 방식: {mode}")
    return solar
