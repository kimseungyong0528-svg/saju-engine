// 결제 전 이야기 화면(상품마다 정보 입력 뒤 → 리포트 안내 앞)에 보여 줄 '해마다 들어오는 별' 지도.
// 상품마다 좋은 표시(돈의 별, 자리의 별, 합…)와 조심할 표시(겁재, 상관, 충…)를 해마다 붙인다.
// 결제 리포트도 같은 규칙을 파이썬(saju/reveal.py)으로 돌려, 고객이 결제 전에 본 해·달을 리포트에서 더 깊게 푼다.
// 규칙을 바꾸면 saju/reveal.py 도 똑같이 바꾸고 site/tools/make_taster_fixture.py 를 다시 돌린다.

import { analyze, branchRelation, branchTenGod, tenGod, elementStrength, chartFromPerson, ELEMENTS, STEMS, BRANCHES, STEMS_HANJA, BRANCHES_HANJA } from './engine.mjs';
import { reading } from './taster.mjs';

const STEM_EL = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4];
const BRANCH_EL = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4];
const GROUP_OF = { 비견: '비겁', 겁재: '비겁', 식신: '식상', 상관: '식상', 편재: '재성', 정재: '재성', 편관: '관성', 정관: '관성', 편인: '인성', 정인: '인성' };
export const FIRST_YEAR = 2027;
export const REUNION_MONTHS = 24;   // 재회사주 지도: 앞으로 24개월(사장님 2026-10-30: 몇 달 안, 길어야 2~3년)
// 태어난 날 지지의 삼합 무리마다 정해진 도화(桃花) 글자: 인오술→묘, 신자진→유, 사유축→오, 해묘미→자
const PEACH_OF = { 2: 3, 6: 3, 10: 3, 8: 9, 0: 9, 4: 9, 5: 6, 9: 6, 1: 6, 11: 0, 3: 0, 7: 0 };

const pillar = (stem, branch) => ({ stem, branch, ko: STEMS[stem] + BRANCHES[branch], hanja: STEMS_HANJA[stem] + BRANCHES_HANJA[branch] });
const yearPillar = y => pillar(((y - 4) % 10 + 10) % 10, ((y - 4) % 12 + 12) % 12);
// 2027년 달력 1월~12월(리포트와 같은 열두 달). 1월은 2026년 병오년의 마지막 달 신축(辛丑, 소한부터),
// 2월~12월은 정미년의 임인(壬寅, 입춘부터)~임자(壬子, 대설부터).
export const MONTHS_2027 = [{ ...pillar(7, 1), label: '1월' },
  ...Array.from({ length: 11 }, (_, k) => ({ ...pillar((8 + k) % 10, (2 + k) % 12), label: `${k + 2}월` }))];

