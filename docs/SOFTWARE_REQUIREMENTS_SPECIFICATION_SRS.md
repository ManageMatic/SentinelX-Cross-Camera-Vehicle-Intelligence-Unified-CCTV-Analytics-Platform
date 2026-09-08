# Software Requirements Specification (SRS)
## SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform

**Target Event:** Gujarat Police Innovation Challenge 2026  
**Document Version:** 1.0.0  
**Status:** Approved & Implemented Foundation  
**Classification:** Official Technical Specification  
**Licensing Constraint:** ₹0 Licensing / 100% Free & Open-Source (Apache-2.0, MIT, BSD, PostgreSQL)

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) document defines the complete functional, non-functional, interface, architectural, and security requirements for **SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform**. It serves as the authoritative blueprint for engineering, testing, integration, and official technical evaluation for the **Gujarat Police Innovation Challenge 2026**.

### 1.2 Document Conventions
- **Mandatory Requirements:** Expressed using "SHALL" or "MUST".
- **Design Constraints:** Expressed using "SHALL NOT" or "MUST NOT".
- **Zero-Cost Mandate:** Under no circumstances shall paid cloud services (AWS/Azure/GCP), paid SaaS, commercial APIs (Google Maps, OpenAI, Twilio, Auth0), or commercial VMS SDKs be introduced.

### 1.3 Intended Audience
- Gujarat Police Evaluators and Technical Assessment Committee
- Senior Software Architects, AI/Computer Vision Engineers, Backend Developers, and Frontend Engineers
- System Administrators, Cyber Crime Investigators, and Control Room Operators

### 1.4 Product Scope
SentinelX is a vendor-neutral, local-first surveillance intelligence platform designed to integrate heterogeneous CCTV infrastructure across government departments. Its flagship capability is:
> **"Enter a vehicle registration number -> Search indexed CCTV metadata across cameras -> Reconstruct chronological journey -> Display route on GIS OpenStreetMap -> Match against Watchlists -> Dispatch real-time WebSocket Red Alerts -> Preserve cryptographically verified SHA-256 evidence."**

---

## 2. Overall Description

### 2.1 Product Perspective
Government CCTV ecosystems are historically siloed across municipal corporations, highway authorities, and police units. SentinelX functions as a centralized intelligence layer that ingests dynamic camera feeds from the Gujarat Police Sentinel Sandbox (`GET /api/ingest`), processes streams via RTSP/TCP, indexes visual metadata into PostgreSQL, and provides a unified Command Center.

```
                    SENTINEL CAMERA CATALOG (/api/ingest)
                                     │
                                     ▼
                            CAMERA REGISTRY
                                     │
                                     ▼
                              STREAM MANAGER
                                     │
                      ┌──────────────┴──────────────┐
                      ▼                             ▼
                LIVE VIDEO                    AI PROCESSING
                PREVIEW                       PIPELINE
              (WHEP / HLS)                   (RTSP / TCP)
                      │                             │
                      │                  ┌──────────┴──────────┐
                      │                  │          │          │
                      │                  ▼          ▼          ▼
                      │              Detection   Tracking    ANPR
                      │                  │          │          │
                      │                  └──────────┼──────────┘
                      │                             │
                      │                             ▼
                      │                      VEHICLE EVENTS
                      │                             │
                      │                     ┌───────┴───────┐
                      │                     │               │
                      │                     ▼               ▼
                      │               VEHICLE RE-ID     EMBEDDINGS
                      │                     │               │
                      │                     └───────┬───────┘
                      │                             │
                      │                             ▼
                      │                    CORRELATION ENGINE
                      │                             │
                      │                 ┌───────────┼───────────┐
                      │                 │           │           │
                      │                 ▼           ▼           ▼
                      │             TIMELINE     WATCHLIST     GIS
                      │                 │           │           │
                      │                 └───────────┼───────────┘
                      │                             │
                      │                             ▼
                      │                       ALERT ENGINE (WebSocket)
                      │                             │
                      └─────────────────────────────┼─────────────────────────┐
                                                    │                         │
                                                    ▼                         ▼
                                         REACT COMMAND CENTER         EVIDENCE VAULT
```

