"""SNS 공식 영상 그리기: 사장님이 승인한 7가지 모양(2026-11-01, 새양식-샘플/확정)을 그대로 쓰고, 글만 날마다 바뀐다.

HTML 을 Playwright(크로미움)로 찍고 ffmpeg 로 영상으로 만든다. 소리는 saju.marketing.video.music 이 만든 잔잔한 배경음.
글꼴: 저장소 lab/fonts(있으면) 또는 jsdelivr 의 fontsource. 배경 영상·사진: 내려받아 둔 곳(SAJU_MEDIA_DIR) 또는 원래 주소에서 받는다.
"""

from __future__ import annotations

import base64
import math
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from ..video import music
from .text import ELEMENTS, B, Evening, Morning, ddi, years_short

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = HERE / "assets"
FONT_PKGS = [("nanum-myeongjo", "5.3.0", "800"), ("noto-sans-kr", "5.3.1", "400"), ("noto-sans-kr", "5.3.1", "500"),
             ("noto-sans-kr", "5.3.1", "700"), ("noto-sans-kr", "5.3.1", "900"), ("do-hyeon", "5.3.0", "400"), ("jua", "5.3.0", "400")]
BASE = "html,body{margin:0;width:1080px;height:1920px;overflow:hidden}*{box-sizing:border-box}"
EMO = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}
ORDER = list(EMO)
MEDIA_DIRS = [Path(os.environ.get("SAJU_MEDIA_DIR", Path.home() / ".cache" / "saju-media")),
              Path("/mnt/project-files/samples/marketing/무료영상/mixkit"), Path("/mnt/project-files/samples/marketing/무료사진")]


def fonts_css() -> str:
    local = Path(os.environ.get("SAJU_FONT_DIR", ROOT / "lab" / "fonts"))
    out = []
    for pkg, ver, w in FONT_PKGS:
        f = local / f"fontsource-{pkg}-{ver}" / "package" / f"{w}.css"
        out.append(f.as_uri() if f.exists() else f"https://cdn.jsdelivr.net/npm/@fontsource/{pkg}@{ver}/{w}.css")
    return "".join(f"<link rel=stylesheet href='{u}'>" for u in out)


def media(item: dict) -> Path:
    """배경 영상·사진 파일. 없으면 원래 주소에서 한 번 받아 둔다."""
    for d in MEDIA_DIRS:
        p = d / item["file"]
        if p.exists() and p.stat().st_size > 10_000:
            return p
    d = MEDIA_DIRS[0]
    d.mkdir(parents=True, exist_ok=True)
    p = d / item["file"]
    req = urllib.request.Request(item["src"], headers={"User-Agent": "Mozilla/5.0 (unmyeong-saju studio)"})
    with urllib.request.urlopen(req, timeout=120) as r, open(p, "wb") as f:
        shutil.copyfileobj(r, f)
    return p


def _data_uri(p: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


# 관리 사이트(넷리파이 함수)는 한 번에 6MB까지 받는데, 영상은 글자로 바꿔 보내면 4/3배로 커진다.
# 5MB 영상은 6.7MB가 되어 413(너무 큼)으로 막혔다(2026-11-01). 그래서 3.5MB 안으로 줄인다.
MAX_VIDEO = 3_500_000


def _ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)
    out = Path(args[-1])
    if out.suffix == ".mp4" and out.stat().st_size > MAX_VIDEO:
        _shrink(out)


def _shrink(out: Path) -> None:
    """영상이 너무 크면 화질을 조금 낮춰 다시 굽는다. 길이·그림·소리는 그대로다."""
    sec = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                               capture_output=True, text=True, check=True).stdout.strip() or 1)
    kbps = max(200, int(MAX_VIDEO * 8 * 0.85 / sec / 1000) - 96)
    tmp = out.with_name(out.stem + "_작게.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out), "-c:v", "libx264", "-b:v", f"{kbps}k",
                    "-maxrate", f"{kbps}k", "-bufsize", f"{kbps * 2}k", "-c:a", "aac", "-b:a", "96k", str(tmp)], check=True)
    tmp.replace(out)


