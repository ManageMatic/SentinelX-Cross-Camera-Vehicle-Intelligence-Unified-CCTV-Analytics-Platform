import {
  SystemHealthResponse,
  SystemStatusData,
  SystemStats,
  Camera,
  VehicleEvent,
  AlertItem,
  WatchlistEntry,
  EvidenceRecord,
  AuditRecord,
  VehicleJourney,
  APIResponse,
} from '../types';

const API_BASE_URL = '';

// Helper for unwrapping backend standardized envelope
async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  const envelope: APIResponse<T> = await response.json();
  return envelope.data !== undefined ? envelope.data : (envelope as unknown as T);
}

// 1. System Health & Telemetry
export async function fetchSystemHealth(): Promise<SystemHealthResponse> {
  try {
    return await request<SystemHealthResponse>('/health');
  } catch {
    return {
      status: 'healthy',
      service: 'SentinelX Core Backend (Local Dev)',
      version: '1.0.0',
      environment: 'development',
    };
  }
}

export async function fetchSystemStatus(): Promise<SystemStatusData> {
  try {
    return await request<SystemStatusData>('/api/v1/system/status');
  } catch {
    return {
      status: 'healthy',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      uptime_seconds: 3600,
      components: {
        database: { status: 'healthy', latency_ms: 1.2 },
        storage: { status: 'healthy' },
        cache: { status: 'healthy', latency_ms: 0.8 },
        ai_runtime: { status: 'healthy', latency_ms: 14.5 },
      },
    };
  }
}

// 2. System Dashboard Stats
export async function fetchSystemStats(): Promise<SystemStats> {
  return {
    totalCameras: 12,
    onlineCameras: 11,
    offlineCameras: 1,
    activeAlerts: 3,
    detectionsToday: 18450,
    vehiclesIndexed: 4120,
    avgProcessTimeMs: 18.4,
  };
}

// 3. Demo Cameras
export const DEMO_CAMERAS: Camera[] = [
  {
    id: 'cam-01',
    external_camera_id: 'GJ-AHM-CAM-001',
    name: 'SG Highway Junction North',
    location_name: 'Ahmedabad S.G. Highway (Km 12.4)',
    latitude: 23.0338,
    longitude: 72.5072,
    live_status: 'ONLINE',
    fps: 25,
    resolution: '1920x1080',
    codec: 'H264',
    whep_url: 'http://localhost:8889/cam01/whep',
    hls_url: 'http://localhost:8888/cam01/index.m3u8',
  },
  {
    id: 'cam-02',
    external_camera_id: 'GJ-AHM-CAM-002',
    name: 'Iskcon Crossroad Inbound',
    location_name: 'Iskcon Circle, Ahmedabad',
    latitude: 23.0278,
    longitude: 72.5065,
    live_status: 'ONLINE',
    fps: 25,
    resolution: '1920x1080',
    codec: 'H264',
    whep_url: 'http://localhost:8889/cam02/whep',
    hls_url: 'http://localhost:8888/cam02/index.m3u8',
  },
  {
    id: 'cam-03',
    external_camera_id: 'GJ-AHM-CAM-003',
    name: 'Pakwan Crossroad South',
    location_name: 'Pakwan Junction, Bodakdev',
    latitude: 23.0385,
    longitude: 72.5121,
    live_status: 'ONLINE',
    fps: 25,
    resolution: '1920x1080',
    codec: 'H264',
    whep_url: 'http://localhost:8889/cam03/whep',
    hls_url: 'http://localhost:8888/cam03/index.m3u8',
  },
  {
    id: 'cam-04',
    external_camera_id: 'GJ-GND-CAM-004',
    name: 'CH-0 Circle Gandhinagar',
    location_name: 'CH Road, Sector 1, Gandhinagar',
    latitude: 23.2156,
    longitude: 72.6369,
    live_status: 'ONLINE',
    fps: 24,
    resolution: '1920x1080',
    codec: 'H264',
    whep_url: 'http://localhost:8889/cam04/whep',
    hls_url: 'http://localhost:8888/cam04/index.m3u8',
  },
  {
    id: 'cam-05',
    external_camera_id: 'GJ-GND-CAM-005',
    name: 'Infocity Entry Plaza',
    location_name: 'Infocity Gandhinagar Gate 2',
    latitude: 23.1895,
    longitude: 72.6284,
    live_status: 'ONLINE',
    fps: 25,
    resolution: '1920x1080',
    codec: 'H264',
    whep_url: 'http://localhost:8889/cam05/whep',
    hls_url: 'http://localhost:8888/cam05/index.m3u8',
  },
  {
    id: 'cam-06',
    external_camera_id: 'GJ-SRT-CAM-006',
    name: 'Ring Road Toll Plaza',
    location_name: 'Surat Central Ring Road Exit 4',
    latitude: 21.1702,
    longitude: 72.8311,
    live_status: 'DEGRADED',
    fps: 15,
    resolution: '1280x720',
    codec: 'H264',
    whep_url: 'http://localhost:8889/cam06/whep',
  },
];

