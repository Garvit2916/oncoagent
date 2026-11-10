"""Download real medical imaging datasets for OncoAgent (all 6 organs).

Sources (all public / research-licensed):
  brain   : BRISC 2025 (Sci Data) - 6000 T1 MRI slices + pixel masks  -> figshare
  lung    : Medical Segmentation Decathlon Task06_Lung (CT + tumor masks) -> MSD AWS S3
  liver   : Medical Segmentation Decathlon Task03_Liver (CT + masks)  -> MSD AWS S3
  pancreas: Medical Segmentation Decathlon Task07_Pancreas (CT + masks) -> MSD AWS S3
  colon   : Kvasir-SEG (polyp endoscopy images + masks)               -> Univ. Simula
  breast  : BUSI (Breast Ultrasound Images, 780 imgs + masks) curated -> Zenodo

Usage:
  python tools/download_datasets.py [--organ all|brain|liver|pancreas|lung|colon|breast]
  --maybe-reuse existing files (resume support).

Outputs are written to data/raw/<organ>/...
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

SOURCES = {
    "brain": {
        "url": "https://ndownloader.figshare.com/files/59298329",
        "filename": "brisc2025.zip",
        "expected_md5": None,
        "note": "BRISC 2025 brain MRI (images + masks)",
    },
    "lung": {
        "url": "https://msd-for-monai.s3.amazonaws.com/Task06_Lung.tar",
        "filename": "Task06_Lung.tar",
        "expected_md5": None,
        "note": "Decathlon Task06_Lung (CT + tumor masks)",
    },
    "liver": {
        "url": "https://msd-for-monai.s3.amazonaws.com/Task03_Liver.tar",
        "filename": "Task03_Liver.tar",
        "expected_md5": None,
        "note": "Decathlon Task03_Liver (CT + masks)",
    },
    "pancreas": {
        "url": "https://msd-for-monai.s3.amazonaws.com/Task07_Pancreas.tar",
        "filename": "Task07_Pancreas.tar",
        "expected_md5": None,
        "note": "Decathlon Task07_Pancreas (CT + masks)",
    },
    "colon": {
        "url": "https://datasets.simula.no/downloads/kvasir-seg.zip",
        "filename": "kvasir-seg.zip",
        "expected_md5": None,
        "note": "Kvasir-SEG polyp images + masks",
    },
    "breast": {
        "url": "https://zenodo.org/records/21128640/files/BUSI.zip?download=1",
        "filename": "BUSI.zip",
        "expected_md5": "c6d336ffa4b0314b1488c7e4c686d7d8",
        "note": "BUSI breast ultrasound (images + masks, curated)",
    },
}


def md5_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def download(url: str, dest: Path, expected_md5=None) -> bool:
    """Download with resume support. Writes to <dest>.part then renames on success."""
    partial = dest.with_suffix(dest.suffix + ".part")

    if dest.exists() and dest.stat().st_size > 0:
        if expected_md5:
            try:
                if md5_of(dest) == expected_md5:
                    print(f"  [{dest.name}] md5 OK, skip download")
                    return True
                print(f"  [{dest.name}] md5 mismatch, re-downloading")
            except Exception as e:
                print(f"  [{dest.name}] md5 check failed ({e}), re-downloading")
        else:
            print(f"  [{dest.name}] already exists, skip download")
            return True

    if partial.exists() and partial.stat().st_size > 0:
        resume = partial.stat().st_size
    else:
        resume = 0
    if resume:
        print(f"  [{dest.name}] resuming from {resume/2**30:.2f} GiB")
    elif partial.exists():
        partial.unlink()

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = partial if partial.exists() else partial
    headers = {"User-Agent": "Mozilla/5.0"}
    if resume:
        headers["Range"] = f"bytes={resume}-"
    req = urllib.request.Request(url, headers=headers)

    print(f"  downloading -> {dest.name}")
    t0 = time.time()
    dl_total = resume
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length", 0)) + (resume or 0)
        mode = "ab" if resume else "wb"
        with open(tmp, mode) as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                dl_total += len(chunk)
                if total:
                    pct = dl_total / total * 100
                    rate = (dl_total - resume) / (time.time() - t0 + 1e-9) / 1e6
                    print(f"\r  [{dest.name}] {dl_total/2**30:.2f}/{total/2**30:.2f} GiB  {pct:.1f}%  {rate:.1f} MB/s   ", end="", flush=True)
    print()
    os.replace(tmp, dest)
    if expected_md5:
        got = md5_of(dest)
        if got != expected_md5:
            print(f"  WARNING: md5 mismatch for {dest.name}: {got}")
    return True


def extract(archive: Path, dest: Path) -> None:
    marker = dest / ".extracted"
    if marker.exists():
        print(f"  [{archive.name}] already extracted, skip")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  extracting -> {dest}")
    if archive.suffix == ".zip" or archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            z.extractall(dest)
    elif archive.suffix == ".tar" or archive.name.endswith(".tar"):
        with tarfile.open(archive) as t:
            if sys.version_info >= (3, 12):
                t.extractall(dest, filter="data")
            else:
                t.extractall(dest)
    marker.touch()


def fetch(organ: str) -> None:
    cfg = SOURCES[organ]
    raw_dir = RAW / organ
    archive = raw_dir / cfg["filename"]
    print(f"\n=== {organ}: {cfg['note']}")
    download(cfg["url"], archive, cfg["expected_md5"])
    extract(archive, raw_dir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--organ", default="all", choices=list(SOURCES) + ["all"])
    args = ap.parse_args()

    organs = list(SOURCES) if args.organ == "all" else [args.organ]
    for o in organs:
        try:
            fetch(o)
        except Exception as e:
            print(f"  !!! {o} failed: {e}")

    print("\nDone. Raw data locations:")
    for o in organs:
        d = RAW / o
        n = sum(1 for _ in d.rglob("*") if _.is_file()) if d.exists() else 0
        print(f"  data/raw/{o}: {n} files")


if __name__ == "__main__":
    main()