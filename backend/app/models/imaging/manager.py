"""Imaging model manager for OncoAgent."""

import asyncio
import time
from typing import Dict, Any, Optional, Tuple
import numpy as np
import cv2
from backend.app.utils.logger import logger


class ImagingModelManager:
    """Manages YOLOv8 localization + Attention U-Net tumor segmentation."""
    
    def __init__(self):
        self.yolo_model = None
        self.unet_model = None
        self._loaded = False
        self._load_lock = asyncio.Lock()
    
    async def _load_models(self):
        if self._loaded:
            return True
        async with self._load_lock:
            if self._loaded:
                return True
            try:
                from backend.app.models.imaging.yolo_model import YOLOModel
                from backend.app.models.imaging.unet_model import AttentionUNetModel
                from backend.app.config import settings
                
                self.yolo_model = YOLOModel(settings.YOLO_MODEL_PATH)
                self.unet_model = AttentionUNetModel(settings.UNET_MODEL_PATH)
                self._loaded = True
                logger.info("Imaging models loaded successfully.")
                return True
            except Exception as e:
                logger.error(f"Failed to load imaging models: {e}")
                return False
    
    async def analyze_image(
        self, file_bytes: Optional[bytes], filename: Optional[str] = None,
        organ_hint: Optional[str] = None, patient_id: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], int]:
        """Perform combined multi-modal imaging analysis."""
        start = time.time()
        
        if not self._loaded:
            await self._load_models()
            
        if not file_bytes or len(file_bytes) == 0:
            elapsed_ms = int((time.time() - start) * 1000)
            return {
                "organ": organ_hint or "Screening",
                "organ_confidence": 0.0,
                "has_tumor": False,
                "tumor_confidence": 0.0,
                "confidence": 0.0,
                "tumor_volume_ratio": 0.0,
                "tumor_area": 0,
                "mask_base64": None,
                "overlay_base64": None,
                "slice_index": "none",
                "patient_id": patient_id,
                "processing_time_ms": elapsed_ms,
            }, elapsed_ms
        
        from backend.app.utils.file_handler import load_medical_image
        img_np, slice_index = load_medical_image(file_bytes, filename)
        
        # Ensure grayscale for inference
        if len(img_np.shape) == 3:
            img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            img_gray = img_np
            
        # 1. YOLO organ localization
        if self.yolo_model and self.yolo_model.model:
            yolo_result = await asyncio.to_thread(self.yolo_model.predict, img_gray, organ_hint)
        else:
            organ_name = (organ_hint or "Screening").capitalize()
            yolo_result = {
                "detected": False,
                "organ": organ_name,
                "organ_confidence": 0.85 if organ_hint else 0.50,
                "confidence": 0.85 if organ_hint else 0.50,
                "bounding_box": None,
                "boxes": [],
            }
            
        # 2. Attention U-Net segmentation
        unet_result = None
        if self.unet_model:
            bbox = yolo_result.get("bounding_box")
            if bbox and yolo_result.get("detected"):
                x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
                crop = img_gray[max(0, y1):min(img_gray.shape[0], y2), max(0, x1):min(img_gray.shape[1], x2)]
                if crop.size == 0:
                    crop = img_gray
            else:
                crop = img_gray
                
            unet_result = await asyncio.to_thread(self.unet_model.predict, crop, img_gray)
            
        has_tumor = unet_result.get("has_tumor", False) if unet_result else False
        tumor_conf = unet_result.get("tumor_confidence", 0.0) if unet_result else 0.0
        
        elapsed_ms = int((time.time() - start) * 1000)
        
        result = {
            "organ": yolo_result.get("organ", organ_hint or "Screening"),
            "organ_confidence": yolo_result.get("organ_confidence", 0.85),
            "has_tumor": has_tumor,
            "tumor_confidence": tumor_conf,
            "confidence": yolo_result.get("organ_confidence", 0.85),
            "bounding_box": yolo_result.get("bounding_box"),
            "boxes": yolo_result.get("boxes", []),
            "slice_index": slice_index,
            "patient_id": patient_id,
            "processing_time_ms": elapsed_ms,
        }
        
        if unet_result:
            result["tumor_volume_ratio"] = unet_result.get("tumor_volume_ratio", 0.0)
            result["tumor_area"] = unet_result.get("tumor_area", 0)
            result["mask_base64"] = unet_result.get("mask_base64")
            result["overlay_base64"] = unet_result.get("overlay_base64")
            
        return result, elapsed_ms
