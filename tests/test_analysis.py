from datetime import datetime, timezone

from saju.analysis import gyeokguk, ten_god, twelve_stage, void_branches
from saju.chart import BirthInputError, analyze_person
from saju.constants import BRANCHES
from saju.luck import daewoon_direction
from saju.pair import compare
from saju.pillars import FourPillars, Pillar

import pytest


@pytest.mark.parametrize("other,expected", [
    (0, "비견"), (1, "겁재"), (2, "식신"), (3, "상관"), (4, "편재"),
    (5, "정재"), (6, "편관"), (7, "정관"), (8, "편인"), (9, "정인"),
])
def test_ten_gods_for_gap(other, expected):
    assert ten_god(0, other) == expected


def test_twelve_stages():
    assert twelve_stage(0, 11) == "장생"   # 갑 → 해
    assert twelve_stage(0, 3) == "제왕"    # 갑 → 묘
    assert twelve_stage(1, 6) == "장생"    # 을 → 오
    assert twelve_stage(1, 2) == "제왕"    # 을 → 인


def test_void_of_gapja_cycle():
    assert [BRANCHES[b] for b in void_branches(Pillar(0, 0))] == ["술", "해"]
    assert [BRANCHES[b] for b in void_branches(Pillar(0, 10))] == ["신", "유"]  # 갑술순


def test_daewoon_direction():
    fp = FourPillars(Pillar(6, 6), Pillar(7, 5), Pillar(6, 4), Pillar(7, 5))  # 경오년(양)
    assert daewoon_direction(fp, "male") == 1
    assert daewoon_direction(fp, "female") == -1


def _person(**kw):
    base = {"name": "테스트", "sex": "male", "birth": "1990-05-15", "calendar": "solar",
            "timeAccuracy": "exact", "time": "10:30",
            "birthPlace": {"status": "known", "regionChoice": "1100000000"}}
    base.update(kw)
    return base


def test_exact_birth_single_chart():
    r = analyze_person(_person(), current_year=2026)
    assert r["variant_count"] == 1
    assert r["variants"][0]["key"] == "경오 신사 경진 신사"
    dw = r["variants"][0]["analysis"]["daewoon"]
    assert dw["direction"] == "순행" and dw["start"]["number"] == 7


def test_lunar_input_converts():
    r = analyze_person(_person(birth="1990-04-21", calendar="lunar", leap=False), current_year=2026)
    assert r["input"]["solar_dates"][0]["date"] == "1990-05-15"


def test_unknown_time_on_ipchun_day_gives_two_candidates():
    r = analyze_person(_person(birth="1988-02-04", timeAccuracy="unknown", time=None), current_year=2026)
    assert r["variant_count"] == 2
    assert r["common_pillars"]["일주"] == "기축" and r["common_pillars"]["년주"] is None


def test_unknown_place_never_assumes_seoul():
    r = analyze_person(_person(birthPlace={"status": "unknown"}), current_year=2026)
    assert any(u["kind"] == "place" for u in r["uncertainties"])


def test_boundary_warning_near_hour_change():
    # 서울 경도 보정 후 11:30 부근이 사시/오시 경계
    r = analyze_person(_person(time="11:28"), current_year=2026)
    assert r["warnings"]


def test_invalid_lunar_leap_rejected():
    with pytest.raises(BirthInputError):
        analyze_person(_person(birth="1990-02-01", calendar="lunar", leap=True))


def test_gyeokguk_skips_bigyeop():
    fp = FourPillars(Pillar(6, 6), Pillar(7, 5), Pillar(6, 4), Pillar(7, 5))
    assert gyeokguk(fp)["name"] == "편관격"  # 사월 정기 병화 = 경금의 편관


def test_pair_compare_shape():
    a = FourPillars(Pillar(6, 6), Pillar(7, 5), Pillar(6, 4), Pillar(7, 5))
    b = FourPillars(Pillar(4, 4), Pillar(2, 4), Pillar(1, 9), None)
    out = compare(a, b)
    assert "육합(금)" in out["spouse_palace"]["relations"]  # 진유합
    assert out["day_master"]["other_as_my_ten_god"] == "정재"
