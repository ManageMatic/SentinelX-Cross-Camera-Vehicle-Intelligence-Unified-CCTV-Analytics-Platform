import { render, screen, fireEvent, act, cleanup } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { SearchPage } from '../pages/SearchPage';
import { WatchlistsPage } from '../pages/WatchlistsPage';
import { AlertsPage } from '../pages/AlertsPage';
import { VehicleEvent, WatchlistEntry, AlertItem } from '../types';

const mockEvents: VehicleEvent[] = [
  {
    id: 'evt-01',
    camera_id: 'cam-01',
    camera_name: 'Ahmedabad Junction Entry Gate',
    event_time: new Date().toISOString(),
    plate_raw: 'GJ01AB1234',
    plate_normalized: 'GJ01AB1234',
    plate_confidence: 0.98,
    vehicle_class: 'car',
    vehicle_confidence: 0.95,
    vehicle_color: 'White',
    vehicle_make: 'Hyundai Creta',
    snapshot_path: 'https://example.com/snapshot1.jpg',
    speed_kmh: 42.5,
    latitude: 23.0225,
    longitude: 72.5714,
    has_embedding: true,
  },
  {
    id: 'evt-02',
    camera_id: 'cam-02',
    camera_name: 'Surat Ring Road Entry',
    event_time: new Date().toISOString(),
    plate_raw: 'GJ05CD5678',
    plate_normalized: 'GJ05CD5678',
    plate_confidence: 0.96,
    vehicle_class: 'truck',
    vehicle_confidence: 0.92,
    vehicle_color: 'Yellow',
    vehicle_make: 'Tata Heavy',
    snapshot_path: 'https://example.com/snapshot2.jpg',
    speed_kmh: 65.0,
    latitude: 21.1959,
    longitude: 72.8302,
    has_embedding: true,
  },
];

const mockWatchlists: WatchlistEntry[] = [
  {
    id: 'wl-01',
    watchlist_id: 'WANTED_GANGS',
    watchlist_name: 'Gold Heist Gang',
    registration_raw: 'GJ01AB1234',
    registration_normalized: 'GJ01AB1234',
    category: 'WANTED',
    priority: 'CRITICAL',
    case_number: 'FIR-2026-AHM-0412',
    reason: 'Armed robbery suspect',
    is_active: true,
    created_at: new Date().toISOString(),
  },
  {
    id: 'wl-02',
    watchlist_id: 'STOLEN_REGISTRY',
    watchlist_name: 'Stolen Surat Truck',
    registration_raw: 'GJ05CD5678',
    registration_normalized: 'GJ05CD5678',
    category: 'STOLEN',
    priority: 'HIGH',
    case_number: 'FIR-2026-SUR-1109',
    reason: 'Stolen vehicle',
    is_active: true,
    created_at: new Date().toISOString(),
  },
];

const mockAlerts: AlertItem[] = [
  {
    id: 'alert-01',
    vehicle_event_id: 'evt-01',
    watchlist_entry_id: 'wl-01',
    plate_number: 'GJ01AB1234',
    watchlist_name: 'Gold Heist Gang',
    category: 'WANTED',
    priority: 'CRITICAL',
    camera_name: 'Ahmedabad Junction Entry Gate',
    camera_id: 'cam-01',
    location: 'Ahmedabad Junction',
    timestamp: new Date().toISOString(),
    status: 'NEW',
    case_number: 'FIR-2026-AHM-0412',
  },
  {
    id: 'alert-02',
    vehicle_event_id: 'evt-02',
    watchlist_entry_id: 'wl-02',
    plate_number: 'GJ05CD5678',
    watchlist_name: 'Stolen Surat Truck',
    category: 'STOLEN',
    priority: 'HIGH',
    camera_name: 'Surat Ring Road Entry',
    camera_id: 'cam-02',
    location: 'Ring Road, Surat',
    timestamp: new Date().toISOString(),
    status: 'ACKNOWLEDGED',
    case_number: 'FIR-2026-SUR-1109',
    acknowledged_by: 'Inspector V. Jadeja',
    acknowledged_at: new Date().toISOString(),
  },
];

