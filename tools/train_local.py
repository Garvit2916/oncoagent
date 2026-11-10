"""Local CPU baseline training for OncoAgent imaging models.

Trains the backend's exact Attention-U-Net (tumor segmentation) and an
ultralytics YOLOv8n (organ detection) on the prepared real dataset, then
writes weights to backend/models/unet_best.pth and yolo_best.pt.

Usage:
  python tools/train_local.py --only unet --epochs 12
  python tools/train_local.py --only yolo --epochs 30 --imgsz 256
  python tools/train_local.py --epochs 12 --yolo-epochs 25
"""

import argparse
import csv
import random
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT_DIR = ROOT / "data" / "training"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CLASSES = ["Liver", "Lung", "Pancreas", "Colon", "Brain", "Breast"]

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


def load_rows(split: str) -> list[dict]:
    rows = []
    with (PROC / "index.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            if r["split"] == split:
                rows.append(r)
    return rows


def read_pair(row: dict, size: int, clahe=True) -> tuple[np.ndarray, np.ndarray]:
    img = cv2.imread(str(PROC / row["image"]), cv2.IMREAD_GRAYSCALE)
    if img is None:
        img = np.zeros((size, size), np.uint8)
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_LINEAR)
    msk = np.zeros((size, size), np.uint8)
    if row["mask"]:
        m = cv2.imread(str(PROC / row["mask"]), cv2.IMREAD_GRAYSCALE)
        if m is not None:
            msk = cv2.resize(m, (size, size), interpolation=cv2.INTER_NEAREST)
    if clahe and int(row["has_mask"]):
        cla = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = cla.apply(img)
    return img, (msk > 0).astype(np.uint8)


def dice_score(pred: torch.Tensor, target: torch.Tensor, eps=1e-6) -> float:
    pred = (pred >= 0.5).float()
    inter = (pred * target).sum()
    return float((2 * inter + eps) / (pred.sum() + target.sum() + eps))


def dice_loss(pred_sig: torch.Tensor, target: torch.Tensor, eps=1e-6) -> torch.Tensor:
    inter = (pred_sig * target).sum()
    return 1 - (2 * inter + eps) / (pred_sig.sum() + target.sum() + eps)