// 달력 year년 month월에 시작하는 달(절기 기준)의 간지. 1월은 앞 해의 마지막 달(축월). saju/reveal.py month_pillar_of 와 같다.
function monthPillarOf(year, month) {
  const y = month === 1 ? year - 1 : year, k = month === 1 ? 11 : month - 2;
  const first = ((((y - 4) % 10 + 10) % 10) % 5 * 2 + 2) % 10;
  return pillar((first + k) % 10, (2 + k) % 12);
}
// 재회사주 지도: start [해, 달]부터 24개월. 이름은 '2027년 3월'처럼.
export function reunionMonths([y, m]) {
  const out = [];
  for (let i = 0; i < REUNION_MONTHS; i++) {
    out.push({ ...monthPillarOf(y, m), label: `${y}년 ${m}월` });
    [y, m] = m === 12 ? [y + 1, 1] : [y, m + 1];
  }
  return out;
}
// 재회사주 지도의 첫 달: 오늘이 15일까지면 이번 달, 16일부터는 다음 달(saju/reveal.py start_month 와 같다).
export function startMonth(y, m, d) { return d <= 15 ? [y, m] : m === 12 ? [y + 1, 1] : [y, m + 1]; }

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
    // 연애사주·평생사주(사장님 2026-10-30): '인연의 별' 하나로 묶지 않고 배우자 별·도화·합을 따로 짚는다
    spouse: p => has(p, [sex === 'female' ? '정관' : '정재']),
    peach: p => p.branch === PEACH_OF[db],
    // 재회사주: 배우자 자리와 육합하는 달이 가장 좋은 달, 반합하는 달이 다시 이어지기 쉬운 달
    best_re: p => rel(p).includes('육합'),
    hap_re: p => rel(p).includes('반합') && !rel(p).includes('육합'),
    hap: p => rel(p).some(r => r === '육합' || r === '반합'),
    clash: p => rel(p).includes('충'),
    fill: p => STEM_EL[p.stem] === weak || BRANCH_EL[p.branch] === weak,
    // 2027년 달: 지지(그 달 생활에 크게 작용)가 나를 돕는 기운이면 좋은 달. 힘이 가운데면 모자란 기운이 오는 달.
    help: p => helpful ? helpful.includes(GROUP_OF[branchTenGod(ds, p.branch)]) : BRANCH_EL[p.branch] === weak,
  };
  const ruleOf = key => RULE[key] || RULE[key.startsWith('clash') ? 'clash' : key.startsWith('hap') ? 'hap' : key.startsWith('spouse') ? 'spouse' : key];
  return { weak: ELEMENTS[weak], ruleOf };
}

const markKey = (key, sex) => key === 'spouse' ? key + (sex === 'female' ? '_f' : '_m') : key;

// 상품 하나의 지도: 12년(지지 열두 개가 한 번씩 다 돈다)(신년운세는 2027년 열두 달)마다 좋은·조심할 표시.
// 돌려주는 값: { unit:'year'|'month', cells:[{label, ko, hanja, good:[key], bad:[key]}], good:{key:[label]}, bad:{key:[label]}, weak }
// 무료 풀이 '2027년 운'이 좋은 쪽인지 조심할 쪽인지(맛보기 TOP3에 든 쪽, 들지 않았으면 50점 이상이 좋은 쪽)와 점수.
// 평생사주 12년 지도의 2027년 칸과 리포트의 2027년 점수가 이것을 따른다(saju/reveal.py ny_verdict 와 같다, 제1조항).
export function nyVerdict(fp, sex, T) {
  const r = reading(fp, { name: '', sex }, T), score = r.scores.newyear;
  if (r.good.some(a => a.id === 'newyear')) return ['good', score];
  if (r.bad.some(a => a.id === 'newyear')) return ['bad', score];
  return [score >= 50 ? 'good' : 'bad', score];
}

// 12년 지도(모든 상품)의 2027년 칸: 무료 풀이 '2027년 운'과 같은 쪽 표시만 남긴다(없으면 '2027년 좋은 흐름'·'2027년 조심').
function yearMarks(fp, sex, product, T, label, good, bad) {
  // 한 칸에 좋은 표시와 조심할 표시를 함께 붙이지 않는다(모든 상품): 조심할 표시가 있으면 조심할 칸
  if (label !== '2027') return good.length && bad.length ? [[], bad] : [good, bad];
  const [side] = nyVerdict(fp, sex, T);
  return side === 'good' ? [good.length ? good : ['ny_good'], []] : [[], bad.length ? bad : ['ny_bad']];
}

