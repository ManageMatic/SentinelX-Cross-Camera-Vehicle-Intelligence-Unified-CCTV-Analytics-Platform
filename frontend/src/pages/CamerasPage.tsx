import React from 'react';
import { Camera as CameraIcon, RefreshCw } from 'lucide-react';
import { Camera } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { CameraStatusBadge } from '../components/common/Badge';

interface CamerasPageProps {
  cameras: Camera[];
}

export const CamerasPage: React.FC<CamerasPageProps> = ({ cameras }) => {
  return (
    <div className="space-y-6">
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-xs font-bold border border-blue-500/30">
              DYNAMIC DISCOVERY ENGINE
            </span>
            <span className="text-xs font-mono text-emerald-400">
              ✓ DYNAMIC /api/ingest SYNC (ZERO HARDCODING)
            </span>
          </div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide mt-1">
            CAMERA CATALOG & TELEMETRY REGISTRY
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time RTSP/TCP and WHEP stream endpoints dynamically ingested from the Sentinel Sandbox
          </p>
        </div>

        <Button variant="secondary" size="md" icon={<RefreshCw className="h-4 w-4" />}>
          Poll /api/ingest Now
        </Button>
      </div>

      <Card title={`Active CCTV Nodes (${cameras.length} Cameras Discovered)`}>
        <div className="divide-y divide-slate-800/80">
          {cameras.map((cam) => (
            <div
              key={cam.id}
              className="py-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-slate-800/30 px-3 rounded-xl transition-colors font-mono text-xs"
            >
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-lg bg-[#070b14] border border-blue-900/60 text-blue-400">
                  <CameraIcon className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-sm">{cam.name}</span>
                    <span className="px-2 py-0.5 rounded bg-black text-blue-300 border border-slate-700 text-[10px]">
                      {cam.external_camera_id}
                    </span>
                    <CameraStatusBadge status={cam.live_status} fps={cam.fps} />
                  </div>
                  <p className="text-slate-400 mt-1 font-sans">{cam.location_name}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    GPS: {cam.latitude}, {cam.longitude} • Transport: RTSP over TCP
                  </p>
                </div>
              </div>

              <div className="text-left md:text-right">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
                    {cam.resolution}
                  </span>
                  <span className="text-blue-400 bg-blue-950/80 px-2 py-0.5 rounded border border-blue-800">
                    {cam.codec}
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 mt-1">
                  WHEP: <span className="text-slate-300">{cam.whep_url || 'N/A'}</span>
                </p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
