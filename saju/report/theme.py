"""주제 사주(재회·깊은 궁합·재물·직업·사업·건강)가 같이 쓰는 도구.

평생사주 모듈은 이 파일을 쓰지 않는다. 연애사주는 screen_years·reveal_fix만 같이 쓴다(제1조항).
상품 모듈은 build(f, result, answers, partner) → f["theme"]를 만들고, 그 안에
label(AI에게 보낼 재료 이름), digest(AI에게 보낼 값), periods(대운별 t_score, 그래프용)를 둔다.
"""

from __future__ import annotations

from . import knowledge as K
from .outline import page
from ..constants import BRANCHES, STEMS
from ..pillars import FourPillars, Pillar

GODS = {"비겁": {"비견", "겁재"}, "식상": {"식신", "상관"}, "재성": {"편재", "정재"},
        "관성": {"편관", "정관"}, "인성": {"편인", "정인"}}
GROUP_WORD = {"비겁": "비겁(나·동료)", "식상": "식상(표현·재능)", "재성": "재성(재물)", "관성": "관성(직장·명예)", "인성": "인성(배움·도움)"}

# 지지 삼합 무리마다 정해진 글자(역마·도화)
YEOKMA = {"인": "신", "오": "신", "술": "신", "신": "인", "자": "인", "진": "인",
          "사": "해", "유": "해", "축": "해", "해": "사", "묘": "사", "미": "사"}
PEACH = {"인": "묘", "오": "묘", "술": "묘", "신": "유", "자": "유", "진": "유",
         "사": "오", "유": "오", "축": "오", "해": "자", "묘": "자", "미": "자"}


def count(f: dict, group: str) -> int:
    return next(g["n"] for g in f["ten_god_groups"] if g["group"] == group)


def has(x: dict, group: str) -> bool:
    """운(대운·세운·월운)의 글자에 그 십신 무리가 들어오는지."""
    gods = GODS[group]
    return x["stem_ten_god"] in gods or x["branch_ten_god"] in gods


def rel(x: dict, pillar: str, kinds: tuple[str, ...]) -> bool:
    """운의 지지가 원국의 그 기둥과 kinds 관계인지(예: ('충',), ('육합','삼합','반합'))."""
    return any(r.get("with") == pillar and r.get("level") == "지지" and K.relation_kind(r["type"]) in kinds
               for r in x.get("relations", []))


HAP = ("육합", "삼합", "반합")
CLASH = ("충",)


def clamp(v: float) -> int:
    return max(20, min(95, round(v)))


def marked(f: dict, fn) -> tuple[list[dict], list[dict], list[dict]]:
    """세운 5년, 월운 12달, 대운 전체에 상품별 표시(fn)를 붙인다. fn(x) → {t_score, t_signs, ...}

    주문한 해는 이미 지난 달이 있으므로, 해 점수와 남은 달 점수의 평균을 반씩 섞는다
    (해는 '좋은 해'인데 남은 달이 모두 낮게 나오는 어긋남을 막는다)."""
    years = [dict(s, **fn(s)) for s in screen_years(f)]
    months = [dict(m, **fn(m)) for m in f["months"]]
    periods = [dict(p, **fn(p)) for p in f["daewoon"]["periods"]]
    blend_current_year(years, months)
    return years, months, periods


def screen_years(f: dict) -> list[dict]:
    """결제 전 이야기 화면의 12년 지도와 같은 해(2027년 또는 주문한 해부터 12년). 제1조항: 화면과 리포트가 같은 해를 본다."""
    from ..reveal import start_year
    first = start_year(int(f["order"]["date"][:4]))
    return [s for s in f["sewoon_all"] if s["year"] >= first][:12]