export function luckMap(fp, sex, product, T, startYear = FIRST_YEAR, start = null) {
  const conf = T.REVEAL.PRODUCTS[product];
  const { weak, ruleOf } = marker(fp, sex);
  const unit = product === 'newyear' || product === 'reunion' ? 'month' : 'year';
  const base = unit === 'month' ? (product === 'reunion' ? reunionMonths(start || [startYear, 1]) : MONTHS_2027) : Array.from({ length: 12 }, (_, i) => ({ ...yearPillar(startYear + i), label: String(startYear + i) }));
  const good = {}, bad = {};
  // 재회사주 2027년 달: 신년운세 지도에서 '조심할 달'인 달에는 좋은 표시를 붙이지 않는다(saju/reveal.py luck_map 과 같다, 제1조항)
  const nyBad = product === 'reunion' ? new Set(luckMap(fp, sex, 'newyear', T).cells.filter(c => c.bad.length).map(c => c.ko)) : null;
  const cells = base.map(p => {
    const cell = { label: p.label, ko: p.ko, hanja: p.hanja };
    [cell.good, cell.bad] = yearMarks(fp, sex, product, T, p.label,
      conf.good.filter(k => ruleOf(k)(p)).map(k => markKey(k, sex)), conf.bad.filter(k => ruleOf(k)(p)).map(k => markKey(k, sex)));
    if (nyBad && p.label.startsWith('2027년') && nyBad.has(p.ko)) cell.good = [];
    for (const [kind, into] of [['good', good], ['bad', bad]]) for (const key of cell[kind]) (into[key] || (into[key] = [])).push(p.label);
    return cell;
  });
  return { unit, cells, good, bad, weak };
}

// ── 두 사람 궁합 점수(깊은 궁합·재회사주 결제 전 화면) ─────────────────
// saju/pair.py compare·pair_score 와 같은 계산. 리포트의 '두 사람 궁합 점수'가 이 점수 그대로다(제1조항).
const PK = (a, b) => (a < b ? a + ',' + b : b + ',' + a);
const PSET = arr => new Set(arr.map(([a, b]) => PK(a, b)));
const P_STEM_COMBINE = PSET([[0, 5], [1, 6], [2, 7], [3, 8], [4, 9]]);
const P_STEM_CLASH = PSET([[0, 6], [1, 7], [2, 8], [3, 9]]);
const P_SIX = PSET([[0, 1], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7]]);
const P_THREE = [[8, 0, 4], [11, 3, 7], [2, 6, 10], [5, 9, 1]];
const P_CLASH = PSET([[0, 6], [1, 7], [2, 8], [3, 9], [4, 10], [5, 11]]);
const P_PUNISH_GROUPS = [[2, 5, 8], [1, 10, 7]];
const P_PUNISH_PAIR = PSET([[0, 3]]);
const P_BREAK = PSET([[0, 9], [1, 4], [2, 11], [3, 6], [5, 8], [7, 10]]);
const P_HARM = PSET([[0, 7], [1, 6], [2, 5], [3, 4], [8, 11], [9, 10]]);
const P_WONJIN = PSET([[0, 7], [1, 6], [2, 9], [3, 8], [4, 11], [5, 10]]);
const GOOD_REL = new Set(['육합', '반합', '천간합', '삼합']);
const HARD_REL = new Set(['충', '형', '자형', '파', '해', '원진', '천간충']);

function stemRel(a, b) {
  const k = PK(a, b), out = [];
  if (P_STEM_COMBINE.has(k)) out.push('천간합');
  if (P_STEM_CLASH.has(k)) out.push('천간충');
  return out;
}
function branchRel(a, b) {
  const k = PK(a, b), out = [];
  if (P_SIX.has(k)) out.push('육합');
  for (const t of P_THREE) if (a !== b && t.includes(a) && t.includes(b) && (t[1] === a || t[1] === b)) out.push('반합');
  if (P_CLASH.has(k)) out.push('충');
  if (P_PUNISH_PAIR.has(k)) out.push('형');
  for (const g of P_PUNISH_GROUPS) if (a !== b && g.includes(a) && g.includes(b)) out.push('형');
  if (a === b && [4, 6, 9, 11].includes(a)) out.push('자형');
  if (P_BREAK.has(k)) out.push('파');
  if (P_HARM.has(k)) out.push('해');
  if (P_WONJIN.has(k)) out.push('원진');
  return out;
}
function tone(rels) {
  const good = rels.some(r => GOOD_REL.has(r)), hard = rels.some(r => HARD_REL.has(r));
  return good && !hard ? '조화' : hard && !good ? '긴장' : rels.length ? '복합' : '중립';
}

