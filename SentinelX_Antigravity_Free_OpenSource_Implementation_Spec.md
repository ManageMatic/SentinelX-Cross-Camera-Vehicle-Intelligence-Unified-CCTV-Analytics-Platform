# Gujarat Police Innovation Challenge 2026
# SentinelX — Free & Open-Source Implementation Specification

**Purpose:** Master implementation document for Antigravity / AI coding agents.

**Important cost rule:** This project must be implementable with **₹0 software/API/cloud licensing cost**. Do not depend on paid SaaS, paid APIs, paid cloud services, paid map APIs, paid AI APIs, paid OCR/ANPR services, or commercial software licenses.

**Core requirement:** Use the Gujarat Police/Sentinel sandbox supplied by the hackathon, plus free/open-source software that can run locally or on freely available hardware.

---

## 1. Executive Summary

### Project name

**SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform**

### Tagline

> **One Search. Every Camera. Complete Movement Intelligence.**

### Main objective

Build a secure, vendor-neutral CCTV intelligence platform whose flagship feature is:

> **Enter a vehicle registration number → search the indexed CCTV events → identify the vehicle across cameras → reconstruct its movement → show the route on GIS → check the watchlist → generate a real-time alert → preserve searchable evidence.**

The platform must work with the Sentinel sandbox and satisfy the mandatory technical evaluation.

---

# 2. Zero-Cost / Free-Only Policy

## 2.1 What "free" means for this project

The implementation must avoid:

- paid cloud hosting;
- paid databases;
- paid AI inference APIs;
- paid OCR/ANPR APIs;
- paid map APIs;
- paid email/SMS/WhatsApp notification APIs;
- commercial CCTV/VMS SDKs unless the hackathon itself supplies them;
- paid monitoring platforms;
- paid vector databases;
- paid search services.

Use software that can be downloaded, self-hosted, and run locally without a subscription or license fee.

## 2.2 Free does not mean "no resource requirement"

The software can be free while the team may still need:

- a laptop/desktop;
- GPU if available;
- electricity;
- local network/internet;
- the Sentinel sandbox access supplied by the hackathon.

Do **not** purchase hardware specifically for the MVP unless necessary.

## 2.3 No paid external dependency

The final MVP should still run if all external commercial services are removed.

The only external environment that is mandatory is:

**Gujarat Police Sentinel sandbox/camera environment supplied for the hackathon.**

---

# 3. Hackathon Context

The supplied Gujarat CCTV Hackathon problem describes:

- multiple government departments;
- independent CCTV ecosystems;
- analog and IP cameras;
- geographically distributed cameras;
- multiple VMS vendors;
- heterogeneous codecs/resolutions/frame rates;
- different storage and retention models;
- existing government databases;
- need for interoperability;
- AI-powered analytics;
- approximately 80,000-camera scalability target.

The challenge asks for a secure, scalable, interoperable, technically feasible and cost-effective architecture that uses existing infrastructure as much as practical.

---

# 4. Mandatory Evaluation Flow

The supplied step-by-step guide requires the team to:

1. Understand the challenge.
2. Choose an integration model.
3. Build the platform.
4. Test on Sentinel CCTV feeds.
5. Prepare submission.
6. Explain scalability.
7. Demonstrate/evaluate the solution.

The technical evaluation requires capabilities around:

- onboarding approximately 50 heterogeneous cameras;
- integrating live feeds;
- tracking a designated vehicle;
- using the registration number supplied during evaluation;
- identifying/tracing the vehicle across cameras;
- showing timestamps and movement;
- maintaining a representative watchlist;
- generating real-time watchlist alerts;
- GIS visualization;
- demonstrating AI analytics, interoperability and scalability.

The supplied Live Portal screenshot showed **30 live cameras**, while the guide refers to approximately **50 cameras** for evaluation. Therefore:

> **Never hard-code 30 or 50. Always consume the dynamic Sentinel catalog.**

---

# 5. Recommended Integration Model

## Final choice: Hybrid / Innovative Architecture

Use a combination of the supplied models:

### Model 1 — Centralised CCTV Registry & GIS Mapping

Use for:

- camera registry;
- camera metadata;
- locations;
- GPS;
- department;
- camera health;
- GIS;
- asset inventory.

### Model 2 — Unified Viewing & Metadata Analytics

Use as the main application layer:

- unified camera viewing;
- event metadata;
- ANPR;
- vehicle search;
- movement records;
- analytics;
- unified control room.

### Model 3 — VMS Federation & Middleware

Use as the interoperability layer:

- adapters;
- stream connectors;
- VMS integration;
- RTSP/ONVIF;
- vendor-neutral normalization;
- event/metadata pipeline.

### Selected Model 4 concepts — Central VMS & AI Platform

Use only the valuable parts:

- centralized AI;
- centralized search;
- command-center dashboard;
- common security/policy layer.

Do **not** claim that the prototype replaces all departmental VMS systems.

### Architecture statement

> SentinelX is a hybrid federated architecture that preserves existing CCTV/VMS infrastructure, normalizes heterogeneous camera streams through a vendor-neutral integration layer, performs centralized metadata-driven AI intelligence, and provides unified cross-camera search, GIS, alerts and investigation workflows.

---

# 6. Sentinel Resources Page — What It Is

The Sentinel Resources page is the **technical integration manual** for the sandbox.

It tells us:

- how cameras are published;
- how to discover cameras;
- how to obtain stream URLs;
- which protocols are available;
- how RTSP behaves;
- how timing works;
- how reconnection should work;
- what codecs to expect;
- what clients should and should not do.

It is **not** our final application.

It is the technical contract between our application and the Sentinel camera environment.

---

# 7. Sentinel Live Camera Portal — What It Is

The Sentinel Live Camera Portal is the **actual sandbox/control-room camera environment**.

It shows:

- camera IDs;
- camera names/locations;
- live status;
- camera grid;
- currently available cameras;
- camera filtering;
- live camera access.

The screenshot supplied by the team showed:

**Sentinel Control Room — Live CCTV Grid — 30 cameras · live**

The portal is the **source environment**.

Our application must consume it and add intelligence.

### Important distinction

