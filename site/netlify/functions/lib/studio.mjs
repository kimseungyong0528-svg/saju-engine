// 관리 사이트(/studio) 서버: 사장님만 쓰는 SNS 게시물 화면.
// 비밀번호(STUDIO_PASSWORD)로 로그인하면 서명된 쿠키를 준다. 게시물 파일은 별도 저장소(unmyeong-studio)에만 두므로
// 게시물을 만들어도 사이트 배포는 일어나지 않는다.
import { createHmac } from 'node:crypto';
import { ApiError, sameSecret } from './orders.mjs';

const COOKIE = 'studio_s';
const DAYS30 = 30 * 24 * 3600;
const KEEP_DAYS = 35;
const WEEK_RE = /^\d{4}-\d{2}-\d{2}$/;
const PATH_RE = /^[\p{L}\p{N}_\-. ()/]+$/u;
const TYPES = { png: 'image/png', jpg: 'image/jpeg', mp4: 'video/mp4', txt: 'text/plain; charset=utf-8' };
const MAX_FILE = 5_500_000;

const json = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...headers },
});

// 메타(인스타·페북·스레드)가 영상·사진을 가져갈 때 쓰는 서명된 주소. 로그인 없이 열리지만 서명이 맞아야 한다.
export function pubSig(env, week, path) {
  return createHmac('sha256', env.WORKER_SECRET || '').update(`pub:${week}/${path}`).digest('hex');
}

function sign(env, exp) {
  return createHmac('sha256', `${env.STUDIO_PASSWORD}|${env.WORKER_SECRET}`).update(`studio:${exp}`).digest('hex');
}

export function sessionCookie(env, now = Date.now()) {
  const exp = Math.floor(now / 1000) + DAYS30;
  return `${COOKIE}=${exp}.${sign(env, exp)}; Path=/; Max-Age=${DAYS30}; HttpOnly; Secure; SameSite=Strict`;
}

function loggedIn(req, env, now = Date.now()) {
  if (!env.STUDIO_PASSWORD || !env.WORKER_SECRET) return false;
  const raw = (req.headers.get('cookie') || '').split(/;\s*/).find(c => c.startsWith(`${COOKIE}=`));
  if (!raw) return false;
  const [exp, mac] = raw.slice(COOKIE.length + 1).split('.');
  if (!exp || !mac || Number(exp) * 1000 < now) return false;
  return sameSecret(mac, sign(env, exp));
}

async function body(req, limit = 65_536) {
  const text = await req.text();
  if (text.length > limit) throw new ApiError(413, 'TOO_LARGE');
  try { return text ? JSON.parse(text) : {}; } catch { throw new ApiError(400, 'BAD_JSON'); }
}

const checkWeek = w => { if (!WEEK_RE.test(w || '')) throw new ApiError(400, 'BAD_WEEK'); return w; };
function checkPath(p) {
  if (!p || p.length > 200 || p.includes('..') || p.startsWith('/') || !PATH_RE.test(p)) throw new ApiError(400, 'BAD_PATH');
  return p;
}

async function index(store) { return (await store.get('weeks')) || []; }
async function setWeek(store, week, patch) {
  const list = await index(store);
  const i = list.findIndex(w => w.week === week);
  const row = { ...(i >= 0 ? list[i] : { week }), ...patch, updatedAt: new Date().toISOString() };
  if (i >= 0) list[i] = row; else list.push(row);
  list.sort((a, b) => b.week.localeCompare(a.week));
  await store.set('weeks', list);
  return row;
}

// 로그인 실패를 한 시간에 20번까지만 받는다(비밀번호 맞히기 막기).
async function tooMany(store, now = new Date()) {
  const key = `login-fails/${now.toISOString().slice(0, 13)}`;
  const n = (await store.get(key)) || 0;
  return { blocked: n >= 20, bump: () => store.set(key, n + 1) };
}

