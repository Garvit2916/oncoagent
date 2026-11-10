"""File handling utilities for medical images."""

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import nibabel as nib
import cv2
from PIL import Image
import io


def validate_image_file(file_bytes: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
    """Validate uploaded medical image file."""
    allowed_exts = {".png", ".jpg", ".jpeg", ".bmp", ".nii", ".nii.gz"}
    ext = ".nii.gz" if filename.lower().endswith(".nii.gz") else os.path.splitext(filename)[1].lower()
    
    if ext not in allowed_exts:
        return False, f"Invalid file extension: {ext}", None
    
    if len(file_bytes) == 0:
        return False, "File is empty", None
    
    return True, "", ext


def load_medical_image(file_bytes: Optional[bytes], filename: Optional[str] = None) -> Tuple[np.ndarray, str]:
    """Load a medical image from bytes, handling NIfTI and standard formats safely."""
    if not file_bytes or len(file_bytes) == 0:
        # Return a blank canvas if no bytes provided
        return np.zeros((512, 512), dtype=np.uint8), "empty"
        
    fn = (filename or "scan.png").lower()
    ext = ".nii.gz" if fn.endswith(".nii.gz") else os.path.splitext(fn)[1]
    
    if ext in [".nii", ".nii.gz"]:
        return _load_nifti(file_bytes, fn)
    else:
        return _load_standard_image(file_bytes)


def _load_nifti(file_bytes: bytes, filename: str) -> Tuple[np.ndarray, str]:
    """Load a NIfTI volume and extract the middle axial slice."""
    with tempfile.NamedTemporaryFile(suffix=".nii.gz" if ".nii.gz" in filename else ".nii", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    
    try:
        nii_img = nib.load(tmp_path)
        vol_data = nii_img.get_fdata()
        
        # Extract middle axial slice
        mid_idx = vol_data.shape[2] // 2
        slice_np = vol_data[:, :, mid_idx]
        
        # Normalize to 0-255
        s_min, s_max = np.percentile(slice_np, 1), np.percentile(slice_np, 99)
        slice_np = np.clip(slice_np, s_min, s_max)
        img_np = ((slice_np - s_min) / (s_max - s_min + 1e-8) * 255).astype(np.uint8)
        
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img_np = clahe.apply(img_np)
        
        # Rotate 90 degrees for proper orientation
        img_np = np.rot90(img_np)
        
        return img_np, str(mid_idx)
    finally:
        os.unlink(tmp_path)


def _load_standard_image(file_bytes: bytes) -> Tuple[np.ndarray, str]:
    """Load a standard image file (PNG, JPG, etc.) as grayscale."""
    image = Image.open(io.BytesIO(file_bytes)).convert("L")
    return np.array(image), "standard"


def estimate_tumor_volume(mask_array: np.ndarray) -> dict:
    """Estimate tumor volume metrics from a binary mask."""
    if mask_array.sum() == 0:
        return {"area": 0, "volume_ratio": 0.0, "bounding_box": None}
    
    height, width = mask_array.shape
    total_area = height * width
    tumor_area = int(mask_array.sum())
    volume_ratio = tumor_area / total_area if total_area > 0 else 0.0
    
    # Find bounding box
    rows = np.any(mask_array, axis=1)
    cols = np.any(mask_array, axis=0)
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    bbox = {
        "y_min": int(y_min), "y_max": int(y_max),
        "x_min": int(x_min), "x_max": int(x_max),
        "width": int(x_max - x_min),
        "height": int(y_max - y_min),
    }
    
    return {
        "area": tumor_area,
        "volume_ratio": round(volume_ratio, 4),
        "bounding_box": bbox,
        "diameter_approx": round(max(bbox["width"], bbox["height"]) * 0.1, 2),  # cm estimate
    }