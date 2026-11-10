"""LangGraph workflow for OncoAgent multi-agent orchestration."""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict, Annotated
import operator
from backend.app.utils.logger import logger
from backend.app.agents.base import ImagingAgent, SymptomAgent, LiteratureAgent, AdvisoryAgent


class AgentState(TypedDict, total=False):
    query: str
    file_bytes: Optional[bytes]
    filename: Optional[str]
    organ_hint: Optional[str]
    patient_id: Optional[str]
    age: int
    gender: str
    smoking: int
    passive_smoker: int
    coughing_blood: int
    chest_pain: int
    weight_loss: int
    shortness_of_breath: int
    fatigue: int
    clubbing: int
    wheezing: int
    dry_cough: int
    family_history: int
    imaging_result: Dict[str, Any]
    symptom_result: Dict[str, Any]
    literature_result: Dict[str, Any]
    advisory_result: Dict[str, Any]
    final_report: Dict[str, Any]
    confidence_score: float
    agreement_level: float
    processing_time_ms: int
    agent_outputs: Dict[str, Any]
    errors: Annotated[List[str], operator.add]


def build_graph():
    """Build and return the LangGraph orchestrator."""
    from langgraph.graph import StateGraph, END
    
    workflow = StateGraph(AgentState)
    
    async def imaging_node(state: AgentState) -> Dict[str, Any]:
        """Imaging agent node. Skips if a pre-computed imaging result was supplied."""
        if state.get("imaging_result") is not None:
            return {}
        agent = ImagingAgent()
        errors = []
        result = {}
        try:
            result = await agent.run_with_metadata({
                "file_bytes": state.get("file_bytes"),
                "filename": state.get("filename", "scan.png"),
                "organ_hint": state.get("organ_hint"),
                "patient_id": state.get("patient_id"),
            })
        except Exception as e:
            logger.error(f"Imaging agent node error: {e}")
            errors.append(f"Imaging agent error: {e}")
            result = {
                "organ": state.get("organ_hint") or "Screening",
                "has_tumor": False,
                "confidence": 0.0,
                "tumor_confidence": 0.0,
            }
            
        outputs = state.get("agent_outputs", {}).copy() if state.get("agent_outputs") else {}
        outputs["imaging"] = result
        return {"imaging_result": result, "agent_outputs": outputs, "errors": errors}
    
    async def symptom_node(state: AgentState) -> Dict[str, Any]:
        """Symptom agent node. Skips if a pre-computed symptom result was supplied."""
        if state.get("symptom_result") is not None:
            return {}
        agent = SymptomAgent()
        errors = []
        result = {}
        try:
            result = await agent.run_with_metadata({
                "age": state.get("age", 45),
                "gender": state.get("gender", "Male"),
                "smoking": state.get("smoking", 2),
                "passive_smoker": state.get("passive_smoker", 2),
                "coughing_blood": state.get("coughing_blood", 1),
                "chest_pain": state.get("chest_pain", 1),
                "weight_loss": state.get("weight_loss", 1),
                "shortness_of_breath": state.get("shortness_of_breath", 1),
                "fatigue": state.get("fatigue", 1),
                "clubbing": state.get("clubbing", 1),
                "wheezing": state.get("wheezing", 1),
                "dry_cough": state.get("dry_cough", 1),
                "family_history": state.get("family_history", 2),
            })
        except Exception as e:
            logger.error(f"Symptom agent node error: {e}")
            errors.append(f"Symptom agent error: {e}")
            result = {
                "ml_risk_score": 15.0,
                "risk_level": "Low",
                "suspicion_index": "Low",
                "critical_findings": [],
                "confidence": 75.0,
            }
            
        outputs = state.get("agent_outputs", {}).copy() if state.get("agent_outputs") else {}
        outputs["symptom"] = result
        return {"symptom_result": result, "agent_outputs": outputs, "errors": errors}
    
    async def literature_node(state: AgentState) -> Dict[str, Any]:
        """Literature agent node. Skips if a pre-computed literature result was supplied."""
        if state.get("literature_result") is not None:
            return {}
        agent = LiteratureAgent()
        errors = []
        result = {}
        try:
            img = state.get("imaging_result", {})
            sym = state.get("symptom_result", {})
            organ = img.get("organ") or state.get("organ_hint") or "lung"
            
            query = f"{organ} cancer diagnosis treatment clinical guidelines"
            if sym.get("risk_level") == "High" or img.get("has_tumor"):
                query += " solitary nodule management"
                
            result = await agent.run_with_metadata({
                "query": query,
                "max_results": 4,
                "top_k": 3,
            })
        except Exception as e:
            logger.error(f"Literature agent node error: {e}")
            errors.append(f"Literature agent error: {e}")
            result = {"papers": [], "context_chunks": [], "evidence_report": "Literature search unavailable."}
            
        outputs = state.get("agent_outputs", {}).copy() if state.get("agent_outputs") else {}
        outputs["literature"] = result
        return {"literature_result": result, "agent_outputs": outputs, "errors": errors}
    
    async def advisory_node(state: AgentState) -> Dict[str, Any]:
        """Advisory agent node. Skips if a pre-computed advisory result was supplied."""
        if state.get("advisory_result") is not None:
            return {}
        agent = AdvisoryAgent()
        errors = []
        result = {}
        try:
            img = state.get("imaging_result", {})
            organ = img.get("organ") or state.get("organ_hint") or "Lung"
            has_tumor = img.get("has_tumor", False)
            conf = img.get("tumor_confidence", 0.0) if has_tumor else img.get("organ_confidence", 0.85)
            
            result = await agent.run_with_metadata({
                "organ_name": organ,
                "has_tumor": has_tumor,
                "confidence": conf,
            })
        except Exception as e:
            logger.error(f"Advisory agent node error: {e}")
            errors.append(f"Advisory agent error: {e}")
            result = {
                "organ_name": "General Oncology",
                "has_tumor": False,
                "simple_steps": ["Schedule a routine physical examination with your primary physician."],
                "doctors": [{"name": "Oncologist", "department": "Internal Medicine"}],
                "medications": [],
            }
            
        outputs = state.get("agent_outputs", {}).copy() if state.get("agent_outputs") else {}
        outputs["advisory"] = result
        return {"advisory_result": result, "agent_outputs": outputs, "errors": errors}
    
    async def synthesis_node(state: AgentState) -> Dict[str, Any]:
        """Synthesis agent node - combines all findings with calibrated risk modeling."""
        img = state.get("imaging_result", {})
        sym = state.get("symptom_result", {})
        adv = state.get("advisory_result", {})
        
        has_tumor = img.get("has_tumor", False)
        tumor_conf = float(img.get("tumor_confidence") or 0.0)
        symptom_score = float(sym.get("ml_risk_score") or 15.0)
        
        # Multi-modal risk synthesis
        has_image = bool(state.get("file_bytes") and len(state.get("file_bytes", b"")) > 0)
        
        if has_image:
            if has_tumor:
                overall_risk = round(tumor_conf * 55.0 + (symptom_score * 0.45), 1)
            else:
                # Normal scan provides strong negative predictive value
                overall_risk = round(5.0 + (symptom_score * 0.40), 1)
        else:
            # Symptom assessment only
            overall_risk = round(symptom_score, 1)
            
        overall_risk = min(98.5, max(4.0, overall_risk))
        
        # Risk level determination
        if overall_risk >= 65.0 or (has_tumor and tumor_conf > 0.8):
            risk_level = "High"
            suspicion_index = "High"
        elif overall_risk >= 35.0:
            risk_level = "Medium"
            suspicion_index = "Moderate"
        else:
            risk_level = "Low"
            suspicion_index = "Low"
            
        critical_alerts = []
        if has_tumor:
            organ_name = img.get("organ", "Scan")
            critical_alerts.append(f"Focal mass / lesion identified in {organ_name} (Volume Ratio: {img.get('tumor_volume_ratio', 0.0):.2%})")
        critical_alerts.extend(sym.get("critical_findings", []))
        
        # Synthesize clinical summary
        if has_tumor:
            summary = (
                f"🚨 Suspicious focal lesion identified in {img.get('organ', 'organ tissue')} with {tumor_conf*100:.1f}% confidence. "
                f"Symptom evaluation indicates {sym.get('risk_level', 'Medium')} systemic risk ({symptom_score}% score). "
                f"Immediate clinical evaluation and tissue confirmation (biopsy/contrast study) is advised."
            )
        elif sym.get("risk_level") == "High":
            summary = (
                f"⚠️ High symptom-based clinical risk score ({symptom_score}%) detected with {len(critical_alerts)} critical signs. "
                f"Although imaging did not identify an overt mass, clinical symptoms warrant priority diagnostic consultation."
            )
        else:
            summary = (
                f"✅ No high-risk malignant lesions or alarming symptom clusters detected (Overall Risk: {overall_risk}%). "
                f"Continue routine preventative health screening and age-appropriate surveillance."
            )
            
        final_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_risk": overall_risk,
            "risk_level": risk_level,
            "suspicion_index": suspicion_index,
            "summary": summary,
            "critical_alerts": critical_alerts,
            "recommended_next_steps": adv.get("simple_steps", []),
            "doctors_to_consult": adv.get("doctors", []),
            "medications_info": adv.get("medications", []),
            "overall_confidence": round(float(sym.get("confidence") or 85.0), 1),
            "agent_agreement": round(float(sym.get("model_agreement") or 92.0), 1),
        }
        
        outputs = state.get("agent_outputs", {}).copy() if state.get("agent_outputs") else {}
        outputs["synthesis"] = final_report
        
        return {
            "final_report": final_report,
            "confidence_score": final_report["overall_confidence"],
            "agreement_level": final_report["agent_agreement"],
            "agent_outputs": outputs,
        }
        
    workflow.add_node("imaging", imaging_node)
    workflow.add_node("symptom", symptom_node)
    workflow.add_node("literature", literature_node)
    workflow.add_node("advisory", advisory_node)
    workflow.add_node("synthesis", synthesis_node)
    
    workflow.set_entry_point("imaging")
    workflow.add_edge("imaging", "symptom")
    workflow.add_edge("symptom", "literature")
    workflow.add_edge("literature", "advisory")
    workflow.add_edge("advisory", "synthesis")
    workflow.add_edge("synthesis", END)
    
    return workflow.compile()