// 무료 사주 맛보기: 운 8개에 점수를 매기고 좋은 운 3개, 조심할 운 3개를 고른다.
// 점수는 50점에서 시작해 사주 근거마다 더하고 뺀다. 근거마다 미리 써 둔 글(texts.json)이 붙는다.
// 결제 리포트도 같은 규칙을 파이썬(saju/taster.py)으로 돌려, 고객이 본 내용과 어긋나지 않게 쓴다.
// 규칙을 바꾸면 saju/taster.py 도 똑같이 바꾸고 site/tools/make_taster_fixture.py 를 다시 돌린다.

import { analyze, branchRelation, branchTenGod, tenGod, ELEMENTS, BRANCHES, BRANCHES_HANJA, STEMS, GROUPS } from './engine.mjs';

const WHERE = { 년주: '태어난 해', 월주: '태어난 달', 일주: '태어난 날', 시주: '태어난 시' };
const HANJA_GOD = { 비견: '比肩', 겁재: '劫財', 식신: '食神', 상관: '傷官', 편재: '偏財', 정재: '正財', 편관: '偏官', 정관: '正官', 편인: '偏印', 정인: '正印' };
const STEM_HANJA = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const STEM_EL = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4];
const ZODIAC = ['쥐', '소', '호랑이', '토끼', '용', '뱀', '말', '양', '원숭이', '닭', '개', '돼지'];
const godName = g => `${g}(${HANJA_GOD[g]})`;
// 일간 이름(예: 을목(乙木)). 같은 구조의 문단이라도 첫 문장에 그 사람 글자를 넣는다(사장님 2026-11-06 저녁 1-3, saju/taster.py _dm 과 같다).
const EL_HANJA = ['木', '火', '土', '金', '水'];
const dmName = f => `${STEMS[f.ds]}${ELEMENTS[STEM_EL[f.ds]]}(${STEM_HANJA[f.ds]}${EL_HANJA[STEM_EL[f.ds]]})`;
const branchName = b => `${BRANCHES[b]}(${BRANCHES_HANJA[b]})`;
const Y2027 = { stem: 3, branch: 7 }; // 정미(丁未)
export const AREA_ORDER = ['newyear', 'romance', 'intimate', 'reunion', 'wealth', 'career', 'business', 'health'];
const PREFIX = { newyear: 'ny', romance: 'ro', intimate: 'im', reunion: 're', wealth: 'we', career: 'ca', business: 'bu', health: 'he' };
const GROUP_OF = { 비견: '비겁', 겁재: '비겁', 식신: '식상', 상관: '식상', 편재: '재성', 정재: '재성', 편관: '관성', 정관: '관성', 편인: '인성', 정인: '인성' };

// 받침에 맞는 조사: {word|이} → 정관이 / 겁재가
function josa(word, pair) {
  const plain = String(word).replace(/\(.*\)$/, '');
  const ch = plain.charCodeAt(plain.length - 1) - 0xac00;
  const batchim = ch >= 0 && ch <= 11171 && ch % 28 !== 0;
  const table = { 이: ['이', '가'], 은: ['은', '는'], 을: ['을', '를'], 와: ['과', '와'] };
  const [withB, without] = table[pair] || [pair, pair];
  return word + (batchim ? withB : without);
}
export function fill(text, vars) {
  return text.replace(/\{(\w+)(?:\|(\S))?\}/g, (_, k, p) => {
    if (!(k in vars)) throw new Error('빈칸 값 없음: ' + k);
    return p ? josa(vars[k], p) : vars[k];
  });
}

function facts(fp, sex) {
  const an = analyze(fp);
  const { me, ds, groups, elements, strength: st } = an;
  const pct = g => elements[ELEMENTS[(me + GROUPS.indexOf(g)) % 5]];
  const names = new Set(an.shinsal.map(s => s.name));
  const branches = [fp.year, fp.month, fp.day, fp.hour].filter(Boolean).map(p => p.branch);
  const db = fp.day.branch;
  const others = [fp.year, fp.month, fp.hour].filter(Boolean).map(p => p.branch);
  const dayRel = new Set(others.flatMap(b => branchRelation(db, b)));
  const allRel = new Set();
  for (let i = 0; i < branches.length; i++) for (let j = i + 1; j < branches.length; j++) branchRelation(branches[i], branches[j]).forEach(r => allRel.add(r));
  const gods = new Set(an.gods.map(g => g.god));
  return { an, me, ds, groups, elements, st: st.score, stLabel: st.label, pct, names, db, dayRel, allRel, gods, sex, fp };
}

