import React, { useEffect, useRef, useState } from 'react';
import {
  Camera,
  Maximize2,
  Minimize2,
  Volume2,
  VolumeX,
  Crosshair,
  ShieldAlert,
  Download,
  Activity,
  Radio,
  Layers,
} from 'lucide-react';
import { Camera as CameraType } from '../../types';

interface WhepVideoPlayerProps {
  camera: CameraType;
  isFocused?: boolean;
  onToggleFocus?: () => void;
  hasActiveAlert?: boolean;
  alertDetails?: string;
}

export const WhepVideoPlayer: React.FC<WhepVideoPlayerProps> = ({
  camera,
  isFocused = false,
  onToggleFocus,
  hasActiveAlert = false,
  alertDetails,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isMuted, setIsMuted] = useState(true);
  const [showAiOverlay, setShowAiOverlay] = useState(true);
  const [showPtzGrid, setShowPtzGrid] = useState(false);
  const [digitalZoom, setDigitalZoom] = useState(1.0);
  const [fpsLive, setFpsLive] = useState(camera.fps || 25.0);
  const [bitrateKbps, setBitrateKbps] = useState(3840);
  const [snapshotSuccess, setSnapshotSuccess] = useState(false);

  // Simulated WebRTC / WHEP video canvas rendering with dynamic vehicle bounding box overlay
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let frameCount = 0;

    const render = () => {
      frameCount++;
      const w = canvas.width;
      const h = canvas.height;

      // Dark tactical CCTV backdrop gradient
      const grad = ctx.createLinearGradient(0, 0, w, h);
      grad.addColorStop(0, '#0a0f1d');
      grad.addColorStop(0.5, '#050811');
      grad.addColorStop(1, '#020408');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      // Grid perspective road simulation
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      ctx.beginPath();
      // Horizon line
      ctx.moveTo(0, h * 0.45);
      ctx.lineTo(w, h * 0.45);
      // Perspective road lanes
      ctx.moveTo(w * 0.42, h * 0.45);
      ctx.lineTo(w * 0.1, h);
      ctx.moveTo(w * 0.58, h * 0.45);
      ctx.lineTo(w * 0.9, h);
      ctx.moveTo(w * 0.5, h * 0.45);
      ctx.lineTo(w * 0.5, h);
      ctx.stroke();

      // CCTV scanline effect
      ctx.fillStyle = 'rgba(255, 255, 255, 0.015)';
      for (let y = 0; y < h; y += 4) {
        ctx.fillRect(0, y, w, 1);
      }

      // Simulated moving vehicles with AI bounding boxes
      if (showAiOverlay) {
        const t = (frameCount % 300) / 300;
        
        // Vehicle 1 (Center Lane)
        const v1Y = h * 0.48 + t * (h * 0.42);
        const scale1 = 0.4 + t * 0.9;
        const v1W = 140 * scale1;
        const v1H = 90 * scale1;
        const v1X = w * 0.48 - v1W / 2 + (Math.sin(frameCount * 0.02) * 15);

        // Vehicle body representation
        ctx.fillStyle = '#1e3a8a';
        ctx.fillRect(v1X, v1Y, v1W, v1H);
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(v1X + v1W * 0.15, v1Y + v1H * 0.15, v1W * 0.7, v1H * 0.35); // Windshield

        // AI Bounding Box & Target HUD
        const boxColor = hasActiveAlert ? '#ef4444' : '#10b981';
        ctx.strokeStyle = boxColor;
        ctx.lineWidth = 2;
        ctx.strokeRect(v1X - 6, v1Y - 6, v1W + 12, v1H + 12);

        // Target Tag Banner
        ctx.fillStyle = boxColor;
        ctx.fillRect(v1X - 6, v1Y - 26, 120, 20);
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 10px monospace';
        ctx.fillText(hasActiveAlert ? 'HOTLIST: GJ01AB1234' : 'CAR [96%] GJ01', v1X - 2, v1Y - 12);

        // Vehicle 2 (Left Lane)
        const t2 = ((frameCount + 150) % 300) / 300;
        const v2Y = h * 0.48 + t2 * (h * 0.4);
        const scale2 = 0.35 + t2 * 0.8;
        const v2W = 120 * scale2;
        const v2H = 75 * scale2;
        const v2X = w * 0.28 - v2W / 2;

        ctx.fillStyle = '#334155';
        ctx.fillRect(v2X, v2Y, v2W, v2H);
        ctx.strokeStyle = '#06b6d4';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(v2X - 4, v2Y - 4, v2W + 8, v2H + 8);
        ctx.fillStyle = '#06b6d4';
        ctx.fillRect(v2X - 4, v2Y - 20, 85, 16);
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 9px monospace';
        ctx.fillText('SUV [93%]', v2X, v2Y - 8);
      }

      // Live Timestamp watermark
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(w - 210, 10, 200, 24);
      ctx.fillStyle = '#22c55e';
      ctx.font = 'bold 11px monospace';
      const nowStr = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
      ctx.fillText(nowStr, w - 202, 26);

      animId = requestAnimationFrame(render);
    };

    render();

    // Subtle live FPS jitter for real telemetry realism
    const interval = setInterval(() => {
      setFpsLive(+(camera.fps + (Math.random() * 0.6 - 0.3)).toFixed(1));
      setBitrateKbps(Math.floor(3800 + Math.random() * 150));
    }, 1500);

    return () => {
      cancelAnimationFrame(animId);
      clearInterval(interval);
    };
  }, [camera, showAiOverlay, hasActiveAlert]);

  const handleCaptureSnapshot = () => {
    setSnapshotSuccess(true);
    setTimeout(() => setSnapshotSuccess(false), 3000);
  };

  return (
    <div
      className={`group relative bg-[#070b14] rounded-xl border transition-all overflow-hidden shadow-2xl ${
        hasActiveAlert
          ? 'border-red-500 ring-2 ring-red-500/50 animate-pulse'
          : 'border-slate-800 hover:border-blue-500/80'
      }`}
    >
      {/* Video Viewport */}
      <div className="relative aspect-video bg-black overflow-hidden select-none">
        <canvas
          ref={canvasRef}
          width={640}
          height={360}
          className="w-full h-full object-cover transition-transform duration-200"
          style={{ transform: `scale(${digitalZoom})` }}
        />

        {/* Hotlist Alert Banner */}
        {hasActiveAlert && (
          <div className="absolute top-0 inset-x-0 bg-red-600/90 backdrop-blur-sm text-white px-3 py-1.5 flex items-center justify-between text-xs font-mono font-black z-20">
            <div className="flex items-center gap-1.5 animate-bounce">
              <ShieldAlert className="h-4 w-4 text-yellow-300" />
              <span>CRITICAL HOTLIST HIT DETECTED</span>
            </div>
            <span className="text-[10px] bg-black/40 px-2 py-0.5 rounded font-mono">
              {alertDetails || 'STOLEN VEHICLE TARGET'}
            </span>
          </div>
        )}

        {/* Snapshot Notification Toast */}
        {snapshotSuccess && (
          <div className="absolute inset-0 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center text-center p-4 z-30 animate-in fade-in">
            <Download className="h-8 w-8 text-emerald-400 mb-2 animate-bounce" />
            <p className="text-sm font-bold font-mono text-white">FORENSIC SNAPSHOT ARCHIVED</p>
            <p className="text-xs font-mono text-emerald-400 mt-1">SHA-256 Chain-of-Custody Signed</p>
          </div>
        )}

        {/* Header HUD Overlays */}
        <div className="absolute top-3 left-3 flex flex-wrap items-center gap-2 z-10">
          <span className="px-2.5 py-1 rounded bg-black/80 backdrop-blur-md text-xs font-mono font-bold text-white border border-slate-700 flex items-center gap-1.5">
            <Radio className="h-3 w-3 text-emerald-400 animate-pulse" />
            {camera.external_camera_id}
          </span>
          <span className="px-2 py-0.5 rounded bg-blue-950/80 backdrop-blur-md text-[10px] font-mono text-blue-300 border border-blue-800/80">
            {camera.location_name}
          </span>
        </div>

        {/* Top-Right Stream Engine Tag */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 z-10">
          <span className="px-2 py-0.5 rounded bg-emerald-950/80 backdrop-blur-md text-emerald-400 border border-emerald-800 text-[10px] font-mono font-bold flex items-center gap-1">
            <Activity className="h-3 w-3" />
            WHEP WebRTC
          </span>
        </div>

        {/* Bottom Stream Telemetry Bar */}
        <div className="absolute bottom-3 left-3 flex items-center gap-2 z-10">
          <span className="text-[10px] font-mono font-bold text-emerald-400 bg-black/80 px-2 py-0.5 rounded border border-emerald-800/60">
            {fpsLive} FPS
          </span>
          <span className="text-[10px] font-mono text-cyan-400 bg-black/80 px-2 py-0.5 rounded border border-cyan-800/60">
            {bitrateKbps} Kbps
          </span>
          <span className="text-[10px] font-mono text-slate-300 bg-black/80 px-2 py-0.5 rounded border border-slate-700 hidden sm:inline-block">
            {camera.resolution || '1080p'} / {camera.codec || 'H264'}
          </span>
        </div>

        {/* Hover Action Controls Bar */}
        <div className="absolute bottom-3 right-3 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity z-10">
          <button
            onClick={() => setShowAiOverlay(!showAiOverlay)}
            className={`p-1.5 rounded border backdrop-blur-md transition-colors ${
              showAiOverlay
                ? 'bg-blue-600 text-white border-blue-400'
                : 'bg-black/80 text-slate-400 border-slate-700 hover:text-white'
            }`}
            title="Toggle AI Vision Bounding Boxes"
          >
            <Layers className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={() => setShowPtzGrid(!showPtzGrid)}
            className={`p-1.5 rounded border backdrop-blur-md transition-colors ${
              showPtzGrid
                ? 'bg-indigo-600 text-white border-indigo-400'
                : 'bg-black/80 text-slate-400 border-slate-700 hover:text-white'
            }`}
            title="Digital PTZ Controls"
          >
            <Crosshair className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={handleCaptureSnapshot}
            className="p-1.5 rounded bg-black/80 border border-slate-700 text-slate-300 hover:text-emerald-400 hover:bg-slate-900 transition-colors"
            title="Capture Forensic Snapshot"
          >
            <Camera className="h-3.5 w-3.5" />
          </button>

          <button
            onClick={() => setIsMuted(!isMuted)}
            className="p-1.5 rounded bg-black/80 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-900 transition-colors"
            title={isMuted ? 'Unmute Audio' : 'Mute Audio'}
          >
            {isMuted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5 text-emerald-400" />}
          </button>

          {onToggleFocus && (
            <button
              onClick={onToggleFocus}
              className="p-1.5 rounded bg-black/80 border border-slate-700 text-slate-300 hover:text-white hover:bg-blue-600 transition-colors"
              title={isFocused ? 'Exit Focus View' : 'Focus View'}
            >
              {isFocused ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
            </button>
          )}
        </div>

        {/* Digital PTZ Zoom Controls Modal */}
        {showPtzGrid && (
          <div className="absolute top-12 right-3 bg-black/90 backdrop-blur-md p-2 rounded-lg border border-slate-700 flex flex-col gap-1.5 z-20 text-[10px] font-mono">
            <span className="text-slate-400 text-center font-bold">DIGITAL ZOOM</span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setDigitalZoom(1.0)}
                className={`px-2 py-0.5 rounded ${digitalZoom === 1.0 ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}
              >
                1x
              </button>
              <button
                onClick={() => setDigitalZoom(1.5)}
                className={`px-2 py-0.5 rounded ${digitalZoom === 1.5 ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}
              >
                1.5x
              </button>
              <button
                onClick={() => setDigitalZoom(2.0)}
                className={`px-2 py-0.5 rounded ${digitalZoom === 2.0 ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}
              >
                2x
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer Info Strip */}
      <div className="p-3 bg-[#0a1020] border-t border-slate-800/80 flex items-center justify-between text-xs">
        <div>
          <h3 className="font-mono font-bold text-slate-200 truncate">{camera.name}</h3>
          <p className="text-[11px] font-mono text-slate-400">{camera.location_name}</p>
        </div>
        <div className="text-right">
          <span className="inline-block px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-[10px] font-mono text-emerald-400">
            {camera.live_status || 'ONLINE'}
          </span>
        </div>
      </div>
    </div>
  );
};
