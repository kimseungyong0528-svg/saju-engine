"""대운 · 세운 · 월운."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import astro
from .analysis import branch_relation, branch_ten_god, stem_relation, ten_god, twelve_stage
from .constants import PILLAR_NAMES, STEM_YANG
from .pillars import FourPillars, Pillar, month_pillar, year_pillar
from .timeutil import SEOUL_TZ


def daewoon_direction(fp: FourPillars, sex: str) -> int:
    """양남음녀는 순행(+1), 음남양녀는 역행(-1)."""
    yang_year = STEM_YANG[fp.year.stem]
    return 1 if (yang_year == (sex == "male")) else -1


def daewoon_start(utc: datetime, direction: int) -> dict:
    """대운수: 출생부터 다음(순행)·이전(역행) 절까지의 날수 ÷ 3."""
    prev_jie, next_jie = astro.previous_and_next_jie(utc)
    target = next_jie[0] if direction > 0 else prev_jie[0]
    days = abs((target - utc).total_seconds()) / 86400
    years_exact = days / 3
    years = int(years_exact)
    months = int(round((years_exact - years) * 12))
    if months == 12:
        years, months = years + 1, 0
    return {
        "days_to_term": round(days, 2),
        "term": next_jie[2] if direction > 0 else prev_jie[2],
        "exact_years": round(years_exact, 2),
        "years": years,
        "months": months,
        "number": max(1, round(years_exact)),  # 전통 표기 대운수(반올림, 최소 1)
    }


def daewoon(fp: FourPillars, utc: datetime, sex: str, count: int = 10) -> dict:
    direction = daewoon_direction(fp, sex)
    start = daewoon_start(utc, direction)
    birth_local = utc.astimezone(SEOUL_TZ)
    ds = fp.day.stem
    periods = []
    for i in range(1, count + 1):
        p = fp.month.shift(direction * i)
        age_from = start["exact_years"] + (i - 1) * 10
        start_date = birth_local + timedelta(days=age_from * 365.2425)
        periods.append({
            "order": i,
            "ganzhi": p.korean,
            "hanja": p.hanja,
            "age_from": int(start["number"] + (i - 1) * 10),
            "age_to": int(start["number"] + i * 10 - 1),
            "start_year": start_date.year,
            "start_date": start_date.date().isoformat(),
            "stem_ten_god": ten_god(ds, p.stem),
            "branch_ten_god": branch_ten_god(ds, p.branch),
            "twelve_stage": twelve_stage(ds, p.branch),
            "relations": interaction_with_natal(fp, p),
        })
    return {"direction": "순행" if direction > 0 else "역행", "start": start, "periods": periods}


def interaction_with_natal(fp: FourPillars, p: Pillar) -> list[dict]:
    """운의 간지가 원국 각 기둥과 맺는 합충 관계."""
    out = []
    for i, n in enumerate(fp.as_list()):
        if n is None:
            continue
        for r in stem_relation(p.stem, n.stem):
            out.append({"type": r, "with": PILLAR_NAMES[i], "level": "천간"})
        for r in branch_relation(p.branch, n.branch):
            out.append({"type": r, "with": PILLAR_NAMES[i], "level": "지지"})
    return out


def _mid_year(year: int) -> datetime:
    return datetime(year, 7, 1, tzinfo=timezone.utc)


def sewoon(fp: FourPillars, years: list[int]) -> list[dict]:
    """연도별 운(세운). 해당 연도 입춘~다음 입춘 기준 간지."""
    ds = fp.day.stem
    out = []
    for y in years:
        p = year_pillar(_mid_year(y))
        out.append({
            "year": y,
            "ganzhi": p.korean,
            "hanja": p.hanja,
            "starts": astro.ipchun(y).astimezone(SEOUL_TZ).isoformat(timespec="minutes"),
            "stem_ten_god": ten_god(ds, p.stem),
            "branch_ten_god": branch_ten_god(ds, p.branch),
            "twelve_stage": twelve_stage(ds, p.branch),
            "relations": interaction_with_natal(fp, p),
        })
    return out


def wolwoon(fp: FourPillars, year: int) -> list[dict]:
    """한 해(입춘부터)의 월별 운. 각 달은 절입 시각에 시작한다."""
    ds = fp.day.stem
    jie = [t for t in astro.solar_terms(year) + astro.solar_terms(year + 1) if t[1] in astro.JIE_LONGITUDES]
    jie = [t for t in jie if t[0] >= astro.ipchun(year)][:12]
    out = []
    for when, _, name in jie:
        moment = when + timedelta(hours=1)
        p = month_pillar(moment, year_pillar(moment))
        out.append({
            "starts": when.astimezone(SEOUL_TZ).isoformat(timespec="minutes"),
            "term": name,
            "ganzhi": p.korean,
            "hanja": p.hanja,
            "stem_ten_god": ten_god(ds, p.stem),
            "branch_ten_god": branch_ten_god(ds, p.branch),
            "relations": interaction_with_natal(fp, p),
        })
    return out
