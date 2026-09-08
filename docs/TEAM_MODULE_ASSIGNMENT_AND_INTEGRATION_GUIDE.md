# SentinelX — 3-Member Team Implementation & Git Integration Guide

> **Target:** Gujarat Police Innovation Challenge 2026  
> **Project:** SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform  
> **Repository:** `https://github.com/ManageMatic/SentinelX-Cross-Camera-Vehicle-Intelligence-Unified-CCTV-Analytics-Platform.git`  
> **Policy:** ₹0 Cost — 100% Free & Open-Source — Zero Hardcoded Camera URLs

---

## 📌 Executive Overview

To build SentinelX quickly, reliably, and without Git merge conflicts, the remaining modules (Module 4 through Module 28) are divided among **3 Developer Tracks**.

Each team member works on their assigned feature branch, verifies their code with automated tests and linter before pushing, and merges into `main` using standardized interfaces.

```
                     SENTINELX MASTER ARCHITECTURE
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
 DEVELOPER 1                  DEVELOPER 2                  DEVELOPER 3
[Core Backend, Stream        [AI/CV Pipeline, ANPR,       [Frontend Command Center,
 Ingestion & Security]        Re-ID & Correlation]         GIS Maps & Live UI]
```

---

## 👥 Team Member Track Assignments

### 🛡️ Developer 1: Core Backend, Stream Ingestion & Security Engineer
* **Feature Branch:** `feature/backend-ingestion-security`
* **Primary Directories:** `backend/app/api/v1/`, `backend/app/services/`, `ingestion/`, `deployment/`

| Module # | Module Name | Exact Responsibilities & Deliverables |
|---|---|---|
| **Module 5** | **Sentinel Camera Catalog Integration** | Build dynamic client consuming `GET /api/ingest`. Parse camera IDs, RTSP/WHEP/HLS URLs, and sync with `cameras` table. |
| **Module 6** | **Camera Registry Management (Backend)** | Camera CRUD endpoints (`/api/v1/cameras`), status toggles (online/offline), department filters. |
| **Module 7** | **Live Stream Manager** | RTSP/TCP worker using OpenCV/FFmpeg, exponential backoff reconnection (1s → 30s), PTS timestamps, bounded queues. |
| **Module 18** | **Watchlist Management (Backend)** | CRUD endpoints for Watchlists and Watchlist Entries (`/api/v1/watchlists`). |
| **Module 19** | **Real-Time Alert Engine (WebSocket)** | WebSocket server (`/ws/alerts`), match detections against active watchlists, broadcast instant alerts. |
| **Module 20** | **Evidence Vault & Integrity (Backend)** | Evidence upload & retrieval APIs (`/api/v1/evidence`), compute SHA-256 hash, verify integrity. |
| **Module 21** | **Authentication & RBAC** | Argon2id password hashing, JWT creation & verification, role dependencies (`Admin`, `Operator`, `Investigator`, `Viewer`). |
| **Module 22** | **Audit Logging & Security Hardening** | Interceptor / service logging all searches, edits, alert acknowledgments, and exports to `audit_logs`. |
| **Module 26** | **Docker Multi-Container Deployment** | Finalize `docker-compose.yml`, backend & frontend Dockerfiles, persistent volumes. |

---

### 🧠 Developer 2: AI, Computer Vision & Analytics Engineer
* **Feature Branch:** `feature/ai-anpr-correlation`
* **Primary Directories:** `ai/`, `backend/app/services/correlation.py`, `backend/app/services/search.py`

| Module # | Module Name | Exact Responsibilities & Deliverables |
|---|---|---|
| **Module 9** | **AI Vehicle Detection Pipeline** | YOLOX / ONNX Runtime detector classifying cars, motorcycles, buses, and trucks from decoded video frames. |
| **Module 10** | **Multi-Object Vehicle Tracking** | ByteTrack integration associating detections across consecutive frames to maintain consistent track IDs. |
| **Module 11** | **ANPR & License Plate OCR** | PaddleOCR pipeline: plate crop extraction, character OCR, confidence score, and Indian license plate normalization (`GJ 01 AB 1234` → `GJ01AB1234`). |
| **Module 12** | **Vehicle Event Indexing** | Ingestion pipeline converting AI detection tracks into searchable `VehicleEvent` records in the database. |
| **Module 13** | **Vehicle Re-ID & Visual Embeddings** | Lightweight Re-ID model (e.g. OSNet) extracting 512-dim visual appearance feature vectors for cross-camera verification. |
| **Module 14** | **Cross-Camera Correlation Engine** | **Flagship Engine**: Reconstruct multi-camera journeys using plate matching, timestamp ordering, and travel-time plausibility filters. |
| **Module 15** | **Vehicle Search Backend Engine** | High-performance search API (`/api/v1/vehicles/search`) filtering by plate number, date/time ranges, and camera IDs. |
| **Module 16** | **Movement Timeline Reconstruction Engine** | Timeline engine generating chronological journey sequence with durations, speeds, and camera waypoints. |
| **Module 25** | **Performance & Frame-Skipping Optimization** | Bounded inference queues, drop-on-lag logic, adaptive sampling (e.g. 5 FPS detection). |

---

### 💻 Developer 3: Frontend & GIS Full-Stack UI/UX Engineer
* **Feature Branch:** `feature/frontend-command-center`
* **Primary Directories:** `frontend/src/`

