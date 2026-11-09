// 전에 입력한 내 정보 다시 쓰기 (2026-10-26 사장님 요청). build_site.py 가 사이트 코드 안에 넣는다.
// 본인 정보를 한 번 넣으면 이 브라우저에 기억해 두고, 다른 상품·무료 분석 입력 화면 맨 위에서 체크 한 번으로 채운다.
const ME_KEY='unmyeong.me';
function savedMe(){try{const v=JSON.parse(localStorage.getItem(ME_KEY)||'null');return v&&personValid(v)?v:null}catch{return null}}
function rememberMe(v){try{if(v&&personValid(v))localStorage.setItem(ME_KEY,JSON.stringify(v))}catch{}}
function meKey(v={}){const p=v.birthPlace||{};return JSON.stringify([v.name,v.sex,v.calendar,v.birth,v.leapStatus,v.timeAccuracy,v.time,v.timeRange,p.status,p.regionChoice,p.districtCode,p.city])}
function reuseBox(current,id){const me=savedMe();if(!me)return '';return `<label class="reuse-me"><input type="checkbox" id="${id}" ${meKey(current)===meKey(me)?'checked':''}><span><b>전에 입력한 내 정보 그대로 쓰기</b><small>${esc(me.name)} · ${personBirthSummary(me)}</small></span></label>`}
// 체크를 풀어도 이미 채운 칸은 지우지 않는다(손님 테스트 2차: 눌렀더니 다 지워져 0/4가 됨). 고칠 칸만 고치면 된다.
// 빈 칸 안내 (2026-11-05): 버튼을 눌렀는데 아무 일도 없으면 손님이 떠난다. 무엇이 비었는지 한 줄로 알려 준다.
function quickMissing(form,v){const f=form.elements,miss=[];if(!v.name)miss.push('이름');const dd=quickDigits(f.namedItem('birth').value,8);if(dd.length<8)miss.push('생년월일 8자리(예: 1990.09.04)');else{const r=validateBirthDate(v);if(!r.valid)return r.message}if(!f.namedItem('timeUnknown').checked&&!v.time)miss.push("태어난 시간(모르면 '시간 모름')");if(!v.sex)miss.push('성별');return miss.length?'아직 비어 있어요: '+miss.join(' · '):''}
// 상대방 정보도 이 브라우저에 기억해 두고(선물 주문 제외), 재회사주·깊은 궁합·결제 페이지에서 한 번에 채운다(2026-11-05).
const PARTNER_KEY='unmyeong.partner';
function savedPartner(){try{const v=JSON.parse(localStorage.getItem(PARTNER_KEY)||'null');return v&&personValid(v)?v:null}catch{return null}}
function rememberPartner(v){try{if(v&&personValid(v))localStorage.setItem(PARTNER_KEY,JSON.stringify(v))}catch{}}
function partnerReuseBox(p,s,d){if(s.who!=='partner'||isGift(p.id))return '';const sp=savedPartner();if(!sp||meKey(d.partner||{})===meKey(sp))return '';return `<label class="reuse-me qi-reuse"><input type="checkbox" data-reuse-partner><span><b>전에 입력한 상대 정보 그대로 쓰기</b><small>${esc(sp.name||'그 사람')} · ${personBirthSummary(sp)}</small></span></label>`}
function bindPartnerExtras(p,s,d){const box=document.querySelector('[data-reuse-partner]');if(box)box.onchange=()=>{if(box.checked){d.partner={...savedPartner()};save();render()}};const help=document.querySelector('[data-partner-unknown]');if(help)help.onclick=()=>partnerUnknownHelp(p)}
// 상대 생년월일을 모를 때 (2026-11-05): 막다른 길 대신 찾는 법과, 상대 정보 없이 볼 수 있는 연애사주를 알려 준다.
function partnerUnknownHelp(p){window.uTrack&&uTrack('partner_unknown',{product:p.id});const m=modal(`<h2>상대 생년월일을 정확히 모르시나요?</h2><div class="modal-prose"><p>${p.id==='reunion'?'재회사주':'깊은 궁합'}는 두 사람 사주를 함께 계산해서, 상대방 생년월일 8자리가 꼭 필요해요. 태어난 시간은 몰라도 괜찮아요('시간 모름'을 눌러 주세요).</p><p>이렇게 찾아보세요: 카카오톡 생일 알림, SNS 프로필, 함께 찍은 사진·메시지의 생일 축하 기록, 같이 아는 친구.</p><p>지금 바로 보고 싶다면, 상대 정보 없이 내 사주만으로 보는 <b>연애사주</b>에서 인연이 들어오는 시기를 먼저 확인할 수 있어요.</p></div><a class="primary" href="#/f/romance/info" data-go-romance>연애사주로 먼저 보기</a><button class="secondary" data-action="close">상대 정보 다시 넣기</button>`,'light-modal','상대 생년월일 안내');const go=m.querySelector('[data-go-romance]');if(go)go.onclick=()=>{const r=draft('romance'),me=draft(p.id).self;if((!r.self||!personValid(r.self))&&me&&personValid(me))r.self={...me};save();window.uTrack&&uTrack('partner_unknown_to_romance',{product:p.id});closeModal()}}
function bindReuse(id,set){const box=document.getElementById(id);if(box)box.onchange=()=>{if(box.checked){set({...savedMe()});render()}}}
// 시·도 목록: 옛 지역명은 빼고, 누구나 아는 짧은 이름으로 보여 준다.
const REGION_PLAIN={'서울특별시':'서울','부산광역시':'부산','대구광역시':'대구','인천광역시':'인천','전남광주통합특별시':'광주·전남','대전광역시':'대전','울산광역시':'울산','세종특별자치시':'세종','경기도':'경기도','강원특별자치도':'강원도','충청북도':'충청북도','충청남도':'충청남도','전북특별자치도':'전라북도','경상북도':'경상북도','경상남도':'경상남도','제주특별자치도':'제주도'};
const REGION_ORDER=Object.keys(REGION_PLAIN);
function plainRegions(){return KOREA_REGIONS.filter(r=>!r.legacy&&REGION_PLAIN[r.name]).sort((a,b)=>REGION_ORDER.indexOf(a.name)-REGION_ORDER.indexOf(b.name))}
// 선물하기(사장님 2026-10-30): 본인 정보 입력 화면 맨 위에서 '내 사주 / 다른 사람 사주(선물)'를 고른다.
// 선물이면 받는 분 정보를 넣고, 문구를 '○○ 님의 정보'로 바꾸며, 이 정보는 '내 정보'로 기억하지 않는다. PDF는 주문한 분 이메일로 간다.
const GIFT_KEY='unmyeong.gift.';
function curPid(){const m=location.hash.match(/#\/f\/([^/]+)/);return m?m[1]:''}
function isGift(pid=curPid()){try{return sessionStorage.getItem(GIFT_KEY+pid)==='1'}catch{return false}}
function setGift(pid,on){try{on?sessionStorage.setItem(GIFT_KEY+pid,'1'):sessionStorage.removeItem(GIFT_KEY+pid)}catch{}}
function giftBox(pid){const g=isGift(pid);return `<div class="gift-pick"><p>누구의 사주인가요?</p><div class="segmented" role="group" aria-label="누구의 사주인가요"><label><input type="radio" name="gift-pick" value="me" ${g?'':'checked'}><span>내 사주</span></label><label><input type="radio" name="gift-pick" value="gift" ${g?'checked':''}><span>다른 사람 사주(선물)</span></label></div>${g?'<small>선물 받을 분의 정보를 넣어 주세요. 결과 PDF는 주문하시는 분 이메일로 보내드려요.</small>':''}</div>`}
function bindGift(pid,d,save){document.querySelectorAll('[name=gift-pick]').forEach(el=>el.onchange=()=>{const on=el.value==='gift';setGift(pid,on);const me=savedMe();if(on&&me&&meKey(d.self)===meKey(me))d.self={};save();render()})}
