---
title: OncoAgent
emoji: 🧬
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Multi-agent AI cancer screening across 6 organs
---

# OncoAgent — Multi-Agent Cancer Diagnostic Orchestrator

A multi-modal, multi-agent cancer diagnostic system combining medical imaging (YOLOv8 + U-Net), symptom risk assessment (ensemble ML), PubMed literature RAG, and clinical advisory — orchestrated via LangGraph with a FastAPI backend and React frontend.

## Features

- **Imaging Agent**: YOLOv8 for organ/tumor detection + Attention U-Net for pixel-level segmentation across 6 organs (liver, lung, pancreas, colon, brain, breast)
- **Symptom Agent**: ML ensemble lung cancer risk assessment from clinical symptoms
- **Literature Agent**: PubMed RAG pipeline with FAISS vector store for evidence-based research
- **Advisory Agent**: Patient-friendly clinical recommendations and specialist referrals
- **Synthesis Agent**: LangGraph orchestration combining all agent findings into unified reports

## Tech Stack

- **Backend**: Python 3.11, FastAPI, LangGraph, SQLAlchemy, FAISS
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **ML Models**: PyTorch (YOLOv8, U-Net), scikit-learn
- **LLM**: Google Gemini 2.0 Flash (free) with Ollama fallback
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (local)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### Installation

1. Clone and enter the project:
```bash
cd OncoAgent
```

2. Install backend dependencies:
```bash
pip install -r backend/requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Configure environment (optional):
```bash
cp .env.example .env
# Edit .env to add your Gemini API key (optional)
```

### Running

1. Start the backend:
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

2. Start the frontend:
```bash
cd frontend
npm run dev
```

3. Open http://localhost:5173 in your browser

### Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/imaging` | Run imaging analysis (YOLO + U-Net) |
| POST | `/api/v1/symptoms` | Run symptom risk assessment |
| POST | `/api/v1/literature` | Search medical literature (PubMed) |
| POST | `/api/v1/consultation` | Full multi-agent synthesis |

## Project Structure

```
OncoAgent/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agent implementations
│   │   ├── core/            # LangGraph orchestrator
│   │   ├── database/        # SQLAlchemy models
│   │   ├── models/          # ML model wrappers
│   │   ├── rag/             # PubMed RAG pipeline
│   │   ├── schemas/         # Pydantic schemas
│   │   └── utils/           # Utilities
│   ├── models/              # Model weights
│   └── data/                # Training data
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── services/        # API client
│   │   └── components/      # Shared components
│   └── ...
└── docs/                    # Documentation
```

## Disclaimer

This AI system is for informational and educational purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.

## License

MIT