// 무료 사주 맛보기 화면 (#/taster). build_site.py 가 사이트 코드 안에 그대로 넣는다.
// 계산은 assets/free/ 의 계산기가 브라우저에서 한다(서버·AI 호출 없음).
let tasterState={person:{},result:null};
let tasterLib=null;
async function tasterLoad(){if(!tasterLib){const json=u=>fetch(u).then(r=>{if(!r.ok)throw Error(u);return r.json()});const [eng,tst,data,texts]=await Promise.all([import('./assets/free/engine.mjs'),import('./assets/free/taster.mjs'),json('assets/free/saju-data.json?v=20261105l'),json('assets/free/texts.json?v=20261105l')]);tasterLib={eng,tst,data,texts}}return tasterLib}
function tasterItem(a,kind,i){const p=pById(a.product);return `<article class="taster-item ${kind}"><div class="taster-rank"><span>${kind==='good'?'좋은 운':'조심할 운'} ${i+1}위</span><h3>${esc(a.title)}</h3></div><p>${esc(a.text)}</p><p class="taster-hook">${esc(a.hook)}</p><a class="taster-more" href="#/f/${p.id}/info" data-taster-product="${p.id}">나의 ${esc(p.short)} 무료로 미리보기 →</a></article>`}
function tasterChart(r){const c=r.chart;
 return `<div class="taster-chart">${c.columns.map(x=>`<div class="tc-col${x.me?' me':''}"><small>${x.label}</small><b>${x.hanja?esc(x.hanja[0]):'?'}</b><b>${x.hanja?esc(x.hanja[1]):'?'}</b><span>${x.ko?esc(x.ko):'모름'}</span>${x.me?'<em>나</em>':''}</div>`).join('')}</div><p class="taster-note">${esc(r.name)} 님이 태어난 해·달·날·시를 여덟 글자로 바꾼 것이 사주팔자입니다. ${esc(r.name)} 님은 ${esc(c.zodiac)}띠입니다.${c.columns[0].hanja?'':' 태어난 시간을 몰라서 시 자리는 비워 두었습니다.'}</p>
 <section class="taster-box"><h3>${esc(r.name)} 님 사주 한눈에 보기</h3>${c.items.map(it=>`<div class="tb-item"><strong>${esc(it.head)}</strong><p>${esc(it.text)}</p></div>`).join('')}<div class="tb-bars">${c.elements.map(e=>`<div class="tb-bar ${e.status}"><span>${esc(e.word)}</span><i><b style="width:${Math.min(100,e.pct*2)}%"></b></i><em>${e.pct}%</em></div>`).join('')}</div></section>`}