```text
Sentinel Resources
      |
      | Technical rules/API/protocols
      v
Sentinel Camera Catalog
      |
      v
Sentinel Live Camera Environment
      |
      v
SentinelX
      |
      +--> AI
      +--> ANPR
      +--> Tracking
      +--> Search
      +--> Cross-camera correlation
      +--> GIS
      +--> Watchlist
      +--> Alerts
      +--> Investigation
```

---

# 8. Sentinel Camera Catalog

The resource page says to start from the catalog instead of hard-coding endpoints.

The screenshot shows:

```text
GET http://<host>/api/ingest
```

The catalog provides information such as:

- camera ID;
- location;
- codec;
- live status;
- stream properties;
- RTSP URL;
- WebRTC/WHEP URL;
- HLS URL.

### Mandatory implementation rule

Do:

```text
GET /api/ingest
       |
       v
Camera catalog
       |
       v
Local camera registry
```

Do NOT do:

```text
camera1 = "hard-coded RTSP URL"
camera2 = "hard-coded RTSP URL"
...
```

Camera IDs and available cameras can change.

---

# 9. Sentinel Stream Protocols

## 9.1 RTSP

Pattern shown by the resource:

```text
rtsp://<host>:8554/stream/<id>
```

Use RTSP for:

- AI inference;
- OpenCV;
- FFmpeg;
- GStreamer;
- DeepStream if NVIDIA hardware is available.

### Primary rule

**RTSP is the primary AI ingestion protocol.**

---

## 9.2 WebRTC / WHEP

Pattern shown by the resource:

```text
http://<host>:8889/stream/<id>/whep
```

Use it for:

- low-latency browser preview;
- live camera UI.

Do not make browser WebRTC the main AI processing pipeline.

---

## 9.3 HLS

Pattern shown:

```text
http://<host>/live/stream/<id>/index.m3u8
```

Use for:

- browser fallback;
- restricted-network playback;
- dashboard/mobile playback where required.

---

# 10. Sentinel Live-Stream Behavior

Treat every camera as a real operational camera.

The resource page states that:

- streams are live;
- approximately one second of video takes one second to arrive;
- frames have monotonic presentation timestamps (PTS);
- there is no seeking;
- there is no byte-range fetching;
- the client cannot run ahead of real time.

Therefore:

## Do not build historical search by seeking the RTSP stream.

Instead:

```text
Live stream
   |
   v
AI processing
   |
   v
Vehicle event
   |
   v
Metadata index
   |
   v
Search historical events
```

This is a critical design decision.

---

# 11. Why Metadata Indexing Is Essential

Suppose:

```text
10:21:34  CAM12  GJ01AB1234
10:29:11  CAM18  GJ01AB1234
10:37:52  CAM24  GJ01AB1234
10:44:03  CAM31  GJ01AB1234
```

The search engine searches **our indexed events**, not the raw Sentinel stream.

This enables:

- historical search;
- movement reconstruction;
- GIS route;
- watchlist matching;
- investigation.

---

# 12. RTSP Must Use TCP

The Sentinel resources explicitly require/advise RTSP over TCP.

OpenCV example:

```python
import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

import cv2
cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
```

Do not rely on UDP for the Sentinel integration.

---

# 13. Video Ingestion Technologies — Free Only

## MVP

### OpenCV

Use:

- RTSP connection;
- frame reading;
- image preprocessing;
- simple debugging.

OpenCV 4.5.0+ is Apache 2 licensed.

Official license:
https://opencv.org/license/

## FFmpeg

Use:

- RTSP diagnostics;
- codec inspection;
- stream debugging;
- decoding where useful.

FFmpeg is free/open source; most files are LGPL, but optional GPL components can change licensing. Keep the build simple and avoid unnecessary GPL/nonfree components.

Official license:
https://ffmpeg.org/doxygen/trunk/md_LICENSE.html

## GStreamer

Use for:

- more reliable multi-stream processing;
- buffering;
- pipeline control;
- hardware acceleration where available.

GStreamer is LGPL.

Official licensing:
https://gstreamer.freedesktop.org/documentation/frequently-asked-questions/licensing.html

## NVIDIA DeepStream

Use **only if the team already has compatible NVIDIA hardware**.

DeepStream is a free software development stack, but NVIDIA hardware itself is not free.

Therefore:

> Do not make NVIDIA hardware a mandatory requirement.

---

# 14. Free AI Detection Stack

## Recommended detector

Use an open-source detector whose **code and selected weights have a license suitable for the project**.

### Preferred approach

Use **YOLOX** or another permissively licensed detector implementation rather than automatically selecting a commercially licensed/dual-licensed package.

YOLOX source is Apache-2.0 licensed.

Official repository:
https://github.com/Megvii-BaseDetection/YOLOX

### Important

Do not download arbitrary model weights without checking their license.

Keep a `MODEL_LICENSES.md` file containing:

- model name;
- repository;
- weight source;
- license;
- date checked;
- modifications, if any.

---

# 15. Object Detection Classes

Minimum:

- car;
- motorcycle;
- bus;
- truck;
- person.

Optional:

- bicycle;
- auto-rickshaw;
- van;
- emergency vehicle.

Do not implement unnecessary classes before the mandatory vehicle use case works.

---

# 16. Tracking — Free

Use:

**ByteTrack**

ByteTrack is available under the MIT license in its official ecosystem/repositories.

Use it for:

- vehicle tracking within a camera;
- track continuity;
- reducing repeated detections.

Architecture:

```text
Frame
  |
Detector
  |
Bounding boxes
  |
ByteTrack
  |
Local track ID
```

Important:

```text
CAM12 track 17
```

does NOT mean:

```text
CAM18 track 17
```

is the same vehicle.

Cross-camera identity requires another layer.

---

# 17. ANPR / OCR — Free

Recommended:

**PaddleOCR**

PaddleOCR is Apache 2.0 licensed.

Official repository:
https://github.com/PaddlePaddle/PaddleOCR

Pipeline:

```text
Vehicle
   |
Vehicle detector
   |
Plate detector
   |
Plate crop
   |
OCR
   |
Normalization
   |
Registration number
```

Store:

```text
raw_ocr_text
normalized_plate
ocr_confidence
```

Example:

```text
Raw:        GJ 01 AB 1234
Normalized: GJ01AB1234
```

