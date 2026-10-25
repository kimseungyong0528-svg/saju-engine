"""무료 사주 맛보기용 계산 자료를 만든다 (site/public/assets/free/saju-data.json).

브라우저는 파이썬 사주 엔진을 돌릴 수 없으므로, 엔진이 쓰는 값 가운데
천문 계산이 필요한 것만 미리 뽑아 둔다.
- jie: 절입 시각(UTC, 1970년부터 분)과 그 달의 지지. 월주·연주(입춘)에 쓴다.
- tz: 한국 표준시 변경 이력(서머타임 포함). [바뀐 UTC 분, UTC와의 차이(분)]
- regions: 시·도 코드별 대표 경도(평균태양시 보정).

예) python site/tools/build_taster_data.py
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from saju import astro
from saju.regions import REGIONS
from saju.timeutil import SEOUL_TZ

OUT = Path(__file__).resolve().parents[1] / "public" / "assets" / "free" / "saju-data.json"
FIRST, LAST = 1899, 2031
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def minutes(dt: datetime) -> int:
    return round((dt - EPOCH).total_seconds() / 60)


def jie_table() -> list[list[int]]:
    out = []
    for y in range(FIRST, LAST + 1):
        for t, lon, _ in astro.solar_terms(y):
            if lon in astro.JIE_LONGITUDES:
                out.append([minutes(t), astro.JIE_LONGITUDES[lon]])
    out.sort()
    return out


def tz_table() -> list[list[int]]:
    out, prev = [], None
    t = datetime(FIRST, 1, 1, tzinfo=timezone.utc)
    while t.year <= LAST:
        off = round(t.astimezone(SEOUL_TZ).utcoffset().total_seconds() / 60)
        if off != prev:
            out.append([minutes(t), off])
            prev = off
        t += timedelta(minutes=30)
    return out


def main() -> None:
    data = {
        "range": [FIRST + 1, LAST - 1],
        "jie": jie_table(),
        "tz": tz_table(),
        "regions": {code: r.lon for code, r in REGIONS.items()},
        "defaultLon": REGIONS["1100000000"].lon,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"{OUT.name} {OUT.stat().st_size // 1024}KB · 절입 {len(data['jie'])}개")


if __name__ == "__main__":
    main()
