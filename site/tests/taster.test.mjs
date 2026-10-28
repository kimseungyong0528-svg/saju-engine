import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as eng from '../public/assets/free/engine.mjs';

const data = JSON.parse(readFileSync(new URL('../public/assets/free/saju-data.json', import.meta.url)));
const cases = JSON.parse(readFileSync(new URL('./fixtures/taster-parity.json', import.meta.url)));
const T = JSON.parse(readFileSync(new URL('../public/assets/free/texts.json', import.meta.url)));

test('맛보기 계산기가 파이썬 사주 엔진과 같은 명식·분석을 낸다', () => {
  const bad = [];
  for (const c of cases) {
    const fp = eng.chartFromPerson(data, c.person, c.person.birth);
    const key = [fp.year, fp.month, fp.day, fp.hour].map(p => p ? p.ko : '??').join(' ');
    const an = eng.analyze(fp);
    const got = {
      key, groups: an.groups, strength: an.strength.score, gyeokguk: an.gyeokguk.name,
      shinsal: an.shinsal.map(s => s.name + '|' + s.pillar).sort(),
    };
    const want = { key: c.key, groups: c.groups, strength: c.strength, gyeokguk: c.gyeokguk, shinsal: c.shinsal };
    const elOk = eng.ELEMENTS.every(e => Math.abs(an.elements[e] - c.elements[e]) <= 0.1001);
    try { assert.deepEqual(got, want); assert.ok(elOk, 'elements'); } catch { bad.push({ birth: c.person.birth, time: c.person.time, got, want }); }
  }
  assert.equal(bad.length, 0, JSON.stringify(bad.slice(0, 3), null, 1));
});

test('맛보기 결과: 좋은 운 3개·조심할 운 3개, 빈칸 없는 글, 파이썬(결제 리포트 쪽)과 같은 결과', async () => {
  const { reading } = await import('../public/assets/free/taster.mjs');
  const ids = new Set(['newyear', 'romance', 'intimate', 'reunion', 'wealth', 'career', 'business', 'health']);
  for (const c of cases) {
    const r = reading(eng.chartFromPerson(data, c.person, c.person.birth), c.person, T);
    assert.equal(r.good.length, 3); assert.equal(r.bad.length, 3);
    const all = [...r.good, ...r.bad];
    assert.equal(new Set(all.map(a => a.id)).size, 6);
    for (const a of all) {
      assert.ok(ids.has(a.product));
      assert.ok(!/[{}]|undefined|NaN/.test(a.text), a.text);
      assert.ok(!/참고용|재미로/.test(a.text));
      assert.ok(a.hook && !/[{}]|undefined|NaN/.test(a.hook), a.hook);
      // 후킹 적정선(사장님 2026-10-27): 반발심이 들 만큼 겁주는 말은 쓰지 않는다. docs/free-taster.md
      assert.ok(!/돌이킬/.test(a.hook), a.hook);
    }
    const pick = x => x.map(a => [a.id, a.reason, a.text, a.hook]);
    assert.deepEqual({ good: pick(r.good), bad: pick(r.bad), scores: r.scores },
      { good: pick(c.reading.good), bad: pick(c.reading.bad), scores: c.reading.scores }, c.person.birth + ' ' + c.person.time);
    assert.ok(r.chart.columns.length === 4 && r.chart.elements.length === 5);
  }
});

test('결제 전 이야기 화면: 상품별 점수 글과 해·달 지도가 파이썬(결제 리포트 쪽)과 같다', async () => {
  const { areaView } = await import('../public/assets/free/taster.mjs');
  const { luckMap } = await import('../public/assets/free/reveal.mjs');
  for (const c of cases) {
    const fp = eng.chartFromPerson(data, c.person, c.person.birth);
    for (const [id, want] of Object.entries(c.areas)) {
      const a = areaView(fp, c.person, T, id);
      assert.deepEqual({ id: a.id, score: a.score, reason: a.reason, text: a.text, hook: a.hook, sign: a.sign }, want, c.person.birth + ' ' + id);
    }
    for (const [pid, want] of Object.entries(c.maps)) {
      const m = luckMap(fp, c.person.sex, pid, T);
      assert.deepEqual(m, want, c.person.birth + ' ' + pid);
      // 지도마다 좋은 표시가 적어도 하나 있어야 화면이 비지 않는다
      assert.ok(Object.keys(m.good).length > 0 || pid === 'reunion' || pid === 'intimate', pid + ' 좋은 표시 없음');
    }
  }
});
