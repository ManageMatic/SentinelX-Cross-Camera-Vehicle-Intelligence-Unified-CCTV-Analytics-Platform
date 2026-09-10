import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';

describe('NETRA-X Tactical Command Center Shell (Module 4)', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          message: 'OK',
          data: {
            status: 'healthy',
            service: 'NETRA-X Core Backend',
            version: '1.0.0',
            environment: 'test',
          },
        }),
      })
    );
  });

  it('renders top navigation with NETRA-X insignia and GPIC badge', () => {
    render(<App />);
    expect(screen.getAllByText(/NETRA/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/GPIC-2026/i)).toBeInTheDocument();
    expect(screen.getByText(/GUJARAT POLICE SURVEILLANCE COMMAND/i)).toBeInTheDocument();
  });

  it('renders sidebar navigation groups and tabs', () => {
    render(<App />);
    expect(screen.getAllByText('LIVE SURVEILLANCE').length).toBeGreaterThan(0);
    expect(screen.getAllByText('VEHICLE INTELLIGENCE').length).toBeGreaterThan(0);
    expect(screen.getAllByText('SECURITY & ALERTS').length).toBeGreaterThan(0);
    expect(screen.getAllByText('FORENSICS & SYSTEM').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Live CCTV Grid').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Plate Search').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Hotlists / Watchlists').length).toBeGreaterThan(0);
  });

  it('renders KPI metrics on Dashboard', () => {
    render(<App />);
    expect(screen.getAllByText(/COMMAND & INTELLIGENCE MATRIX/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Active CCTV Feeds/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Detections Today/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Watchlist Hits/i).length).toBeGreaterThan(0);
  });

  it('navigates seamlessly across tabs when clicking sidebar items', () => {
    render(<App />);
    
    // Click Live CCTV Grid tab
    fireEvent.click(screen.getAllByText('Live CCTV Grid')[0]);
    expect(screen.getAllByText(/LIVE CCTV SURVEILLANCE WALL/i).length).toBeGreaterThan(0);

    // Click Plate Search tab
    fireEvent.click(screen.getAllByText('Plate Search')[0]);
    expect(screen.getAllByText(/VEHICLE REGISTRATION SEARCH & INDEX/i).length).toBeGreaterThan(0);

    // Click Hotlists / Watchlists tab
    fireEvent.click(screen.getAllByText('Hotlists / Watchlists')[0]);
    expect(screen.getAllByText(/HOTLISTS & WATCHLIST REPOSITORY/i).length).toBeGreaterThan(0);

    // Click Evidence Vault tab
    fireEvent.click(screen.getAllByText('Evidence Vault (SHA-256)')[0]);
    expect(screen.getAllByText(/CRYPTOGRAPHIC EVIDENCE VAULT/i).length).toBeGreaterThan(0);
  });
});
