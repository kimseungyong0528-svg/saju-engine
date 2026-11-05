// 무료 사주 맛보기 화면 (#/taster). build_site.py 가 사이트 코드 안에 그대로 넣는다.
// 계산은 assets/free/ 의 계산기가 브라우저에서 한다(서버·AI 호출 없음).
let tasterState={person:{},result:null};
let tasterLib=null;
async function tasterLoad(){if(!tasterLib){const json=u=>fetch(u).then(r=>{if(!r.ok)throw Error(u);return r.json()});const [eng,tst,data,texts]=await Promise.all([import('./assets/free/engine.mjs'),import('./assets/free/taster.mjs'),json('assets/free/saju-data.json?v=20261105j'),json('assets/free/texts.json?v=20261105j')]);tasterLib={eng,tst,data,texts}}return tasterLib}
function tasterItem(a,kind,i){const p=pById(a.product);return `<article class="taster-item ${kind}"><div class="taster-rank"><span>${kind==='good'?'좋은 운':'조심할 운'} ${i+1}위</span><h3>${esc(a.title)}</h3></div><p>${esc(a.text)}</p><p class="taster-hook">${esc(a.hook)}</p><a class="taster-more" href="#/f/${p.id}/info" data-taster-product="${p.id}">나의 ${esc(p.short)} 무료로 미리보기 →</a></article>`}
function tasterChart(r){const c=r.chart;
 return `<div class="taster-chart">${c.columns.map(x=>`<div class="tc-col${x.me?' me':''}"><small>${x.label}</small><b>${x.hanja?esc(x.hanja[0]):'?'}</b><b>${x.hanja?esc(x.hanja[1]):'?'}</b><span>${x.ko?esc(x.ko):'모름'}</span>${x.me?'<em>나</em>':''}</div>`).join('')}</div><p class="taster-note">${esc(r.name)} 님이 태어난 해·달·날·시를 여덟 글자로 바꾼 것이 사주팔자입니다. ${esc(r.name)} 님은 ${esc(c.zodiac)}띠입니다.${c.columns[0].hanja?'':' 태어난 시간을 몰라서 시 자리는 비워 두었습니다.'}</p>
 <section class="taster-box"><h3>${esc(r.name)} 님 사주 한눈에 보기</h3>${c.items.map(it=>`<div class="tb-item"><strong>${esc(it.head)}</strong><p>${esc(it.text)}</p></div>`).join('')}<div class="tb-bars">${c.elements.map(e=>`<div class="tb-bar ${e.status}"><span>${esc(e.word)}</span><i><b style="width:${Math.min(100,e.pct*2)}%"></b></i><em>${e.pct}%</em></div>`).join('')}</div></section>`}
