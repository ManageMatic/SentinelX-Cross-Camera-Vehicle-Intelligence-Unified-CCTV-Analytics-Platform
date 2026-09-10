import React, { useState } from 'react';
import { Camera as CameraIcon, RefreshCw, Copy, Check, Search, ExternalLink } from 'lucide-react';
import { Camera } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { CameraStatusBadge } from '../components/common/Badge';

interface CamerasPageProps {
  cameras: Camera[];
}

export const CamerasPage: React.FC<CamerasPageProps> = ({ cameras }) => {
  const [search, setSearch] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredCameras = cameras.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.external_camera_id.toLowerCase().includes(search.toLowerCase()) ||
      c.location_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-xs font-bold border border-blue-500/30">
              OFFICIAL SENTINEL GRID
            </span>
            <span className="text-xs font-mono text-emerald-400">
              ✓ 30 GUJARAT STATE POLICE CCTV CHANNELS
            </span>
          </div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide mt-1">
            CAMERA CATALOG & TELEMETRY REGISTRY
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time HLS (CDN: cctv.corp8.cloud), RTSP/TCP, and WHEP endpoints for live AI inference and tactical monitoring
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="h-3.5 w-3.5 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search 30 cameras..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-[#070b14] border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 font-mono focus:border-blue-500 focus:outline-none w-48"
            />
          </div>
          <a
            href="https://cctv.corp8.cloud/"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-mono text-xs font-bold transition-colors"
          >
            Live Grid <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>

      <Card title={`Registered CCTV Nodes (${filteredCameras.length} of ${cameras.length} Active Feeds)`}>
        <div className="divide-y divide-slate-800/80">
          {filteredCameras.map((cam) => {
            const camId = cam.external_camera_id.toLowerCase().replace(/[^a-z0-9]/g, '');
            const hlsUrl = cam.hls_url || `https://cctv.corp8.cloud/${camId}/index.m3u8`;
            const rtspUrl = cam.rtsp_url || `rtsp://103.250.160.189:8554/stream/${camId}`;

            return (
              <div
                key={cam.id}
                className="py-4 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 hover:bg-slate-800/30 px-3 rounded-xl transition-colors font-mono text-xs"
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
                      GPS: {cam.latitude.toFixed(4)}, {cam.longitude.toFixed(4)} • Transport: RTSP over TCP / HLS CDN
                    </p>
                  </div>
                </div>

                <div className="text-left lg:text-right space-y-1.5 w-full lg:w-auto">
                  <div className="flex items-center lg:justify-end gap-2">
                    <span className="text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800 text-[10px]">
                      {cam.resolution}
                    </span>
                    <span className="text-blue-400 bg-blue-950/80 px-2 py-0.5 rounded border border-blue-800 text-[10px]">
                      {cam.codec}
                    </span>
                  </div>

                  {/* Endpoints and Copy Actions */}
                  <div className="flex flex-wrap items-center lg:justify-end gap-2 text-[10px]">
                    <button
                      onClick={() => handleCopy(hlsUrl, `hls-${cam.id}`)}
                      className="px-2 py-1 rounded bg-[#070b14] border border-slate-700 hover:border-blue-500 text-slate-300 flex items-center gap-1 transition-colors"
                      title="Copy HLS Stream URL"
                    >
                      {copiedId === `hls-${cam.id}` ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      HLS: {camId}/index.m3u8
                    </button>

                    <button
                      onClick={() => handleCopy(rtspUrl, `rtsp-${cam.id}`)}
                      className="px-2 py-1 rounded bg-[#070b14] border border-slate-700 hover:border-blue-500 text-slate-300 flex items-center gap-1 transition-colors"
                      title="Copy RTSP Stream URL"
                    >
                      {copiedId === `rtsp-${cam.id}` ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                      RTSP (TCP)
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};
