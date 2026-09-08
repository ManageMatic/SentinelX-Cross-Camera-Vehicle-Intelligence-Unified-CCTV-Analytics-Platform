import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';

describe('SentinelX App Foundation', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'healthy',
        service: 'SentinelX Backend',
        version: '0.1.0',
        environment: 'test',
      }),
    }));
  });

  it('renders the SentinelX header title and banner', async () => {
    render(<App />);
    expect(screen.getByText('SentinelX')).toBeInTheDocument();
    expect(screen.getByText('GPIC 2026')).toBeInTheDocument();
    expect(screen.getByText('Unified Command Center')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Online \(v0.1.0\)/i)).toBeInTheDocument();
    });
  });

  it('renders key navigation items in sidebar', async () => {
    render(<App />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Camera Registry')).toBeInTheDocument();
    expect(screen.getByText('Vehicle Search')).toBeInTheDocument();
    expect(screen.getByText('GIS Map')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Online \(v0.1.0\)/i)).toBeInTheDocument();
    });
  });
});
