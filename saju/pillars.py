"""사주팔자(년·월·일·시주) 계산."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from . import astro
from .constants import BRANCHES, BRANCHES_HANJA, STEMS, STEMS_HANJA, ganzhi_index
from .timeutil import local_solar_time


@dataclass(frozen=True)
class Pillar:
    stem: int
    branch: int

    @property
    def index(self) -> int:
        return ganzhi_index(self.stem, self.branch)

    @property
    def korean(self) -> str:
        return STEMS[self.stem] + BRANCHES[self.branch]

    @property
    def hanja(self) -> str:
        return STEMS_HANJA[self.stem] + BRANCHES_HANJA[self.branch]

    @classmethod
    def from_index(cls, i: int) -> "Pillar":
        return cls(i % 10, i % 12)

    def shift(self, n: int) -> "Pillar":
        return Pillar.from_index((self.index + n) % 60)


@dataclass(frozen=True)
class FourPillars:
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar | None  # 시간 모름이면 None

    def as_list(self) -> list[Pillar | None]:
        return [self.year, self.month, self.day, self.hour]

    @property
    def key(self) -> str:
        return " ".join(p.korean if p else "??" for p in self.as_list())


@dataclass(frozen=True)
class PillarOptions:
    solar_time: str = "mean"   # mean | apparent | none (timeutil.local_solar_time 참고)
    zi_rule: str = "23"        # "23": 자시(23시)에 날짜가 바뀜 / "midnight": 야자시·조자시 구분


def _jdn(d: date) -> int:
    return d.toordinal() + 1721425


def day_pillar_for_date(d: date) -> Pillar:
    # 율리우스 적일 기준: (JDN - 11) mod 60 이 갑자(0)부터의 번호
    return Pillar.from_index((_jdn(d) - 11) % 60)


def year_pillar(utc: datetime) -> Pillar:
    y = utc.astimezone(timezone.utc).year
    saju_year = y if utc >= astro.ipchun(y) else y - 1
    return Pillar.from_index((saju_year - 4) % 60)


def month_pillar(utc: datetime, year: Pillar) -> Pillar:
    (_, lon, _), _ = astro.previous_and_next_jie(utc)
    branch = astro.JIE_LONGITUDES[lon]
    # 연간으로 인월(寅月)의 천간을 정하는 연두법(年頭法)
    first_stem = ((year.stem % 5) * 2 + 2) % 10
    offset = (branch - 2) % 12
    return Pillar((first_stem + offset) % 10, branch)


def hour_branch(solar: datetime) -> int:
    minutes = solar.hour * 60 + solar.minute + solar.second / 60
    return int(((minutes + 60) // 120) % 12)


def hour_stem(day_stem: int, branch: int) -> int:
    # 일간으로 자시(子時)의 천간을 정하는 시두법(時頭法)
    return ((day_stem % 5) * 2 + branch) % 10


def compute_pillars(utc: datetime, longitude: float, known_time: bool = True,
                    options: PillarOptions = PillarOptions()) -> FourPillars:
    """UTC 출생 시각과 출생지 경도로 사주팔자를 계산.

    시간을 모르면(known_time=False) utc는 그날 낮 12시 같은 대표 시각이어도 되며,
    시주는 비우고 년·월·일주만 돌려준다. 이때 날짜·절기 경계는 variants 모듈이 따로 비교한다.
    """
    year = year_pillar(utc)
    month = month_pillar(utc, year)
    solar = local_solar_time(utc, longitude, options.solar_time)
    if not known_time:
        return FourPillars(year, month, day_pillar_for_date(solar.date()), None)

    late_zi = solar.hour >= 23
    if options.zi_rule == "23":
        day_date = solar.date() + (timedelta(days=1) if late_zi else timedelta())
        day = day_pillar_for_date(day_date)
        hb = hour_branch(solar)
        hour = Pillar(hour_stem(day.stem, hb), hb)
    elif options.zi_rule == "midnight":
        day = day_pillar_for_date(solar.date())
        hb = hour_branch(solar)
        # 야자시(23~24시): 일주는 그날 그대로, 시주는 다음 날 자시
        stem_base = day_pillar_for_date(solar.date() + timedelta(days=1)).stem if late_zi else day.stem
        hour = Pillar(hour_stem(stem_base, hb), hb)
    else:
        raise ValueError(f"알 수 없는 자시 규칙: {options.zi_rule}")
    return FourPillars(year, month, day, hour)
