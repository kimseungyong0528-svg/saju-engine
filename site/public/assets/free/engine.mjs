// 무료 사주 맛보기 계산기. 파이썬 사주 엔진(saju/pillars.py, saju/analysis.py)과 같은 규칙을
// 브라우저에서 돌린다. 천문 계산이 필요한 절입 시각·표준시 이력은 saju-data.json 에 미리 뽑아 둔다
// (site/tools/build_taster_data.py). 같은 결과가 나오는지는 site/tests/taster.test.mjs 가 확인한다.

export const STEMS = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계'];
export const STEMS_HANJA = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
export const BRANCHES = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해'];
export const BRANCHES_HANJA = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
export const ELEMENTS = ['목', '화', '토', '금', '수'];
const STEM_ELEMENT = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4];
const STEM_YANG = i => i % 2 === 0;
const BRANCH_ELEMENT = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4];
const HIDDEN = [
  [[8, 10], [9, 20]], [[9, 9], [7, 3], [5, 18]], [[4, 7], [2, 7], [0, 16]], [[0, 10], [1, 20]],
  [[1, 9], [9, 3], [4, 18]], [[4, 7], [6, 7], [2, 16]], [[2, 10], [5, 9], [3, 11]], [[3, 9], [1, 3], [5, 18]],
  [[4, 7], [8, 7], [6, 16]], [[6, 10], [7, 20]], [[7, 9], [3, 3], [4, 18]], [[4, 7], [0, 7], [8, 16]],
];
const mainHidden = b => HIDDEN[b][HIDDEN[b].length - 1][0];
export const TEN_GODS = ['비견', '겁재', '식신', '상관', '편재', '정재', '편관', '정관', '편인', '정인'];
export const GROUPS = ['비겁', '식상', '재성', '관성', '인성'];
const groupOf = god => GROUPS[Math.floor(TEN_GODS.indexOf(god) / 2)];
export const PILLAR_NAMES = ['년주', '월주', '일주', '시주'];

const pillar = (stem, branch) => ({ stem, branch, ko: STEMS[stem] + BRANCHES[branch], hanja: STEMS_HANJA[stem] + BRANCHES_HANJA[branch] });
const fromIndex = i => pillar(((i % 10) + 10) % 10, ((i % 12) + 12) % 12);

// ── 날짜 · 시각 ───────────────────────────────────────────────
const DAY = 1440;
const civilMinutes = (y, m, d, hh = 0, mm = 0) => Date.UTC(y, m - 1, d, hh, mm) / 60000;
const bisectRight = (arr, x) => { let lo = 0, hi = arr.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (x < arr[mid][0]) hi = mid; else lo = mid + 1; } return lo; };

// 한국 현지 시각 → UTC(분). 파이썬 zoneinfo fold=0 과 같게: 겹치는 시각은 앞쪽(서머타임), 없는 시각은 바뀌기 전 시차.
export function civilToUtc(data, y, m, d, hh, mm) {
  const local = civilMinutes(y, m, d, hh, mm), tz = data.tz;
  const offsetAt = u => tz[Math.max(0, bisectRight(tz, u) - 1)][1];
  const hits = [...new Set(tz.map(t => t[1]))].filter(o => offsetAt(local - o) === o);
  if (hits.length) {
    const order = hits.map(o => [local - o, o]).sort((a, b) => a[0] - b[0]);
    return order[0][0];
  }
  const before = offsetAt(local - Math.max(...tz.map(t => t[1])) - 60);
  return local - before;
}

function jdnDays(y, m, d) { return Date.UTC(y, m - 1, d) / 86400000; }
export function dayPillarForDate(y, m, d) {
  // 1970-01-01 = 신사(辛巳, 17). 파이썬: (JDN - 11) mod 60
  return fromIndex(((jdnDays(y, m, d) + 17) % 60 + 60) % 60);
}

