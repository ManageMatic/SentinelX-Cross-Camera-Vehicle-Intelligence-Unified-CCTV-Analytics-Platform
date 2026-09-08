"""Comprehensive Software Requirements Specification (SRS) Generator for SentinelX.

Generates:
1. docs/SOFTWARE_REQUIREMENTS_SPECIFICATION_SRS.docx (Microsoft Word)
2. docs/SOFTWARE_REQUIREMENTS_SPECIFICATION_SRS.pdf (Adobe PDF)
3. docs/SOFTWARE_REQUIREMENTS_SPECIFICATION_SRS.md (Markdown)
"""

import os
import sys
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

DOCX_PATH = DOCS_DIR / "SOFTWARE_REQUIREMENTS_SPECIFICATION_SRS.docx"
PDF_PATH = DOCS_DIR / "SOFTWARE_REQUIREMENTS_SPECIFICATION_SRS.pdf"
MD_PATH = DOCS_DIR / "SOFTWARE_REQUIREMENTS_SPECIFICATION_SRS.md"

# -------------------------------------------------------------
# 1. MARKDOWN CONTENT GENERATION
# -------------------------------------------------------------
srs_markdown = """# Software Requirements Specification (SRS)
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
"""

# Write Markdown SRS
with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(srs_markdown)
print(f"Generated Markdown SRS: {MD_PATH}")

