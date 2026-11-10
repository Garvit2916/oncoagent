"""Extract BUSI (breast ultrasound) images + masks from the HuggingFace parquet mirror."""
import io
import urllib.request
from pathlib import Path

import pandas as pd
from PIL import Image

RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "breast"
RAW.mkdir(parents=True, exist_ok=True)
pq_path = RAW / "busi_train.parquet"
URL = "https://huggingface.co/datasets/MedOtter/BUSI/resolve/main/data/train-00000-of-00001.parquet"

print("downloading parquet...")
urllib.request.urlretrieve(URL, pq_path)
print("parquet size MB:", round(pq_path.stat().st_size / 1e6, 1))

df = pd.read_parquet(pq_path)
print("rows:", len(df), "cols:", list(df.columns))

im_dir = RAW / "images"
mk_dir = RAW / "masks"
im_dir.mkdir(exist_ok=True)
mk_dir.mkdir(exist_ok=True)

n = 0
for i, row in df.iterrows():
    img, msk = row["image"], row["mask"]
    if isinstance(img, dict):
        img = img.get("bytes")
    if isinstance(msk, dict):
        msk = msk.get("bytes")
    if not (img and msk):
        continue
    im = Image.open(io.BytesIO(img)).convert("L")
    mm = Image.open(io.BytesIO(msk)).convert("L")
    cls = str(row.get("class_label", "x")).replace(",", "").split()[0] if row.get("class_label") else "x"
    name = f"busi_{i:04d}_{cls}.png"
    im.save(im_dir / name)
    mm.save(mk_dir / name)
    n += 1

print("saved", n, "image+mask pairs")