export function makeStudio({ store, services, env, orderStore = store }) {
  return async function handle(req, parts) {
    const m = req.method;
    const url = new URL(req.url);
    const route = parts.join('/');

    // ── 관리 작업(깃허브)에서 오는 요청: WORKER_SECRET 확인 ──
    if (parts[0] === 'internal') {
      if (!sameSecret(req.headers.get('x-worker-secret') || '', env.WORKER_SECRET || '')) throw new ApiError(403, 'FORBIDDEN');
      if (m === 'GET' && parts[2] === 'used') {
        const keys = [];
        // 하루치 묶음도 한 줄이라 넉넉히 3주치를 본다
        // before=시작일: 같은 주를 다시 만들 때는 그 주와 뒤 묶음의 재료를 빼고 본다 (심사한 글이 그대로 다시 나오게)
        const before = url.searchParams.get('before') || '';
        for (const w of (await index(store)).filter(w => !before || w.week < before).slice(0, 21)) {
          const man = await store.get(`manifest/${w.week}`);
          if (man?.used) keys.push(...man.used);
        }
        return json({ keys: [...new Set(keys)] });
      }
      // 오늘 올릴 게시물: 그날이 들어 있는 가장 최근 묶음 + 승인·올림 표시
      if (m === 'GET' && parts[2] === 'today') {
        const date = checkWeek(url.searchParams.get('date'));
        for (const w of (await index(store)).filter(w => w.status === 'ready' && w.week <= date).slice(0, 10)) {
          const man = await store.get(`manifest/${w.week}`);
          const day = man?.days?.find(d => d.date === date);
          if (day) return json({ week: w.week, items: day.items, approved: (await store.get(`approved/${w.week}`)) || {}, posted: (await store.get(`posted/${w.week}`)) || {} });
        }
        return json({ week: null, items: [] });
      }
      if (parts[2] === 'meta' && parts[3] === 'threads-token') {
        if (m === 'GET') return json((await store.get('meta/threads-token')) || {});
        if (m === 'POST') {
          const b = await body(req);
          if (typeof b.token !== 'string' || b.token.length < 20) throw new ApiError(400, 'BAD_TOKEN');
          await store.set('meta/threads-token', { token: b.token, refreshedAt: String(b.refreshedAt || new Date().toISOString()) });
          return json({ ok: true });
        }
      }
      const week = checkWeek(parts[2]);
      const action = parts[3];
      if (m === 'POST' && action === 'posted') {
        const b = await body(req);
        if (typeof b.id !== 'string' || b.id.length > 80) throw new ApiError(400, 'BAD_ID');
        const posted = (await store.get(`posted/${week}`)) || {};
        posted[b.id] = { ok: Boolean(b.ok), url: String(b.url || '').slice(0, 300), error: String(b.error || '').slice(0, 300), at: new Date().toISOString() };
        await store.set(`posted/${week}`, posted);
        return json({ ok: true });
      }
      if (m === 'POST' && action === 'status') {
        const b = await body(req);
        return json(await setWeek(store, week, { status: String(b.status || ''), note: String(b.note || '').slice(0, 200) }));
      }
      if (m === 'PUT' && action === 'file') {
        const path = checkPath(url.searchParams.get('path'));
        const bytes = new Uint8Array(await req.arrayBuffer());
        if (bytes.byteLength > MAX_FILE) throw new ApiError(413, 'TOO_LARGE');
        await store.setBytes(`files/${week}/${path}`, bytes);
        return json({ ok: true, bytes: bytes.byteLength });
      }
      if (m === 'POST' && action === 'manifest') {
        const man = await body(req, 3_000_000);
        if (man.week !== week) throw new ApiError(400, 'WEEK_MISMATCH');
        await store.set(`manifest/${week}`, man);
        const posts = (man.days || []).reduce((n, d) => n + d.items.length, 0);
        return json(await setWeek(store, week, { status: 'ready', note: '', posts, problems: (man.problems || []).length }));
      }
      throw new ApiError(404, 'NOT_FOUND');
    }

    // ── 메타가 가져가는 영상·사진 (서명 확인, 로그인 없음) ──
    if (parts[1] === 'pub' && parts[2] && m === 'GET') {
      const week = checkWeek(parts[2]);
      const path = checkPath(url.searchParams.get('path'));
      if (!env.WORKER_SECRET || !sameSecret(url.searchParams.get('sig') || '', pubSig(env, week, path))) throw new ApiError(403, 'FORBIDDEN');
      const bytes = await store.getBytes(`files/${week}/${path}`);
      if (!bytes) throw new ApiError(404, 'NO_FILE');
      return new Response(bytes, { headers: { 'Content-Type': TYPES[path.split('.').pop().toLowerCase()] || 'application/octet-stream', 'Cache-Control': 'private, max-age=3600' } });
    }

    // ── 로그인 ──
    if (route === 'studio/me' && m === 'GET') {
      return json({ loggedIn: loggedIn(req, env), configured: Boolean(env.STUDIO_PASSWORD) });
    }
    if (route === 'studio/login' && m === 'POST') {
      if (!env.STUDIO_PASSWORD) throw new ApiError(503, 'NOT_CONFIGURED');
      const t = await tooMany(store);
      if (t.blocked) throw new ApiError(429, 'TOO_MANY');
      const b = await body(req, 2048);
      if (!sameSecret(String(b.password || ''), env.STUDIO_PASSWORD)) { await t.bump(); throw new ApiError(401, 'WRONG_PASSWORD'); }
      return json({ ok: true }, 200, { 'Set-Cookie': sessionCookie(env) });
    }
    if (route === 'studio/logout' && m === 'POST') {
      return json({ ok: true }, 200, { 'Set-Cookie': `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict` });
    }
    if (!loggedIn(req, env)) throw new ApiError(401, 'LOGIN_REQUIRED');

    // ── 로그인한 사장님만 ──
    if (route === 'studio/weeks' && m === 'GET') return json({ weeks: await index(store) });
    // 손님이 온 곳별 결제 수(사장님 2026-11-03). 최근 3달.
    if (route === 'studio/sources' && m === 'GET') {
      const months = [];
      const kst = new Date(Date.now() + 9 * 3600_000);
      for (let i = 0; i < 3; i++) {
        const d = new Date(Date.UTC(kst.getUTCFullYear(), kst.getUTCMonth() - i, 1));
        const month = d.toISOString().slice(0, 7);
        months.push({ month, sources: (await orderStore.get(`stats/sources/${month}`)) || {} });
      }
      return json({ months });
    }
    // 일별 주문과 발송 결과(사장님 2026-11-04 "일별 주문 횟수랑 성공실패"). 최근 14일, 한국 날짜 기준.
    if (route === 'studio/daily' && m === 'GET') return json({ days: await dailyOrders(orderStore) });
    // 결제창 앞뒤: 온 곳마다 결제하기 누른 사람·결제한 사람·안 한 사람(P-30). 최근 14일.
    if (route === 'studio/funnel' && m === 'GET') return json(await sourceFunnel(orderStore));
    if (parts[1] === 'weeks' && parts[2] && m === 'GET') {
      const week = checkWeek(parts[2]);
      const row = (await index(store)).find(w => w.week === week) || null;
      return json({ week: row, manifest: await store.get(`manifest/${week}`), done: (await store.get(`done/${week}`)) || {},
        approved: (await store.get(`approved/${week}`)) || {}, posted: (await store.get(`posted/${week}`)) || {} });
    }
    if (parts[1] === 'file' && parts[2] && m === 'GET') {
      const week = checkWeek(parts[2]);
      const path = checkPath(url.searchParams.get('path'));
      const bytes = await store.getBytes(`files/${week}/${path}`);
      if (!bytes) throw new ApiError(404, 'NO_FILE');
      const ext = path.split('.').pop().toLowerCase();
      const name = path.split('/').pop();
      return new Response(bytes, { headers: {
        'Content-Type': TYPES[ext] || 'application/octet-stream', 'Cache-Control': 'private, max-age=86400',
        ...(url.searchParams.get('dl') ? { 'Content-Disposition': `attachment; filename*=UTF-8''${encodeURIComponent(name)}` } : {}),
      } });
    }
    if (route === 'studio/done' && m === 'POST') {
      const b = await body(req);
      const week = checkWeek(b.week);
      if (typeof b.id !== 'string' || b.id.length > 80) throw new ApiError(400, 'BAD_ID');
      const done = (await store.get(`done/${week}`)) || {};
      if (b.done) done[b.id] = new Date().toISOString(); else delete done[b.id];
      await store.set(`done/${week}`, done);
      return json({ done });
    }
    if (route === 'studio/approve' && m === 'POST') {
      const b = await body(req);
      const week = checkWeek(b.week);
      const ids = Array.isArray(b.ids) ? b.ids : [b.id];
      if (!ids.length || ids.length > 40 || ids.some(id => typeof id !== 'string' || id.length > 80)) throw new ApiError(400, 'BAD_ID');
      const approved = (await store.get(`approved/${week}`)) || {};
      for (const id of ids) { if (b.approved) approved[id] = new Date().toISOString(); else delete approved[id]; }
      await store.set(`approved/${week}`, approved);
      return json({ approved });
    }
    if (route === 'studio/generate' && m === 'POST') {
      const b = await body(req);
      const week = checkWeek(b.start);
      const days = b.days === 1 ? 1 : 7;
      const row = (await index(store)).find(w => w.week === week);
      if (row && ['requested', 'running'].includes(row.status)
        && Date.now() - Date.parse(row.updatedAt) < 60 * 60 * 1000) throw new ApiError(409, 'ALREADY_RUNNING');
      await services.startStudio(week, days);
      // 다시 만들면 예전 승인은 지운다 (새 게시물을 보고 다시 승인)
      await store.delete(`approved/${week}`);
      return json(await setWeek(store, week, { status: 'requested', note: '만들기를 시작했어요' }));
    }
    throw new ApiError(404, 'NOT_FOUND');
  };
}