Never delete the raw OCR result.

---

# 18. ANPR Accuracy Strategy

Use multiple frames for the same tracked vehicle.

Instead of:

```text
one frame -> one OCR result -> final
```

use:

```text
Vehicle Track
   |
multiple plate crops
   |
OCR results
   |
confidence filtering
   |
majority/weighted voting
   |
final plate
```

This is faster and more reliable than running expensive OCR on every frame.

---

# 19. Vehicle Feature Extraction

Store optional supporting attributes:

- vehicle class;
- approximate color;
- make/model only if reliable;
- bounding box;
- appearance embedding;
- plate;
- timestamp;
- camera;
- GPS;
- direction;
- confidence.

Use visual features as supporting evidence.

Do not claim an uncertain appearance match as a confirmed identity.

---

# 20. Cross-Camera Vehicle Search

This is the flagship feature.

### User workflow

```text
Investigator
    |
Enter plate number
    |
Choose date/time
    |
Choose all/specific cameras
    |
Search event index
    |
Rank detections
    |
Correlate movement
    |
Show timeline
    |
Show GIS route
    |
Show evidence
```

Example:

```text
Vehicle: GJ01AB1234

10:21:34  CAM12  96%
10:29:11  CAM18  94%
10:37:52  CAM24  97%
10:44:03  CAM31  91%
```

---

# 21. Cross-Camera Correlation

Use staged filtering to remain fast.

```text
All detections
      |
Plate match
      |
Time-window filter
      |
Geographic filter
      |
Travel-time plausibility
      |
Vehicle class/color
      |
Appearance similarity
      |
Final correlation
```

This is better than comparing every vehicle against every other vehicle.

---

# 22. Movement Plausibility

Suppose:

```text
CAM12 -> CAM50
```

requires 20 minutes by road, but detections are only 2 minutes apart.

The system should mark the transition as:

**Low plausibility / rejected**

This prevents false movement routes.

---

# 23. Camera Topology

Maintain optional camera relationships:

```text
CAM12 ---> CAM18 ---> CAM24
   \                    |
    ----> CAM20 --------
```

Store:

- neighboring cameras;
- approximate distance;
- expected travel time;
- direction if known.

This makes movement reconstruction more realistic.

---

# 24. GIS — Free Only

Use:

**Leaflet**

and:

**OpenStreetMap-compatible map data/tiles**

Use:

**PostGIS**

for geospatial database operations.

No:

- Google Maps API;
- Mapbox paid APIs;
- HERE API;
- commercial GIS SaaS.

### Important zero-cost deployment rule

For a hackathon demo, standard OpenStreetMap tiles may be used in accordance with their usage policy.

For a production deployment, do **not** assume the public OSM tile servers are an unlimited free tile-hosting service. Self-host map tiles or use an approved internally hosted map service.

The application must not become dependent on a paid map provider.

---

# 25. Database — Free

## Primary database

**PostgreSQL**

PostgreSQL is free/open source and uses the PostgreSQL License.

Official:
https://www.postgresql.org/about/licence/

Add:

**PostGIS** for geospatial operations.

PostGIS is open source under GPLv2.

Official:
https://postgis.net/

Use:

- cameras;
- departments;
- users;
- detections;
- vehicle events;
- tracks;
- watchlists;
- alerts;
- investigations;
- audit logs.

---

# 26. Vector Search — Free

For vehicle appearance embeddings:

**pgvector**

Use pgvector with PostgreSQL.

This avoids paying for a hosted vector database.

MVP:

```text
PostgreSQL
 + PostGIS
 + pgvector
```

Only introduce another search system when PostgreSQL cannot meet measured requirements.

---

# 27. Search Engine — Optional Free Upgrade

If the event volume becomes large:

**OpenSearch**

OpenSearch is Apache 2.0 licensed and can be self-hosted.

Official:
https://opensearch.org/

Use it for:

- high-volume event search;
- filtering;
- full-text search;
- vector search if needed;
- analytics.

### MVP rule

Start with PostgreSQL.

Do not introduce OpenSearch before it is actually needed.

---

# 28. Cache and Fast State — Free

Do NOT depend on Redis Cloud or another paid hosted service.

Use:

**Valkey**

Valkey is open source under a BSD license.

Official:
https://valkey.io/

Use for:

- camera status;
- active alerts;
- temporary state;
- WebSocket fan-out;
- rate limiting;
- short-lived correlation state.

Permanent records remain in PostgreSQL.

---

# 29. Event Bus — Free

## MVP

Use:

**Valkey Streams**

This keeps the stack small.

## Larger self-hosted deployment

Use:

**Apache Kafka**

Kafka is open source and can be self-hosted.

Do not use Confluent Cloud or another paid managed Kafka service.

Architecture:

```text
AI Worker
   |
Event Stream
   |
+--+--------+---------+
|           |         |
Search    Alerts   Analytics
```

---

# 30. Evidence Storage — Free

Do not use AWS S3, Azure Blob or Google Cloud Storage.

## MVP

Use local filesystem storage with a clear evidence directory:

```text
data/evidence/
```

Store:

- snapshots;
- short evidence clips where permitted;
- generated reports.

Database stores:

- file path/object ID;
- SHA-256 hash;
- timestamp;
- camera;
- event ID;
- retention metadata.

## Optional scale-up

Use a self-hosted S3-compatible object store only after testing the exact license and operational requirements.

For the simplest zero-cost MVP:

> **Local filesystem + PostgreSQL metadata is enough.**

---

# 31. Backend — Free

Use:

**Python + FastAPI**

Components:

- FastAPI;
- Uvicorn;
- Pydantic;
- SQLAlchemy;
- Alembic;
- Python asyncio.

All can be installed locally without a paid subscription.

Use REST APIs for normal operations.

Use WebSockets for real-time:

- alerts;
- camera health;
- processing status.

---

# 32. Frontend — Free

Use:

- React;
- TypeScript;
- Vite;
- Tailwind CSS;
- a free/open-source UI component library;
- Leaflet;
- native WebSocket.

No:

- paid dashboard templates;
- paid UI libraries;
- paid analytics widgets.

---

# 33. Authentication — Free

Use:

### MVP

- FastAPI security;
- Argon2id password hashing;
- secure HTTP-only session cookies or JWT;
- RBAC.