function ipchun(data, year) {
  const start = civilMinutes(year, 1, 1);
  return data.jie.find(j => j[1] === 2 && j[0] >= start)[0];
}

export function computePillars(data, utc, lon, knownTime = true) {
  const uy = new Date(utc * 60000).getUTCFullYear();
  const sajuYear = utc >= ipchun(data, uy) ? uy : uy - 1;
  const year = fromIndex(((sajuYear - 4) % 60 + 60) % 60);
  const jie = data.jie[bisectRight(data.jie, utc) - 1];
  const firstStem = ((year.stem % 5) * 2 + 2) % 10;
  const month = pillar((firstStem + ((jie[1] - 2 + 12) % 12)) % 10, jie[1]);
  const solar = new Date((utc + lon * 4) * 60000);
  let sy = solar.getUTCFullYear(), sm = solar.getUTCMonth() + 1, sd = solar.getUTCDate();
  if (!knownTime) return { year, month, day: dayPillarForDate(sy, sm, sd), hour: null };
  const h = solar.getUTCHours(), minute = solar.getUTCMinutes() + solar.getUTCSeconds() / 60 + solar.getUTCMilliseconds() / 60000;
  if (h >= 23) { const n = new Date(Date.UTC(sy, sm - 1, sd + 1)); sy = n.getUTCFullYear(); sm = n.getUTCMonth() + 1; sd = n.getUTCDate(); }
  const day = dayPillarForDate(sy, sm, sd);
  const hb = Math.floor((h * 60 + minute + 60) / 120) % 12;
  return { year, month, day, hour: pillar(((day.stem % 5) * 2 + hb) % 10, hb) };
}

// ── 원국 분석 ─────────────────────────────────────────────────
export function tenGod(dayStem, other) {
  const rel = ((STEM_ELEMENT[other] - STEM_ELEMENT[dayStem]) % 5 + 5) % 5;
  return TEN_GODS[rel * 2 + (STEM_YANG(dayStem) === STEM_YANG(other) ? 0 : 1)];
}
export const branchTenGod = (dayStem, b) => tenGod(dayStem, mainHidden(b));
const list = fp => [fp.year, fp.month, fp.day, fp.hour];

const STEM_W = [1, 1, 1, 1], BRANCH_W = [1, 2, 1.5, 1];
const round1 = x => Math.round(x * 10 + 1e-9 * Math.sign(x)) / 10;
export function elementStrength(fp) {
  const score = [0, 0, 0, 0, 0];
  list(fp).forEach((p, i) => {
    if (!p) return;
    score[STEM_ELEMENT[p.stem]] += STEM_W[i];
    const total = HIDDEN[p.branch].reduce((a, [, d]) => a + d, 0);
    for (const [s, d] of HIDDEN[p.branch]) score[STEM_ELEMENT[s]] += BRANCH_W[i] * d / total;
  });
  const total = score.reduce((a, b) => a + b, 0);
  return Object.fromEntries(ELEMENTS.map((e, i) => [e, round1(score[i] * 100 / total)]));
}

export function tenGodCounts(fp) {
  const c = Object.fromEntries(GROUPS.map(g => [g, 0])), ds = fp.day.stem;
  list(fp).forEach((p, i) => {
    if (!p) return;
    if (i !== 2) c[groupOf(tenGod(ds, p.stem))]++;
    c[groupOf(branchTenGod(ds, p.branch))]++;
  });
  return c;
}

