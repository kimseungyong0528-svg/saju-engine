// 무료 맛보기 결과 메일(2026-11-05). 손님이 요청할 때만, 서버가 다시 계산한 결과로, 생년월일은 저장하지 않고, 할인·가격은 없다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { makeApi, memoryStore } from '../netlify/functions/lib/api.mjs';
import { eraseOldLeads, emailHash } from '../netlify/functions/lib/leads.mjs';
import * as eng from '../public/assets/free/engine.mjs';
import { reading } from '../public/assets/free/taster.mjs';

const data = JSON.parse(readFileSync(new URL('../public/assets/free/saju-data.json', import.meta.url)));
const texts = JSON.parse(readFileSync(new URL('../public/assets/free/texts.json', import.meta.url)));
const ENV = { TOSS_CLIENT_KEY: 'live_ck', TOSS_SECRET_KEY: 'live_sk', GH_DISPATCH_TOKEN: 'gh', WORKER_SECRET: 'w', RESEND_API_KEY: 're', SITE_URL: 'https://unmyeong-saju.com' };
const person = { name: '김테스트', sex: 'female', calendar: 'solar', birth: '1995-03-14', timeAccuracy: 'exact', time: '06:30' };

function setup() {
  const store = memoryStore(), sent = [];
  const services = { sendMail: async (m, key) => { sent.push({ ...m, key }); return 'id'; } };
  const api = makeApi({ store, services, env: ENV, assets: async () => ({ data, texts }) });
  const post = (body, ip = '1.2.3.4') => api(new Request('https://x.test/api/taster-mail', { method: 'POST', headers: { 'Content-Type': 'application/json', 'x-nf-client-connection-ip': ip }, body: JSON.stringify(body) }));
  return { store, sent, api, post };
}
const birthLeft = store => [...store.data.values()].some(v => JSON.stringify(v).includes('1995-03-14') || JSON.stringify(v).includes('06:30'));

test('결과 메일: 화면과 같은 좋은 운 3개·조심할 운 3개를 보내고, 생년월일은 남기지 않는다', async () => {
  const t = setup();
  const r = await t.post({ email: 'a@example.com', agree: true, person, solar: person.birth });
  assert.equal(r.status, 200);
  assert.equal(t.sent.length, 1);
  const m = t.sent[0];
  const want = reading(eng.chartFromPerson(data, person, person.birth), person, texts);
  for (const a of [...want.good, ...want.bad]) { assert.ok(m.text.includes(a.title), a.title); assert.ok(m.text.includes(a.text)); }
  assert.deepEqual(m.to, ['a@example.com']);
  assert.match(m.subject, /김테스트님의 무료 사주 결과/);
  assert.ok(!/할인|\d,\d{3}원|\d+%\s*(할인|off)/i.test(m.text), '할인·가격은 메일에 쓰지 않는다(2026-10-27 사장님)');
  assert.ok(m.text.includes('AI 안내자'));
  assert.ok(m.text.includes('다른 메일은 보내지 않아요'));
  assert.ok(!birthLeft(t.store));
  assert.equal((await t.store.list('leads/')).length, 0, '소식 받기를 안 고르면 이메일을 보관하지 않는다');
});

test('동의 없이, 잘못된 이메일·이름이면 보내지 않는다', async () => {
  const t = setup();
  assert.equal((await t.post({ email: 'a@example.com', person, solar: person.birth })).status, 400);
  assert.equal((await t.post({ email: 'not-mail', agree: true, person, solar: person.birth })).status, 400);
  assert.equal((await t.post({ email: 'a@example.com', agree: true, person: { ...person, name: '<a href=x>' }, solar: person.birth })).status, 400);
  assert.equal((await t.post({ email: 'a@example.com', agree: true, person, solar: '1995-13-40' })).status, 400);
  assert.equal(t.sent.length, 0);
});

test('같은 이메일은 하루 3번, 같은 곳에서는 한 시간 10번까지만', async () => {
  const t = setup();
  for (let i = 0; i < 3; i++) assert.equal((await t.post({ email: 'b@example.com', agree: true, person, solar: person.birth }, '9.9.9.' + i)).status, 200);
  const r = await t.post({ email: 'b@example.com', agree: true, person, solar: person.birth }, '9.9.9.9');
  assert.equal(r.status, 429); assert.equal((await r.json()).code, 'TOO_MANY');
  const u = setup();
  for (let i = 0; i < 10; i++) assert.equal((await u.post({ email: `c${i}@example.com`, agree: true, person, solar: person.birth })).status, 200);
  assert.equal((await u.post({ email: 'c99@example.com', agree: true, person, solar: person.birth })).status, 429);
});

test('소식 받기(선택)를 고른 분만 이메일을 보관하고, 메일 속 링크로 바로 지운다', async () => {
  const t = setup();
  assert.equal((await t.post({ email: 'N@Example.com', agree: true, news: true, person, solar: person.birth, from: 'd' })).status, 200);
  const keys = await t.store.list('leads/');
  assert.equal(keys.length, 1);
  const rec = await t.store.get(keys[0]);
  assert.equal(rec.email, 'N@Example.com'); assert.equal(rec.from, 'd'); assert.ok(rec.consentAt);
  assert.ok(!birthLeft(t.store));
  const link = t.sent[0].text.match(/https:\/\/unmyeong-saju\.com\/api\/leads\/stop\?id=[0-9a-f]+&t=[0-9a-f]+/)[0];
  const wrong = await t.api(new Request(link.replace(/t=[0-9a-f]+/, 't=00').replace('https://unmyeong-saju.com', 'https://x.test')));
  assert.equal(wrong.status, 200); assert.equal((await t.store.list('leads/')).length, 1, '틀린 열쇠로는 지우지 않는다');
  const ok = await t.api(new Request(link.replace('https://unmyeong-saju.com', 'https://x.test')));
  assert.equal(ok.status, 200); assert.match(await ok.text(), /그만두었어요/);
  assert.equal((await t.store.list('leads/')).length, 0);
  assert.equal(keys[0], 'leads/' + emailHash('n@example.com'));
});

test('정리 작업: 지난 보내기 횟수 기록과 2년 지난 소식 기록을 지운다', async () => {
  const store = memoryStore();
  await store.set('lead-rate/e/abc/2026-11-04', { n: 1 });
  await store.set('lead-rate/e/abc/2026-11-05', { n: 1 });
  await store.set('lead-rate/ip/xyz/2026-11-05T09', { n: 1 });
  await store.set('lead-rate/ip/xyz/2026-11-05T10', { n: 1 });
  await store.set('leads/old', { email: 'o@x.com', updatedAt: '2024-01-01T00:00:00.000Z' });
  await store.set('leads/new', { email: 'n@x.com', updatedAt: '2026-11-01T00:00:00.000Z' });
  assert.equal(await eraseOldLeads(store, new Date('2026-11-05T10:30:00Z')), 3);
  assert.deepEqual((await store.list('')).sort(), ['lead-rate/e/abc/2026-11-05', 'lead-rate/ip/xyz/2026-11-05T10', 'leads/new']);
});