### Optional self-hosted identity provider

**Keycloak**

Use only if the team needs centralized identity management.

Do not use:

- Auth0 paid plans;
- Firebase Authentication paid dependencies;
- commercial identity SaaS.

---

# 34. Roles

Create:

### Administrator
- users;
- roles;
- system settings;
- camera registry.

### Control Room Operator
- live cameras;
- alerts;
- watchlist;
- camera health.

### Investigator
- cross-camera search;
- movement timeline;
- GIS;
- evidence.

### Analyst
- analytics;
- reports;
- trends.

### Viewer
- read-only access.

---

# 35. Security Architecture

```text
Browser
   |
HTTPS
   |
Reverse Proxy
   |
FastAPI
   |
Private Services
   |
+---+------+-------+
|          |       |
DB       AI      Sentinel
```

Never expose:

- PostgreSQL;
- Valkey;
- AI workers;
- internal event streams

directly to the public network.

---

# 36. Reverse Proxy — Free

Use:

**Nginx**

or:

**Caddy**

No paid load balancer is required for the MVP.

Responsibilities:

- TLS;
- routing;
- security headers;
- request limits;
- static frontend serving.

---

# 37. TLS / HTTPS

For local development:

```text
localhost
```

For a real deployment:

- use a legitimate certificate;
- use an approved domain;
- use an internal CA if appropriate;
- never disable TLS simply to make the demo work.

No paid certificate is inherently required; free certificate authorities can be used where publicly applicable.

---

# 38. Secrets

Never put secrets in:

- React code;
- Git;
- screenshots;
- README;
- Docker image layers.

Development:

```text
.env
```

with:

```text
.env.example
```

containing placeholders only.

For a larger deployment, use a self-hosted secret manager if needed.

---

# 39. Logging — Free

Use Python structured logging.

Log:

- camera ID;
- stream state;
- reconnect count;
- processing time;
- inference errors;
- event IDs.

Never log:

- passwords;
- tokens;
- private keys;
- raw credentials.

---

# 40. Monitoring — Free

Use:

**Prometheus**

for metrics.

Prometheus is Apache 2.0 licensed.

Use:

**Grafana OSS**

for dashboards where its current license is acceptable for the intended deployment.

Alternative zero-cost approach:

- Prometheus;
- simple FastAPI `/metrics`;
- application health pages.

Monitor:

- active streams;
- reconnects;
- inference latency;
- FPS;
- CPU;
- RAM;
- GPU if present;
- queue depth;
- ANPR confidence;
- API latency.

---

# 41. No Paid Notifications

Do not depend on:

- Twilio;
- paid SMS;
- paid WhatsApp API;
- SendGrid;
- paid email APIs.

For the hackathon:

```text
Watchlist match
    |
Alert Engine
    |
WebSocket
    |
Dashboard
    |
RED ALERT
```

The alert appears instantly inside the application.

This is sufficient for the mandatory demonstration.

---

# 42. AI Processing Pipeline

```text
Sentinel RTSP
     |
RTSP/TCP
     |
Decoder
     |
Frame sampling
     |
Vehicle detection
     |
ByteTrack
     |
Vehicle crop
     |
Plate detection/OCR
     |
Plate normalization
     |
Event creation
     |
PostgreSQL
     |
Search/Correlation
```

---

# 43. Efficient Processing

Do not run heavy AI on every decoded frame.

Recommended starting approach:

```text
Stream decode
      |
Frame sampling
      |
Detector at selected FPS
      |
Tracker between detections
      |
ANPR only on useful vehicle frames
```

Tune the FPS experimentally.

A reasonable starting point is around 5 detection FPS, but the final value must be benchmarked on the available hardware and Sentinel feed.

---

# 44. Multi-Camera Resource Management

Do not open every stream unnecessarily.

Use:

### Stream Manager

Responsibilities:

- start stream;
- stop stream;
- reconnect;
- monitor health;
- limit concurrent streams;
- maintain bounded queues.

Priority:

```text
1. Evaluation cameras
2. Investigation cameras
3. Alert-related cameras
4. User live-preview cameras
5. Idle cameras
```

---

# 45. Backpressure

Every queue must be bounded.

Bad:

```text
camera -> unlimited queue -> RAM grows forever
```

Good:

```text
camera
  |
bounded queue
  |
worker
```

If AI falls behind, discard stale frames rather than allowing unlimited latency.

For live analytics:

> A fresh frame is usually more valuable than an old frame.

---

# 46. Reconnection

Use exponential backoff:

```text
1 sec
2 sec
4 sec
8 sec
16 sec
30 sec maximum
```

After successful reconnection:

- reset backoff;
- record health event;
- continue processing.

Do not crash the entire application because one camera disconnected.

---

# 47. PTS Timing

Use source PTS where available.

Do not build movement timelines solely from:

```text
frame_received_time
```

Maintain:

```text
source_pts
received_at
processed_at
```

This helps distinguish:

- actual video timing;
- network delay;
- AI processing delay.

---

# 48. H.264 / H.265

The Sentinel environment may contain both.

The pipeline must support:

- H.264;
- H.265/HEVC;
- mixed resolutions;
- stream interruptions.

Read codec information from the catalog.

Do not assume one universal codec.

---

# 49. Camera Registry Schema

Example:

