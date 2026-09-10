"""Comprehensive Unit Tests for Append-Only Audit Logging Engine (Module 21)."""

import json

import pytest
from app.db.session import AsyncSessionLocal
from app.main import app
from app.schemas.audit import (
    AuditAction,
    AuditExportFormat,
    AuditExportRequest,
    AuditStatus,
)
from app.services.audit_service import audit_service
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_log_action_and_retrieval():
    """Test append-only log record insertion and details serialization."""
    async with AsyncSessionLocal() as session:
        entry = await audit_service.log_action(
            db=session,
            username="OFFICER-AHM-101",
            action=AuditAction.VEHICLE_SEARCH,
            resource_type="VEHICLE_PLATE",
            resource_id="GJ01AB1234",
            ip_address="192.168.1.50",
            user_agent="Mozilla/5.0 SentinelX",
            details={"search_mode": "FUZZY", "max_distance": 1, "matches_found": 3},
            status=AuditStatus.SUCCESS,
        )

        assert entry.id is not None
        assert entry.username == "OFFICER-AHM-101"
        assert entry.action == "VEHICLE_SEARCH"
        assert entry.resource_id == "GJ01AB1234"
        assert entry.status == "SUCCESS"
        assert "FUZZY" in entry.details


@pytest.mark.asyncio
async def test_query_audit_logs_filters():
    """Test multi-parameter filtering across audit trail records."""
    async with AsyncSessionLocal() as session:
        # Create a series of distinct audit entries
        await audit_service.log_action(
            db=session,
            username="INSPECTOR-PATEL",
            action=AuditAction.WATCHLIST_CREATE,
            resource_type="WATCHLIST",
            resource_id="WL-STOLEN-2026",
            status=AuditStatus.SUCCESS,
        )
        await audit_service.log_action(
            db=session,
            username="INSPECTOR-PATEL",
            action=AuditAction.ALERT_ACK,
            resource_type="ALERT",
            resource_id="ALT-999",
            status=AuditStatus.SUCCESS,
        )
        await audit_service.log_action(
            db=session,
            username="DISPATCHER-02",
            action=AuditAction.ALERT_DISMISS,
            resource_type="ALERT",
            resource_id="ALT-1000",
            status=AuditStatus.FAILURE,
        )

        # 1. Filter by username
        patel_logs, count1 = await audit_service.query_logs(
            db=session, username="INSPECTOR-PATEL"
        )
        assert count1 >= 2
        assert all(log.username == "INSPECTOR-PATEL" for log in patel_logs)

        # 2. Filter by action
        ack_logs, count2 = await audit_service.query_logs(
            db=session, action="ALERT_ACK"
        )
        assert count2 >= 1
        assert all(log.action == "ALERT_ACK" for log in ack_logs)

        # 3. Filter by status
        fail_logs, count3 = await audit_service.query_logs(
            db=session, status="FAILURE"
        )
        assert count3 >= 1
        assert any(log.username == "DISPATCHER-02" for log in fail_logs)



@pytest.mark.asyncio
async def test_export_audit_trail_formats():
    """Test compliance export generation in CSV, JSON, and NDJSON with cryptographic checksums."""
    async with AsyncSessionLocal() as session:
        # Seed test audit log
        await audit_service.log_action(
            db=session,
            username="CHIEF-AUDITOR",
            action=AuditAction.EVIDENCE_ACCESS,
            resource_type="EVIDENCE",
            resource_id="EV-TEST-EXPORT",
            status=AuditStatus.SUCCESS,
        )

        # 1. Export CSV
        csv_req = AuditExportRequest(export_format=AuditExportFormat.CSV, officer_badge="AUDIT-OFFICER-1")
        csv_res = await audit_service.export_audit_trail(session, csv_req)
        assert csv_res.format == "CSV"
        assert "Audit_ID,Timestamp_UTC,Username_Badge" in csv_res.content
        assert len(csv_res.export_sha256) == 64

        # 2. Export JSON
        json_req = AuditExportRequest(export_format=AuditExportFormat.JSON)
        json_res = await audit_service.export_audit_trail(session, json_req)
        assert json_res.format == "JSON"
        parsed = json.loads(json_res.content)
        assert isinstance(parsed, list)
        assert len(parsed) >= 1

        # 3. Export NDJSON
        ndjson_req = AuditExportRequest(export_format=AuditExportFormat.NDJSON)
        ndjson_res = await audit_service.export_audit_trail(session, ndjson_req)
        assert ndjson_res.format == "NDJSON"
        assert len(ndjson_res.content.splitlines()) >= 1


@pytest.mark.asyncio
async def test_verify_audit_hash_chain():
    """Test sequential cryptographic hash chaining across immutable audit trail."""
    async with AsyncSessionLocal() as session:
        verification = await audit_service.verify_audit_chain(session)
        assert verification.verified_chain is True
        assert len(verification.chain_sha256) == 64
        assert verification.anomalies_detected == 0


@pytest.mark.asyncio
async def test_audit_rest_api_endpoints():
    """Test full REST API integration for Audit Trail endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Post new audit log via API
        log_resp = await client.post(
            "/api/v1/audit/log",
            json={
                "username": "POLICE-OPERATOR-99",
                "action": "VEHICLE_SEARCH",
                "resource_type": "PLATE_SEARCH",
                "resource_id": "GJ01XY7777",
                "details": {"query": "GJ01XY7777", "filters": "EXACT"},
                "status": "SUCCESS",
            },
        )
        assert log_resp.status_code == 201
        log_data = log_resp.json()["data"]
        audit_id = log_data["id"]
        assert log_data["username"] == "POLICE-OPERATOR-99"

        # 2. Query audit logs
        list_resp = await client.get("/api/v1/audit?username=POLICE-OPERATOR-99")
        assert list_resp.status_code == 200
        assert list_resp.json()["data"]["total"] >= 1

        # 3. Get single audit log
        get_resp = await client.get(f"/api/v1/audit/{audit_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["id"] == audit_id

        # 4. Export audit report via API
        export_resp = await client.post(
            "/api/v1/audit/export",
            json={"export_format": "CSV", "officer_badge": "INSP-01"},
        )
        assert export_resp.status_code == 200
        assert "export_sha256" in export_resp.json()["data"]

        # 5. Verify cryptographic hash chain via API
        chain_resp = await client.post("/api/v1/audit/verify-chain")
        assert chain_resp.status_code == 200
        assert chain_resp.json()["data"]["verified_chain"] is True

        # 6. Telemetry endpoint
        telem_resp = await client.get("/api/v1/audit/telemetry")
        assert telem_resp.status_code == 200
        assert telem_resp.json()["data"]["total_logs"] >= 1