const supports = (ds, el) => el === STEM_ELEMENT[ds] || el === (STEM_ELEMENT[ds] + 4) % 5;
export function strength(fp) {
  const ds = fp.day.stem, ws = { 0: 10, 1: 10, 3: 10 }, wb = [10, 30, 15, 10];
  let support = 0, drain = 0;
  list(fp).forEach((p, i) => {
    if (!p) return;
    if (i in ws) { if (supports(ds, STEM_ELEMENT[p.stem])) support += ws[i]; else drain += ws[i]; }
    const total = HIDDEN[p.branch].reduce((a, [, d]) => a + d, 0);
    const s = HIDDEN[p.branch].filter(([st]) => supports(ds, STEM_ELEMENT[st])).reduce((a, [, d]) => a + d, 0) / total;
    support += wb[i] * s; drain += wb[i] * (1 - s);
  });
  const score = round1(support / (support + drain) * 100);
  const label = score >= 70 ? '극신강' : score >= 55 ? '신강' : score > 45 ? '중화' : score > 30 ? '신약' : '극신약';
  return { score, label };
}

export function gyeokguk(fp) {
  const ds = fp.day.stem, mb = fp.month.branch;
  const visible = new Set(list(fp).filter((p, i) => p && i !== 2).map(p => p.stem));
  let chosen = mainHidden(mb);
  if (!['비견', '겁재'].includes(tenGod(ds, chosen))) {
    for (const [stem] of [...HIDDEN[mb]].reverse()) {
      if (visible.has(stem) && !['비견', '겁재'].includes(tenGod(ds, stem))) { chosen = stem; break; }
    }
  }
  const god = tenGod(ds, chosen);
  const name = god === '비견' || (god === '겁재' && !STEM_YANG(ds)) ? '건록격' : god === '겁재' ? '양인격' : god + '격';
  return { name, god };
}

const SAMHAP = { 8: 0, 0: 0, 4: 0, 2: 1, 6: 1, 10: 1, 5: 2, 9: 2, 1: 2, 11: 3, 3: 3, 7: 3 };
const DOHWA = [9, 3, 6, 0], YEOKMA = [2, 8, 11, 5], HWAGAE = [4, 10, 1, 7];
const CHEONEUL = { 0: [1, 7], 4: [1, 7], 6: [1, 7], 1: [0, 8], 5: [0, 8], 2: [11, 9], 3: [11, 9], 7: [2, 6], 8: [5, 3], 9: [5, 3] };
const MUNCHANG = { 0: 5, 1: 6, 2: 8, 3: 9, 4: 8, 5: 9, 6: 11, 7: 0, 8: 2, 9: 3 };
const YANGIN = { 0: 3, 2: 6, 4: 6, 6: 9, 8: 0 };
const HONGYEOM = { 0: 6, 1: 6, 2: 2, 3: 7, 4: 4, 5: 4, 6: 10, 7: 9, 8: 0, 9: 8 };
const GOEGANG = new Set(['경진', '경술', '임진', '임술', '무술']);
const BAEKHO = new Set(['갑진', '을미', '병술', '정축', '무진', '임술', '계축']);

export function shinsal(fp) {
  const out = [], seen = new Set(), day = fp.day;
  const pillars = list(fp).map((p, i) => [PILLAR_NAMES[i], p]).filter(([, p]) => p);
  const add = (name, where) => { const k = name + '|' + where; if (!seen.has(k)) { seen.add(k); out.push({ name, pillar: where }); } };
  for (const [basisName, basis] of [['년지', fp.year.branch], ['일지', day.branch]]) {
    const g = SAMHAP[basis];
    for (const [where, p] of pillars) {
      if (where === '년주' && basisName === '년지') continue;
      if (p.branch === DOHWA[g]) add('도화살', where);
      if (p.branch === YEOKMA[g]) add('역마살', where);
      if (p.branch === HWAGAE[g]) add('화개살', where);
    }
  }
  for (const [where, p] of pillars) {
    if (CHEONEUL[day.stem].includes(p.branch)) add('천을귀인', where);
    if (MUNCHANG[day.stem] === p.branch) add('문창귀인', where);
    if (YANGIN[day.stem] === p.branch) add('양인살', where);
    if (HONGYEOM[day.stem] === p.branch) add('홍염살', where);
    if (BAEKHO.has(p.ko)) add('백호살', where);
  }
  if (GOEGANG.has(day.ko)) add('괴강살', '일주');
  const start = idx(day) - idx(day) % 10, fb = start % 12, voids = [(fb + 10) % 12, (fb + 11) % 12];
  for (const [where, p] of pillars) if (where !== '일주' && voids.includes(p.branch)) add('공망', where);
  return out;
}
function idx(p) { for (let i = 0; i < 60; i++) if (i % 10 === p.stem && i % 12 === p.branch) return i; return -1; }

