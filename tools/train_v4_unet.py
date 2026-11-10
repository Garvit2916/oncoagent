"""Training pass v4 for the OncoAgent U-Net (GPU).

Goal: squeeze segmentation accuracy (dice + recall) beyond v3 (test dice 0.223).

What changes vs v3:
  * Hybrid loss = pos-weighted BCE + Dice + Focal (focuses hard, tiny lesions)
  * Recall-emphasized soft Tversky term (alpha=0.3, beta=0.7) so false
    negatives are penalised harder -> higher lesion recall
  * Stronger augmentation: rotation/scale/flip + brightness-contrast jitter +
    cutout erasing; keeps one image per tile (no mixup so masks stay exact)
  * Balanced caps across all 6 organs (worst organs pancreas/lung/colon get a
    small extra weight when sampling)
  * 256 px / batch 32 / AdamW + OneCycle cosine for 40 epochs

Evaluation is identical to v3: fixed val subset (1000) for early stopping and
the same 4000-row test split for the FINAL reported numbers, so results are
directly comparable. Best weights save to backend/models/unet_best.pth.
"""

import argparse
import csv
import random
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
UNET_DEST = ROOT / "backend" / "models" / "unet_best.pth"

SEED = 2026
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

EXTRA_WEIGHT = {"pancreas": 1.30, "lung": 1.15, "colon": 1.15}


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
        w = EXTRA_WEIGHT.get(r["organ"], 1.0)
        by_organ[r["organ"]].extend([r] * int(round(w * 10)))
    per = max(1, cap // len(by_organ))
    picks = []
    rng = random.Random(SEED)
    for g in by_organ.values():
        rng.shuffle(g)
        picks.extend(g[: per + 8])
    return picks[:cap]


def augment(img, msk, size=256):
    center = (size / 2 - 0.5, size / 2 - 0.5)
    if np.random.rand() < 0.9:
        ang = np.random.uniform(-14, 14)
        M = cv2.getRotationMatrix2D(center, ang, 1.0)
        img = cv2.warpAffine(img, M, (size, size), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REFLECT_101)
        msk = cv2.warpAffine(msk, M, (size, size), flags=cv2.INTER_NEAREST, borderValue=0)
    s = np.random.uniform(0.88, 1.12)
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
    # brightness / contrast jitter on tile
    if np.random.rand() < 0.5:
        a = np.random.uniform(0.85, 1.15)
        b = np.random.uniform(-18, 18)
        img = np.clip(img.astype(np.float32) * a + b, 0, 255).astype(np.uint8)
    # cutout erasing (helps robustness to occlusions)
    if np.random.rand() < 0.4:
        eh, ew = int(size * np.random.uniform(0.06, 0.18)), int(size * np.random.uniform(0.06, 0.18))
        y0 = int(np.random.uniform(0, size - eh))
        x0 = int(np.random.uniform(0, size - ew))
        img[y0:y0 + eh, x0:x0 + ew] = 0
    return img, msk


def dice_loss(pred_sig, target, eps=1e-6):
    inter = (pred_sig * target).sum()
    return 1 - (2 * inter + eps) / (pred_sig.sum() + target.sum() + eps)


def tversky_loss(pred_sig, target, alpha=0.3, beta=0.7, eps=1e-6):
    tp = (pred_sig * target).sum()
    fp = ((1 - target) * pred_sig).sum()
    fn = (target * (1 - pred_sig)).sum()
    return 1 - (tp + eps) / (tp + alpha * fp + beta * fn + eps)


def focal_loss(logits, target, alpha=0.6, gamma=2.0):
    bce = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
    pt = torch.exp(-bce)
    mod = alpha * target + (1 - alpha) * (1 - target)
    return (mod * (1 - pt) ** gamma * bce).mean()


def dice_score(pred, target, eps=1e-6):
    pred = (pred >= 0.5).float()
    inter = (pred * target).sum()
    return float((2 * inter + eps) / (pred.sum() + target.sum() + eps))


def train_unet(epochs: int, size: int, batch: int, cap: int):
    sys.path.insert(0, str(ROOT))
    from backend.app.models.imaging.unet_architecture import AttentionEnhancedUNet

    train_rows = build_balanced(load_rows("train"), cap)
    val_rows = load_rows("val")[:1000]
    test_rows = load_rows("test")[:4000]
    log(f"[unet v4] train {len(train_rows)} val {len(val_rows)} test {len(test_rows)}")

    imgs_v, msks_v = [], []
    for r in val_rows:
        i, m = read_pair(r, size=size)
        imgs_v.append(i)
        msks_v.append(m)
    xv = torch.from_numpy(np.stack(imgs_v).astype(np.float32)[:, None] / 255.0).to("cpu")
    yv = torch.from_numpy(np.stack(msks_v).astype(np.float32)[:, None]).to("cpu")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AttentionEnhancedUNet(in_channels=1, out_channels=1).to(device)

    if UNET_DEST.exists():
        sd = torch.load(str(UNET_DEST), map_location=device)
        model.load_state_dict(sd)
        log(f"[unet v4] resumed from {UNET_DEST}")
    else:
        log("[unet v4] no prior weights; training from scratch")

    opt = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=5e-5)
    total_steps = epochs * (len(train_rows) // batch + 1)
    warm = total_steps // 20
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=1.2e-3, total_steps=total_steps, pct_start=warm / max(total_steps, 1),
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
            pos_w = torch.tensor(max((xb.numel() - pos) / max(pos, 1.0), 1.0), device=device)
            bce = nn.BCEWithLogitsLoss(pos_weight=pos_w)
            opt.zero_grad()
            logits = model(xb)
            prob = torch.sigmoid(logits)
            loss = 0.50 * bce(logits, yb) + 0.35 * tversky_loss(prob, yb) + 0.15 * focal_loss(logits, yb)
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
        log(f"[unet v4] saved best (val_dice {best_dice:.4f}) -> {UNET_DEST}")

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
        log(f"[unet v4] FINAL test dice {np.mean(scores):.4f} recall {np.mean(recalls):.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--cap", type=int, default=8000)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()
    train_unet(args.epochs, args.size, args.batch, args.cap)


if __name__ == "__main__":
    main()