| Module # | Module Name | Exact Responsibilities & Deliverables |
|---|---|---|
| **Module 4** | **Frontend Foundation & Dashboard Shell** | Command Center dark theme layout, responsive navigation, summary KPI widgets, and system telemetry cards. |
| **Module 8** | **Live Camera Preview UI** | Multi-camera CCTV grid with low-latency WebRTC/WHEP playback and HLS fallback. |
| **Module 15** | **Vehicle Search Interface (UI)** | Plate number search bar (`GJ01AB1234`), date/time picker, department/camera filters, and results grid. |
| **Module 16** | **Movement Timeline View (UI)** | Interactive vertical/horizontal journey timeline with timestamps, camera badges, and snapshot thumbnails. |
| **Module 17** | **GIS Route Visualization (Leaflet)** | Interactive OpenStreetMap / Leaflet map plotting camera locations, journey path polylines, and synchronized timeline clicks. |
| **Module 18 & 19** | **Watchlist & Live Alerts Modal (UI)** | Hotlist management tables, real-time WebSocket alert popups with flashing audio/visual indicators and acknowledge buttons. |
| **Module 20** | **Evidence Vault & Export UI** | High-resolution snapshot viewer, plate crop comparison, SHA-256 hash verification badge, and PDF/CSV evidence report export. |
| **Module 23** | **System Health & Telemetry UI** | Live graphs showing connected cameras, stream FPS, inference latency, and database status. |
| **Module 27 & 28** | **Hackathon Demo Workflow & Polish** | End-to-end evaluation flow UI walkthrough (Discover → Stream → Detect → Search → Correlate → Alert → Audit). |

---

## 🔄 Git Workflow & Branching Strategy

To prevent merge conflicts, all developers must strictly adhere to the following workflow:

### Step 1: Clone and Set Up Main Branch
```bash
git clone https://github.com/ManageMatic/SentinelX-Cross-Camera-Vehicle-Intelligence-Unified-CCTV-Analytics-Platform.git
cd "SentinelX-Cross-Camera-Vehicle-Intelligence-Unified-CCTV-Analytics-Platform"
git checkout main
git pull origin main
```

### Step 2: Create Your Assigned Feature Branch
* **Developer 1:**
  ```bash
  git checkout -b feature/backend-ingestion-security
  ```
* **Developer 2:**
  ```bash
  git checkout -b feature/ai-anpr-correlation
  ```
* **Developer 3:**
  ```bash
  git checkout -b feature/frontend-command-center
  ```

### Step 3: Before Every Commit (Mandatory Quality Check)
Before committing, each member must run tests and linters locally:

* **Backend / AI (Dev 1 & Dev 2):**
  ```powershell
  backend\.venv\Scripts\ruff check backend database ai
  backend\.venv\Scripts\pytest backend/tests
  ```
* **Frontend (Dev 3):**
  ```powershell
  cd frontend
  npm run test
  npm run build
  ```

### Step 4: Commit with Conventional Messages
```bash
git add .
git commit -m "feat(moduleX): implement [short description of functionality]"
git push -u origin feature/your-branch-name
```

### Step 5: Sync with `main` Daily
Before merging, pull the latest changes from `main`:
```bash
git checkout main
git pull origin main
git checkout feature/your-branch-name
git merge main
```

---

## 📡 API Contracts & Interface Boundaries

All team members must use the standardized JSON envelope implemented in **Module 3**:

```json
{
  "success": true,
  "message": "Operation description",
  "data": { ... },
  "errors": null,
  "timestamp": "2026-09-08T17:00:00Z",
  "request_id": "uuid-v4-string"
}
```

### Key Endpoints Contract Matrix:
- `GET /api/v1/cameras` → Returns list of dynamic cameras for UI and AI streams.
- `GET /api/v1/vehicles/search?plate=GJ01AB1234` → Returns cross-camera vehicle detections.
- `GET /api/v1/vehicles/{plate}/timeline` → Returns chronological journey sequence.
- `GET /api/v1/vehicles/{plate}/route` → Returns ordered GPS coordinates `[[lat, lon], ...]` for Leaflet map.
- `WS /ws/alerts` → Real-time alert stream for frontend toast / red banner popups.

---

## 🚀 Local Quickstart Guide for All 3 Members

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm

### Backend Setup (Dev 1 & Dev 2)
```powershell
# In project root
python -m venv backend/.venv
.\backend\.venv\Scripts\activate
pip install -r backend/requirements.txt

# Run backend
& ".\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir backend --port 8000 --reload
```
API Docs: `http://localhost:8000/docs`

### Frontend Setup (Dev 3)
```powershell
cd frontend
npm install
npm run dev
```
UI: `http://localhost:5173`

---

## 🏆 Master Hackathon Demonstration Flow (Evaluation Script)

When all 3 tracks merge, the final demonstration to the judges will execute this exact story:
1. **Dynamic Discovery**: Show dynamic ingestion from `GET /api/ingest` (no hardcoded cameras).
2. **Live CCTV Grid**: Show heterogeneous live camera streams with FPS/PTS telemetry.
3. **Vehicle Detection & ANPR**: AI pipeline detects vehicles and OCR reads plate (`GJ01AB1234`).
4. **Vehicle Search**: Operator enters `GJ01AB1234` in search bar.
5. **Cross-Camera Correlation**: System identifies vehicle across 4 cameras in sequence.
6. **Movement Timeline & GIS Route**: Interactive Leaflet map draws the reconstructed route across Ahmedabad/Gandhinagar.
7. **Watchlist Match & Real-Time Red Alert**: Stolen vehicle triggers instant WebSocket alert with snapshot evidence.
8. **Forensic Evidence & Audit Trail**: Open snapshot evidence, show SHA-256 hash integrity check, and review immutable audit log.
