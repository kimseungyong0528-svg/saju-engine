"""시험용 샘플: (1) 스레드 글 캡처 릴스 (2) 띠 티어표 영상. 결과: lab/samples/out/"""
import base64, json, subprocess, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from saju.marketing.ranking import rank, month_period
from saju.marketing.video import music
from saju.marketing.content import birth_years

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "lab" / "samples" / "out"; OUT.mkdir(parents=True, exist_ok=True)
PRET = (ROOT / "site/public/assets/fonts/PretendardVariable.woff2").as_uri()
BHS = (ROOT / "saju/marketing/fonts/BlackHanSans.ttf").as_uri()
PIC = "data:image/jpeg;base64," + base64.b64encode(pathlib.Path("/mnt/project-files/samples/marketing/프로필사진/2-금월선녀-붉은한복.jpg").read_bytes()).decode()
HANDLE = "unmyeong_saju.kr"

POSTS = [
 ("2026. 11. 1.", "흥미로운 사주 이야기 (금월선녀 ver.) - 1탄", [
  "일지에 도화가 있는 사람은 꾸미지 않아도 사람이 먼저 다가온다. 연애 시작은 쉬운데 고르는 게 어렵다.",
  "관성이 없는 여자는 남자복이 없는 게 아니다. 고르는 기준이 남다를 뿐이다. 대운에서 관성이 들어오면 인연이 확 붙는다.",
  "식상이 강한 사람은 말로 돈을 번다. 영업, 강의, 방송 쪽에서 빛난다.",
  "인성이 많은 사람은 생각이 많아서 시작이 늦다. 대신 한 번 시작하면 끝까지 간다.",
  "재성이 없는 사주라고 돈이 없는 게 아니다. 돈을 쫓지 않을 때 오히려 돈이 붙는다.",
  "비겁이 강한 사람은 동업하면 손해 보기 쉽다. 혼자 결정하는 일이 맞다."], None),
 ("2026. 11. 1.", "<연애할 때 절대 먼저 연락 안 하는 사주>", [
  "경금 일간 - 자존심이 손가락을 막는다",
  "신금 일간 - 상대가 먼저 오는지 조용히 지켜본다",
  "계수 일간 - 마음은 이미 보냈는데 손이 안 간다",
  "무토 일간 - 연락할 이유가 생길 때까지 기다린다",
  "편관이 강한 사람 - 먼저 하면 지는 거라고 생각한다"],
  "근데 이 사람들, 답장은 제일 빨리 한다.\n먼저 한 번만 보내 봐요."),
 ("2026. 11. 1.", "흥미로운 사주 이야기 (금월선녀 ver.) - 2탄", [
  "정재가 있는 사람은 월급이 잘 맞는다. 큰돈보다 꾸준한 돈이 쌓인다.",
  "편재가 있는 사람은 부업이나 투자로 돈을 만질 일이 많다. 대신 들어온 만큼 나가기도 쉽다.",
  "상관이 강한 사람은 회사에서 윗사람과 부딪히기 쉽다. 내 일을 할 때 운이 열린다.",
  "역마가 있는 사람은 한자리에 오래 있으면 답답해한다. 출장과 이동이 많은 일이 맞다.",
  "화개가 있는 사람은 혼자 있는 시간이 있어야 기운이 찬다.",
  "천을귀인이 있는 사람은 힘들 때 꼭 누군가 나타나 도와준다."], None),
]

CARD = """<!doctype html><html><head><meta charset=utf-8><style>
@font-face{font-family:P;src:url(PRET) format('woff2');font-weight:100 900}
html,body{margin:0;width:1080px;height:1920px;background:#101010;font-family:P}
.card{position:absolute;left:40px;right:40px;top:50%;transform:translateY(-50%);background:#fff;border-radius:28px;padding:56px 54px 48px}
.top{display:flex;align-items:center;gap:22px;margin-bottom:30px}
.top img{width:96px;height:96px;border-radius:50%;object-fit:cover}
.name{font-weight:700;font-size:38px;color:#111}.date{font-size:30px;color:#999;margin-left:6px;font-weight:400}
.ttl{font-size:41px;font-weight:600;color:#111;margin-bottom:26px;line-height:1.45}
ol{margin:0;padding-left:0;list-style:none;counter-reset:n}
li{counter-increment:n;font-size:39px;line-height:1.55;color:#111;margin-bottom:14px}
li:before{content:counter(n) ". "}
.end{font-size:39px;line-height:1.55;color:#111;margin-top:24px;white-space:pre-line}
.foot{display:flex;gap:46px;margin-top:34px;font-size:32px;color:#555}
</style></head><body><div class=card><div class=top><img src="PIC"><div class=name>HANDLE <span class=date>DATE</span></div></div>
<div class=ttl>TITLE</div><ol>ITEMS</ol>END<div class=foot><span>♡</span><span>💬</span><span>↻</span><span>➤</span></div></div></body></html>"""

