const { chromium } = require('playwright'); const { next, fillPerson } = require('./flow');
const OUT = process.env.OUT || 'shots';
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
  const page = await ctx.newPage(); const s = { page };
  page.on('console', m => { if (m.type() === 'error') console.log('console', m.text()); });
  const shot = async (n, full = true) => { await page.waitForTimeout(800); await page.screenshot({ path: `${OUT}/${n}.png`, fullPage: full }); console.log('shot', n, page.url()); };
  await page.goto('https://unmyeong-saju.com/#/f/wealth/intro', { waitUntil: 'networkidle' }); await page.waitForTimeout(1500);
  await page.evaluate(() => document.querySelectorAll('.modal,.entry-modal').forEach(e => e.remove()));
  for (let i = 0; i < 8 && !(await page.locator('[name=name]').count()); i++) await next(s);
  await fillPerson(page, { name: '최민지', sex: 'female', cal: 'solar', y: 1995, m: 3, d: 12, region: '서울', district: '종로구', acc: 'exact', ap: 'pm', h: '02', mi: '20' });
  for (let i = 0; i < 14 && !page.url().includes('checkout'); i++) { await next(s); const r = page.locator('main input[type=radio]:visible'); if (await r.count()) await r.first().check({ force: true }); }
  await shot('1-checkout');
  await page.fill('#email', 'test@example.com'); await page.check('#all-consent'); await page.waitForTimeout(500);
  await page.click('#pay'); await page.waitForTimeout(5000);
  await shot('2-after-check');
  const start = page.locator('[data-start-payment]');
  console.log('start buttons', await start.count());
  if (await start.count()) {
    const pop = ctx.waitForEvent('page', { timeout: 15000 }).catch(() => null);
    await start.first().click(); await page.waitForTimeout(8000);
    await shot('3-toss', false);
    const w = await pop; if (w) { await w.waitForTimeout(5000); await w.screenshot({ path: `${OUT}/4-toss-popup.png` }); console.log('popup', w.url()); }
    for (const f of page.frames()) console.log('frame', f.url().slice(0, 120));
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
