import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';

describe('SentinelX Tactical Command Center Shell (Module 4)', () => {
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
            service: 'SentinelX Core Backend',
            version: '1.0.0',
            environment: 'test',
          },
        }),
      })
    );
  });

  it('renders top navigation with SentinelX insignia and GPIC badge', () => {
    render(<App />);
    expect(screen.getAllByText(/SENTINEL/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/GPIC-2026/i)).toBeInTheDocument();
    expect(screen.getByText(/GUJARAT POLICE SURVEILLANCE COMMAND/i)).toBeInTheDocument();
  });

  it('renders sidebar navigation groups and tabs', () => {
    render(<App />);
    expect(screen.getByText('LIVE SURVEILLANCE')).toBeInTheDocument();
    expect(screen.getByText('VEHICLE INTELLIGENCE')).toBeInTheDocument();
    expect(screen.getByText('SECURITY & ALERTS')).toBeInTheDocument();
    expect(screen.getByText('FORENSICS & SYSTEM')).toBeInTheDocument();
    expect(screen.getByText('Live CCTV Grid')).toBeInTheDocument();
    expect(screen.getByText('Plate Search')).toBeInTheDocument();
    expect(screen.getByText('Hotlists / Watchlists')).toBeInTheDocument();
  });

  it('renders KPI metrics on Dashboard', () => {
    render(<App />);
    expect(screen.getByText(/COMMAND & INTELLIGENCE MATRIX/i)).toBeInTheDocument();
    expect(screen.getByText(/Active CCTV Feeds/i)).toBeInTheDocument();
    expect(screen.getByText(/Detections Today/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Watchlist Hits/i).length).toBeGreaterThan(0);
  });

  it('navigates seamlessly across tabs when clicking sidebar items', () => {
    render(<App />);
    
    // Click Live CCTV Grid tab
    fireEvent.click(screen.getByText('Live CCTV Grid'));
    expect(screen.getByText(/LIVE CCTV SURVEILLANCE WALL/i)).toBeInTheDocument();

    // Click Plate Search tab
    fireEvent.click(screen.getByText('Plate Search'));
    expect(screen.getByText(/VEHICLE REGISTRATION SEARCH & INDEX/i)).toBeInTheDocument();

    // Click Hotlists / Watchlists tab
    fireEvent.click(screen.getByText('Hotlists / Watchlists'));
    expect(screen.getByText(/HOTLISTS & WATCHLIST REPOSITORY/i)).toBeInTheDocument();

    // Click Evidence Vault tab
    fireEvent.click(screen.getByText('Evidence Vault (SHA-256)'));
    expect(screen.getByText(/CRYPTOGRAPHIC EVIDENCE VAULT/i)).toBeInTheDocument();
  });
});
