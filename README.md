# SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform

> **"One Search. Every Camera. Complete Movement Intelligence."**
> Target: **Gujarat Police Innovation Challenge 2026**

---

## 📌 Executive Summary
SentinelX is a zero-cost (₹0 SaaS/API licensing), local-first, vendor-neutral cross-camera vehicle intelligence and unified CCTV analytics platform designed to solve large-scale CCTV interoperability challenges across heterogeneous cameras and VMS deployments.

### Key Capabilities
- **Dynamic Sentinel Catalog Ingestion**: Discovers live sandbox feeds dynamically (`GET /api/ingest`).
- **Real-Time Stream Resilience**: RTSP over TCP with bounded frame queues, drop-on-lag backpressure, and exponential reconnect.
- **AI Vehicle Detection & ANPR**: Permissively licensed object detection, ByteTrack tracking, PaddleOCR plate extraction, and strict Indian license plate normalization.
- **Cross-Camera Correlation Engine**: Multi-camera journey reconstruction with travel-time plausibility filters and appearance Re-ID.
- **Unified Command Center**: Real-time Leaflet GIS mapping, timeline reconstruction, automated watchlist matching, instant in-app WebSocket alerts, and cryptographic SHA-256 evidence integrity logging.

---

## 🏛️ High-Level Architecture

```
                    SENTINEL CAMERA CATALOG (/api/ingest)
                                     |
                                     v
                            CAMERA REGISTRY
                                     |
                                     v
                              STREAM MANAGER
                                     |
                      +--------------+--------------+
                      |                             |
                      v                             v
                LIVE VIDEO                    AI PROCESSING
                PREVIEW                       PIPELINE
              (WHEP / HLS)                   (RTSP / TCP)
                      |                             |
                      |                  +----------+----------+
                      |                  |          |          |
                      |                  v          v          v
                      |              Detection   Tracking    ANPR
                      |                  |          |          |
                      |                  +----------+----------+
                      |                             |
                      |                             v
                      |                      VEHICLE EVENTS
                      |                             |
                      |                     +-------+-------+
                      |                     |               |
                      |                     v               v
                      |               VEHICLE RE-ID     EMBEDDINGS
                      |                     |               |
                      |                     +-------+-------+
                      |                             |
                      |                             v
                      |                    CORRELATION ENGINE
                      |                             |
                      |                 +-----------+-----------+
                      |                 |           |           |
                      |                 v           v           v
                      |             TIMELINE     WATCHLIST     GIS
                      |                 |           |           |
                      |                 +-----------+-----------+
                      |                             |
                      |                             v
                      |                       ALERT ENGINE (WebSocket)
                      |                             |
                      +-----------------------------+
                                                    |
                                                    v
                                         REACT COMMAND CENTER UI
```

---

## 🛠️ Technology Stack (100% Free & Open-Source)

- **Frontend**: React 18/19, TypeScript, Vite, Tailwind CSS, Leaflet GIS.
- **Backend**: Python 3.12, FastAPI, Uvicorn, SQLAlchemy (asyncio), Pydantic v2.
- **Database**: PostgreSQL 16 + PostGIS + pgvector (SQLite fallback for local unit tests).
- **Cache & Fast State**: Valkey / Redis streams.
- **AI & Vision**: OpenCV, ByteTrack, PaddleOCR, YOLOX / ONNX Runtime.
- **Testing**: Pytest, Vitest, Ruff linter, TypeScript compiler.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- (Optional for full containerization) Docker & Docker Compose

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

The SentinelX command center will be available at `http://localhost:5173`.
Backend API docs available at `http://localhost:8000/docs`.

---

## 📜 Documentation & Progress
- [Implementation Progress Document](file:///docs/IMPLEMENTATION_PROGRESS.md)
- [Third-Party Notices](file:///THIRD_PARTY_NOTICES.md)
- [Model Licenses](file:///MODEL_LICENSES.md)
