"""시험: 단아선녀(dan_aaahhh2) 인스타 게시물을 메타 비즈니스 검색으로 받을 수 있는지."""
import json, os, urllib.request, urllib.error, pathlib
G = "https://graph.facebook.com/v23.0"; IG = "17841476113870391"; TOK = os.environ["IG_ACCESS_TOKEN"]
out = {}
def get(name, url):
    try:
        out[name] = json.load(urllib.request.urlopen(url + ("&" if "?" in url else "?") + "access_token=" + TOK, timeout=60))
    except urllib.error.HTTPError as e:
        out[name] = {"ERR": e.code, "body": e.read().decode()[:400]}
    print(name, json.dumps(out[name], ensure_ascii=False)[:600])
get("perms", f"{G}/me/permissions")
get("own", f"{G}/{IG}?fields=username,followers_count,media_count")
get("bd_min", f"{G}/{IG}?fields=business_discovery.username(dan_aaahhh2){{username,followers_count,media_count}}")
F = "username,followers_count,media_count,media.limit(100){caption,like_count,comments_count,media_type,media_product_type,permalink,timestamp,thumbnail_url,media_url}"
get("bd_media", f"{G}/{IG}?fields=business_discovery.username(dan_aaahhh2){{{F}}}")
get("bd_self", f"{G}/{IG}?fields=business_discovery.username(unmyeong_saju.kr){{username,followers_count}}")
p = pathlib.Path("refs"); p.mkdir(exist_ok=True)
(p / "ig.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
