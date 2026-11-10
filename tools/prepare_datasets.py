"""Prepare all organs into a unified training layout.

Reads raw sources (Decathlon NIfTI volumes + 2D datasets) and emits:
  data/processed/index.csv          : per-sample rows (split, organ, image, mask, has_mask)
  data/processed/images/{split}/..  : 256x256 grayscale PNG
  data/processed/masks/{split}/..   : 256x256 binary PNG (0/255)
  data/processed/yolo_labels/{split}/.. : normalized bbox txt files
  data/processed/yolo_cfg/data.yaml : YOLO class config (fixed 6-class order)

Usage: python tools/prepare_datasets.py
"""

import argparse
import csv
import hashlib
import os
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

# Fixed class order MUST match backend YOLOModel.ORGAN_MAP
CLASSES = ["Liver", "Lung", "Pancreas", "Colon", "Brain", "Breast"]
CLASS_ID = {name.lower(): i for i, name in enumerate(CLASSES)}

SIZE = (256, 256)

SOURCES = {
    "lung": "nifti",
    "liver": "nifti",
    "pancreas": "nifti",
    "brain": "images",
    "colon": "images",
    "breast": "images",
}


def stable_split(key: str, train=0.7, val=0.15) -> str:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    r = h / (2**128)
    if r < train:
        return "train"
    if r < train + val:
        return "val"
    return "test"


