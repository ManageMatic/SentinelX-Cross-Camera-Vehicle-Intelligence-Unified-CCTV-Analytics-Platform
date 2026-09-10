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
  Key,
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

  const [showIntegratorGuide, setShowIntegratorGuide] = useState(false);
  const [authEmail, setAuthEmail] = useState(
    localStorage.getItem('sentinel_email') || ''
  );
  const [authPassword, setAuthPassword] = useState(
    localStorage.getItem('sentinel_password') || ''
  );
  const [activeCodeTab, setActiveCodeTab] = useState<'python' | 'gstreamer' | 'ffmpeg'>('python');

  const handleSaveCredentials = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('sentinel_email', authEmail);
    localStorage.setItem('sentinel_password', authPassword);
    setShowIntegratorGuide(false);
  };

  const allCameras = cameras;

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

          {/* Integrator Guide & Stream Credentials */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowIntegratorGuide(true)}
            icon={<Key className="h-3.5 w-3.5 text-blue-400" />}
          >
            Stream Credentials & Guide
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
          {['ALL', 'Ahmedabad', 'Gandhinagar', 'Junagadh', 'Surat', 'Vadodara', 'Rajkot', 'Somnath', 'Dwarka'].map((district) => (
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
          <span className="text-sm font-bold font-mono text-blue-400">HLS (CDN) / WHEP</span>
        </div>
        <div className="bg-[#090e1a] p-3 rounded-lg border border-slate-800 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400">TOTAL REGISTERED</span>
          <span className="text-sm font-bold font-mono text-emerald-400">{allCameras.length} Cameras</span>
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

      {/* Integrator's Guide & Stream Access Credentials Modal */}
      {showIntegratorGuide && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0c1424] border border-blue-600/40 rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-[0_0_50px_rgba(37,99,235,0.2)] max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-[10px] font-mono font-bold text-blue-400 px-2 py-0.5 rounded bg-blue-950 border border-blue-800">
                  SENTINEL // INTEGRATOR'S GUIDE
                </span>
                <h2 className="text-lg font-black text-white font-mono mt-1">
                  Sentinel Camera Grid Credentials & Direct Ingestion
                </h2>
              </div>
              <button
                onClick={() => setShowIntegratorGuide(false)}
                className="text-slate-400 hover:text-white font-mono text-sm px-2 py-1 rounded bg-slate-800"
              >
                ✕
              </button>
            </div>

            {/* Access Model Description */}
            <div className="bg-[#080d19] p-4 rounded-xl border border-slate-800 space-y-2 text-xs font-mono text-slate-300">
              <p>
                <strong className="text-emerald-400">Access Model:</strong> HLS is served over CDN (
                <code className="text-blue-300">https://cctv.corp8.cloud/</code>) behind your access password. RTSP & WebRTC/WHEP are served directly on public IP <code className="text-yellow-300">103.250.160.189</code>.
              </p>
              <p>
                <strong className="text-emerald-400">Credentials Encoding:</strong> The <code className="text-cyan-300">@</code> in your email must be percent-encoded as <code className="text-cyan-300">%40</code> (e.g. <code className="text-slate-200">user%40example.com</code>).
              </p>
            </div>

            {/* Credential Save Form */}
            <form onSubmit={handleSaveCredentials} className="space-y-3 bg-[#080d19] p-4 rounded-xl border border-blue-900/40">
              <h3 className="text-xs font-bold text-white font-mono">Set Authorized Credentials for RTSP/WHEP</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
                <div>
                  <label className="text-slate-400 text-[10px] block mb-1">Registered Email</label>
                  <input
                    type="text"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full bg-[#0c1424] border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="text-slate-400 text-[10px] block mb-1">Access Password</label>
                  <input
                    type="password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="Access Password"
                    className="w-full bg-[#0c1424] border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-400"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowIntegratorGuide(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm">
                  Save Credentials
                </Button>
              </div>
            </form>

            {/* Code Snippets for AI Inference */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white font-mono">Inference Connection Snippets</h3>
                <div className="flex gap-1 font-mono text-[10px]">
                  {(['python', 'gstreamer', 'ffmpeg'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveCodeTab(tab)}
                      className={`px-2 py-0.5 rounded capitalize ${
                        activeCodeTab === tab ? 'bg-blue-600 text-white font-bold' : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-[#050811] p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-200 overflow-x-auto">
                {activeCodeTab === 'python' && (
                  <pre className="text-cyan-300">
{`import os, cv2

# RTSP over TCP (force TCP transport):
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
url = "rtsp://${authEmail ? authEmail.replace('@', '%40') : 'you%40example.com'}:${authPassword || 'YOUR_PASSWORD'}@103.250.160.189:8554/stream/cam01"
cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

while True:
    ok, frame = cap.read()
    if not ok:
        break
    pts_ms = cap.get(cv2.CAP_PROP_POS_MSEC)`}
                  </pre>
                )}

                {activeCodeTab === 'gstreamer' && (
                  <pre className="text-emerald-300">
{`gst-launch-1.0 rtspsrc location=rtsp://${authEmail ? authEmail.replace('@', '%40') : 'you%40example.com'}:${authPassword || 'YOUR_PASSWORD'}@103.250.160.189:8554/stream/cam01 protocols=tcp latency=200 \\
  ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! fakesink`}
                  </pre>
                )}

                {activeCodeTab === 'ffmpeg' && (
                  <pre className="text-yellow-300">
{`# FFplay RTSP over TCP:
ffplay -rtsp_transport tcp "rtsp://${authEmail ? authEmail.replace('@', '%40') : 'you%40example.com'}:${authPassword || 'YOUR_PASSWORD'}@103.250.160.189:8554/stream/cam01"

# FFplay HLS:
ffplay https://cctv.corp8.cloud/cam01/index.m3u8`}
                  </pre>
                )}
              </div>
            </div>

            {/* Direct Portal Link */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs font-mono">
              <a
                href="https://cctv.corp8.cloud/"
                target="_blank"
                rel="noreferrer"
                className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
              >
                Open Official Gujarat CCTV Grid Portal ↗
              </a>
              <Button variant="secondary" size="sm" onClick={() => setShowIntegratorGuide(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
