"""카드뉴스 이미지(인스타 4:5)와 쇼츠 세로 영상(9:16)을 만든다.

HTML → PDF(weasyprint) → PNG(pdftoppm) → MP4(ffmpeg). 모두 무료 도구이고 API를 쓰지 않는다.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

from .content import BRAND, SITE_URL, Post

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "saju" / "report" / "fonts"
ART = ROOT / "site" / "public" / "assets" / "geumwol"
COVER_IMG = {"ddi": "newyear-cover.jpg", "summary": "newyear-cover.jpg", "topic": "master.jpg"}

SIZES = {"feed": (1080, 1350), "shorts": (1080, 1920)}

CSS = """
@font-face { font-family: "Gowun Batang"; src: url("FONTS/GowunBatang-Regular.ttf"); font-weight: 400; }
@font-face { font-family: "Gowun Batang"; src: url("FONTS/GowunBatang-Bold.ttf"); font-weight: 700; }
@font-face { font-family: "Song Myung"; src: url("FONTS/SongMyung-Regular.ttf"); }
@page { size: Wpx Hpx; margin: 0; }
html { font-family: "Gowun Batang", serif; color: #1f1b16; }
body { margin: 0; }
.w { white-space: nowrap; }
.txt.md { font-size: MDpx; }
.txt.sm { font-size: SMpx; }
.pg { width: Wpx; height: Hpx; position: relative; overflow: hidden; break-after: page; background: #f1e9d6; }
.frame { position: absolute; left: 36px; top: 36px; right: 36px; bottom: 36px; border: 6px double #3a2e22; }
.cover { background-size: cover; background-position: center top; }
.shade { position: absolute; left: 0; right: 0; bottom: 0; height: 58%;
         background: linear-gradient(to bottom, rgba(20,10,8,0), rgba(20,10,8,0.82) 38%, rgba(20,10,8,0.92)); }
.cv { position: absolute; left: 72px; right: 72px; bottom: CVBpx; color: #fff; }
.label { font-size: 36px; color: #e8cf8f; letter-spacing: 2px; margin-bottom: 18px; }
.hook { font-family: "Song Myung", serif; font-size: 104px; line-height: 1.15; margin: 0 0 26px; }
.hook.long { font-size: 80px; }
.sub { font-size: 44px; line-height: 1.55; font-weight: 700; word-break: keep-all; }
.years { font-size: 36px; color: #e8cf8f; margin-top: 22px; }
.top { position: absolute; left: 84px; right: 84px; top: 78px; font-size: 32px; color: #6b5a44;
       border-bottom: 2px solid #b9a77f; padding-bottom: 14px; }
.top .no { float: right; color: #9e2f22; }
.body { position: absolute; left: 84px; right: 84px; top: BTpx; }
h2 { font-family: "Song Myung", serif; font-weight: 400; font-size: HEADpx; line-height: 1.3; color: #9e2f22;
     border-left: 12px solid #9e2f22; padding-left: 26px; margin: 0 0 44px; word-break: keep-all; }
.txt { font-size: TXTpx; line-height: 1.7; word-break: keep-all; white-space: pre-line; }
.foot { position: absolute; left: 84px; right: 84px; bottom: 74px; font-size: 30px; color: #6b5a44; }
.seal { position: absolute; right: 84px; bottom: 64px; width: 96px; height: 96px; background: #9e2f22; color: #f6e6c8;
        font-family: "Song Myung", serif; font-size: 38px; line-height: 44px; text-align: center; padding-top: 4px; }
.cover .seal { bottom: auto; top: 64px; }
.remember { border: 4px solid #9e2f22; padding: 40px 44px; font-family: "Song Myung", serif; font-size: 60px;
            line-height: 1.45; color: #1f1b16; background: #f8f1e1; word-break: keep-all; margin-bottom: 56px; }
.rlabel { font-size: 36px; color: #9e2f22; margin-bottom: 18px; }
.cta { font-size: 44px; line-height: 1.65; word-break: keep-all; }
.site { margin-top: 30px; font-size: 46px; font-weight: 700; color: #9e2f22; }
"""


def _css(fmt: str) -> str:
    w, h = SIZES[fmt]
    tall = fmt == "shorts"
    return (CSS.replace("FONTS", FONTS.as_uri()).replace("Wpx", f"{w}px").replace("Hpx", f"{h}px")
            .replace("CVBpx", "300px" if tall else "130px").replace("BTpx", "470px" if tall else "230px")
            .replace("HEADpx", "66px" if tall else "62px").replace("TXTpx", "58px" if tall else "52px")
            .replace("MDpx", "52px" if tall else "47px").replace("SMpx", "48px" if tall else "43px"))


def _t(text: str) -> str:
    """weasyprint는 keep-all을 지키지 않아 낱말 중간에서 줄을 바꾼다. 낱말마다 묶어서 띄어쓰기에서만 바뀌게 한다."""
    lines = []
    for line in text.split("\n"):
        lines.append(" ".join(f'<span class="w">{escape(w)}</span>' for w in line.split(" ") if w))
    return "<br>".join(lines)


def _size(body: str) -> str:
    return "sm" if len(body) > 150 else "md" if len(body) > 110 else ""


FONT_PX = {"feed": {"": 52, "md": 47, "sm": 43, "head": 62}, "shorts": {"": 58, "md": 52, "sm": 48, "head": 66}}
BAND = {"feed": (190, 1230), "shorts": (230, 1760)}   # 본문이 들어갈 세로 범위


def _lines(text: str, px: int, width: int = 912) -> int:
    per = max(1, int(width / (px * 0.98)))
    return sum(max(1, -(-len(line) // per)) for line in text.split("\n"))


def _top(head: str, body: str, fmt: str) -> int:
    """본문 덩어리를 위아래 가운데에 놓는다. 글이 짧은 장에 아래쪽이 텅 비지 않게."""
    f = FONT_PX[fmt]
    px = f[_size(body)]
    h = _lines(head, f["head"]) * f["head"] * 1.3 + 44 + _lines(body, px) * px * 1.7
    y0, y1 = BAND[fmt]
    return int(max(y0, (y0 + y1 - h) / 2 - 40))


def _seal() -> str:
    return f'<div class="seal">{BRAND[:2]}<br>{BRAND[2:]}</div>'


def slides_html(p: Post, fmt: str) -> str:
    total = len(p.slides) + 2
    cover_img = (ART / COVER_IMG[p.kind]).as_uri()
    hook_cls = "hook long" if len(p.hook) > 11 else "hook"
    years = ""
    if p.kind == "ddi":
        years = f'<div class="years">{"·".join(f"{y % 100:02d}" for y in p.facts["years"])}년생</div>'
    pages = [f'''<div class="pg cover" style="background-image:url('{cover_img}')">
  <div class="shade"></div>{_seal()}
  <div class="cv"><div class="label">2027 정미년 · 丁未年</div><div class="{hook_cls}">{_t(p.hook)}</div>
  <div class="sub">{_t(p.sub)}</div>{years}</div></div>''']
    for n, s in enumerate(p.slides, 2):
        pages.append(f'''<div class="pg"><div class="frame"></div>
  <div class="top">{escape(p.hook)}<span class="no">{n} / {total}</span></div>
  <div class="body" style="top:{_top(s["head"], s["body"], fmt)}px"><h2>{_t(s["head"])}</h2><div class="txt {_size(s["body"])}">{_t(s["body"])}</div></div>
  <div class="foot">{BRAND} · {SITE_URL.removeprefix("https://")}</div>{_seal()}</div>''')
    pages.append(f'''<div class="pg"><div class="frame"></div>
  <div class="top">{escape(p.hook)}<span class="no">{total} / {total}</span></div>
  <div class="body"><div class="rlabel">기억할 한 줄</div><div class="remember">{_t(p.remember)}</div>
  <div class="cta">{_t("띠는 태어난 해 하나만 본 것이에요.")}<br>{_t("내 생년월일로 2027년 12달 흐름을 확인하세요.")}</div>
  <div class="site">{SITE_URL.removeprefix("https://")}</div></div>{_seal()}</div>''')
    return f"<!doctype html><html lang='ko'><head><meta charset='utf-8'><style>{_css(fmt)}</style></head><body>{''.join(pages)}</body></html>"


def render_pngs(p: Post, fmt: str, out_dir: Path, prefix: str) -> list[Path]:
    from weasyprint import HTML

    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "c.pdf"
        HTML(string=slides_html(p, fmt)).write_pdf(str(pdf))
        subprocess.run(["pdftoppm", "-r", "96", "-png", str(pdf), str(Path(tmp) / "s")], check=True)
        files = sorted(Path(tmp).glob("s-*.png"))
        outs = []
        for i, f in enumerate(files, 1):
            dst = out_dir / f"{prefix}_{i:02d}.png"
            shutil.move(str(f), dst)
            outs.append(dst)
    return outs


def render_video(pngs: list[Path], out: Path, first: float = 3.0, each: float = 4.5) -> Path:
    """세로 카드들을 이어 붙인 무음 쇼츠 영상. 음악은 올릴 때 앱에서 고르면 된다."""
    with tempfile.TemporaryDirectory() as tmp:
        lst = Path(tmp) / "list.txt"
        lines = []
        for i, p in enumerate(pngs):
            lines += [f"file '{p.resolve()}'", f"duration {first if i == 0 else each}"]
        lines.append(f"file '{pngs[-1].resolve()}'")  # concat은 마지막 장 길이를 쓰려면 한 번 더 적어야 한다
        lst.write_text("\n".join(lines), encoding="utf-8")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-movflags", "+faststart", str(out)],
                       check=True)
    return out