def threads_reels(pg):
    for i, (date, title, items, end) in enumerate(POSTS, 1):
        h = (CARD.replace("PRET", PRET).replace("PIC", PIC).replace("HANDLE", HANDLE).replace("DATE", date)
             .replace("TITLE", title).replace("ITEMS", "".join(f"<li>{x}</li>" for x in items))
             .replace("END", f"<div class=end>{end}</div>" if end else ""))
        f=OUT/"_c.html"; f.write_text(h,encoding="utf-8"); pg.goto(f.as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        png = OUT / f"스레드-{i}.png"; pg.screenshot(path=str(png))
        bgm = music.ambient(6.0, OUT / f"bgm{i}.wav", seed=i * 5)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(bgm), "-t", "5",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-shortest",
                        str(OUT / f"스레드릴스-{i}.mp4")], check=True)

TIERS = [("S", "#e8453c", 0, 2), ("A", "#f08a3c", 2, 5), ("B", "#f2c94c", 5, 8), ("C", "#7cc56b", 8, 10), ("D", "#5b8def", 10, 12)]

TIER = """<!doctype html><html><head><meta charset=utf-8><style>
@font-face{font-family:P;src:url(PRET) format('woff2');font-weight:100 900}
@font-face{font-family:B;src:url(BHS)}
html,body{margin:0;width:1080px;height:1920px;background:#14110f;font-family:P;color:#fff;overflow:hidden}
.h1{font-family:B;text-align:center;font-size:92px;line-height:1.15;margin-top:150px}
.h1 em{font-style:normal;color:#ffd24a}
.sub{text-align:center;font-size:38px;color:#bbb;margin-top:22px}
.board{margin:70px 40px 0;border:3px solid #333}
.row{display:flex;min-height:205px;border-bottom:3px solid #333;opacity:0;transform:translateX(-60px)}
.row.on{opacity:1;transform:none;transition:all .35s}
.tag{width:170px;display:flex;align-items:center;justify-content:center;font-family:B;font-size:110px;color:#111}
.cells{flex:1;display:flex;flex-wrap:wrap;align-items:center;gap:18px;padding:18px 22px;background:#1f1b18}
.c{background:#2e2824;border-radius:18px;padding:14px 22px;text-align:center}
.c b{display:block;font-family:B;font-size:58px}.c span{font-size:28px;color:#bbb}
.cta{position:absolute;bottom:150px;width:100%;text-align:center;font-family:B;font-size:66px;opacity:0}
.cta.on{opacity:1;transition:opacity .4s}
</style></head><body><div class=h1>11월 <em>재물운</em><br>띠 티어표</div><div class=sub>2026년 11월 · 기해월 기준</div>
<div class=board>ROWS</div><div class=cta id=cta>내 띠는 몇 티어? 댓글로 👇</div>
<script>window.show=n=>{document.querySelectorAll('.row').forEach((r,i)=>{if(i>=5-n)r.classList.add('on')}); if(n>5)document.getElementById('cta').classList.add('on')}</script>
</body></html>"""

def tier_video(pg):
    rows = rank("money", month_period(2026, 11))
    html_rows = ""
    for t, col, a, b in TIERS:
        cells = "".join(f"<div class=c><b>{r.ddi}띠</b><span>{"·".join(f"{y%100:02d}" for y in birth_years(r.ddi) if 1965<=y<=2005)}년생</span></div>" for r in rows[a:b])
        html_rows += f"<div class=row><div class=tag style='background:{col}'>{t}</div><div class=cells>{cells}</div></div>"
    f=OUT/"_t.html"; f.write_text(TIER.replace("PRET", PRET).replace("BHS", BHS).replace("ROWS", html_rows),encoding="utf-8"); pg.goto(f.as_uri())
    pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
    frames = OUT / "tier"; frames.mkdir(exist_ok=True)
    # 0~1.5초 제목, 그다음 D→S 1.6초씩, 마지막 문구 2.5초
    shots = [(0, 1.5)] + [(n, 1.6) for n in range(1, 6)] + [(6, 2.5)]
    lst = []
    for k, (n, d) in enumerate(shots):
        pg.evaluate(f"window.show({n})"); pg.wait_for_timeout(450)
        f = frames / f"{k}.png"; pg.screenshot(path=str(f)); lst.append((f, d))
    (frames / "list.txt").write_text("".join(f"file '{f}'\nduration {d}\n" for f, d in lst) + f"file '{lst[-1][0]}'\n")
    total = sum(d for _, d in lst)
    bgm = music.ambient(total + 1, OUT / "bgm-tier.wav", seed=21)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(frames / "list.txt"), "-i", str(bgm),
                    "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(OUT / "티어표-11월재물운.mp4")], check=True)
    pg.evaluate("window.show(6)"); pg.wait_for_timeout(450); pg.screenshot(path=str(OUT / "티어표-11월재물운.png"))
    print(json.dumps([(r.rank, r.ddi, r.score, r.good[:1]) for r in rows], ensure_ascii=False))

with sync_playwright() as p:
    br = p.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1080, "height": 1920})
    threads_reels(pg); tier_video(pg)
    br.close()
