"""시험용 아침 샘플 3종: 솔로사주식(풍경+가운데 제목), 포스텔러식(위 큰 제목+아래 설명), 신비사주식(날짜별 띠 운세 표)."""
import subprocess, sys, pathlib, datetime as dt
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from saju.marketing.ranking import rank, month_period, Period, KINDS
from saju.marketing.content import birth_years
from saju.marketing.video import music
from saju.pillars import day_pillar_for_date

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "lab" / "samples" / "out"; OUT.mkdir(parents=True, exist_ok=True)
PRET = (ROOT / "site/public/assets/fonts/PretendardVariable.woff2").as_uri()
BHS = (ROOT / "saju/marketing/fonts/BlackHanSans.ttf").as_uri()
BG = (ROOT / "site/public/assets/geumwol/palace-garden.jpg").as_uri()
CSS = f"@font-face{{font-family:P;src:url({PRET}) format('woff2');font-weight:100 900}}@font-face{{font-family:B;src:url({BHS})}}html,body{{margin:0;width:1080px;height:1920px;overflow:hidden;font-family:P}}"
yrs = lambda d: "·".join(f"{y % 100:02d}" for y in birth_years(d) if 1965 <= y <= 2005)

def shot(pg, html, name):
    f = OUT / f"_{name}.html"; f.write_text(html, encoding="utf-8"); pg.goto(f.as_uri())
    pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(400)
    png = OUT / f"{name}.png"; pg.screenshot(path=str(png)); return png

def ff(*a): subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)

# 1) 솔로사주식: 배경이 천천히 다가오고 가운데 2줄 제목, 7초
def solo(pg):
    top = rank("love", month_period(2026, 11))[:3]
    html = f"""<html><head><meta charset=utf-8><style>{CSS}body{{background:transparent}}
    .box{{position:absolute;top:760px;left:0;right:0;text-align:center;font-family:B;line-height:1.25}}
    .l{{display:inline-block;background:#000;color:#fff;font-size:92px;padding:10px 30px;border-radius:14px}}
    .r{{display:inline-block;background:#000;color:#ff2a2a;font-size:92px;padding:6px 30px;border-radius:14px;margin-top:-4px}}</style></head>
    <body><div class=box><div class=l>11월에 연애운</div><br><div class=r>들어오는 띠 3개</div></div></body></html>"""
    png = shot(pg, html, "아침A-제목")
    bgm = music.ambient(8, OUT / "bgmA.wav", seed=33)
    ff("-loop", "1", "-i", str(ROOT / "site/public/assets/geumwol/palace-garden.jpg"), "-i", str(png), "-i", str(bgm),
       "-filter_complex", "[0]scale=1620:-2,crop=1620:2880,zoompan=z='1+0.0009*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=210:s=1080x1920:fps=30[bg];[bg][1]overlay=0:0,format=yuv420p[v]",
       "-map", "[v]", "-map", "2", "-t", "7", "-c:v", "libx264", "-c:a", "aac", str(OUT / "아침A-솔로사주식.mp4"))
    cap = ("💬 댓글에 본인 띠만 남겨 주세요\n11월에 들어오는 인연이 어떤 사람인지 DM 보내 드릴게요💌\n\n—\n\n"
           f"11월은 기해월이에요.\n띠 글자와 짝이 맞는 달에는 연락이 다시 붙고 약속이 잡혀요.\n\n본문에는 힌트만 남길게요 👀\n\n"
           + "\n".join(f"✅ {i}위 {r.ddi}띠 ({yrs(r.ddi)}년생)\n{(r.good or ['좋은 기운이 들어와요'])[0]}" for i, r in enumerate(top, 1)))
    (OUT / "아침A-캡션.txt").write_text(cap, encoding="utf-8")

