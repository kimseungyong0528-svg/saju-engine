// 무료 사주 맛보기 화면 (#/taster). build_site.py 가 사이트 코드 안에 그대로 넣는다.
// 계산은 assets/free/ 의 계산기가 브라우저에서 한다(서버·AI 호출 없음).
let tasterState={person:{},result:null};
let tasterLib=null;
async function tasterLoad(){if(!tasterLib){const json=u=>fetch(u).then(r=>{if(!r.ok)throw Error(u);return r.json()});const [eng,tst,data,texts]=await Promise.all([import('./assets/free/engine.mjs'),import('./assets/free/taster.mjs'),json('assets/free/saju-data.json'),json('assets/free/texts.json')]);tasterLib={eng,tst,data,texts}}return tasterLib}
function tasterItem(a,kind,i){const p=pById(a.product);return `<article class="taster-item ${kind}"><div class="taster-rank"><span>${kind==='good'?'좋은 운':'조심할 운'} ${i+1}위</span><h3>${esc(a.title)}</h3></div><p>${esc(a.text)}</p><p class="taster-hook">${esc(a.hook)}</p><a class="taster-more" href="#/f/${p.id}/intro" data-taster-product="${p.id}">나의 ${esc(p.short)} 자세히 알아보기 →</a></article>`}
function tasterChart(r){const c=r.chart;
 return `<div class="taster-chart">${c.columns.map(x=>`<div class="tc-col${x.me?' me':''}"><small>${x.label}</small><b>${x.hanja?esc(x.hanja[0]):'?'}</b><b>${x.hanja?esc(x.hanja[1]):'?'}</b><span>${x.ko?esc(x.ko):'모름'}</span>${x.me?'<em>나</em>':''}</div>`).join('')}</div><p class="taster-note">${esc(r.name)} 님이 태어난 해·달·날·시를 여덟 글자로 바꾼 것이 사주팔자입니다. ${esc(r.name)} 님은 ${esc(c.zodiac)}띠입니다.${c.columns[0].hanja?'':' 태어난 시간을 몰라서 시 자리는 비워 두었습니다.'}</p>
 <section class="taster-box"><h3>${esc(r.name)} 님 사주 한눈에 보기</h3>${c.items.map(it=>`<div class="tb-item"><strong>${esc(it.head)}</strong><p>${esc(it.text)}</p></div>`).join('')}<div class="tb-bars">${c.elements.map(e=>`<div class="tb-bar ${e.status}"><span>${esc(e.word)}</span><i><b style="width:${Math.min(100,e.pct*2)}%"></b></i><em>${e.pct}%</em></div>`).join('')}</div></section>`}
function tasterPage(){
 document.title='무료 사주 맛보기 · '+BRAND.name;
 const r=tasterState.result;
 if(!r){layout('무료 사주 맛보기',`<div class="flow-content birth-info-page taster-form" data-birth-tone="lifetime"><span class="eyebrow">FREE SAJU</span><h1>내 사주에서<br>좋은 운 3개, 조심할 운 3개</h1><p class="muted">생년월일과 태어난 시간을 넣으면, 연애·결혼·돈·직장·사업·건강·2027년 가운데 가장 좋은 운 3개와 가장 조심할 운 3개를 바로 보여드려요. 무료입니다.</p><form id="taster-form" novalidate>${reuseBox(tasterState.person,'reuse-me')}${personFields('taster',tasterState.person)}<button class="primary taster-submit" id="taster-submit" type="submit" disabled>무료로 내 운 보기</button></form><p class="local-note">입력한 정보는 이 화면에서만 계산하고 서버에 보내지 않아요.</p></div>`);
  const f=document.querySelector('#taster-form'),btn=document.querySelector('#taster-submit');
  bindPerson(f,(v,valid)=>{tasterState.person=v;btn.disabled=!valid});
  bindReuse('reuse-me',v=>{tasterState.person=v});
  f.onsubmit=async e=>{e.preventDefault();const v=readPerson(f);if(!personValid(v)||!f.checkValidity()){f.reportValidity();return}
   btn.disabled=true;btn.textContent='사주를 계산하고 있어요';
   try{const {eng,tst,data,texts}=await tasterLoad();const date=validateBirthDate(v);const fp=eng.chartFromPerson(data,v,v.calendar==='lunar'?date.solarDate:v.birth);rememberMe(v);tasterState={person:v,result:tst.reading(fp,v,texts)};tasterPage();window.scrollTo({top:0,behavior:'instant'})}
   catch(err){console.error(err);btn.disabled=false;btn.textContent='무료로 내 운 보기';toast('계산하지 못했어요. 잠시 뒤 다시 눌러 주세요.')}};
  return}
 layout('무료 사주 맛보기',`<div class="page-pad taster-result"><span class="eyebrow">FREE SAJU</span><h1>${esc(r.name)} 님의<br>좋은 운과 조심할 운</h1>${tasterChart(r)}<h2 class="taster-head good">좋은 운 TOP 3</h2>${r.good.map((a,i)=>tasterItem(a,'good',i)).join('')}<h2 class="taster-head bad">조심할 운 TOP 3</h2>${r.bad.map((a,i)=>tasterItem(a,'bad',i)).join('')}<a class="taster-lifetime" href="#/f/lifetime/intro" data-taster-product="lifetime"><span class="eyebrow">내 사주 전체</span><strong>내 사주 전체를<br>한 권으로 보고 싶다면</strong><span>${esc(pById('lifetime').name)} 자세히 알아보기 →</span></a><button type="button" class="taster-redo" id="taster-redo">입력한 정보 고쳐서 다시 보기</button></div>`);
 // 잘못 넣었을 수 있으니, 넣었던 정보를 그대로 채운 입력 화면으로 돌아간다.
 document.querySelector('#taster-redo').onclick=()=>{tasterState.result=null;tasterPage();window.scrollTo({top:0,behavior:'instant'})};
 // '자세히 알아보기'로 간 상품에는 방금 넣은 출생 정보를 미리 채워 둔다.
 document.querySelectorAll('[data-taster-product]').forEach(a=>a.addEventListener('click',()=>{const d=draft(a.dataset.tasterProduct);if(!d.self||!personValid(d.self)){d.self={...tasterState.person};save()}}));
}