def reveal_fix(result: dict, product: str, rows: list[dict], score: str = "t_score", signs: str = "t_signs",
               replace: bool = True) -> None:
    """제1조항(모순 금지): 해·달마다 결제 전 이야기 화면과 같은 규칙(saju/reveal.py)의 좋은 표시·조심할 표시를 붙이고,
    점수와 표시가 화면과 반대로 읽히지 않게 맞춘다.
    좋은 표시만 있으면 60점 이상, 조심할 표시만 있으면 40점 이하, 둘 다 있으면 45~55점, 둘 다 없으면 41~59점.
    replace=True면 표의 '표시' 칸을 화면에 나온 말(예: '돈의 별', '돈이 샘')로 바꾼다."""
    from .. import reveal as RV
    from ..taster import texts
    sex = result["person"].get("sex", "")
    conf = texts()["REVEAL"]["PRODUCTS"][product]
    marks = texts()["REVEAL"]["MARKS"]
    fp = fourpillars(result)
    _, rule_of = RV._marker(fp, sex)
    # 2027년 달: 신년운세 결제 전 화면(2027년 12달 지도)에서 '조심할 달'인 달은 다른 책에서도 좋은 달로 쓰지 않는다
    # (손님 테스트 3차: 묶음으로 산 사업운은 2027년 4월이 '큰돈', 신년운세는 4월이 '조심할 달'이었다).
    # 반대 방향도 같다: 신년운세 화면에서 '돕는 달'인 2027년 달은 다른 책에서도 조심할 달로 쓰지 않는다(손님 테스트 4차).
    ny_cells = RV.luck_map(fp, sex, "newyear")["cells"] if product != "newyear" else []
    ny_bad = {c["ko"] for c in ny_cells if c["bad"]}
    ny_good = {c["ko"] for c in ny_cells if c["good"]}
    from .facts import NY_AREA
    area = NY_AREA.get(product)
    for r in rows:
        gz = r["ganzhi"]
        p = {"stem": STEMS.index(gz[0]), "branch": BRANCHES.index(gz[1])}
        label = str(r["year"]) if "month" not in r and "year" in r else ""
        gk, bk = RV.year_marks(fp, sex, product, label, [RV._mark_key(k, sex) for k in conf["good"] if rule_of(k)(p)],
                               [RV._mark_key(k, sex) for k in conf["bad"] if rule_of(k)(p)])
        if "month" in r and r.get("year") == 2027 and gz in ny_bad:
            gk = []
        if "month" in r and r.get("year") == 2027 and gz in ny_good:
            bk = []
        good, bad = [marks[k]["tag"] for k in gk], [marks[k]["tag"] for k in bk]
        ny_area = (r.get("ny_areas") or {}).get(area) if area and "month" in r else None
        if ny_area is not None:
            # 신년운세 책의 같은 분야, 같은 달과 표시·점수를 그대로 쓴다(제1조항: 묶음으로 산 두 책이 같은 달을 다르게 말하지 않게)
            good, bad = list(ny_area["good"]), list(ny_area["bad"])
        r["r_good"], r["r_bad"] = good, bad
        raw = [marks[RV._mark_key(k, sex)]["tag"] for k in conf["good"] if rule_of(k)(p)]
        if label == "2027" and bad and raw:
            # 2027년 칸은 한 해 전체 운(맛보기 '2027년 운')을 따라 조심으로 표시한다. 그해에 들어오는 좋은 별은 이 줄로 함께 알려 준다(손님 테스트 3차).
            r["ny_note"] = f"2027년에는 {'·'.join(dict.fromkeys(raw))}도 들어오지만, 한 해 전체 운이 조심할 쪽이라 지도에 '조심'으로 표시했어요."
        raw_bad = [marks[RV._mark_key(k, sex)]["tag"] for k in conf["bad"] if rule_of(k)(p)]
        if label == "2027" and good and not bad and raw_bad:
            r["ny_also_bad"] = list(dict.fromkeys(raw_bad))
            r["ny_note"] = f"2027년에는 {'·'.join(dict.fromkeys(raw_bad))}도 들어오지만, 한 해 전체 운이 좋은 쪽이라 지도에 좋은 표시를 했어요. 이 부분은 조심하세요."
        v = r[score]
        if ny_area is not None:
            v = ny_area["score"]
        elif label == "2027" and (product == "lifetime" or all(k.startswith("ny_") for k in gk + bk)):
            # 맛보기 '2027년 운' 점수 그대로. 다른 상품도 2027년 칸에 그 상품의 표시가 없고 '2027년 좋은 흐름·조심'만 있으면 같은 점수
            # (손님 테스트 3차: 건강운 12년 표 2027년 60점, 보너스·신년운세 58점)
            v = RV.ny_verdict(fp, sex)[1]
        else:
            v = max(v, 60) if good and not bad else min(v, 40) if bad and not good else min(max(v, 45), 55) if good else min(max(v, 41), 59)
        r[score] = v
        r.setdefault("raw_signs", list(r.get(signs, [])))   # 화면 말로 바꾸기 전 이 상품 계산의 표시(직업운 '일 자리 변동'처럼 화면에 없는 표시를 찾을 때)
        r[signs] = good + bad if replace else list(dict.fromkeys(good + bad + [x for x in r[signs]]))


