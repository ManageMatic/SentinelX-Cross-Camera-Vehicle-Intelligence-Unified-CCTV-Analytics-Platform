import React, { useState } from 'react';
import { Maximize2, RefreshCw, Video } from 'lucide-react';
import { Camera } from '../types';
import { Button } from '../components/common/Button';
import { CameraStatusBadge } from '../components/common/Badge';

interface LiveGridPageProps {
  cameras: Camera[];
}

export const LiveGridPage: React.FC<LiveGridPageProps> = ({ cameras }) => {
  const [gridLayout, setGridLayout] = useState<'2x2' | '3x3' | '1x1'>('2x2');
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);

  const displayedCameras =
    gridLayout === '1x1'
      ? cameras.filter((c) => c.id === (selectedCameraId || cameras[0]?.id))
      : gridLayout === '2x2'
      ? cameras.slice(0, 4)
      : cameras.slice(0, 9);

  const gridClass =
    gridLayout === '1x1'
      ? 'grid-cols-1'
      : gridLayout === '2x2'
      ? 'grid-cols-1 sm:grid-cols-2'
      : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';

  return (
    <div className="space-y-6">
      {/* Top Toolbar */}
      <div className="bg-[#0c1424] p-4 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide">
            LIVE CCTV SURVEILLANCE WALL
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time low-latency WHEP / HLS stream matrix with TCP video ingestion
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Layout Switcher */}
          <div className="flex items-center bg-[#070b14] p-1 rounded-lg border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setGridLayout('1x1')}
              className={`px-3 py-1 rounded transition-colors ${
                gridLayout === '1x1' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              1x1 FOCUS
            </button>
            <button
              onClick={() => setGridLayout('2x2')}
              className={`px-3 py-1 rounded transition-colors ${
                gridLayout === '2x2' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              2x2 QUAD
            </button>
            <button
              onClick={() => setGridLayout('3x3')}
              className={`px-3 py-1 rounded transition-colors ${
                gridLayout === '3x3' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              3x3 MATRIX
            </button>
          </div>

          <Button variant="secondary" size="sm" icon={<RefreshCw className="h-3.5 w-3.5" />}>
            Refresh Streams
          </Button>
        </div>
      </div>

      {/* Video Grid */}
      <div className={`grid ${gridClass} gap-4`}>
        {displayedCameras.map((cam) => (
          <div
            key={cam.id}
            className="group relative bg-[#090e1a] rounded-xl border border-slate-800 hover:border-blue-500 transition-all overflow-hidden shadow-xl"
          >
            {/* Video Viewport */}
            <div className="aspect-video bg-slate-950 relative flex items-center justify-center cctv-scanline">
              <div className="text-center p-4">
                <Video className="h-10 w-10 text-slate-700 mx-auto group-hover:text-blue-400 transition-colors animate-pulse" />
                <p className="text-xs font-mono font-bold text-slate-300 mt-2">{cam.name}</p>
                <p className="text-[10px] font-mono text-slate-400">{cam.location_name}</p>
                <span className="inline-block mt-2 px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800 text-[9px] font-mono">
                  WHEP WebRTC Engine Active
                </span>
              </div>

              {/* Overlays */}
              <div className="absolute top-3 left-3 flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-black/80 backdrop-blur-sm text-xs font-mono font-bold text-white border border-slate-700">
                  {cam.external_camera_id}
                </span>
                <CameraStatusBadge status={cam.live_status} fps={cam.fps} />
              </div>

              <div className="absolute bottom-3 left-3 flex items-center gap-2">
                <span className="text-[10px] font-mono text-emerald-400 bg-black/80 px-2 py-0.5 rounded border border-emerald-800/60">
                  {cam.resolution}
                </span>
                <span className="text-[10px] font-mono text-blue-400 bg-black/80 px-2 py-0.5 rounded border border-blue-800/60">
                  {cam.codec} / TCP
                </span>
              </div>

              <div className="absolute bottom-3 right-3 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => {
                    setSelectedCameraId(cam.id);
                    setGridLayout('1x1');
                  }}
                  className="p-1.5 rounded bg-black/80 text-white hover:bg-blue-600 transition-colors"
                  title="Focus View"
                >
                  <Maximize2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