// 4. Demo Active Alerts
export const DEMO_ALERTS: AlertItem[] = [
  {
    id: 'alert-01',
    vehicle_event_id: 'evt-901',
    plate_number: 'GJ01AB1234',
    watchlist_name: 'Crime Branch Stolen Vehicles Hotlist',
    category: 'STOLEN',
    priority: 'CRITICAL',
    camera_name: 'SG Highway Junction North',
    camera_id: 'cam-01',
    location: 'Ahmedabad (Km 12.4)',
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    status: 'NEW',
    case_number: 'FIR-2026-AHM-CR-88219',
  },
  {
    id: 'alert-02',
    vehicle_event_id: 'evt-902',
    plate_number: 'GJ05CD5678',
    watchlist_name: 'State Wanted Inter-District Gang',
    category: 'WANTED',
    priority: 'HIGH',
    camera_name: 'CH-0 Circle Gandhinagar',
    camera_id: 'cam-04',
    location: 'Gandhinagar Sector 1',
    timestamp: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
    status: 'NEW',
    case_number: 'FIR-2026-GND-CR-44102',
  },
  {
    id: 'alert-03',
    vehicle_event_id: 'evt-903',
    plate_number: 'GJ27XY9900',
    watchlist_name: 'Suspicious Night Patrol Sightings',
    category: 'SUSPICIOUS',
    priority: 'MEDIUM',
    camera_name: 'Iskcon Crossroad Inbound',
    camera_id: 'cam-02',
    location: 'Iskcon Circle',
    timestamp: new Date(Date.now() - 22 * 60 * 1000).toISOString(),
    status: 'ACKNOWLEDGED',
    case_number: 'INTEL-2026-NOC-0912',
    acknowledged_by: 'Insp. V. Patel',
    acknowledged_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
  },
];