def none_text(rows: list[dict], what: str) -> str:
    """'몸 조심할 해'처럼 목록이 비었을 때 쓰는 말. 2027년 칸이 한 해 전체 운을 따라 좋은 표시가 됐지만 그해에 조심 기운도 들어오면
    그 사실을 함께 적는다(손님 테스트 4차: 8쪽은 '뚜렷하지 않아요', 12년 표 아래 줄은 '2027년에는 몸 조심도 들어와요')."""
    also = next((r["ny_also_bad"] for r in rows if r.get("ny_also_bad")), None)
    if also:
        return f"지도에 {what} 표시가 붙은 해는 없어요. 다만 2027년에는 {'·'.join(also)}도 함께 들어와요(12년 표 아래 설명)."
    return "앞으로 12년 안에는 뚜렷하지 않아요"


def _own(tags) -> bool:
    """이 상품의 표시가 있는지. '2027년 좋은 흐름'·'2027년 조심'(한 해 전체 운 표시)만 있는 칸은 '기운 채움 해'·'돈이 샘 해' 같은
    상품 목록에 넣지 않는다(손님 테스트 3차: 화면은 2027년을 따로 보여 주는데 PDF 요약표가 '기운 채움 해 2027년'으로 묶었다)."""
    from ..taster import texts
    m = texts()["REVEAL"]["MARKS"]
    return bool(set(tags or ()) - {m["ny_good"]["tag"], m["ny_bad"]["tag"]})


def good_rows(rows: list[dict], n: int, label, score: str = "t_score") -> list:
    """화면에서 좋은 표시가 붙은 해·달 가운데 점수 높은 n개(시간 순)."""
    top = sorted([r for r in rows if _own(r.get("r_good"))], key=lambda r: -r[score])[:n]
    return [label(r) for r in rows if r in top]


def near_good_rows(rows: list[dict], n: int, label) -> list:
    """'가까운 좋은 달': 화면과 같은 좋은 표시가 붙은 달 가운데 지금부터 가까운 n개(손님 테스트 3차: 점수 순으로 골라 더 가까운 달이 빠졌다)."""
    return [label(r) for r in rows if _own(r.get("r_good"))][:n]


def bad_rows(rows: list[dict], n: int, label, score: str = "t_score") -> list:
    """화면에서 조심할 표시가 붙은 해·달 가운데 점수 낮은 n개(시간 순)."""
    low = sorted([r for r in rows if _own(r.get("r_bad"))], key=lambda r: r[score])[:n]
    return [label(r) for r in rows if r in low]


def blend_current_year(years: list[dict], months: list[dict], key: str = "t_score") -> None:
    if not years:
        return
    if months and years[0]["year"] != months[0]["year"]:
        return   # 표의 첫 해가 주문한 해가 아니면(화면과 같은 2027년부터) 섞지 않는다
    rest = [m[key] for m in months if m["year"] == years[0]["year"]]
    if rest:
        years[0][key] = clamp((years[0][key] + sum(rest) / len(rest)) / 2)
        years[0]["rest_months"] = len(rest)


def near(f: dict, periods: list[dict], span: int = 40, cap: int = 80) -> list[dict]:
    """의미 있는 대운만: 지난 대운은 두고, 앞으로의 대운은 '지금 나이 + span'과 cap 가운데 이른 나이 안에서 시작하는 것만."""
    limit = min(cap, f["person"]["age"] + span)
    return [p for p in periods if p["state"] == "지난" or p["age_from"] <= max(limit, f["person"]["age"])]


def best(rows: list[dict], n: int, label) -> list[str]:
    """점수가 높은 n개를 원래 순서(시간 순)대로."""
    if rows and "r_good" in rows[0]:
        return good_rows(rows, n, label)   # 화면에서 좋은 표시가 있는 것만(없으면 빈 목록: 화면에 없는 '좋은 해'를 만들지 않는다)
    top = sorted(rows, key=lambda r: -r["t_score"])[:n]
    return [label(r) for r in rows if r in top]


