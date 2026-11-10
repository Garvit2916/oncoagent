"""Training pass v3 for OncoAgent imaging models (runs on GPU).

U-Net:  fine-tune from backend/models/unet_best.pth at 256px with the same
        augmentation (rotation/flip/scale), OneCycle cosine, pos-weighted
        BCE + Dice. Tracks best val dice, reports FINAL test dice, saves to
        backend/models/unet_best.pth. Wider input -> segments smaller lesions.

YOLO:   continue from backend/models/yolo_best.pt at imgsz 512 (higher
        resolution -> sharper organ boxes on small CT/MRI slices), saves the
        best weights back to backend/models/yolo_best.pt and prints final
        val mAP.

Logs go to stdout; run backgrounded and pipe to data/train_v3.log.
"""

import argparse
import csv
import random
import shutil
import sys
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
UNET_DEST = ROOT / "backend" / "models" / "unet_best.pth"
YOLO_DEST = ROOT / "backend" / "models" / "yolo_best.pt"

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


def log(msg):
    print(msg, flush=True)


def load_rows(split: str):
    rows = []
    with (PROC / "index.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            if r["split"] == split:
                rows.append(r)
    return rows


def read_pair(row, size=256):
    img = cv2.imread(str(PROC / row["image"]), cv2.IMREAD_GRAYSCALE)
    if img is None:
        img = np.zeros((size, size), np.uint8)
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_LINEAR)
    msk = np.zeros((size, size), np.uint8)
    if row["mask"]:
        m = cv2.imread(str(PROC / row["mask"]), cv2.IMREAD_GRAYSCALE)
        if m is not None:
            msk = cv2.resize(m, (size, size), interpolation=cv2.INTER_NEAREST)
    if int(row["has_mask"]):
        cla = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = cla.apply(img)
    return img, (msk > 0).astype(np.uint8)


def build_balanced(rows, cap):
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


def dice_score(pred, target, eps=1e-6):
    pred = (pred >= 0.5).float()
    inter = (pred * target).sum()
    return float((2 * inter + eps) / (pred.sum() + target.sum() + eps))


def dice_loss(pred_sig, target, eps=1e-6):
    inter = (pred_sig * target).sum()
    return 1 - (2 * inter + eps) / (pred_sig.sum() + target.sum() + eps)


def augment(img, msk, size=256):
    center = (size / 2 - 0.5, size / 2 - 0.5)
    if np.random.rand() < 0.9:
        ang = np.random.uniform(-12, 12)
        M = cv2.getRotationMatrix2D(center, ang, 1.0)
        img = cv2.warpAffine(img, M, (size, size), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REFLECT_101)
        msk = cv2.warpAffine(msk, M, (size, size), flags=cv2.INTER_NEAREST,
                             borderValue=0)
    s = np.random.uniform(0.9, 1.1)
    M = cv2.getRotationMatrix2D(center, 0, s)
    img = cv2.warpAffine(img, M, (size, size), flags=cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT_101)
    msk = cv2.warpAffine(msk, M, (size, size), flags=cv2.INTER_NEAREST, borderValue=0)
    if np.random.rand() < 0.5:
        img = cv2.flip(img, 1)
        msk = cv2.flip(msk, 1)
    if np.random.rand() < 0.5:
        img = cv2.flip(img, 0)
        msk = cv2.flip(msk, 0)
    return img, msk


