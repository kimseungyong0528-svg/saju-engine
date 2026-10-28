"""출생 정보 → 사주 명식과 분석 결과.

입력 형식은 운명서재 화면의 사람 정보(personFields/readPerson)와 같다.
모르는 시간·지역은 임의로 채우지 않고, 가능한 범위 전체를 계산해
공통 결과와 달라지는 결과(후보)를 나눈다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from korean_lunar_calendar import KoreanLunarCalendar

from . import analysis, classics, luck
from .constants import PILLAR_NAMES, STEMS, ELEMENTS, STEM_ELEMENT, ZODIAC_ANIMALS
from .pillars import FourPillars, PillarOptions, compute_pillars, day_pillar_for_date
from .regions import KOREA, Region, region_by_code
from .timeutil import civil_to_utc

CALCULATION_VERSION = "saju-engine/0.1.0"
MIN_YEAR, MAX_YEAR = 1940, 2050


class BirthInputError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class Person:
    name: str
    sex: str                         # male | female
    birth: str                       # YYYY-MM-DD (calendar 기준 날짜)
    calendar: str = "solar"          # solar | lunar | unknown
    leap: bool | None = None         # 음력 윤달 여부 (None = 모름)
    time_accuracy: str = "exact"     # exact | approximate | unknown
    time: str | None = None          # HH:MM
    time_range: dict | None = None   # {"start": "HH:MM", "end": "HH:MM", "endDayOffset": 0|1}
    birth_place: dict = field(default_factory=lambda: {"status": "unknown"})

    @classmethod
    def from_frontend(cls, v: dict) -> "Person":
        accuracy = v.get("timeAccuracy") or ("unknown" if v.get("unknown") else "exact")
        return cls(
            name=v.get("name", ""), sex=v.get("sex", ""), birth=v.get("birth", ""),
            calendar=v.get("calendar", "solar"), leap=v.get("leap"),
            time_accuracy=accuracy, time=v.get("time"), time_range=v.get("timeRange"),
            birth_place=v.get("birthPlace") or {"status": "unknown"},
        )


def _parse_hm(s: str) -> time:
    h, m = s.split(":")
    t = time(int(h), int(m))
    return t


def solar_birth_dates(p: Person) -> list[dict]:
    """입력 날짜를 양력으로. 확정되지 않으면 가능한 날짜를 모두 돌려준다."""
    try:
        y, m, d = (int(x) for x in p.birth.split("-"))
    except Exception:
        raise BirthInputError("INVALID_BIRTH_DATE", "생년월일 형식을 확인해주세요.")
    if not (MIN_YEAR <= y <= MAX_YEAR):
        raise BirthInputError("INVALID_BIRTH_DATE", f"{MIN_YEAR}~{MAX_YEAR}년 출생만 지원해요.")
    out = []
    if p.calendar in ("solar", "unknown"):
        try:
            out.append({"solar": date(y, m, d), "basis": "양력"})
        except ValueError:
            if p.calendar == "solar":
                raise BirthInputError("INVALID_BIRTH_DATE", "존재하지 않는 양력 날짜예요.")
    if p.calendar in ("lunar", "unknown"):
        leaps = [p.leap] if p.leap is not None else [False, True]
        for leap in leaps:
            c = KoreanLunarCalendar()
            if c.setLunarDate(y, m, d, bool(leap)):
                out.append({"solar": date.fromisoformat(c.SolarIsoFormat()),
                            "basis": "음력 윤달" if leap else "음력 평달"})
            elif p.leap is not None:
                raise BirthInputError("INVALID_BIRTH_DATE", "존재하지 않는 음력 날짜예요. 윤달 여부를 확인해주세요.")
    if not out:
        raise BirthInputError("INVALID_BIRTH_DATE", "존재하지 않는 날짜예요.")
    return out


def _place_range(place: dict) -> tuple[Region | None, list[float], str]:
    """(대표 지역, 비교할 경도 목록, 설명)."""
    status = place.get("status", "unknown")
    region = region_by_code(place.get("regionChoice") or place.get("regionCode"))
    if status in ("known", "region-only") and region:
        lons = sorted({region.lon_min, region.lon, region.lon_max})
        return region, lons, region.name
    return None, [KOREA.lon_min, KOREA.lon, KOREA.lon_max], "대한민국(지역 미상)"


@dataclass
class Variant:
    pillars: FourPillars
    civil_from: datetime
    civil_to: datetime
    dates: set = field(default_factory=set)
    longitudes: set = field(default_factory=set)
    utc_sample: datetime | None = None


def _scan(solar_dates: list[dict], p: Person, lons: list[float], options: PillarOptions,
          center: float | None = None) -> list[Variant]:
    """가능한 명식을 모두 모은다. 맨 앞(대표 명식)은 첫 날짜·시작 시각·지역 대표 경도의 명식이다
    (시간 모름은 낮 12시. 사이트 engine.mjs chartFromPerson 과 같은 명식, 제1조항)."""
    known_time = p.time_accuracy != "unknown"
    variants: dict[str, Variant] = {}
    first: list[str] = []

    def visit(civil: datetime, basis: str, lon: float):
        ct = civil_to_utc(civil.date(), civil.time())
        utcs = [ct.utc] + ([ct.alternative_utc] if ct.alternative_utc else [])
        for u in utcs:
            fp = compute_pillars(u, lon, known_time, options)
            if not known_time:
                # 시간 미상: 일주는 입력한 날짜 기준(경도 보정으로 날짜를 옮기지 않음)
                fp = FourPillars(fp.year, fp.month, day_pillar_for_date(civil.date()), None)
            if not first and lon == center and (known_time or civil.time() == time(12, 0)):
                first.append(fp.key)   # 시간 모름은 사이트처럼 낮 12시 명식을 대표로
            v = variants.get(fp.key)
            if v is None:
                v = variants[fp.key] = Variant(fp, civil, civil, utc_sample=u)
            v.civil_from = min(v.civil_from, civil)
            v.civil_to = max(v.civil_to, civil)
            v.dates.add(basis)
            v.longitudes.add(lon)

    for sd in solar_dates:
        day = sd["solar"]
        if p.time_accuracy == "exact":
            start = end = datetime.combine(day, _parse_hm(p.time or ""))
        elif p.time_accuracy == "approximate":
            r = p.time_range or {}
            start = datetime.combine(day, _parse_hm(r["start"]))
            end = datetime.combine(day + timedelta(days=r.get("endDayOffset", 0)), _parse_hm(r["end"]))
            if end < start:
                raise BirthInputError("TIME_REQUIRED", "출생 시간 범위의 끝이 시작보다 빨라요.")
        else:
            start = datetime.combine(day, time(0, 0))
            end = datetime.combine(day, time(23, 59))
        t = start
        while t <= end:
            for lon in lons:
                visit(t, sd["basis"], lon)
            t += timedelta(minutes=1)
    return sorted(variants.values(), key=lambda v: (v.pillars.key not in first, v.civil_from))


def _boundary_warnings(p: Person, solar_dates, lon: float, options: PillarOptions, base: FourPillars) -> list[str]:
    """정확한 시각이라도 ±15분 안에 명식이 바뀌면 경고."""
    if p.time_accuracy != "exact" or len(solar_dates) != 1:
        return []
    t0 = datetime.combine(solar_dates[0]["solar"], _parse_hm(p.time))
    out = set()
    for delta in range(-15, 16):
        t = t0 + timedelta(minutes=delta)
        ct = civil_to_utc(t.date(), t.time())
        fp = compute_pillars(ct.utc, lon, True, options)
        for i, (a, b) in enumerate(zip(base.as_list(), fp.as_list())):
            if a != b:
                out.add(f"출생 시각 {abs(delta)}분 {'이후' if delta > 0 else '이전'}에 {PILLAR_NAMES[i]}가 바뀌는 경계예요.")
    return sorted(out)


def analyze_pillars(fp: FourPillars, utc: datetime, sex: str, current_year: int) -> dict:
    st = analysis.strength(fp)
    strength_by_el = analysis.element_strength(fp)
    out = {
        "pillars": analysis.ten_god_table(fp),
        "day_master": {
            "stem": STEMS[fp.day.stem],
            "element": ELEMENTS[STEM_ELEMENT[fp.day.stem]],
            "yang": fp.day.stem % 2 == 0,
        },
        "zodiac": ZODIAC_ANIMALS[fp.year.branch],
        "elements": {
            "count": analysis.element_counts(fp),
            "strength": strength_by_el,
            "judgement": analysis.element_judgement(strength_by_el),
        },
        "ten_god_groups": analysis.ten_god_counts(fp),
        "strength": st,
        "gyeokguk": analysis.gyeokguk(fp),
        "yongsin": analysis.yongsin_candidates(fp, st),
        "classics": classics.judge(fp),
        "relations": analysis.natal_relations(fp),
        "shinsal": analysis.shinsal(fp),
        "daewoon": luck.daewoon(fp, utc, sex),
        "sewoon": luck.sewoon(fp, list(range(current_year - 1, current_year + 14))),   # 결제 전 화면의 12년 지도(2027~)까지
        "wolwoon": luck.wolwoon(fp, current_year),
        # 주문한 달부터 12개월을 고를 수 있도록 앞뒤 해까지 36개월
        "wolwoon_span": [m for y in (current_year - 1, current_year, current_year + 1)
                         for m in luck.wolwoon(fp, y)],
    }
    if fp.hour is None:
        out["notes"] = ["출생 시간 미상으로 시주를 제외한 삼주(三柱)로 분석했어요."]
    return out


def analyze_person(raw: dict | Person, options: PillarOptions = PillarOptions(),
                   current_year: int | None = None) -> dict:
    p = raw if isinstance(raw, Person) else Person.from_frontend(raw)
    if p.sex not in ("male", "female"):
        raise BirthInputError("PERSON_REQUIRED", "성별을 확인해주세요.")
    if p.time_accuracy == "exact" and not p.time:
        raise BirthInputError("TIME_REQUIRED", "출생 시각을 입력해주세요.")
    if p.time_accuracy == "approximate" and not (p.time_range and p.time_range.get("start") and p.time_range.get("end")):
        raise BirthInputError("TIME_REQUIRED", "대략적인 출생 시간 범위를 입력해주세요.")
    current_year = current_year or datetime.now().year

    solar_dates = solar_birth_dates(p)
    region, lons, place_label = _place_range(p.birth_place)
    variants = _scan(solar_dates, p, lons, options, region.lon if region else KOREA.lon)

    uncertainties = []
    if len(solar_dates) > 1:
        uncertainties.append({"kind": "date", "message": "양력·음력 또는 윤달 여부가 확정되지 않아 가능한 날짜를 모두 계산했어요."})
    if p.time_accuracy == "approximate":   # 사이트 화면과 같은 시각으로 푼다(제1조항)
        uncertainties.append({"kind": "time", "message": f"출생 시간은 넣어 주신 범위의 시작 시각({p.time_range['start']})으로 풀었어요."})
    elif p.time_accuracy != "exact":
        uncertainties.append({"kind": "time", "message": "태어난 시간을 몰라 시주(태어난 시간의 기둥)는 ?로 비워 두고, 해·달·날의 여섯 글자로 풀었어요."})
    if not region or p.birth_place.get("status") != "known":
        uncertainties.append({"kind": "place", "message": f"태어난 지역은 {place_label} 대표 위치로 풀었어요."})

    analyzed = []
    for v in variants:
        utc = v.utc_sample
        analyzed.append({
            "key": v.pillars.key,
            "civil_from": v.civil_from.isoformat(timespec="minutes"),
            "civil_to": v.civil_to.isoformat(timespec="minutes"),
            "date_basis": sorted(v.dates),
            "longitudes": sorted(v.longitudes),
            "analysis": analyze_pillars(v.pillars, utc, p.sex, current_year),
        })

    common = {}
    for i, name in enumerate(PILLAR_NAMES):
        values = {(v.pillars.as_list()[i].korean if v.pillars.as_list()[i] else None) for v in variants}
        common[name] = values.pop() if len(values) == 1 else None

    warnings = []
    if len(variants) == 1:
        lon = region.lon if region else KOREA.lon
        warnings = _boundary_warnings(p, solar_dates, lon, options, variants[0].pillars)
    for sd in solar_dates:
        if p.time_accuracy == "exact":
            ct = civil_to_utc(sd["solar"], _parse_hm(p.time))
            if ct.ambiguous:
                warnings.append("서머타임 해제 시각이라 같은 시각이 두 번 있었어요. 두 경우를 모두 계산했어요.")
            if ct.nonexistent:
                warnings.append("서머타임 시작으로 건너뛴 시각이에요. 기록된 시각을 다시 확인해주세요.")

    return {
        "version": CALCULATION_VERSION,
        "options": {"solar_time": options.solar_time, "zi_rule": options.zi_rule},
        "person": {"name": p.name, "sex": p.sex},
        "input": {
            "birth": p.birth, "calendar": p.calendar, "leap": p.leap,
            "solar_dates": [{"date": sd["solar"].isoformat(), "basis": sd["basis"]} for sd in solar_dates],
            "time_accuracy": p.time_accuracy, "time": p.time, "time_range": p.time_range,
            "place": place_label,
        },
        "variant_count": len(variants),
        "common_pillars": common,
        "uncertainties": uncertainties,
        "warnings": warnings,
        "variants": analyzed,
    }