// 각 운의 근거 목록: [이유 키, 점수, 글에 넣을 값]
const RULES = {
  newyear(f, T) {
    const out = [], elName = e => `${T.ELEMENT_WORD[e]}(${e})`;
    const helpful = f.st >= 55 ? ['식상', '재성', '관성'] : f.st <= 45 ? ['인성', '비겁'] : [];
    const g1 = GROUP_OF[tenGod(f.ds, Y2027.stem)], g2 = GROUP_OF[branchTenGod(f.ds, Y2027.branch)];
    const good = [], bad = [];
    // 가장 모자란 기운을 '부담'이라 하지 않고, 넘치는 기운을 '도와주는 기운'이라 하지 않는다(saju/taster.py _newyear 와 같다)
    const lack = new Set(ELEMENTS.filter(e => f.elements[e] < 8)), many = new Set(ELEMENTS.filter(e => f.elements[e] >= 35));
    for (const [g, el] of [[g1, '화'], [g2, '토']]) {
      if (!helpful.length) continue;
      const help = helpful.includes(g);
      if ((!help && lack.has(el)) || (help && many.has(el))) continue;
      if (help) good.push(el); else bad.push(el);
    }
    if (good.length === 2) out.push(['ny_help2', 28]);
    else if (good.length === 1) out.push(['ny_help1', 14, { good: elName(good[0]) }]);
    if (bad.length) out.push(['ny_hurt', -11 * bad.length, { bad: bad.map(elName).join('과 ') }]);
    const rel = branchRelation(f.db, Y2027.branch);
    const mb = f.fp.month.branch;
    // '부딪히지 않는다'는 말은 태어난 날과 충·형·원진이 없고 더운 계절생이 아닐 때만(saju/taster.py 와 같다)
    if (!helpful.length && !rel.some(r => ['충', '형', '원진'].includes(r)) && ![5, 6, 7].includes(mb)) out.push(['ny_balance', 6]);
    const dayBranch = branchName(f.db);
    if (rel.includes('충')) out.push(['ny_clash', -16]);
    if (rel.includes('육합') || rel.includes('반합')) out.push(['ny_combine', 9, { dayBranch }]);
    if (rel.includes('형')) out.push(['ny_punish', -8, { dayBranch }]);
    if (rel.includes('원진')) out.push(['ny_wonjin', -7]);
    if ([11, 0, 1].includes(mb) && !bad.includes('화')) out.push(['ny_warm', 8]);
    if ([5, 6, 7].includes(mb) && !good.includes('화')) out.push(['ny_hot', -7]);
    return out;
  },
  romance(f, T) {
    const out = [];
    const dohwa = f.an.shinsal.filter(s => s.name === '도화살');
    if (dohwa.length) {
      const near = dohwa.find(s => ['일주', '시주'].includes(s.pillar)) || dohwa[0];
      out.push(['ro_dohwa', 14 + (['일주', '시주'].includes(near.pillar) ? 4 : 0), { where: WHERE[near.pillar] }]);
    }
    if (f.names.has('홍염살')) out.push(['ro_hongyeom', 8]);
    const star = T.STAR[f.sex === 'female' ? 'female' : 'male'];
    const sg = f.sex === 'female' ? '관성' : '재성', n = f.groups[sg];
    // 재물운 '재다신약'·직업운 '관성이 강한데 받칠 힘이 약함'과 같은 사주에 '딱 맞게'라고 쓰지 않는다(제1조항).
    const heavy = f.pct(sg) >= 30 && f.st <= 45;
    if (n === 0) out.push(['ro_nostar', -14, star]);
    else if (n <= 2 && !heavy) out.push(['ro_star', 8, { ...star, count: n }]);
    else if (n >= 4) out.push(['ro_manystar', -10, { ...star, count: n }]);
    if (f.groups.식상 >= 1) out.push(['ro_express', 4]); else out.push(['ro_shy', -7]);
    if (f.dayRel.has('충')) out.push(['ro_dayclash', -10]);
    if (f.names.has('화개살')) out.push(['ro_hwagae', -4]);
    return out;
  },
  intimate(f, T) {
    const out = [];
    const pg = branchTenGod(f.ds, f.db), palaceGod = godName(pg);
    const best = f.sex === 'female' ? '정관' : '정재';
    if (pg === best) out.push(['im_palace_good', 12, { palaceGod }]);
    else if (['정인', '식신'].includes(pg)) out.push(['im_palace_soft', 6, { palaceGod }]);
    else if (T.PALACE_ROUGH[pg]) out.push(['im_palace_rough', -8, { palaceGod, palaceMeaning: T.PALACE_ROUGH[pg] }]);
    if (f.dayRel.has('육합')) out.push(['im_combine', 8]);
    if (f.dayRel.has('충')) out.push(['im_clash', -12]);
    if (f.dayRel.has('원진')) out.push(['im_wonjin', -8]);
    if (f.sex === 'male' && f.groups.비겁 >= 3) out.push(['im_rival', -10, { count: f.groups.비겁 }]);
    if (f.sex === 'female' && f.groups.식상 >= 3) out.push(['im_sangwan', -10, { count: f.groups.식상 }]);
    if (f.gods.has(best)) out.push(['im_steady', 6, T.STEADY[f.sex === 'female' ? 'female' : 'male']]);
    return out;
  },
  reunion(f) {
    const out = [];
    if (f.allRel.has('육합') || f.allRel.has('반합')) out.push(['re_combine', 8]);
    if (f.names.has('화개살')) out.push(['re_hwagae', 8]);
    if (f.groups.인성 >= 2) out.push(['re_memory', 6, { count: f.groups.인성 }]);
    if (f.allRel.has('충')) out.push(['re_clash', -10]);
    if (f.allRel.has('원진')) out.push(['re_wonjin', -8]);
    if (f.groups.비겁 >= 3) out.push(['re_pride', -6, { count: f.groups.비겁 }]);
    return out;
  },
  wealth(f, T) {
    const out = [];
    const jae = f.groups.재성;
    if (f.groups.식상 >= 1 && jae >= 1) out.push(['we_flow', 14, { dm: dmName(f), sik: f.groups.식상, jae }]);
    const gy = f.an.gyeokguk.name;
    if (['정재격', '편재격'].includes(gy)) out.push(['we_gyeok', 10, { gyeok: gy, gyeokMeaning: T.GYEOK_MEANING[gy] }]);
    if (f.st >= 55 && jae >= 1) out.push(['we_strong', 8]);
    if (jae === 0) out.push(['we_none', -12]);
    if (f.pct('재성') >= 30 && f.st <= 45) out.push(['we_heavy', -14]);
    if (f.groups.비겁 >= 3 && jae >= 1) out.push(['we_rival', -12, { count: f.groups.비겁 }]);
    return out;
  },
  career(f, T) {
    const out = [];
    const gwan = f.groups.관성;
    if (gwan >= 1 && f.groups.인성 >= 1) out.push(['ca_flow', 14, { dm: dmName(f), gwan, inn: f.groups.인성 }]);
    const gy = f.an.gyeokguk.name;
    if (['정관격', '편관격', '정인격', '편인격'].includes(gy)) out.push(['ca_gyeok', 8, { gyeok: gy, gyeokMeaning: T.GYEOK_MEANING[gy] }]);
    if (f.names.has('문창귀인')) out.push(['ca_munchang', 8]);
    if (f.names.has('천을귀인')) out.push(['ca_cheoneul', 6]);
    if (f.names.has('역마살')) out.push(['ca_yeokma', 4]);
    if (gwan === 0) out.push(['ca_free', -8]);
    if (f.pct('관성') >= 30 && f.st <= 45) out.push(['ca_pressure', -14, { dm: dmName(f) }]);
    if (f.gods.has('상관') && gwan >= 1 && f.groups.식상 >= 2) out.push(['ca_clash', -10]);
    return out;
  },
  business(f, T) {
    const out = [];
    if (f.groups.식상 >= 1 && f.groups.재성 >= 1) out.push(['bu_flow', 12]);
    if (f.gods.has('편재')) out.push(['bu_pyeonjae', 8]);
    if (f.st >= 55) out.push(['bu_strong', 10]);
    if (f.names.has('양인살')) out.push(['bu_drive', 6, T.DRIVE.양인살]);
    else if (f.names.has('괴강살')) out.push(['bu_drive', 6, T.DRIVE.괴강살]);
    if (f.st <= 30) out.push(['bu_weak', -14]); else if (f.st <= 45) out.push(['bu_weak', -8]);
    if (f.groups.비겁 >= 3) out.push(['bu_partner', -10, { count: f.groups.비겁 }]);
    if (f.groups.재성 === 0) out.push(['bu_nomoney', -8]);
    return out;
  },
  health(f, T) {
    const out = [];
    const vals = ELEMENTS.map(e => [e, f.elements[e]]);
    if (vals.every(([, v]) => v >= 10 && v <= 30)) out.push(['he_balance', 16, { dm: dmName(f) }]);
    if (f.st >= 50 && f.st < 70) out.push(['he_stamina', 6]);
    const lack = vals.filter(([, v]) => v < 8).sort((a, b) => a[1] - b[1] || ELEMENTS.indexOf(b[0]) - ELEMENTS.indexOf(a[0]));   // 같으면 뒤 순서(taster.py 와 같다)
    // 모자란 정도(8%에서 얼마나 모자란지)로 점수를 달리한다(손님마다 늘 34점이 되지 않게). saju/taster.py 와 같은 식.
    const gap = lack.length ? Math.round(8 - lack[0][1]) : 0;
    if (lack.length) out.push(['he_lack', lack.length > 1 ? -(10 + gap) : -(6 + gap), { lack: lack[0][0], lackWord: T.ELEMENT_WORD[lack[0][0]], lackPct: lack[0][1], lackBody: T.ELEMENT_BODY[lack[0][0]] }]);
    const many = vals.filter(([, v]) => v >= 35).sort((a, b) => b[1] - a[1]);
    if (many.length) out.push(['he_excess', -8, { many: many[0][0], manyWord: T.ELEMENT_WORD[many[0][0]], manyPct: many[0][1], manyBody: T.ELEMENT_BODY[many[0][0]] }]);
    if (f.st <= 30) out.push(['he_weak', -8]);
    return out;
  },
};