### 2.2 User Classes and Roles
1. **State Administrator (`ADMIN`):** Full administrative authority, user provisioning, camera onboarding, system settings, and audit configuration.
2. **Control Room Operator (`OPERATOR`):** Live CCTV grid monitoring, alert triage and acknowledgment, active camera telemetry.
3. **Police Investigator (`INVESTIGATOR`):** Vehicle registration search, cross-camera correlation, movement timeline reconstruction, GIS route analysis, and evidence vault export.
4. **Crime Intelligence Analyst (`ANALYST`):** Trend analytics, traffic density reporting, vehicle frequency analysis.
5. **Viewer (`VIEWER`):** Read-only observational access without export or acknowledge privileges.

### 2.3 Operating Environment & Constraints
- **Hardware:** Standard laptop / desktop / server. Optional NVIDIA GPU for TensorRT acceleration.
- **Operating System:** Ubuntu 22.04+ LTS / Debian / Windows with PowerShell.
- **Runtime:** Python 3.12+, Node.js 20+, Docker & Docker Compose.
- **Database:** PostgreSQL 16 + PostGIS 3.4 + pgvector (with SQLite aiosqlite zero-setup dev fallback).
- **In-Memory Cache:** Valkey 8.0 (BSD licensed open-source Redis alternative).

---

## 3. System Architecture & Data Models

### 3.1 Entity Relationship & Data Schema

| Entity | Primary Key | Key Attributes | Purpose |
|---|---|---|---|
| **`cameras`** | `id (UUID)` | `external_camera_id`, `name`, `latitude`, `longitude`, `rtsp_url`, `whep_url`, `hls_url`, `live_status`, `codec`, `fps` | Dynamic camera registry from Sentinel `/api/ingest` |
| **`vehicle_events`** | `id (UUID)` | `camera_id`, `event_time`, `plate_raw`, `plate_normalized`, `vehicle_class`, `confidence`, `latitude`, `longitude`, `snapshot_path` | Searchable index of all vehicle sightings across cameras |
| **`vehicle_tracks`** | `id (UUID)` | `camera_id`, `track_id`, `first_seen`, `last_seen`, `vehicle_class`, `total_frames` | ByteTrack local multi-frame track associations |
| **`vehicle_plates`** | `id (UUID)` | `event_id`, `plate_text`, `plate_normalized`, `confidence`, `crop_path` | OCR readings and confidence scores from PaddleOCR |
| **`vehicle_embeddings`**| `id (UUID)` | `event_id`, `model_name`, `embedding_dim`, `vector_data` | 512-dimensional visual appearance feature vectors for Re-ID |
| **`watchlists`** | `id (UUID)` | `name`, `category (STOLEN, WANTED, SUSPICIOUS)`, `is_active`, `created_by` | Hotlist containers linked to police FIRs |
| **`watchlist_entries`** | `id (UUID)`| `watchlist_id`, `registration_normalized`, `priority (HIGH, MEDIUM)`, `is_active`| Monitored license plate numbers |
| **`alerts`** | `id (UUID)` | `vehicle_event_id`, `watchlist_entry_id`, `status (NEW, ACKNOWLEDGED)`, `alert_time` | Real-time security hits dispatched over WebSockets |
| **`evidence`** | `id (UUID)` | `camera_id`, `file_path`, `file_type`, `sha256_hash`, `captured_at`, `file_size_bytes` | Forensically secure evidence vault records |
| **`audit_logs`** | `id (UUID)` | `username`, `action`, `resource_type`, `resource_id`, `timestamp`, `ip_address` | Immutable append-only audit trail |

---

## 4. Functional Requirements

### 4.1 Ingestion & Camera Management
- **FR-01 (Dynamic Catalog Ingestion):** The system SHALL query `GET /api/ingest` dynamically at configured intervals. No camera IDs, URLs, or camera counts shall be hard-coded.
- **FR-02 (RTSP/TCP Stream Ingestion):** Ingestion workers SHALL enforce RTSP over TCP (`OPENCV_FFMPEG_CAPTURE_OPTIONS=rtsp_transport;tcp`) to prevent packet loss.
- **FR-03 (Resilient Reconnection):** When a stream disconnects, the system SHALL execute exponential backoff reconnection (1s, 2s, 4s, 8s, 16s, max 30s) without crashing other streams.
- **FR-04 (Bounded Buffers & Backpressure):** Frame queues SHALL be bounded (e.g. 10 frames). Stale frames SHALL be dropped during lag rather than accumulating RAM.