def worst(rows: list[dict], n: int, label, limit: int = 40) -> list[str]:
    if rows and "r_bad" in rows[0]:
        return bad_rows(rows, n, label)   # 화면과 같은 규칙이 붙어 있으면 화면에서 조심할 표시가 있는 것만
    low = [r for r in sorted(rows, key=lambda r: r["t_score"]) if r["t_score"] <= limit or "충" in " ".join(r["t_signs"])][:n]
    return [label(r) for r in rows if r in low]


def ym(m: dict) -> str:
    return f"{m['year']}년 {m['month']}월"


def digest_rows(years: list[dict], months: list[dict], periods: list[dict]) -> dict:
    keep = ("t_score", "t_signs", "score")
    return {
        "연도별": [{"year": y["year"], "ganzhi": y["ganzhi"], **{k: y[k] for k in keep}} for y in years],
        "달별": [{"start_text": m["start_text"], "ganzhi": m["ganzhi"], **{k: m[k] for k in keep}} for m in months],
        "대운별": [{"age_text": p["age_text"], "years_text": p["years_text"], "ganzhi": p["ganzhi"], "state": p["state"],
                   **{k: p[k] for k in keep}} for p in periods],
        "점수 읽는 법": f"연도별 첫 해({years[0]['year']}년)의 t_score는 이미 지난 달을 빼고, 해 점수와 남은 달 점수를 반씩 섞은 값이에요. "
                     "올해 이야기는 남은 달의 점수와 함께 씁니다. 대운별은 의미 있는 나이까지만 실었어요." if years else "",
    }


def year_grid(years: list[dict], best_years: list[int], head: str = "점수") -> dict:
    return {"head": ["해", "간지", "표시", head],
            "rows": [[str(y["year"]), f"{y['hanja']} {y['ganzhi']}", ", ".join(y["t_signs"]) or "—", f"{y['t_score']}점"] for y in years],
            "hl": [i for i, y in enumerate(years) if y["year"] in best_years], "left": [2], "widths": ["13%", "20%", "47%", "20%"],
            "notes": [y["ny_note"] for y in years if y.get("ny_note")]}


def month_grid(months: list[dict], head: str = "점수") -> dict:
    return {"head": ["달", "간지", "표시", head],
            "rows": [[f"{m['year']}.{m['month']}", m["hanja"], ", ".join(m["t_signs"]) or "—", str(m["t_score"])] for m in months],
            "hl": [i for i, m in enumerate(months) if m["t_score"] >= 70], "left": [2], "widths": ["16%", "14%", "50%", "20%"]}


def period_grid(periods: list[dict], head: str = "점수") -> dict:
    rows = [p for p in periods if p["state"] != "지난"]
    return {"head": ["나이", "해", "대운", "표시", head],
            "rows": [[p["age_text"], p["years_text"], p["hanja"], ", ".join(p["t_signs"]) or "—", f"{p['t_score']}점"] for p in rows],
            "hl": [i for i, p in enumerate(rows) if p["t_score"] >= 65], "left": [3]}


def tpage(pid: str, title: str, *, rows: list | None = None, grid: dict | None = None, note: str = "", **kw) -> dict:
    """표(rows: [제목, 내용] 목록, grid: 머리줄과 줄들)를 함께 싣는 쪽."""
    p = page(pid, title, **kw)
    if rows is not None:
        p["rows"] = rows
    if grid is not None:
        p["grid"] = grid
    if note:
        p["note"] = note
    return p


def fourpillars(result: dict) -> FourPillars:
    """analyze_person 결과(첫 후보)를 계산용 FourPillars로 되돌린다."""
    ps = []
    for p in result["variants"][0]["analysis"]["pillars"]:
        ps.append(None if p.get("unknown") else Pillar(STEMS.index(p["stem"]), BRANCHES.index(p["branch"])))
    return FourPillars(*ps)


def chart_brief(f: dict) -> dict:
    """상대방 사주를 AI에게 보낼 때 쓰는 요약."""
    return {
        "이름": f["person"]["name"], "성별": f["person"]["sex_word"], "나이": f["person"]["age"], "띠": f["person"]["zodiac"],
        "사주표": [{k: p.get(k) for k in ("label", "ganzhi", "stem_ten_god", "branch_ten_god")} for p in f["pillars"]],
        "일간": {k: f["day_master"][k] for k in ("stem", "element", "image", "basic", "strengths", "weaknesses")},
        "오행": [{k: e[k] for k in ("name", "pct", "status")} for e in f["elements"]],
        "십신 무리": {g["group"]: g["n"] for g in f["ten_god_groups"]},
        "신강약": f["strength"]["label"], "격국": f["gyeokguk"]["name"], "도움 되는 기운": f["lucky"]["element_name"],
        "신살": f["shinsal_names"],
    }