// 네 기둥 아래 "내 사주 한눈에": 숫자 하나 + 그래서 생활에서 어떤지, 쉬운 말로
function chartDetail(f, T, name) {
  const fp = f.fp;
  const cols = [['시주', fp.hour], ['일주', fp.day], ['월주', fp.month], ['년주', fp.year]]
    .map(([label, p]) => ({ label: T.PILLAR_MEANING[label], hanja: p?.hanja || null, ko: p?.ko || null, me: label === '일주' }));
  const els = ELEMENTS.map(e => ({ el: e, word: T.ELEMENT_WORD[e], pct: f.elements[e], status: f.elements[e] < 8 ? 'lack' : f.elements[e] >= 30 ? 'many' : 'ok' }));
  const sorted = [...els].sort((a, b) => b.pct - a.pct);
  const top = sorted[0], low = sorted[sorted.length - 1];
  const dm = STEMS[f.ds] + ELEMENTS[STEM_EL[f.ds]];
  const gy = f.an.gyeokguk.name;
  const items = [
    { head: `나를 뜻하는 글자 · ${STEM_HANJA[f.ds]} ${dm}`, text: `태어난 날의 위 글자가 나 자신입니다. ${name} 님은 ${T.DAY_MASTER[f.ds]}` },
    { head: `가장 센 기운 · ${top.word} ${top.pct}%`, text: T.ELEMENT_STRONG[top.el] },
    { head: `가장 모자란 기운 · ${low.word} ${low.pct}%`, text: T.ELEMENT_WEAK[low.el] },
    { head: `나를 받쳐 주는 힘 · 100점 중 ${Math.round(f.st)}점`, text: `${T.STRENGTH_PLAIN} ${fill(T.STRENGTH_LINE[f.stLabel], { name })}` },
  ];
  if (T.GYEOK_MEANING[gy]) items.push({ head: `타고난 큰 방향 · ${gy}`, text: T.GYEOK_MEANING[gy] });
  return { zodiac: ZODIAC[fp.year.branch], columns: cols, elements: els, items };
}

