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

export function makeStudio({ store, services, env }) {
  return async function handle(req, parts) {
    const m = req.method;
    const url = new URL(req.url);
    const route = parts.join('/');

    // ── 관리 작업(깃허브)에서 오는 요청: WORKER_SECRET 확인 ──
    if (parts[0] === 'internal') {
      if (!sameSecret(req.headers.get('x-worker-secret') || '', env.WORKER_SECRET || '')) throw new ApiError(403, 'FORBIDDEN');
      if (m === 'GET' && parts[2] === 'used') {
        const keys = [];
        for (const w of (await index(store)).slice(0, 8)) {
          const man = await store.get(`manifest/${w.week}`);
          if (man?.used) keys.push(...man.used);
        }
        return json({ keys: [...new Set(keys)] });
      }
      const week = checkWeek(parts[2]);
      const action = parts[3];
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
    if (parts[1] === 'weeks' && parts[2] && m === 'GET') {
      const week = checkWeek(parts[2]);
      const row = (await index(store)).find(w => w.week === week) || null;
      return json({ week: row, manifest: await store.get(`manifest/${week}`), done: (await store.get(`done/${week}`)) || {} });
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
    if (route === 'studio/generate' && m === 'POST') {
      const b = await body(req);
      const week = checkWeek(b.start);
      const row = (await index(store)).find(w => w.week === week);
      if (row && ['requested', 'running'].includes(row.status)
        && Date.now() - Date.parse(row.updatedAt) < 60 * 60 * 1000) throw new ApiError(409, 'ALREADY_RUNNING');
      await services.startStudio(week);
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
  }
  if (gone.length) await store.set('weeks', keep);
  return gone.length;
}