// 5. Demo Vehicle Events
export const DEMO_VEHICLE_EVENTS: VehicleEvent[] = [
  {
    id: 'evt-01',
    camera_id: 'cam-01',
    camera_name: 'SG Highway Junction North',
    event_time: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
    plate_raw: 'GJ 01 AB 1234',
    plate_normalized: 'GJ01AB1234',
    plate_confidence: 0.96,
    vehicle_class: 'car',
    vehicle_confidence: 0.94,
    vehicle_color: 'White',
    vehicle_make: 'Sedan (Swift Dzire)',
    snapshot_path: '/storage/evidence/snapshots/demo_dzire.jpg',
    speed_kmh: 58.4,
    latitude: 23.0338,
    longitude: 72.5072,
    has_embedding: true,
  },
  {
    id: 'evt-02',
    camera_id: 'cam-02',
    camera_name: 'Iskcon Crossroad Inbound',
    event_time: new Date(Date.now() - 9 * 60 * 1000).toISOString(),
    plate_raw: 'GJ 01 AB 1234',
    plate_normalized: 'GJ01AB1234',
    plate_confidence: 0.94,
    vehicle_class: 'car',
    vehicle_confidence: 0.92,
    vehicle_color: 'White',
    vehicle_make: 'Sedan (Swift Dzire)',
    snapshot_path: '/storage/evidence/snapshots/demo_dzire_2.jpg',
    speed_kmh: 62.1,
    latitude: 23.0278,
    longitude: 72.5065,
    has_embedding: true,
  },
  {
    id: 'evt-03',
    camera_id: 'cam-03',
    camera_name: 'Pakwan Crossroad South',
    event_time: new Date(Date.now() - 17 * 60 * 1000).toISOString(),
    plate_raw: 'GJ 01 AB 1234',
    plate_normalized: 'GJ01AB1234',
    plate_confidence: 0.98,
    vehicle_class: 'car',
    vehicle_confidence: 0.96,
    vehicle_color: 'White',
    vehicle_make: 'Sedan (Swift Dzire)',
    snapshot_path: '/storage/evidence/snapshots/demo_dzire_3.jpg',
    speed_kmh: 54.0,
    latitude: 23.0385,
    longitude: 72.5121,
    has_embedding: true,
  },
  {
    id: 'evt-04',
    camera_id: 'cam-04',
    camera_name: 'CH-0 Circle Gandhinagar',
    event_time: new Date(Date.now() - 25 * 60 * 1000).toISOString(),
    plate_raw: 'GJ 05 CD 5678',
    plate_normalized: 'GJ05CD5678',
    plate_confidence: 0.91,
    vehicle_class: 'truck',
    vehicle_confidence: 0.89,
    vehicle_color: 'Red / Yellow',
    vehicle_make: 'Commercial Truck',
    snapshot_path: '/storage/evidence/snapshots/demo_truck.jpg',
    speed_kmh: 44.2,
    latitude: 23.2156,
    longitude: 72.6369,
    has_embedding: true,
  },
];

// 6. Demo Vehicle Journey for GJ01AB1234
export const DEMO_JOURNEY_GJ01AB1234: VehicleJourney = {
  registration: 'GJ01AB1234',
  vehicle_class: 'car',
  total_sightings: 3,
  first_seen: new Date(Date.now() - 17 * 60 * 1000).toISOString(),
  last_seen: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
  total_distance_km: 4.8,
  waypoints: [
    {
      order: 1,
      camera_id: 'cam-03',
      camera_name: 'Pakwan Crossroad South',
      location: 'Bodakdev Junction',
      latitude: 23.0385,
      longitude: 72.5121,
      timestamp: new Date(Date.now() - 17 * 60 * 1000).toISOString(),
      speed_kmh: 54.0,
      travel_duration_minutes: 0,
      distance_km: 0,
      snapshot_url: '/storage/evidence/snapshots/demo_dzire_3.jpg',
      is_plausible: true,
    },
    {
      order: 2,
      camera_id: 'cam-02',
      camera_name: 'Iskcon Crossroad Inbound',
      location: 'Iskcon Circle',
      latitude: 23.0278,
      longitude: 72.5065,
      timestamp: new Date(Date.now() - 9 * 60 * 1000).toISOString(),
      speed_kmh: 62.1,
      travel_duration_minutes: 8,
      distance_km: 2.2,
      snapshot_url: '/storage/evidence/snapshots/demo_dzire_2.jpg',
      is_plausible: true,
    },
    {
      order: 3,
      camera_id: 'cam-01',
      camera_name: 'SG Highway Junction North',
      location: 'Ahmedabad (Km 12.4)',
      latitude: 23.0338,
      longitude: 72.5072,
      timestamp: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
      speed_kmh: 58.4,
      travel_duration_minutes: 6,
      distance_km: 2.6,
      snapshot_url: '/storage/evidence/snapshots/demo_dzire.jpg',
      is_plausible: true,
    },
  ],
};

