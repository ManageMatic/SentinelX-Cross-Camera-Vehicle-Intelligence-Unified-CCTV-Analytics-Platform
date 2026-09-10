import React, { useEffect, useRef } from 'react';
import { Camera, VehicleJourney, JourneyWaypoint } from '../../types';
import L from 'leaflet';

interface TacticalLeafletMapProps {
  cameras: Camera[];
  journey?: VehicleJourney | null;
  activeWaypointIndex?: number | null;
  selectedCameraId?: string | null;
  onSelectCamera?: (camera: Camera) => void;
  onSelectWaypoint?: (waypoint: JourneyWaypoint, index: number) => void;
  showCamerasLayer?: boolean;
  showTrajectoryLayer?: boolean;
  showSpeedLayer?: boolean;
  showLoiteringLayer?: boolean;
  centerCoordinates?: [number, number];
  zoomLevel?: number;
}

export const TacticalLeafletMap: React.FC<TacticalLeafletMapProps> = ({
  cameras,
  journey,
  activeWaypointIndex,
  selectedCameraId,
  onSelectCamera,
  onSelectWaypoint,
  showCamerasLayer = true,
  showTrajectoryLayer = true,
  showSpeedLayer = true,
  showLoiteringLayer = true,
  centerCoordinates = [23.0225, 72.5714], // Gujarat / Ahmedabad default
  zoomLevel = 11,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersGroupRef = useRef<L.LayerGroup | null>(null);

  // Initialize Leaflet Map Instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Prevent re-initialization on hot reload
    if (!mapInstanceRef.current) {
      try {
        const map = L.map(mapContainerRef.current, {
          center: centerCoordinates,
          zoom: zoomLevel,
          zoomControl: false,
          attributionControl: false,
        });

        // Add 100% Free OpenStreetMap Basemap (No API Key Required, No Watermarks)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          subdomains: ['a', 'b', 'c'],
          className: 'tactical-dark-tiles',
        }).addTo(map);

        // Custom Zoom Control at Top-Right
        L.control.zoom({ position: 'topright' }).addTo(map);

        const layersGroup = L.layerGroup().addTo(map);
        layersGroupRef.current = layersGroup;
        mapInstanceRef.current = map;
      } catch (e) {
        // Fallback gracefully in headless test / JSDOM environments
        console.warn('TacticalLeafletMap initialized in fallback mode', e);
      }
    }

    return () => {
      // Map cleanup if container is unmounted
    };
  }, []);

  // Update Center and Zoom if controlled props change
  useEffect(() => {
    if (mapInstanceRef.current && centerCoordinates) {
      try {
        mapInstanceRef.current.setView(centerCoordinates, zoomLevel, { animate: true });
      } catch (e) {
        // Ignore setView errors in JSDOM
      }
    }
  }, [centerCoordinates, zoomLevel]);

  // Render Map Layers: Camera Nodes, Trajectory Lines, and Waypoints
  useEffect(() => {
    const map = mapInstanceRef.current;
    const group = layersGroupRef.current;
    if (!map || !group) return;

    group.clearLayers();

    // 1. Render CCTV Camera Markers
    if (showCamerasLayer) {
      cameras.forEach((cam) => {
        const isSelected = cam.id === selectedCameraId;
        const isOnline = cam.live_status === 'ONLINE';

        const markerHtml = `
          <div class="relative flex items-center justify-center cursor-pointer group">
            <div class="w-7 h-7 rounded-full flex items-center justify-center ${
              isSelected
                ? 'bg-blue-600 ring-4 ring-blue-400/50 shadow-lg shadow-blue-500/50'
                : isOnline
                ? 'bg-[#0f172a] border-2 border-emerald-400 text-emerald-400'
                : 'bg-[#1e1e24] border-2 border-rose-500 text-rose-400'
            }">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
              </svg>
            </div>
            ${
              isOnline
                ? '<span class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping"></span>'
                : ''
            }
          </div>
        `;

        const icon = L.divIcon({
          html: markerHtml,
          className: 'custom-camera-pin',
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        });

        const marker = L.marker([cam.latitude, cam.longitude], { icon });

        // Popup with metadata and action
        const popupContent = `
          <div class="font-mono text-xs space-y-1 p-1">
            <div class="font-bold text-white flex items-center justify-between border-b border-slate-700 pb-1">
              <span>${cam.name}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded ${
                isOnline ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'
              }">${cam.live_status}</span>
            </div>
            <div class="text-slate-300 text-[11px] pt-1">${cam.location_name}</div>
            <div class="text-slate-400 text-[10px]">ID: <span class="text-blue-400">${cam.external_camera_id}</span> • ${cam.fps} FPS (${cam.resolution})</div>
            <div class="text-[10px] text-slate-500 pt-0.5">GPS: ${cam.latitude.toFixed(4)}, ${cam.longitude.toFixed(4)}</div>
          </div>
        `;
        marker.bindPopup(popupContent);

        marker.on('click', () => {
          if (onSelectCamera) onSelectCamera(cam);
        });

        marker.addTo(group);
      });
    }

    // 2. Render Vehicle Trajectory Polylines & Waypoint Pins
    if (journey && journey.waypoints && journey.waypoints.length > 0) {
      const latlngs: [number, number][] = journey.waypoints.map((wp) => [wp.latitude, wp.longitude]);

      // Connect trajectory polylines
      if (showTrajectoryLayer && latlngs.length >= 2) {
        // Render glowing background path
        L.polyline(latlngs, {
          color: '#3b82f6',
          weight: 6,
          opacity: 0.4,
          smoothFactor: 1,
        }).addTo(group);

        // Render animated directional foreground dashed path
        L.polyline(latlngs, {
          color: '#60a5fa',
          weight: 3,
          dashArray: '8, 8',
          opacity: 0.9,
          smoothFactor: 1,
        }).addTo(group);

        // Render Speed & Physical Feasibility Vectors for each leg
        if (showSpeedLayer) {
          for (let i = 0; i < journey.waypoints.length - 1; i++) {
            const w1 = journey.waypoints[i];
            const w2 = journey.waypoints[i + 1];
            const midLat = (w1.latitude + w2.latitude) / 2;
            const midLng = (w1.longitude + w2.longitude) / 2;

            const isHighSpeed = w2.speed_kmh > 120;
            const badgeColor = !w2.is_plausible
              ? 'bg-rose-900 border-rose-500 text-rose-200'
              : isHighSpeed
              ? 'bg-amber-900 border-amber-500 text-amber-200'
              : 'bg-emerald-950 border-emerald-500 text-emerald-300';

            const speedLabel = `
              <div class="px-2 py-0.5 rounded-full border text-[9px] font-mono font-bold shadow-md ${badgeColor} whitespace-nowrap">
                ${w2.speed_kmh.toFixed(0)} km/h • ${w2.distance_km.toFixed(1)} km
              </div>
            `;

            const speedIcon = L.divIcon({
              html: speedLabel,
              className: 'custom-speed-badge',
              iconSize: [80, 20],
              iconAnchor: [40, 10],
            });

            L.marker([midLat, midLng], { icon: speedIcon }).addTo(group);
          }
        }
      }

      // Render Chronological Waypoint Pins (1, 2, 3...)
      journey.waypoints.forEach((wp, index) => {
        const isActive = activeWaypointIndex === index;
        const isFirst = index === 0;
        const isLast = index === journey.waypoints.length - 1;

        const pinColor = isActive
          ? 'bg-amber-500 text-black ring-4 ring-amber-300 animate-pulse'
          : isFirst
          ? 'bg-emerald-500 text-black'
          : isLast
          ? 'bg-rose-500 text-white'
          : 'bg-blue-600 text-white';

        const waypointHtml = `
          <div class="relative flex items-center justify-center cursor-pointer">
            <div class="w-8 h-8 rounded-full flex items-center justify-center font-mono font-black text-xs shadow-xl border-2 border-white/80 ${pinColor}">
              ${wp.order || index + 1}
            </div>
            ${
              isActive
                ? '<div class="absolute -inset-1 rounded-full border-2 border-amber-400 animate-ping"></div>'
                : ''
            }
          </div>
        `;

        const icon = L.divIcon({
          html: waypointHtml,
          className: 'custom-waypoint-pin',
          iconSize: [32, 32],
          iconAnchor: [16, 16],
        });

        const marker = L.marker([wp.latitude, wp.longitude], { icon });

        // Waypoint Sighting Popup
        const popupContent = `
          <div class="font-mono text-xs space-y-1.5 p-1 w-52">
            <div class="font-bold text-white flex items-center justify-between border-b border-slate-700 pb-1">
              <span class="text-amber-400">WAYPOINT #${wp.order || index + 1}</span>
              <span class="text-[10px] text-slate-400">${new Date(wp.timestamp).toLocaleTimeString()}</span>
            </div>
            <div class="text-white font-semibold text-[11px]">${wp.camera_name}</div>
            <div class="text-slate-300 text-[10px]">${wp.location}</div>
            <div class="grid grid-cols-2 gap-1 bg-[#090e1a] p-1.5 rounded border border-slate-800 text-[10px]">
              <div><span class="text-slate-400">Speed:</span> <span class="text-emerald-400 font-bold">${wp.speed_kmh} km/h</span></div>
              <div><span class="text-slate-400">Leg:</span> <span class="text-blue-400 font-bold">${wp.distance_km} km</span></div>
            </div>
            <div class="text-[10px] text-slate-400">Plausibility: <span class="${
              wp.is_plausible ? 'text-emerald-400' : 'text-rose-400 font-bold'
            }">${wp.is_plausible ? 'PLAUSIBLE' : 'FLAGGED (SPEED ANOMALY)'}</span></div>
          </div>
        `;
        marker.bindPopup(popupContent);

        marker.on('click', () => {
          if (onSelectWaypoint) onSelectWaypoint(wp, index);
        });

        marker.addTo(group);

        // Optional Loitering Radius Circle
        if (showLoiteringLayer && (wp.travel_duration_minutes > 20 || index === 0)) {
          L.circle([wp.latitude, wp.longitude], {
            radius: 400,
            color: '#f59e0b',
            weight: 1,
            fillColor: '#f59e0b',
            fillOpacity: 0.12,
            dashArray: '4, 4',
          }).addTo(group);
        }
      });
    }
  }, [
    cameras,
    journey,
    activeWaypointIndex,
    selectedCameraId,
    showCamerasLayer,
    showTrajectoryLayer,
    showSpeedLayer,
    showLoiteringLayer,
    onSelectCamera,
    onSelectWaypoint,
  ]);

  return (
    <div className="w-full h-full relative rounded-2xl overflow-hidden border border-slate-800 bg-[#070b14]">
      {/* Leaflet DOM Viewport Container */}
      <div
        ref={mapContainerRef}
        className="w-full h-full min-h-[520px] z-0"
        data-testid="leaflet-map-container"
      />

      {/* Floating Tactical Overlay HUD */}
      <div className="absolute top-3 left-3 z-10 flex flex-wrap items-center gap-2 pointer-events-none">
        <div className="bg-[#070b14]/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 shadow-xl pointer-events-auto flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-blue-400 font-bold">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-sm shadow-blue-400" />
            {cameras.length} CCTV Nodes
          </span>
          {journey && (
            <>
              <span className="text-slate-600">•</span>
              <span className="flex items-center gap-1.5 text-amber-400 font-bold">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
                {journey.waypoints.length} Sightings
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-emerald-400 font-bold">
                {journey.total_distance_km} KM Trajectory
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
