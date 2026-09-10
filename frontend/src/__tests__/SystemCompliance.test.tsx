import { render, screen, fireEvent, cleanup, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { EvidencePage } from '../pages/EvidencePage';
import { AuditPage } from '../pages/AuditPage';
import { SystemPage } from '../pages/SystemPage';
import { EvidenceRecord, AuditRecord, SystemHealthResponse } from '../types';

const mockEvidence: EvidenceRecord[] = [
  {
    id: 'ev-01',
    file_name: 'CAM_AHM_001_SNAPSHOT.jpg',
    file_type: 'image/jpeg',
    file_size_bytes: 428912,
    sha256_hash: '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    camera_id: 'cam-01',
    camera_name: 'Ahmedabad Junction Entry Gate',
    captured_at: new Date().toISOString(),
    is_verified: true,
    chain_of_custody_count: 4,
  },
  {
    id: 'ev-02',
    file_name: 'CAM_SUR_001_CLIP.mp4',
    file_type: 'video/mp4',
    file_size_bytes: 4891200,
    sha256_hash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    camera_id: 'cam-02',
    camera_name: 'Surat Ring Road Entry',
    captured_at: new Date().toISOString(),
    is_verified: true,
    chain_of_custody_count: 3,
  },
];

const mockAuditLogs: AuditRecord[] = [
  {
    id: 'aud-01',
    timestamp: new Date().toISOString(),
    username: 'inspector_patel',
    role: 'COMMAND_OFFICER',
    action: 'ALERT_DISPATCH',
    resource_type: 'ALERT',
    resource_id: 'alert-001',
    ip_address: '10.24.100.15',
    status: 'SUCCESS',
  },
  {
    id: 'aud-02',
    timestamp: new Date().toISOString(),
    username: 'analyst_sharma',
    role: 'ANALYST',
    action: 'ANPR_SEARCH',
    resource_type: 'VEHICLE_INDEX',
    resource_id: 'GJ01AB1234',
    ip_address: '10.24.100.22',
    status: 'SUCCESS',
  },
];

const mockHealth: SystemHealthResponse = {
  status: 'healthy',
  service: 'NETRA-X Core Backend',
  version: '1.0.0',
  environment: 'production-evaluation',
};

describe('System Health, Forensic Vault & Compliance Audit UI (Module 28)', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    cleanup();
  });

  /* ==================== EvidencePage Tests ==================== */
  describe('EvidencePage Component', () => {
    it('renders Cryptographic Evidence Vault header and Section 65B compliance', () => {
      render(<EvidencePage evidence={mockEvidence} />);

      expect(screen.getAllByText(/CRYPTOGRAPHIC EVIDENCE VAULT/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/SECTION 65B EVIDENCE ACT COMPLIANT/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('CAM_AHM_001_SNAPSHOT.jpg').length).toBeGreaterThan(0);
    });

    it('verifies cryptographic hash on button click', () => {
      render(<EvidencePage evidence={mockEvidence} />);

      const verifyBtns = screen.getAllByRole('button', { name: /Verify Hash/i });
      fireEvent.click(verifyBtns[0]);

      act(() => {
        vi.advanceTimersByTime(800);
      });

      expect(screen.getAllByText(/Cryptographic SHA-256 verification passed/i).length).toBeGreaterThan(0);
    });

    it('opens Chain of Custody detail modal', () => {
      render(<EvidencePage evidence={mockEvidence} />);

      const custBtns = screen.getAllByRole('button', { name: /Chain of Custody/i });
      fireEvent.click(custBtns[0]);

      expect(screen.getAllByText(/CHAIN OF CUSTODY AUDIT:/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/PAYLOAD SHA-256 HASH/i).length).toBeGreaterThan(0);
    });
  });

  /* ==================== AuditPage Tests ==================== */
  describe('AuditPage Component', () => {
    it('renders Forensic Audit Trail header and audit records', () => {
      render(<AuditPage logs={mockAuditLogs} />);

      expect(screen.getAllByText(/FORENSIC AUDIT TRAIL/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/APPEND-ONLY COMPLIANCE LOGS/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('inspector_patel').length).toBeGreaterThan(0);
    });

    it('filters audit logs by user role dropdown', () => {
      render(<AuditPage logs={mockAuditLogs} />);

      const roleSelect = screen.getAllByRole('combobox')[0];
      fireEvent.change(roleSelect, { target: { value: 'ANALYST' } });

      expect(screen.getAllByText('analyst_sharma').length).toBeGreaterThan(0);
      expect(screen.queryByText('inspector_patel')).not.toBeInTheDocument();
    });

    it('exports audit log to CSV format', () => {
      render(<AuditPage logs={mockAuditLogs} />);

      const exportBtn = screen.getAllByRole('button', { name: /Export Audit Log/i })[0];
      fireEvent.click(exportBtn);

      expect(screen.getAllByText(/Exported \d+ audit trail records to CSV/i).length).toBeGreaterThan(0);
    });
  });

  /* ==================== SystemPage Tests ==================== */
  describe('SystemPage Component', () => {
    it('renders component vitals and cluster health metrics', () => {
      render(<SystemPage status={null} health={mockHealth} />);

      expect(screen.getAllByText(/HEALTH & INFRASTRUCTURE MONITOR/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/FastAPI Core Engine/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/PostgreSQL \/ PostGIS/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Valkey In-Memory Cache/i).length).toBeGreaterThan(0);
    });

    it('displays 80,000-camera scalability and 99.990% bandwidth savings', () => {
      render(<SystemPage status={null} health={mockHealth} />);

      expect(screen.getAllByText(/Gujarat Statewide 80,000-Camera Scalability Benchmark/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('99.990%').length).toBeGreaterThan(0);
      expect(screen.getAllByText('320.0 Gbps').length).toBeGreaterThan(0);
    });

    it('displays ₹0 commercial licensing certification matrix', () => {
      render(<SystemPage status={null} health={mockHealth} />);

      expect(screen.getAllByText(/₹0 Commercial Licensing Certification Matrix/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/MIT License/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/BSD-3-Clause/i).length).toBeGreaterThan(0);
    });
  });
});