const pairKey = (a, b) => (a < b ? a + ',' + b : b + ',' + a);
const SET = arr => new Set(arr.map(([a, b]) => pairKey(a, b)));
export const SIX_COMBINE = SET([[0, 1], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7]]);
export const CLASH = SET([[0, 6], [1, 7], [2, 8], [3, 9], [4, 10], [5, 11]]);
export const WONJIN = SET([[0, 7], [1, 6], [2, 9], [3, 8], [4, 11], [5, 10]]);
const HARM = SET([[0, 7], [1, 6], [2, 5], [3, 4], [8, 11], [9, 10]]);
const PUNISH = SET([[0, 3], [2, 5], [5, 8], [2, 8], [1, 10], [10, 7], [1, 7]]);
const HALF = [[8, 0, 4], [11, 3, 7], [2, 6, 10], [5, 9, 1]];

// 두 지지 사이 관계 (saju/analysis.py branch_relation 과 같은 이름)
export function branchRelation(a, b) {
  const k = pairKey(a, b), out = [];
  if (SIX_COMBINE.has(k)) out.push('육합');
  if (a !== b && HALF.some(t => t.includes(a) && t.includes(b) && (t[1] === a || t[1] === b))) out.push('반합');
  if (CLASH.has(k)) out.push('충');
  if (a !== b && PUNISH.has(k)) out.push('형');
  if (a === b && [4, 6, 9, 11].includes(a)) out.push('자형');
  if (HARM.has(k)) out.push('해');
  if (WONJIN.has(k)) out.push('원진');
  return out;
}

export function analyze(fp) {
  const st = strength(fp);
  return {
    fp, ds: fp.day.stem, me: STEM_ELEMENT[fp.day.stem],
    elements: elementStrength(fp), groups: tenGodCounts(fp), strength: st,
    gyeokguk: gyeokguk(fp), shinsal: shinsal(fp),
    gods: list(fp).flatMap((p, i) => !p ? [] : [...(i === 2 ? [] : [{ god: tenGod(fp.day.stem, p.stem), at: i, level: '천간' }]),
      { god: branchTenGod(fp.day.stem, p.branch), at: i, level: '지지' }]),
  };
}

// ── 사이트 입력 → 명식 ────────────────────────────────────────
// person: 사이트 readPerson() 결과. solarDate: validateBirthDate 가 돌려준 양력 날짜(YYYY-MM-DD).
export function chartFromPerson(data, person, solarDate) {
  const [y, m, d] = (solarDate || person.birth).split('-').map(Number);
  const place = person.birthPlace || {};
  const lon = (['known', 'region-only'].includes(place.status) && data.regions[place.regionChoice || place.regionCode]) || data.defaultLon;
  let time = null;
  if (person.timeAccuracy === 'exact' && person.time) time = person.time;
  // 대략 시간은 범위의 시작 시각으로 본다(리포트 saju/chart.py 의 첫 번째 명식과 같은 시주, 제1조항).
  else if (person.timeAccuracy === 'approximate' && person.timeRange?.start && person.timeRange?.end) time = person.timeRange.start;
  if (!time) {
    const fp = computePillars(data, civilToUtc(data, y, m, d, 12, 0), lon, false);
    return { ...fp, day: dayPillarForDate(y, m, d) };
  }
  const [hh, mm] = time.split(':').map(Number);
  return computePillars(data, civilToUtc(data, y, m, d, hh, mm), lon, true);
}
