const fs = require('fs');
function rec(s, name) {
  const out = fs.createWriteStream(`${name}.log`);
  const w = (...a) => { out.write(a.join(' ') + '\n'); };
  const look = async (label, { full = true } = {}) => {
    await s.page.waitForTimeout(400);
    const f = await s.shot(label, full);
    w('\n##### ', label, s.page.url(), '->', f);
    w(await s.text());
    const sm = await s.small(); if (sm.length) w('SMALL<14:', JSON.stringify(sm));
    const hs = await s.hscroll(); if (hs > 0) w('HSCROLL', hs);
    return f;
  };
  return { w, look, out };
}
async function next(s) {
  const b = s.page.locator('button.primary:not([disabled]):visible, button[type=submit]:not([disabled]):visible').filter({ hasNotText: /소리|멈추기|메뉴/ }).last();
  const t = (await b.innerText()).trim(); await b.click(); await s.page.waitForTimeout(1500); return t;
}
async function fillPerson(page, p, root) {
  root = root || page;
  const L = sel => root.locator(sel).first();
  const sel = async (n, v) => { await L(`[name=${n}]`).selectOption(v); await page.waitForTimeout(150); };
  const radio = async (n, v) => { await L(`input[name=${n}][value=${v}]`).evaluate(e => e.click()); await page.waitForTimeout(150); };
  if (p.name !== undefined) await L('[name=name]').fill(p.name);
  if (p.sex) { await page.waitForTimeout(300); await radio('sex', p.sex); }
  await radio('calendar', p.cal); await page.waitForTimeout(200);
  if (p.cal === 'solar') { await sel('solarYear', String(p.y)); await sel('solarMonth', String(p.m)); await sel('solarDay', String(p.d)); }
  if (p.cal === 'lunar') { await sel('lunarYear', String(p.y)); await sel('lunarMonth', String(p.m)); await page.waitForTimeout(200);
    if (await root.locator('[name=leapStatus]:enabled').count()) await sel('leapStatus', p.leap ? 'intercalary' : 'regular');
    await sel('lunarDay', String(p.d)); }
  await sel('region', { label: p.region }); await page.waitForTimeout(300);
  if (p.district) await sel('district', { label: p.district });
  await radio('timeAccuracy', p.acc); await page.waitForTimeout(200);
  if (p.acc === 'exact') { await radio('timePeriod', p.ap); await sel('timeHour', p.h); await sel('timeMinute', p.mi); }
  if (p.acc === 'approximate') { await radio('timeStartPeriod', p.s[0]); await sel('timeStartHour', p.s[1]); await sel('timeStartMinute', p.s[2]);
    await radio('timeEndPeriod', p.e[0]); await sel('timeEndHour', p.e[1]); await sel('timeEndMinute', p.e[2]); }
  await page.waitForTimeout(400);
}
module.exports = { rec, next, fillPerson };
