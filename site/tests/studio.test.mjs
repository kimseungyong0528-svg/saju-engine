// 관리 사이트(/studio) 서버 시험: 비밀번호 잠금, 게시물 묶음 올리기, 만들기 버튼, 오래된 묶음 지우기.
import test from 'node:test';
import assert from 'node:assert/strict';
import { makeApi, memoryStore } from '../netlify/functions/lib/api.mjs';
import { eraseOldWeeks } from '../netlify/functions/lib/studio.mjs';

const ENV = { WORKER_SECRET: 'worker-secret', STUDIO_PASSWORD: 'open-sesame-123', GH_DISPATCH_TOKEN: 'gh' };

function setup(env = ENV) {
  const store = memoryStore(), studioStore = memoryStore();
  const calls = { studio: [] };
  const services = { startStudio: async s => { calls.studio.push(s); } };
  const api = makeApi({ store, studioStore, services, env });
  let cookie = '';
  const call = async (method, path, { body, headers = {}, raw } = {}) => {
    const r = await api(new Request('https://x.test' + path, {
      method, headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...(cookie ? { cookie } : {}), ...headers },
      body: raw ?? (body ? JSON.stringify(body) : undefined),
    }));
    const set = r.headers.get('set-cookie');
    if (set) cookie = set.split(';')[0];
    return r;
  };
  return { store, studioStore, calls, call, worker: { 'x-worker-secret': 'worker-secret' } };
}

const manifest = week => ({ week, days: [{ date: week, items: [{ id: 'a' }, { id: 'b' }] }], problems: [], used: ['말', 'jeongmi'] });

test('로그인 전에는 아무것도 볼 수 없다', async () => {
  const t = setup();
  assert.equal((await t.call('GET', '/api/studio/weeks')).status, 401);
  assert.equal((await t.call('GET', '/api/studio/file/2026-10-19?path=a.png')).status, 401);
  const me = await (await t.call('GET', '/api/studio/me')).json();
  assert.deepEqual(me, { loggedIn: false, configured: true });
});

test('비밀번호가 틀리면 거절, 맞으면 쿠키로 들어간다', async () => {
  const t = setup();
  assert.equal((await t.call('POST', '/api/studio/login', { body: { password: 'nope' } })).status, 401);
  const r = await t.call('POST', '/api/studio/login', { body: { password: 'open-sesame-123' } });
  assert.equal(r.status, 200);
  assert.match(r.headers.get('set-cookie'), /HttpOnly; Secure; SameSite=Strict/);
  assert.equal((await t.call('GET', '/api/studio/weeks')).status, 200);
  await t.call('POST', '/api/studio/logout');
  assert.equal((await t.call('GET', '/api/studio/weeks')).status, 401);
});

test('비밀번호를 설정하지 않으면 로그인 자체가 안 된다', async () => {
  const t = setup({ WORKER_SECRET: 'worker-secret' });
  assert.equal((await t.call('POST', '/api/studio/login', { body: { password: '' } })).status, 503);
});

test('로그인 실패는 한 시간에 20번까지만', async () => {
  const t = setup();
  for (let i = 0; i < 20; i++) await t.call('POST', '/api/studio/login', { body: { password: 'x' } });
  assert.equal((await t.call('POST', '/api/studio/login', { body: { password: 'open-sesame-123' } })).status, 429);
});

test('작업이 파일과 목록을 올리면 화면에서 보인다, 비밀 열쇠 없이는 못 올린다', async () => {
  const t = setup();
  assert.equal((await t.call('PUT', '/api/internal/studio/2026-10-19/file?path=a.png', { raw: 'x' })).status, 403);
  assert.equal((await t.call('PUT', '/api/internal/studio/2026-10-19/file?path=../x', { raw: 'x', headers: t.worker })).status, 400);
  assert.equal((await t.call('PUT', `/api/internal/studio/2026-10-19/file?path=${encodeURIComponent('유튜브/10-19_오전_말.mp4')}`, { raw: 'video', headers: t.worker })).status, 200);
  await t.call('POST', '/api/internal/studio/2026-10-19/manifest', { body: manifest('2026-10-19'), headers: t.worker });
  await t.call('POST', '/api/studio/login', { body: { password: 'open-sesame-123' } });
  const weeks = (await (await t.call('GET', '/api/studio/weeks')).json()).weeks;
  assert.equal(weeks[0].week, '2026-10-19'); assert.equal(weeks[0].status, 'ready'); assert.equal(weeks[0].posts, 2);
  const f = await t.call('GET', `/api/studio/file/2026-10-19?path=${encodeURIComponent('유튜브/10-19_오전_말.mp4')}`);
  assert.equal(f.headers.get('content-type'), 'video/mp4'); assert.equal(await f.text(), 'video');
  const used = await (await t.call('GET', '/api/internal/studio/used', { headers: t.worker })).json();
  assert.deepEqual(used.keys, ['말', 'jeongmi']);
});

test('올렸음 체크가 저장된다', async () => {
  const t = setup();
  await t.call('POST', '/api/studio/login', { body: { password: 'open-sesame-123' } });
  await t.call('POST', '/api/studio/done', { body: { week: '2026-10-19', id: '10-19_오전-youtube', done: true } });
  let w = await (await t.call('GET', '/api/studio/weeks/2026-10-19')).json();
  assert.ok(w.done['10-19_오전-youtube']);
  await t.call('POST', '/api/studio/done', { body: { week: '2026-10-19', id: '10-19_오전-youtube', done: false } });
  w = await (await t.call('GET', '/api/studio/weeks/2026-10-19')).json();
  assert.deepEqual(w.done, {});
});

