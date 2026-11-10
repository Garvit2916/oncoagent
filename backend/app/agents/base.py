"""Base agent class for all OncoAgent agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgent(ABC):
    """Base class for all OncoAgent agents."""
    
    name: str
    description: str
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._last_output = None
    
    @abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent with given input data."""
        raise NotImplementedError
    
    async def run_with_metadata(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent and return output with metadata."""
        import time
        start = time.time()
        output = await self.run(input_data)
        elapsed_ms = int((time.time() - start) * 1000)
        output["agent_name"] = self.name
        output["agent_description"] = self.description
        output["processing_time_ms"] = elapsed_ms
        return output


class ImagingAgent(BaseAgent):
    """Agent responsible for medical image analysis (YOLO + U-Net)."""
    
    def __init__(self):
        super().__init__(
            name="Imaging Agent",
            description="Analyzes medical images (CT/MRI) for tumor detection and segmentation"
        )
        self._model_manager = None
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run imaging analysis."""
        if self._model_manager is None:
            from backend.app.models.imaging.manager import ImagingModelManager
            self._model_manager = ImagingModelManager()
        
        file_bytes = input_data.get("file_bytes")
        filename = input_data.get("filename", "scan.png")
        organ_hint = input_data.get("organ_hint")
        patient_id = input_data.get("patient_id")
        
        result, processing_time_ms = await self._model_manager.analyze_image(
            file_bytes=file_bytes,
            filename=filename,
            organ_hint=organ_hint,
            patient_id=patient_id,
        )
        
        result["processing_time_ms"] = processing_time_ms
        return result


class SymptomAgent(BaseAgent):
    """Agent responsible for symptom-based risk assessment."""
    
    def __init__(self):
        super().__init__(
            name="Symptom Agent",
            description="Assesses lung cancer risk from patient symptoms and clinical risk factors"
        )
        self._model_manager = None
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run symptom risk assessment."""
        if self._model_manager is None:
            from backend.app.models.tabular.manager import SymptomModelManager
            self._model_manager = SymptomModelManager()
        
        result, processing_time_ms = await self._model_manager.assess_risk(input_data)
        result["processing_time_ms"] = processing_time_ms
        return result


class LiteratureAgent(BaseAgent):
    """Agent responsible for literature research and evidence grounding."""
    
    def __init__(self):
        super().__init__(
            name="Literature Agent",
            description="Searches PubMed and retrieves evidence-based medical literature"
        )
        self._rag_pipeline = None
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run literature search and retrieval."""
        if self._rag_pipeline is None:
            from backend.app.rag.pipeline import RAGPipeline
            self._rag_pipeline = RAGPipeline()
        
        query = input_data.get("query", "")
        max_results = input_data.get("max_results", 5)
        top_k = input_data.get("top_k", 4)
        
        papers = self._rag_pipeline.search_literature(query, max_results=max_results)
        if papers:
            try:
                self._rag_pipeline.add_papers_to_index(papers)
            except Exception as e:
                from backend.app.utils.logger import logger
                logger.warning(f"Could not index papers to vector store: {e}")
                
        context = self._rag_pipeline.retrieve_context(query, top_k=top_k)
        
        return {
            "query": query,
            "papers": [
                {
                    "pmid": paper.pmid,
                    "title": paper.title,
                    "authors": paper.authors,
                    "journal": paper.journal,
                    "pub_date": paper.pub_date,
                    "url": paper.url,
                }
                for paper in papers
            ],
            "context_chunks": context,
            "evidence_report": self._rag_pipeline.build_evidence_report(context),
        }


class AdvisoryAgent(BaseAgent):
    """Agent responsible for patient-friendly clinical advisory."""
    
    def __init__(self):
        super().__init__(
            name="Advisory Agent",
            description="Provides patient-friendly explanations, recommended doctors, and next steps"
        )
        self._advisory_module = None
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run clinical advisory generation."""
        if self._advisory_module is None:
            try:
                from backend.app.agents.clinical_advisory import generate_clinical_summary
                self._advisory_fn = generate_clinical_summary
            except ImportError:
                self._advisory_fn = self._fallback_advisory
        
        result = self._advisory_fn(
            organ_name=input_data.get("organ_name", "Unknown"),
            has_tumor=input_data.get("has_tumor", False),
            confidence=input_data.get("confidence", 0),
        )
        
        return result
    
    def _fallback_advisory(self, organ_name: str, has_tumor: bool, confidence: float) -> Dict[str, Any]:
        """Built-in fallback advisory."""
        doctors = [
            {"name": "Oncologist", "department": "Cancer Treatment"},
            {"name": "Radiologist", "department": "Medical Imaging"},
            {"name": "Surgeon", "department": "Surgical Oncology"},
        ]
        
        steps = [
            "Schedule follow-up consultation with oncologist",
            "Complete recommended imaging studies",
            "Discuss treatment options with your care team",
        ]
        
        if has_tumor and confidence > 0.5:
            steps.insert(0, "Urgent: Schedule immediate oncology consultation")
            doctors.insert(0, {"name": "Surgical Oncologist", "department": "Surgery"})
        
        medications = [
            {"name": "N/A", "what_it_does": "No medication recommendations without full clinical evaluation", "simple_tip": "Consult your doctor for any medication questions"},
        ]
        
        return {
            "organ_name": organ_name,
            "has_tumor": has_tumor,
            "confidence": confidence,
            "simple_steps": steps,
            "doctors": doctors,
            "medications": medications,
        }


class SynthesisAgent(BaseAgent):
    """Agent responsible for synthesizing all agent findings."""
    
    def __init__(self, llm_client=None):
        super().__init__(
            name="Synthesis Agent",
            description="Integrates all agent findings into a unified clinical report"
        )
        self.llm_client = llm_client
        self._graph = None
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all agent findings."""
        if self._graph is None:
            from backend.app.core.graph import build_graph
            self._graph = build_graph()
        
        return await self._graph.ainvoke(input_data)


# Lazy agent manager
class AgentManager:
    """Manages all OncoAgent agents."""
    
    def __init__(self):
        self.agents = {}
    
    def get(self, name: str) -> BaseAgent:
        """Get an agent by name."""
        if name not in self.agents:
            if name == "imaging":
                self.agents[name] = ImagingAgent()
            elif name == "symptom":
                self.agents[name] = SymptomAgent()
            elif name == "literature":
                self.agents[name] = LiteratureAgent()
            elif name == "advisory":
                self.agents[name] = AdvisoryAgent()
            elif name == "synthesis":
                self.agents[name] = SynthesisAgent()
            else:
                raise ValueError(f"Unknown agent: {name}")
        return self.agents[name]
    
    async def run(self, agent_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single agent."""
        return await self.get(agent_name).run(input_data)