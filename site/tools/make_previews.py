"""리포트 미리보기 그림 만들기 (2026-10-27).

가상의 인물로 만든 상품별 견본 PDF에서 표지·목차·사주표·요약 쪽을 골라 WebP로 저장한다.
견본 PDF는 저장소 밖(/mnt/project-files/samples)에 있으므로 그림만 저장소에 넣는다.
예) python site/tools/make_previews.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

SAMPLES = Path("/mnt/project-files/samples")
OUT = Path(__file__).resolve().parents[1] / "public" / "assets" / "preview"

# 상품: (견본 PDF, 보여 줄 쪽 번호). 쪽 번호는 1부터.
PICKS = {
    "lifetime": ("lifetime-sample-hong.pdf", [1, 2, 6, 9, 11]),
    "romance": ("romance-preview-draft.pdf", [1, 2, 4, 5, 7]),
    "reunion": ("theme/재회사주-박지은.pdf", [1, 2, 5, 6, 8]),
    "intimate": ("theme/깊은궁합-최유나.pdf", [1, 2, 5, 6, 7]),
    "wealth": ("theme/재물운-이준호.pdf", [1, 2, 5, 6, 8]),
    "career": ("theme/직업이직운-윤서진.pdf", [1, 2, 5, 6, 8]),
    "business": ("theme/사업운-강태준.pdf", [1, 2, 5, 6, 8]),
    "health": ("theme/건강운-오미숙.pdf", [1, 2, 5, 6, 8]),
    "newyear": ("theme/신년운세-한서연.pdf", [1, 2, 5, 6, 8]),
}
WIDTH = 720


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for pid, (pdf, pages) in PICKS.items():
        for n, page in enumerate(pages, 1):
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp) / "p"
                subprocess.run(["pdftoppm", "-r", "110", "-png", "-singlefile", "-f", str(page), "-l", str(page),
                                str(SAMPLES / pdf), str(base)], check=True)
                im = Image.open(str(base) + ".png").convert("RGB")
                im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
                dest = OUT / f"{pid}-{n}.webp"
                im.save(dest, "WEBP", quality=80, method=6)
                print(dest.name, dest.stat().st_size // 1024, "KB", file=sys.stderr)


if __name__ == "__main__":
    main()