// 무료 결과 공유 카드(자청 기획안 H-2, 2026-11-05, 그림은 금월선녀 master): 좋은 운 1위를 인스타 스토리 크기(1080×1920) 그림으로 저장·공유. 글은 결과 화면 그대로(제1조항). 링크는 /s(공유로 온 손님 꼬리표).
// 무료 결과 '금월선녀가 고른 다음 한 권'과 나머지 운 안내(사장님 2026-11-06): 사주 이름을 짚고, 결과에 나온 운과 리포트를 이어 준다.
// 공유 카드 자리는 나머지 다섯 운을 그 사람 결과(순위·좋은/조심)대로 안내하는 칸으로 바꿨다.
const TP_COPY={
reunion:{good:'{n} 님 사주에는 끊어진 인연을 다시 잇는 힘이 있어요. 재회사주는 앞으로 24개월 가운데 연락이 다시 닿기 쉬운 달과, 그 달에 보낼 첫마디까지 짚어 드려요.',bad:'{n} 님 사주에는 다시 만나도 같은 이유로 엇갈리기 쉬운 기운이 있어요. 재회사주는 언제 연락하면 엇갈리는지, 다시 만나도 헤어지지 않으려면 무엇을 바꿔야 하는지 짚어 드려요.',free:'앞으로 24개월, 다시 이어지기 좋은 달 지도',row:{good:'연락이 다시 닿기 쉬운 달을 24개월 지도로',bad:'엇갈리는 달과 다시 헤어지지 않는 법'}},
romance:{good:'{n} 님 사주에는 사람을 끄는 기운이 있어요. 연애사주는 앞으로 12년 가운데 인연이 들어오는 해와, 나와 맞는 사람의 모습을 짚어 드려요.',bad:'{n} 님 사주는 인연이 오는 때를 놓치기 쉬운 구조예요. 연애사주는 배우자 별·도화·합이 들어오는 해를 짚어, 그때 어디로 나가야 하는지 알려 드려요.',free:'앞으로 12년, 인연이 들어오는 해 지도',row:{good:'인연이 들어오는 해를 12년 지도로',bad:'인연을 놓치지 않을 해와 만날 자리'}},
intimate:{good:'{n} 님 사주에는 가까운 사람과 손을 잡는 기운이 있어요. 깊은 궁합은 두 사람 궁합 점수와, 서로 가까워지는 해를 짚어 드려요.',bad:'{n} 님 사주에는 가까운 사람과 부딪히기 쉬운 기운이 있어요. 깊은 궁합은 상대와 언제 부딪히고 언제 가까워지는지, 서로 상처 주지 않는 법을 짚어 드려요.',free:'두 사람 궁합 점수와 가까워지는 해',row:{good:'두 사람이 가까워지는 해와 궁합 점수',bad:'부딪히는 때와 상처 주지 않는 법'}},
newyear:{good:'{n} 님에게 2027년은 기다린 기운이 들어오는 해예요. 2027 신년운세는 열두 달 가운데 이 기운이 가장 세게 들어오는 달과, 그 달에 할 일을 짚어 드려요.',bad:'{n} 님에게 2027년은 조심할 기운이 들어오는 해예요. 2027 신년운세는 열두 달을 돕는 달과 조심할 달로 나눠, 무엇을 미루고 무엇을 시작할지 짚어 드려요.',free:'2027년 열두 달, 돕는 달과 조심할 달',row:{good:'2027년 기운이 가장 세게 들어오는 달',bad:'2027년 조심할 달과 돕는 달'}},
wealth:{good:'{n} 님 사주에는 돈이 붙는 구조가 있어요. 재물운은 앞으로 12년 가운데 돈이 들어오는 해와, 그때 어디에 넣어야 하는지 짚어 드려요.',bad:'{n} 님 사주에는 돈이 새기 쉬운 구조가 있어요. 재물운은 돈이 새는 해와 막는 법, 돈이 들어오는 해를 함께 짚어 드려요.',free:'앞으로 12년, 돈이 들어오는 해 지도',row:{good:'돈이 들어오는 해를 12년 지도로',bad:'돈이 새는 해와 막는 법'}},
career:{good:'{n} 님 사주에는 일에서 인정받는 기운이 있어요. 직업·이직운은 앞으로 12년 가운데 옮기기 좋은 해와, 나에게 맞는 일을 짚어 드려요.',bad:'{n} 님 사주에는 일에서 부딪히기 쉬운 기운이 있어요. 직업·이직운은 버텨야 할 해와 옮겨도 되는 해를 나눠 짚어 드려요.',free:'앞으로 12년, 옮기기 좋은 해 지도',row:{good:'옮기기 좋은 해와 나에게 맞는 일',bad:'버틸 해와 옮겨도 되는 해'}},
business:{good:'{n} 님 사주에는 혼자 결정하고 버티는 힘이 있어요. 사업운은 크게 키워도 되는 해와 지켜야 할 해를 12년 지도로 짚어 드려요.',bad:'{n} 님 사주에는 사업에서 돈이 새기 쉬운 기운이 있어요. 사업운은 동업·투자를 조심할 해와 키워도 되는 해를 나눠 짚어 드려요.',free:'앞으로 12년, 키울 해와 지킬 해 지도',row:{good:'크게 키워도 되는 해와 지킬 해',bad:'동업·투자를 조심할 해'}},
health:{good:'{n} 님 사주에는 몸을 받쳐 주는 기운이 있어요. 건강운은 몸이 힘을 받는 해와, 오래 지키는 생활 리듬을 짚어 드려요.',bad:'{n} 님 사주에는 한 기운이 모자라 먼저 지치기 쉬운 자리가 있어요. 건강운은 무리하면 안 되는 해와, 내 몸에 맞는 생활 리듬을 짚어 드려요.',free:'내 생활 리듬과 쉬어야 할 해',row:{good:'몸이 힘을 받는 해와 생활 리듬',bad:'무리하면 안 되는 해와 생활 리듬'}}};
function tasterPickHtml(r){const all=[...r.good.map((a,i)=>[a,'good',i+1]),...r.bad.map((a,i)=>[a,'bad',i+1])].filter(([a])=>pById(a.product)&&TP_COPY[a.product]);const c=all;/* 사장님 2026-11-06: 좋은 운 1위부터 크게 보여 준다(순위 그대로) */const n=esc(r.name),K={good:'좋은 운',bad:'조심할 운'};let html='';const pick=c[0];if(pick){const [a,k,rank]=pick,pp=pById(a.product),C=TP_COPY[pp.id];html+=`<a class="taster-pick" href="#/f/${pp.id}/info" data-taster-product="${pp.id}"><span class="eyebrow">금월선녀가 고른 다음 한 권</span><strong>${n} 님은<br>${esc(pp.short)}부터 보세요</strong><p class="tp-why"><em class="${k}">${K[k]} ${rank}위</em>'${esc(a.title)}' 운은 ${esc(pp.short)}에서 자세히 봐요.</p><p>${esc(C[k].replace('{n}',r.name))}</p><ul><li>무료로 공개: ${esc(C.free)}</li><li>방금 넣은 생일 그대로, 다시 입력 없이</li></ul><span class="taster-pick-cta">내 ${esc(pp.short)} 무료로 보기 →</span></a>`}const rest=all.filter(x=>x!==pick);if(rest.length)html+=`<section class="taster-others"><h3>${n} 님 결과에 맞춘<br>다른 리포트 ${rest.length}개</h3><p class="tos-sub">무료 결과에 나온 운마다, 이어서 볼 리포트를 골라 뒀어요.</p>${rest.map(([a,k,rank])=>{const pp=pById(a.product);return `<a class="tos-row" href="#/f/${pp.id}/info" data-taster-product="${pp.id}"><span class="tos-tag ${k}">${K[k]} ${rank}위 · ${esc(a.title)}</span><b>${esc(pp.short)}</b><span class="tos-line">${esc(TP_COPY[pp.id].row[k])}</span><span class="tos-go">무료로 보기 →</span></a>`}).join('')}</section>`;return html}
function tasterShareBox(r){const a=r.good[0];if(!a)return '';return `<section class="taster-share"><h3>내 좋은 운, 카드로 남기기</h3><p>'${esc(a.title)}' 운을 인스타 스토리 크기 카드로 저장하거나 친구에게 보내 보세요.</p><button type="button" class="tm-send" id="taster-share-btn">좋은 운 카드 저장·공유</button></section>`}
async function tasterShareCard(r){const a=r.good[0];if(!a)return;const W=1080,H=1920,c=document.createElement('canvas');c.width=W;c.height=H;const x=c.getContext('2d');try{await document.fonts.ready}catch{}
 const g=x.createLinearGradient(0,0,0,H);g.addColorStop(0,'#1b140a');g.addColorStop(1,'#07060a');x.fillStyle=g;x.fillRect(0,0,W,H);x.strokeStyle='#d8bb78';x.lineWidth=6;x.strokeRect(60,60,W-120,H-120);x.lineWidth=2;x.strokeRect(80,80,W-160,H-160);
 const F=(s,w=700)=>`${w} ${s}px 'Pretendard Variable','Apple SD Gothic Neo','Malgun Gothic',sans-serif`;
 const wrap=(t,maxW,font)=>{x.font=font;const out=[];let line='';for(const ch of String(t)){const tt=line+ch;if(x.measureText(tt).width>maxW&&line){out.push(line);line=ch}else line=tt}if(line)out.push(line);return out};
 x.textAlign='center';x.fillStyle='#d8bb78';x.font=F(44,700);x.fillText('금월선녀 무료 사주',W/2,220);
 x.fillStyle='#fff';x.font=F(60,800);x.fillText(`${r.name} 님의 좋은 운 1위`,W/2,330);
 x.fillStyle='#f0c75e';let y=520;for(const l of wrap(a.title,W-240,F(104,900))){x.font=F(104,900);x.fillText(l,W/2,y);y+=130}
 const first=String(a.text).split(/(?<=[.!?])\s/).slice(0,3).join(' ');x.fillStyle='#f3efe6';y+=40;for(const l of wrap(first,W-260,F(46,500)).slice(0,8)){x.font=F(46,500);x.fillText(l,W/2,y);y+=72}
 x.fillStyle='#fff';y+=40;for(const l of wrap(a.hook,W-260,F(48,800)).slice(0,4)){x.font=F(48,800);x.fillText(l,W/2,y);y+=74}
 try{const im=new Image();im.src='assets/geumwol/master.webp';await im.decode();const top=y+30,bot=H-380,h=Math.max(0,bot-top),w=Math.min(W-240,h*im.width/im.height);if(h>200){x.save();x.beginPath();x.roundRect((W-w)/2,top,w,h,24);x.clip();const sc=Math.max(w/im.width,h/im.height),dw=im.width*sc,dh=im.height*sc;x.drawImage(im,(W-dw)/2,top+(h-dh)*0.2,dw,dh);x.restore()}}catch{}
 x.fillStyle='#d8bb78';x.font=F(44,700);x.fillText('내 좋은 운 3개도 무료로 보기',W/2,H-300);x.fillStyle='#fff';x.font=F(56,800);x.fillText('unmyeong-saju.com/s',W/2,H-220);
 const blob=await new Promise(res=>c.toBlob(res,'image/png'));const file=new File([blob],'운명서재-좋은운.png',{type:'image/png'});window.uTrack&&uTrack('taster_share',{});
 try{if(navigator.canShare&&navigator.canShare({files:[file]})){await navigator.share({files:[file],text:'내 좋은 운 1위 · unmyeong-saju.com/s'});return}}catch(e){if(e&&e.name==='AbortError')return}
 const u=URL.createObjectURL(blob),dl=document.createElement('a');dl.href=u;dl.download=file.name;document.body.append(dl);dl.click();dl.remove();setTimeout(()=>URL.revokeObjectURL(u),4000);toast('카드를 저장했어요. 인스타 스토리에 올려 보세요.')}