// 두 사람 궁합 점수(48~96)와 화면에 짚어 줄 근거(배우자 자리끼리의 분위기, 서로 채워 주는 기운).
export function pairScore(me, other) {
  const ea = elementStrength(me), eb = elementStrength(other);
  const fill = ELEMENTS.filter(e => ea[e] < 10 && eb[e] >= 20), give = ELEMENTS.filter(e => eb[e] < 10 && ea[e] >= 20);
  const pa = [me.year, me.month, me.day, me.hour].filter(Boolean), pb = [other.year, other.month, other.day, other.hour].filter(Boolean);
  let good = 0, hard = 0;
  for (const x of pa) for (const y of pb) for (const r of [...stemRel(x.stem, y.stem), ...branchRel(x.branch, y.branch)]) {
    if (GOOD_REL.has(r)) good++;
    if (HARD_REL.has(r)) hard++;
  }
  const palace = tone(branchRel(me.day.branch, other.day.branch));
  const d = ((STEM_EL[other.day.stem] - STEM_EL[me.day.stem]) % 5 + 5) % 5;
  let s = 62 + 4 * good - 3 * hard + 6 * (fill.length + give.length);
  s += { 조화: 8, 긴장: -8, 복합: 2 }[palace] || 0;
  s += [3, 5, 0, 0, 5][d];
  s += stemRel(me.day.stem, other.day.stem).includes('천간합') ? 4 : 0;
  return { score: Math.max(48, Math.min(96, s)), palace, fill, give, harmony: good, tension: hard };
}

// ── 태어난 시각이 기둥이 바뀌는 경계에 가까울 때(정확한 시각만, ±15분) ─────────
// 리포트 사주표의 같은 줄(saju/chart.py _boundary_warnings → saju/report _merge_boundary)을 결제 전 화면에도 보여 준다(제1조항).
export function boundaryLines(data, person, solarDate) {
  if (person.timeAccuracy !== 'exact' || !person.time) return [];
  const names = ['년주', '월주', '일주', '시주'];
  const at = delta => {
    const [y, m, d] = solarDate.split('-').map(Number), [hh, mm] = person.time.split(':').map(Number);
    const t = new Date(Date.UTC(y, m - 1, d, hh, mm + delta));
    const iso = t.toISOString();
    return chartFromPerson(data, { ...person, calendar: 'solar', birth: iso.slice(0, 10), time: iso.slice(11, 16) }, iso.slice(0, 10));
  };
  const base = at(0), near = {};
  for (let delta = -15; delta <= 15; delta++) {
    if (!delta) continue;
    const fp = at(delta);
    ['year', 'month', 'day', 'hour'].forEach((k, i) => {
      if ((base[k]?.ko || null) !== (fp[k]?.ko || null)) {
        const key = (delta > 0 ? '이후' : '이전') + '|' + names[i];
        near[key] = Math.min(near[key] ?? 99, Math.abs(delta));
      }
    });
  }
  // 같은 분, 같은 방향이면 한 줄로 묶는다('일주와 시주가'). 파이썬 saju/report _merge_boundary 와 같다.
  const groups = new Map();
  for (const key of Object.keys(near).sort()) {
    const [d, pillar] = key.split('|'), g = d + '|' + near[key];
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g).push(pillar);
  }
  return [...groups].map(([g, ps]) => {
    const [d, n] = g.split('|');
    return `태어난 시각이 ${n}분만 ${d === '이후' ? '늦었다면' : '빨랐다면'} ${ps.join('와 ')}가 달라지는 경계예요. 시각이 정확한지 한 번 더 확인해 주세요.`;
  });
}
