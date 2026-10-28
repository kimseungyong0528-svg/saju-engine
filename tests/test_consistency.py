"""제1조항(모순 금지) 검사: 무료 풀이·결제 전 화면 글이 '원국에 없다'와 '그 해에 들어온다'를 섞어 쓰지 않는지."""

import json
import re
from pathlib import Path

TEXTS = json.loads((Path(__file__).resolve().parents[1] / "site/public/assets/free/texts.json").read_text(encoding="utf-8"))
STARS = r"(재성|관성|식상|인성|비겁|편재|정재|식신|상관|겁재|편관|정관|{starName)"


def _strings(x, path=""):
    if isinstance(x, str):
        yield path, x
    elif isinstance(x, dict):
        for k, v in x.items():
            yield from _strings(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _strings(v, f"{path}[{i}]")


def test_none_sentences_name_the_birth_chart():
    """'별이 하나도 없다'는 말은 태어날 때 받은 여덟 글자 이야기라고 밝혀야 한다(해마다 들어오는 별과 모순되지 않게)."""
    bad = []
    for path, s in _strings(TEXTS):
        for sent in re.split(r"(?<=다\.)\s*", s):
            none = ("하나도 없" in sent and re.search(STARS, sent)) or ("기운이 없습니다" in sent or "기운이 약합니다" in sent)
            if none and "태어날 때 받은 여덟 글자" not in sent and "해의 기운" not in sent:
                bad.append((path, sent))
    assert not bad, bad


def test_yearly_stars_come_from_outside():
    """해마다 들어오는 별은 '바깥에서 들어오는'으로 써서 원국 이야기와 구분한다."""
    bad = []
    for key, mk in TEXTS["REVEAL"]["MARKS"].items():
        if re.search(STARS, mk["line"]) and re.search(r"(재성|관성|편재|식신)\(", mk["line"]) and "바깥에서" not in mk["line"]:
            bad.append((key, mk["line"]))
    assert not bad, bad


def test_good_base_texts_admit_yearly_trouble():
    """'막는 기운이 없다'는 좋은 글도, 결제 전 지도에 늘 나오는 조심할 해(달)가 있다는 것을 함께 말한다."""
    bad = [k for k, v in TEXTS["REASONS"].items() if (k.endswith("_base_good") or k == "ny_balance") and "다만" not in v]
    assert not bad, bad