def style(product_name: str, extra: str) -> str:
    """평생사주 글쓰기 규칙을 바탕으로 상품 규칙을 더한다."""
    from .writer import STYLE_RULES
    return STYLE_RULES.replace("사주 리포트 '평생사주'", f"사주 리포트 '{product_name}'").replace(
        "- 물상 그림은 한 장에 한두 번만 씁니다. 고전 이름(자평진전, 적천수)은 2장의 '사주의 뼈대와 흐름' 쪽에서만 소개합니다.",
        "- 물상 그림은 한 장에 한두 번만 씁니다. 고전 이름(자평진전, 적천수)은 쓰지 않습니다.") + extra


def against(ganzhi: str, stem: str | None, branch: str | None) -> list[str]:
    """운의 간지(예: '병오')가 다른 사람의 글자(일간·일지)와 맺는 관계 종류. 예: ['천간합', '육합']"""
    from ..analysis import branch_relation, stem_relation
    out = []
    if stem:
        out += [K.relation_kind(r) for r in stem_relation(STEMS.index(ganzhi[0]), STEMS.index(stem))]
    if branch:
        out += [K.relation_kind(r) for r in branch_relation(BRANCHES.index(ganzhi[1]), BRANCHES.index(branch))]
    return out


def day_of(f: dict) -> dict:
    return next(p for p in f["pillars"] if p["pillar"] == "일주")


def god_count(f: dict, god: str) -> int:
    """원국 천간·지지에 보이는 그 십신의 개수(숨은 글자 제외)."""
    return sum((p.get("stem_ten_god") == god) + (p.get("branch_ten_god") == god) for p in f["pillars"] if not p.get("unknown"))


def seats(f: dict, group: str) -> list[str]:
    """그 십신 무리가 놓인 자리. 예: ['태어난 달 지지', '태어난 시간 숨은 글자']"""
    gods = GODS[group]
    out = []
    for p in f["pillars"]:
        if p.get("unknown"):
            continue
        out += [f"{p['label']} {w}" for w, g in (("천간", p["stem_ten_god"]), ("지지", p["branch_ten_god"])) if g in gods]
        if not any(g in gods for g in (p["stem_ten_god"], p["branch_ten_god"])) and any(h["ten_god"] in gods for h in p["hidden_stems"]):
            out.append(f"{p['label']} 숨은 글자")
    return out


def screen_score(f: dict, result: dict, product: str) -> dict:
    """결제 전 이야기 화면 '내 점수'에서 고객이 본 점수(전체·좋은 점·조심할 점). 리포트 첫 요약에 그대로 싣는다(제1조항)."""
    from .. import reveal as RV
    d = RV.digest(fourpillars(result), f["person"]["name"], result["person"].get("sex", ""), product,
                  f["order"]["date"], f["order"].get("reveal_start", ""))["화면에서 본 점수"]
    return {"score": d["전체 점수"], "good": d["좋은 점"]["점수"], "bad": d["조심할 점"]["점수"]}


def screen_row(s: dict, seen: bool = True) -> list[str]:
    """첫 요약의 점수 줄. 묶음으로 산 상품은 결제 전 화면을 보지 않았으므로 '결제 전에 보신'이라고 쓰지 않는다."""
    # 무료 풀이를 안 본 손님도 있으므로 '전체 점수'라고만 쓴다(결제 전 화면 STEP 3과 같은 말, 2026-10-30 사장님).
    # 칸 이름은 짧게: '결제 전에 보신 점수'는 표에서 '점/수'로 줄이 갈렸다(손님 테스트 3차). STEP 3 제목도 '내 점수'.
    parts = [f"좋은 점 {s['good']}점" if s["good"] is not None else "", f"조심할 점 {s['bad']}점" if s["bad"] is not None else "",
             f"전체 점수 {s['score']}점"]
    return ["내 점수", " · ".join(x for x in parts if x)]
