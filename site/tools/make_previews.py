"""리포트 미리보기 그림 만들기 (2026-10-27).

가상의 인물로 만든 상품별 견본 PDF에서 풀이 쪽을 골라 WebP로 저장한다.
견본 PDF는 저장소 밖(/mnt/project-files/samples)에 있으므로 그림만 저장소에 넣는다.
예) python site/tools/make_previews.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

SAMPLES = Path("/mnt/project-files/samples")
OUT = Path(__file__).resolve().parents[1] / "public" / "assets" / "preview"

# 상품: (견본 PDF, 보여 줄 쪽 번호). 쪽 번호는 1부터, 이 순서대로 보여 준다.
# 2026-10-27 사장님: 표지·목차·한자 분석 쪽은 빼고, 결과가 자극적으로 나온 풀이 쪽 8장만.
# 평생사주·연애사주는 초안 견본의 풀이가 비어 있어 실제 글쓰기로 만든 견본(real-kim, sua)에서 뽑는다.
PICKS = {
    "lifetime": ("lifetime-sample-real-kim.pdf", [54, 60, 62, 112, 82, 59, 45, 29]),
    "romance": ("romance-sample-sua.pdf", [41, 28, 17, 24, 25, 16, 9, 44]),
    "reunion": ("theme/재회사주-박지은.pdf", [26, 28, 20, 43, 31, 19, 12, 39]),
    "intimate": ("theme/깊은궁합-최유나.pdf", [38, 14, 9, 25, 20, 17, 34, 39]),
    "wealth": ("theme/재물운-이준호.pdf", [20, 33, 10, 29, 19, 24, 28, 40]),
    "career": ("theme/직업이직운-윤서진.pdf", [29, 25, 31, 32, 33, 14, 16, 19]),
    "business": ("theme/사업운-강태준.pdf", [26, 27, 36, 18, 11, 30, 32, 44]),
    "health": ("theme/건강운-오미숙.pdf", [11, 10, 25, 40, 12, 16, 34, 35]),
    "newyear": ("theme/신년운세-한서연.pdf", [10, 21, 22, 30, 52, 18, 36, 14]),
}
WIDTH = 720


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.webp"):
        old.unlink()
    captions = {}
    for pid, (pdf, pages) in PICKS.items():
        for n, page in enumerate(pages, 1):
            # 그림 아래 이름: 그 쪽의 소제목(머리글 두 줄 다음 첫 줄)
            text = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), str(SAMPLES / pdf), "-"],
                                  capture_output=True, text=True, check=True).stdout
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            captions.setdefault(pid, []).append(lines[2] if len(lines) > 2 else "")
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp) / "p"
                subprocess.run(["pdftoppm", "-r", "110", "-png", "-singlefile", "-f", str(page), "-l", str(page),
                                str(SAMPLES / pdf), str(base)], check=True)
                im = Image.open(str(base) + ".png").convert("RGB")
                im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
                dest = OUT / f"{pid}-{n}.webp"
                im.save(dest, "WEBP", quality=80, method=6)
                print(dest.name, dest.stat().st_size // 1024, "KB", captions[pid][-1], file=sys.stderr)
    (OUT / "captions.json").write_text(json.dumps(captions, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
