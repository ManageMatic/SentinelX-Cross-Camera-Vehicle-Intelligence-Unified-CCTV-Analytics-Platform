import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { LiveGridPage } from '../pages/LiveGridPage';
import { Camera } from '../types';

const mockCameras: Camera[] = [
  {
    id: 'cam-01',
    external_camera_id: 'CAM_AHM_001',
    name: 'Ahmedabad Junction Entry Gate',
    location_name: 'Ahmedabad Junction',
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
];

describe('Live CCTV Grid & WHEP Video Wall (Module 25)', () => {
  it('renders CCTV surveillance wall header and layout controls', () => {
    render(<LiveGridPage cameras={mockCameras} />);
    expect(screen.getByText(/LIVE CCTV SURVEILLANCE WALL/i)).toBeInTheDocument();
    expect(screen.getByText('1x1')).toBeInTheDocument();
    expect(screen.getByText('2x2')).toBeInTheDocument();
    expect(screen.getByText('3x3')).toBeInTheDocument();
    expect(screen.getByText('4x4')).toBeInTheDocument();
  });

  it('switches multi-grid layouts when clicking 1x1, 2x2, 3x3, 4x4 buttons', () => {
    render(<LiveGridPage cameras={mockCameras} />);

    // Click 1x1 layout
    fireEvent.click(screen.getByText('1x1'));
    expect(screen.getByText('1x1')).toHaveClass('bg-blue-600');

    // Click 3x3 layout
    fireEvent.click(screen.getByText('3x3'));
    expect(screen.getByText('3x3')).toHaveClass('bg-blue-600');

    // Click 4x4 layout
    fireEvent.click(screen.getByText('4x4'));
    expect(screen.getByText('4x4')).toHaveClass('bg-blue-600');
  });

  it('filters cameras by search input query', () => {
    render(<LiveGridPage cameras={mockCameras} />);
    const searchInput = screen.getByPlaceholderText(/Filter cameras/i);
    fireEvent.change(searchInput, { target: { value: 'Surat' } });

    expect(screen.getByText('Surat Ring Road Entry')).toBeInTheDocument();
  });

  it('toggles district filter drawer', () => {
    render(<LiveGridPage cameras={mockCameras} />);
    const districtBtn = screen.getByRole('button', { name: /Districts/i });
    fireEvent.click(districtBtn);

    expect(screen.getByText(/STATE DISTRICT:/i)).toBeInTheDocument();
    expect(screen.getByText('Vadodara')).toBeInTheDocument();
  });

  it('simulates critical hotlist hit alert overlay', () => {
    render(<LiveGridPage cameras={mockCameras} />);
    const alertBtns = screen.getAllByRole('button', { name: /Simulate Hotlist Hit/i });
    fireEvent.click(alertBtns[0]);

    expect(screen.getAllByText(/CRITICAL HOTLIST HIT DETECTED/i).length).toBeGreaterThan(0);
  });
});