describe('Vehicle Intelligence, Watchlists & Alert Triage UI (Module 27)', () => {
  afterEach(() => {
    cleanup();
  });

  /* ==================== SearchPage Tests ==================== */
  describe('SearchPage Component', () => {
    it('renders ANPR search header and latency telemetry', () => {
      const handleTrackPlate = vi.fn();
      render(<SearchPage events={mockEvents} onTrackPlate={handleTrackPlate} />);

      expect(
        screen.getAllByText(/VEHICLE REGISTRATION SEARCH & INDEX/i).length
      ).toBeGreaterThan(0);
      expect(screen.getAllByText(/Indexed Engine:/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('GJ01AB1234').length).toBeGreaterThan(0);
    });

    it('filters sightings by wildcard plate pattern', () => {
      const handleTrackPlate = vi.fn();
      render(<SearchPage events={mockEvents} onTrackPlate={handleTrackPlate} />);

      const searchInput = screen.getAllByPlaceholderText(/Enter Plate/i)[0];
      fireEvent.change(searchInput, { target: { value: 'GJ05*' } });

      expect(screen.getAllByText('GJ05CD5678').length).toBeGreaterThan(0);
      expect(screen.queryByText('Hyundai Creta')).not.toBeInTheDocument();
    });

    it('opens forensic sighting detail modal on button click', () => {
      const handleTrackPlate = vi.fn();
      render(<SearchPage events={mockEvents} onTrackPlate={handleTrackPlate} />);

      const forensicBtns = screen.getAllByRole('button', { name: /Forensic Sighting/i });
      fireEvent.click(forensicBtns[0]);

      expect(screen.getAllByText(/FORENSIC SIGHTING:/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/NORMALIZED REGISTRATION/i).length).toBeGreaterThan(0);
    });
  });

  /* ==================== WatchlistsPage Tests ==================== */
  describe('WatchlistsPage Component', () => {
    it('renders watchlist repository with Valkey sync badge', () => {
      render(<WatchlistsPage watchlists={mockWatchlists} />);

      expect(screen.getAllByText(/HOTLISTS & WATCHLIST REPOSITORY/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Valkey Synced/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('GJ01AB1234').length).toBeGreaterThan(0);
    });

    it('filters watchlist entries by category tabs', () => {
      render(<WatchlistsPage watchlists={mockWatchlists} />);

      const stolenTab = screen.getAllByRole('button', { name: 'STOLEN' })[0];
      fireEvent.click(stolenTab);

      expect(screen.getAllByText('GJ05CD5678').length).toBeGreaterThan(0);
      expect(screen.queryByText('Gold Heist Gang')).not.toBeInTheDocument();
    });

    it('opens Add Hotlist Plate modal and creates a new entry', () => {
      const handleAdd = vi.fn();
      render(<WatchlistsPage watchlists={mockWatchlists} onAddEntry={handleAdd} />);

      const addBtn = screen.getAllByRole('button', { name: /Add Hotlist Plate/i })[0];
      fireEvent.click(addBtn);

      expect(screen.getAllByText(/ADD PLATE TO STATEWIDE HOTLIST/i).length).toBeGreaterThan(0);

      const plateInput = screen.getAllByPlaceholderText(/e.g. GJ01AB9999/i)[0];
      fireEvent.change(plateInput, { target: { value: 'GJ02XX1111' } });

      const commitBtn = screen.getAllByRole('button', { name: /Commit to Hotlist/i })[0];
      fireEvent.submit(commitBtn.closest('form')!);

      expect(screen.getAllByText('GJ02XX1111').length).toBeGreaterThan(0);
    });
  });

  /* ==================== AlertsPage Tests ==================== */
  describe('AlertsPage Component', () => {
    it('renders real-time alert triage inbox and severity metrics', () => {
      const handleAck = vi.fn();
      const handleTrack = vi.fn();
      render(
        <AlertsPage
          alerts={mockAlerts}
          onAcknowledgeAlert={handleAck}
          onTrackPlate={handleTrack}
        />
      );

      expect(screen.getAllByText(/SECURITY ALERTS & HOTLIST TRIAGE/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Critical Action Required/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('GJ01AB1234').length).toBeGreaterThan(0);
    });

    it('acknowledges a pending alert when clicking Acknowledge', () => {
      const handleAck = vi.fn();
      const handleTrack = vi.fn();
      render(
        <AlertsPage
          alerts={mockAlerts}
          onAcknowledgeAlert={handleAck}
          onTrackPlate={handleTrack}
        />
      );

      const ackBtn = screen.getAllByRole('button', { name: 'Acknowledge' })[0];
      fireEvent.click(ackBtn);

      expect(screen.getAllByText(/Acknowledged by Duty Officer/i).length).toBeGreaterThan(0);
    });

    it('triggers simulated emergency hotlist ingest alert', () => {
      const handleAck = vi.fn();
      const handleTrack = vi.fn();
      render(
        <AlertsPage
          alerts={mockAlerts}
          onAcknowledgeAlert={handleAck}
          onTrackPlate={handleTrack}
        />
      );

      const simBtn = screen.getAllByRole('button', { name: /Simulate Hotlist Ingest Hit/i })[0];
      fireEvent.click(simBtn);

      expect(screen.getAllByText(/LIVE INCOMING HOTLIST HIT/i).length).toBeGreaterThan(0);
    });

    it('opens PCR Interceptor Dispatch modal and confirms dispatch', () => {
      const handleAck = vi.fn();
      const handleTrack = vi.fn();
      render(
        <AlertsPage
          alerts={mockAlerts}
          onAcknowledgeAlert={handleAck}
          onTrackPlate={handleTrack}
        />
      );

      const dispatchBtns = screen.getAllByRole('button', { name: /Dispatch PCR Van/i });
      fireEvent.click(dispatchBtns[0]);

      expect(screen.getAllByText(/DISPATCH INTERCEPTOR:/i).length).toBeGreaterThan(0);

      const confirmBtn = screen.getAllByRole('button', { name: /Confirm Emergency Dispatch/i })[0];
      fireEvent.click(confirmBtn);

      expect(screen.getAllByText(/DISPATCH TRANSMITTED:/i).length).toBeGreaterThan(0);
    });
  });
});
