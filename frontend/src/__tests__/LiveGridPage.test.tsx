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
    expect(screen.getAllByText(/LIVE CCTV SURVEILLANCE WALL/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('1x1').length).toBeGreaterThan(0);
    expect(screen.getAllByText('2x2').length).toBeGreaterThan(0);
    expect(screen.getAllByText('3x3').length).toBeGreaterThan(0);
    expect(screen.getAllByText('4x4').length).toBeGreaterThan(0);
  });

  it('switches multi-grid layouts when clicking 1x1, 2x2, 3x3, 4x4 buttons', () => {
    render(<LiveGridPage cameras={mockCameras} />);

    // Click 1x1 layout
    const btn1x1 = screen.getAllByText('1x1')[0];
    fireEvent.click(btn1x1);
    expect(btn1x1).toHaveClass('bg-blue-600');

    // Click 3x3 layout
    const btn3x3 = screen.getAllByText('3x3')[0];
    fireEvent.click(btn3x3);
    expect(btn3x3).toHaveClass('bg-blue-600');

    // Click 4x4 layout
    const btn4x4 = screen.getAllByText('4x4')[0];
    fireEvent.click(btn4x4);
    expect(btn4x4).toHaveClass('bg-blue-600');
  });

  it('filters cameras by search input query', () => {
    render(<LiveGridPage cameras={mockCameras} />);
    const searchInput = screen.getAllByPlaceholderText(/Filter cameras/i)[0];
    fireEvent.change(searchInput, { target: { value: 'Surat' } });

    expect(screen.getAllByText('Surat Ring Road Entry').length).toBeGreaterThan(0);
  });

  it('toggles district filter drawer', () => {
    render(<LiveGridPage cameras={mockCameras} />);
    const districtBtns = screen.getAllByRole('button', { name: /Districts/i });
    fireEvent.click(districtBtns[0]);

    expect(screen.getAllByText(/STATE DISTRICT:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText('Vadodara').length).toBeGreaterThan(0);
  });

  it('simulates critical hotlist hit alert overlay', () => {
    render(<LiveGridPage cameras={mockCameras} />);
    const alertBtns = screen.getAllByRole('button', { name: /Simulate Hotlist Hit/i });
    fireEvent.click(alertBtns[0]);

    expect(screen.getAllByText(/CRITICAL HOTLIST HIT DETECTED/i).length).toBeGreaterThan(0);
  });
});