def build_balanced(rows: list[dict], cap: int) -> list[dict]:
    from collections import defaultdict

    by_organ = defaultdict(list)
    for r in rows:
        by_organ[r["organ"]].append(r)
    per = max(1, cap // len(by_organ))
    picks = []
    for g in by_organ.values():
        rng = random.Random(SEED)
        rng.shuffle(g)
        picks.extend(g[:per])
    return picks[:cap]


def train_unet(epochs: int):
    sys = __import__("sys")
    sys.path.insert(0, str(ROOT))

    from backend.app.models.imaging.unet_architecture import AttentionEnhancedUNet

    train_rows = load_rows("train")
    val_rows = load_rows("val")
    test_rows = load_rows("test")

    def load_split(rows):
        imgs, msks = [], []
        for r in rows:
            img, msk = read_pair(r, 128)
            imgs.append(img)
            msks.append(msk)
        imgs = np.stack(imgs).astype(np.float32) / 255.0
        msks = np.stack(msks).astype(np.float32)
        return torch.from_numpy(imgs[:, None]), torch.from_numpy(msks[:, None])

    print(f"[unet] train {len(train_rows)} val {len(val_rows)} test {len(test_rows)}")
    train_rows = build_balanced(train_rows, 9000)
    xt, yt = load_split(train_rows)
    xv, yv = load_split(val_rows[:1500])
    print(f"[unet] balanced train {len(xt)}", flush=True)
    N = len(xt)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AttentionEnhancedUNet(in_channels=1, out_channels=1).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=8e-4, weight_decay=1e-4)
    sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=epochs * (N // 32 + 1))
    best_dice, best_state = 0.0, None
    t0 = time.time()

    for ep in range(1, epochs + 1):
        model.train()
        order = torch.randperm(N)
        total_loss, steps = 0.0, 0
        for i in range(0, N, 32):
            idx = order[i : i + 32]
            xb, yb = xt[idx].to(device), yt[idx].to(device)
            if np.random.rand() < 0.5:
                xb = torch.flip(xb, dims=[3])
                yb = torch.flip(yb, dims=[3])
            if np.random.rand() < 0.5:
                xb = torch.flip(xb, dims=[2])
                yb = torch.flip(yb, dims=[2])
            pos = float(yb.sum())
            pos_w = torch.tensor(max((yb.numel() - pos) / max(pos, 1.0), 1.0), device=device)
            bce = nn.BCEWithLogitsLoss(pos_weight=pos_w)
            opt.zero_grad()
            logits = model(xb)
            loss = bce(logits, yb) + dice_loss(torch.sigmoid(logits), yb)
            loss.backward()
            opt.step()
            total_loss += float(loss.item())
            steps += 1
        sch.step()

        model.eval()
        scores = []
        recalls = []
        with torch.no_grad():
            for i in range(0, len(xv), 32):
                xb, yb = xv[i : i + 32].to(device), yv[i : i + 32].to(device)
                pred = torch.sigmoid(model(xb))
                scores.append(dice_score(pred, yb))
                pred_b = (pred >= 0.5).float()
                tp = (pred_b * yb).sum()
                recalls.append(float(tp / max(yb.sum(), 1)))
        val_dice = float(np.mean(scores))
        val_recall = float(np.mean(recalls))
        print(f"[unet] epoch {ep}/{epochs} loss {total_loss/steps:.4f} val_dice {val_dice:.4f} val_recall {val_recall:.3f} ({time.time()-t0:.0f}s)", flush=True)
        if val_dice > best_dice:
            best_dice = val_dice
            best_state = {k: v.float().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        dest = ROOT / "backend" / "models" / "unet_best.pth"
        torch.save(best_state, str(dest))
        print(f"[unet] saved best (val_dice {best_dice:.4f}) -> {dest}")

    xt2, yt2 = load_split(test_rows)
    model.load_state_dict(best_state)
    model.eval()
    scores = []
    with torch.no_grad():
        for i in range(0, len(xt2), 32):
            xb, yb = xt2[i : i + 32].to(device), yt2[i : i + 32].to(device)
            scores.append(dice_score(torch.sigmoid(model(xb)), yb))
    print(f"[unet] FINAL test dice {np.mean(scores):.4f}", flush=True)


def train_yolo(epochs: int, imgsz: int, batch: int, cap: int = 1200, full: bool = False):
    import shutil

    from ultralytics import YOLO

    if full:
        yaml_path = str(PROC / "yolo_cfg" / "data.yaml")
        name = "oncoagent_yolo_full"
        print(f"[yolo] FULL dataset run ({yaml_path})", flush=True)
    else:

        def copy_subset(rows: list[dict], split: str, per: int):
            dst_img = YOLO_SUB / "images" / split
            dst_lbl = YOLO_SUB / "labels" / split
            dst_img.mkdir(parents=True, exist_ok=True)
            dst_lbl.mkdir(parents=True, exist_ok=True)

            from collections import defaultdict

            by_organ = defaultdict(list)
            for r in rows:
                by_organ[r["organ"]].append(r)
            out = []
            for g in by_organ.values():
                rng = random.Random(SEED + len(out))
                rng.shuffle(g)
                for r in g[:per]:
                    src_img, src_lbl = PROC / r["image"], PROC / "labels" / Path(r["image"]).parent.name / (Path(r["image"]).stem + ".txt")
                    if not src_lbl.exists():
                        continue
                    shutil.copyfile(str(src_img), str(dst_img / Path(r["image"]).name))
                    shutil.copyfile(str(src_lbl), str(dst_lbl / (Path(r["image"]).stem + ".txt")))
                    out.append(r)
            return out

        YOLO_SUB = ROOT / "data" / "processed" / "yolo_subset"
        if YOLO_SUB.exists():
            shutil.rmtree(YOLO_SUB)
        YOLO_SUB.mkdir(parents=True)

        per_train = max(1, cap // 6)
        per_val = 150
        copy_subset(load_rows("train"), "train", per_train)
        n_val = copy_subset(load_rows("val"), "val", per_val)
        print(f"[yolo] subset train ~{6 * per_train} val {len(n_val)}", flush=True)

        (YOLO_SUB / "data.yaml").write_text(
            "path: {}\n".format(YOLO_SUB.resolve()) +
            "train: images/train\nval: images/val\n\n" +
            "names:\n" + "\n".join(f"  {i}: {n}" for i, n in enumerate(CLASSES)) + "\n"
        )

        yaml_path = str(YOLO_SUB / "data.yaml")
        name = "oncoagent_yolo"

    yolo = YOLO("yolov8n.yaml")
    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"[yolo] device {device} ({torch.cuda.get_device_name(0) if device == '0' else 'CPU'})", flush=True)
    yolo.train(
        data=yaml_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        name=name,
        project=str(OUT_DIR / "yolo_runs"),
        patience=8,
        cache=False,
        workers=0,
        verbose=True,
    )
    best = Path(OUT_DIR / "yolo_runs" / "oncoagent_yolo" / "weights" / "best.pt")
    if best.exists():
        dest = ROOT / "backend" / "models" / "yolo_best.pt"
        import shutil

        shutil.copyfile(str(best), str(dest))
        print(f"[yolo] saved -> {dest}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["unet", "yolo"], default=None)
    ap.add_argument("--epochs", type=int, default=24)
    ap.add_argument("--yolo-epochs", type=int, default=25)
    ap.add_argument("--imgsz", type=int, default=224)
    ap.add_argument("--batch", type=int, default=24)
    ap.add_argument("--yolo-cap", type=int, default=1200)
    ap.add_argument("--yolo-full", action="store_true")
    args = ap.parse_args()

    if args.only in (None, "unet"):
        train_unet(args.epochs)
    if args.only in (None, "yolo"):
        train_yolo(args.yolo_epochs, args.imgsz, args.batch, args.yolo_cap, args.yolo_full)


if __name__ == "__main__":
    main()