// 7. Demo Watchlists
export const DEMO_WATCHLISTS: WatchlistEntry[] = [
  {
    id: 'wl-01',
    watchlist_id: 'wl-cat-01',
    watchlist_name: 'Crime Branch Stolen Vehicles Hotlist',
    registration_raw: 'GJ 01 AB 1234',
    registration_normalized: 'GJ01AB1234',
    category: 'STOLEN',
    priority: 'CRITICAL',
    case_number: 'FIR-2026-AHM-CR-88219',
    reason: 'Reported stolen from Navrangpura parking plaza on 02-Sep-2026.',
    is_active: true,
    created_at: '2026-09-02T10:00:00Z',
  },
  {
    id: 'wl-02',
    watchlist_id: 'wl-cat-02',
    registration_raw: 'GJ 05 CD 5678',
    registration_normalized: 'GJ05CD5678',
    watchlist_name: 'State Wanted Inter-District Gang',
    category: 'WANTED',
    priority: 'HIGH',
    case_number: 'FIR-2026-GND-CR-44102',
    reason: 'Wanted in highway freight theft syndicate case.',
    is_active: true,
    created_at: '2026-09-03T14:30:00Z',
  },
  {
    id: 'wl-03',
    watchlist_id: 'wl-cat-03',
    registration_raw: 'GJ 27 XY 9900',
    registration_normalized: 'GJ27XY9900',
    watchlist_name: 'Suspicious Night Patrol Sightings',
    category: 'SUSPICIOUS',
    priority: 'MEDIUM',
    case_number: 'INTEL-2026-NOC-0912',
    reason: 'Multiple night-time perimeter violations near restricted infrastructure.',
    is_active: true,
    created_at: '2026-09-05T08:15:00Z',
  },
];

// 8. Demo Evidence Records with SHA-256
export const DEMO_EVIDENCE: EvidenceRecord[] = [
  {
    id: 'evi-01',
    file_name: 'EVT_GJ01AB1234_CAM01_20260910_072011.jpg',
    file_type: 'image/jpeg',
    file_size_bytes: 348210,
    sha256_hash: '8f7a93b4c12d5e6f8a90123456789abcdef0123456789abcdef0123456789abc',
    camera_id: 'cam-01',
    camera_name: 'SG Highway Junction North',
    captured_at: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
    is_verified: true,
    chain_of_custody_count: 4,
  },
  {
    id: 'evi-02',
    file_name: 'EVT_GJ01AB1234_CAM02_20260910_071422.jpg',
    file_type: 'image/jpeg',
    file_size_bytes: 382450,
    sha256_hash: '3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f',
    camera_id: 'cam-02',
    camera_name: 'Iskcon Crossroad Inbound',
    captured_at: new Date(Date.now() - 9 * 60 * 1000).toISOString(),
    is_verified: true,
    chain_of_custody_count: 3,
  },
];

// 9. Demo Immutable Audit Logs
export const DEMO_AUDIT_LOGS: AuditRecord[] = [
  {
    id: 'aud-01',
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
    username: 'insp_patel',
    role: 'STATE_ADMIN',
    action: 'WATCHLIST_MATCH_DISPATCH',
    resource_type: 'Alert',
    resource_id: 'alert-01',
    ip_address: '10.20.1.45',
    status: 'SUCCESS',
  },
  {
    id: 'aud-02',
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    username: 'insp_patel',
    role: 'STATE_ADMIN',
    action: 'VEHICLE_CORRELATION_SEARCH',
    resource_type: 'VehicleEvent',
    resource_id: 'GJ01AB1234',
    ip_address: '10.20.1.45',
    status: 'SUCCESS',
  },
  {
    id: 'aud-03',
    timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    username: 'ctrl_operator_02',
    role: 'OPERATOR',
    action: 'ALERT_ACKNOWLEDGE',
    resource_type: 'Alert',
    resource_id: 'alert-03',
    ip_address: '10.20.1.62',
    status: 'SUCCESS',
  },
];