# -------------------------------------------------------------
# 2. WORD (.DOCX) GENERATION USING python-docx
# -------------------------------------------------------------
try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn

    doc = docx.Document()

    # Set Margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Title Banner
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("SOFTWARE REQUIREMENTS SPECIFICATION (SRS)")
    title_run.font.name = "Arial"
    title_run.font.size = Pt(20)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(11, 46, 89)

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform\nGujarat Police Innovation Challenge 2026")
    sub_run.font.name = "Arial"
    sub_run.font.size = Pt(12)
    sub_run.font.color.rgb = RGBColor(70, 80, 95)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Metadata Table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Project Name", "SentinelX — Cross-Camera Vehicle Intelligence Platform"),
        ("Target Challenge", "Gujarat Police Innovation Challenge 2026 (GPIC 2026)"),
        ("Document Version", "1.0.0 (Official Release)"),
        ("Cost & License Policy", "₹0 Software Licensing Cost / 100% Free & Open-Source"),
        ("Architecture Model", "Hybrid Federated Edge-Metadata Intelligence (80k Camera Scalable)"),
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        row = meta_table.rows[row_idx]
        cell_0 = row.cells[0]
        cell_1 = row.cells[1]
        cell_0.text = k
        cell_1.text = v
        cell_0.paragraphs[0].runs[0].font.bold = True
        cell_0.paragraphs[0].runs[0].font.size = Pt(9.5)
        cell_1.paragraphs[0].runs[0].font.size = Pt(9.5)
        # Background color for key
        shading = parse_xml(r'<w:shd {} w:fill="F1F5F9"/>'.format(nsdecls('w')))
        cell_0._tc.get_or_add_tcPr().append(shading)

    doc.add_page_break()

    # Helper function for adding styled headings
    def add_custom_heading(text, level):
        h = doc.add_heading(text, level=level)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        if level == 1:
            h.runs[0].font.color.rgb = RGBColor(11, 46, 89)
            h.runs[0].font.size = Pt(14)
        elif level == 2:
            h.runs[0].font.color.rgb = RGBColor(2, 132, 199)
            h.runs[0].font.size = Pt(12)
        return h

    # Section 1
    add_custom_heading("1. Executive Summary & Introduction", 1)
    p = doc.add_paragraph(
        "SentinelX is an advanced, vendor-neutral CCTV intelligence platform built for the Gujarat Police Innovation "
        "Challenge 2026. The platform seamlessly bridges heterogeneous CCTV networks across government departments, "
        "enabling real-time cross-camera vehicle tracking, automatic license plate recognition (ANPR), and movement "
        "reconstruction on interactive GIS maps with zero proprietary licensing costs."
    )
    p.paragraph_format.line_spacing = 1.15

    add_custom_heading("1.1 Core Flagship Objective", 2)
    p_box = doc.add_paragraph()
    p_box_run = p_box.add_run(
        "\"Enter a vehicle registration number -> Search indexed CCTV metadata across cameras -> "
        "Reconstruct chronological movement -> Show route on GIS OpenStreetMap -> Check watchlists -> "
        "Generate real-time WebSocket Red Alerts -> Preserve cryptographically verified SHA-256 evidence.\""
    )
    p_box_run.font.italic = True
    p_box_run.font.bold = True
    p_box_run.font.color.rgb = RGBColor(15, 23, 42)

    add_custom_heading("1.2 Zero-Cost & Open-Source Policy", 2)
    doc.add_paragraph(
        "The entire platform is engineered strictly with ₹0 commercial licensing cost. It prohibits reliance on paid cloud "
        "hosting (AWS, Azure, GCP), paid vector databases (Pinecone), paid AI/OCR APIs (OpenAI, commercial OCR), paid map "
        "services (Google Maps, Mapbox), paid SMS/WhatsApp gateways, or commercial VMS SDKs."
    )

    # Section 2
    add_custom_heading("2. System Architecture & High-Level Design", 1)
    doc.add_paragraph(
        "SentinelX uses a federated metadata-driven architecture. Video ingestion workers connect to Sentinel live cameras "
        "via RTSP over TCP. Bounded frame queues feed an AI pipeline (YOLOX + ByteTrack + PaddleOCR). Extracted vehicle events "
        "are indexed in PostgreSQL + PostGIS. The Cross-Camera Correlation engine evaluates spatial-temporal plausibility, "
        "while WebSocket dispatchers push instant alerts to the React Command Center."
    )

    add_custom_heading("2.1 Data Models & Core Entities", 2)
    models_table = doc.add_table(rows=1, cols=3)
    models_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = models_table.rows[0]
    hdr.cells[0].text = "Entity / Table"
    hdr.cells[1].text = "Key Fields"
    hdr.cells[2].text = "Operational Purpose"
    for cell in hdr.cells:
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        shading = parse_xml(r'<w:shd {} w:fill="0B2E59"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading)

    table_data = [
        ("cameras", "id, external_camera_id, name, lat, lon, rtsp_url, whep_url, live_status", "Dynamic registry synchronized from /api/ingest"),
        ("vehicle_events", "id, camera_id, event_time, plate_normalized, vehicle_class, lat, lon", "Core searchable vehicle sighting metadata index"),
        ("vehicle_tracks", "id, camera_id, track_id, first_seen, last_seen, total_frames", "ByteTrack single-camera multi-frame track associations"),
        ("vehicle_plates", "id, event_id, plate_text, plate_normalized, confidence, crop_path", "Detailed OCR plate readings from PaddleOCR"),
        ("vehicle_embeddings", "id, event_id, model_name, embedding_dim, vector_data", "512-dim visual appearance feature vectors for Re-ID"),
        ("watchlists", "id, name, category (STOLEN, WANTED, SUSPICIOUS), is_active", "Hotlist definitions linked to CID Crime FIRs"),
        ("alerts", "id, vehicle_event_id, status (NEW, ACKNOWLEDGED), alert_time", "Real-time security hit alerts dispatched to dashboard"),
        ("evidence", "id, camera_id, file_path, sha256_hash, captured_at", "Forensic evidence vault with cryptographic verification"),
        ("audit_logs", "id, username, action, resource_type, timestamp, ip_address", "Immutable append-only audit trail for all user operations"),
    ]
    for ent, flds, purp in table_data:
        r = models_table.add_row()
        r.cells[0].text = ent
        r.cells[1].text = flds
        r.cells[2].text = purp
        r.cells[0].paragraphs[0].runs[0].font.bold = True
        r.cells[0].paragraphs[0].runs[0].font.size = Pt(8.5)
        r.cells[1].paragraphs[0].runs[0].font.size = Pt(8.5)
        r.cells[2].paragraphs[0].runs[0].font.size = Pt(8.5)

    # Section 3
    add_custom_heading("3. Functional Requirements (FR)", 1)
    fr_items = [
        ("FR-01: Dynamic Catalog Ingestion", "The system SHALL query GET /api/ingest dynamically without hard-coded camera IDs or counts."),
        ("FR-02: RTSP/TCP Stream Ingestion", "Ingestion workers SHALL enforce RTSP over TCP with exponential backoff (1s -> 30s) reconnects."),
        ("FR-03: AI Vehicle Detection & Tracking", "The vision pipeline SHALL detect vehicles (car, bike, bus, truck) and maintain tracks via ByteTrack."),
        ("FR-04: ANPR & Plate Normalization", "PaddleOCR SHALL extract plate characters and normalize Indian registration formats (e.g. GJ01AB1234)."),
        ("FR-05: Historical Metadata Search", "The search engine SHALL query indexed database events in < 200ms without seeking live RTSP streams."),
        ("FR-06: Cross-Camera Correlation", "The system SHALL reconstruct journeys across cameras using travel-time and speed plausibility filters."),
        ("FR-07: Leaflet GIS Route Mapping", "The UI SHALL display camera markers and chronological route polylines on interactive OpenStreetMap."),
        ("FR-08: Watchlist Matching & Red Alerts", "Detections matching active watchlists SHALL trigger immediate WebSocket Red Alerts with snapshot crops."),
        ("FR-09: Cryptographic Evidence Integrity", "Every stored evidence snapshot SHALL have a SHA-256 hash stored in the database for chain of custody."),
        ("FR-10: RBAC & Immutable Audit Logs", "All searches, edits, alert acknowledgments, and exports SHALL be recorded in append-only audit logs."),
    ]
    for title, desc in fr_items:
        p_fr = doc.add_paragraph()
        r_title = p_fr.add_run(f"• {title}: ")
        r_title.bold = True
        r_title.font.color.rgb = RGBColor(11, 46, 89)
        p_fr.add_run(desc)

    # Section 4
    add_custom_heading("4. 80,000-Camera Statewide Scalability Blueprint", 1)
    doc.add_paragraph(
        "To support statewide scalability across approximately 80,000 cameras in Gujarat, SentinelX implements an Edge-Metadata "
        "Federated Architecture:\n"
        "1. Regional Edge Ingestion: Local edge workers decode camera streams and perform AI detection at the district/city level.\n"
        "2. Metadata-Only Central Stream: Only lightweight detection events (~1 KB JSON) and alert events are transmitted centrally, "
        "reducing state-wide CCTV network bandwidth by over 99%.\n"
        "3. Local VMS Storage Preservation: Raw video remains stored on existing local NVR/VMS infrastructure; high-resolution video is "
        "only fetched on-demand during active criminal investigations."
    )

    doc.save(str(DOCX_PATH))
    print(f"Generated Word (.docx) SRS: {DOCX_PATH}")

except Exception as e:
    print(f"Error creating DOCX: {e}")

# -------------------------------------------------------------
# 3. PDF GENERATION USING reportlab
# -------------------------------------------------------------
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
    )

    pdf = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    # Custom Styles
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0B2E59'),
        alignment=1,
    )
    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1,
    )
    style_h1 = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0B2E59'),
        spaceBefore=14,
        spaceAfter=6,
    )
    style_h2 = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0284C7'),
        spaceBefore=10,
        spaceAfter=4,
    )
    style_body = ParagraphStyle(
        'BodyDark',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#1E293B'),
    )
    style_callout = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0F172A'),
        backColor=colors.HexColor('#F8FAFC'),
        borderColor=colors.HexColor('#0284C7'),
        borderWidth=1,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6,
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("SOFTWARE REQUIREMENTS SPECIFICATION (SRS)", style_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>SentinelX — Cross-Camera Vehicle Intelligence & Unified CCTV Analytics Platform</b><br/>Gujarat Police Innovation Challenge 2026", style_subtitle))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0B2E59'), spaceBefore=2, spaceAfter=10))

    # Summary Metadata Box
    meta_table_data = [
        [Paragraph("<b>Project Target:</b>", style_body), Paragraph("Gujarat Police Innovation Challenge 2026", style_body)],
        [Paragraph("<b>Document Version:</b>", style_body), Paragraph("1.0.0 (Official Technical Release)", style_body)],
        [Paragraph("<b>Cost & License:</b>", style_body), Paragraph("₹0 Licensing Cost · 100% Free & Open-Source (Apache-2.0 / MIT / BSD / PostgreSQL)", style_body)],
        [Paragraph("<b>Architecture:</b>", style_body), Paragraph("Hybrid Federated Edge-Metadata Intelligence (80,000 Camera Scalable)", style_body)],
    ]
    meta_t = Table(meta_table_data, colWidths=[120, 400])
    meta_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_t)
    story.append(Spacer(1, 12))

    # Section 1
    story.append(Paragraph("1. Executive Summary & Purpose", style_h1))
    story.append(Paragraph(
        "SentinelX is a unified, vendor-neutral CCTV intelligence platform built for the Gujarat Police Innovation Challenge 2026. "
        "The system normalizes heterogeneous video streams across independent departmental VMS networks to deliver real-time vehicle "
        "tracking, license plate recognition (ANPR), journey reconstruction, and instant watchlist security alerts without commercial cloud or API dependencies.",
        style_body
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Flagship User Story:</b> Enter vehicle registration number -> Search indexed detections across cameras -> Reconstruct movement timeline -> "
        "Visualize route on OpenStreetMap GIS -> Check watchlists -> Dispatch real-time WebSocket Red Alerts -> Export SHA-256 verified evidence.",
        style_callout
    ))

    # Section 2
    story.append(Paragraph("2. High-Level Architecture & Entity Schema", style_h1))
    story.append(Paragraph(
        "SentinelX combines dynamic catalog ingestion from <code>/api/ingest</code>, RTSP over TCP stream ingestion, AI vision workers (YOLOX + ByteTrack + PaddleOCR), "
        "and PostgreSQL/PostGIS metadata indexing.",
        style_body
    ))
    story.append(Spacer(1, 6))

    pdf_table_data = [
        [Paragraph("<b>Entity / Table</b>", style_body), Paragraph("<b>Key Attributes</b>", style_body), Paragraph("<b>Operational Function</b>", style_body)],
        [Paragraph("<code>cameras</code>", style_body), Paragraph("id, external_camera_id, name, lat, lon, rtsp_url, whep_url, live_status", style_body), Paragraph("Dynamic CCTV registry consumed from /api/ingest", style_body)],
        [Paragraph("<code>vehicle_events</code>", style_body), Paragraph("id, camera_id, event_time, plate_normalized, vehicle_class, lat, lon", style_body), Paragraph("Searchable vehicle sighting metadata index", style_body)],
        [Paragraph("<code>vehicle_tracks</code>", style_body), Paragraph("id, camera_id, track_id, first_seen, last_seen, total_frames", style_body), Paragraph("ByteTrack single-camera multi-frame track continuity", style_body)],
        [Paragraph("<code>vehicle_plates</code>", style_body), Paragraph("id, event_id, plate_text, plate_normalized, confidence", style_body), Paragraph("PaddleOCR optical character readings and confidence", style_body)],
        [Paragraph("<code>vehicle_embeddings</code>", style_body), Paragraph("id, event_id, model_name, embedding_dim, vector_data", style_body), Paragraph("512-dim visual appearance vectors for Re-ID", style_body)],
        [Paragraph("<code>watchlists</code>", style_body), Paragraph("id, name, category (STOLEN, WANTED, SUSPICIOUS), is_active", style_body), Paragraph("Hotlists linked to active FIR cases", style_body)],
        [Paragraph("<code>alerts</code>", style_body), Paragraph("id, vehicle_event_id, status (NEW, ACKNOWLEDGED), alert_time", style_body), Paragraph("Real-time security hit alerts dispatched to dashboard", style_body)],
        [Paragraph("<code>evidence</code>", style_body), Paragraph("id, camera_id, file_path, sha256_hash, captured_at", style_body), Paragraph("Forensic snapshot vault with SHA-256 chain of custody", style_body)],
        [Paragraph("<code>audit_logs</code>", style_body), Paragraph("id, username, action, resource_type, timestamp, ip_address", style_body), Paragraph("Immutable append-only forensic user action trail", style_body)],
    ]
    pdf_t = Table(pdf_table_data, colWidths=[90, 240, 190])
    pdf_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0B2E59')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94A3B8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(pdf_t)
    story.append(Spacer(1, 10))

    # Section 3
    story.append(Paragraph("3. Functional Requirements (FR)", style_h1))
    fr_list = [
        "<b>FR-01 (Dynamic Ingestion):</b> Query <code>GET /api/ingest</code> dynamically. Never hardcode camera counts or endpoints.",
        "<b>FR-02 (RTSP/TCP & Resilient Reconnection):</b> Enforce RTSP over TCP with exponential backoff (1s -> 30s) and bounded queues.",
        "<b>FR-03 (Detection & ByteTracking):</b> YOLOX detects vehicles; ByteTrack assigns persistent track IDs across frames.",
        "<b>FR-04 (ANPR OCR & Plate Normalization):</b> PaddleOCR extracts plates and normalizes registration formats (e.g. <code>GJ01AB1234</code>).",
        "<b>FR-05 (Historical Event Search):</b> Queries indexed metadata in < 200ms without seeking raw RTSP streams.",
        "<b>FR-06 (Cross-Camera Correlation Engine):</b> Reconstructs multi-camera journeys using travel-time plausibility filters.",
        "<b>FR-07 (Leaflet GIS Route Visualization):</b> Renders camera markers and journey polylines on interactive OpenStreetMap.",
        "<b>FR-08 (Watchlist & Real-Time Alerts):</b> Matches plates against watchlists and dispatches WebSocket Red Alerts in < 500ms.",
        "<b>FR-09 (Evidence Vault & SHA-256):</b> Records cryptographic SHA-256 hashes for all evidence snapshots.",
        "<b>FR-10 (RBAC & Forensic Audit Logging):</b> Enforces role access (Admin, Operator, Investigator) and logs all user actions.",
    ]
    for item in fr_list:
        story.append(Paragraph(f"• {item}", style_body))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 8))

    # Section 4
    story.append(Paragraph("4. 80,000-Camera Scalability & Evaluation Workflow", style_h1))
    story.append(Paragraph(
        "<b>Statewide Scalability:</b> SentinelX scales to 80,000 cameras using regional edge gateways that extract metadata locally, "
        "transmitting only lightweight JSON detection events (~1 KB) to the central command center, reducing network bandwidth by > 99%.<br/><br/>"
        "<b>Mandatory Evaluation Script:</b> 1. Dynamic Catalog Discovery -> 2. Live CCTV Grid -> 3. Vehicle Detection & ANPR -> "
        "4. Vehicle Search (<code>GJ01AB1234</code>) -> 5. Cross-Camera Correlation -> 6. Movement Timeline & GIS Route -> 7. Watchlist Red Alert -> 8. Evidence & Audit.",
        style_body
    ))

    pdf.build(story)
    print(f"Generated PDF SRS: {PDF_PATH}")

except Exception as e:
    print(f"Error creating PDF: {e}")
