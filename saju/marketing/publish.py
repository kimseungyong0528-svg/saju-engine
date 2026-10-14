"""만든 게시물 묶음을 관리 사이트(운명서재 /studio)에 올린다. 사이트 저장소(Blobs)에만 올리므로 사이트 배포는 일어나지 않는다."""

from __future__ import annotations

import json
import mimetypes
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _call(method: str, path: str, body: bytes | None = None, content_type: str = "application/json") -> dict:
    url = os.environ.get("SITE_URL", "https://unmyeong-saju.com").rstrip("/") + path
    for attempt in range(3):
        req = urllib.request.Request(url, data=body, method=method, headers={
            "X-Worker-Secret": os.environ["WORKER_SECRET"], "Content-Type": content_type, "User-Agent": "unmyeong-studio"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == 2:
                raise
        except urllib.error.URLError:
            if attempt == 2:
                raise
        time.sleep(3 * (attempt + 1))
    return {}


def status(week: str, value: str, note: str = "") -> None:
    try:
        _call("POST", f"/api/internal/studio/{week}/status", json.dumps({"status": value, "note": note}).encode())
    except urllib.error.URLError as e:
        print(f"상태 보내기 실패: {value} {e}")


def used_keys() -> set[str]:
    try:
        return set(_call("GET", "/api/internal/studio/used").get("keys", []))
    except urllib.error.URLError as e:
        print(f"쓴 재료 목록 받기 실패: {e}")
        return set()


def upload_week(folder: Path) -> None:
    week = folder.name
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    files = set()
    for d in manifest["days"]:
        for it in d["items"]:
            files.update(f for f in [it.get("video"), it.get("thumb"), *it.get("images", [])] if f)
    for rel in sorted(files):
        ctype = mimetypes.guess_type(rel)[0] or "application/octet-stream"
        _call("PUT", f"/api/internal/studio/{week}/file?path={urllib.parse.quote(rel)}", (folder / rel).read_bytes(), ctype)
    # 목록(manifest)은 파일을 다 올린 뒤 마지막에 올린다. 그래야 화면에 반쯤 올라간 묶음이 보이지 않는다.
    _call("POST", f"/api/internal/studio/{week}/manifest", json.dumps(manifest, ensure_ascii=False).encode())
    print(f"관리 사이트에 올림: 파일 {len(files)}개")