// person: { name, sex }, fp: engine.chartFromPerson 결과, T: texts.json
export function reading(fp, person, T) {
  const name = (person.name || '').trim() || '고객';
  const f = facts(fp, person.sex);
  const areas = AREA_ORDER.map((id, order) => {
    const reasons = RULES[id](f, T);
    const score = Math.max(5, Math.min(95, 50 + reasons.reduce((a, r) => a + r[1], 0)));
    return { id, order, score, reasons };
  });
  const good = [...areas].sort((a, b) => b.score - a.score || a.order - b.order).slice(0, 3);
  const bad = areas.filter(a => !good.includes(a)).sort((a, b) => a.score - b.score || a.order - b.order).slice(0, 3);
  const pick = (a, sign) => {
    const own = a.reasons.filter(r => Math.sign(r[1]) === sign).sort((x, y) => Math.abs(y[1]) - Math.abs(x[1]));
    const [key, , vars = {}] = own[0] || [`${PREFIX[a.id]}_base_${sign > 0 ? 'good' : 'bad'}`];
    return { ...T.AREAS[a.id], id: a.id, score: a.score, reason: key, text: fill(T.REASONS[key], { name, ...vars }), hook: fill(T.HOOKS[key], { name, ...vars }) };
  };
  return {
    name,
    pillars: [fp.hour, fp.day, fp.month, fp.year].map((p, i) => ({ label: ['시주', '일주', '월주', '년주'][i], hanja: p?.hanja || null, ko: p?.ko || null })),
    chart: chartDetail(f, T, name),
    good: good.map(a => pick(a, 1)),
    bad: bad.map(a => pick(a, -1)),
    scores: Object.fromEntries(areas.map(a => [a.id, a.score])),
  };
}

