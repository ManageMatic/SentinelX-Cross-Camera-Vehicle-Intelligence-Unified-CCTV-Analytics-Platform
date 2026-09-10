import React from 'react';
import { Navigation, Layers } from 'lucide-react';
import { Camera, VehicleJourney } from '../types';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

interface MapPageProps {
  cameras: Camera[];
  journey?: VehicleJourney;
}

export const MapPage: React.FC<MapPageProps> = ({ cameras, journey }) => {
  return (
    <div className="space-y-6">
      {/* Map Header & Controls */}
      <div className="bg-[#0c1424] p-4 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-black text-white font-mono tracking-wide">
            GIS OPENSTREETMAP TACTICAL RADAR
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Dynamic camera geospatial positions & cross-camera vehicle trajectory polylines
          </p>
        </div>

        <div className="flex items-center gap-3">
          {journey && (
            <span className="px-3 py-1 rounded bg-black border border-yellow-500/60 text-yellow-300 font-mono font-bold text-xs">
              TRACKING: {journey.registration}
            </span>
          )}
          <Button variant="secondary" size="sm" icon={<Layers className="h-3.5 w-3.5" />}>
            Toggle Heatmap Layer
          </Button>
        </div>
      </div>

      {/* Map Viewport Container */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left 3 cols: Tactical Map Screen */}
        <div className="lg:col-span-3 bg-[#090e1a] rounded-2xl border border-slate-800 p-4 h-[600px] flex flex-col justify-between relative overflow-hidden shadow-2xl bg-tactical-grid">
          {/* Top Floating Legend */}
          <div className="z-10 flex items-center gap-3 bg-[#070b14]/90 backdrop-blur-md p-3 rounded-xl border border-slate-700 w-max text-xs font-mono">
            <span className="flex items-center gap-1.5 text-blue-400">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> CCTV Node
            </span>
            <span className="flex items-center gap-1.5 text-yellow-400">
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" /> Sighting Waypoint
            </span>
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Plausible Vector
            </span>
          </div>

          {/* Center Geospatial Radar Center Mock */}
          <div className="m-auto text-center space-y-4">
            <div className="relative inline-block">
              <div className="w-48 h-48 rounded-full border border-blue-500/30 flex items-center justify-center animate-pulse">
                <div className="w-32 h-32 rounded-full border border-blue-500/50 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full border border-blue-400 flex items-center justify-center bg-blue-950/40">
                    <Navigation className="h-6 w-6 text-blue-400 animate-spin" />
                  </div>
                </div>
              </div>
            </div>

            <div>
              <p className="text-sm font-bold font-mono text-white">GUJARAT STATE GIS TACTICAL LAYER</p>
              <p className="text-xs text-slate-400 font-mono">
                Centered on Ahmedabad - Gandhinagar Corridor (23.0338° N, 72.5072° E)
              </p>
            </div>
          </div>

          {/* Bottom Waypoint Bar */}
          {journey && (
            <div className="z-10 bg-[#070b14]/90 backdrop-blur-md p-3 rounded-xl border border-slate-700 flex items-center justify-between text-xs font-mono">
              <span>Path: {journey.waypoints.map((w) => w.camera_name).join(' ➔ ')}</span>
              <span className="text-emerald-400 font-bold">{journey.total_distance_km} KM TOTAL</span>
            </div>
          )}
        </div>

        {/* Right 1 col: Camera Waypoint List */}
        <div className="space-y-4">
          <Card title="Active GIS Nodes" subtitle="All geocoded camera positions">
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {cameras.map((cam) => (
                <div
                  key={cam.id}
                  className="p-3 rounded-lg bg-[#080d19] border border-slate-800 hover:border-blue-500/60 transition-all text-xs font-mono"
                >
                  <div className="flex items-center justify-between text-white font-bold">
                    <span>{cam.name}</span>
                    <span className="text-emerald-400">ONLINE</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">{cam.location_name}</p>
                  <p className="text-[9px] text-slate-400 mt-0.5">
                    Lat: {cam.latitude} • Lng: {cam.longitude}
                  </p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
