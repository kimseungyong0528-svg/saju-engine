"""레퍼런스 채널 쇼츠 대본 보관함 (내부 참고용). python archive.py 채널키
1) 채널 쇼츠 목록 2) 영상마다 제목·조회수·날짜 + 한국어 자막(올린 자막 > 자동 자막)
3) 자막이 없으면 소리를 받아 faster-whisper 로 받아쓰기. 시간 예산 안에서만.
결과: out/<키>.jsonl (한 줄에 영상 하나), out/<키>_log.txt"""
import json, sys, time, pathlib, re, traceback, subprocess
import yt_dlp
key = sys.argv[1]
ch = next(c for c in json.load(open(pathlib.Path(__file__).with_name("channels.json"), encoding="utf-8")) if c["key"] == key)
OUT = pathlib.Path(__file__).with_name("out"); OUT.mkdir(exist_ok=True)
dst, logf = OUT / f"{key}.jsonl", open(OUT / f"{key}_log.txt", "a", encoding="utf-8")
BUDGET = float(sys.argv[2]) if len(sys.argv) > 2 else 300 * 60
T0 = time.time()
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); logf.write(s + "\n"); logf.flush()
done = set()
if dst.exists():
    done = {json.loads(l)["id"] for l in dst.open(encoding="utf-8") if l.strip()}
base = {"quiet": True, "no_warnings": True, "sleep_interval_requests": 0.5, "retries": 3, "extractor_retries": 3}
with yt_dlp.YoutubeDL({**base, "extract_flat": True}) as y:
    lst = y.extract_info(ch["url"], download=False)
ents = [e for e in lst.get("entries", []) if e.get("id")]
ids = [e["id"] for e in ents]
with (OUT / f"{key}_list.jsonl").open("w", encoding="utf-8") as f:
    for e in ents:
        f.write(json.dumps({"id": e["id"], "title": e.get("title"), "views": e.get("view_count"), "dur": e.get("duration")}, ensure_ascii=False) + "\n")
log(ch["name"], "쇼츠", len(ids), "개, 이미", len(done))

def clean_json3(raw):
    ev = json.loads(raw).get("events", [])
    parts = ["".join(s.get("utf8", "") for s in e.get("segs", [])) for e in ev if e.get("segs")]
    txt = " ".join(p.strip() for p in parts if p.strip() and p.strip() != "\n")
    return re.sub(r"\s+", " ", txt).strip()

whisper = None
def transcribe(vid):
    global whisper
    if whisper is None:
        from faster_whisper import WhisperModel
        whisper = WhisperModel("small", device="cpu", compute_type="int8")
    p = f"/tmp/{vid}"
    with yt_dlp.YoutubeDL({**base, "format": "bestaudio/best", "outtmpl": p + ".%(ext)s"}) as y:
        info = y.extract_info(f"https://www.youtube.com/shorts/{vid}", download=True)
        f = y.prepare_filename(info)
    segs, _ = whisper.transcribe(f, language="ko", vad_filter=True, beam_size=1)
    txt = " ".join(s.text.strip() for s in segs)
    pathlib.Path(f).unlink(missing_ok=True)
    return txt

CLIENTS = ["default", "tv", "web_safari", "mweb", "android_vr", "ios"]
def ydl_for(c):
    o = {**base, "skip_download": True}
    if c != "default": o["extractor_args"] = {"youtube": {"player_client": [c]}}
    return yt_dlp.YoutubeDL(o)
ydls = {c: ydl_for(c) for c in CLIENTS}
good = None
def info_any(url):
    global good
    order = [good] + [c for c in CLIENTS if c != good] if good else CLIENTS
    last = None
    for c in order:
        try:
            i = ydls[c].extract_info(url, download=False); good = c; return i, ydls[c]
        except Exception as e:
            last = e
    raise last
def tapi(vid):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        t = YouTubeTranscriptApi().fetch(vid, languages=["ko"])
        return " ".join(s.text for s in t)
    except Exception as e:
        log("자막API 실패", vid, str(e)[:120]); return ""
fails = 0
for n, vid in enumerate(ids, 1):
    if vid in done: continue
    if time.time() - T0 > BUDGET:
        log("시간 예산 끝, 남은 영상은 다음 실행에서"); break
    rec = {"id": vid, "url": f"https://www.youtube.com/shorts/{vid}", "channel": ch["name"]}
    try:
        text, src = tapi(vid), "자막API"
        if text: src = "자막API"
        try:
            info, y = info_any(rec["url"]); log("client", good)
        except Exception:
            if not text: raise
            info = {}
        rec.update(title=info.get("title"), views=info.get("view_count"), likes=info.get("like_count"),
                   date=info.get("upload_date"), dur=info.get("duration"), desc=(info.get("description") or "")[:500])
        for kind in ("subtitles", "automatic_captions"):
            tracks = (info.get(kind) or {})
            lang = next((l for l in tracks if l == "ko" or l.startswith("ko")), None)
            if text or not lang: continue
            fmt = next((t for t in tracks[lang] if t.get("ext") == "json3"), None)
            if not fmt: continue
            text = clean_json3(y.urlopen(fmt["url"]).read().decode("utf-8")); src = "자막" if kind == "subtitles" else "자동자막"
            if text: break
        if not text:
            text, src = transcribe(vid), "받아쓰기"
        rec.update(text=text, source=src); fails = 0
    except Exception as e:
        rec["error"] = str(e)[-300:]; fails += 1
        log("실패", vid, rec["error"][:200])
        if fails >= 4:
            log("연속 실패, 멈춤"); 
            with dst.open("a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            break
    with dst.open("a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if n % 20 == 0: log(n, "/", len(ids), round((time.time() - T0) / 60, 1), "분")
log("끝", round((time.time() - T0) / 60, 1), "분")
