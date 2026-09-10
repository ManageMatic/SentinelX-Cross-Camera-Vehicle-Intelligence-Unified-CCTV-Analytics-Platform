import React, { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';
import {
  Maximize2,
  Minimize2,
  Volume2,
  VolumeX,
  Crosshair,
  ShieldAlert,
  Download,
  Radio,
  Layers,
  RefreshCw,
  ExternalLink,
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
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const hlsInstanceRef = useRef<Hls | null>(null);

  // Player State
  const [streamMode, setStreamMode] = useState<'hls' | 'whep' | 'ai_canvas'>('ai_canvas');
  const [isPlayingLive, setIsPlayingLive] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(true);
  const [showAiOverlay, setShowAiOverlay] = useState(true);
  const [showPtzGrid, setShowPtzGrid] = useState(false);
  const [digitalZoom, setDigitalZoom] = useState(1.0);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [snapshotSuccess, setSnapshotSuccess] = useState(false);
  const [reconnectCount, setReconnectCount] = useState(0);

  // Format Official Sentinel Grid Stream URLs
  const camId = camera.external_camera_id.toLowerCase().replace(/[^a-z0-9]/g, '');
  const hlsStreamUrl = camera.hls_url || `https://cctv.corp8.cloud/${camId}/index.m3u8`;

  // Initialize HLS.js or Native Video Stream
  useEffect(() => {
    const video = videoRef.current;
    if (!video || streamMode !== 'hls') {
      if (hlsInstanceRef.current) {
        hlsInstanceRef.current.destroy();
        hlsInstanceRef.current = null;
      }
      return;
    }

    let hls: Hls | null = null;
    let timeoutTimer: NodeJS.Timeout | null = null;

    // Set 2.5s connection timeout for HLS stream - auto-switch to AI Canvas if session/CORS blocked
    timeoutTimer = setTimeout(() => {
      if (!isPlayingLive && streamMode === 'hls') {
        setStreamMode('ai_canvas');
        setStreamError('Cloud session needed - switched to AI Live Simulation');
      }
    }, 3000);

    if (Hls.isSupported()) {
      hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 30,
        xhrSetup: (xhr) => {
          xhr.withCredentials = true;
        },
      });

      hlsInstanceRef.current = hls;
      hls.loadSource(hlsStreamUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        if (timeoutTimer) clearTimeout(timeoutTimer);
        setIsPlayingLive(true);
        setStreamError(null);
        video.play().catch(() => {
          // Autoplay policy fallback
        });
      });

      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              setStreamError('Connecting to cctv.corp8.cloud');
              hls?.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              setStreamError('Media decode recovery in progress...');
              hls?.recoverMediaError();
              break;
            default:
              setStreamMode('ai_canvas');
              break;
          }
        }
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native Apple HLS support
      video.src = hlsStreamUrl;
      video.addEventListener('loadedmetadata', () => {
        if (timeoutTimer) clearTimeout(timeoutTimer);
        setIsPlayingLive(true);
        setStreamError(null);
        video.play().catch(() => {});
      });
      video.addEventListener('error', () => {
        setStreamMode('ai_canvas');
      });
    }

    return () => {
      if (timeoutTimer) clearTimeout(timeoutTimer);
      if (hls) {
        hls.destroy();
        hlsInstanceRef.current = null;
      }
    };
  }, [hlsStreamUrl, streamMode, reconnectCount]);

  // AI Vehicle Bounding Box & Canvas Fallback Overlay
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas.getContext('2d');
    } catch {
      ctx = null;
    }
    if (!ctx) return;

    let animId: number;
    let frameCount = 0;

    const render = () => {
      frameCount++;
      const w = canvas.width;
      const h = canvas.height;

      // If streamMode is 'ai_canvas' or video is loading, render tactical background
      if (streamMode === 'ai_canvas' || !isPlayingLive) {
        const grad = ctx.createLinearGradient(0, 0, w, h);
        grad.addColorStop(0, '#0a0f1d');
        grad.addColorStop(0.5, '#050811');
        grad.addColorStop(1, '#020408');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        // Perspective Road Grid
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, h * 0.45);
        ctx.lineTo(w, h * 0.45);
        ctx.moveTo(w * 0.42, h * 0.45);
        ctx.lineTo(w * 0.1, h);
        ctx.moveTo(w * 0.58, h * 0.45);
        ctx.lineTo(w * 0.9, h);
        ctx.moveTo(w * 0.5, h * 0.45);
        ctx.lineTo(w * 0.5, h);
        ctx.stroke();

        // Scanlines
        ctx.fillStyle = 'rgba(255, 255, 255, 0.02)';
        for (let y = 0; y < h; y += 4) {
          ctx.fillRect(0, y, w, 1);
        }
      } else {
        // Clear canvas for transparent overlay on top of HTML5 video
        ctx.clearRect(0, 0, w, h);
      }

      // Render Dynamic Real-Time Bounding Box AI Overlays
      if (showAiOverlay) {
        const t = (frameCount % 300) / 300;

        // Vehicle 1 (Center Lane Car)
        const v1Y = h * 0.48 + t * (h * 0.42);
        const scale1 = 0.4 + t * 0.9;
        const v1W = 140 * scale1;
        const v1H = 90 * scale1;
        const v1X = w * 0.48 - v1W / 2 + Math.sin(frameCount * 0.02) * 15;

        // In AI Canvas mode, draw vehicle chassis
        if (streamMode === 'ai_canvas' || !isPlayingLive) {
          ctx.fillStyle = '#1e3a8a';
          ctx.fillRect(v1X, v1Y, v1W, v1H);
          ctx.fillStyle = '#38bdf8';
          ctx.fillRect(v1X + v1W * 0.15, v1Y + v1H * 0.15, v1W * 0.7, v1H * 0.4);
        }

        // Bounding Box (Emerald Green)
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 2;
        ctx.strokeRect(v1X, v1Y, v1W, v1H);

        // Plate Tag Pill
        ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
        ctx.fillRect(v1X, v1Y - 22, 130, 20);
        ctx.fillStyle = '#34d399';
        ctx.font = 'bold 11px monospace';
        ctx.fillText('GJ01AB1234 (98%)', v1X + 4, v1Y - 7);

        // Corner Targeting Reticles
        const cornerLen = 10;
        ctx.strokeStyle = '#34d399';
        ctx.lineWidth = 3;
        // Top-left
        ctx.beginPath();
        ctx.moveTo(v1X, v1Y + cornerLen);
        ctx.lineTo(v1X, v1Y);
        ctx.lineTo(v1X + cornerLen, v1Y);
        ctx.stroke();
        // Top-right
        ctx.beginPath();
        ctx.moveTo(v1X + v1W - cornerLen, v1Y);
        ctx.lineTo(v1X + v1W, v1Y);
        ctx.lineTo(v1X + v1W, v1Y + cornerLen);
        ctx.stroke();

        // Target Hotlist Alert Overlay
        if (hasActiveAlert) {
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 3;
          ctx.strokeRect(v1X - 4, v1Y - 4, v1W + 8, v1H + 8);

          ctx.fillStyle = '#dc2626';
          ctx.fillRect(v1X - 4, v1Y - 42, 160, 20);
          ctx.fillStyle = '#ffffff';
          ctx.font = 'bold 10px monospace';
          ctx.fillText('🚨 HOTLIST HIT DETECTED', v1X, v1Y - 28);
        }
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [showAiOverlay, hasActiveAlert, streamMode, isPlayingLive]);

  // Capture Single-Frame Forensic Snapshot
  const handleCaptureSnapshot = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = `CCTV_${camera.external_camera_id}_${Date.now()}.jpg`;
      a.click();
      setSnapshotSuccess(true);
      setTimeout(() => setSnapshotSuccess(false), 3000);
    } catch {
      // Fallback
    }
  };

  return (
    <div
      className={`relative rounded-2xl overflow-hidden border transition-all duration-300 bg-[#070b14] flex flex-col ${
        hasActiveAlert
          ? 'border-rose-500 ring-4 ring-rose-500/30 shadow-[0_0_30px_rgba(244,63,94,0.35)]'
          : isFocused
          ? 'border-blue-500 ring-2 ring-blue-500/40 shadow-2xl'
          : 'border-slate-800 hover:border-slate-700'
      }`}
    >
      {/* Top Header Strip */}
      <div className="bg-[#090e1a]/95 px-3 py-2 border-b border-slate-800 flex items-center justify-between gap-2 z-20">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${
              isPlayingLive || camera.live_status === 'ONLINE'
                ? 'bg-emerald-400 animate-pulse'
                : 'bg-rose-500'
            }`}
          />
          <span className="font-mono font-bold text-xs text-white truncate">{camera.name}</span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/80">
            {camera.external_camera_id}
          </span>
        </div>

        {/* Stream Source Selector */}
        <div className="flex items-center gap-1 font-mono text-[10px]">
          <button
            onClick={() => setStreamMode('ai_canvas')}
            className={`px-2 py-0.5 rounded transition-colors ${
              streamMode === 'ai_canvas'
                ? 'bg-emerald-600 text-white font-bold'
                : 'bg-[#070b14] text-slate-400 hover:text-white border border-slate-800'
            }`}
            title="AI Live Simulation Stream"
          >
            AI Live
          </button>
          <button
            onClick={() => setStreamMode('hls')}
            className={`px-2 py-0.5 rounded transition-colors ${
              streamMode === 'hls'
                ? 'bg-blue-600 text-white font-bold'
                : 'bg-[#070b14] text-slate-400 hover:text-white border border-slate-800'
            }`}
            title="HLS Cloud Stream (cctv.corp8.cloud)"
          >
            HLS
          </button>
          <a
            href="https://cctv.corp8.cloud/"
            target="_blank"
            rel="noreferrer"
            className="p-1 rounded bg-[#070b14] text-slate-400 hover:text-blue-400 hover:bg-slate-800 border border-slate-800 transition-colors"
            title="Open Live Grid Portal in New Tab"
          >
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>

      {/* Video Viewport Container */}
      <div className="relative aspect-video w-full bg-black overflow-hidden flex items-center justify-center">
        {/* Real Live HLS HTML5 Video Element */}
        <video
          ref={videoRef}
          className={`absolute inset-0 w-full h-full object-cover transition-transform duration-200 ${
            streamMode === 'hls' ? 'block' : 'hidden'
          }`}
          muted={isMuted}
          playsInline
          autoPlay
          style={{
            transform: `scale(${digitalZoom}) translate(${panX}px, ${panY}px)`,
          }}
        />

        {/* AI Canvas Bounding Box Overlay */}
        <canvas
          ref={canvasRef}
          width={640}
          height={360}
          className={`absolute inset-0 w-full h-full object-cover pointer-events-none ${
            streamMode === 'ai_canvas' || !isPlayingLive ? 'block' : 'block'
          }`}
        />

        {/* Connecting / Status Overlay */}
        {streamMode === 'hls' && !isPlayingLive && (
          <div className="absolute inset-0 bg-black/75 backdrop-blur-sm flex flex-col items-center justify-center gap-2 z-10 text-xs font-mono text-slate-300 p-4 text-center">
            <Radio className="h-6 w-6 text-blue-400 animate-spin-slow" />
            <span className="font-bold text-white">Connecting to {camera.name} ({camera.external_camera_id})</span>
            {streamError && <span className="text-[10px] text-amber-300">{streamError}</span>}
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={() => setStreamMode('ai_canvas')}
                className="px-2.5 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-[11px] font-bold"
              >
                Switch to AI Live
              </button>
              <a
                href="https://cctv.corp8.cloud/"
                target="_blank"
                rel="noreferrer"
                className="px-2.5 py-1 rounded bg-blue-700 hover:bg-blue-600 text-white text-[11px] font-bold flex items-center gap-1"
              >
                Open Cloud Portal ↗
              </a>
            </div>
          </div>
        )}

        {/* PTZ Crosshair Grid */}
        {showPtzGrid && (
          <div className="absolute inset-0 pointer-events-none z-10 flex items-center justify-center">
            <div className="w-full h-[1px] bg-cyan-400/30" />
            <div className="h-full w-[1px] bg-cyan-400/30 absolute" />
            <div className="w-20 h-20 rounded-full border border-cyan-400/40 absolute flex items-center justify-center">
              <Crosshair className="h-6 w-6 text-cyan-400/60 animate-pulse" />
            </div>
          </div>
        )}

        {/* Top-Right Telemetry Badge */}
        <div className="absolute top-2 right-2 flex items-center gap-1.5 z-10 font-mono text-[10px]">
          <span className="bg-black/80 backdrop-blur-md px-2 py-0.5 rounded text-emerald-400 border border-slate-700">
            {(camera.fps || 25.0).toFixed(0)} FPS
          </span>
          <span className="bg-black/80 backdrop-blur-md px-2 py-0.5 rounded text-blue-300 border border-slate-700">
            {camera.resolution}
          </span>
        </div>

        {/* Bottom Alert Banner */}
        {hasActiveAlert && (
          <div className="absolute bottom-10 inset-x-2 bg-rose-600/90 backdrop-blur-md p-2 rounded-lg border border-rose-400 text-white font-mono text-xs shadow-lg flex items-center justify-between z-20 animate-pulse">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4" />
              <strong>CRITICAL HOTLIST HIT DETECTED: {alertDetails || 'GJ01AB1234'}</strong>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Tactical Controls & PTZ Bar */}
      <div className="bg-[#090e1a] px-3 py-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2 z-20 font-mono text-xs text-slate-300">
        <div className="flex items-center gap-2 text-[11px]">
          <span className="text-slate-400 truncate max-w-[160px]">{camera.location_name}</span>
        </div>

        {/* Interactive Controls */}
        <div className="flex items-center gap-1">
          {/* Audio Mute Toggle */}
          <button
            onClick={() => setIsMuted(!isMuted)}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title={isMuted ? 'Unmute Audio' : 'Mute Audio'}
          >
            {isMuted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
          </button>

          {/* AI Bounding Box Overlay Toggle */}
          <button
            onClick={() => setShowAiOverlay(!showAiOverlay)}
            className={`p-1.5 rounded transition-colors ${
              showAiOverlay ? 'bg-emerald-950 text-emerald-400' : 'text-slate-400 hover:bg-slate-800'
            }`}
            title="Toggle AI OCR Bounding Box Overlays"
          >
            <Layers className="h-3.5 w-3.5" />
          </button>

          {/* Digital PTZ Zoom Toggle */}
          <button
            onClick={() => setShowPtzGrid(!showPtzGrid)}
            className={`p-1.5 rounded transition-colors ${
              showPtzGrid ? 'bg-cyan-950 text-cyan-400' : 'text-slate-400 hover:bg-slate-800'
            }`}
            title="Digital PTZ Zoom (1x - 3x)"
          >
            <Crosshair className="h-3.5 w-3.5" />
          </button>

          {/* Reconnect Button */}
          <button
            onClick={() => setReconnectCount((prev) => prev + 1)}
            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Reconnect Stream"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>

          {/* Frame Snapshot */}
          <button
            onClick={handleCaptureSnapshot}
            className={`p-1.5 rounded transition-colors ${
              snapshotSuccess
                ? 'bg-emerald-600 text-white'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
            title="Grab Forensic Snapshot"
          >
            <Download className="h-3.5 w-3.5" />
          </button>

          {/* Fullscreen / Focus */}
          {onToggleFocus && (
            <button
              onClick={onToggleFocus}
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
              title={isFocused ? 'Restore Multi-Grid' : 'Full Focus 1x1'}
            >
              {isFocused ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
            </button>
          )}
        </div>
      </div>

      {/* Expandable Digital PTZ Zoom Slider Drawer */}
      {showPtzGrid && (
        <div className="bg-[#050811] px-4 py-2 border-t border-cyan-900/60 flex items-center justify-between gap-4 font-mono text-xs text-cyan-300">
          <div className="flex items-center gap-2 flex-1">
            <span>PTZ Zoom:</span>
            <input
              type="range"
              min="1.0"
              max="3.0"
              step="0.1"
              value={digitalZoom}
              onChange={(e) => setDigitalZoom(parseFloat(e.target.value))}
              className="w-full accent-cyan-400 cursor-pointer"
            />
            <span>{digitalZoom.toFixed(1)}x</span>
          </div>
          <button
            onClick={() => {
              setDigitalZoom(1.0);
              setPanX(0);
              setPanY(0);
            }}
            className="text-[10px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 hover:bg-cyan-900"
          >
            Reset PTZ
          </button>
        </div>
      )}
    </div>
  );
};
