"""리포트 끝에 넣는 다른 상품 안내.

순서와 이름, 소개 문구, 판매가·정가는 운명서재 화면(unmyeong-preview-v32.html의 PRODUCTS)과 같다.
링크는 화면의 상품 소개 주소 형식(#/f/{id}/intro)을 따른다. 사이트 주소는 SAJU_SITE_URL로 정한다.
"""

from __future__ import annotations

from ..taster import ieyo
import os

SITE_URL = os.environ.get("SAJU_SITE_URL", "https://unmyeong-saju.com").rstrip("/")

PRODUCTS = [
    {"id": "newyear", "name": "금월선녀의 2027 신년운세", "category": "운세/평생운", "price": 29800, "original": 55000,
     "line": "2027년, 나에게 어떤 해가 될까요"},
    {"id": "lifetime", "name": "금월선녀의 평생사주", "category": "운세/평생운", "price": 49800, "original": 110000,
     "line": "지나온 나를 이해하고 앞으로의 길을 만나다"},
    {"id": "romance", "name": "금월선녀의 연애사주", "category": "연애/재회", "price": 29800, "original": 55000,
     "line": "다음 사랑은 어떤 모습으로 올까요"},
    {"id": "reunion", "name": "금월선녀의 재회사주", "category": "연애/재회", "price": 29800, "original": 55000,
     "line": "끝나지 않은 마음, 다시 이어질 수 있을까"},
    {"id": "intimate", "name": "금월선녀의 깊은 궁합", "category": "연애/재회", "price": 29800, "original": 55000,
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


def product_url(pid: str, site: str | None = None, coupon: str | None = None) -> str:
    """coupon이 있으면 재구매 할인 링크(?coupon=)로 만든다. 이 링크로 들어가야만 10% 할인된다(2026-10-27 사장님)."""
    query = f"?coupon={coupon}" if coupon else ""
    return f"{(site or SITE_URL).rstrip('/')}/{query}#/f/{pid}/intro"


def _count(f: dict, group: str) -> int:
    return next(g["n"] for g in f["ten_god_groups"] if g["group"] == group)


EL_WORD = {"목": "나무", "화": "불", "토": "흙", "금": "쇠", "수": "물"}


def _screen(f: dict):
    """결제 전 화면과 같은 계산(saju/reveal.py)에 쓰는 사주와 성별. facts의 첫 번째 명식에서 되돌린다."""
    from ..constants import BRANCHES, STEMS
    from ..pillars import FourPillars, Pillar
    ps = [None if k == "??" else Pillar(STEMS.index(k[0]), BRANCHES.index(k[1])) for k in f["variants"][0].split()]
    return FourPillars(*ps), f["person"]["sex"]


def _first_good(f: dict, pid: str, current: str = "") -> tuple[str, str] | None:
    """그 상품의 결제 전 12년 지도에서 처음 나오는 좋은 해와 그 해의 설명(화면 문장 그대로). 제1조항: 화면과 다른 해를 말하지 않는다.
    current: 지금 읽는 책. 그 책의 지도에서 조심할 표시가 있는 해는 고르지 않는다
    (손님 테스트 3차: 평생사주 지도는 2034년이 '큰 변화'인데 직업운 안내가 '2034년은 자리의 별'이라고 했다)."""
    from .. import reveal as RV
    from ..taster import fill, texts
    fp, sex = _screen(f)
    marks = texts()["REVEAL"]["MARKS"]
    own = {c["label"] for c in RV.luck_map(fp, sex, current)["cells"] if c["bad"]} if current in texts()["REVEAL"]["PRODUCTS"] and current != pid else set()
    for c in RV.luck_map(fp, sex, pid)["cells"]:
        keys = [k for k in c["good"] if not k.startswith("ny_")]
        if keys and c["label"] not in own:
            return c["label"], fill(marks[keys[0]]["line"], {"name": f["person"]["name"]})
    return None


def _weak_strong(f: dict) -> tuple[str, str]:
    """결제 전 화면 '이거 맞죠?'와 같은 가장 모자란 기운·가장 센 기운."""
    from .. import analysis as A
    from .. import reveal as RV
    fp, _ = _screen(f)
    el = A.element_strength(fp)
    strong = sorted(RV.ELEMENTS, key=lambda e: -el[e])[0]
    return EL_WORD[RV._weakest(el)], EL_WORD[strong]


def hooks(f: dict, current: str = "") -> dict[str, str]:
    """상품마다 이 사람 사주에 맞춘 한두 문장(계산값만 사용).
    해·기운은 결제 전 화면과 같은 계산에서 가져온다(제1조항). 원국에 없는 별은 '태어날 때 받은 여덟 글자 안에는'으로, 해마다 오는 별은 '바깥에서 들어오는'으로 쓴다."""
    name = f["person"]["name"]
    male = f["person"]["sex"] == "male"
    spouse_group = "재성" if male else "관성"
    n_spouse = _count(f, spouse_group)
    dm = f["day_master"]
    peach = [s for s in f["shinsal_names"] if s in ("도화살", "홍염살")]
    weak, strong = _weak_strong(f)
    year_line = lambda pid, tail: (lambda g: f"{g[0]}년은 {g[1]}예요. " if g else tail)(_first_good(f, pid, current))
    return {
        "lifetime": (f"{name} 님의 일간은 {dm['stem']}({dm['element_name']})이고 사주의 틀은 {ieyo(f['gyeokguk']['name'])}. "
                     "성격, 일, 돈, 연애, 건강과 앞으로의 10년 운, 연도별·월별 운세까지 인생 전체를 15장, 100쪽이 넘는 한 권으로 풀어 드려요. 다른 리포트가 한 가지 주제를 깊게 본다면, 평생사주는 모든 주제를 함께 봐요."),
        "romance": ((f"태어날 때 받은 {name} 님의 여덟 글자 안에 배우자를 뜻하는 {spouse_group}이 {n_spouse}개 있어요. " if n_spouse
                     else f"태어날 때 받은 {name} 님의 여덟 글자 안에는 배우자를 뜻하는 {spouse_group}이 없어서, 인연은 바깥에서 들어오는 해를 잡는 것이 중요해요. ")
                    + (f"{', '.join(peach)}도 있어 사람을 끌어당기는 힘이 있어요. " if peach else "")
                    + year_line("romance", "")
                    + "어떤 사람이 언제, 어떻게 오는지 달 단위로 알려 드려요."),
        "reunion": (f"헤어진 사람의 사주를 {name} 님 사주와 나란히 놓고, 두 사람이 다시 이어질 수 있는지 봐요. "
                    "앞으로 24개월 가운데 연락하기 좋은 달과 피해야 할 달, 먼저 다가갈지 기다릴지까지 정리해 드려요."),
        "intimate": (f"{name} 님은 {dm['element_name']}의 기운을 타고났고, 가장 모자란 기운은 {ieyo(weak)}. "
                     "상대방이 그 기운을 채워 주는 사람인지, 어디서 부딪히는지 두 사람의 오행을 비교해 알려 드려요."),
        "wealth": ((f"태어날 때 받은 {name} 님의 여덟 글자 안에 재물을 뜻하는 재성이 {_count(f, '재성')}개 있어요. " if _count(f, "재성")
                    else f"태어날 때 받은 {name} 님의 여덟 글자 안에는 재물을 뜻하는 재성이 없어서, 재물이 바깥에서 들어오는 해를 아는 것이 특히 중요해요. ")
                   + year_line("wealth", "")
                   + "돈이 들어오는 해와 새는 해, 나에게 맞는 돈 모으는 방법을 해마다 짚어 드려요."),
        "career": (f"{name} 님의 사주 틀은 {ieyo(f['gyeokguk']['name'])}. "
                   + year_line("career", "")
                   + "맞는 직무와 이직·승진에 좋은 시기를 연도와 달까지 알려 드려요."),
        "business": (f"사업은 나 자신(비겁 {_count(f, '비겁')}개), 표현과 재능(식상 {_count(f, '식상')}개), 재물(재성 {_count(f, '재성')}개)의 균형으로 봐요. "
                     + year_line("business", "")
                     + "혼자 할지 함께 할지, 언제 확장하고 언제 지켜야 할지 정리해 드려요."),
        "health": (f"{name} 님은 {strong} 기운이 가장 세고, {weak} 기운이 가장 모자라요. "
                   "이 균형에 맞는 생활 리듬, 잠과 휴식, 계절별 돌봄 습관을 한 주 실천표로 드려요."),
        "newyear": _newyear_hook(f),
    }


def _newyear_hook(f: dict) -> str:
    from .newyear import hook
    return hook(f)


# 사이트 카테고리 탭 순서: 신년운세(2026-10-13 맨 위 배너) → 연애(연애사주, 깊은 궁합) → 재회 → 금전(재물·직업·사업) → 건강 → 인생총운(평생사주)
SITE_ORDER = ("newyear", "romance", "intimate", "reunion", "wealth", "career", "business", "health", "lifetime")


def cross_sell(f: dict, current: str = "lifetime", site: str | None = None, first: list[str] | None = None,
               coupon: str | None = None) -> list[dict]:
    """다른 상품 안내. 사이트 카테고리 순서(신년운세→연애→재회→금전→건강→인생총운)로 두고 평생사주는 맨 끝.
    first는 예전 호출과 맞추려고 받기만 한다(2026-10-12 사장님 요청으로 순서를 바꾸지 않음)."""
    h = hooks(f, current)
    # 결혼했거나 연애 중인 손님(깊은 궁합을 산 손님 포함)에게 '다음 사랑'·'헤어진 인연' 책은 권하지 않는다(손님 테스트 3차: 결혼 35주년 선물 책 끝에 '다음 사랑은…')
    rel = str((f.get("order") or {}).get("relationship") or "")
    coupled = current == "intimate" or any(w in rel for w in ("결혼했", "연애하고", "연애 중", "결혼"))
    items = [{**p, "url": product_url(p["id"], site, coupon), "hook": h.get(p["id"], ""),
              "price_text": f"{p['price']:,}원", "original_text": f"{p['original']:,}원",
              "discount": discount_percent(p),
              # 재구매 링크로 들어가면 서버(discounts.mjs)가 10%를 더 깎는다. 같은 계산(반올림)으로 보여 준다.
              "rebuy_text": f"{round(p['price'] * 0.9):,}원" if coupon else None} for p in PRODUCTS
             if p["id"] != current and p["id"] not in (f.get("owned") or [])   # 같은 주문에서 함께 산 상품은 다시 권하지 않는다
             and not (coupled and p["id"] in ("romance", "reunion"))]
    items.sort(key=lambda p: SITE_ORDER.index(p["id"]))
    return items


def taster_recap(view: dict, current: str, site: str | None = None, coupon: str | None = None, owned=(), answers=()) -> dict:
    """리포트 끝 '무료 분석에서 본 나의 좋은 운과 조심할 운' (2026-10-27 사장님 요청).
    무료 분석과 같은 계산(saju/taster.py)의 6가지를 다시 짚고, 운마다 그 운을 깊게 다룬 리포트로 잇는다."""
    names = {p["id"]: p["name"].replace("금월선녀의 ", "") for p in PRODUCTS}
    def item(kind: str, n: int, a: dict) -> dict:
        pid = a["product"]
        from ..taster import situation_note
        note = situation_note(a["id"], answers)   # 결제 전 화면 카드와 같은 '지금 상황' 한 줄
        return {"kind": kind, "rank": n, "title": a["title"], "score": a["score"], "text": a["text"] + (" " + note if note else ""), "hook": a["hook"], "product": pid,
                "product_name": names.get(pid, ""), "url": product_url(pid, site, coupon), "here": pid == current,
                "owned": pid != current and pid in owned}   # 같은 주문에서 함께 받은 리포트
    return {"good": [item("good", n, a) for n, a in enumerate(view["good"], 1)],
            "bad": [item("bad", n, a) for n, a in enumerate(view["bad"], 1)]}