// 35일 지난 묶음은 파일까지 지운다(저장 공간 아끼기).
export async function eraseOldWeeks(store, now = Date.now()) {
  const list = await index(store);
  const keep = [], gone = [];
  for (const w of list) (now - Date.parse(w.week) > KEEP_DAYS * 86400e3 ? gone : keep).push(w);
  for (const w of gone) {
    for (const k of await store.list(`files/${w.week}/`)) await store.delete(k);
    await store.delete(`manifest/${w.week}`);
    await store.delete(`done/${w.week}`);
    await store.delete(`approved/${w.week}`);
    await store.delete(`posted/${w.week}`);
  }
  if (gone.length) await store.set('weeks', keep);
  return gone.length;
}

// 결제된 리포트 하나의 결과: 보냄 / 보류(못 보냄) / 만드는 중 / 취소. 개인정보 지우기로 'erased'가 돼도 발송 시각·기록으로 가린다.
export function outcomeOf(order) {
  if (order.emailedAt) return 'sent';
  const last = [...(order.history || [])].reverse().find(h => h.status !== 'erased')?.status || order.status;
  if (last === 'held') return 'held';
  if (['queued', 'processing', 'retry'].includes(last)) return 'running';
  if (['refund_pending', 'refunded', 'payment_adjusted'].includes(last)) return 'canceled';
  return 'other';
}

