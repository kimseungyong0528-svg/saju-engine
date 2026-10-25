// 무료 사주 맛보기 화면 (#/taster). build_site.py 가 사이트 코드 안에 그대로 넣는다.
// 계산은 assets/free/ 의 계산기가 브라우저에서 한다(서버·AI 호출 없음).
let tasterState={person:{},result:null};
let tasterLib=null;
async function tasterLoad(){if(!tasterLib){const [eng,tst,data]=await Promise.all([import('./assets/free/engine.mjs'),import('./assets/free/taster.mjs'),fetch('assets/free/saju-data.json').then(r=>r.json())]);tasterLib={eng,tst,data}}return tasterLib}
function tasterItem(a,kind,i){const p=pById(a.product);return `<article class="taster-item ${kind}"><div class="taster-rank"><span>${kind==='good'?'좋은 운':'조심할 운'} ${i+1}위</span><h3>${esc(a.title)}</h3></div><p>${esc(a.text)}</p><a class="taster-more" href="#/f/${p.id}/intro" data-taster-product="${p.id}">나의 ${esc(p.short)} 자세히 알아보기 →</a></article>`}
function tasterPage(){
 document.title='무료 사주 맛보기 · '+BRAND.name;
 const r=tasterState.result;
 if(!r){layout('무료 사주 맛보기',`<div class="flow-content birth-info-page taster-form" data-birth-tone="lifetime"><span class="eyebrow">FREE SAJU</span><h1>내 사주에서<br>좋은 운 3개, 조심할 운 3개</h1><p class="muted">생년월일과 태어난 시간을 넣으면, 연애·결혼·돈·직장·사업·건강·2027년 가운데 가장 좋은 운 3개와 가장 조심할 운 3개를 바로 보여드려요. 무료입니다.</p><form id="taster-form" novalidate>${personFields('taster',tasterState.person)}<button class="primary taster-submit" id="taster-submit" type="submit" disabled>무료로 내 운 보기</button></form><p class="local-note">입력한 정보는 이 화면에서만 계산하고 서버에 보내지 않아요.</p></div>`);
  const f=document.querySelector('#taster-form'),btn=document.querySelector('#taster-submit');
  bindPerson(f,(v,valid)=>{tasterState.person=v;btn.disabled=!valid});
  f.onsubmit=async e=>{e.preventDefault();const v=readPerson(f);if(!personValid(v)||!f.checkValidity()){f.reportValidity();return}
   btn.disabled=true;btn.textContent='사주를 계산하고 있어요';
   try{const {eng,tst,data}=await tasterLoad();const date=validateBirthDate(v);const fp=eng.chartFromPerson(data,v,v.calendar==='lunar'?date.solarDate:v.birth);tasterState={person:v,result:tst.reading(fp,v)};tasterPage();window.scrollTo({top:0,behavior:'instant'})}
   catch(err){console.error(err);btn.disabled=false;btn.textContent='무료로 내 운 보기';toast('계산하지 못했어요. 잠시 뒤 다시 눌러 주세요.')}};
  return}
 const p=r.pillars;
 layout('무료 사주 맛보기',`<div class="page-pad taster-result"><span class="eyebrow">FREE SAJU</span><h1>${esc(r.name)} 님의<br>좋은 운과 조심할 운</h1><div class="taster-pillars">${p.map(x=>`<div><small>${x.label}</small><b>${x.hanja?esc(x.hanja[0]):'?'}</b><b>${x.hanja?esc(x.hanja[1]):'?'}</b></div>`).join('')}</div>${p[0].hanja?'':'<p class="taster-note">태어난 시간을 몰라서 시주를 빼고 봤어요.</p>'}<p class="taster-intro">${esc(r.intro)}</p><h2 class="taster-head good">좋은 운 TOP 3</h2>${r.good.map((a,i)=>tasterItem(a,'good',i)).join('')}<h2 class="taster-head bad">조심할 운 TOP 3</h2>${r.bad.map((a,i)=>tasterItem(a,'bad',i)).join('')}<a class="taster-lifetime" href="#/f/lifetime/intro" data-taster-product="lifetime"><span class="eyebrow">내 사주 전체</span><strong>내 사주 전체를 한 권으로 보고 싶다면</strong><span>${esc(pById('lifetime').name)} 자세히 알아보기 →</span></a><button class="text-button taster-again" id="taster-again">가족·친구 사주도 무료로 보기</button></div>`);
 // '자세히 알아보기'로 간 상품에는 방금 넣은 출생 정보를 미리 채워 둔다.
 document.querySelectorAll('[data-taster-product]').forEach(a=>a.addEventListener('click',()=>{const d=draft(a.dataset.tasterProduct);if(!d.self||!personValid(d.self)){d.self={...tasterState.person};save()}}));
 document.querySelector('#taster-again').onclick=()=>{tasterState={person:{},result:null};tasterPage();window.scrollTo({top:0,behavior:'instant'})};
}