function tasterPage(){
 document.title='금월선녀 무료 사주 분석 · '+BRAND.name;
 const r=tasterState.result;
 // 입력 화면은 상품 입력 화면과 같은 한 화면 양식(사장님 2026-11-03): 배경은 사람 없는 밤 궁궐 연못, 글씨는 금월선녀 멘트와 같은 Gowun Batang, '맛보기' 제목은 뺀다.
 if(!r){
  if(!tasterState.person.name&&!tasterState.person.birth){const me=savedMe();if(me)tasterState.person={...me}}
  const lp=pById('lifetime');
  app.innerHTML=`<div class="shell flow quick-info taster-quick" style="--accent:${lp.color}"><div class="qi-bg" aria-hidden="true"><img src="assets/geumwol/palace-garden.webp" alt="" decoding="async"></div>
<header class="qi-top"><a class="qi-back" href="#/" aria-label="홈으로">${icon('back')}</a></header>
<main id="main" class="qi-main"><div class="taster-intro"><h1>내 사주에서<br>좋은 운 3개, 조심할 운 3개</h1><p>생년월일과 태어난 시간을 넣으면<br>연애·결혼·재회·돈·직장·사업·건강·2027년<br>여덟 가지 운 중 좋은 운 3개, 조심할 운 3개를<br>바로 보여드려요. 무료입니다.</p></div><form id="taster-form" novalidate autocomplete="off">${quickFields('taster',tasterState.person)}</form><p class="qi-err" data-qi-err hidden aria-live="polite"></p></main>
<div class="qi-bottom"><button class="qi-next" id="taster-submit" type="button" disabled>무료로 내 운 보기</button></div></div>`;
  const f=document.querySelector('#taster-form'),btn=document.querySelector('#taster-submit'),prev=tasterState.person;
  bindQuick(f,prev,(v,valid)=>{tasterState.person=v;btn.disabled=!valid});
  f.addEventListener('focusin',e=>{const el=e.target;if(!el.matches('input:not([type=radio]):not([type=checkbox])'))return;setTimeout(()=>el.scrollIntoView({block:'center',behavior:'smooth'}),320)});
  f.onsubmit=e=>{e.preventDefault();btn.click()};
  btn.onclick=async()=>{const v=readQuick(f,prev);if(!personValid(v))return;
   btn.disabled=true;btn.textContent='사주를 계산하고 있어요';
   try{const {eng,tst,data,texts}=await tasterLoad();const date=validateBirthDate(v);const fp=eng.chartFromPerson(data,v,v.calendar==='lunar'?date.solarDate:v.birth);rememberMe(v);tasterState={person:v,result:tst.reading(fp,v,texts)};try{const rr=tasterState.result;localStorage.setItem('unmyeong.tasterPicks',JSON.stringify({good:rr.good.map(a=>a.product),bad:rr.bad.map(a=>a.product),at:Date.now()}))}catch{}window.uTrack&&uTrack('taster_result',{});tasterPage();window.scrollTo({top:0,behavior:'instant'})}
   catch(err){console.error(err);btn.disabled=false;btn.textContent='무료로 내 운 보기';toast('계산하지 못했어요. 잠시 뒤 다시 눌러 주세요.')}};
  return}
 layout('금월선녀 무료 사주 분석',`<div class="page-pad taster-result">${revealSpeech(pById('lifetime'),`${r.name} 님의 좋은 운과 조심할 운을\n자세하게 알려드릴게요\n지금부터 집중해주세요!`)}${tasterChart(r)}<h2 class="taster-head good">좋은 운 TOP 3</h2>${r.good.map((a,i)=>tasterItem(a,'good',i)).join('')}<h2 class="taster-head bad">조심할 운 TOP 3</h2>${r.bad.map((a,i)=>tasterItem(a,'bad',i)).join('')}${(()=>{const PRI=['reunion','romance','newyear','wealth','intimate','career','business','health'];const c=[...r.bad.map(a=>[a,'bad']),...r.good.map(a=>[a,'good'])].filter(([a])=>pById(a.product)&&PRI.includes(a.product)).sort((x,y)=>PRI.indexOf(x[0].product)-PRI.indexOf(y[0].product)||(x[1]==='bad'?-1:1));if(!c.length)return '';const [a,k]=c[0],pp=pById(a.product);return `<a class="taster-pick" href="#/f/${pp.id}/info" data-taster-product="${pp.id}"><span class="eyebrow">금월선녀가 고른 다음 한 권</span><strong>${esc(r.name)} 님은<br>'${esc(a.title)}'부터 보세요</strong><p>${k==='bad'?`위 결과에서 '${esc(a.title)}' 운은 미리 대비하면 달라지는 운이에요. ${esc(pp.short)}에서 언제 조심하고 언제 움직이면 좋은지, 해와 달까지 짚어 드려요.`:`위 결과에서 '${esc(a.title)}' 운은 크게 받을 수 있는 운이에요. ${esc(pp.short)}에서 그 운이 언제 들어오는지, 해와 달까지 짚어 드려요.`}</p><ul><li>내 ${esc(pp.short)} 점수와 지도는 무료로 먼저</li><li>방금 넣은 생일 그대로, 다시 입력 없이</li></ul><span class="taster-pick-cta">무료로 내 ${esc(pp.short)} 먼저 보기 →</span></a>`})()}<a class="taster-lifetime" href="#/f/lifetime/info" data-taster-product="lifetime"><span class="eyebrow">내 사주 전체</span><strong>내 사주 전체를<br>한 권으로 보고 싶다면</strong><span>${esc(pById('lifetime').name)} 자세히 알아보기 →</span></a><div class="taster-all"><p>다른 운도 자세히 보기</p>${['newyear','romance','reunion','intimate','wealth','career','business','health'].map(id=>`<a href="#/f/${id}/info" data-taster-product="${id}">${esc(pById(id).short)}</a>`).join('')}</div><button type="button" class="taster-redo" id="taster-redo">입력한 정보 고쳐서 다시 보기</button></div>`);
 // 잘못 넣었을 수 있으니, 넣었던 정보를 그대로 채운 입력 화면으로 돌아간다.
 document.querySelector('#taster-redo').onclick=()=>{tasterState.result=null;tasterPage();window.scrollTo({top:0,behavior:'instant'})};
 // '자세히 알아보기'로 간 상품에는 방금 넣은 출생 정보를 미리 채워 둔다.
 document.querySelectorAll('[data-taster-product]').forEach(a=>a.addEventListener('click',()=>{window.uTrack&&uTrack('taster_click',{product:a.dataset.tasterProduct});const d=draft(a.dataset.tasterProduct);if(!d.self||!personValid(d.self)){d.self={...tasterState.person};save()}}));
}