def _gray(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 3:
        return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    return arr


def _norm01(arr: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(arr, 1.0), np.percentile(arr, 99.0)
    if hi - lo < 1e-6:
        return np.zeros_like(arr)
    return np.clip((arr.astype(np.float32) - lo) / (hi - lo), 0, 1)


def process_nifti(organ: str, counter) -> list:
    task_dir = None
    for cand in sorted((RAW / organ).iterdir()):
        if cand.is_dir() and (cand / "imagesTr").exists() and not cand.name.startswith("."):
            task_dir = cand
            break
    if task_dir is None:
        print(f"  [{organ}] no task dir with imagesTr found, skip")
        return []

    img_dir = task_dir / "imagesTr"
    lbl_dir = task_dir / "labelsTr"
    nii_img = sorted(p for p in img_dir.glob("*.nii.gz") if not p.name.startswith("._"))
    nii_lbl = sorted(p for p in lbl_dir.glob("*.nii.gz") if not p.name.startswith("._"))

    # group labels by case id
    lbl_by_case = {}
    for lp in nii_lbl:
        case = lp.name.replace("segmentation_", "").replace(".nii.gz", "")
        lbl_by_case[case] = lp

    rows, images_kept = [], {s: 0 for s in ("train", "val", "test")}

    for ip in nii_img:
        case = ip.name.replace(".nii.gz", "")
        lp = None
        for k, v in lbl_by_case.items():
            if k in case or case in k:
                lp = v
                break
        if lp is None:
            continue

        vol = _norm01(nib_load(ip))
        seg = nib_load(lp)

        split = stable_split(case)
        h, w, d = vol.shape
        sel = np.where(seg.max(axis=(0, 1)) > 0)[0]
        sel = sel[sel < d] if len(sel) else sel
        if len(sel) == 0:
            sel = np.arange(d)
        sel = sel[:: max(1, len(sel) // 120)][:120]

        for idx in sel:
            img = prepare_kv(vol[:, :, idx], seg[:, :, idx], organ, counter, source=case, idx=idx)
            if img is None:
                continue
            img["split"] = split
            rows.append(img)
            images_kept[split] += 1
            counter += 1

    print(f"  [{organ}] kept slices -> train {images_kept['train']} val {images_kept['val']} test {images_kept['test']}")
    return rows


def process_images2d(organ: str, image_dir: Path, mask_dir: Path, pattern: str, mask_stem_fn, counter) -> list:
    rows = []
    images_kept = {s: 0 for s in ("train", "val", "test")}
    img_files = sorted(image_dir.glob(pattern))
    for ip in img_files:
        mp = mask_dir / mask_stem_fn(ip)
        if not mp.exists():
            continue
        img = cv2.imread(str(ip), cv2.IMREAD_GRAYSCALE)
        mask = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE)
        if img is None or mask is None:
            continue
        split = stable_split(ip.stem)
        row = prepare_kv(img, mask, organ, counter, source=ip.stem, idx=0, normalize=True)
        if row is None:
            continue
        rows.append(row)
        images_kept[split] += 1
        counter += 1
    print(f"  [{organ}] kept -> train {images_kept['train']} val {images_kept['val']} test {images_kept['test']}")
    return rows


def prepare_kv(img: np.ndarray, mask: np.ndarray, organ: str, counter: int, source: str, idx: int, normalize=False) -> dict | None:
    img = _gray(img)
    mask = _gray(mask)
    if img.shape != SIZE:
        img = cv2.resize(img, SIZE, interpolation=cv2.INTER_LINEAR)
        mask = cv2.resize(mask, SIZE, interpolation=cv2.INTER_NEAREST)
    if normalize:
        img = _norm01(img)

    cid = CLASS_ID.get(organ, 0)

    img8 = (img * 255).astype(np.uint8) if img.max() <= 1.0 else img.astype(np.uint8)
    mbin = (mask > 0).astype(np.uint8)
    has_mask = bool(mbin.sum() > 0)

    name = f"{organ}_{counter:05d}"
    split = stable_split(f"{organ}:{source}:{idx}")
    img_p = OUT / "images" / split / f"{name}.png"
    msk_p = OUT / "masks" / split / f"{name}.png"

    cv2.imwrite(str(img_p), img8)
    if has_mask:
        cv2.imwrite(str(msk_p), mbin * 255)
        write_yolo_label(name, split, cid, mbin)

    return dict(split=split, organ=organ, image=f"images/{split}/{name}.png", mask=f"masks/{split}/{name}.png" if has_mask else "", has_mask=int(has_mask), source=source)


def write_yolo_label(name: str, split: str, cid: int, mbin: np.ndarray):
    ys, xs = np.where(mbin > 0)
    x1, x2, y1, y2 = xs.min(), xs.max(), ys.min(), ys.max()
    xc = ((x1 + x2) / 2) / SIZE[0]
    yc = ((y1 + y2) / 2) / SIZE[1]
    w = (x2 - x1) / SIZE[0]
    h = (y2 - y1) / SIZE[1]
    lbl = OUT / "labels" / split / f"{name}.txt"
    lbl.parent.mkdir(parents=True, exist_ok=True)
    lbl.write_text(f"{cid} {xc:.6f} {yc:.6f} {max(w, 1e-4):.6f} {max(h, 1e-4):.6f}\n")


def detect_organ(source: str) -> str:
    s = source.lower()
    for organ, src in SOURCES.items():
        toks = {"lung": ["lung"], "liver": ["liver"], "pancreas": ["pancreas"], "brain": ["brisc", "brain"], "colon": ["kvasir", "colon", "polyp"], "breast": ["busi", "breast"]}
        if any(t in s for t in toks.get(organ, [])):
            return organ
    return "Screening"


def detect_organ(source: str) -> str:
    s = source.lower()
    for organ in SOURCES:
        toks = {"lung": ["lung"], "liver": ["liver"], "pancreas": ["pancreas"], "brain": ["brisc", "brain"], "colon": ["kvasir", "colon", "polyp"], "breast": ["busi", "breast"]}
        if any(t in s for t in toks.get(organ, [])):
            return organ
    return "Screening"


def nib_load(p: Path) -> np.ndarray:
    import nibabel as nib

    return np.asarray(nib.load(str(p)).get_fdata())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--organs", default="all", help="comma list: lung,liver,pancreas,brain,colon,breast")
    args = ap.parse_args()

    organs = list(SOURCES) if args.organs == "all" else [o.strip() for o in args.organs.split(",")]

    for s in ("train", "val", "test"):
        (OUT / "images" / s).mkdir(parents=True, exist_ok=True)
        (OUT / "masks" / s).mkdir(parents=True, exist_ok=True)
        (OUT / "labels" / s).mkdir(parents=True, exist_ok=True)

    counter = 0
    all_rows = []

    for organ in organs:
        kind = SOURCES[organ]
        src_dir = RAW / organ
        if not src_dir.exists():
            print(f"[{organ}] raw dir missing, skip")
            continue
        if not (src_dir / ".extracted").exists():
            print(f"[{organ}] not extracted yet, skip")
            continue
        print(f"\n== {organ} ({kind}) ==")
        if kind == "nifti":
            rows = process_nifti(organ, counter)
        else:
            if organ == "brain":
                img_dir = RAW / "brain" / "brisc2025" / "segmentation_task" / "train" / "images"
                msk_dir = RAW / "brain" / "brisc2025" / "segmentation_task" / "train" / "masks"
                rows = process_images2d(organ, img_dir, msk_dir, "*.jpg", lambda p: p.stem + ".png", counter)
            elif organ == "colon":
                rows = process_images2d(organ, RAW / "colon" / "Kvasir-SEG" / "images", RAW / "colon" / "Kvasir-SEG" / "masks", "*.jpg", lambda p: p.name, counter)
            elif organ == "breast":
                rows = process_images2d(organ, RAW / "breast" / "images", RAW / "breast" / "masks", "*.png", lambda p: p.name, counter)
            else:
                rows = []
        all_rows.extend(rows)
        counter = len(all_rows)

    with (OUT / "index.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["split", "organ", "image", "mask", "has_mask", "source"])
        w.writeheader()
        w.writerows(all_rows)

    yaml_cfg = OUT / "yolo_cfg" / "data.yaml"
    yaml_cfg.parent.mkdir(parents=True, exist_ok=True)
    yaml_cfg.write_text(
        "path: {}\n".format((OUT).resolve()) +
        "train: images/train\nval: images/val\n\n" +
        "names:\n" + "\n".join(f"  {i}: {n}" for i, n in enumerate(CLASSES)) + "\n"
    )

    print(f"\nTOTAL {len(all_rows)} samples -> {OUT}")


if __name__ == "__main__":
    main()