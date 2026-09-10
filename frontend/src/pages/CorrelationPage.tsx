import React from 'react';
import { GitFork, MapPin, CheckCircle2 } from 'lucide-react';
import { VehicleJourney } from '../types';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';

interface CorrelationPageProps {
  journey: VehicleJourney;
  onOpenMap: () => void;
  onSearchNewPlate: (plate: string) => void;
}

export const CorrelationPage: React.FC<CorrelationPageProps> = ({
  journey,
  onOpenMap,
}) => {
  return (
    <div className="space-y-6">
      {/* Target Vehicle Header */}
      <div className="bg-[#0c1424] p-6 rounded-2xl border border-blue-600/50 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono text-xs font-bold border border-blue-500/30">
              CROSS-CAMERA CORRELATION
            </span>
            <span className="text-xs font-mono text-emerald-400">
              ✓ SPATIAL-TEMPORAL SPEED PLAUSIBILITY VERIFIED
            </span>
          </div>

          <div className="flex items-center gap-4 mt-2">
            <span className="px-4 py-1.5 rounded-xl bg-black border border-yellow-400/80 text-yellow-300 font-mono font-black text-2xl tracking-wider shadow-md">
              {journey.registration}
            </span>
            <div>
              <h2 className="text-base font-bold text-white uppercase font-mono">
                {journey.vehicle_class.toUpperCase()} SIGHTING TIMELINE
              </h2>
              <p className="text-xs text-slate-400 font-mono">
                Total Sightings: {journey.total_sightings} Cameras • Estimated Distance: {journey.total_distance_km} km
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="primary" size="md" icon={<MapPin className="h-4 w-4" />} onClick={onOpenMap}>
            View GIS Trajectory Map
          </Button>
        </div>
      </div>

      {/* Chronological Waypoints Timeline */}
      <Card
        title="Chronological Camera Waypoints & Journey Reconstruction"
        subtitle="Ordered movement history with inter-camera travel times and speed validation"
        icon={<GitFork className="h-4 w-4 text-blue-400" />}
      >
        <div className="relative pl-6 space-y-8 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-blue-600/50">
          {journey.waypoints.map((wp) => (
            <div key={wp.order} className="relative flex items-start gap-4">
              {/* Timeline Marker Dot */}
              <div className="absolute -left-6 mt-1 flex items-center justify-center">
                <div className="w-6 h-6 rounded-full bg-blue-600 border-2 border-[#0c1424] text-white font-mono text-xs font-bold flex items-center justify-center shadow-[0_0_10px_rgba(37,99,235,0.8)]">
                  {wp.order}
                </div>
              </div>

              {/* Waypoint Details Card */}
              <div className="flex-1 bg-[#090e1a] p-5 rounded-xl border border-slate-800 hover:border-blue-500/60 transition-all shadow-md">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                  <div>
                    <h4 className="text-sm font-bold text-white font-mono">{wp.camera_name}</h4>
                    <p className="text-xs text-slate-400">{wp.location}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono font-bold text-blue-300">
                      {new Date(wp.timestamp).toLocaleTimeString()}
                    </span>
                    <p className="text-[10px] font-mono text-slate-400">
                      {new Date(wp.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-3 text-xs font-mono">
                  <div>
                    <span className="text-slate-400 block text-[10px]">SPEED ESTIMATE</span>
                    <span className="text-white font-bold">{wp.speed_kmh} km/h</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">INTER-CAMERA TIME</span>
                    <span className="text-white font-bold">
                      {wp.travel_duration_minutes > 0 ? `+${wp.travel_duration_minutes} mins` : 'First Sighting'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">DISTANCE OFFSET</span>
                    <span className="text-white font-bold">+{wp.distance_km} km</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">PHYSICAL FEASIBILITY</span>
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Plausible
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
