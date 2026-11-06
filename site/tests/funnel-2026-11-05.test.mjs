// 2026-11-05 결제까지 가는 길 고치기(사장님 전권 위임) — 지워지거나 되돌아가지 않았는지 본다.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const html = fs.readFileSync(new URL('../public/index.html', import.meta.url), 'utf8');
const toml = fs.readFileSync(new URL('../../netlify.toml', import.meta.url), 'utf8');
const os = fs.readFileSync(new URL('../public/order-status.html', import.meta.url), 'utf8');

test('방문 통계: GA4·Clarity 가 있고, 이름·생년월일·이메일을 보내는 코드는 없다', () => {
  assert.ok(html.includes('G-X371D3S5X7') && html.includes('z8ppu3yvj7'));
  const calls = html.match(/uTrack\('[a-z_]+',\{[^}]*\}/g) || [];
  assert.ok(calls.length >= 15, '이벤트 ' + calls.length);
  for (const c of calls) assert.ok(!/(\.name|\.birth|email\.value|\.time\b|self\.)/.test(c), '개인정보를 보내면 안 됨: ' + c);
  assert.ok(html.includes('2-1. 방문 통계') && html.includes('Microsoft(미국, 화면 이용 기록)'));
  assert.ok(os.includes("gtag('event','purchase'") && os.includes('unmyeong.ga.purchase.'));
});
test('이름 묻기 장면이 따로 없고, 정보 입력 화면 첫 줄은 상품마다 공감 한 줄이다 (2026-11-05 자청 점검 N-2)', () => {
  assert.ok(!html.includes("scene('name','운명을 열어보기 전에"));
  assert.ok(html.includes('하루에도 몇 번씩 카톡 열어 봤죠. 연락해도 되는 달부터 찾아 드릴게요.'));
  assert.ok(html.includes('먼저 이름과 생일만 알려 주세요.'));
});
test('정보 입력: 빈 칸을 알려 주고, 상대 생일을 모를 때 길을 알려 준다', () => {
  assert.ok(html.includes('function quickMissing(') && html.includes('아직 비어 있어요: '));
  assert.ok(html.includes('data-partner-unknown') && html.includes('function partnerUnknownHelp('));
  assert.ok(html.includes('function savedPartner(') && html.includes('data-reuse-partner'));
});
test('결제 페이지: 이메일이 함께 받아 보기보다 위에 있고, 결제 버튼은 꺼 두지 않는다', () => {
  const co = html.slice(html.indexOf('function checkoutPage('), html.indexOf('function searchPage('));
  assert.ok(co.indexOf('id="email"') > 0 && co.indexOf('id="email"') < co.indexOf('${bundleBlock(p,d)}'));
  assert.ok(co.includes('form="checkout-form"'));
  assert.ok(!/id="pay" type="submit" disabled/.test(co));
  assert.ok(html.includes('맨 위에 리포트 받을 이메일을 넣어 주세요.'));
});
test('함께 받아 보기: 손님에게 맞는 순서, 사장님 순서는 같은 점수일 때 그대로', () => {
  assert.ok(html.includes('function coOrder(') && html.includes('const order=coOrder(p,d,others)'));
  assert.ok(html.includes("CO_TOP=['newyear','romance','reunion','intimate','wealth','career','business','health','lifetime']"));
  assert.ok(html.includes('상대 정보 그대로'));
});
test('미리 보기 A/B 와 손님 답 반영', () => {
  assert.ok(html.includes('function abPreview(') && html.includes("v.ab==='B'"));
  assert.ok(html.includes("RV_FOCUS={newyear:{'일과 직장':'4','돈과 재물':'5','연애와 결혼':'7','건강':'9','한 해 전체':'2'}}"));
  assert.ok(!html.includes('님 사주로 풀어 드리는 이 장의 내용`'));
  assert.ok(html.includes('rv-situation'));
});
test('첫 화면 선물하기 버튼과 지금 답 반영', () => {
  assert.ok(html.includes('class="cover-gift"') && html.includes('data-gift-entry'));
  assert.ok(html.includes('const ans=draft(p.id).answers||{};let pick=(RV_FOCUS[p.id]||{})[ans.focus]'));
  // 잠긴 칸 안내는 달·해를 구분해 말한다(2026-11-06 밤: '황금색 해가 좋은 해인지 조심할 해인지는')
  assert.ok(html.includes("${month||re?'달이':'해가'}"));
});
test('검색·카드·무료 분석: 단계 수 대신 무료 미리보기, 무료 분석에서 바로 정보 확인으로', () => {
  assert.ok(!html.includes('${p.steps}단계'));
  assert.ok(html.includes('card-free') && html.includes('무료로 미리보기 →'));
  assert.ok(html.includes('href="#/f/${p.id}/info" data-taster-product'));
});
test('상품별 공유 페이지와 짧은 주소', () => {
  for (const id of ['newyear','romance','reunion','intimate','wealth','career','business','health','lifetime','taster']) {
    const p = fs.readFileSync(new URL('../public/p/' + id + '/index.html', import.meta.url), 'utf8');
    assert.ok(p.includes('og:image" content="https://unmyeong-saju.com/assets/og/' + id + '.jpg'));
    assert.ok(p.includes("&go=" + id));
    assert.ok(fs.existsSync(new URL('../public/assets/og/' + id + '.jpg', import.meta.url)));
  }
  assert.ok(toml.includes('to = "/p/newyear/?from=dn"') && !/&go=/.test(toml));
});
test('글꼴: 2MB 한 파일 대신 조각 글꼴', () => {
  assert.ok(!html.includes('rel="preload" href="assets/fonts/PretendardVariable.woff2"'));
  assert.ok((html.match(/assets\/fonts\/pretendard-ds\/PretendardVariable\.subset\.\d+\.woff2/g) || []).length >= 90);
});

test('신년운세에만 있던 것을 9개 상품 모두에 (2026-11-05 사장님 "일부만 반영된 거 전부"): 목차 강조, 지도 위 한 줄, 12개월 잠금 줄, 상품별 질문', () => {
  const all = ['romance','reunion','intimate','newyear','wealth','career','business','health','lifetime'];
  const obj = name => { const i = html.indexOf('const ' + name + '={'); assert.ok(i > 0, name); return html.slice(i, html.indexOf('\n', i)); };
  const focus = obj('RV_FOCUS_ALL') + obj('RV_FOCUS'), sit = obj('RV_SIT'), month = obj('RV_MONTH_LOCK'), faq = obj('PRODUCT_FAQ');
  for (const id of all) {
    assert.ok(new RegExp('[{,]' + id + ':').test(focus), 'focus ' + id);
    assert.ok(new RegExp('[{,]' + id + ':').test(faq), 'faq ' + id);
    if (id !== 'reunion') assert.ok(new RegExp('[{,]' + id + ':').test(sit), 'sit ' + id);
    if (!['reunion','newyear'].includes(id)) assert.ok(new RegExp('[{,]' + id + ':').test(month), 'month ' + id);
  }
  // 목차 강조 번호는 그 상품 리포트 목차에 실제로 있는 장이다(제1조항)
  const ed = JSON.parse(html.slice(html.indexOf('const EXTRA_DATA=') + 17, html.indexOf('};', html.indexOf('const EXTRA_DATA=')) + 1));
  const F = Function('return ' + obj('RV_FOCUS_ALL').replace(/^const RV_FOCUS_ALL=/, '').replace(/;$/, ''))();
  for (const [id, qs] of Object.entries(F)) for (const m of Object.values(qs)) for (const no of Object.values(m)) assert.ok(ed.toc[id].some(t => String(t[0]) === no), id + ' ' + no);
});
