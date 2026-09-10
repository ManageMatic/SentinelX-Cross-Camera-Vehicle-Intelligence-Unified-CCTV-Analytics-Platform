import React, { useState } from 'react';
import {
  Activity,
  Filter,
  Grid2X2,
  Grid3X3,
  LayoutGrid,
  Maximize2,
  Radio,
  RefreshCw,
  Search,
  ShieldAlert,
} from 'lucide-react';
import { Camera } from '../types';
import { Button } from '../components/common/Button';
import { WhepVideoPlayer } from '../components/video/WhepVideoPlayer';

interface LiveGridPageProps {
  cameras: Camera[];
}

export const LiveGridPage: React.FC<LiveGridPageProps> = ({ cameras }) => {
  const [gridLayout, setGridLayout] = useState<'1x1' | '2x2' | '3x3' | '4x4'>('2x2');
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('ALL');
  const [showFilterDrawer, setShowFilterDrawer] = useState(false);
  const [simulatedAlertCameraId, setSimulatedAlertCameraId] = useState<string | null>(null);

  // Generate fallback sample cameras if list is minimal
  const allCameras: Camera[] = cameras.length >= 16 ? cameras : [
    ...cameras,
    {
      id: 'cam-sim-01',
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
      id: 'cam-sim-02',
      external_camera_id: 'CAM_AHM_002',
      name: 'SG Highway — Iscon Flyover North',
      location_name: 'SG Highway, Ahmedabad',
      latitude: 23.0298,
      longitude: 72.5074,
      live_status: 'ONLINE',
      fps: 30.0,
      resolution: '1080p',
      codec: 'H264',
    },
    {
      id: 'cam-sim-03',
      external_camera_id: 'CAM_AHM_003',
      name: 'Ring Road — Vaishnodevi Circle',
      location_name: 'Vaishnodevi Circle, Ahmedabad',
      latitude: 23.1362,
      longitude: 72.5448,
      live_status: 'ONLINE',
      fps: 25.0,
      resolution: '1080p',
      codec: 'H264',
    },
    {
      id: 'cam-sim-04',
      external_camera_id: 'CAM_SUR_001',
      name: 'Surat Textile Market Gate 1',
      location_name: 'Ring Road, Surat',
      latitude: 21.1959,
      longitude: 72.8302,
      live_status: 'ONLINE',
      fps: 25.0,
      resolution: '1080p',
      codec: 'H264',
    },
    {
      id: 'cam-sim-05',
      external_camera_id: 'CAM_SUR_002',
      name: 'Dumas Road — Airport Junction',
      location_name: 'Dumas Road, Surat',
      latitude: 21.1274,
      longitude: 72.7487,
      live_status: 'ONLINE',
      fps: 30.0,
      resolution: '1080p',
      codec: 'H264',
    },
    {
      id: 'cam-sim-06',
      external_camera_id: 'CAM_VAD_001',
      name: 'Alkapuri Main Underpass',
      location_name: 'Alkapuri, Vadodara',
      latitude: 22.3107,
      longitude: 73.1812,
      live_status: 'ONLINE',
      fps: 25.0,
      resolution: '1080p',
      codec: 'H264',
    },
    {
      id: 'cam-sim-07',
      external_camera_id: 'CAM_RAJ_001',
      name: '150 Feet Ring Road Checkpoint',
      location_name: 'Kalawad Road, Rajkot',
      latitude: 22.2858,
      longitude: 70.7684,
      live_status: 'ONLINE',
      fps: 25.0,
      resolution: '1080p',
      codec: 'H264',
    },
    {
      id: 'cam-sim-08',
      external_camera_id: 'CAM_GAN_001',
      name: 'CH Road — Sector 11 Junction',
      location_name: 'Sector 11, Gandhinagar',
      latitude: 23.2156,
      longitude: 72.6369,
      live_status: 'ONLINE',
      fps: 25.0,
      resolution: '1080p',
      codec: 'H264',
    },
  ];

  // Filtering
  const filteredCameras = allCameras.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.external_camera_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.location_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDistrict =
      selectedDistrict === 'ALL' || c.location_name.toLowerCase().includes(selectedDistrict.toLowerCase());
    return matchesSearch && matchesDistrict;
  });

  const displayedCameras =
    gridLayout === '1x1'
      ? filteredCameras.filter((c) => c.id === (selectedCameraId || filteredCameras[0]?.id)).slice(0, 1)
      : gridLayout === '2x2'
      ? filteredCameras.slice(0, 4)
      : gridLayout === '3x3'
      ? filteredCameras.slice(0, 9)
      : filteredCameras.slice(0, 16);

  const gridClass =
    gridLayout === '1x1'
      ? 'grid-cols-1'
      : gridLayout === '2x2'
      ? 'grid-cols-1 sm:grid-cols-2'
      : gridLayout === '3x3'
      ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
      : 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4';

  return (
    <div className="space-y-6">
      {/* Top Tactical Command Toolbar */}
      <div className="bg-[#0c1424] p-4 rounded-xl border border-slate-800 shadow-2xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="h-5 w-5 text-emerald-400 animate-pulse" />
            <h1 className="text-xl font-black text-white font-mono tracking-wide">
              LIVE CCTV SURVEILLANCE WALL
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-0.5 font-mono">
            Gujarat Police Command & Control — Real-Time WHEP WebRTC Low-Latency Matrix
          </p>
        </div>

        {/* Action Controls & Layout Selector */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Quick Search */}
          <div className="relative">
            <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Filter cameras..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-[#070b14] border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 font-mono focus:border-blue-500 focus:outline-none w-44"
            />
          </div>

          {/* Grid Layout Switcher */}
          <div className="flex items-center bg-[#070b14] p-1 rounded-lg border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setGridLayout('1x1')}
              className={`px-2.5 py-1 rounded flex items-center gap-1 transition-colors ${
                gridLayout === '1x1' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
              title="1x1 Full Focus View"
            >
              <Maximize2 className="h-3 w-3" />
              1x1
            </button>
            <button
              onClick={() => setGridLayout('2x2')}
              className={`px-2.5 py-1 rounded flex items-center gap-1 transition-colors ${
                gridLayout === '2x2' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
              title="2x2 Quad Multi-Grid"
            >
              <Grid2X2 className="h-3 w-3" />
              2x2
            </button>
            <button
              onClick={() => setGridLayout('3x3')}
              className={`px-2.5 py-1 rounded flex items-center gap-1 transition-colors ${
                gridLayout === '3x3' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
              title="3x3 9-Feed Matrix"
            >
              <Grid3X3 className="h-3 w-3" />
              3x3
            </button>
            <button
              onClick={() => setGridLayout('4x4')}
              className={`px-2.5 py-1 rounded flex items-center gap-1 transition-colors ${
                gridLayout === '4x4' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
              title="4x4 Statewide Surveillance Wall (16 Feeds)"
            >
              <LayoutGrid className="h-3 w-3" />
              4x4
            </button>
          </div>

          {/* District Filter Toggle */}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setShowFilterDrawer(!showFilterDrawer)}
            icon={<Filter className="h-3.5 w-3.5" />}
          >
            Districts ({selectedDistrict})
          </Button>

          {/* Test Alert Simulator */}
          <Button
            variant="danger"
            size="sm"
            onClick={() => {
              const target = displayedCameras[0]?.id || null;
              setSimulatedAlertCameraId(simulatedAlertCameraId ? null : target);
            }}
            icon={<ShieldAlert className="h-3.5 w-3.5" />}
          >
            {simulatedAlertCameraId ? 'Clear Alert' : 'Simulate Hotlist Hit'}
          </Button>
        </div>
      </div>

      {/* District Filter Selector Drawer */}
      {showFilterDrawer && (
        <div className="bg-[#090f1d] p-3 rounded-xl border border-slate-800 flex flex-wrap items-center gap-2 text-xs font-mono animate-in slide-in-from-top duration-200">
          <span className="text-slate-400 font-bold mr-2">STATE DISTRICT:</span>
          {['ALL', 'Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar'].map((district) => (
            <button
              key={district}
              onClick={() => setSelectedDistrict(district)}
              className={`px-3 py-1 rounded border transition-colors ${
                selectedDistrict === district
                  ? 'bg-blue-600 text-white border-blue-400 font-bold'
                  : 'bg-black/60 text-slate-400 border-slate-800 hover:text-white'
              }`}
            >
              {district}
            </button>
          ))}
        </div>
      )}

      {/* Active Surveillance Status Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[#090e1a] p-3 rounded-lg border border-slate-800 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400">ACTIVE TILES</span>
          <span className="text-sm font-bold font-mono text-emerald-400">{displayedCameras.length} Feeds</span>
        </div>
        <div className="bg-[#090e1a] p-3 rounded-lg border border-slate-800 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400">STREAM PROTOCOL</span>
          <span className="text-sm font-bold font-mono text-blue-400">WHEP WebRTC</span>
        </div>
        <div className="bg-[#090e1a] p-3 rounded-lg border border-slate-800 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400">MEAN LATENCY</span>
          <span className="text-sm font-bold font-mono text-emerald-400">&lt; 150 ms</span>
        </div>
        <div className="bg-[#090e1a] p-3 rounded-lg border border-slate-800 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400">STATE STATUS</span>
          <span className="text-sm font-bold font-mono text-cyan-400 flex items-center gap-1">
            <Activity className="h-3.5 w-3.5" />
            OPTIMAL
          </span>
        </div>
      </div>

      {/* Dynamic Video Grid */}
      <div className={`grid ${gridClass} gap-4`}>
        {displayedCameras.map((cam) => (
          <WhepVideoPlayer
            key={cam.id}
            camera={cam}
            isFocused={gridLayout === '1x1'}
            hasActiveAlert={simulatedAlertCameraId === cam.id}
            alertDetails="HOTLIST MATCH: GJ01AB1234 (STOLEN VEHICLE)"
            onToggleFocus={() => {
              if (gridLayout === '1x1') {
                setGridLayout('2x2');
                setSelectedCameraId(null);
              } else {
                setSelectedCameraId(cam.id);
                setGridLayout('1x1');
              }
            }}
          />
        ))}
      </div>

      {displayedCameras.length === 0 && (
        <div className="bg-[#090e1a] p-12 rounded-xl border border-slate-800 text-center text-slate-400 font-mono">
          <p className="text-sm">No camera streams matching current search filter.</p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setSearchQuery('');
              setSelectedDistrict('ALL');
            }}
            className="mt-3"
            icon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Reset Filters
          </Button>
        </div>
      )}
    </div>
  );
};
