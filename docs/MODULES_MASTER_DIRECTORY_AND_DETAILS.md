# SentinelX — Complete Modules Directory & Technical Specification

**Project:** SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform  
**Target Event:** Gujarat Police Innovation Challenge 2026  
**License:** ₹0 Licensing / 100% Free & Open-Source (Apache-2.0, MIT, BSD, PostgreSQL)  
**Total Modules:** 29 Modules (Module 0 to Module 28)  
**Current Status:** Modules 0, 1, 2, 3 Complete (4/29 Modules, 100% Green Tests, 0 Linter Diagnostics)

---

## Executive Summary & Architecture Overview

SentinelX is structured into **29 focused, decoupled modules** spanning edge/backend streaming, computer vision, cross-camera correlation, forensic security, and high-performance React GIS command centers.

```
                    ┌──────────────────────────────────────────┐
                    │       SENTINEL SANDBOX (/api/ingest)     │
                    └─────────────────────┬────────────────────┘
                                          │
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               BACKEND & INGESTION PIPELINE                             │
│  [M0] Foundation ──▶ [M1] Config/Logs ──▶ [M2] Database ──▶ [M3] API Foundation        │
│  [M5] Dynamic Ingest ──▶ [M6] RTSP/TCP Worker ──▶ [M7] Resilient Stream Manager        │
│  [M8] WebRTC/WHEP Proxy ──▶ [M9] Frame Buffer & Backpressure                           │
└─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                          │
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              AI & ANALYTICS PIPELINE                                   │
│  [M10] Detection (YOLOX) ──▶ [M11] ByteTrack Multi-Object Tracker                      │
│  [M12] ANPR & Plate Normalizer (PaddleOCR) ──▶ [M13] Re-ID Appearance Embeddings       │
│  [M14] Real-time Vehicle Event Indexer ──▶ [M15] Sub-200ms Search Engine               │
│  [M16] Cross-Camera Correlation Engine ──▶ [M17] Journey & Timeline Reconstructor      │
│  [M18] Watchlist Hotlist Evaluator ──▶ [M19] WebSocket Alert Dispatcher                │
└─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                          │
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           SECURITY, FORENSICS & INFRASTRUCTURE                         │
│  [M20] Evidence Vault & SHA-256 Chain of Custody ──▶ [M21] Immutable Audit Logger      │
│  [M22] RBAC & JWT Auth ──▶ [M23] Valkey In-Memory Cache & Streams                      │
│  [M24] Statewide 80k-Camera Scalability & Edge Gateway Simulation                      │
└─────────────────────────────────────────┬──────────────────────────────────────────────┘
                                          │
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             FRONTEND COMMAND CENTER (REACT)                            │
│  [M4] Command Center Shell & Design System ──▶ [M25] Live Multi-Camera CCTV Grid       │
│  [M26] GIS OpenStreetMap & Trajectory Map ──▶ [M27] Vehicle Intelligence UI            │
│  [M28] System Diagnostics, Telemetry & Evaluation Suite                                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Master Directory of All 29 Modules

### Track 1: Foundation & Core Infrastructure (Modules 0 – 4)

#### [COMPLETED] Module 0: Project Foundation & Architecture Setup
- **Status:** Complete (Verified with automated Pytest and Vitest suites)
- **Purpose:** Initializes repository layout, licensing notices, container specifications, and testing harnesses.
- **Key Deliverables:** 
  - Directory structures (`backend/`, `frontend/`, `docs/`, `scripts/`, `storage/`).
  - `docker-compose.yml` with PostgreSQL 16 PostGIS, Valkey, Backend, and Frontend.
  - Strict ₹0 licensing documentation (`THIRD_PARTY_NOTICES.md`, `MODEL_LICENSES.md`).

#### [COMPLETED] Module 1: Configuration & Structured Logging Engine
- **Status:** Complete (100% test coverage)
- **Purpose:** Centralized, type-safe settings management with zero credential leakage.
- **Key Deliverables:**
  - `backend/app/core/config.py`: Pydantic v2 `Settings` with port validators, CORS parsers, directory bootstrapping.
  - `backend/app/core/logging.py`: Structured JSON logger with `SafeLogFilter` masking passwords, tokens, and database URIs.

#### [COMPLETED] Module 2: Database Layer, SQLAlchemy Async Models & Seed Data
- **Status:** Complete (100% test coverage)
- **Purpose:** Relational and vector database foundation for high-throughput CCTV metadata.
- **Key Deliverables:**
  - `backend/app/db/`: Async engine supporting SQLite (local zero-setup dev) and PostgreSQL 16 + PostGIS + pgvector.
  - 10 ORM Models: `User`, `Role`, `Permission`, `Camera`, `CameraSource`, `CameraHealth`, `VehicleEvent`, `VehicleTrack`, `VehiclePlate`, `VehicleEmbedding`, `Watchlist`, `WatchlistEntry`, `Alert`, `AlertEvent`, `Evidence`, `AuditLog`, `SystemHealthMetric`.
  - `backend/app/db/seed/dev_seed.py`: Deterministic test data generator for cross-camera verification.

#### [COMPLETED] Module 3: API Foundation, Standardized Envelope, Error Handlers & Middleware
- **Status:** Complete (100% test coverage)
- **Purpose:** Uniform RESTful API response wrappers, request correlation IDs, and global exception handlers.
- **Key Deliverables:**
  - `backend/app/schemas/response.py`: `APIResponse[T]` and `PaginatedResponse[T]` standard envelopes.
  - `backend/app/middleware/request_logging.py`: `RequestLoggingMiddleware` with `X-Request-ID` and timing.
  - `backend/app/api/v1/endpoints/system.py`: `/api/v1/system/status` and health endpoints.

#### [IN PROGRESS / NEXT] Module 4: Frontend Foundation, Shell, Design System & Layouts
- **Status:** Next in Queue
- **Purpose:** Establishes the tactical dark-mode command center UI, collapsible navigation, live status monitors, and modular routing.
- **Key Deliverables:**
  - `frontend/src/components/layout/`: `AppLayout`, `TopNav`, `Sidebar`, `Breadcrumbs`, `AlertTicker`.
  - `frontend/src/pages/`: Page containers for Dashboard, Live Grid, Vehicle Search, Trajectory Map, Watchlists, Alerts, Evidence, and System Telemetry.
  - `frontend/src/services/api.ts`: Typed API client handling `APIResponse[T]` unpacking and error notifications.
  - Tailwind Dark Theme tokens: High-contrast law enforcement dark theme palette.

---

### Track 2: Ingestion & Live Video Processing (Modules 5 – 9)

#### Module 5: Dynamic Camera Catalog Ingestion Engine
- **Purpose:** Discovers cameras dynamically from Gujarat Police Sentinel `/api/ingest` without hardcoded URLs or counts.
- **Key Responsibilities:** Periodic polling, camera registry sync, schema normalization, RTSP/WHEP URL extraction.
- **Inputs/Outputs:** Input: `GET /api/ingest` JSON payload; Output: Updated `Camera` & `CameraSource` database records.

#### Module 6: RTSP / TCP Stream Ingestion Worker
- **Purpose:** Connects to IP cameras and VMS streams strictly over TCP to eliminate packet loss and artifacting.
- **Key Responsibilities:** OpenCV / FFmpeg RTSP ingestion, frame decoding, timestamp synchronization, worker threads.
- **Inputs/Outputs:** Input: RTSP stream URL; Output: Decoded RGB video frames in memory.

#### Module 7: Resilient Stream Manager & Auto-Reconnect Engine
- **Purpose:** Ensures 24/7 uptime across unstable network connections with exponential backoff reconnection.
- **Key Responsibilities:** Stream health monitoring, watchdog heartbeats, automatic reconnection (1s -> 30s), circuit breakers.
- **Inputs/Outputs:** Input: Stream disconnect signals; Output: Restored stream threads & updated `CameraHealth` records.

#### Module 8: Low-Latency WebRTC (WHEP) & HLS Proxy
- **Purpose:** Bridges low-latency camera streams directly to operator browsers without browser plugins.
- **Key Responsibilities:** WHEP signaling proxy, HLS fallback streaming, sub-second latency streaming for live surveillance grid.
- **Inputs/Outputs:** Input: RTSP / WHEP camera endpoints; Output: Browser-consumable video streams.

#### Module 9: Frame Buffer Manager & Adaptive Backpressure Queue
- **Purpose:** Protects AI workers from memory exhaustion during heavy CCTV traffic bursts.
- **Key Responsibilities:** Ring-buffer queues (bounded at 10-20 frames), intelligent frame-dropping for lagging streams, FPS decimation (5-10 FPS for AI detection).
- **Inputs/Outputs:** Input: Raw 25/30 FPS camera frames; Output: Bounded, prioritized frame queue for computer vision.

---

### Track 3: Computer Vision, Tracking & ANPR Pipeline (Modules 10 – 14)

#### Module 10: Multi-Class Vehicle Detection Engine (YOLOX / ONNX)
- **Purpose:** Detects and classifies vehicles in CCTV frames using 100% permissively licensed models (Apache-2.0).
- **Key Responsibilities:** ONNX Runtime inference, CPU/GPU acceleration, bounding box localization for `car`, `motorcycle`, `bus`, `truck`.
- **Inputs/Outputs:** Input: Decoded video frames; Output: Normalized vehicle bounding boxes with confidence scores.

#### Module 11: ByteTrack Multi-Object Tracking Engine
- **Purpose:** Associates vehicle detections across sequential frames within a single camera feed.
- **Key Responsibilities:** Kalman filter motion prediction, Hungarian matching, persistent track ID assignment, duplicate OCR suppression.
- **Inputs/Outputs:** Input: Frame detections; Output: Temporal vehicle tracks (`track_id`, trajectory vectors).

#### Module 12: ANPR Engine & Indian License Plate Normalizer (PaddleOCR)
- **Purpose:** Recognizes Indian license plates and formats them into clean, searchable alphanumeric strings.
- **Key Responsibilities:** License plate region localization, Apache-2.0 PaddleOCR recognition, Indian regex normalization (`"GJ 01 AB 1234"` -> `"GJ01AB1234"`), confidence scoring.
- **Inputs/Outputs:** Input: Vehicle snapshot crop; Output: `plate_raw`, `plate_normalized`, OCR confidence.

#### Module 13: Vehicle Appearance Re-ID & Visual Embedding Generator
- **Purpose:** Generates visual feature vectors to enable cross-camera tracking even when plates are occluded or unreadable.
- **Key Responsibilities:** Fast 512-dimensional embedding extraction (OSNet / MobileNet-v3), color/make/model classification.
- **Inputs/Outputs:** Input: Vehicle crop; Output: 512-dim visual embedding stored in `vehicle_embeddings`.

#### Module 14: Real-time Vehicle Event Ingestion & Indexer
- **Purpose:** Aggregates detection, tracking, ANPR, and embedding data into unified database event records.
- **Key Responsibilities:** Fast batch ingestion into PostgreSQL / SQLite, automated snapshot saving, metadata indexing.
- **Inputs/Outputs:** Input: Combined AI pipeline outputs; Output: Committed `VehicleEvent` records.

---

### Track 4: Search, Correlation & Real-time Alerts (Modules 15 – 19)

#### Module 15: Sub-200ms Vehicle Search Engine
- **Purpose:** High-performance search API querying indexed metadata without seeking live video feeds.
- **Key Responsibilities:** Exact match, wildcard/fuzzy plate search, date-time range filters, camera location filters, vehicle class filters.
- **Inputs/Outputs:** Input: Search parameters; Output: Paginated `VehicleEvent` list in < 200ms.

#### Module 16: Cross-Camera Correlation Engine & Spatial-Temporal Filter
- **Purpose:** Connects isolated camera events to reconstruct multi-camera journeys across the city/state.
- **Key Responsibilities:** Chronological multi-camera grouping, speed-distance plausibility validation (eliminating physically impossible teleports), visual Re-ID similarity matching.
- **Inputs/Outputs:** Input: Target vehicle ID / plate; Output: Ordered multi-camera sighting graph.

#### Module 17: Chronological Journey & Route Timeline Reconstructor
- **Purpose:** Generates formatted movement histories complete with transit durations, camera waypoints, and speed estimates.
- **Key Responsibilities:** Point-to-point journey construction, speed calculation, transit anomaly detection.
- **Inputs/Outputs:** Input: Correlated sightings; Output: Reconstructed journey timeline model.

#### Module 18: Real-Time Watchlist & Hotlist Matching Engine
- **Purpose:** Evaluates every incoming vehicle detection against active police hotlists in < 50ms.
- **Key Responsibilities:** In-memory plate hash lookup, category evaluation (Wanted, Stolen, Suspicious, VIP), priority grading (High/Critical).
- **Inputs/Outputs:** Input: Ingested `VehicleEvent`; Output: Match status & generated `Alert` record.

#### Module 19: Real-time WebSocket Alert Dispatcher & Notification Hub
- **Purpose:** Pushes instant Red Alerts to all connected Control Room dashboards in < 500ms.
- **Key Responsibilities:** FastAPI WebSocket endpoint (`/ws/alerts`), client subscription management, sound/visual alert triggers.
- **Inputs/Outputs:** Input: Generated `Alert`; Output: Real-time JSON broadcast to operators.

---

### Track 5: Security, Forensics & System Scaling (Modules 20 – 24)

#### Module 20: Forensic Evidence Vault & Cryptographic SHA-256 Chain of Custody
- **Purpose:** Secures snapshot and video evidence for courtroom admissibility with cryptographic verification.
- **Key Responsibilities:** SHA-256 hashing on snapshot capture, tamper-evident hash verification, tamper detection alerts.
- **Inputs/Outputs:** Input: Image/video snapshot; Output: Signed `Evidence` record with verifiable hash.

#### Module 21: Append-Only Immutable Audit Logging Engine
- **Purpose:** Logs every operator search, watchlist update, alert acknowledgment, and export for internal accountability.
- **Key Responsibilities:** Non-destructive audit trail, user IP tracking, timestamping, compliance exports.
- **Inputs/Outputs:** Input: User action event; Output: Immutable `AuditLog` entry.

#### Module 22: Role-Based Access Control (RBAC) & Argon2id Authentication
- **Purpose:** Secure user login and fine-grained authorization.
- **Key Responsibilities:** Argon2id password hashing, JWT access/refresh tokens, 5 roles (`ADMIN`, `OPERATOR`, `INVESTIGATOR`, `ANALYST`, `VIEWER`).
- **Inputs/Outputs:** Input: Credentials; Output: JWT token with verified role permissions.

#### Module 23: Valkey In-Memory Cache & Stream Broker
- **Purpose:** High-performance caching and messaging using 100% open-source Valkey 8.0 (BSD licensed).
- **Key Responsibilities:** Dynamic camera status caching, alert pub/sub, hotlist memory index.
- **Inputs/Outputs:** Input: Fast read/write cache operations; Output: Sub-millisecond data retrieval.

#### Module 24: Statewide 80,000-Camera Scalability & Edge Gateway Simulation
- **Purpose:** Validates Gujarat statewide scalability model using distributed edge metadata aggregation.
- **Key Responsibilities:** Edge gateway simulation script, bandwidth benchmarking (>99% network savings via metadata-first transit), distributed clustering architecture docs.
- **Inputs/Outputs:** Input: Simulated 80,000 camera feeds; Output: Aggregate throughput and latency metrics report.

---

### Track 6: React Command Center & Evaluation UI (Modules 25 – 28)

#### Module 25: Live Multi-Camera CCTV Grid & WHEP Video Player
- **Purpose:** Tactical video wall displaying live camera feeds with configurable grid layouts (2x2, 3x3, 4x4, focus mode).
- **Key Responsibilities:** WHEP/HLS video playback, live FPS and bit-rate overlays, full-screen camera inspection.
- **Inputs/Outputs:** Input: Active camera streams; Output: Interactive multi-grid surveillance UI.

#### Module 26: GIS OpenStreetMap & Chronological Route Visualization
- **Purpose:** Interactive map plotting camera locations, vehicle detection pins, and reconstructed travel paths.
- **Key Responsibilities:** Leaflet / OpenStreetMap integration, numbered waypoint markers, animated journey polylines, map-to-timeline synchronized selection.
- **Inputs/Outputs:** Input: Journey waypoints; Output: Interactive tactical map view.

#### Module 27: Vehicle Intelligence, Watchlists & Alert Triage UI
- **Purpose:** Operator workstation for conducting plate searches, managing hotlists, and triaging real-time alerts.
- **Key Responsibilities:** Instant search bar, filter drawers, alert detail modal with snapshot comparisons, one-click acknowledgment and export.
- **Inputs/Outputs:** Input: Operator queries & triage decisions; Output: Visual search results, updated alert statuses.

#### Module 28: System Diagnostics, Health Telemetry & 8-Step Evaluation Suite
- **Purpose:** Live system monitoring and automated validation test runner for the Gujarat Police Innovation Challenge evaluation script.
- **Key Responsibilities:** CPU/RAM/VRAM telemetry gauges, camera status tables, 8-step evaluation demo launcher (`GJ01AB1234` end-to-end verification).
- **Inputs/Outputs:** Input: System metrics and evaluation triggers; Output: Real-time telemetry dashboards and evaluation reports.

---

## Complete Module Summary Table

| Module ID | Module Title | Primary Technology | Licensing | Status |
|:---:|---|---|:---:|:---:|
| **M0** | Project Foundation & Architecture Setup | Python, Node.js, Docker | Apache-2.0 | **COMPLETED** |
| **M1** | Configuration & Structured Logging Engine | Pydantic v2, Python logging | BSD-3 | **COMPLETED** |
| **M2** | Database Layer & SQLAlchemy Async Models | SQLAlchemy 2.0, PostgreSQL / SQLite | MIT / PostgreSQL | **COMPLETED** |
| **M3** | API Foundation, Standardized Envelopes & Middleware | FastAPI, Starlette | MIT | **COMPLETED** |
| **M4** | Frontend Foundation, Shell & Design System | React 18, Tailwind CSS, Lucide | MIT | **IN PROGRESS (Next)** |
| **M5** | Dynamic Camera Catalog Ingestion Engine | FastAPI, HTTPX, Pydantic | MIT | Pending |
| **M6** | RTSP / TCP Stream Ingestion Worker | OpenCV, FFmpeg | Apache-2.0 / LGPL | Pending |
| **M7** | Resilient Stream Manager & Auto-Reconnect | Python Asyncio, Threading | PSF | Pending |
| **M8** | Low-Latency WebRTC (WHEP) & HLS Proxy | MediaMTX / WebRTC | Apache-2.0 | Pending |
| **M9** | Frame Buffer Manager & Adaptive Backpressure | Python Queues, RingBuffer | BSD-3 | Pending |
| **M10** | Multi-Class Vehicle Detection Engine | ONNX Runtime, YOLOX | Apache-2.0 | Pending |
| **M11** | ByteTrack Multi-Object Tracking Engine | ByteTrack, NumPy, SciPy | MIT | Pending |
| **M12** | ANPR Engine & Indian License Plate Normalizer | PaddleOCR, OpenCV | Apache-2.0 | Pending |
| **M13** | Vehicle Appearance Re-ID & Embeddings | PyTorch / ONNX, OSNet | MIT | Pending |
| **M14** | Real-time Vehicle Event Ingestion & Indexer | SQLAlchemy Async, PostgreSQL | MIT | Pending |
| **M15** | Sub-200ms Vehicle Search Engine | PostgreSQL Indices / SQLite FTS | PostgreSQL / MIT | Pending |
| **M16** | Cross-Camera Correlation Engine | NetworkX, SciPy, Spatial Filters | BSD-3 | Pending |
| **M17** | Chronological Journey & Route Timeline | Python Data Pipeline | MIT | Pending |
| **M18** | Real-Time Watchlist & Hotlist Matching | In-Memory Hash Trie, SQLAlchemy | MIT | Pending |
| **M19** | Real-time WebSocket Alert Dispatcher | FastAPI WebSockets, Valkey | MIT | Pending |
| **M20** | Forensic Evidence Vault & SHA-256 Custody | Cryptography, hashlib | Apache-2.0 | Pending |
| **M21** | Append-Only Immutable Audit Logging | SQLAlchemy Async, PostgreSQL | MIT | Pending |
| **M22** | RBAC & Argon2id Authentication | Passlib, PyJWT, Argon2 | Apache-2.0 | Pending |
| **M23** | Valkey In-Memory Cache & Stream Broker | Valkey (Redis-compatible) | BSD-3 | Pending |
| **M24** | Statewide 80k-Camera Scalability & Edge Sim | Python Async Sim, WebSockets | MIT | Pending |
| **M25** | Live Multi-Camera CCTV Grid & Video Player | React, Hls.js, WebRTC WHEP | MIT | Pending |
| **M26** | GIS OpenStreetMap & Route Visualization | Leaflet, React-Leaflet, OSM | BSD-2 / OpenData | Pending |
| **M27** | Vehicle Intelligence, Watchlist & Alert UI | React, Tailwind, Lucide React | MIT | Pending |
| **M28** | System Diagnostics & Evaluation Suite | React, Chart.js, FastAPI Telemetry | MIT | Pending |