def train_unet(epochs: int, size: int, batch: int, cap: int):
    sys.path.insert(0, str(ROOT))
    from backend.app.models.imaging.unet_architecture import AttentionEnhancedUNet

    train_rows = build_balanced(load_rows("train"), cap)
    val_rows = load_rows("val")[:1000]
    test_rows = load_rows("test")[:4000]

    imgs_v, msks_v = [], []
    for r in val_rows:
        i, m = read_pair(r, size=size)
        imgs_v.append(i)
        msks_v.append(m)
    xv = torch.from_numpy(np.stack(imgs_v).astype(np.float32)[:, None] / 255.0)
    yv = torch.from_numpy(np.stack(msks_v).astype(np.float32)[:, None])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AttentionEnhancedUNet(in_channels=1, out_channels=1).to(device)

    if UNET_DEST.exists():
        sd = torch.load(str(UNET_DEST), map_location=device)
        model.load_state_dict(sd)
        log(f"[unet] resumed from {UNET_DEST} at {size}px")
    else:
        log("[unet] no prior weights; training from scratch")

    opt = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=5e-5)
    total_steps = epochs * (len(train_rows) // batch + 1)
    warm = total_steps // 20
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=1.0e-3, total_steps=total_steps, pct_start=warm / max(total_steps, 1),
        anneal_strategy="cos",
    )

    best_dice, best_state = 0.0, None
    t0 = time.time()
    N = len(train_rows)
    order = np.arange(N)

    for ep in range(1, epochs + 1):
        np.random.shuffle(order)
        model.train()
        total_loss, steps = 0.0, 0
        for i in range(0, N, batch):
            idx = order[i:i + batch]
            xs, ys = [], []
            for j in idx:
                img, msk = read_pair(train_rows[j], size=size)
                img, msk = augment(img, msk, size=size)
                xs.append(img)
                ys.append(msk)
            xb = torch.from_numpy(np.stack(xs).astype(np.float32)[:, None] / 255.0).to(device)
            yb = torch.from_numpy(np.stack(ys).astype(np.float32)[:, None]).to(device)
            pos = float(yb.sum())
            pos_w = torch.tensor(max((yb.numel() - pos) / max(pos, 1.0), 1.0), device=device)
            bce = nn.BCEWithLogitsLoss(pos_weight=pos_w)
            opt.zero_grad()
            logits = model(xb)
            loss = bce(logits, yb) + dice_loss(torch.sigmoid(logits), yb)
            loss.backward()
            opt.step()
            sched.step()
            total_loss += float(loss.item())
            steps += 1

        model.eval()
        scores, recalls = [], []
        with torch.no_grad():
            for i in range(0, len(xv), batch):
                xb = xv[i:i + batch].to(device)
                yb = yv[i:i + batch].to(device)
                pred = torch.sigmoid(model(xb))
                scores.append(dice_score(pred, yb))
                pb = (pred >= 0.5).float()
                recalls.append(float((pb * yb).sum() / max(float(yb.sum()), 1.0)))
        val_dice, val_recall = float(np.mean(scores)), float(np.mean(recalls))
        log(f"[unet] ep {ep}/{epochs} loss {total_loss/steps:.4f} val_dice {val_dice:.4f} "
            f"val_recall {val_recall:.3f} lr {sched.get_last_lr()[0]:.2e} ({time.time()-t0:.0f}s)")
        if val_dice > best_dice:
            best_dice = val_dice
            best_state = {k: v.float().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        torch.save(best_state, str(UNET_DEST))
        log(f"[unet] saved best (val_dice {best_dice:.4f}) -> {UNET_DEST}")

        model.load_state_dict(best_state)
        model.eval()
        scores, recalls = [], []
        with torch.no_grad():
            for i in range(0, len(test_rows), batch):
                xs, ys = [], []
                for r in test_rows[i:i + batch]:
                    img, msk = read_pair(r, size=size)
                    xs.append(img)
                    ys.append(msk)
                xb = torch.from_numpy(np.stack(xs).astype(np.float32)[:, None] / 255.0).to(device)
                yb = torch.from_numpy(np.stack(ys).astype(np.float32)[:, None]).to(device)
                pred = torch.sigmoid(model(xb))
                scores.append(dice_score(pred, yb))
                pb = (pred >= 0.5).float()
                recalls.append(float((pb * yb).sum() / max(float(yb.sum()), 1.0)))
        log(f"[unet] FINAL test dice {np.mean(scores):.4f} recall {np.mean(recalls):.3f}")


def train_yolo(epochs: int, imgsz: int, batch: int):
    from ultralytics import YOLO

    if not YOLO_DEST.exists():
        raise FileNotFoundError(f"{YOLO_DEST} missing - need pretrained weights to continue")
    yaml_path = str(PROC / "yolo_cfg" / "data.yaml")
    device = "0" if torch.cuda.is_available() else "cpu"
    log(f"[yolo] continue from {YOLO_DEST} at imgsz {imgsz} on {device} "
        f"({torch.cuda.get_device_name(0) if device == '0' else 'CPU'})")
    yolo = YOLO(str(YOLO_DEST))
    yolo.train(
        data=yaml_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        name="oncoagent_yolo_v3",
        project=str(OUT_DIR / "yolo_runs3"),
        patience=10,
        cache=False,
        workers=0,
        verbose=False,
        plots=False,
        exist_ok=True,
    )
    best = Path(OUT_DIR / "yolo_runs3" / "oncoagent_yolo_v3" / "weights" / "best.pt")
    if best.exists():
        shutil.copyfile(str(best), str(YOLO_DEST))
        log(f"[yolo] saved -> {YOLO_DEST}")
    res = Path(OUT_DIR / "yolo_runs3" / "oncoagent_yolo_v3" / "results.csv")
    if res.exists():
        with res.open() as f:
            rows = list(csv.DictReader(f))
        last = rows[-1]
        log(f"[yolo] final val mAP50 {float(last.get('metrics/mAP50(B)', 0.0)):.4f} "
            f"mAP50-95 {float(last.get('metrics/mAP50-95(B)', 0.0)):.4f} "
            f"P {float(last.get('metrics/precision(B)', 0.0)):.4f} R {float(last.get('metrics/recall(B)', 0.0)):.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["unet", "yolo"], default=None)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--epochs", type=int, default=45)
    ap.add_argument("--cap", type=int, default=8000)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--yolo-epochs", type=int, default=30)
    ap.add_argument("--imgsz", type=int, default=512)
    ap.add_argument("--yolo-batch", type=int, default=8)
    args = ap.parse_args()

    if args.only in (None, "unet"):
        train_unet(args.epochs, args.size, args.batch, args.cap)
    if args.only in (None, "yolo"):
        train_yolo(args.yolo_epochs, args.imgsz, args.yolo_batch)


if __name__ == "__main__":
    main()