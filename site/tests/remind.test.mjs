// 결제 이어하기 안내 메일(선택 동의, 2026-11-05): 동의한 사람만, 최대 2번, 결제하면 멈추고, 수신 거부가 된다.
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeApi, memoryStore } from '../netlify/functions/lib/api.mjs';
import { sendReminders, reminderMail } from '../netlify/functions/lib/remind.mjs';
import { emailHash, afterPaid } from '../netlify/functions/lib/discounts.mjs';
import { productName } from '../netlify/functions/lib/orders.mjs';

const ENV = { TOSS_CLIENT_KEY: 'test_ck', TOSS_SECRET_KEY: 'test_sk', GH_DISPATCH_TOKEN: 'gh', WORKER_SECRET: 'w', RESEND_API_KEY: 're' };
function setup() {
  const store = memoryStore(), sent = [];
  const services = { sendReminder: async (rec, n) => { sent.push({ to: rec.email, n, product: rec.productId }); } };
  const api = makeApi({ store, services, env: ENV });
  const post = body => api(new Request('https://x.test/api/remind', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }));
  return { store, services, sent, api, post };
}
const H = 3600_000;

test('동의하지 않으면 저장하지 않고, 동의하면 이메일·상품만 저장한다', async () => {
  const t = setup();
  assert.equal((await t.post({ email: 'a@naver.com', productId: 'newyear', consent: false })).status, 200);
  assert.equal((await t.store.list('remind/')).length, 0);
  assert.equal((await t.post({ email: 'bad', productId: 'newyear', consent: true })).status, 400);
  assert.equal((await t.post({ email: 'A@Naver.com ', productId: 'newyear', consent: true, name: '김지은', birth: '1995-03-15' })).status, 200);
  const rec = await t.store.get(`remind/${emailHash('a@naver.com')}`);
  assert.equal(rec.email, 'a@naver.com'); assert.equal(rec.productId, 'newyear');
  assert.equal(rec.name, undefined); assert.equal(rec.birth, undefined);
  await t.post({ email: 'a@naver.com', consent: false });
  assert.equal((await t.store.list('remind/')).length, 0);
});

test('1시간 뒤 1번, 24시간 뒤 1번, 그 뒤로는 보내지 않는다', async () => {
  const t = setup(), t0 = new Date('2026-11-05T03:00:00Z');
  await t.post({ email: 'b@gmail.com', productId: 'reunion', consent: true });
  const key = `remind/${emailHash('b@gmail.com')}`;
  await t.store.set(key, { ...(await t.store.get(key)), startedAt: t0.toISOString() });
  assert.equal(await sendReminders(t.store, t.services, new Date(+t0 + 30 * 60_000)), 0);
  assert.equal(await sendReminders(t.store, t.services, new Date(+t0 + 1.1 * H)), 1);
  assert.equal(await sendReminders(t.store, t.services, new Date(+t0 + 2 * H)), 0);
  assert.equal(await sendReminders(t.store, t.services, new Date(+t0 + 25 * H)), 1);
  assert.equal(await sendReminders(t.store, t.services, new Date(+t0 + 49 * H)), 0);
  assert.deepEqual(t.sent.map(s => s.n), [1, 2]);
  assert.equal(await t.store.get(key), null);
});

test('결제하면 안내를 보내지 않는다', async () => {
  const t = setup(), t0 = new Date('2026-11-05T03:00:00Z');
  await t.post({ email: 'c@daum.net', productId: 'wealth', consent: true });
  await afterPaid(t.store, { email: 'c@daum.net' }, new Date(+t0 + 10 * 60_000));
  assert.equal(await sendReminders(t.store, t.services, new Date(Date.now() + 2 * H)), 0);
  assert.equal(t.sent.length, 0);
});

test('수신 거부 링크로 지우고, 잘못된 열쇠는 거부한다', async () => {
  const t = setup();
  await t.post({ email: 'd@kakao.com', productId: 'romance', consent: true });
  const h = emailHash('d@kakao.com'), rec = await t.store.get(`remind/${h}`);
  const bad = await t.api(new Request(`https://x.test/api/unsubscribe?h=${h}&t=nope`));
  assert.match(await bad.text(), /잘못된 링크/);
  assert.ok(await t.store.get(`remind/${h}`));
  const ok = await t.api(new Request(`https://x.test/api/unsubscribe?h=${h}&t=${rec.token}`));
  assert.match(await ok.text(), /수신 거부가 끝났어요/);
  assert.equal(await t.store.get(`remind/${h}`), null);
  assert.ok(await t.store.get(`optout/${h}`));
});

test('메일 글: 제목에 (광고), 보낸 곳, 수신 거부, 할인 없음', () => {
  const rec = { email: 'e@x.com', productId: 'newyear', hash: 'a'.repeat(64), token: 't'.repeat(32), consentAt: '2026-11-05T03:00:00Z' };
  for (const n of [1, 2]) {
    const m = reminderMail(rec, n, 'https://unmyeong-saju.com', productName);
    assert.match(m.subject, /^\(광고\) /);
    assert.match(m.text, /수신 거부|더 받지 않으려면/); assert.match(m.text, /상호 김승용/);
    assert.match(m.text, /\/p\/newyear\/\?from=remind/);
    assert.doesNotMatch(m.text + m.subject, /할인|쿠폰|%/);
  }
});
