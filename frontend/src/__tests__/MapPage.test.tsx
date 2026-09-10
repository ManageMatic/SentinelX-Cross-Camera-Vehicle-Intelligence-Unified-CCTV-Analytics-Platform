import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MapPage } from '../pages/MapPage';
import { Camera } from '../types';

const mockCameras: Camera[] = [
  {
    id: 'cam-01',
    external_camera_id: 'CAM_AHM_001',
    name: 'Ahmedabad Junction Entry Gate',
    location_name: 'Ahmedabad Junction, Ahmedabad',
    latitude: 23.0225,
    longitude: 72.5714,
    live_status: 'ONLINE',
    fps: 25.0,
    resolution: '1080p',
    codec: 'H264',
  },
  {
    id: 'cam-02',
    external_camera_id: 'CAM_SUR_001',
    name: 'Surat Ring Road Entry',
    location_name: 'Ring Road, Surat',
    latitude: 21.1959,
    longitude: 72.8302,
    live_status: 'ONLINE',
    fps: 30.0,
    resolution: '1080p',
    codec: 'H264',
  },
  {
    id: 'cam-03',
    external_camera_id: 'CAM_VAD_001',
    name: 'Vadodara Alkapuri Underpass',
    location_name: 'Alkapuri, Vadodara',
    latitude: 22.3107,
    longitude: 73.1812,
    live_status: 'ONLINE',
    fps: 25.0,
    resolution: '1080p',
    codec: 'H264',
  },
];

describe('GIS OpenStreetMap & Chronological Route Visualization (Module 26)', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  it('renders GIS Tactical Radar header and district hub selector', () => {
    render(<MapPage cameras={mockCameras} />);

    expect(screen.getByText(/GIS OPENSTREETMAP TACTICAL RADAR/i)).toBeInTheDocument();
    expect(screen.getByText(/STATEWIDE OVERVIEW/i)).toBeInTheDocument();
    expect(screen.getAllByText('AHMEDABAD').length).toBeGreaterThan(0);
    expect(screen.getAllByText('SURAT').length).toBeGreaterThan(0);
    expect(screen.getAllByText('VADODARA').length).toBeGreaterThan(0);
  });

  it('toggles map layer filter buttons', () => {
    render(<MapPage cameras={mockCameras} />);

    const camLayerBtn = screen.getAllByRole('button', { name: /Cameras/i })[0];
    const polyLayerBtn = screen.getAllByRole('button', { name: /Polylines/i })[0];
    const speedLayerBtn = screen.getAllByRole('button', { name: /Speed/i })[0];
    const loiterLayerBtn = screen.getAllByRole('button', { name: /Loitering/i })[0];

    expect(camLayerBtn).toBeInTheDocument();
    expect(polyLayerBtn).toBeInTheDocument();
    expect(speedLayerBtn).toBeInTheDocument();
    expect(loiterLayerBtn).toBeInTheDocument();

    // Toggle layer off and back on
    fireEvent.click(camLayerBtn);
    expect(camLayerBtn).not.toHaveClass('bg-blue-600');
    fireEvent.click(camLayerBtn);
    expect(camLayerBtn).toHaveClass('bg-blue-600');
  });

  it('changes active trajectory when selecting journey preset', () => {
    render(<MapPage cameras={mockCameras} />);

    const presetSelect = screen.getAllByRole('combobox')[0];
    fireEvent.change(presetSelect, { target: { value: 'GJ05CD5678' } });

    expect(screen.getAllByText('GJ05CD5678').length).toBeGreaterThan(0);
  });

  it('controls playback replay animation with play, pause and reset', () => {
    render(<MapPage cameras={mockCameras} />);

    const playBtn = screen.getAllByRole('button', { name: /PLAY REPLAY/i })[0];
    fireEvent.click(playBtn);

    expect(screen.getAllByRole('button', { name: /PAUSE/i })[0]).toBeInTheDocument();

    // Fast-forward fake timer
    act(() => {
      vi.advanceTimersByTime(2500);
    });

    const resetBtn = screen.getAllByRole('button', { name: /Reset/i })[0];
    fireEvent.click(resetBtn);

    expect(screen.getAllByRole('button', { name: /PLAY REPLAY/i })[0]).toBeInTheDocument();
  });

  it('switches between Sightings and GIS Nodes directory tabs', () => {
    render(<MapPage cameras={mockCameras} />);

    const nodesTab = screen.getAllByRole('button', { name: /GIS Nodes/i })[0];
    fireEvent.click(nodesTab);

    expect(screen.getByPlaceholderText(/Search node or junction/i)).toBeInTheDocument();
    expect(screen.getAllByText('Surat Ring Road Entry').length).toBeGreaterThan(0);

    // Filter cameras in search
    const searchInput = screen.getByPlaceholderText(/Search node or junction/i);
    fireEvent.change(searchInput, { target: { value: 'Vadodara' } });

    expect(screen.getAllByText('Vadodara Alkapuri Underpass').length).toBeGreaterThan(0);
  });

  it('jumps map district focus when clicking district preset buttons', () => {
    render(<MapPage cameras={mockCameras} />);

    const suratBtn = screen.getAllByRole('button', { name: 'SURAT' })[0];
    fireEvent.click(suratBtn);

    expect(suratBtn).toHaveClass('bg-blue-600');
  });
});
