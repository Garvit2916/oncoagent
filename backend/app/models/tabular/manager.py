"""Symptom model manager for OncoAgent."""

import asyncio
import time
from typing import Dict, Any, Tuple
from backend.app.utils.logger import logger


class SymptomModelManager:
    """Manages the symptom risk assessment model."""
    
    def __init__(self):
        self._loaded = False
        self._load_lock = asyncio.Lock()
    
    async def _load_model(self):
        """Warm up / load the symptom ensemble model."""
        if self._loaded:
            return True
        async with self._load_lock:
            if self._loaded:
                return True
            try:
                from backend.app.models.tabular.symptom_model import get_loaded_model
                model = await asyncio.to_thread(get_loaded_model)
                self._loaded = True
                if model:
                    logger.info("Symptom ensemble model ready.")
                else:
                    logger.warning("Symptom model loaded in fallback rule-based mode.")
                return True
            except Exception as e:
                logger.error(f"Failed to load symptom model: {e}")
                self._loaded = True
                return False
    
    async def assess_risk(self, input_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Assess lung cancer risk from clinical symptoms."""
        start = time.time()
        if not self._loaded:
            await self._load_model()
            
        try:
            from backend.app.models.tabular.symptom_model import predict_risk
            result = await asyncio.to_thread(predict_risk, input_data)
        except Exception as e:
            logger.error(f"Symptom assessment failed: {e}")
            from backend.app.models.tabular.symptom_model import _rule_based_fallback
            result = _rule_based_fallback(input_data)
            
        elapsed_ms = int((time.time() - start) * 1000)
        result["processing_time_ms"] = elapsed_ms
        return result, elapsed_ms