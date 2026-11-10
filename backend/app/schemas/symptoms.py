"""Schemas for symptom risk assessment endpoints."""

from pydantic import BaseModel, Field, validator
from typing import Optional, List


class RiskAssessmentRequest(BaseModel):
    """Symptom risk assessment request."""
    age: int = Field(ge=0, le=120, description="Patient age in years")
    gender: str = Field(default="Male", description="Patient gender")
    smoking: int = Field(ge=1, le=8, description="Smoking severity 1-8")
    passive_smoker: int = Field(ge=1, le=8, description="Passive smoking severity 1-8")
    coughing_blood: int = Field(ge=1, le=8, description="Coughing of blood severity 1-8")
    chest_pain: int = Field(ge=1, le=8, description="Chest pain severity 1-8")
    weight_loss: int = Field(ge=1, le=8, description="Weight loss severity 1-8")
    shortness_of_breath: int = Field(ge=1, le=8, description="Shortness of breath severity 1-8")
    fatigue: int = Field(ge=1, le=8, description="Fatigue severity 1-8")
    clubbing: int = Field(ge=1, le=8, description="Clubbing of finger nails severity 1-8")
    wheezing: int = Field(ge=1, le=8, description="Wheezing severity 1-8")
    dry_cough: int = Field(ge=1, le=8, description="Dry cough severity 1-8")
    family_history: int = Field(ge=1, le=8, description="Genetic risk factor 1-8")

    @validator("gender")
    def gender_male_or_female(cls, v):
        if v not in ("Male", "Female", "M", "F"):
            raise ValueError("Gender must be Male or Female")
        return v


class RiskAssessmentResponse(BaseModel):
    """Symptom risk assessment response."""
    ml_risk_score: float = Field(ge=0, le=100, description="ML ensemble risk score (%)")
    risk_level: str = Field(description="Low/Medium/High")
    suspicion_index: str = Field(description="Low/Moderate/High")
    critical_findings: List[str] = Field(default_factory=list, description="Critical clinical findings")
    model_agreement: float = Field(ge=0, le=100, description="ML vs clinical agreement (%)")
    confidence: float = Field(ge=0, le=100, description="Overall prediction confidence (%)")
    processing_time_ms: int = Field(ge=0, description="Processing time in ms")


class LiteratureSearchRequest(BaseModel):
    """Literature search request schema."""
    query: str = Field(..., description="Search query for PubMed/Medical literature")
    organ: Optional[str] = Field(None, description="Optional organ filter")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum number of papers to return")


class LiteraturePaper(BaseModel):
    """Single PubMed paper result."""
    pmid: str = Field(..., description="PubMed ID")
    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Author list")
    journal: str = Field(..., description="Journal name")
    pub_date: str = Field(..., description="Publication date")
    abstract: str = Field(..., description="Paper abstract")
    url: str = Field(..., description="PubMed URL")


class LiteratureSearchResponse(BaseModel):
    """Literature search response schema."""
    papers: List[LiteraturePaper] = Field(default_factory=list, description="Found papers")
    query: str
    total_found: int = Field(default=0, ge=0, description="Total papers found")


class ConsultationRequest(BaseModel):
    """Main consultation request schema."""
    imaging_result: dict = Field(..., description="Result from imaging agent")
    symptom_risk: dict = Field(..., description="Result from symptom agent")
    patient_id: Optional[str] = Field(None, description="Optional patient identifier")
    include_literature: bool = Field(default=True, description="Whether to include literature evidence")
    urgency_override: Optional[str] = Field(None, description="Manual urgency override")


class ConsultationResponse(BaseModel):
    """Main consultation response schema."""
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    overall_risk: float = Field(ge=0, le=100, description="Combined risk score (%)")
    risk_level: str = Field(description="Low/Medium/High")
    suspicion_index: str = Field(description="Low/Moderate/High")
    imaging_findings: dict = Field(default_factory=dict, description="Imaging agent conclusions")
    symptom_findings: dict = Field(default_factory=dict, description="Symptom agent conclusions")
    literature_findings: List[dict] = Field(default_factory=list, description="Key literature evidence")
    advisory_findings: dict = Field(default_factory=dict, description="Clinical advisory output")
    summary: str = Field(description="Patient-friendly summary")
    critical_alerts: List[str] = Field(default_factory=list, description="Critical action items")
    recommended_next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    doctors_to_consult: List[dict] = Field(default_factory=list, description="Recommended specialists")
    medications_info: List[dict] = Field(default_factory=list, description="Medication information (informational only)")
    overall_confidence: float = Field(ge=0, le=100, description="Overall system confidence (%)")
    agent_agreement: float = Field(ge=0, le=100, description="Agent consensus level (%)")
    processing_time_ms: int = Field(ge=0, description="Total processing time in ms")
    disclaimer: str = Field(
        description="IMPORTANT: This AI system is for informational and educational purposes only. "
                    "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
                    "Always seek the advice of your physician or other qualified health provider "
                    "with any questions you may have regarding a medical condition. "
                    "Do not disregard professional medical advice or delay in seeking it because of "
                    "content generated by this system."
    )