test('만들기 버튼은 깃허브 작업을 한 번만 시작한다', async () => {
  const t = setup();
  await t.call('POST', '/api/studio/login', { body: { password: 'open-sesame-123' } });
  assert.equal((await t.call('POST', '/api/studio/generate', { body: { start: '2026-13' } })).status, 400);
  assert.equal((await t.call('POST', '/api/studio/generate', { body: { start: '2026-10-19' } })).status, 200);
  assert.equal((await t.call('POST', '/api/studio/generate', { body: { start: '2026-10-19' } })).status, 409);
  assert.deepEqual(t.calls.studio, ['2026-10-19']);
});

test('35일 지난 묶음은 파일까지 지운다', async () => {
  const t = setup();
  for (const w of ['2026-08-01', '2026-10-19']) {
    await t.call('PUT', `/api/internal/studio/${w}/file?path=a.png`, { raw: 'x', headers: t.worker });
    await t.call('POST', `/api/internal/studio/${w}/manifest`, { body: manifest(w), headers: t.worker });
  }
  const n = await eraseOldWeeks(t.studioStore, Date.parse('2026-10-20'));
  assert.equal(n, 1);
  assert.equal(await t.studioStore.getBytes('files/2026-08-01/a.png'), null);
  assert.ok(await t.studioStore.getBytes('files/2026-10-19/a.png'));
});

test('승인한 게시물만 오늘 목록에 승인으로 나오고, 올린 결과가 남는다', async () => {
  const t = setup();
  const day = { week: '2026-11-02', days: [{ date: '2026-11-02', items: [{ id: 'r', slot: '오전', channel: 'instagram-reel' }, { id: 'th', slot: '저녁', channel: 'threads' }] }], problems: [], used: [] };
  await t.call('POST', '/api/internal/studio/2026-11-02/manifest', { body: day, headers: t.worker });
  await t.call('POST', '/api/studio/login', { body: { password: 'open-sesame-123' } });
  assert.equal((await t.call('POST', '/api/studio/approve', { body: { week: '2026-11-02', ids: ['r', 'th'], approved: true } })).status, 200);
  await t.call('POST', '/api/studio/approve', { body: { week: '2026-11-02', id: 'th', approved: false } });
  assert.equal((await t.call('GET', '/api/internal/studio/today?date=2026-11-02')).status, 403);
  const plan = await (await t.call('GET', '/api/internal/studio/today?date=2026-11-02', { headers: t.worker })).json();
  assert.equal(plan.week, '2026-11-02');
  assert.deepEqual(Object.keys(plan.approved), ['r']);
  await t.call('POST', '/api/internal/studio/2026-11-02/posted', { body: { id: 'r', ok: true, url: 'https://instagram.com/p/x' }, headers: t.worker });
  const view = await (await t.call('GET', '/api/studio/weeks/2026-11-02')).json();
  assert.equal(view.posted.r.ok, true);
  assert.deepEqual(Object.keys(view.approved), ['r']);
  const none = await (await t.call('GET', '/api/internal/studio/today?date=2026-11-05', { headers: t.worker })).json();
  assert.equal(none.week, null);
});

test('메타가 가져가는 파일 주소는 서명이 맞아야 열린다', async () => {
  const { pubSig } = await import('../netlify/functions/lib/studio.mjs');
  const t = setup();
  await t.call('PUT', '/api/internal/studio/2026-11-02/file?path=' + encodeURIComponent('인스타/a.jpg'), { raw: new Uint8Array([1, 2, 3]), headers: { ...t.worker, 'Content-Type': 'image/jpeg' } });
  const sig = pubSig(ENV, '2026-11-02', '인스타/a.jpg');
  const ok = await t.call('GET', `/api/studio/pub/2026-11-02?path=${encodeURIComponent('인스타/a.jpg')}&sig=${sig}`);
  assert.equal(ok.status, 200);
  assert.equal(ok.headers.get('content-type'), 'image/jpeg');
  assert.equal((await t.call('GET', `/api/studio/pub/2026-11-02?path=${encodeURIComponent('인스타/a.jpg')}&sig=bad`)).status, 403);
  assert.equal((await t.call('GET', `/api/studio/pub/2026-11-02?path=${encodeURIComponent('인스타/b.jpg')}&sig=${sig}`)).status, 403);
});

test('스레드 열쇠를 저장하고 꺼낸다 (작업 비밀 열쇠로만)', async () => {
  const t = setup();
  assert.equal((await t.call('GET', '/api/internal/studio/meta/threads-token')).status, 403);
  await t.call('POST', '/api/internal/studio/meta/threads-token', { body: { token: 'THAA'.padEnd(40, 'x'), refreshedAt: '2026-11-01T00:00:00Z' }, headers: t.worker });
  const j = await (await t.call('GET', '/api/internal/studio/meta/threads-token', { headers: t.worker })).json();
  assert.equal(j.refreshedAt, '2026-11-01T00:00:00Z');
});

test('손님이 온 곳: 로그인한 사장님만 최근 3달 결제 수를 본다', async () => {
  const t = setup();
  assert.equal((await t.call('GET', '/api/studio/sources')).status, 401);
  await t.call('POST', '/api/studio/login', { body: { password: 'open-sesame-123' } });
  const month = new Date(Date.now() + 9 * 3600_000).toISOString().slice(0, 7);
  await t.store.set(`stats/sources/${month}`, { d: { orders: 2, amount: 59600 } });
  const j = await (await t.call('GET', '/api/studio/sources')).json();
  assert.equal(j.months.length, 3); assert.equal(j.months[0].month, month);
  assert.deepEqual(j.months[0].sources.d, { orders: 2, amount: 59600 });
});
