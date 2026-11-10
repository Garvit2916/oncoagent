"""OncoAgent FastAPI Backend - Multi-Agent Cancer Diagnostic System."""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi import Request
import uvicorn
import os
import sys
import asyncio
import time
import json
import math
import urllib.request
import urllib.parse
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.config import settings
from backend.app.utils.logger import setup_logger, logger
from backend.app.agents.base import AgentManager
from backend.app.rag.pipeline import RAGPipeline
from backend.app.database.models import init_db
from backend.app.schemas import (
    ImagingResult, SymptomRiskInput, SymptomRiskOutput,
    LiteratureSearch, LiteratureSearchResponse, ConsultationRequest, ConsultationResponse
)

app = FastAPI(
    title="OncoAgent API",
    description="Multi-Agent Cancer Diagnostic Orchestration System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _release_memory():
    """Return freed heap pages to the OS (keeps small-RAM hosts stable after inference)."""
    try:
        import gc
        import ctypes

        gc.collect()
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except (OSError, AttributeError, ValueError):
        pass


@app.middleware("http")
async def trim_memory_after_inference(request: Request, call_next):
    """Heavy model inference fragments the heap; release it back after POST responses."""
    response = await call_next(request)
    if request.method == "POST" and request.url.path.startswith("/api/"):
        _release_memory()
    return response

# Global instances
agent_manager = AgentManager()
rag_pipeline = RAGPipeline()

# Initialize database
engine, SessionLocal = init_db()

# Sample scans directory
SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "tests" / "sample_scans"

# ─────────────────────────────────────────────
#  Root & Health
# ─────────────────────────────────────────────

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    # Single-origin hosting: serve the built React SPA from FastAPI.
    # Mount assets now (no conflicts); the SPA fallback route is appended at
    # the very end of this module so every API route keeps priority.
    from fastapi.staticfiles import StaticFiles
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")
else:
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        """Root endpoint with API overview (dev mode, no frontend build present)."""
        return HTMLResponse(content=API_OVERVIEW_HTML)

API_OVERVIEW_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>OncoAgent API v2.0</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #0f172a; color: #e2e8f0; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; }
        h1 { color: #38bdf8; } h2 { color: #94a3b8; }
        code { background: #0f172a; padding: 2px 8px; border-radius: 4px; font-family: monospace; color: #7dd3fc; }
        .endpoint { margin: 8px 0; padding: 10px; background: #0f172a; border-left: 3px solid #38bdf8; border-radius: 4px; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 12px; font-weight: 600; }
        .post { background: #1d4ed8; color: white; }
        .get  { background: #15803d; color: white; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🧬 OncoAgent API v2.0</h1>
        <p><strong>Status:</strong> ✅ Running</p>
        <p><strong>Description:</strong> Multi-Agent AI Cancer Diagnostic Orchestration — Imaging (YOLO + U-Net) + Symptom ML + PubMed RAG + Clinical Advisory</p>
        <p><a href="/docs" style="color:#38bdf8">📚 Swagger UI</a> &nbsp; <a href="/redoc" style="color:#38bdf8">📖 ReDoc</a></p>
    </div>
    <div class="card">
        <h2>🔗 Endpoints</h2>
        <div class="endpoint"><span class="badge post">POST</span> <code>/api/v1/imaging</code> — YOLO organ detection + U-Net tumor segmentation</div>
        <div class="endpoint"><span class="badge post">POST</span> <code>/api/v1/symptoms</code> — Ensemble ML risk assessment</div>
        <div class="endpoint"><span class="badge post">POST</span> <code>/api/v1/literature</code> — PubMed RAG search</div>
        <div class="endpoint"><span class="badge post">POST</span> <code>/api/v1/consultation</code> — Full multi-agent synthesis (JSON)</div>
        <div class="endpoint"><span class="badge post">POST</span> <code>/api/v1/consultation/full</code> — Full consultation with image upload (multipart)</div>
        <div class="endpoint"><span class="badge get">GET</span>  <code>/api/v1/samples</code> — List verified benchmark sample scans</div>
        <div class="endpoint"><span class="badge get">GET</span>  <code>/api/v1/samples/{filename}</code> — Download a sample scan file</div>
        <div class="endpoint"><span class="badge get">GET</span>  <code>/api/v1/history</code> — Consultation history</div>
        <div class="endpoint"><span class="badge get">GET</span>  <code>/api/v1/health</code> — Health check</div>
    </div>
</body>
</html>
"""


@app.get("/api/v1/health")
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "agents": ["imaging", "symptom", "literature", "advisory", "synthesis"],
        "llm_provider": settings.LLM_PROVIDER,
        "gemini_available": settings.is_gemini_available,
        "samples_dir_exists": SAMPLES_DIR.exists(),
        "sample_count": len(list(SAMPLES_DIR.glob("*.png"))) if SAMPLES_DIR.exists() else 0,
    }


# ─────────────────────────────────────────────
#  Sample Scans
# ─────────────────────────────────────────────

SAMPLE_METADATA = [
    {"file": "real_brain_brain_22610.png",        "organ": "brain",    "has_tumor": True,  "label": "Brain MRI (BRISC) — T1c slice 22610"},
    {"file": "real_lung_lung_01186.png",          "organ": "lung",     "has_tumor": True,  "label": "Lung CT (MSD Task 06) — slice 01186"},
    {"file": "real_liver_liver_12313.png",        "organ": "liver",    "has_tumor": True,  "label": "Liver CT (MSD Task 03) — slice 12313"},
    {"file": "real_pancreas_pancreas_14799.png",  "organ": "pancreas", "has_tumor": True,  "label": "Pancreas CT (MSD Task 07) — slice 14799"},
    {"file": "real_colon_colon_25957.png",        "organ": "colon",    "has_tumor": True,  "label": "Colonoscopy (Kvasir-SEG) — img 25957"},
    {"file": "real_breast_breast_26679.png",      "organ": "breast",   "has_tumor": True,  "label": "Breast Ultrasound (BUSI) — img 26679"},
]


@app.get("/api/v1/samples")
async def list_sample_scans():
    """List all verified benchmark medical sample scans."""
    samples = []
    for meta in SAMPLE_METADATA:
        path = SAMPLES_DIR / meta["file"]
        if path.exists():
            samples.append({
                **meta,
                "size_bytes": path.stat().st_size,
                "download_url": f"/api/v1/samples/{meta['file']}",
            })
    return {"samples": samples, "count": len(samples)}


@app.get("/api/v1/samples/{filename}")
async def get_sample_scan(filename: str):
    """Download a specific sample scan by filename."""
    # Security: only allow alphanumeric, underscore, hyphen, dot
    safe = all(c.isalnum() or c in "-_." for c in filename)
    if not safe or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = SAMPLES_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Sample '{filename}' not found")
    return FileResponse(str(path), media_type="image/png", filename=filename)


# ─────────────────────────────────────────────
#  Imaging Agent
# ─────────────────────────────────────────────

@app.post("/api/v1/imaging")
async def run_imaging_agent(
    file: UploadFile = File(...),
    organ_hint: str = Form(None),
    patient_id: str = Form(None),
):
    """Run the imaging agent on uploaded medical image (YOLO + U-Net)."""
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        result = await agent_manager.run("imaging", {
            "file_bytes": contents,
            "filename": file.filename or "scan.png",
            "organ_hint": organ_hint,
            "patient_id": patient_id,
        })
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Imaging agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
#  Symptom Agent
# ─────────────────────────────────────────────

@app.post("/api/v1/symptoms")
async def run_symptom_agent(data: SymptomRiskInput):
    """Run symptom risk assessment ensemble ML model, then attach specialist,
    medication, imaging-recommendation and care-plan guidance."""
    try:
        result = await agent_manager.run("symptom", {
            "age": data.age,
            "gender": data.gender,
            "smoking": data.smoking,
            "passive_smoker": data.passive_smoker,
            "coughing_blood": data.coughing_blood,
            "chest_pain": data.chest_pain,
            "weight_loss": data.weight_loss,
            "shortness_of_breath": data.shortness_of_breath,
            "fatigue": data.fatigue,
            "clubbing": data.clubbing,
            "wheezing": data.wheezing,
            "dry_cough": data.dry_cough,
            "family_history": data.family_history,
        })

        risk_level = result.get("risk_level", "Low")
        needs_follow_up = risk_level in ("High", "Medium")

        # Advisory content (patient-friendly doctors, medications, steps) for the lung pathway.
        # High/Medium symptom risk maps to the tumor advisory so the full specialist+medication
        # guidance is returned; Low risk falls back to the low-key primary-care variant.
        advisory = await agent_manager.run("advisory", {
            "organ_name": "Lung",
            "has_tumor": needs_follow_up,
            "confidence": 0.0,
        })
        doctors = advisory.get("doctors", [])
        medications = advisory.get("medications", [])
        steps = advisory.get("simple_steps", [])

        imaging_recommendation = {
            "recommended": needs_follow_up,
            "organ": "Lung",
            "modality": "Low-dose chest CT (LDCT)",
            "reason": (
                "A symptom-only assessment captures clinical signals but cannot see tissue. "
                "Imaging locates lesions, confirms or rules out a mass, and gives the treating "
                "doctor a much higher-confidence picture of what is happening."
            ) if needs_follow_up else "No imaging is currently recommended based on this symptom profile.",
        }

        care_plan = []
        if needs_follow_up:
            care_plan.append({
                "category": "imaging",
                "title": "Confirm with medical imaging",
                "detail": f"Request a {imaging_recommendation['modality']} to visualize the lung parenchyma and localize any suspected lesion.",
            })
        if doctors:
            care_plan.append({
                "category": "referral",
                "title": f"Consult a leading specialist — {doctors[0]['name']}",
                "detail": doctors[0].get("why_visit", "Obtain a specialist evaluation of this symptom profile."),
            })
        for step in steps[:2]:
            care_plan.append({
                "category": "review",
                "title": step,
                "detail": step,
            })
        care_plan.append({
            "category": "lifestyle",
            "title": "Reduce modifiable risk today",
            "detail": "Avoid smoking and second-hand smoke, stay physically active, and keep a symptom diary to share with your doctor.",
        })

        result["recommended_next_steps"] = steps
        result["doctors_to_consult"] = doctors
        result["medications_info"] = medications
        result["suggested_specialist"] = doctors[0]["name"] if doctors else "Pulmonologist / Thoracic Oncologist"
        result["imaging_recommendation"] = imaging_recommendation
        result["care_plan"] = care_plan
        result["disclaimer"] = (
            "IMPORTANT: AI risk screening and the suggestions above (including medication "
            "information) are for educational purposes only. They are not a diagnosis and never "
            "a substitute for professional medical advice. Always consult a qualified physician "
            "before starting, stopping, or changing any treatment or medication."
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Symptom agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
#  Literature Agent
# ─────────────────────────────────────────────

@app.post("/api/v1/literature")
async def run_literature_agent(search: LiteratureSearch):
    """Run literature search agent (PubMed RAG pipeline)."""
    try:
        result = await agent_manager.run("literature", {
            "query": search.query,
            "max_results": search.max_results,
            "top_k": 4,
        })
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Literature agent error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/literature/pubmed")
async def run_literature_pubmed(search: LiteratureSearch):
    """Direct PubMed search endpoint (alias of literature agent)."""
    return await run_literature_agent(search)


# ─────────────────────────────────────────────
#  Consultation — JSON mode (pre-computed results)
# ─────────────────────────────────────────────

@app.post("/api/v1/consultation")
async def run_consultation_json(request: ConsultationRequest):
    """Full multi-agent consultation from pre-computed imaging + symptom results (JSON body)."""
    start = time.time()
    try:
        imaging_data = request.imaging_result.model_dump()
        symptom_data = request.symptom_risk.model_dump()

        advisory_task = asyncio.create_task(agent_manager.run("advisory", {
            "organ_name": imaging_data.get("organ", "Unknown"),
            "has_tumor":  imaging_data.get("has_tumor", False),
            "confidence": imaging_data.get("tumor_confidence") or 0.0,
        }))

        lit_result: dict = {}
        if request.include_literature:
            lit_result = await agent_manager.run("literature", {
                "query": f"{imaging_data.get('organ', 'lung')} cancer diagnosis treatment",
                "max_results": 4,
                "top_k": 3,
            })

        advisory_result = await advisory_task

        synthesis_result = await agent_manager.run("synthesis", {
            "imaging_result":   imaging_data,
            "symptom_result":   symptom_data,
            "advisory_result":  advisory_result,
            "literature_result": lit_result,
            "patient_id": request.patient_id,
        })

        total_ms = int((time.time() - start) * 1000)
        report = synthesis_result.get("final_report") or synthesis_result
        response = ConsultationResponse(
            patient_id=request.patient_id,
            overall_risk=report.get("overall_risk", 0),
            risk_level=report.get("risk_level", "Low"),
            suspicion_index=report.get("suspicion_index", "Low"),
            imaging_findings=imaging_data,
            symptom_findings=symptom_data,
            literature_findings=lit_result.get("context_chunks", []) if lit_result else [],
            advisory_findings=advisory_result,
            summary=report.get("summary", ""),
            critical_alerts=report.get("critical_alerts", []),
            recommended_next_steps=report.get("recommended_next_steps", []),
            doctors_to_consult=report.get("doctors_to_consult", []),
            medications_info=report.get("medications_info", []),
            overall_confidence=report.get("overall_confidence", synthesis_result.get("confidence_score", 0)),
            agent_agreement=report.get("agent_agreement", synthesis_result.get("agreement_level", 0)),
            processing_time_ms=total_ms,
            disclaimer="IMPORTANT: This AI system is for educational purposes only. Not a substitute for professional medical advice.",
        )
        return JSONResponse(content=response.model_dump())

    except Exception as e:
        logger.error(f"Consultation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
#  Consultation — Multipart mode (image upload + raw symptom values)
# ─────────────────────────────────────────────

@app.post("/api/v1/consultation/full")
async def run_full_consultation(
    file: UploadFile = File(None),
    organ_hint: str = Form("lung"),
    include_literature: str = Form("true"),
    patient_id: str = Form("anonymous"),
    age: int = Form(45),
    gender: str = Form("Male"),
    smoking: int = Form(2),
    passive_smoker: int = Form(2),
    coughing_blood: int = Form(1),
    chest_pain: int = Form(1),
    weight_loss: int = Form(1),
    shortness_of_breath: int = Form(1),
    fatigue: int = Form(1),
    clubbing: int = Form(1),
    wheezing: int = Form(1),
    dry_cough: int = Form(1),
    family_history: int = Form(1),
):
    """Full multipart consultation — accepts image upload + raw symptom sliders."""
    start = time.time()
    include_lit = include_literature.lower() in ("true", "1", "yes")

    try:
        # --- Run imaging if file present ---
        imaging_task = None
        if file and file.filename:
            contents = await file.read()
            if contents:
                imaging_task = asyncio.create_task(agent_manager.run("imaging", {
                    "file_bytes": contents,
                    "filename": file.filename,
                    "organ_hint": organ_hint,
                    "patient_id": patient_id,
                }))

        symptom_data = {
            "age": age, "gender": gender,
            "smoking": smoking, "passive_smoker": passive_smoker,
            "coughing_blood": coughing_blood, "chest_pain": chest_pain,
            "weight_loss": weight_loss, "shortness_of_breath": shortness_of_breath,
            "fatigue": fatigue, "clubbing": clubbing,
            "wheezing": wheezing, "dry_cough": dry_cough,
            "family_history": family_history,
        }

        symptom_task = asyncio.create_task(agent_manager.run("symptom", symptom_data))

        # Wait for imaging
        if imaging_task:
            imaging_result = await imaging_task
        else:
            imaging_result = {
                "organ": organ_hint.capitalize(),
                "has_tumor": False,
                "tumor_confidence": 0.0,
                "organ_confidence": 0.85,
                "mask_base64": None,
                "overlay_base64": None,
            }

        symptom_result = await symptom_task

        advisory_task = asyncio.create_task(agent_manager.run("advisory", {
            "organ_name": imaging_result.get("organ", organ_hint.capitalize()),
            "has_tumor":  imaging_result.get("has_tumor", False),
            "confidence": imaging_result.get("tumor_confidence", 0.0),
        }))

        lit_result: dict = {}
        if include_lit:
            organ_name = imaging_result.get("organ", organ_hint)
            lit_result = await agent_manager.run("literature", {
                "query": f"{organ_name} cancer diagnosis treatment clinical guidelines",
                "max_results": 4,
                "top_k": 3,
            })

        advisory_result = await advisory_task

        synthesis_result = await agent_manager.run("synthesis", {
            "imaging_result":   imaging_result,
            "symptom_result":   symptom_result,
            "advisory_result":  advisory_result,
            "literature_result": lit_result,
            "patient_id": patient_id,
        })

        total_ms = int((time.time() - start) * 1000)

        report = synthesis_result.get("final_report") or synthesis_result

        return JSONResponse(content={
            **report,
            "final_report":   report,
            "imaging_findings":   imaging_result,
            "symptom_findings":   symptom_result,
            "advisory_findings":  advisory_result,
            "literature_findings": lit_result.get("context_chunks", []) if lit_result else [],
            "processing_time_ms": total_ms,
            "overlay_base64": imaging_result.get("overlay_base64"),
            "mask_base64":    imaging_result.get("mask_base64"),
            "disclaimer": "IMPORTANT: For educational purposes only. Not a substitute for professional medical advice.",
        })

    except Exception as e:
        logger.error(f"Full consultation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
#  History
# ─────────────────────────────────────────────

@app.get("/api/v1/history")
async def get_consultation_history(limit: int = 20, offset: int = 0):
    """Return recent consultation history from SQLite database."""
    try:
        from backend.app.database.models import AnalysisHistory
        with SessionLocal() as session:
            records = (
                session.query(AnalysisHistory)
                .order_by(AnalysisHistory.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return {
                "history": [
                    {
                        "id": r.id,
                        "patient_id": r.patient_id,
                        "risk_level": r.risk_level,
                        "overall_risk": r.overall_risk,
                        "created_at": str(r.created_at),
                    }
                    for r in records
                ],
                "total": session.query(AnalysisHistory).count(),
            }
    except Exception as e:
        logger.warning(f"History fetch error: {e}")
        return {"history": [], "total": 0}


# ─────────────────────────────────────────────
#  Nearby healthcare facilities (OSM / Overpass)
# ─────────────────────────────────────────────

NEARBY_KINDS = {
    "hospital": '"amenity"~"hospital|clinic"',
    "doctor": '"healthcare"~"physician|doctor|clinic|centre|doctor_specialist"',
    "pharmacy": '"amenity"="pharmacy"',
}

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _overpass_nearest(lat: float, lon: float, radius: float, kind: str) -> list:
    tags = NEARBY_KINDS.get(kind)
    query = (
        f"[out:json][timeout:20];"
        f"(nwr[{tags}](around:{radius * 1000:.0f},{lat},{lon}););"
        f"out center tags 40;"
    )
    params = urllib.parse.urlencode({"data": query})
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            req = urllib.request.Request(
                f"{endpoint}?{params}", headers={"User-Agent": "OncoAgent/2.0 (educational research)"}
            )
            with urllib.request.urlopen(req, timeout=18) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, dict) and payload.get("elements") is not None:
                if payload["elements"]:
                    return payload["elements"]
                logger.warning(f"Overpass {endpoint.split('/')[2]} returned empty for {kind}; trying next")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Overpass attempt failed ({endpoint.split('/')[2]}): {e}")
            time.sleep(0.6)
    return []


@app.get("/api/v1/nearby")
async def nearby_healthcare(lat: float, lon: float, radius: float = 15.0, kind: str = "hospital"):
    """Return nearby hospitals / doctors / pharmacies via OpenStreetMap Overpass data."""
    kind = (kind or "hospital").lower()
    if kind not in NEARBY_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(NEARBY_KINDS)}")
    try:
        elements = await asyncio.to_thread(_overpass_nearest, lat, lon, radius, kind)
        items = []
        for el in elements:
            tags = el.get("tags", {})
            la = el.get("lat") or el.get("center", {}).get("lat")
            lo = el.get("lon") or el.get("center", {}).get("lon")
            if la is None or lo is None:
                continue
            street = tags.get("addr:street", "")
            house = tags.get("addr:housenumber", "")
            city = tags.get("addr:city", "")
            addr = ", ".join(p for p in [f"{house} {street}".strip(), city] if p)
            items.append({
                "name": tags.get("name") or tags.get("operator") or f"{kind.title()} near you",
                "kind": kind,
                "address": addr or tags.get("display_name", ""),
                "phone": tags.get("phone") or tags.get("contact:phone", ""),
                "website": tags.get("website", ""),
                "opening_hours": tags.get("opening_hours", ""),
                "lat": float(la),
                "lon": float(lo),
                "distance_km": round(_haversine_km(lat, lon, float(la), float(lo)), 2),
            })
        items.sort(key=lambda x: x["distance_km"])
        return {
            "kind": kind,
            "location": {"lat": lat, "lon": lon},
            "data_source": "OpenStreetMap / Overpass API (community data)",
            "nearby": items[:25],
        }
    except Exception as e:
        logger.error(f"Nearby lookup error: {e}", exc_info=True)
        return JSONResponse(
            status_code=502,
            content={"kind": kind, "nearby": [], "detail": "Unable to reach the healthcare locator service."},
        )


# ─────────────────────────────────────────────
#  SPA fallback (must be LAST — after every API route)
# ─────────────────────────────────────────────

if FRONTEND_DIST.is_dir():
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """Serve static files from the SPA build; fall back to index.html for
        client-side routes. API/docs paths fall through to a normal 404."""
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            raise StarletteHTTPException(status_code=404)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_DIST / "index.html"))


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)