# 2) 포스텔러식: 위 큰 2줄 제목 고정 + 아래 설명 카드가 바뀜, 약 20초
def fortell(pg):
    lines = ["수(水) 기운이 없는 사람은\n생각보다 몸이 먼저 움직여요", "쉬어야 할 때도 계속 달려서\n번아웃이 자주 와요",
             "수 기운이 많은 사람을 만나면\n속도를 맞춰 주는 브레이크가 생겨요", "대신 결정은 늦어져요\n서로 역할을 나누면 오래 가요",
             "내 사주에 수가 있는지 궁금하면\n댓글에 '수' 남겨 주세요"]
    pngs = []
    for i, t in enumerate(lines):
        html = f"""<html><head><meta charset=utf-8><style>{CSS}body{{background:#0b0b0b}}
        .t{{height:560px;display:flex;flex-direction:column;justify-content:center;text-align:center;font-family:B;font-size:104px;line-height:1.2;color:#fff}}
        .t em{{font-style:normal;color:#ffd23f}}
        .art{{height:1360px;background:linear-gradient(160deg,#e8f1ee,#f7ece6);position:relative}}
        .o{{position:absolute;width:210px;height:210px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;font-family:B;font-size:96px}}
        .o span{{font-family:P;font-size:30px;font-weight:600}}
        .say{{position:absolute;left:60px;right:60px;bottom:120px;background:rgba(0,0,0,.82);color:#fff;border-radius:26px;padding:40px;font-size:56px;font-weight:700;line-height:1.4;text-align:center;white-space:pre-line}}
        .w{{opacity:.25}}</style></head><body><div class=t><div><em>수 기운 없는 사주</em>가</div><div>꼭 만나야 하는 사람</div></div>
        <div class=art>
        <div class="o w" style="left:435px;top:90px;background:#4caf7a">木<span>나무</span></div>
        <div class="o w" style="left:760px;top:330px;background:#e0505a">火<span>불</span></div>
        <div class="o w" style="left:640px;top:690px;background:#d9a520">土<span>흙</span></div>
        <div class="o w" style="left:230px;top:690px;background:#9a9a9a">金<span>쇠</span></div>
        <div class="o" style="left:110px;top:330px;background:#2f7fd6;box-shadow:0 0 0 14px rgba(47,127,214,.25)">水<span>물</span></div>
        <div class=say>{t}</div></div></body></html>"""
        pngs.append(shot(pg, html, f"아침B-{i}"))
    lst = OUT / "B.txt"; lst.write_text("".join(f"file '{p}'\nduration 3.8\n" for p in pngs) + f"file '{pngs[-1]}'\n")
    bgm = music.ambient(20, OUT / "bgmB.wav", seed=44)
    ff("-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(bgm), "-vf", "fps=30,format=yuv420p", "-c:v", "libx264",
       "-c:a", "aac", "-shortest", str(OUT / "아침B-포스텔러식.mp4"))

# 3) 신비사주식: 오늘 띠별 운세 표 1장, 5초
def daily(pg):
    d = dt.date(2026, 11, 1); p = day_pillar_for_date(d)
    per = Period(d.isoformat(), "오늘", f"{d.month}월 {d.day}일", p.stem, p.branch, None)
    rows = {}
    for kind in ("money", "love", "care"):
        for r in rank(kind, per):
            rows.setdefault(r.ddi, []).append((kind, r))
    order = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    cells = ""
    for a in order:
        m, l, c = (dict(rows[a])[k] for k in ("money", "love", "care"))
        if c.rank <= 2: txt = "말이 부딪히기 쉬운 날. 큰 결정은 내일로 미뤄요."
        elif m.rank <= 3: txt = "돈 들어올 일이 생기는 날. 미뤄 둔 연락을 먼저 해요."
        elif l.rank <= 3: txt = "사람 운이 좋은 날. 약속을 잡으면 좋은 소식이 와요."
        else: txt = (m.good or l.good or ["평소처럼 지내면 무난한 날이에요."])[0] + "."
        cells += f"<div class=c><b>{a}띠</b><span>{yrs(a)}</span><p>{txt}</p></div>"
    html = f"""<html><head><meta charset=utf-8><style>{CSS}body{{background:#fffaf2}}
    h1{{font-family:B;font-size:84px;text-align:center;margin:120px 0 10px;color:#2a1d14}} .s{{text-align:center;font-size:34px;color:#8a6d55}}
    .g{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:50px 36px}}
    .c{{background:#fff;border:3px solid #ead9c4;border-radius:22px;padding:22px 24px}} .c b{{font-family:B;font-size:46px;color:#a8262b}}
    .c span{{font-size:24px;color:#9a8470;margin-left:10px}} .c p{{margin:10px 0 0;font-size:31px;line-height:1.4;color:#2a1d14;font-weight:600}}
    .f{{text-align:center;font-size:30px;color:#8a6d55}}</style></head><body><h1>{d.month}월 {d.day}일 띠별 운세</h1>
    <div class=s>오늘은 {p.stem and ''}{ ['갑','을','병','정','무','기','경','신','임','계'][p.stem] }{['자','축','인','묘','진','사','오','미','신','유','술','해'][p.branch]}일 · @unmyeong_saju.kr</div>
    <div class=g>{cells}</div></body></html>"""
    png = shot(pg, html, "아침C-띠별운세표")
    bgm = music.ambient(6, OUT / "bgmC.wav", seed=55)
    ff("-loop", "1", "-i", str(png), "-i", str(bgm), "-t", "5", "-vf", "format=yuv420p", "-c:v", "libx264", "-r", "30",
       "-c:a", "aac", "-shortest", str(OUT / "아침C-신비사주식.mp4"))

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium", args=["--no-sandbox"])
    pg = br.new_page(viewport={"width": 1080, "height": 1920})
    solo(pg); fortell(pg); daily(pg)
    br.close()