```sql
CREATE TABLE cameras (
    id UUID PRIMARY KEY,
    sentinel_camera_id TEXT UNIQUE NOT NULL,
    name TEXT,
    location_name TEXT,
    department TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    vendor TEXT,
    vms TEXT,
    protocol TEXT,
    codec TEXT,
    width INTEGER,
    height INTEGER,
    fps REAL,
    rtsp_url TEXT,
    whep_url TEXT,
    hls_url TEXT,
    live_status BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

Never expose privileged RTSP credentials to the browser.

---

# 50. Vehicle Event Schema

Example:

```sql
CREATE TABLE vehicle_events (
    id UUID PRIMARY KEY,
    camera_id UUID REFERENCES cameras(id),
    track_id TEXT,
    event_time TIMESTAMPTZ NOT NULL,
    source_pts BIGINT,
    plate_raw TEXT,
    plate_normalized TEXT,
    plate_confidence REAL,
    vehicle_class TEXT,
    vehicle_color TEXT,
    detection_confidence REAL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    snapshot_path TEXT,
    embedding VECTOR,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Exact vector column syntax depends on the selected pgvector version.

---

# 51. Watchlist Schema

```text
watchlist_id
registration_number
category
description
priority
active
created_at
updated_at
```

Example:

```text
GJ01AB1234
Stolen Vehicle
HIGH
ACTIVE
```

---

# 52. Alert Schema

```text
alert_id
vehicle_event_id
registration_number
camera_id
timestamp
watchlist_id
confidence
snapshot_path
location
status
acknowledged_by
acknowledged_at
created_at
```

---

# 53. Investigation Module

Investigator should be able to:

1. Enter registration number.
2. Choose date/time.
3. Search.
4. See all detections.
5. Open an event.
6. View snapshot.
7. View camera.
8. View route.
9. See movement timeline.
10. Export a report if permitted.

---

# 54. Dashboard Pages

## Page 1 — Login

- secure login;
- role-based redirect.

## Page 2 — Control Room

Show:

- active cameras;
- alerts;
- system health;
- recent detections.

## Page 3 — Live Camera Grid

Show:

- camera cards;
- live/offline;
- location;
- protocol status.

## Page 4 — Camera Detail

Show:

- live preview;
- camera metadata;
- current detections;
- connection health.

## Page 5 — Vehicle Search

Fields:

- registration number;
- date;
- time;
- camera;
- department.

## Page 6 — Investigation

Show:

- results;
- confidence;
- snapshots;
- movement timeline.

## Page 7 — GIS

Show:

- cameras;
- route;
- detections;
- timestamps.

## Page 8 — Watchlist

CRUD:

- add;
- edit;
- activate/deactivate;
- remove.

## Page 9 — Alerts

Show:

- live alerts;
- acknowledged/unacknowledged;
- severity;
- evidence.

## Page 10 — Camera Health

Show:

- online;
- offline;
- reconnect count;
- codec;
- FPS;
- latency.

---

# 55. UI Design Principle

The interface should look like a professional command-center application.

Use:

- dark control-room theme;
- clear status badges;
- strong alert hierarchy;
- map + timeline combination;
- readable tables;
- no unnecessary animations.

Do not copy the Sentinel portal UI.

Build a better intelligence dashboard.

---

# 56. Main Demonstration Workflow

The judge should see this:

```text
1. Login
      |
2. Sentinel cameras automatically discovered
      |
3. Camera grid appears
      |
4. Live feed opened
      |
5. AI detects vehicles
      |
6. ANPR reads plates
      |
7. Vehicle event indexed
      |
8. Search GJ01AB1234
      |
9. Results appear across cameras
      |
10. Timeline generated
      |
11. GIS route generated
      |
12. Watchlist match
      |
13. Real-time alert
      |
14. Evidence/snapshot
```

This should be the primary story of the project.

---

# 57. Live Portal vs SentinelX

| Capability | Sentinel Live Portal | SentinelX |
|---|---|---|
| Camera grid | Yes | Yes |
| Camera locations | Yes | Yes |
| Live stream | Yes | Yes |
| Dynamic catalog | Source | Consumed |
| Vehicle detection | No/limited sandbox purpose | Yes |
| ANPR | No | Yes |
| Cross-camera search | No | Yes |
| Movement timeline | No | Yes |
| GIS route | Basic camera context | Vehicle route |
| Watchlist | No | Yes |
| Real-time watchlist alert | No | Yes |
| Investigation | No | Yes |
| Evidence metadata | No | Yes |
| AI analytics | No/limited | Yes |

---

# 58. Free Technology Matrix

| Layer | Free/Open-Source Choice | Paid Alternative to Avoid |
|---|---|---|
| Frontend | React + TypeScript + Vite | Paid UI builders |
| UI | Tailwind CSS | Paid UI kits |
| Backend | FastAPI | Paid API platform |
| Database | PostgreSQL | Managed DB SaaS |
| GIS DB | PostGIS | Paid GIS database |
| Vector | pgvector | Pinecone/paid vector SaaS |
| Cache | Valkey | Redis Cloud |
| Event stream | Valkey Streams | Managed streaming SaaS |
| Large event search | OpenSearch | Paid hosted search |
| Video | OpenCV | Commercial SDK |
| Video debug | FFmpeg | Commercial media SDK |
| Pipeline | GStreamer | Commercial VMS SDK |
| GPU pipeline | DeepStream if hardware exists | Paid inference service |
| Detector | YOLOX/permissive model | Paid AI API |
| Tracker | ByteTrack | Paid tracking API |
| OCR | PaddleOCR | Paid ANPR API |
| Browser live | WebRTC/WHEP | Paid video streaming SaaS |
| Playback | HLS | Paid video CDN |
| Maps | Leaflet + OSM-compatible data | Google Maps/Mapbox paid APIs |
| Auth | FastAPI + Argon2id | Auth0 paid dependency |
| SSO | Keycloak | Paid identity SaaS |
| Proxy | Nginx/Caddy | Paid gateway |
| Monitoring | Prometheus | Datadog/New Relic |
| Dashboard | Grafana OSS or custom dashboard | Paid observability SaaS |
| Evidence | Local filesystem | AWS/Azure/GCP storage |
| Containers | Docker | Paid container platform |
| Orchestration | Docker Compose | Paid managed Kubernetes |
| Notifications | In-app WebSocket | Twilio/paid SMS |
| Development | VS Code | Paid IDE |
| Git | Local Git / self-hosted Git | Paid Git hosting requirement |

---

# 59. Important Licensing Rules

"Free to download" does not automatically mean "any use is allowed."

Before adding any model or package:

1. Check source license.
2. Check model-weight license.
3. Check dependency licenses.
4. Record the information in `THIRD_PARTY_NOTICES.md`.
5. Avoid packages requiring a commercial license for the intended use.

Recommended permissive/free components include:

- PostgreSQL — PostgreSQL License;
- OpenCV 4.5+ — Apache 2.0;
- PaddleOCR — Apache 2.0;
- Valkey — BSD;
- OpenSearch — Apache 2.0;
- Prometheus — Apache 2.0;
- GStreamer — LGPL;
- FFmpeg — LGPL by default, with care around optional GPL/nonfree components;
- ByteTrack — MIT;
- YOLOX source — Apache 2.0.

Always verify the exact version and model weights used before distribution.

---

# 60. No Paid Cloud Architecture

Do not build the architecture around:

```text
AWS
Azure
Google Cloud
Firebase paid services
Supabase paid services
MongoDB Atlas paid tier
Pinecone
OpenAI API
Google Maps API
Mapbox paid APIs
Twilio
SendGrid
Auth0 paid plans
Datadog
```

The complete MVP should run on one local machine or a local LAN.

---

# 61. Local-First Architecture

```text
                    LOCAL MACHINE / LAN

+-----------------------------------------------------+
|                  SentinelX                          |
|                                                     |
|  React UI                                           |
|       |                                             |
|  FastAPI                                             |
|       |                                             |
|  +----+-------+---------+----------------------+     |
|  |            |         |                      |     |
| PostgreSQL   Valkey    AI Workers           Files   |
| PostGIS      Streams                        Evidence |
| pgvector                                            |
|                                                     |
| OpenCV / FFmpeg / GStreamer                         |
+-----------------------------------------------------+
                       |
                       | RTSP/TCP
                       v
                Sentinel Sandbox
```

No paid cloud is required.

---

# 62. Optional Multi-Machine Free Architecture

If one machine is insufficient, use machines already available to the team.

```text
Machine 1
Frontend + Backend

Machine 2
AI Workers

Machine 3
PostgreSQL + PostGIS

Machine 4
Optional search/monitoring
```

Connect them over a private LAN.

No cloud subscription is necessary.

---

# 63. Hardware Strategy

## CPU-only

Possible for:

- development;
- one/few streams;
- UI;
- database;
- basic inference.

Use:

- smaller detector;
- lower inference FPS;
- frame skipping.

## Existing NVIDIA GPU

Use:

- CUDA;
- TensorRT;
- DeepStream;
- GPU OCR if supported.

## No GPU

Do not stop development.

Build the entire pipeline with CPU support and optimize later.

---

# 64. 80,000-Camera Scalability Story

The hackathon asks how the system could scale to approximately 80,000 cameras.

Do not claim:

> "One server will process 80,000 cameras."

Instead propose:

```text
Department
   |
Regional Gateway
   |
Regional AI Workers
   |
Event Bus
   |
Central Metadata/Search
   |
State Command Centre
```

Use distributed processing.

---

# 65. Regional Architecture

```text
Region A
Cameras
  |
Stream Gateway
  |
AI Workers
  |
Events
  |
  +----------------------+
                         |
Region B                 |
Cameras                  |
  |                      |
Stream Gateway           |
  |                      |
AI Workers               |
  |                      |
Events ------------------+--> Central Event/Search
                         |
Region C                 |
Cameras                  |
  |                      |
AI Workers -------------+
```

Only metadata/events need to move centrally whenever operational requirements permit.

This reduces bandwidth.

---

# 66. Bandwidth Optimization

Do not send every raw video stream to a central server.

Instead:

```text
Camera
  |
Regional processing
  |
Detection metadata
  |
Plate/event
  |
Central system
```

For investigations, request/relay the relevant live/evidence stream.

This is more scalable.

---

# 67. Storage Strategy

Do not store everything forever.

Use retention categories:

```text
Metadata
  -> longer retention

Snapshots
  -> configurable retention

Evidence clips
  -> investigation-controlled retention

Raw video
  -> remain in existing CCTV/VMS infrastructure wherever possible
```

This supports the challenge requirement to use existing infrastructure.

---

# 68. Privacy/Security by Design

The system should include:

- RBAC;
- audit logging;
- minimal collection;
- configurable retention;
- evidence access control;
- secure storage;
- encrypted transport;
- no unnecessary facial recognition;
- no unnecessary personal-data processing.

Do not implement facial recognition as a bonus feature unless explicitly required and legally/operationally approved.

The strongest demo is vehicle intelligence.

---

# 69. Audit Trail

Record:

- who searched a vehicle;
- when;
- query parameters;
- cameras selected;
- results viewed;
- watchlist changes;
- alert acknowledgement;
- evidence access;
- user/role changes.

Audit records should be append-oriented and protected from ordinary user modification.

---

# 70. Evidence Integrity

For every saved snapshot/clip:

```text
Evidence file
     |
SHA-256
     |
Database
```

Store:

- file hash;
- creation time;
- source camera;
- source PTS;
- event ID.

This provides basic integrity verification.

---

# 71. API Design

## Camera APIs

```text
GET    /api/cameras
GET    /api/cameras/{id}
GET    /api/cameras/{id}/health
POST   /api/cameras/sync
```

## Vehicle APIs

```text
GET    /api/vehicles/search
GET    /api/vehicles/{plate}/timeline
GET    /api/vehicles/{plate}/route
```

## Watchlist

```text
GET    /api/watchlist
POST   /api/watchlist
PUT    /api/watchlist/{id}
DELETE /api/watchlist/{id}
```

## Alerts

```text
GET    /api/alerts
POST   /api/alerts/{id}/acknowledge
```

## Investigations

```text
POST   /api/investigations
GET    /api/investigations/{id}
```

## WebSocket

```text
/ws/alerts
/ws/camera-status
/ws/system-status
```

---

# 72. Sentinel Connector Service

Create a dedicated component:

```text
sentinel_connector/
```

Responsibilities:

1. Read `/api/ingest`.
2. Validate catalog response.
3. Store/update camera registry.
4. Select RTSP URL for AI.
5. Select WHEP URL for browser.
6. Select HLS fallback.
7. Monitor camera status.
8. Reconnect.
9. Expose normalized camera objects to the rest of the application.

Do not spread Sentinel-specific logic throughout the codebase.

---

# 73. Stream Manager

Create:

```text
stream_manager/
```

Responsibilities:

- stream lifecycle;
- RTSP/TCP;
- reconnect;
- backoff;
- decoder;
- PTS;
- frame queue;
- health;
- metrics.

Interface:

```python
start(camera_id)
stop(camera_id)
restart(camera_id)
get_status(camera_id)
```

---

# 74. AI Worker

Create:

```text
ai_worker/
```

Pipeline:

```text
frame
 |
detector
 |
tracker
 |
vehicle crop
 |
plate detection/OCR
 |
event builder
```

Output:

```json
{
  "camera_id": "CAM12",
  "event_time": "...",
  "plate": "GJ01AB1234",
  "plate_confidence": 0.96,
  "vehicle_class": "car",
  "track_id": "17"
}
```

---

# 75. Correlation Engine

Create:

```text
correlation/
```

Responsibilities:

- plate matching;
- time ordering;
- geographic filtering;
- travel-time validation;
- appearance similarity;
- route generation;
- confidence scoring.

Keep correlation explainable.

---

# 76. Alert Engine

Create:

```text
alerts/
```

Flow:

```text
vehicle_event
      |
watchlist lookup
      |
match
      |
alert object
      |
Valkey
      |
WebSocket
      |
Dashboard
```

No paid messaging service is needed.

---

# 77. Free Development Environment

Recommended:

### OS

Linux preferred.

Ubuntu is suitable.

Windows can be used with WSL2 if necessary.

### Editor

VS Code.

### Runtime

Python 3.x.

Node.js LTS.

### Containers

Docker Engine + Docker Compose.

### Version control

Git.

All can be used without paying for licenses.

---

# 78. Repository Structure

```text
sentinelx/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── services/
│
├── backend/
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── auth/
│   └── main.py
│
├── sentinel_connector/
│   ├── catalog.py
│   ├── rtsp.py
│   ├── whep.py
│   └── hls.py
│
├── stream_manager/
│   ├── manager.py
│   ├── reconnect.py
│   └── health.py
│
├── ai_worker/
│   ├── detector/
│   ├── tracker/
│   ├── anpr/
│   └── pipeline.py
│
├── correlation/
│   ├── matcher.py
│   ├── routing.py
│   └── scoring.py
│
├── database/
│   ├── migrations/
│   └── seed/
│
├── data/
│   └── evidence/
│
├── tests/
│
├── docs/
│
├── docker-compose.yml
├── .env.example
├── README.md
├── THIRD_PARTY_NOTICES.md
├── MODEL_LICENSES.md
└── LICENSE
```

---

# 79. Docker Compose — MVP

Services:

```text
frontend
backend
ai-worker
postgres
valkey
```

Optional:

```text
opensearch
prometheus
grafana
```

Do not start optional services until needed.

---

# 80. MVP Dependency Order

Implement in this exact order.

## Phase 1 — Sentinel connectivity

```text
Catalog
  |
Camera registry
  |
One RTSP stream
```

## Phase 2 — Live dashboard

```text
Camera registry
  |
Live camera grid
  |
WHEP/HLS preview
```

## Phase 3 — AI

```text
RTSP
 |
Detector
 |
Tracker
```

## Phase 4 — ANPR

```text
Vehicle
 |
Plate
 |
OCR
 |
Normalized plate
```

## Phase 5 — Search

```text
Events
 |
PostgreSQL
 |
Plate search
```

## Phase 6 — Cross-camera

```text
Search
 |
Correlation
 |
Timeline
 |
GIS
```

## Phase 7 — Watchlist

```text
ANPR
 |
Watchlist
 |
Alert
 |
WebSocket
```

## Phase 8 — Reliability

```text
Reconnect
Health
Metrics
Audit
Security
```

---

# 81. Testing Strategy

## Sentinel integration tests

Test:

- catalog fetch;
- dynamic camera discovery;
- RTSP/TCP;
- H.264;
- H.265;
- reconnect;
- decoder warnings;
- mixed resolutions;
- scene discontinuity.

## AI tests

Test:

- vehicle detection;
- tracking;
- plate detection;
- OCR;
- normalization.

## Search tests

Test:

- exact plate;
- partial/noisy OCR;
- time range;
- camera filter;
- department filter.

## Correlation tests

Test:

- valid route;
- impossible route;
- missing camera;
- duplicate detection;
- low-confidence OCR.

## Security tests

Test:

- unauthorized API;
- wrong role;
- invalid input;
- SQL injection;
- path traversal;
- rate limits;
- session expiry.

---

# 82. Performance Targets

These are engineering targets, not promises.

Measure:

- camera connect time;
- stream reconnect time;
- detection latency;
- ANPR latency;
- event insertion latency;
- search latency;
- alert latency;
- dashboard update latency.

Example target:

```text
Vehicle detection -> watchlist alert -> UI
```

should be near real time on the selected hardware.

Always report measured values in the final demo.

---

# 83. Security Checklist

Before demo:

- [ ] No secrets in Git.
- [ ] No Sentinel credentials in frontend.
- [ ] Protected APIs.
- [ ] RBAC enforced server-side.
- [ ] Input validation.
- [ ] SQL parameterization/ORM.
- [ ] HTTPS where deployed.
- [ ] Secure cookies/session.
- [ ] CORS restricted.
- [ ] Evidence paths protected.
- [ ] Audit logging enabled.
- [ ] Rate limiting enabled.
- [ ] Error messages do not expose secrets.
- [ ] Dependencies reviewed.
- [ ] Model licenses documented.

---

# 84. Free-Only Checklist

Before final submission:

- [ ] No paid API key required.
- [ ] No paid cloud required.
- [ ] No Google Maps API.
- [ ] No Mapbox paid dependency.
- [ ] No AWS/Azure/GCP dependency.
- [ ] No Pinecone.
- [ ] No paid OCR/ANPR service.
- [ ] No Twilio.
- [ ] No paid email service.
- [ ] No Auth0 dependency.
- [ ] No Datadog/New Relic.
- [ ] No proprietary VMS SDK unless supplied by the challenge.
- [ ] No model with an incompatible commercial license.
- [ ] All third-party licenses documented.

---

# 85. Definition of Done — Mandatory

The project is not considered complete until:

### Sentinel

- [ ] Catalog is read dynamically.
- [ ] No camera URLs are hard-coded.
- [ ] RTSP/TCP works.
- [ ] H.264 works.
- [ ] H.265 works if present.
- [ ] Reconnection works.
- [ ] PTS is handled.
- [ ] Mixed resolutions work.

### AI

- [ ] Vehicle detection works.
- [ ] Tracking works.
- [ ] ANPR works.
- [ ] Plate normalization works.
- [ ] Confidence is stored.

### Search

- [ ] Vehicle registration search works.
- [ ] Date/time filtering works.
- [ ] Camera filtering works.
- [ ] Cross-camera results work.
- [ ] Timeline works.
- [ ] GIS route works.

### Watchlist

- [ ] Watchlist CRUD works.
- [ ] Match detection works.
- [ ] Real-time alert works.
- [ ] Alert acknowledgement works.

### Security

- [ ] Login works.
- [ ] RBAC works.
- [ ] Audit logging works.
- [ ] Secrets are protected.

### Cost

- [ ] No paid external service is required.
- [ ] Project runs locally/LAN.
- [ ] Third-party license list is complete.

---

# 86. Antigravity Master Instruction

Use the following as the main instruction to Antigravity:

> Build SentinelX according to this specification.
>
> The project must be **free/open-source and local-first**. Do not add any paid API, cloud service, SaaS dependency, paid map service, paid AI service, paid OCR service, paid notification service, or commercial SDK.
>
> First implement the Sentinel connector and dynamic `/api/ingest` camera catalog. Never hard-code camera URLs or assume a fixed camera count.
>
> Implement RTSP over TCP as the primary AI ingestion path. Support H.264/H.265, PTS timing, reconnect with exponential backoff, bounded queues, mixed resolutions and stream discontinuity.
>
> Use OpenCV/FFmpeg initially. Keep GStreamer as the scalable video pipeline. Use DeepStream/TensorRT only when compatible NVIDIA hardware already exists.
>
> Implement a permissively licensed object detector, ByteTrack for tracking, and PaddleOCR for ANPR. Keep model code and model weights/license information documented.
>
> Use PostgreSQL + PostGIS + pgvector as the primary data platform. Use Valkey for cache/streams. Do not introduce OpenSearch/Kafka until performance measurements justify them.
>
> Implement:
>
> 1. Authentication/RBAC
> 2. Dynamic CCTV registry
> 3. Sentinel stream manager
> 4. Live camera grid
> 5. Vehicle detection
> 6. Tracking
> 7. ANPR
> 8. Vehicle event indexing
> 9. Cross-camera vehicle search
> 10. Movement timeline
> 11. GIS route
> 12. Watchlist
> 13. Real-time in-app alerts
> 14. Investigation/evidence
> 15. Camera health
> 16. Audit logs
> 17. Metrics
>
> The primary judge demonstration must be:
>
> **Sentinel live cameras → vehicle detection → ANPR → registration-number search → cross-camera results → movement timeline → GIS route → watchlist match → real-time alert → evidence.**
>
> Keep the code modular, documented, testable and easy to run using Docker Compose.
>
> Do not over-engineer the MVP. Build the mandatory evaluation flow first, then add scalability and bonus capabilities.
>
> Never expose Sentinel credentials or privileged stream URLs to the browser.
>
> Never implement unnecessary facial recognition.
>
> Do not claim statewide performance until the system has been benchmarked. For the 80,000-camera architecture, explain regional gateways, distributed AI workers, metadata-first centralization and existing-VMS preservation.

---

# 87. Final Architecture

```text
                       SENTINEL
                          |
                    /api/ingest
                          |
                  Dynamic Catalog
                          |
             +------------+------------+
             |            |            |
            RTSP         WHEP         HLS
             |            |            |
             |            |       Browser fallback
             |            |
             |        Live preview
             |
         RTSP/TCP
             |
       Stream Manager
             |
       OpenCV/FFmpeg
             |
      GStreamer optional
             |
       AI Worker
             |
     +-------+--------+
     |       |        |
 Detector  Tracker   ANPR
     |       |        |
     +-------+--------+
             |
       Vehicle Events
             |
      PostgreSQL/PostGIS
             |
          pgvector
             |
     Cross-Camera Engine
             |
      +------+------+------+
      |      |      |      |
     GIS  Timeline Search Watchlist
                            |
                         Alert
                            |
                       WebSocket
                            |
                       Dashboard
```

---

# 88. Final Technology Decision

## Use these first

```text
Frontend:
React + TypeScript + Vite + Tailwind

Backend:
Python + FastAPI

Database:
PostgreSQL + PostGIS + pgvector

Fast state:
Valkey

Video:
OpenCV + FFmpeg

Scalable video:
GStreamer

Detection:
YOLOX/permissively licensed detector

Tracking:
ByteTrack

OCR:
PaddleOCR

GIS:
Leaflet + OSM-compatible data

Auth:
FastAPI security + Argon2id + RBAC

Live alerts:
WebSocket

Storage:
Local filesystem + PostgreSQL metadata

Monitoring:
Prometheus

Containers:
Docker + Docker Compose
```

## Add only when necessary

```text
OpenSearch
Apache Kafka
DeepStream
TensorRT
Grafana
Keycloak
Kubernetes
```

All can be self-hosted without paid SaaS.

---

# 89. Bottom Line

The best zero-cost strategy is **not** to find a free replacement for every commercial product.

It is to design the platform so that:

```text
Sentinel
   +
Open-source software
   +
Existing team hardware
   +
Local/LAN deployment
   =
Complete working hackathon solution
```

The solution should be:

**Free to build + fast enough for the demo + secure + modular + scalable in architecture + independent of paid services.**

---

# 90. License / Reference Notes

The following official sources should be checked when preparing the final `THIRD_PARTY_NOTICES.md`:

- PostgreSQL License: https://www.postgresql.org/about/licence/
- OpenCV License: https://opencv.org/license/
- PostGIS License FAQ: https://postgis.net/documentation/faq/gpl-license/
- Valkey: https://valkey.io/
- OpenSearch: https://opensearch.org/faq/
- Prometheus: https://prometheus.io/docs/introduction/faq/
- GStreamer licensing: https://gstreamer.freedesktop.org/documentation/frequently-asked-questions/licensing.html
- FFmpeg License: https://ffmpeg.org/doxygen/trunk/md_LICENSE.html
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- YOLOX: https://github.com/Megvii-BaseDetection/YOLOX
- ByteTrack: https://github.com/ifzhang/ByteTrack

**Always verify the exact version, plugins, model weights and datasets used.**
