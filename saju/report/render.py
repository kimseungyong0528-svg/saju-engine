"""리포트 HTML을 만들고 PDF로 바꾼다."""

from __future__ import annotations

from pathlib import Path

import re

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from . import knowledge as K
from .outline import STATIC
from .products import cross_sell, taster_recap
from ..constants import STEMS, STEMS_HANJA, BRANCHES, BRANCHES_HANJA, ZODIAC_ANIMALS, ELEMENTS, STEM_ELEMENT

HERE = Path(__file__).parent
TEMPLATES = HERE / "templates"

EL_COLOR = {"목": "#4f7a4a", "화": "#b2452f", "토": "#b58b3c", "금": "#8c8a84", "수": "#2c3f5c"}


def _svg_element_cycle() -> str:
    import math
    cx, cy, r = 250, 190, 130
    pts = {}
    parts = ['<svg class="svg-fig" width="500" height="380" viewBox="0 0 500 380" xmlns="http://www.w3.org/2000/svg">',
             '<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0,0 L10,5 L0,10 z" fill="#3a2e22"/></marker>'
             '<marker id="ar2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0,0 L10,5 L0,10 z" fill="#9e2f22"/></marker></defs>']
    for i, el in enumerate(K.ELEMENT_ORDER):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        pts[el] = (cx + r * math.cos(a), cy + r * math.sin(a))

    def shorten(p, q, d=38):
        dx, dy = q[0] - p[0], q[1] - p[1]
        n = math.hypot(dx, dy)
        return p[0] + dx / n * d, p[1] + dy / n * d, q[0] - dx / n * d, q[1] - dy / n * d

    for a, b in K.GENERATES.items():
        x1, y1, x2, y2 = shorten(pts[a], pts[b])
        parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#3a2e22" stroke-width="2.5" marker-end="url(#ar)"/>')
    for a, b in K.CONTROLS.items():
        x1, y1, x2, y2 = shorten(pts[a], pts[b], 40)
        parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#9e2f22" stroke-width="1.8" stroke-dasharray="6 5" marker-end="url(#ar2)"/>')
    for el, (x, y) in pts.items():
        info = K.ELEMENT[el]
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="34" fill="{EL_COLOR[el]}"/>')
        parts.append(f'<text x="{x:.0f}" y="{y + 2:.0f}" text-anchor="middle" font-family="Song Myung, Noto Serif CJK KR" font-size="26" fill="#f6ecd8">{info["hanja"]}</text>')
        parts.append(f'<text x="{x:.0f}" y="{y + 25:.0f}" text-anchor="middle" font-family="Gowun Batang, Noto Serif CJK KR" font-size="16" fill="#f6ecd8">{info["name"]}</text>')
    parts.append('<line x1="40" y1="362" x2="80" y2="362" stroke="#3a2e22" stroke-width="2.5"/>'
                 '<text x="88" y="368" font-family="Gowun Batang, Noto Serif CJK KR" font-size="18.7" fill="#1f1b16">돕는 관계(상생)</text>'
                 '<line x1="270" y1="362" x2="310" y2="362" stroke="#9e2f22" stroke-width="2" stroke-dasharray="6 5"/>'
                 '<text x="318" y="368" font-family="Gowun Batang, Noto Serif CJK KR" font-size="18.7" fill="#1f1b16">누르는 관계(상극)</text>')
    parts.append("</svg>")
    return "".join(parts)


def _svg_strength(score: float) -> str:
    x = 30 + 440 * max(0, min(100, score)) / 100
    return ('<svg class="svg-fig" width="500" height="92" viewBox="0 0 500 92" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="30" y="34" width="440" height="18" fill="#e9dfc6" stroke="#b9a77f"/>'
            '<rect x="228" y="34" width="44" height="18" fill="#d3c5a3"/>'
            f'<polygon points="{x - 9:.0f},22 {x + 9:.0f},22 {x:.0f},36" fill="#9e2f22"/>'
            f'<text x="{x:.0f}" y="16" text-anchor="middle" font-family="Gowun Batang, Noto Serif CJK KR" font-size="18.7" fill="#9e2f22">{score:.0f}점</text>'
            '<text x="30" y="80" font-family="Gowun Batang, Noto Serif CJK KR" font-size="18.7" fill="#3d362c">신약</text>'
            '<text x="250" y="80" text-anchor="middle" font-family="Gowun Batang, Noto Serif CJK KR" font-size="18.7" fill="#3d362c">중화</text>'
            '<text x="470" y="80" text-anchor="end" font-family="Gowun Batang, Noto Serif CJK KR" font-size="18.7" fill="#3d362c">신강</text></svg>')


