"""Live download progress for the OncoAgent dataset pipeline.

Run anytime to see where the downloads stand:
    python tools/progress.py
Add a watch loop:
    while (1) { cls; python tools/progress.py; sleep 10 }  (or: python tools/progress.py --watch)
"""
import sys
import time
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# expected final file sizes (bytes)
TARGETS = {
    "brain":    ("brisc2025.zip",            248_000_000),
    "colon":    ("kvasir-seg.zip",            46_200_000),
    "breast":   ("busi_train.parquet",       167_500_000),
    "lung":     ("Task06_Lung.tar",  8_530_000_000 + 300_000_000),   # tar is ~9.16e9 bytes on disk
    "liver":    ("Task03_Liver.tar", 26_940_000_000 + 1_000_000_000),
    "pancreas": ("Task07_Pancreas.tar", 11_450_000_000 + 300_000_000),
}

# precise sizes from real HTTP Content-Lengths
PRECISE = {
    "brain":    260_300_000,
    "colon":     46_227_172,
    "breast":   175_800_000,
    "lung":   9_163_696_640,
    "liver": 28_925_891_584,
    "pancreas": 12_289_971_712,
}


def file_size(path: Path, use_part=True) -> int:
    if path.exists():
        return path.stat().st_size
    if use_part:
        part = path.with_suffix(path.suffix + ".part")
        if part.exists():
            return part.stat().st_size
    return 0


def progress() -> dict:
    out = {}
    for organ, (name, _) in TARGETS.items():
        total = PRECISE[organ]
        done = file_size(RAW / organ / name)
        out[organ] = (done, total)
    return out


def render(prog: dict) -> str:
    lines = []
    done_all, total_all = 0, 0
    for organ, (done, total) in prog.items():
        done_all += min(done, total)
        total_all += total
        pct = done / total * 100 if total else 0
        bar_w = 28
        filled = int(bar_w * pct / 100)
        bar = "#" * filled + "-" * (bar_w - filled)
        done_str = f"{done/2**30:.2f} GiB" if done > 2**30 else f"{done/2**30:.2f} GiB"
        lines.append(f"{organ:9s} [{bar}] {pct:5.1f}%  {min(done,total)/2**30:6.2f}/{total/2**30:6.2f} GiB")
    overall = done_all / total_all * 100
    lines.append("")
    lines.append(f"OVERALL: {overall:.1f}%  ({done_all/2**30:.1f} / {total_all/2**30:.1f} GiB)")
    return "\n".join(lines)


if __name__ == "__main__":
    watch = "--watch" in sys.argv
    if watch:
        while True:
            print("\033[H\033[J" + render(progress()))
            time.sleep(5)
    else:
        print(render(progress()))