// 상품 하나의 운(결제 전 이야기 화면의 '내 점수'): 점수와, 맛보기와 같은 쪽(좋은 운/조심할 운)의 근거 글.
// 맛보기 TOP3 안에 있으면 맛보기와 같은 글, 가운데 운은 점수가 50 이상이면 좋은 쪽, 아니면 조심할 쪽.
export function areaView(fp, person, T, id) {
  const r = reading(fp, person, T);
  const hit = [...r.good, ...r.bad].find(a => a.id === id);
  if (hit) return { ...hit, sign: r.good.includes(hit) ? 1 : -1, scores: r.scores, chart: r.chart, pillars: r.pillars };
  const name = (person.name || '').trim() || '고객';
  const score = r.scores[id], sign = score >= 50 ? 1 : -1;
  const own = RULES[id](facts(fp, person.sex), T).filter(x => Math.sign(x[1]) === sign).sort((x, y) => Math.abs(y[1]) - Math.abs(x[1]));
  const [key, , vars = {}] = own[0] || [`${PREFIX[id]}_base_${sign > 0 ? 'good' : 'bad'}`];
  return { ...T.AREAS[id], id, score, reason: key, text: fill(T.REASONS[key], { name, ...vars }), hook: fill(T.HOOKS[key], { name, ...vars }), sign, scores: r.scores, chart: r.chart, pillars: r.pillars };
}

// 상품 하나의 운을 좋은 점과 조심할 점으로 나눈다(결제 전 이야기 화면 '내 점수', 사장님 2026-10-28).
// 좋은 점 점수 = 50 + 좋은 근거 점수 합, 조심할 점 점수 = 50 + 나쁜 근거 점수 합. 근거가 없는 쪽은 null.
export function areaParts(fp, person, T, id) {
  const name = (person.name || '').trim() || '고객';
  const reasons = RULES[id](facts(fp, person.sex), T);
  const part = sign => {
    const own = reasons.filter(x => Math.sign(x[1]) === sign).sort((x, y) => Math.abs(y[1]) - Math.abs(x[1]));
    if (!own.length) return null;
    const [key, , vars = {}] = own[0];
    const score = Math.max(5, Math.min(95, 50 + own.reduce((a, x) => a + x[1], 0)));
    return { score, reason: key, text: fill(T.REASONS[key], { name, ...vars }), hook: fill(T.HOOKS[key], { name, ...vars }) };
  };
  return { id, score: Math.max(5, Math.min(95, 50 + reasons.reduce((a, x) => a + x[1], 0))), good: part(1), bad: part(-1) };
}

// 손님이 답한 지금 상황에 맞춰 화면 글의 한 문장을 바꾼다(texts.json SITUATION.swap, saju/taster.py situ_text 와 같다).
// 결혼한 분에게 '고르는 눈이 필요합니다', 사업하는 분에게 '월급 밖의 돈' 같은 문장이 나오지 않게(사장님 2026-11-06 저녁 1-2).
export function situText(path, text, answers, T, product) {
  const S = T.SITUATION.swap?.[path];
  if (!S || !text) return text;
  const vals = new Set(Object.values(answers || {}).filter(Boolean).map(String));
  let rules = null;
  for (const [key, opts] of Object.entries(T.SITUATION.groups)) if (S[key] && opts.some(o => vals.has(o))) { rules = S[key]; break; }
  if (!rules && product && S['@' + product]) rules = S['@' + product];
  return rules ? rules.reduce((t, [a, b]) => t.split(a).join(b), text) : text;
}

// 손님이 답한 지금 상황(연애 중·결혼·쉬는 중…)에 맞춰 그 운이 어떻게 나타나는지 한 줄(saju/taster.py situation_note 와 같다).
export function situationNote(area, answers, T) {
  const vals = new Set(Object.values(answers || {}).filter(Boolean).map(String));
  for (const [key, opts] of Object.entries(T.SITUATION.groups)) if (opts.some(o => vals.has(o)) && T.SITUATION.notes[area]?.[key]) return T.SITUATION.notes[area][key];
  return '';
}
