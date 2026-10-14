"""리포트 끝에 넣는 다른 상품 안내.

순서와 이름, 소개 문구, 판매가·정가는 운명서재 화면(unmyeong-preview-v32.html의 PRODUCTS)과 같다.
링크는 화면의 상품 소개 주소 형식(#/f/{id}/intro)을 따른다. 사이트 주소는 SAJU_SITE_URL로 정한다.
"""

from __future__ import annotations

import os

SITE_URL = os.environ.get("SAJU_SITE_URL", "https://unmyeong-saju.com").rstrip("/")

PRODUCTS = [
    {"id": "newyear", "name": "금월선녀의 2027 신년운세", "category": "운세/평생운", "price": 29800, "original": 55000,
     "line": "2027년, 나에게 어떤 해가 될까요"},
    {"id": "lifetime", "name": "금월선녀의 평생사주", "category": "운세/평생운", "price": 49800, "original": 110000,
     "line": "지나온 나를 이해하고 앞으로의 길을 만나다"},
    {"id": "romance", "name": "금월선녀의 연애사주", "category": "연애", "price": 29800, "original": 55000,
     "line": "다음 사랑은 어떤 모습으로 올까요"},
    {"id": "reunion", "name": "금월선녀의 재회사주", "category": "재회", "price": 29800, "original": 55000,
     "line": "끝나지 않은 마음, 다시 이어질 수 있을까"},
    {"id": "intimate", "name": "금월선녀의 깊은 궁합", "category": "연애", "price": 29800, "original": 55000,
     "line": "말하지 못한 마음까지, 우리 얼마나 닮았을까"},
    {"id": "wealth", "name": "금월선녀의 재물운", "category": "금전", "price": 29800, "original": 55000,
     "line": "내 삶의 결실은 언제 익어갈까요"},
    {"id": "career", "name": "금월선녀의 직업·이직운", "category": "금전", "price": 29800, "original": 55000,
     "line": "나에게 맞는 일, 움직여야 할 순간"},
    {"id": "business", "name": "금월선녀의 사업운", "category": "금전", "price": 29800, "original": 55000,
     "line": "내가 키우는 일, 사업의 다음 장을 읽다"},
    {"id": "health", "name": "금월선녀의 건강운", "category": "건강", "price": 29800, "original": 55000,
     "line": "나의 몸과 마음, 돌봄의 리듬을 찾다"},
]


def discount_percent(p: dict) -> int:
    """화면과 같은 계산: (정가 - 판매가) / 정가, 반올림."""
    return round((p["original"] - p["price"]) / p["original"] * 100)


def product_url(pid: str, site: str | None = None) -> str:
    return f"{(site or SITE_URL).rstrip('/')}/#/f/{pid}/intro"


def _first_year(f: dict, gods: set[str]) -> int | None:
    for s in f["sewoon"]:
        if s["stem_ten_god"] in gods or s["branch_ten_god"] in gods:
            return s["year"]
    return None


def _count(f: dict, group: str) -> int:
    return next(g["n"] for g in f["ten_god_groups"] if g["group"] == group)


