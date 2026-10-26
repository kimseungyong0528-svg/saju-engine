// 전에 입력한 내 정보 다시 쓰기 (2026-10-26 사장님 요청). build_site.py 가 사이트 코드 안에 넣는다.
// 본인 정보를 한 번 넣으면 이 브라우저에 기억해 두고, 다른 상품·무료 분석 입력 화면 맨 위에서 체크 한 번으로 채운다.
const ME_KEY='unmyeong.me';
function savedMe(){try{const v=JSON.parse(localStorage.getItem(ME_KEY)||'null');return v&&personValid(v)?v:null}catch{return null}}
function rememberMe(v){try{if(v&&personValid(v))localStorage.setItem(ME_KEY,JSON.stringify(v))}catch{}}
function meKey(v={}){const p=v.birthPlace||{};return JSON.stringify([v.name,v.sex,v.calendar,v.birth,v.leapStatus,v.timeAccuracy,v.time,v.timeRange,p.status,p.regionChoice,p.districtCode,p.city])}
function reuseBox(current,id){const me=savedMe();if(!me)return '';return `<label class="reuse-me"><input type="checkbox" id="${id}" ${meKey(current)===meKey(me)?'checked':''}><span><b>전에 입력한 내 정보 그대로 쓰기</b><small>${esc(me.name)} · ${personBirthSummary(me)}</small></span></label>`}
function bindReuse(id,set){const box=document.getElementById(id);if(box)box.onchange=()=>{set(box.checked?{...savedMe()}:{});render()}}
// 시·도 목록: 옛 지역명은 빼고, 누구나 아는 짧은 이름으로 보여 준다.
const REGION_PLAIN={'서울특별시':'서울','부산광역시':'부산','대구광역시':'대구','인천광역시':'인천','전남광주통합특별시':'광주·전남','대전광역시':'대전','울산광역시':'울산','세종특별자치시':'세종','경기도':'경기도','강원특별자치도':'강원도','충청북도':'충청북도','충청남도':'충청남도','전북특별자치도':'전라북도','경상북도':'경상북도','경상남도':'경상남도','제주특별자치도':'제주도'};
const REGION_ORDER=Object.keys(REGION_PLAIN);
function plainRegions(){return KOREA_REGIONS.filter(r=>!r.legacy&&REGION_PLAIN[r.name]).sort((a,b)=>REGION_ORDER.indexOf(a.name)-REGION_ORDER.indexOf(b.name))}
