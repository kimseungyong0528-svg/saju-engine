"""자평진전·적천수 판단 규칙."""

from saju.classics import judge, luck_effect
from saju.constants import BRANCHES, STEMS
from saju.pillars import FourPillars, Pillar


def chart(key: str) -> FourPillars:
    return FourPillars(*[Pillar(STEMS.index(k[0]), BRANCHES.index(k[1])) for k in key.split()])


def test_summer_metal_needs_water_first():
    j = judge(chart("경오 신사 경진 신사"))      # 사월 경금, 수 거의 없음
    assert j["johu"]["state"] == "난" and j["johu"]["urgent"]
    assert j["yongsin"]["element"] == "수" and j["yongsin"]["method"] == "조후"
    assert "화" in j["yongsin"]["gisin"]          # 더운 사주에 불을 더 보태지 않는다
    assert j["mulsang"]["season"] == "여름"


def test_mixed_officers_is_a_flaw():
    j = judge(chart("경오 신사 경진 신사"))
    assert j["ziping"]["gyeok"] == "편관격"
    assert any("관살혼잡" in b for b in j["ziping"]["bad"])


def test_follow_wealth_when_no_support():
    j = judge(chart("무진 무술 갑진 무진"))
    assert j["jong"]["name"] == "종재격"
    assert j["yongsin"]["element"] == "토"


def test_follow_strength_when_no_officer():
    j = judge(chart("임인 계묘 갑인 을해"))
    assert j["jong"]["name"] == "종왕격"
    assert j["yongsin"]["element"] == "목"


def test_transformed_earth():
    j = judge(chart("병진 기축 갑술 무진"))     # 갑기합, 축월(토), 목 천간 없음
    assert j["hwagi"]["name"] == "갑기 합화토격"
    assert j["yongsin"]["element"] == "토"


def test_stem_pair_image():
    assert "벽갑" in judge(chart("경신 을유 갑신 경오"))["mulsang"]["pairs"]


def test_luck_effect_follows_sangsin():
    j = judge(chart("신사 기해 정유 을사"))      # 정관격, 신약 → 인성이 상신
    assert j["ziping"]["sangsin"] == "인성"
    assert luck_effect(j, "정인", "편인")["effect"] == "도움"
    assert luck_effect(j, "상관", "상관")["effect"] == "방해"