def _svg_life_graph(periods: list[dict], current: int) -> str:
    w, h, left, right, top, bottom = 620, 330, 60, 40, 30, 70
    n = len(periods)
    step = (w - left - right) / max(1, n - 1)
    def px(i): return left + i * step
    def py(s): return top + (90 - s) / 70 * (h - top - bottom)
    parts = [f'<svg class="svg-fig" width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for s in (30, 50, 70, 90):
        parts.append(f'<line x1="{left}" y1="{py(s):.0f}" x2="{w - right}" y2="{py(s):.0f}" stroke="#d3c5a3"/>'
                     f'<text x="{left - 8}" y="{py(s) + 6:.0f}" text-anchor="end" font-family="Gowun Batang, Noto Serif CJK KR" font-size="16" fill="#3d362c">{s}</text>')
    if 0 <= current < n:
        parts.append(f'<rect x="{px(current) - step / 2:.0f}" y="{top - 10}" width="{step:.0f}" height="{h - top - bottom + 10}" fill="#1f2a3d" opacity="0.12"/>')
    line = " ".join(f"{px(i):.0f},{py(p['score']):.0f}" for i, p in enumerate(periods))
    parts.append(f'<polyline points="{line}" fill="none" stroke="#9e2f22" stroke-width="3"/>')
    for i, p in enumerate(periods):
        parts.append(f'<circle cx="{px(i):.0f}" cy="{py(p["score"]):.0f}" r="6" fill="{"#1f2a3d" if i == current else "#9e2f22"}"/>')
        parts.append(f'<text x="{px(i):.0f}" y="{h - bottom + 26}" text-anchor="middle" font-family="Gowun Batang, Noto Serif CJK KR" font-size="16.5" fill="#1f1b16">{p["age_from"]}세</text>')
        parts.append(f'<text x="{px(i):.0f}" y="{h - bottom + 50}" text-anchor="middle" font-family="Song Myung, Noto Serif CJK KR" font-size="18" fill="#9e2f22">{p["hanja"]}</text>')
    parts.append("</svg>")
    return "".join(parts)


# 문장 중간에 붙은 이름표(예: "... 보세요. 보완법: ...")는 새 줄에서 시작하게 한다
_INLINE_LABEL = re.compile(r'(?<=[.!?"”’);])\s+([가-힣][가-힣 ]{0,9}):\s*')
_LEAD_LABEL = re.compile(r'^([^:<>]{1,24}):\s+')


_START_LABEL = re.compile(r'^([가-힣][가-힣 ]{0,7}):\s*')


def para(text: str) -> Markup:
    html = str(escape(text))
    html = _START_LABEL.sub(r'<b class="label">\1:</b> ', html, count=1)
    return Markup(_INLINE_LABEL.sub(r'<br><b class="label">\1:</b> ', html))


def bullet(text: str) -> Markup:
    """요약 줄 "제목: 설명"은 제목을 굵게, 설명은 다음 줄에."""
    html = str(escape(text))
    return Markup(_LEAD_LABEL.sub(r'<b>\1</b><br>', html, count=1))


def _kb() -> dict:
    return {
        "stems": [{"name": STEMS[i], "hanja": STEMS_HANJA[i], "el": ELEMENTS[STEM_ELEMENT[i]]} for i in range(10)],
        "branches": [{"name": BRANCHES[i], "hanja": BRANCHES_HANJA[i], "animal": ZODIAC_ANIMALS[i]} for i in range(12)],
        "stages": list(K.TWELVE_STAGE.items()),
        "relations": [(k, v) for k, v in K.RELATION.items() if k in ("천간합", "육합", "삼합", "충", "형", "파", "해", "원진")],
        "shinsal": list(K.SHINSAL.items()),
    }


def _used_glossary(f: dict) -> list[tuple[str, str]]:
    """부록 용어 사전: 기본 용어 + 이 사람 사주에 나온 십신·신살·격국만."""
    names = set(K.GLOSSARY) - set(K.SHINSAL) - set(K.GYEOKGUK) - set(K.TEN_GOD)
    for p in f["pillars"]:
        names.update(x for x in (p.get("stem_ten_god"), p.get("branch_ten_god")) if x in K.TEN_GOD)
        names.update(h["ten_god"] for h in p.get("hidden_stems") or [])
    names.update(f["shinsal_names"])
    names.add(f["gyeokguk"]["name"])
    return sorted((n, K.GLOSSARY[n]) for n in names if n in K.GLOSSARY)


# 표지(첫 장) 색: 사이트에서 각 사주 주인공(금월선녀)이 입은 옷 색을 따른다 (2026-10-11 Mr KIM 결정)
# line: 금색 선·글자, glow_in/glow_out: 바탕 그라데이션, dark/darker: 책 실·산·테두리 그림자, table: 여덟 글자 표 바탕
COVER = {
    "lifetime": {"outfit": "검정 바탕에 금색 무늬", "glow_in": "#3a3127", "glow_out": "#120f0c", "dark": "#080706", "darker": "#050403",
                 "line": "#d8bb78", "thread": "#e9dfc6", "table": "#1c1712", "text": "#efe3c8", "name": "#f6ecd8"},
    "romance": {"outfit": "연분홍", "glow_in": "#fbebe8", "glow_out": "#efc4be", "dark": "#c4847e", "darker": "#a8665f",
                "line": "#a07a34", "thread": "#7a4a45", "table": "#f3d2cd", "text": "#4a2b28", "name": "#3d2220"},
    "reunion": {"outfit": "남색", "glow_in": "#2c3b55", "glow_out": "#141c2a", "dark": "#111826", "darker": "#0b0f18",
                "line": "#d8bb78", "thread": "#e9dfc6", "table": "#172033", "text": "#e9dfc6", "name": "#f6ecd8"},
    "intimate": {"outfit": "진홍", "glow_in": "#8c2a2c", "glow_out": "#4a1012", "dark": "#2c0708", "darker": "#1d0405",
                 "line": "#d8bb78", "thread": "#f0dcc4", "table": "#3a0d0f", "text": "#f3e3cf", "name": "#f8ecd8"},
    # 2026-10-12 사이트 표지 그림과 맞춤: 재물·직업·사업은 master.jpg(금색 옷), 건강은 career-cover.jpg(초록 옷)
    "wealth": {"outfit": "금색", "glow_in": "#e9c56c", "glow_out": "#c4923a", "dark": "#8c6220", "darker": "#6e4c17",
               "line": "#6b4a16", "thread": "#5a3f14", "table": "#e3bd62", "text": "#2e210b", "name": "#2e210b"},
    "career": {"outfit": "금색", "glow_in": "#e9c56c", "glow_out": "#c4923a", "dark": "#8c6220", "darker": "#6e4c17",
               "line": "#6b4a16", "thread": "#5a3f14", "table": "#e3bd62", "text": "#2e210b", "name": "#2e210b"},
    "business": {"outfit": "금색", "glow_in": "#e9c56c", "glow_out": "#c4923a", "dark": "#8c6220", "darker": "#6e4c17",
               "line": "#6b4a16", "thread": "#5a3f14", "table": "#e3bd62", "text": "#2e210b", "name": "#2e210b"},
    "health": {"outfit": "초록", "glow_in": "#2f6a4a", "glow_out": "#123322", "dark": "#0a2014", "darker": "#06150d",
               "line": "#d8bb78", "thread": "#e9dfc6", "table": "#10291b", "text": "#ecdfc4", "name": "#f6ecd8"},
    # 2026-10-13 임시 색: 신년운세는 사이트 그림이 아직 없어 설빔 느낌의 짙은 다홍 바탕에 금색 선(그림이 정해지면 맞춘다)
    "newyear": {"outfit": "다홍(임시)", "glow_in": "#a8262b", "glow_out": "#5e0d12", "dark": "#3d070b", "darker": "#280407",
                "line": "#e2c173", "thread": "#f3dcae", "table": "#4c0a0f", "text": "#f6e6c6", "name": "#fbf0d9"},
}

# 상품마다 다른 표지 글자와 안내 문구(기본값은 평생사주)
PRODUCT = {
    "lifetime": {"id": "lifetime", "name": "평생사주", "cover_title": "平<br>生<br>四<br>柱",
                 "more_intro": "평생사주가 인생 전체의 지도였다면, 아래 리포트는 한 가지 주제를 훨씬 깊게 들여다보는 책이에요.",
                 "cover": COVER["lifetime"]},
    "romance": {"id": "romance", "name": "연애사주", "cover_title": "戀<br>愛<br>四<br>柱", "header": "戀愛四柱", "toc_compact": True,
                "more_intro": "연애사주가 나의 인연을 살펴본 책이었다면, 아래 리포트는 다른 주제를 깊게 들여다보는 책이에요.",
                "cover": COVER["romance"]},
    # 주제 사주(2026-10-11): 목차는 /mnt/project-files/plan/<id>-report-toc.md
    "reunion": {"id": "reunion", "name": "재회사주", "cover_title": "再<br>會<br>四<br>柱", "header": "再會四柱", "toc_compact": True,
                "more_intro": "재회사주가 두 사람의 다음 장을 살펴본 책이었다면, 아래 리포트는 다른 주제를 깊게 들여다보는 책이에요.",
                "cover": COVER["reunion"]},
    "intimate": {"id": "intimate", "name": "깊은 궁합", "cover_title": "宮<br>合", "header": "宮合", "toc_compact": True,
                 "more_intro": "깊은 궁합이 두 사람 사이를 살펴본 책이었다면, 아래 리포트는 다른 주제를 깊게 들여다보는 책이에요.",
                 "cover": COVER["intimate"]},
    "wealth": {"id": "wealth", "name": "재물운", "cover_title": "財<br>物<br>運", "header": "財物運", "toc_compact": True,
               "more_intro": "재물운이 돈의 흐름을 살펴본 책이었다면, 아래 리포트는 다른 주제를 깊게 들여다보는 책이에요.",
               "cover": COVER["wealth"]},
    "career": {"id": "career", "name": "직업·이직운", "cover_title": "職<br>業<br>運", "header": "職業運", "toc_compact": True,
               "more_intro": "직업·이직운이 나의 일을 살펴본 책이었다면, 아래 리포트는 다른 주제를 깊게 들여다보는 책이에요.",
               "cover": COVER["career"]},
    "business": {"id": "business", "name": "사업운", "cover_title": "事<br>業<br>運", "header": "事業運", "toc_compact": True,
                 "more_intro": "사업운이 내가 키우는 일을 살펴본 책이었다면, 아래 리포트는 다른 주제를 깊게 들여다보는 책이에요.",
                 "cover": COVER["business"]},
    "health": {"id": "health", "name": "건강운", "cover_title": "健<br>康<br>運", "header": "健康運", "toc_compact": True,
               "more_intro": "건강운이 나의 생활 리듬을 살펴본 책이었다면, 아래 리포트는 다른 주제를 깊게 들여다보는 책이에요.",
               "cover": COVER["health"]},
    # 표지 이름표 아래 글자는 한 줄(4자 안팎)이어야 도장과 겹치지 않는다: 해(2027·丁未年)는 머리글과 본문에 둔다
    "newyear": {"id": "newyear", "name": "2027 신년운세", "cover_sub": "신년운세", "cover_title": "新<br>年<br>運<br>勢", "header": "丁未年 新年運勢", "toc_compact": True,
                "more_intro": "신년운세가 2027년 한 해를 살펴본 책이었다면, 아래 리포트는 한 가지 주제를 훨씬 깊게 들여다보는 책이에요.",
                "cover": COVER["newyear"]},
}


def _svg_love_graph(periods: list[dict], current: int) -> str:
    """대운별 인연 점수 그래프(연애사주)."""
    return _svg_life_graph([dict(p, score=min(90, p["love_score"])) for p in periods], current)


def render_html(facts: dict, sections: list[dict], texts: dict, site_url: str | None = None,
                product: str = "lifetime", static: dict | None = None, first: list[str] | None = None) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]))
    env.filters["para"] = para
    env.filters["bullet"] = bullet
    env.filters["ord"] = ord
    tpl = env.get_template("report.html.j2")
    svg = {"element_cycle": _svg_element_cycle(), "strength": _svg_strength(facts["strength"]["score"]),
           "life_graph": _svg_life_graph(facts["daewoon"]["periods"], facts["daewoon"]["current_index"])}
    if facts.get("romance"):
        svg["love_graph"] = _svg_love_graph(facts["romance"]["periods"], facts["daewoon"]["current_index"])
    if facts.get("theme", {}).get("periods"):
        from .theme import near
        svg["theme_graph"] = _svg_life_graph([dict(p, score=min(90, p["t_score"])) for p in near(facts, facts["theme"]["periods"], 100)],
                                             facts["daewoon"]["current_index"])
    recap = None
    if facts.get("taster_view"):
        # 책 맨 끝 '더보기' 앞쪽에 보너스로 6가지 핵심운(좋은 운 3·조심할 운 3)을 넣는다(목차 줄은 그대로).
        recap = taster_recap(facts["taster_view"], product, site_url, (facts.get("rebuy") or {}).get("code"), facts.get("owned") or ())
        sections = [dict(sec, pages=[{"id": "recap", "title": "보너스 · 무료 풀이의 좋은 운과 조심할 운", "figure": "taster_recap",
                                       "slot": None, "static": None, "span": 2, "opener": True},
                                      *[dict(pg, opener=False) for pg in sec["pages"]]])
                    if sec.get("no") == "더보기" else sec for sec in sections]
    return tpl.render(
        f=facts, sections=sections, recap=recap, texts=texts, static=static or STATIC, kb=_kb(),
        more=cross_sell(facts, current=product, site=site_url, first=first, coupon=(facts.get("rebuy") or {}).get("code")), secmark={"더보기": "續"},
        glossary=K.GLOSSARY, glossary_sorted=_used_glossary(facts), product=PRODUCT[product],
        svg=svg,
    )


def render_pdf(html: str, out_path: str | Path) -> int:
    """PDF를 쓰고 쪽수를 돌려준다."""
    from weasyprint import HTML
    doc = HTML(string=html, base_url=str(TEMPLATES) + "/").render()
    doc.write_pdf(str(out_path))
    return len(doc.pages)
