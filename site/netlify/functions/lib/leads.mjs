// 무료 맛보기 결과 메일(2026-11-05 사장님 선택 "맛보기 이메일 받기").
// 손님이 결과 화면에서 직접 요청할 때만 한 번 보낸다. 결과 글은 서버가 같은 계산기로 다시 계산해서 쓴다(손님이 보낸 글을 그대로 메일에 넣지 않는다).
// 생년월일·태어난 시간은 메일을 만들 때만 쓰고 저장하지 않는다. 새 리포트 소식(광고성 정보)은 따로 고른 분만 이메일을 남기고, 메일 속 링크로 언제든 그만 받는다.
// 할인·가격은 이 메일에 쓰지 않는다(2026-10-27 사장님: 할인 메일 없음).
import { createHash, randomBytes } from 'node:crypto';
import { chartFromPerson } from '../../../public/assets/free/engine.mjs';
import { reading } from '../../../public/assets/free/taster.mjs';
import { PRODUCTS } from './intake.mjs';

export class LeadError extends Error { constructor(status, code) { super(code); this.status = status; this.code = code; } }

const EMAIL_RE = /^[^\s@<>()",;:]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,24}$/;
const NAME_RE = /^[가-힣A-Za-z ]{1,12}$/;
const DATE_RE = /^(19[0-9]{2}|20[0-4][0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$/;
const PERSON_KEYS = ['name', 'sex', 'calendar', 'birth', 'leapStatus', 'timeAccuracy', 'time', 'timeRange'];
const PER_EMAIL_DAY = 3, PER_IP_HOUR = 10;
export const LEAD_KEEP_DAYS = 730;   // 소식 받기 동의 기록은 그만 받기 전까지, 길어도 2년

export const emailHash = email => createHash('sha256').update('lead:' + String(email).trim().toLowerCase()).digest('hex').slice(0, 40);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function cleanPerson(raw = {}) {
  const p = {};
  for (const k of PERSON_KEYS) if (typeof raw[k] === 'string' && raw[k].length <= 40) p[k] = raw[k].trim();
  const hm = v => (typeof v === 'string' && /^([01][0-9]|2[0-3]):[0-5][0-9]$/.test(v) ? v : '');
  if (raw.timeRange && hm(raw.timeRange.start) && hm(raw.timeRange.end)) p.timeRange = { start: raw.timeRange.start, end: raw.timeRange.end };
  // 예전에 태어난 곳을 넣어 기기에 저장된 분은 그 위치로 계산한다(결제 리포트와 같은 명식, 제1조항).
  const bp = raw.birthPlace || {};
  if (['known', 'region-only'].includes(bp.status)) p.birthPlace = { status: bp.status, regionChoice: String(bp.regionChoice || '').slice(0, 12), regionCode: String(bp.regionCode || '').slice(0, 12) };
  p.name = (p.name || '').replace(/\s+/g, ' ');
  if (!NAME_RE.test(p.name)) throw new LeadError(400, 'BAD_NAME');
  if (!['male', 'female'].includes(p.sex)) throw new LeadError(400, 'BAD_PERSON');
  return p;
}

async function bump(store, key, limit) {
  const n = ((await store.get(key))?.n || 0) + 1;
  if (n > limit) throw new LeadError(429, 'TOO_MANY');
  await store.set(key, { n });
}

export function tasterMail({ name, r, site, unsubUrl }) {
  const prod = id => PRODUCTS.find(p => p.id === id);
  const link = id => `${site}/p/${id}/?from=tm`;
  const block = (a, i, kind) => {
    const p = prod(a.product), short = (p?.name || '').replace(/^금월선녀의\s*/, '');
    return { title: `${kind} ${i + 1}위 · ${a.title}`, text: a.text, hook: a.hook, more: short ? `나의 ${short} 무료로 미리보기` : '', url: link(a.product) };
  };
  const rows = [...r.good.map((a, i) => block(a, i, '좋은 운')), ...r.bad.map((a, i) => block(a, i, '조심할 운'))];
  const subject = `[운명서재] ${name}님의 무료 사주 결과예요`;
  const foot = [
    '이 메일은 운명서재 무료 사주 결과 화면에서 직접 요청하신 결과예요. 생년월일과 태어난 시간은 이 메일을 만들면서만 쓰고 저장하지 않았어요.',
    '금월선녀는 운명서재의 AI 안내자예요. 사주는 타고난 흐름을 읽는 전통 해석이고, 결과를 약속하지 않아요.',
    unsubUrl ? `새 리포트 소식 받기에 동의하셨어요. 그만 받으려면: ${unsubUrl}` : '이 메일 말고 다른 메일은 보내지 않아요.',
    `운명서재 ${site} · 김승용 · 사업자등록번호 101-69-00805 · benedicto528@naver.com`,
  ];
  const text = [`${name}님, 금월선녀예요.`, '요청하신 무료 사주 결과를 보내 드려요. 생각날 때 다시 열어 보세요.', '',
    ...rows.flatMap(x => [`■ ${x.title}`, x.text, x.hook, `${x.more}: ${x.url}`, '']), `내 무료 사주 다시 보기: ${site}/p/taster/?from=tm`, '', ...foot].join('\n');
  const html = `<div style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:560px;margin:0 auto;color:#1d1d1f;font-size:17px;line-height:1.7">
<p style="margin:0 0 4px;font-size:20px;font-weight:700">${esc(name)}님, 금월선녀예요.</p>
<p style="margin:0 0 20px">요청하신 무료 사주 결과를 보내 드려요. 생각날 때 다시 열어 보세요.</p>
${rows.map(x => `<div style="border:1px solid #e3dccb;border-radius:12px;padding:16px 18px;margin:0 0 14px">
<p style="margin:0 0 6px;font-weight:700;font-size:18px">${esc(x.title)}</p><p style="margin:0 0 8px">${esc(x.text)}</p><p style="margin:0 0 10px;font-weight:700">${esc(x.hook)}</p>
${x.more ? `<a href="${esc(x.url)}" style="color:#9a6a00;font-weight:700">${esc(x.more)} →</a>` : ''}</div>`).join('')}
<p style="margin:18px 0"><a href="${esc(site)}/p/taster/?from=tm" style="display:inline-block;background:#e9c35a;color:#1d1d1f;font-weight:700;padding:12px 20px;border-radius:10px;text-decoration:none">내 무료 사주 다시 보기</a></p>
${foot.map(l => `<p style="margin:0 0 6px;font-size:15px;color:#555">${esc(l)}</p>`).join('')}</div>`;
  return { subject, text, html };
}

export async function sendTasterMail({ store, send, assets, env, body, ip = '', now = new Date() }) {
  const email = String(body.email || '').trim();
  if (!EMAIL_RE.test(email) || email.length > 120) throw new LeadError(400, 'BAD_EMAIL');
  if (body.agree !== true) throw new LeadError(400, 'CONSENT_REQUIRED');
  const person = cleanPerson(body.person);
  const solar = String(body.solar || person.birth || '');
  if (!DATE_RE.test(solar)) throw new LeadError(400, 'BAD_PERSON');
  const h = emailHash(email), day = now.toISOString().slice(0, 10), hour = now.toISOString().slice(0, 13);
  await bump(store, `lead-rate/e/${h}/${day}`, PER_EMAIL_DAY);
  if (ip) await bump(store, `lead-rate/ip/${createHash('sha256').update(ip).digest('hex').slice(0, 24)}/${hour}`, PER_IP_HOUR);
  const { data, texts } = await assets();
  let r;
  try { r = reading(chartFromPerson(data, person, solar), person, texts); } catch { throw new LeadError(400, 'BAD_PERSON'); }
  const site = env.SITE_URL || 'https://unmyeong-saju.com';
  let unsubUrl = '';
  if (body.news === true) {
    const old = await store.get(`leads/${h}`);
    const token = old?.token || randomBytes(16).toString('hex');
    await store.set(`leads/${h}`, {
      email, name: person.name, token, consentAt: old?.consentAt || now.toISOString(), updatedAt: now.toISOString(),
      from: String(body.from || '').slice(0, 20), picks: [...r.good, ...r.bad].map(a => a.product),
      consentText: '새 리포트 소식 받기(광고성 정보 수신, 선택)',
    });
    unsubUrl = `${site}/api/leads/stop?id=${h}&t=${token}`;
  }
  await send({ to: [email], ...tasterMail({ name: person.name, r, site, unsubUrl }) }, `taster-${h}-${hour}`);
  return { ok: true, news: Boolean(unsubUrl) };
}

export async function stopLead(store, id, token) {
  const rec = /^[0-9a-f]{40}$/.test(id || '') ? await store.get(`leads/${id}`) : null;
  if (rec && rec.token === token) await store.delete(`leads/${id}`);
  // 이미 지웠거나 잘못된 링크여도 같은 안내를 보여 준다(누가 동의했는지 알 수 없게).
  return new Response(`<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>소식 그만 받기 · 운명서재</title>
<body style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;background:#0d0d10;color:#f3efe6;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;padding:24px;font-size:18px;line-height:1.7;text-align:center">
<div><p style="font-size:22px;font-weight:700;margin:0 0 8px">소식 받기를 그만두었어요</p><p style="margin:0 0 20px">이 이메일은 지웠고, 앞으로 운명서재 소식 메일을 보내지 않아요.</p><a href="/" style="color:#e9c35a;font-weight:700">운명서재로 가기</a></div></body></html>`,
  { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' } });
}

// 한 시간마다(cleanup): 하루 지난 보내기 횟수 기록, 2년 지난 소식 받기 기록을 지운다.
export async function eraseOldLeads(store, now = new Date()) {
  let n = 0;
  const today = now.toISOString().slice(0, 10), thisHour = now.toISOString().slice(0, 13);
  for (const k of await store.list('lead-rate/')) {
    const stamp = k.split('/').pop();
    if ((stamp.length === 10 && stamp < today) || (stamp.length === 13 && stamp < thisHour)) { await store.delete(k); n++; }
  }
  const cut = new Date(now.getTime() - LEAD_KEEP_DAYS * 864e5).toISOString();
  for (const k of await store.list('leads/')) {
    const rec = await store.get(k);
    if (!rec || (rec.updatedAt || rec.consentAt || '') < cut) { await store.delete(k); n++; }
  }
  return n;
}