class Renderer:
    """한 번 띄운 크로미움으로 여러 장을 찍는다."""

    def __init__(self, work: Path):
        from playwright.sync_api import sync_playwright
        self.work = work = Path(work).resolve()
        work.mkdir(parents=True, exist_ok=True)
        self._pw = sync_playwright().start()
        exe = "/opt/pw-browsers/chromium" if Path("/opt/pw-browsers/chromium").exists() else None
        self.br = self._pw.chromium.launch(**({"executable_path": exe} if exe else {}), args=["--no-sandbox"])
        self.pg = self.br.new_page(viewport={"width": 1080, "height": 1920})
        self.fonts = fonts_css()

    def close(self) -> None:
        self.br.close()
        self._pw.stop()

    # ── 찍기 ──
    def _load(self, html: str, name: str) -> None:
        f = self.work / f"_{name}.html"
        f.write_text(f"<!doctype html><html><head><meta charset=utf-8>{self.fonts}<style>{BASE}</style></head>{html}</html>",
                     encoding="utf-8")
        self.pg.goto(f.as_uri())
        self.pg.wait_for_timeout(300)
        self.pg.evaluate("document.fonts.ready")
        self.pg.wait_for_timeout(600)
        self.pg.evaluate(FIT_JS)
        self.pg.wait_for_timeout(100)

    def shot(self, html: str, name: str, transparent: bool = False) -> Path:
        self._load(html, name)
        png = self.work / f"{name}.png"
        self.pg.screenshot(path=str(png), omit_background=transparent)
        return png

    def animated(self, html: str, out: Path, sec: int, seed: int, fps: int = 30) -> Path:
        """CSS 움직임을 시간별로 멈춰 찍어서 영상으로 만든다."""
        self._load(html, out.stem)
        fr = self.work / f"_fr-{out.stem}"
        shutil.rmtree(fr, ignore_errors=True)
        fr.mkdir()
        self.pg.evaluate("document.getAnimations().forEach(a=>a.pause())")
        for k in range(sec * fps):
            self.pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={k * 1000 / fps})")
            self.pg.screenshot(path=str(fr / f"{k:04d}.jpg"), type="jpeg", quality=92)
        bgm = music.bgm(sec + 1, self.work / f"bgm-{out.stem}.wav", seed=seed)
        _ff("-framerate", str(fps), "-i", str(fr / "%04d.jpg"), "-i", str(bgm), "-t", str(sec), "-vf", "format=yuv420p",
            "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-shortest", str(out))
        shutil.rmtree(fr, ignore_errors=True)
        return out

    def still(self, png: Path, out: Path, sec: int, seed: int) -> Path:
        bgm = music.bgm(sec + 1, self.work / f"bgm-{out.stem}.wav", seed=seed)
        _ff("-loop", "1", "-i", str(png), "-i", str(bgm), "-t", str(sec), "-vf", "format=yuv420p", "-r", "30",
            "-c:v", "libx264", "-c:a", "aac", "-shortest", str(out))
        return out

    def slides(self, pngs: list[Path], durs: list[float], out: Path, seed: int) -> Path:
        lst = self.work / f"{out.stem}.txt"
        lst.write_text("".join(f"file '{p}'\nduration {d}\n" for p, d in zip(pngs, durs)) + f"file '{pngs[-1]}'\n")
        bgm = music.bgm(sum(durs) + 1, self.work / f"bgm-{out.stem}.wav", seed=seed)
        _ff("-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(bgm), "-vf", "fps=30,format=yuv420p",
            "-c:v", "libx264", "-c:a", "aac", "-shortest", str(out))
        return out

    def voiceover(self, video: Path, lines: list[str], seed: int = 1) -> Path:
        """대본(formula/script.py)을 타입캐스트로 읽어 영상에 입힌다 (사장님 2026-11-01).
        목소리가 영상보다 길면 마지막 장면을 그대로 두고 늘린다. 배경음악은 목소리 밑으로 작게 깐다."""
        from ..video import voice
        parts = []
        for i, line in enumerate(lines):
            w = self.work / f"vo-{video.stem}-{i:02d}.wav"
            voice.speak(line, w, prev=lines[i - 1] if i else "", nxt=lines[i + 1] if i + 1 < len(lines) else "")
            parts.append(w)
        narr = self.work / f"vo-{video.stem}.wav"
        ins = sum((["-i", str(w)] for w in parts), [])
        gaps = "".join(f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,apad=pad_dur=0.25[a{i}];" for i in range(len(parts)))
        _ff(*ins, "-filter_complex", gaps + "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[o]",
            "-map", "[o]", str(narr))
        nd = _dur(narr)
        fit = _dur(video) - 1.0          # 영상은 7초 (사장님 2026-11-01). 대사가 길면 조금 빠르게 읽혀 7초 안에 넣는다
        if nd > fit:
            fast = narr.with_name(narr.stem + "-빠르게.wav")
            _ff("-i", str(narr), "-filter:a", f"atempo={min(nd / fit, 1.25):.3f}", str(fast))
            narr, nd = fast, _dur(fast)
        total = max(_dur(video), nd + 0.8)
        bgm = music.bgm(total + 1, self.work / f"bgm-vo-{video.stem}.wav", seed=seed)
        tmp = video.with_name(video.stem + "-목소리.mp4")
        _ff("-i", str(video), "-i", str(narr), "-i", str(bgm), "-filter_complex",
            f"[0:v]tpad=stop_mode=clone:stop_duration={total:.2f}[v];[1:a]adelay=300|300,volume=1.0[n];"
            "[2:a]volume=0.16[b];[n][b]amix=inputs=2:duration=longest:normalize=0[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "20", "-c:a", "aac", str(tmp))
        tmp.replace(video)
        return video

    # ── 아침 ──
    def morning(self, m: Morning, out: Path, seed: int = 1, cta: str = "") -> Path:
        """영상은 모두 7초 (사장님 2026-11-01, 레퍼런스 5~9초). cta = 화면 밑에 넣는 글 (가림식만, formula/script.py)."""
        if m.fmt == "hidden":
            return self.hidden(m, out, seed, cta)
        return {"tier": self.tier, "sinbi": self.sinbi, "forceteller": self.forceteller,
                "solo": self.solo}[m.fmt](m, out, seed)

    def tier(self, m: Morning, out: Path, seed: int) -> Path:
        """천복식 (456만회 레퍼런스): 황금 빛 배경 + 도는 고리 + 육각 빛망울, 남색·빨강 명조 3줄 제목, 1~12위 출생연도."""
        bokeh = "".join(
            f"<b class=hex style='left:{x}px;top:{y}px;width:{w}px;height:{w * .87:.0f}px;opacity:{o};animation-delay:-{d}s'></b>"
            for x, y, w, o, d in [(40, 1560, 150, .7, 0), (230, 1650, 110, .5, 2), (700, 1590, 170, .65, 4), (900, 1700, 120, .5, 1),
                                  (480, 1720, 90, .45, 3), (60, 260, 90, .35, 5), (930, 380, 110, .35, 2), (820, 1450, 80, .4, 6),
                                  (140, 1380, 70, .35, 1)])
        rings = "".join(f"<div class='rg {c}' style='width:{s}px;height:{s}px;{st}'></div>" for c, s, st in [
            ("spin", 1500, "border:2px solid rgba(255,248,220,.35)"), ("spin", 1360, "border:14px dashed rgba(255,248,220,.18)"),
            ("spin2", 1180, "border:3px solid rgba(255,248,220,.30)"), ("spin2", 1080, "border:28px dotted rgba(255,248,220,.14)"),
            ("spin", 860, "border:2px solid rgba(255,248,220,.35);box-shadow:0 0 120px rgba(255,250,230,.45) inset"),
            ("spin2", 640, "border:10px dashed rgba(255,248,220,.16)"),
            ("", 420, "background:radial-gradient(circle,rgba(255,255,245,.6),transparent 70%)")])
        li = "".join(
            f"<div class='s r{' t' if r.rank <= 3 else ''}'><span class=n>{r.rank}위</span><span class=d>{ddi(r.ddi) if len(r.ddi) < 3 else r.ddi}</span>"
            f"<span class=y>: {years_short(r.ddi)}년생</span></div>" for r in m.rows)
        t1, t2, t3 = m.title
        html = f"""<style>
        body{{background:radial-gradient(circle at 50% 50%,#fff6d6 0%,#f6dc93 22%,#e2b553 48%,#b9842a 74%,#7a5414 100%);font-family:'Nanum Myeongjo';position:relative}}
        .rg{{position:absolute;left:50%;top:50%;border-radius:50%;transform:translate(-50%,-50%)}}
        .spin{{animation:spin 40s linear infinite}} .spin2{{animation:spin2 60s linear infinite}}
        @keyframes spin{{to{{transform:translate(-50%,-50%) rotate(360deg)}}}} @keyframes spin2{{to{{transform:translate(-50%,-50%) rotate(-360deg)}}}}
        .hex{{position:absolute;clip-path:polygon(25% 5%,75% 5%,100% 50%,75% 95%,25% 95%,0 50%);background:radial-gradient(circle,rgba(255,250,225,.55),rgba(255,240,190,.12) 70%);animation:float 7s ease-in-out infinite alternate}}
        @keyframes float{{from{{transform:translateY(30px)}}to{{transform:translateY(-40px)}}}}
        .vig{{position:absolute;inset:0;background:radial-gradient(circle at 50% 48%,transparent 55%,rgba(70,40,0,.35) 100%)}}
        .h{{position:absolute;top:110px;width:100%;text-align:center;font-weight:800;line-height:1.22}}
        .s{{-webkit-text-stroke:.8px currentColor;paint-order:stroke fill;filter:drop-shadow(0 0 10px rgba(255,250,230,.7))}}
        .h1{{font-size:84px;color:#d10000}} .h2{{font-size:100px;color:#0a1640}} .h3{{font-size:96px;color:#d10000}}
        .h>div{{white-space:nowrap}}
        .list{{position:absolute;top:580px;left:60px}}
        .r{{font-weight:800;font-size:60px;line-height:1;margin:0 0 24px;white-space:nowrap}}
        .n{{display:inline-block;width:136px;color:#0a1640}} .d{{display:inline-block;width:186px;color:#d10000}} .y{{color:#0a1640}}
        .t .y,.t .n{{color:#d10000}}
        .f{{position:absolute;bottom:70px;width:100%;text-align:center;font-family:'Noto Sans KR';font-weight:700;font-size:30px;color:#5a3a08}}
        </style><body>{rings}{bokeh}<div class=vig></div>
        <div class=h><div class='h1 s fit' data-w=1020>{t1}</div><div class='h2 s fit' data-w=1020>{t2}</div><div class='h3 s fit' data-w=1020>{t3}</div></div>
        <div class=list>{li}</div>
        <div class=f>운명서재 · 사주 엔진 계산 · {m.period.long} {m.period.ganzhi} 기준</div>
        <script>document.fonts.ready.then(()=>{{const L=document.querySelector('.list');L.style.left='0';L.style.width='max-content';
          const rs=[...document.querySelectorAll('.r')];let fs=parseFloat(getComputedStyle(rs[0]).fontSize);
          for(let k=0;k<4;k++){{const w=L.getBoundingClientRect().width;fs*=960/w;rs.forEach(r=>r.style.fontSize=fs+'px');
            document.querySelectorAll('.n').forEach(e=>e.style.width=(fs*2.35)+'px');document.querySelectorAll('.d').forEach(e=>e.style.width=(fs*3.2)+'px');}}
          L.style.left=((1080-L.getBoundingClientRect().width)/2)+'px';}})</script></body>"""
        return self.animated(html, out, 7, seed)

    def hidden(self, m: Morning, out: Path, seed: int, cta: str = "") -> Path:
        """가림식 (90만회 레퍼런스): 은하수 사진이 천천히 다가오고, 12위→4위 공개, 1~3위는 ???? 로 가림."""
        sky = _data_uri(media(B["milky"]), "image/jpeg")
        stars = "".join(f"<i style='left:{(i * 211) % 1080}px;top:{(i * 97) % 1250}px;width:{2 + i % 3}px;height:{2 + i % 3}px;opacity:{.3 + (i % 6) / 9:.2f}'></i>"
                        for i in range(60))
        med = {1: "🥇", 2: "🥈", 3: "🥉"}
        ph = m.data["phrase"]
        li = ""
        for r in sorted(m.rows, key=lambda x: -x.rank):
            if r.rank > 3:
                li += f"<div class=r><span class=n>{r.rank}위</span> <span class=e>{EMO[r.ddi]}</span> <span class=d>{ddi(r.ddi)}</span><span class=p>👉{ph[r.ddi]}</span></div>"
            else:
                li += f"<div class=r><span class=n>{med[r.rank]}</span> <span class=d>????</span><span class=p>👉{ph[r.ddi]}</span></div>"
        a, b = [x.replace("{p}", m.period.label) for x in B["kinds"][m.kind]["hidden"]]
        html = f"""<style>
        body{{background:#070b1c;font-family:'Do Hyeon';position:relative}}
        .bg{{position:absolute;inset:-40px;background:url('{sky}') center 30%/cover;filter:brightness(1.35) contrast(1.1) saturate(1.2);animation:zoom 6s linear infinite}}
        @keyframes zoom{{from{{transform:scale(1)}}to{{transform:scale(1.08)}}}}
        .tint{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(25,45,130,.45) 0%,rgba(40,60,140,.30) 50%,rgba(5,8,25,.55) 100%)}}
        i{{position:absolute;border-radius:50%;background:#fff;box-shadow:0 0 8px #fff;animation:tw 1.8s ease-in-out infinite alternate}}
        @keyframes tw{{from{{opacity:.15}}to{{opacity:1}}}}
        .tag{{position:absolute;top:150px;left:50%;transform:translateX(-50%);background:#ff8a1f;color:#fff;font-size:56px;padding:6px 40px;border-radius:6px}}
        .h{{position:absolute;top:250px;width:100%;text-align:center;font-size:108px;line-height:1.08;color:#ffc93c;text-shadow:0 6px 0 #6b3b00,0 0 24px rgba(0,0,0,.5)}}
        .h div{{white-space:nowrap}} .h b{{color:#ff9a2e;font-weight:400}}
        .list{{position:absolute;top:560px;left:44px}}
        .r{{font-size:54px;line-height:1;margin-bottom:30px;white-space:nowrap;color:#fff;text-shadow:0 3px 0 #000}}
        .n{{color:#ffc93c;display:inline-block;margin-right:16px}} .e{{font-family:'Noto Color Emoji';font-size:.8em;margin-right:6px}} .d{{color:#ff9a2e}} .p{{color:#fff;margin-left:6px}}
        .cta{{position:absolute;bottom:150px;width:100%;text-align:center;white-space:nowrap;font-family:Jua;font-size:76px;line-height:1.2;color:#e6a3ff;text-shadow:0 5px 0 #3a0d55}}
        </style><body><div class=bg></div><div class=tint></div>{stars}<div class=tag>과연 1위는?</div>
        <div class=h><div class=fit data-w=1020>{a}</div><div class=fit data-w=1020><b>{b}</b> 띠 순위</div></div>
        <div class='list fitbox' data-w=1000>{li}</div>
        <div class=cta>{_cta_html(cta or "1위가 궁금하면 댓글에 내 띠 남기기♥")}</div></body>"""
        return self.animated(html, out, 7, seed)

    def sinbi(self, m: Morning, out: Path, seed: int) -> Path:
        """신비사주식: 흰 표, 날짜 제목 + 계정, 12띠 그림 + 두 줄 글."""
        import datetime as dt
        d = dt.date.fromisoformat(m.data["date"])
        txt = m.data["text"]
        Z = ASSETS / "zodiac"
        cell = lambda a: (f"<div class=c><div class=l><b>{ddi(a)}</b><img src='{(Z / (a + '.png')).as_uri()}'></div><p>{txt[a]}</p></div>")
        rows = "".join(f"<div class=row>{cell(ORDER[i])}{cell(ORDER[i + 6])}</div>" for i in range(6))
        html = f"""<style>body{{background:#000;font-family:'Noto Sans KR'}}
        .sheet{{position:absolute;top:50%;transform:translateY(-50%);left:0;right:0;background:#fff;padding:0 0 30px}}
        .hd{{display:flex;align-items:center;justify-content:center;height:150px;border-bottom:3px solid #ddd;position:relative}}
        .hd h1{{margin:0;font-weight:700;font-size:56px;color:#111}} .hd i{{position:absolute;right:22px;bottom:18px;font-style:normal;font-size:24px;color:#333;font-weight:500}}
        .row{{display:flex;border-bottom:2px solid #e6e3ef}} .c{{background:linear-gradient(90deg,#fff 0%,#fbfaff 55%,#eeeaf8 100%)}}
        .c{{flex:1;display:flex;gap:14px;padding:16px 18px 18px;min-height:212px;align-items:center}} .c:first-child{{border-right:2px solid #e3e3e3}}
        .l{{width:168px;flex:none}} .l b{{display:block;color:#222;font-weight:500;font-size:32px;margin-bottom:6px}} .l img{{width:150px;height:140px;object-fit:contain;filter:drop-shadow(0 4px 6px rgba(0,0,0,.15))}}
        .c p{{margin:30px 0 0;font-size:31px;line-height:1.5;color:#222;font-weight:400;word-break:keep-all}}
        </style><body><div class=sheet><div class=hd><h1>{d.month}월 {d.day}일 띠별 운세</h1><i>@unmyeong_saju.kr</i></div>{rows}</div></body>"""
        return self.still(self.shot(html, out.stem), out, 7, seed)

    def forceteller(self, m: Morning, out: Path, seed: int) -> Path:
        """포스텔러식: 위 검은 띠 큰 2줄 제목 + 아래 수채화 오행 그림, 아래 설명이 바뀐다."""
        D = m.data
        on = {D["el"]} | ({D["pair"]} if D["tpl"] == "pair" else set())
        pos = {"목": (545, 260, "#4fa98a", "나무"), "화": (865, 490, "#d95a6c", "불"), "토": (750, 860, "#d9a32a", "땅"),
               "금": (340, 860, "#bdb7c4", "쇠"), "수": (225, 490, "#3d8fc8", "물")}
        H = {e: B["elements"][e]["hanja"] for e in ELEMENTS}
        R, cx, cy = 92, 545, 600
        circles = "".join(f"<div class='o{' on' if k in on else ''}' style='left:{x - R}px;top:{y - R}px;background:{c};--c:{c}'>{H[k]}<span>{t}</span></div>"
                          for k, (x, y, c, t) in pos.items())

        def seg(a, b, pad=R + 16):
            (x1, y1, *_), (x2, y2, *_) = pos[a], pos[b]
            d = math.hypot(x2 - x1, y2 - y1)
            ux, uy = (x2 - x1) / d, (y2 - y1) / d
            return x1 + ux * pad, y1 + uy * pad, x2 - ux * pad, y2 - uy * pad
        outer = ""
        for a_, b_ in [("목", "화"), ("화", "토"), ("토", "금"), ("금", "수"), ("수", "목")]:
            x1, y1, x2, y2 = seg(a_, b_, R + 22)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            k = 1 + 70 / math.hypot(mx - cx, my - cy)
            outer += f"<path d='M{x1:.0f} {y1:.0f} Q{cx + (mx - cx) * k:.0f} {cy + (my - cy) * k:.0f} {x2:.0f} {y2:.0f}' stroke='#c9c6c2' stroke-width='5' fill='none' marker-end='url(#ag)'/>"
        inner = ""
        for a_, b_ in [("목", "토"), ("화", "금"), ("토", "수"), ("금", "목"), ("수", "화")]:
            x1, y1, x2, y2 = seg(a_, b_)
            inner += f"<path d='M{x1:.0f} {y1:.0f} L{x2:.0f} {y2:.0f}' stroke='{pos[a_][2]}' stroke-opacity='.75' stroke-width='4' stroke-dasharray='14 10' fill='none' marker-end='url(#a{ELEMENTS.index(a_)})'/>"
        marks = ("<marker id='ag' viewBox='0 0 10 10' refX='6' refY='5' markerWidth='5' markerHeight='5' orient='auto'><path d='M0 0L10 5L0 10z' fill='#c9c6c2'/></marker>"
                 + "".join(f"<marker id='a{i}' viewBox='0 0 10 10' refX='6' refY='5' markerWidth='5' markerHeight='5' orient='auto'><path d='M0 0L10 5L0 10z' fill='{pos[e][2]}'/></marker>"
                           for i, e in enumerate(ELEMENTS)))
        wc = """<svg width=1080 height=1320 style='position:absolute;left:0;top:0;z-index:0'><defs><filter id=wc x='-20%' y='-20%' width='140%' height='140%'>
          <feTurbulence type='fractalNoise' baseFrequency='.012' numOctaves='4' seed='7'/><feDisplacementMap in='SourceGraphic' scale='120'/><feGaussianBlur stdDeviation='2'/></filter>
          <filter id=grain><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/><feColorMatrix values='0 0 0 0 .5 0 0 0 0 .5 0 0 0 0 .5 0 0 0 .08 0'/></filter></defs>
          <g filter='url(#wc)'><ellipse cx='820' cy='70' rx='420' ry='260' fill='#9fcbc0' opacity='.55'/><ellipse cx='900' cy='120' rx='260' ry='150' fill='#7fb8ab' opacity='.35'/>
          <ellipse cx='1080' cy='640' rx='170' ry='330' fill='#eab3ab' opacity='.55'/><ellipse cx='130' cy='1180' rx='380' ry='190' fill='#e9b9a6' opacity='.45'/>
          <ellipse cx='-40' cy='860' rx='200' ry='260' fill='#a9bfd9' opacity='.45'/></g>
          <g fill='#7f8fa3' opacity='.75'><path d='M40 700l40-12 28 18-10 22-44 4z'/><path d='M110 760l34-6 18 20-22 16-30-8z'/><path d='M60 820l46-4 12 22-34 14-26-10z'/>
          <path d='M140 860l30 2 10 18-26 10-18-12z'/><path d='M20 900l38 0 8 20-30 10-20-14z'/><path d='M170 940l26-4 12 16-22 12-16-10z'/></g>
          <rect width=1080 height=1320 filter='url(#grain)'/></svg>"""
        h1, h2 = D["head"]
        pngs = []
        for i, t in enumerate(D["say"][:2]):   # 7초엔 두 장까지만 읽힌다. 나머지 풀이는 설명란 (사장님 2026-11-01 7초)
            html = f"""<style>body{{background:#000;font-family:'Noto Sans KR'}}
            .t{{height:600px;display:flex;flex-direction:column;justify-content:flex-end;padding-bottom:70px;text-align:center;font-weight:900;font-size:104px;line-height:1.22;color:#fff;letter-spacing:-3px}}
            .t div{{white-space:nowrap}} .t em{{font-style:normal;color:#ffd23f}}
            .art{{position:absolute;top:600px;left:0;right:0;bottom:0;background:#f7f4ef;overflow:hidden}}
            .o{{position:absolute;width:{2 * R}px;height:{2 * R}px;border-radius:50%;z-index:3;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;font-family:'Nanum Myeongjo';font-weight:800;font-size:76px;line-height:1;box-shadow:0 6px 14px rgba(0,0,0,.08)}}
            .o span{{font-family:'Noto Sans KR';font-size:24px;font-weight:500;margin-top:6px}}
            .o.on{{box-shadow:0 0 0 16px color-mix(in srgb,var(--c) 25%,transparent),0 0 50px var(--c)}}
            svg.ar{{position:absolute;left:0;top:0;z-index:2}}
            .say{{position:absolute;left:70px;right:70px;bottom:110px;z-index:4;background:#fff;border-radius:30px;padding:40px 30px;font-size:56px;font-weight:700;line-height:1.38;text-align:center;white-space:pre-line;color:#1b1b1b;box-shadow:0 10px 30px rgba(0,0,0,.12);word-break:keep-all}}
            </style><body><div class=t><div class=fit data-w=1020>{h1}</div><div class=fit data-w=1020>{h2}</div></div>
            <div class=art>{wc}<svg class=ar width=1080 height=1320><defs>{marks}</defs>{outer}{inner}</svg>
            {circles}<div class=say>{t}</div></div></body>"""
            pngs.append(self.shot(html, f"{out.stem}-{i}"))
        durs = [7 / len(pngs)] * len(pngs)   # 영상은 7초 (사장님 2026-11-01)
        return self.slides(pngs, durs, out, seed)

    def overlay(self, html: str, name: str, sec: float, fps: int = 30) -> Path:
        """CSS 움직임을 투명 배경 사진 여러 장으로 찍는다 (풍경 영상 위에 얹는다)."""
        self._load(html, name)
        fr = self.work / f"_ov-{name}"
        shutil.rmtree(fr, ignore_errors=True)
        fr.mkdir()
        self.pg.evaluate("document.getAnimations().forEach(a=>a.pause())")
        for k in range(int(sec * fps)):
            self.pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={k * 1000 / fps})")
            self.pg.screenshot(path=str(fr / f"{k:04d}.png"), omit_background=True)
        return fr

    def solo(self, m: Morning, out: Path, seed: int) -> Path:
        """솔로사주식: 예쁜 풍경 영상 + 검은 상자 2줄 제목(흰 줄 + 빨간 줄).
        사장님 2026-11-01: 제목이 화면 한가운데 먼저 나오고 → 위로 올라간 뒤 → 1·2·3위가 하나씩 나온다.
        순위마다 밑에 자극적인 한 줄 두 개 (banks.json solo_hype, 엔진 순위 종류와 같은 방향)."""
        l1, l2 = m.data["lines"]
        hype = B["solo_hype"][m.kind]
        top3 = "".join(
            f"<div class='k' style='animation-delay:{2.3 + i * 1.1:.1f}s'><div class=h><b>{r.rank}위</b> {EMO[r.ddi]} {ddi(r.ddi)} <i>{years_short(r.ddi)}년생</i></div>"
            f"<div class=s>{hype[i][0]}<br>{hype[i][1]}</div></div>" for i, r in enumerate(m.rows[:3]))
        html = f"""<style>body{{background:transparent;font-family:'Noto Sans KR'}}
        .w{{position:absolute;left:0;right:0;top:960px;display:flex;flex-direction:column;align-items:center;transform:translateY(-50%);animation:up .7s ease-in-out 1.5s both}}
        @keyframes up{{to{{top:150px;transform:translateY(0)}}}}
        .l,.r{{background:#000;font-weight:900;font-size:96px;line-height:1.18;letter-spacing:-3px;white-space:nowrap}}
        .l{{color:#fff;padding:10px 34px 14px;border-radius:18px 18px 0 0}}
        .r{{color:#ff1f1f;padding:0 34px 16px;border-radius:0 0 18px 18px}}
        .list{{position:absolute;top:520px;left:50px;right:50px}}
        .k{{background:rgba(0,0,0,.74);border-radius:24px;padding:22px 30px 24px;margin-bottom:30px;opacity:0;animation:pop .45s ease-out both}}
        @keyframes pop{{from{{opacity:0;transform:translateY(40px)}}to{{opacity:1;transform:none}}}}
        .h{{color:#fff;font-weight:900;font-size:68px;line-height:1.1;white-space:nowrap;letter-spacing:-2px}}
        .h b{{color:#ffd23f}} .h i{{font-style:normal;font-size:44px;color:#eee;font-weight:700}}
        .s{{color:#ffe9a8;font-weight:800;font-size:50px;line-height:1.3;margin-top:12px;letter-spacing:-1.5px;word-break:keep-all}}
        </style><body><div class=w><div class='l fit' data-w=1000>{l1}</div><div class='r fit' data-w=1000>{l2}</div></div>
        <div class=list>{top3}</div></body>"""
        fr = self.overlay(html, f"{out.stem}-제목", 7)
        clip = media(m.data["bg"])
        bgm = music.bgm(8, self.work / f"bgm-{out.stem}.wav", seed=seed)
        _ff("-stream_loop", "-1", "-i", str(clip), "-framerate", "30", "-i", str(fr / "%04d.png"), "-i", str(bgm), "-filter_complex",
            "[0]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30[bg];[bg][1]overlay=0:0:eof_action=repeat,format=yuv420p[v]",
            "-map", "[v]", "-map", "2", "-t", "7", "-c:v", "libx264", "-c:a", "aac", str(out))
        shutil.rmtree(fr, ignore_errors=True)
        return out

    # ── 저녁: 스레드 글 캡처 ──
    def threads(self, e: Evening, out: Path, seed: int = 70) -> Path:
        pic = _data_uri(ASSETS / "profile.jpg", "image/jpeg")
        dark = e.dark
        bg, fg, sub = ("#101010", "#f3f3f3", "#8a8a8a") if dark else ("#fff", "#111", "#999")
        pngs = []
        for i, lines in enumerate(e.shown, 1):
            body = "".join(f"<p>{_esc(x)}</p>" if x else "<div class=gap></div>" for ln in lines for x in ln.split("\n"))
            html = f"""<style>body{{background:{'#101010' if dark else '#000'};font-family:'Noto Sans KR'}}
            .w{{position:absolute;left:{40 if dark else 18}px;right:{30 if dark else 18}px;top:50%;transform:translateY(-50%);background:{bg};color:{fg};border-radius:8px;padding:{'0' if dark else '50px 40px 40px'}}}
            .top{{display:flex;align-items:center;gap:24px;margin-bottom:40px}} .top img{{width:118px;height:118px;border-radius:50%;object-fit:cover}}
            .nm{{font-size:44px;font-weight:700}} .dt{{font-size:34px;color:{sub};font-weight:400;margin-left:14px}}
            p{{margin:0 0 14px;font-size:{50 if dark else 43}px;line-height:1.42;font-weight:500;word-break:keep-all;letter-spacing:-1px}} .gap{{height:34px}}
            .pg{{text-align:right;font-size:32px;color:{sub};margin-top:20px}}</style>
            <body><div class='w fitv'><div class=top><img src="{pic}"><div class=nm>unmyeong_saju.kr<span class=dt>2시간</span></div></div>{body}{f'<div class=pg>{i} / {len(e.pages)}</div>' if len(e.pages) > 1 else ''}</div></body>"""
            pngs.append(self.shot(html, f"{out.stem}-{i}"))
        return self.slides(pngs, [5.5] + [4.5] * (len(pngs) - 1), out, seed)

    # ── 인스타 게시글: 스레드 글 캡처 사진 (사장님 2026-11-01 "스레드 글은 릴스 말고 게시글로") ──
    def thread_cards(self, e: Evening, folder: Path, stem: str) -> list[Path]:
        """스레드 글 한 장을 사진 한 장으로 찍는다. 인스타 여러 장 게시글은 4:5(1080×1350)까지라 그 크기로 찍는다."""
        pic = _data_uri(ASSETS / "profile.jpg", "image/jpeg")
        folder.mkdir(parents=True, exist_ok=True)
        self.pg.set_viewport_size({"width": 1080, "height": 1350})
        out = []
        try:
            for i, lines in enumerate(e.shown[:10], 1):
                body = "".join(f"<p>{_esc(x)}</p>" if x else "<div class=gap></div>" for ln in lines for x in ln.split("\n"))
                html = f"""<style>body{{background:#fff;font-family:'Noto Sans KR'}}
                .w{{position:absolute;left:70px;right:70px;top:50%;transform:translateY(-50%);color:#111}}
                .top{{display:flex;align-items:center;gap:22px;margin-bottom:36px}} .top img{{width:96px;height:96px;border-radius:50%;object-fit:cover}}
                .nm{{font-size:38px;font-weight:700}}
                p{{margin:0 0 12px;font-size:40px;line-height:1.45;font-weight:500;word-break:keep-all;letter-spacing:-1px}} .gap{{height:28px}}
                .pg{{text-align:right;font-size:30px;color:#999;margin-top:18px}}</style>
                <body><div class='w fitv'><div class=top><img src="{pic}"><div class=nm>unmyeong_saju.kr</div></div>{body}{f'<div class=pg>{i} / {min(len(e.pages), 10)}</div>' if len(e.pages) > 1 else ''}</div></body>"""
                png = self.shot(html, f"{stem}-카드{i}")
                jpg = folder / f"{stem}_{i}.jpg"
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(png), "-q:v", "3", str(jpg)], check=True)
                out.append(jpg)
        finally:
            self.pg.set_viewport_size({"width": 1080, "height": 1920})
        return out


