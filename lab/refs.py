"""레퍼런스 계정 인기 게시물 모으기 (시험용). 인스타: 비즈니스 검색 API(우리 열쇠), 유튜브: yt-dlp."""
import json, os, subprocess, urllib.request, urllib.parse, pathlib
OUT = pathlib.Path("refs"); (OUT / "img").mkdir(parents=True, exist_ok=True)
G = "https://graph.facebook.com/v23.0"; IG = "17841476113870391"; TOK = os.environ["IG_ACCESS_TOKEN"]
IG_ACCTS = ["dohwadore_life_reader", "fortune_tellingpower88", "forceteller_official", "seoyara_daily", "sinbi_saju",
            "taebaek_saju", "the.saju", "bachelor.saju", "salgusaju"]
YT = {"도화도르": "https://www.youtube.com/channel/UC0asDkei6mvw2YXcq6had8g",
      "현인의 명언": "https://www.youtube.com/@wise.saying77",
      "행운의신": "https://www.youtube.com/channel/UCV5jzEeY_Z_GHcVLwVyY4aw",
      "준철학관": "https://www.youtube.com/channel/UCQg_Y9uQBKfC-CCBMdksrVw"}
res = {"instagram": {}, "youtube": {}, "errors": []}
F = "username,name,followers_count,media_count,media.limit(50){caption,like_count,comments_count,media_type,media_product_type,permalink,timestamp,thumbnail_url,media_url}"
for u in IG_ACCTS:
    items, after, info = [], None, {}
    for page in range(6):
        f = F if not after else F.replace("media.limit(50)", f"media.after({after}).limit(50)")
        url = f"{G}/{IG}?fields=business_discovery.username({u}){{{f}}}&access_token={TOK}"
        try:
            d = json.load(urllib.request.urlopen(url, timeout=60))["business_discovery"]
        except urllib.error.HTTPError as e:
            res["errors"].append(f"IG {u}: {e.code} {e.read().decode()[:200]}"); break
        info = {k: d.get(k) for k in ("username", "name", "followers_count", "media_count")}
        m = d.get("media", {}); items += m.get("data", [])
        after = m.get("paging", {}).get("cursors", {}).get("after")
        if not after or not m.get("paging", {}).get("next"):
            break
    if info:
        res["instagram"][u] = {**info, "media": items}
        print(f"IG {u}: {len(items)}개, 팔로워 {info.get('followers_count')}")
for name, ch in YT.items():
    rows = []
    for tab in ("shorts", "videos"):
        p = subprocess.run(["yt-dlp", "--flat-playlist", "-J", "--playlist-end", "400", f"{ch}/{tab}"], capture_output=True, text=True)
        k = subprocess.run(["yt-dlp", "--flat-playlist", "-J", "--extractor-args", "youtube:lang=ko", "--playlist-end", "400", f"{ch}/{tab}"], capture_output=True, text=True)
        if p.returncode:
            res["errors"].append(f"YT {name} {tab}: {p.stderr[-200:]}"); continue
        ko = {e.get("id"): e.get("title") for e in (json.loads(k.stdout).get("entries") or [])} if k.returncode == 0 else {}
        for e in json.loads(p.stdout).get("entries") or []:
            rows.append({"id": e.get("id"), "title": ko.get(e.get("id")) or e.get("title"), "views": e.get("view_count"), "tab": tab,
                         "url": f"https://www.youtube.com/{'shorts/' if tab == 'shorts' else 'watch?v='}{e.get('id')}"})
    # 조회수 상위는 좋아요·댓글 수까지 받는다
    for tab in ("shorts", "videos"):
        for r in sorted([r for r in rows if r["tab"] == tab], key=lambda r: r["views"] or 0, reverse=True)[:15]:
            p = subprocess.run(["yt-dlp", "-j", "--skip-download", "--extractor-args", "youtube:lang=ko", r["url"]],
                               capture_output=True, text=True)
            if p.returncode == 0:
                j = json.loads(p.stdout)
                r.update(likes=j.get("like_count"), comments=j.get("comment_count"),
                         date=j.get("upload_date"), dur=j.get("duration"))
    res["youtube"][name] = rows
    print(f"YT {name}: {len(rows)}개")
# 인기 순 상위 썸네일 받기 (주소가 곧 만료되므로)
for u, a in res["instagram"].items():
    top = sorted(a["media"], key=lambda m: (m.get("like_count") or 0) + 3 * (m.get("comments_count") or 0), reverse=True)[:24]
    for m in top:
        src = m.get("thumbnail_url") or m.get("media_url")
        if src and m.get("media_type") != "VIDEO" or m.get("thumbnail_url"):
            try:
                (OUT / "img" / f"{m['id']}.jpg").write_bytes(urllib.request.urlopen(src, timeout=30).read())
            except Exception as e:  # noqa
                res["errors"].append(f"img {m['id']}: {e}")
for name, rows in res["youtube"].items():
    for r in sorted(rows, key=lambda r: r["views"] or 0, reverse=True)[:12]:
        try:
            (OUT / "img" / f"yt_{r['id']}.jpg").write_bytes(urllib.request.urlopen(f"https://i.ytimg.com/vi/{r['id']}/hqdefault.jpg", timeout=30).read())
        except Exception as e:  # noqa
            res["errors"].append(f"ytimg {r['id']}: {e}")
(OUT / "refs.json").write_text(json.dumps(res, ensure_ascii=False))
print("errors:", *res["errors"], sep="\n ")