export async function dailyOrders(store, now = new Date(), days = 14) {
  const kstDay = t => new Date(new Date(t).getTime() + 9 * 3600_000).toISOString().slice(0, 10);
  const out = {};
  for (let i = 0; i < days; i++) out[kstDay(now.getTime() - i * 86_400_000)] = { orders: 0, amount: 0, books: 0, sent: 0, held: 0, running: 0, canceled: 0, late: 0 };
  for (const key of await store.list('orders/')) {
    const o = await store.get(key);
    // 묶음으로 함께 산 책(parentId)은 결제 승인 때 만들어지므로 만든 시각이 결제 시각이다
    const paid = o?.paidAt || (o?.parentId && o.createdAt);
    if (!paid || o.testOnly) continue;
    const row = out[kstDay(paid)];
    if (!row) continue;
    if (!o.parentId) { row.orders += 1; row.amount += o.amount || 0; }
    row.books += 1;
    const r = outcomeOf(o);
    if (r in row) row[r] += 1;
    if (r === 'sent' && (o.history || []).some(h => h.status === 'held')) row.late += 1;
  }
  return Object.entries(out).map(([date, v]) => ({ date, ...v }));
}

// 결제창 앞뒤(P-30, 11-05): 최근 며칠 동안 손님이 온 곳마다 '결제하기를 누른 사람'과 그중 결제한 사람·안 한 사람.
// 주문 기록(awaiting_payment → 결제 또는 만료)은 이미 저장되고 있다. 새 개인정보를 모으지 않고, 화면에는 숫자만 보낸다.
// 같은 사람이 같은 날 여러 번 누르면 한 번으로 센다(이메일·상품·한국 날짜가 같으면 한 사람). 한 번이라도 결제했으면 결제로 본다.
export async function sourceFunnel(store, now = new Date(), days = 14) {
  const kstDay = t => new Date(new Date(t).getTime() + 9 * 3600_000).toISOString().slice(0, 10);
  const from = kstDay(now.getTime() - (days - 1) * 86_400_000);
  const people = new Map();
  for (const key of await store.list('orders/')) {
    const o = await store.get(key);
    if (!o || o.parentId || o.testOnly || !o.createdAt) continue;
    const day = kstDay(o.createdAt);
    if (day < from) continue;
    const id = `${o.email || o.id}|${o.productId}|${day}`;
    const p = people.get(id) || { source: o.source || 'direct', paid: false, waiting: false, amount: 0 };
    if (o.paidAt) { p.paid = true; p.amount += o.amount || 0; }
    else if (o.status === 'awaiting_payment') p.waiting = true;
    people.set(id, p);
  }
  const out = {};
  for (const p of people.values()) {
    const r = out[p.source] ||= { started: 0, paid: 0, unpaid: 0, waiting: 0, amount: 0 };
    r.started += 1;
    if (p.paid) { r.paid += 1; r.amount += p.amount; }
    else if (p.waiting) r.waiting += 1;
    else r.unpaid += 1;
  }
  return { from, days, sources: out };
}
