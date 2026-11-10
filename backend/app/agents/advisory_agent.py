"""Clinical advisory agent for OncoAgent."""

import os
from typing import Dict, Any


class AdvisoryAgent:
    """Agent responsible for patient-friendly clinical advisory."""
    
    def __init__(self):
        self._advisory_module = None
    
    def _load_module(self):
        """Load the clinical advisory module."""
        if self._advisory_module is None:
            import importlib.util
            
            source_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "app",
                "agents",
                "clinical_advisory.py"
            )
            
            if os.path.exists(source_path):
                spec = importlib.util.spec_from_file_location("clinical_advisory", source_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._advisory_module = module
            else:
                raise FileNotFoundError(f"Clinical advisory module not found at {source_path}")
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run clinical advisory generation."""
        self._load_module()
        
        result = self._advisory_module.generate_clinical_summary(
            organ_name=input_data.get("organ_name", "Unknown"),
            has_tumor=input_data.get("has_tumor", False),
            confidence=input_data.get("confidence", 0),
        )
        
        return result