// 결과를 메일로 받아 두기(2026-11-05 사장님 선택 "맛보기 이메일 받기"). 손님이 직접 누를 때만 한 번 보낸다.
// 서버가 같은 계산기로 다시 계산해 메일을 쓰고, 생년월일은 저장하지 않는다. 소식 받기는 따로 고르는 선택(기본 꺼짐), 할인·가격은 메일에 없다.
function tasterMailBox(r){return `<section class="taster-mail" id="taster-mail"><h3>이 결과, 메일로 받아 두세요</h3><p>좋은 운 3개와 조심할 운 3개를 메일로 보내 드려요. 생각날 때 다시 열어 보세요.</p><form id="taster-mail-form" novalidate><label class="tm-field"><span>받을 이메일</span><input type="email" name="email" inputmode="email" autocomplete="email" maxlength="120" placeholder="example@naver.com" value="${esc(savedEmail())}"></label><label class="tm-check"><input type="checkbox" name="agree"><span><b>(필수)</b> 결과 메일을 보내려고 이메일과 이름을 받는 데 동의해요. 생년월일은 메일을 만들 때만 쓰고 저장하지 않아요. <a href="#/legal/privacy">자세히</a></span></label><label class="tm-check"><input type="checkbox" name="news"><span><b>(선택)</b> 새 리포트 소식도 메일로 받을게요(광고성 정보). 메일 속 링크로 언제든 그만 받을 수 있어요.</span></label><button type="submit" class="tm-send">결과 메일로 받기</button><p class="tm-msg" role="status" aria-live="polite"></p></form></section>`}
function bindTasterMail(){const f=document.querySelector('#taster-mail-form');if(!f)return;const msg=f.querySelector('.tm-msg'),btn=f.querySelector('.tm-send');
 f.onsubmit=async e=>{e.preventDefault();const email=f.email.value.trim();msg.className='tm-msg';
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)){msg.textContent='이메일 주소를 다시 확인해 주세요.';msg.classList.add('bad');f.email.focus();return}
  if(!f.agree.checked){msg.textContent='(필수) 동의에 체크해 주셔야 보낼 수 있어요.';msg.classList.add('bad');return}
  btn.disabled=true;btn.textContent='보내는 중이에요';
  try{const res=await fetch('/api/taster-mail',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,agree:true,news:f.news.checked,person:tasterState.person,solar:tasterState.solar,from:(()=>{try{return JSON.parse(localStorage.getItem('unmyeong.from')||'{}').f||''}catch{return ''}})()})});
   const b=await res.json().catch(()=>({}));
   if(res.ok){rememberEmail(email);window.uTrack&&uTrack('taster_mail',{news:f.news.checked?1:0});msg.textContent=`보냈어요. ${email} 메일함을 확인해 주세요. 안 보이면 스팸함도 봐 주세요.`;msg.classList.add('ok');btn.textContent='보냈어요';return}
   msg.textContent=({TOO_MANY:'오늘은 이 메일로 더 보낼 수 없어요. 내일 다시 눌러 주세요.',BAD_EMAIL:'이메일 주소를 다시 확인해 주세요.',BAD_NAME:'이름은 한글이나 영문 12자 안으로 넣어 주세요. 위 "입력한 정보 고쳐서 다시 보기"에서 고칠 수 있어요.'})[b.code]||'보내지 못했어요. 잠시 뒤 다시 눌러 주세요.';msg.classList.add('bad')}
  catch{msg.textContent='보내지 못했어요. 인터넷 연결을 확인하고 다시 눌러 주세요.';msg.classList.add('bad')}
  btn.disabled=false;btn.textContent='결과 메일로 받기'}}
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
   try{const {eng,tst,data,texts}=await tasterLoad();const date=validateBirthDate(v);const fp=eng.chartFromPerson(data,v,v.calendar==='lunar'?date.solarDate:v.birth);rememberMe(v);tasterState={person:v,solar:v.calendar==='lunar'?date.solarDate:v.birth,result:tst.reading(fp,v,texts)};try{const rr=tasterState.result;localStorage.setItem('unmyeong.tasterPicks',JSON.stringify({good:rr.good.map(a=>a.product),bad:rr.bad.map(a=>a.product),at:Date.now()}))}catch{}window.uTrack&&uTrack('taster_result',{});tasterPage();window.scrollTo({top:0,behavior:'instant'})}
   catch(err){console.error(err);btn.disabled=false;btn.textContent='무료로 내 운 보기';toast('계산하지 못했어요. 잠시 뒤 다시 눌러 주세요.')}};
  return}
 layout('금월선녀 무료 사주 분석',`<div class="page-pad taster-result">${revealSpeech(pById('lifetime'),`${r.name} 님의 좋은 운과 조심할 운을\n자세하게 알려드릴게요\n지금부터 집중해주세요!`)}${tasterChart(r)}<h2 class="taster-head good">좋은 운 TOP 3</h2>${r.good.map((a,i)=>tasterItem(a,'good',i)).join('')}<h2 class="taster-head bad">조심할 운 TOP 3</h2>${r.bad.map((a,i)=>tasterItem(a,'bad',i)).join('')}${tasterPickHtml(r)}${tasterMailBox(r)}<a class="taster-lifetime" href="#/f/lifetime/info" data-taster-product="lifetime"><span class="eyebrow">내 사주 전체</span><strong>내 사주 전체를<br>한 권으로 보고 싶다면</strong><span>${esc(pById('lifetime').name)} 자세히 알아보기 →</span></a><div class="taster-all"><p>다른 운도 자세히 보기</p>${['newyear','romance','reunion','intimate','wealth','career','business','health'].map(id=>`<a href="#/f/${id}/info" data-taster-product="${id}">${esc(pById(id).short)}</a>`).join('')}</div><button type="button" class="taster-redo" id="taster-redo">입력한 정보 고쳐서 다시 보기</button></div>`);
 // 잘못 넣었을 수 있으니, 넣었던 정보를 그대로 채운 입력 화면으로 돌아간다.
 bindTasterMail();
 {const sb=document.querySelector('#taster-share-btn');if(sb)sb.onclick=()=>tasterShareCard(tasterState.result)}
 document.querySelector('#taster-redo').onclick=()=>{tasterState.result=null;tasterPage();window.scrollTo({top:0,behavior:'instant'})};
 // '자세히 알아보기'로 간 상품에는 방금 넣은 출생 정보를 미리 채워 둔다.
 document.querySelectorAll('[data-taster-product]').forEach(a=>a.addEventListener('click',()=>{window.uTrack&&uTrack('taster_click',{product:a.dataset.tasterProduct});const d=draft(a.dataset.tasterProduct);if(!d.self||!personValid(d.self)){d.self={...tasterState.person};save()}}));
}