def hooks(f: dict) -> dict[str, str]:
    """상품마다 이 사람 사주에 맞춘 한두 문장(계산값만 사용)."""
    name = f["person"]["name"]
    male = f["person"]["sex"] == "male"
    spouse_group, spouse_gods = ("재성", {"편재", "정재"}) if male else ("관성", {"편관", "정관"})
    n_spouse = _count(f, spouse_group)
    love_year = _first_year(f, spouse_gods)
    money_year = _first_year(f, {"편재", "정재"})
    career_year = _first_year(f, {"편관", "정관", "식신", "상관"})
    dm = f["day_master"]
    peach = [s for s in f["shinsal_names"] if s in ("도화살", "홍염살")]
    lacking = [e["name"] for e in f["elements"] if e["status"] == "부족"]
    many = [e["name"] for e in f["elements"] if e["status"] == "많음"]
    return {
        "lifetime": (f"{name}님의 일간은 {dm['stem']}({dm['element_name']})이고 사주의 틀은 {f['gyeokguk']['name']}이에요. "
                     "성격, 일, 돈, 연애, 건강과 앞으로의 10년 운, 연도별·월별 운세까지 인생 전체를 한 권으로 풀어 드려요."),
        "romance": ((f"{name}님 사주에는 배우자를 뜻하는 {spouse_group}이 {n_spouse}개 있어요. " if n_spouse
                     else f"{name}님 타고난 사주에는 배우자를 뜻하는 {spouse_group}이 없어서, 인연은 운에서 들어오는 시기를 잡는 것이 중요해요. ")
                    + (f"{', '.join(peach)}도 있어 이성에게 끌림을 주는 힘이 있어요. " if peach else "")
                    + (f"{love_year}년에 인연의 기운이 들어와요. 어떤 사람이 언제, 어떻게 오는지 달 단위로 알려 드려요." if love_year
                       else "인연이 들어오는 시기와 만나는 방법을 달 단위로 알려 드려요.")),
        "reunion": (f"헤어진 사람의 사주를 {name}님 사주와 나란히 놓고, 두 사람이 다시 이어질 수 있는지 봐요. "
                    "연락하기 좋은 달과 피해야 할 달, 먼저 다가갈지 기다릴지까지 정리해 드려요."),
        "intimate": (f"{name}님은 {dm['element_name']}의 기운을 타고났고, {f['lucky']['element_name']}의 기운이 필요해요. "
                     "상대방이 그 기운을 채워 주는 사람인지, 어디서 부딪히는지 두 사람의 오행을 비교해 알려 드려요."),
        "wealth": ((f"{name}님 사주에는 재물을 뜻하는 재성이 {_count(f, '재성')}개 있어요. " if _count(f, "재성")
                    else f"{name}님 타고난 사주에는 재물을 뜻하는 재성이 없어서, 재물이 들어오는 해를 아는 것이 특히 중요해요. ")
                   + (f"{money_year}년에 재물의 기운이 들어와요. " if money_year else "")
                   + "돈이 들어오는 해와 새는 해, 나에게 맞는 돈 모으는 방법을 해마다 짚어 드려요."),
        "career": (f"{name}님의 사주 틀은 {f['gyeokguk']['name']}이에요. "
                   + (f"{career_year}년에 일의 흐름이 크게 움직여요. " if career_year else "")
                   + "맞는 직무와 이직·승진에 좋은 시기를 연도와 달까지 알려 드려요."),
        "business": (f"사업은 나 자신(비겁 {_count(f, '비겁')}개), 표현과 재능(식상 {_count(f, '식상')}개), 재물(재성 {_count(f, '재성')}개)의 균형으로 봐요. "
                     "혼자 할지 함께 할지, 언제 확장하고 언제 지켜야 할지 정리해 드려요."),
        "health": ((f"{name}님은 {', '.join(many)} 기운이 강하고 " if many else f"{name}님은 ")
                   + (f"{', '.join(lacking)} 기운이 약해요. " if lacking else "오행이 비교적 고른 편이에요. ")
                   + "이 균형에 맞는 생활 리듬, 잠과 휴식, 계절별 돌봄 습관을 한 주 실천표로 드려요."),
        "newyear": _newyear_hook(f),
    }


def _newyear_hook(f: dict) -> str:
    from .newyear import hook
    return hook(f)


# 사이트 카테고리 탭 순서: 신년운세(2026-10-13 맨 위 배너) → 연애(연애사주, 깊은 궁합) → 재회 → 금전(재물·직업·사업) → 건강 → 인생총운(평생사주)
SITE_ORDER = ("newyear", "romance", "intimate", "reunion", "wealth", "career", "business", "health", "lifetime")


def cross_sell(f: dict, current: str = "lifetime", site: str | None = None, first: list[str] | None = None) -> list[dict]:
    """다른 상품 안내. 사이트 카테고리 순서(신년운세→연애→재회→금전→건강→인생총운)로 두고 평생사주는 맨 끝.
    first는 예전 호출과 맞추려고 받기만 한다(2026-10-12 사장님 요청으로 순서를 바꾸지 않음)."""
    h = hooks(f)
    items = [{**p, "url": product_url(p["id"], site), "hook": h.get(p["id"], ""),
              "price_text": f"{p['price']:,}원", "original_text": f"{p['original']:,}원",
              "discount": discount_percent(p)} for p in PRODUCTS if p["id"] != current]
    items.sort(key=lambda p: SITE_ORDER.index(p["id"]))
    return items
