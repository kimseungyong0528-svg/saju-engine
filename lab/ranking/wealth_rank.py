"""2027 정미년 띠별 재물 순위(시험): 엔진의 띠-해 관계 + 오행 재성으로 점수를 매긴다.
점수 근거
- 그해 천간·지지에 띠의 재성(띠 오행이 이기는 오행)이 있으면 +3 (천간 정화 丁, 지지 미토 未)
- 띠 오행이 그해 오행을 낳으면(식상, 돈 버는 활동) +1.5 / 같은 오행(비겁, 나눠 갖는 사람)이면 -1
- 그해가 띠를 누르면(관성, 부담) -0.5
- 띠와 未의 관계: 육합 +2, 반합 +1.5, 충 -2, 형 -1, 파 -1, 해 -0.5, 원진 -1
- 삼재: 들·눌 -1, 날 -0.5
"""
import json
from saju.analysis import branch_relation
from saju.constants import BRANCHES, ZODIAC_ANIMALS
from saju.report.newyear import samjae

EL = dict(zip(BRANCHES, "수토목목토화화토금금토수"))
WINS = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}
MAKES = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
YEAR, YEAR_ELS, YB = 2027, ("화", "토"), "미"
REL = {"육합": 2, "반합": 1.5, "충": -2, "형": -1, "파": -1, "해": -0.5, "원진": -1}


def birth_years(i):
    return [y for y in range(1950, 2009) if (y - 4) % 12 == i]


rows = []
for i, (b, name) in enumerate(zip(BRANCHES, ZODIAC_ANIMALS)):
    e, s, why = EL[b], 0.0, []
    if WINS[e] in YEAR_ELS:
        s += 3; why.append(f"재물 기운({WINS[e]})이 들어옴")
    if MAKES[e] in YEAR_ELS:
        s += 1.5; why.append("돈 버는 활동이 늘어남")
    if e in YEAR_ELS:
        s -= 1; why.append("돈을 나눠 갖는 사람이 생김")
    if any(WINS[y] == e for y in YEAR_ELS):
        s -= 0.5; why.append("책임과 부담이 커짐")
    rels = branch_relation(BRANCHES.index(b), BRANCHES.index(YB))
    for r in rels:
        k = r.split("(")[0]; s += REL.get(k, 0); why.append(f"띠와 2027년이 '{k}'")
    sj = samjae(b, YEAR)
    if sj["kind"]:
        s -= 0.5 if sj["kind"] == "날삼재" else 1; why.append(sj["kind"])
    ys = birth_years(i)
    rows.append({"ddi": name, "score": s, "why": why, "years": "·".join(f"{y % 100:02d}" for y in ys[-4:-1])})
rows.sort(key=lambda r: -r["score"])
for n, r in enumerate(rows, 1):
    r["rank"] = n
print(json.dumps(rows, ensure_ascii=False, indent=1))
json.dump(rows, open("lab/ranking/wealth_2027.json", "w"), ensure_ascii=False, indent=1)