def _dur(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _cta_html(t: str) -> str:
    """밑에 글을 두 줄로: '…싶다면' 뒤에서 끊는다."""
    for cut in ("싶다면 ", "궁금하면 "):
        a, sep, b = t.partition(cut)
        if sep:
            return f"<div class=fit data-w=1000>{a}{sep.strip()}</div><div class=fit data-w=1000>{b}</div>"
    return f"<div class=fit data-w=1000>{t}</div>"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# 글이 길어 넘치면 글씨를 줄인다 (가로: .fit, 목록 전체: .fitbox, 세로로 긴 스레드 장: .fitv)
FIT_JS = """(()=>{
 const cw=e=>{const r=document.createRange();r.selectNodeContents(e);return r.getBoundingClientRect().width+parseFloat(getComputedStyle(e).paddingLeft)+parseFloat(getComputedStyle(e).paddingRight);};
 document.querySelectorAll('.fit').forEach(e=>{const W=+e.dataset.w||1000;let fs=parseFloat(getComputedStyle(e).fontSize);
   for(let k=0;k<30&&cw(e)>W;k++){fs*=0.96;e.style.fontSize=fs+'px';}});
 document.querySelectorAll('.fitbox').forEach(L=>{const W=+L.dataset.w||1000;L.style.width='max-content';
   const rs=[...L.children];let fs=parseFloat(getComputedStyle(rs[0]).fontSize);
   for(let k=0;k<30&&L.getBoundingClientRect().width>W;k++){fs*=0.96;rs.forEach(r=>r.style.fontSize=fs+'px');}});
 document.querySelectorAll('.fitv').forEach(w=>{let s=1;for(let k=0;k<40&&w.getBoundingClientRect().height>innerHeight*0.9375;k++){s*=0.96;
   w.querySelectorAll('p').forEach(p=>{p.style.fontSize=(parseFloat(getComputedStyle(p).fontSize)*0.96)+'px'});}});
})()"""
