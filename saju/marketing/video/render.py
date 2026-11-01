"""대본 → 목소리 → 시간표 → 배경음 섞기 → HTML 틀을 한 장씩 찍어 mp4.

make_talk(Post, out): 이야기형 쇼츠 (표지 → 본문 장마다 → 기억할 한 줄 → 마무리)
make_rank(RankPost, out): 띠 순위 쇼츠 (12위부터 1위까지)
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from ..content import Post
from ..ranking import KINDS, RankPost
from . import images, music, voice

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
FONTS = ROOT / "saju" / "report" / "fonts"
MFONTS = ROOT / "saju" / "marketing" / "fonts"
ART = ROOT / "site" / "public" / "assets" / "geumwol"
FPS = 30
LEAD, GAP, TAIL = 0.4, 0.3, 1.4
OUTRO = "내일도 띠별 운세 올려요. 놓치기 싫으면 팔로우 해 두세요."
BGS = ["palace-study.jpg", "palace-garden.jpg", "palace-gate.jpg"]
COVER = {"ddi": "newyear-cover.jpg", "summary": "newyear-cover.jpg", "topic": "master.jpg"}


def _dur(path: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)]).decode().strip())


def _voice_lines(texts: list[str], work: Path) -> tuple[list[Path], list[float], list[float], float]:
    """줄마다 목소리 파일을 만들고 시작 시각을 정한다."""
    files, starts, ends, t = [], [], [], LEAD
    for i, text in enumerate(texts):
        f = voice.speak(text, work / f"v{i:02d}.wav")
        d = _dur(f)
        files.append(f); starts.append(round(t, 2)); ends.append(round(t + d + GAP, 2))
        t += d + GAP
    return files, starts, ends, round(t + TAIL, 2)


def _mix(files: list[Path], starts: list[float], total: float, seed: int, out: Path,
         events: list[tuple[float, str]] | None = None) -> Path:
    bgm = music.ambient(total + 1, out.with_name("bgm.wav"), seed)
    fx = music.sfx(total, events or [], out.with_name("sfx.wav"))
    ins, flt = [], []
    for i, (f, s) in enumerate(zip(files, starts)):
        ins += ["-i", str(f)]
        ms = int(s * 1000)
        flt.append(f"[{i}]aresample=44100,aformat=channel_layouts=mono,adelay={ms}|{ms}[v{i}]")
    n = len(files)
    ins += ["-i", str(bgm), "-i", str(fx)]
    flt.append("".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,loudnorm=I=-15:TP=-1.5,"
               "aresample=44100,apad,asplit=2[voice][voice2]")
    flt.append(f"[{n}]atrim=0:{total},volume=0.14,aformat=channel_layouts=mono,aresample=44100[bg]")
    flt.append(f"[{n + 1}]atrim=0:{total},volume=0.22,aformat=channel_layouts=mono,aresample=44100[fx]")
    flt.append("[bg][voice]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=400[duck]")
    flt.append("[duck][voice2][fx]amix=inputs=3:normalize=0[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(flt), "-map", "[a]",
                    "-t", str(total), "-ar", "44100", "-b:a", "160k", str(out)], check=True)
    return out


def _browser(p):
    try:
        return p.chromium.launch()
    except Exception:
        exe = os.environ.get("CHROMIUM_PATH") or next(iter(sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))), None)
        if not exe:
            raise
        return p.chromium.launch(executable_path=exe)


def _chunk(args) -> str:
    """frames [a, b) 를 찍어 소리 없는 조각 영상으로 만든다(프로세스마다 브라우저 하나)."""
    page_file, plan, a, b, out = args
    from playwright.sync_api import sync_playwright

    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "21", "-r", str(FPS), out],
                          stdin=subprocess.PIPE)
    try:
        with sync_playwright() as p:
            br = _browser(p)
            pg = br.new_page(viewport={"width": 1080, "height": 1920})
            pg.goto(Path(page_file).as_uri())
            pg.evaluate("p => document.fonts.ready.then(() => window.setPlan(p))", plan)
            pg.wait_for_timeout(300)
            for i in range(a, b):
                pg.evaluate("t => window.render(t)", i / FPS)
                ff.stdin.write(pg.screenshot(type="jpeg", quality=88))
            br.close()
    finally:
        ff.stdin.close()
        if ff.wait() != 0:
            raise RuntimeError("ffmpeg가 영상 조각을 만들지 못함")
    return out


def workers() -> int:
    return max(1, int(os.environ.get("SAJU_VIDEO_WORKERS") or os.cpu_count() or 1))


def _capture(template: str, plan: dict, audio: Path, out: Path, work: Path) -> Path:
    """프레임을 나눠 여러 브라우저로 동시에 찍고, 조각을 이은 뒤 소리를 붙인다."""
    import multiprocessing as mp

    html = (HERE / template).read_text(encoding="utf-8")
    html = html.replace("url(FONTS/", f"url({FONTS.as_uri()}/").replace("url(MFONTS/", f"url({MFONTS.as_uri()}/")
    page_file = work / template
    page_file.write_text(html, encoding="utf-8")
    n = int(plan["total"] * FPS)
    w = min(workers(), max(1, n // 60))
    cuts = [n * k // w for k in range(w + 1)]
    jobs = [(str(page_file), plan, cuts[k], cuts[k + 1], str(work / f"part{k:02d}.mp4")) for k in range(w)]
    if w == 1:
        parts = [_chunk(jobs[0])]
    else:
        with mp.get_context("spawn").Pool(w) as pool:
            parts = pool.map(_chunk, jobs)
    lst = work / "parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(audio),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)],
                   check=True)
    return out


def _split_body(body: str) -> tuple[list[str], list[str]]:
    """본문 → (자막·대본 문장들, 화면에 띄울 번호 목록)."""
    items = [re.sub(r"^\s*\d+\.\s*", "", l).strip() for l in body.splitlines() if re.match(r"^\s*\d+\.", l)]
    if items:
        rest = [l for l in body.splitlines() if l.strip() and not re.match(r"^\s*\d+\.", l)]
        return [s for l in rest for s in voice.sentences(l)] + items, items
    return voice.sentences(body), []


def talk_plan(p: Post) -> tuple[list[str], dict]:
    keys = sorted({*p.keywords[:1], *(p.facts.get("relations") or []), f"{p.key}띠" if p.kind == "ddi" else ""} - {""},
                  key=len, reverse=True)
    scenes, texts, caps = [], [], []
    kicker = "·".join(f"{y % 100:02d}" for y in p.facts["years"]) + "년생" if p.kind == "ddi" else "운명서재 사주 상식"
    scenes.append({"type": "cover", "bg": (ART / COVER.get(p.kind, "master.jpg")).as_uri(), "kicker": kicker, "title": p.hook})
    for s in [p.hook if p.kind != "ddi" else f"{p.hook}, 지금 알려 드릴게요.", p.sub]:
        if s:
            texts.append(s); caps.append((s, 0))
    for i, sl in enumerate(p.slides, 1):
        sents, items = _split_body(sl["body"])
        scenes.append({"type": "point", "no": i, "head": sl["head"], "items": items,
                       "bg": (ART / BGS[(i - 1 + len(p.key)) % len(BGS)]).as_uri()})
        for s in sents:
            texts.append(s); caps.append((s, len(scenes) - 1))
    scenes.append({"type": "remember", "text": p.remember, "bg": (ART / "palace-gate.jpg").as_uri()})
    texts.append(p.remember); caps.append((p.remember, len(scenes) - 1))
    scenes.append({"type": "end", "bg": (ART / "palace-gate.jpg").as_uri(), "sub": "내 생년월일로 보는 운세 한 권"})
    texts.append(OUTRO); caps.append(("놓치기 싫으면 팔로우", len(scenes) - 1))
    chip = "2027 정미년 띠별 운세" if p.kind in ("ddi", "summary") else "운명서재 사주 상식"
    hook = f"{p.key}띠라면\n꼭 보세요" if p.kind == "ddi" else ("내 띠는\n괜찮을까?" if p.kind == "summary" else "모르면\n손해예요")
    return texts, {"scenes": scenes, "caps": caps, "keys": keys, "chip": chip, "hook": hook}


def _ai_art(p: Post, scenes: list[dict], work: Path, day: str) -> int:
    """본문·기억 장면 그림을 그날 새로 그린다. 그린 장 수를 돌려준다 (실패한 장면은 고정 그림 그대로)."""
    animal = p.key if p.kind == "ddi" else ""
    n = 0
    for i, sc in enumerate(scenes):
        if sc["type"] not in ("point", "remember"):
            continue
        text = sc.get("head", "") + " " + " ".join(sc.get("items") or []) + " " + sc.get("text", "")
        prompt = images.scene_prompt(text, f"{day}|{p.kind}|{p.key}", i, animal)
        got = images.draw(prompt, work / f"art{i}.jpg", images._seed(day, p.key, str(i)))
        if got:
            sc["bg"] = got.as_uri(); n += 1
    return n


def make_talk(p: Post, out: Path, seed: int = 7, day: str = "") -> dict:
    texts, base = talk_plan(p)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        art = _ai_art(p, base["scenes"], work, day or date.today().isoformat())
        files, starts, ends, total = _voice_lines(texts, work)
        lines = [{"s": s, "e": e, "cap": c, "scene": sc} for s, e, (c, sc) in zip(starts, ends, base.pop("caps"))]
        plan = {**base, "lines": lines, "total": total}
        changes = [l["s"] - 0.15 for a, l in zip(lines, lines[1:]) if l["scene"] != a["scene"]]
        audio = _mix(files, starts, total, seed, work / "audio.m4a", [(t, "whoosh") for t in changes])
        _capture("talk.html", plan, audio, out, work)
    return {"seconds": total, "voice": voice.status(), "art": art}


def rank_plan(p: RankPost, starts: list[float], ends: list[float], total: float) -> dict:
    k = KINDS[p.kind]
    rows = [{"rank": r.rank, "ddi": r.ddi, "years": r.years} for r in p.rows]
    # lines: 0 소개, 1~12 = 12위…1위, 13 마무리
    reveal = [starts[13 - r] for r in range(1, 13)]
    top = p.rows[0]
    crown = "<br>".join((top.good + top.bad)[:2])
    return {"rows": rows, "reveal": reveal, "crownAt": round(starts[12] + 1.6, 2), "crown": crown,
            "caps": [{"s": s, "e": e, "text": c} for s, e, c in zip(starts, ends, p.caps)], "total": total,
            "t1": k["head"], "t2": p.period.long, "t3": f"{k['name']} 띠 순위", "c1": f"{p.period.label} {k['name']} 1위",
            "foot": f"내 사주로 보는 {p.period.label} {k['name']}", "hook": "내 띠는\n몇 위?"}


def make_rank(p: RankPost, out: Path, seed: int = 11) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        files, starts, ends, total = _voice_lines(p.lines, work)
        plan = rank_plan(p, starts, ends, total)
        ev = [(t, "big" if i < 3 else "ding") for i, t in enumerate(plan["reveal"])] + [(plan["crownAt"], "crown")]
        audio = _mix(files, starts, total, seed, work / "audio.m4a", ev)
        _capture("rank.html", plan, audio, out, work)
    return {"seconds": total, "voice": voice.status()}


if __name__ == "__main__":   # 시험: python -m saju.marketing.video.render 출력폴더
    import datetime as dt
    import sys

    from ..content import ddi_posts
    from ..ranking import rank_post, year_period
    o = Path(sys.argv[1]); o.mkdir(parents=True, exist_ok=True)
    print(json.dumps(make_rank(rank_post("money", year_period(2027)), o / "rank.mp4"), ensure_ascii=False))
    print(json.dumps(make_talk(ddi_posts()[0], o / "talk.mp4"), ensure_ascii=False))
