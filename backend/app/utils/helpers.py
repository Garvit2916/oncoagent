"""Utility helper functions."""

import base64
import io
import json
import time
from pathlib import Path
from typing import Any, Optional
from PIL import Image
import numpy as np


def encode_image_to_base64(image_array: np.ndarray) -> str:
    """Convert a numpy array image to base64 string."""
    buffer = io.BytesIO()
    img = Image.fromarray(image_array)
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def decode_base64_to_image(b64_string: str) -> np.ndarray:
    """Convert a base64 string to numpy array image."""
    image_data = base64.b64decode(b64_string)
    image = Image.open(io.BytesIO(image_data))
    return np.array(image)


def timer_decorator(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        return result, elapsed
    return wrapper


def measure_time(func):
    """Measure function execution time in milliseconds."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = int((time.time() - start) * 1000)
        return result, elapsed_ms
    return wrapper


def safe_json_dumps(data: Any, default: Any = None) -> str:
    """Safely convert data to JSON string."""
    try:
        return json.dumps(data, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps(default or {}, ensure_ascii=False)


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))