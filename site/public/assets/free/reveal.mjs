// 결제 전 이야기 화면(상품마다 정보 입력 뒤 → 리포트 안내 앞)에 보여 줄 '해마다 들어오는 별' 지도.
// 상품마다 좋은 표시(돈의 별, 자리의 별, 합…)와 조심할 표시(겁재, 상관, 충…)를 해마다 붙인다.
// 결제 리포트도 같은 규칙을 파이썬(saju/reveal.py)으로 돌려, 고객이 결제 전에 본 해·달을 리포트에서 더 깊게 푼다.
// 규칙을 바꾸면 saju/reveal.py 도 똑같이 바꾸고 site/tools/make_taster_fixture.py 를 다시 돌린다.

import { analyze, branchRelation, branchTenGod, tenGod, ELEMENTS, STEMS, BRANCHES, STEMS_HANJA, BRANCHES_HANJA } from './engine.mjs';

const STEM_EL = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4];
const BRANCH_EL = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4];
const GROUP_OF = { 비견: '비겁', 겁재: '비겁', 식신: '식상', 상관: '식상', 편재: '재성', 정재: '재성', 편관: '관성', 정관: '관성', 편인: '인성', 정인: '인성' };
export const FIRST_YEAR = 2027;

const pillar = (stem, branch) => ({ stem, branch, ko: STEMS[stem] + BRANCHES[branch], hanja: STEMS_HANJA[stem] + BRANCHES_HANJA[branch] });
const yearPillar = y => pillar(((y - 4) % 10 + 10) % 10, ((y - 4) % 12 + 12) % 12);
// 2027년(정미년) 열두 달: 인월(2월, 입춘부터) ~ 축월(2028년 1월). 정(丁)년의 첫 달은 임인(壬寅).
export const MONTHS_2027 = Array.from({ length: 12 }, (_, k) => ({ ...pillar((8 + k) % 10, (2 + k) % 12), label: k === 11 ? '2028년 1월' : `${k + 2}월` }));

// 사주에서 가장 모자란 기운(무료 맛보기 '가장 모자란 기운'과 같은 것: 같으면 뒤 순서)
function weakest(elements) {
  const sorted = ELEMENTS.map(e => [e, elements[e]]).sort((a, b) => b[1] - a[1]);
  return sorted[sorted.length - 1][0];
}

function marker(fp, sex) {
  const an = analyze(fp), ds = fp.day.stem, db = fp.day.branch, st = an.strength.score;
  const weak = ELEMENTS.indexOf(weakest(an.elements));
  const gods = p => [tenGod(ds, p.stem), branchTenGod(ds, p.branch)];
  const has = (p, names) => gods(p).some(g => names.includes(g));
  const group = (p, gs) => gods(p).some(g => gs.includes(GROUP_OF[g]));
  const rel = p => branchRelation(db, p.branch);
  const helpful = st >= 55 ? ['식상', '재성', '관성'] : st <= 45 ? ['인성', '비겁'] : null;
  const RULE = {
    money: p => group(p, ['재성']),
    rob: p => has(p, ['겁재']),
    job: p => group(p, ['관성']),
    boss: p => has(p, ['상관']),
    bigmoney: p => has(p, ['편재']),
    make: p => has(p, ['식신']),
    love: p => group(p, [sex === 'female' ? '관성' : '재성']),
    hap: p => rel(p).some(r => r === '육합' || r === '반합'),
    clash: p => rel(p).includes('충'),
    fill: p => STEM_EL[p.stem] === weak || BRANCH_EL[p.branch] === weak,
    // 2027년 달: 지지(그 달 생활에 크게 작용)가 나를 돕는 기운이면 좋은 달. 힘이 가운데면 모자란 기운이 오는 달.
    help: p => helpful ? helpful.includes(GROUP_OF[branchTenGod(ds, p.branch)]) : BRANCH_EL[p.branch] === weak,
  };
  const ruleOf = key => RULE[key.startsWith('clash') ? 'clash' : key.startsWith('hap') ? 'hap' : key.startsWith('love') ? 'love' : key];
  return { weak: ELEMENTS[weak], ruleOf };
}

const markKey = (key, sex) => key === 'love' ? (sex === 'female' ? 'love_f' : 'love_m') : key;

// 상품 하나의 지도: 12년(지지 열두 개가 한 번씩 다 돈다)(신년운세는 2027년 열두 달)마다 좋은·조심할 표시.
// 돌려주는 값: { unit:'year'|'month', cells:[{label, ko, hanja, good:[key], bad:[key]}], good:{key:[label]}, bad:{key:[label]}, weak }
export function luckMap(fp, sex, product, T, startYear = FIRST_YEAR) {
  const conf = T.REVEAL.PRODUCTS[product];
  const { weak, ruleOf } = marker(fp, sex);
  const unit = product === 'newyear' ? 'month' : 'year';
  const base = unit === 'month' ? MONTHS_2027 : Array.from({ length: 12 }, (_, i) => ({ ...yearPillar(startYear + i), label: String(startYear + i) }));
  const good = {}, bad = {};
  const cells = base.map(p => {
    const cell = { label: p.label, ko: p.ko, hanja: p.hanja, good: [], bad: [] };
    for (const [kind, list, into] of [['good', conf.good, good], ['bad', conf.bad, bad]]) {
      for (const k of list) if (ruleOf(k)(p)) { const key = markKey(k, sex); cell[kind].push(key); (into[key] || (into[key] = [])).push(p.label); }
    }
    return cell;
  });
  return { unit, cells, good, bad, weak };
}