### 4.2 Computer Vision, Tracking & ANPR
- **FR-05 (Vehicle Detection):** The AI detector SHALL classify `car`, `motorcycle`, `bus`, and `truck` using a permissively licensed model (YOLOX / ONNX).
- **FR-06 (Multi-Object Tracking):** ByteTrack SHALL associate detections across frames to maintain stable track IDs and suppress duplicate OCR requests.
- **FR-07 (ANPR OCR & Plate Normalization):** PaddleOCR SHALL read license plates and normalize Indian registration numbers (e.g., `"GJ 01 AB 1234"` -> `"GJ01AB1234"`).
- **FR-08 (Vehicle Appearance Embeddings):** The vision pipeline SHALL extract appearance vectors for cross-camera Re-ID verification.

### 4.3 Search, Correlation & GIS Intelligence
- **FR-09 (Historical Plate Search):** The search engine SHALL query indexed database metadata (not live RTSP seeking) and return cross-camera sightings in < 200ms.
- **FR-10 (Cross-Camera Correlation Engine):** The correlation engine SHALL reconstruct multi-camera journeys by evaluating plate matches, time windows, and travel-time plausibility filters to eliminate physically impossible hops.
- **FR-11 (Chronological Journey Timeline):** The system SHALL display an ordered movement timeline with timestamps, camera waypoints, speeds, and snapshot crops.
- **FR-12 (Leaflet GIS Route Visualization):** The UI SHALL plot interactive Leaflet / OpenStreetMap route polylines connecting camera waypoints with synchronized timeline clicks.

### 4.4 Watchlists, Real-Time Alerts & Security
- **FR-13 (Watchlist Hotlist Matching):** Every detected license plate SHALL be evaluated in real-time against active watchlists.
- **FR-14 (WebSocket Real-Time Dispatch):** On a watchlist hit, a Red Alert SHALL be pushed over `/ws/alerts` within 500ms to the Command Center dashboard.
- **FR-15 (Forensic Evidence Integrity):** All saved snapshot crops SHALL have a SHA-256 cryptographic hash recorded in the database to guarantee chain of custody.
- **FR-16 (Append-Only Audit Logging):** All user searches, watchlist modifications, alert acknowledgments, and exports SHALL be logged immutably.

---

## 5. Non-Functional Requirements

### 5.1 Performance & Latency
- **API Response Time:** 95th percentile search latency SHALL be under 200 milliseconds.
- **Alert Latency:** Time from vehicle frame capture to operator dashboard alert SHALL be under 500 milliseconds.
- **Stream Ingestion Throughput:** System SHALL support concurrent multi-camera processing with adaptive frame skipping (5-10 detection FPS).

### 5.2 Security & Compliance
- **Zero Plaintext Secrets:** Passwords hashed with Argon2id; JWT secrets and database passwords masked in all logs and serialization (`get_safe_dict()`).
- **Stream Security:** Raw privileged RTSP credentials SHALL NEVER be exposed to the browser UI.
- **Network Security:** Strict CORS whitelist; secure WebSocket handshake authorization.

### 5.3 80,000-Camera Scalability Blueprint
To scale to statewide Gujarat deployment (~80,000 cameras), SentinelX utilizes a **distributed metadata-first edge architecture**:
1. **Regional Edge Gateways:** Local AI workers process video streams at district/city control rooms and extract metadata.
2. **Central Metadata Aggregation:** Only lightweight JSON events (~1 KB per detection) and alert triggers are transmitted centrally via Valkey Streams / Kafka, reducing statewide network bandwidth by > 99%.
3. **Preservation of Existing Infrastructure:** Regional VMS servers retain raw 30-day video archives; SentinelX accesses high-res streams on-demand during investigations.

---

## 6. Verification and Demonstration Script

During official technical evaluation, SentinelX proves compliance through this mandatory workflow:
1. **Dynamic Ingestion:** Connect to Sentinel `/api/ingest` and discover all live sandbox cameras.
2. **Live CCTV Grid:** Display multi-camera feeds with WHEP/HLS low-latency streaming and active FPS metrics.
3. **AI Pipeline:** Live vehicle detection and ANPR reading plates in real-time.
4. **Designated Search:** Enter evaluation vehicle number `GJ01AB1234`.
5. **Cross-Camera Correlation:** Show vehicle detected across Cameras 1 -> 2 -> 3 in chronological sequence.
6. **Timeline & GIS Mapping:** Display reconstructed journey on interactive Leaflet GIS map.
7. **Watchlist Match & Red Alert:** Trigger automated high-priority alert with audio/visual flash and snapshot evidence.
8. **Audit Trail & Evidence:** Inspect SHA-256 evidence integrity and export forensic audit log.

---
*Document approved for SentinelX Implementation — Gujarat Police Innovation Challenge 2026.*
