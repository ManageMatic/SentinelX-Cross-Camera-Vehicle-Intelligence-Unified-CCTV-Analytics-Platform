export type NavigationTab =
  | 'dashboard'
  | 'live'
  | 'search'
  | 'correlation'
  | 'gis'
  | 'watchlists'
  | 'alerts'
  | 'evidence'
  | 'audit'
  | 'cameras'
  | 'system';

export type AlertPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type AlertStatus = 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED' | 'FALSE_POSITIVE';
export type WatchlistCategory = 'WANTED' | 'STOLEN' | 'SUSPICIOUS' | 'VIP' | 'SPECIAL_INTEREST';
export type CameraStatus = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'CONNECTING';
export type VehicleClass = 'car' | 'motorcycle' | 'bus' | 'truck' | 'auto_rickshaw' | 'unknown';

export interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  request_id?: string;
  process_time_ms?: number;
}

export interface PaginatedResponse<T> {
  success: boolean;
  message: string;
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  request_id?: string;
}

export interface SystemHealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export interface ComponentHealth {
  status: 'healthy' | 'unhealthy' | 'degraded' | 'not_configured';
  details?: Record<string, unknown>;
  latency_ms?: number;
  error?: string;
}

export interface SystemStatusData {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  timestamp: string;
  uptime_seconds: number;
  components: {
    database: ComponentHealth;
    storage: ComponentHealth;
    cache?: ComponentHealth;
    ai_runtime?: ComponentHealth;
  };
}

export interface SystemStats {
  totalCameras: number;
  onlineCameras: number;
  offlineCameras: number;
  activeAlerts: number;
  detectionsToday: number;
  vehiclesIndexed: number;
  avgProcessTimeMs: number;
}

export interface CameraTestResult {
  camera_id: string;
  reachable: boolean;
  first_frame_received: boolean;
  codec: string;
  width: number;
  height: number;
  fps: number;
  latency_ms: number;
  message: string;
}

export interface CameraHealthLive {
  camera_id: string;
  is_online: boolean;
  state: string;
  measured_fps: number;
  latency_ms: number;
  resolution_width: number;
  resolution_height: number;
  codec: string;
  reconnect_count: number;
  decoder_errors: number;
  total_frames_received: number;
  dropped_frames: number;
  last_frame_time?: string;
  last_error?: string;
}

export interface CameraSyncResult {
  catalog_url: string;
  total_discovered: number;
  added_count: number;
  updated_count: number;
  unchanged_count: number;
  errors_count: number;
  synced_at: string;
  duration_ms: number;
}

export interface Camera {
  id: string;
  external_camera_id: string;
  name: string;
  location_name: string;
  latitude: number;
  longitude: number;
  live_status: CameraStatus;
  fps: number;
  resolution: string;
  codec: string;
  rtsp_url?: string;
  whep_url?: string;
  hls_url?: string;
  last_heartbeat?: string;
}

export interface VehicleEvent {
  id: string;
  camera_id: string;
  camera_name?: string;
  event_time: string;
  plate_raw: string;
  plate_normalized: string;
  plate_confidence: number;
  vehicle_class: VehicleClass;
  vehicle_confidence: number;
  vehicle_color?: string;
  vehicle_make?: string;
  snapshot_path: string;
  plate_crop_path?: string;
  speed_kmh?: number;
  latitude?: number;
  longitude?: number;
  has_embedding?: boolean;
}

export interface WatchlistEntry {
  id: string;
  watchlist_id: string;
  watchlist_name?: string;
  registration_raw: string;
  registration_normalized: string;
  category: WatchlistCategory;
  priority: AlertPriority;
  case_number?: string;
  reason?: string;
  is_active: boolean;
  created_at: string;
}

export interface AlertItem {
  id: string;
  vehicle_event_id: string;
  watchlist_entry_id?: string;
  plate_number: string;
  watchlist_name: string;
  category: WatchlistCategory;
  priority: AlertPriority;
  camera_name: string;
  camera_id: string;
  location: string;
  timestamp: string;
  status: AlertStatus;
  snapshot_url?: string;
  case_number?: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
}

export interface EvidenceRecord {
  id: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  camera_id: string;
  camera_name: string;
  captured_at: string;
  is_verified: boolean;
  chain_of_custody_count: number;
}

export interface AuditRecord {
  id: string;
  timestamp: string;
  username: string;
  role: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  ip_address: string;
  status: 'SUCCESS' | 'FAILURE' | 'WARNING';
}

export interface JourneyWaypoint {
  order: number;
  camera_id: string;
  camera_name: string;
  location: string;
  latitude: number;
  longitude: number;
  timestamp: string;
  speed_kmh: number;
  travel_duration_minutes: number;
  distance_km: number;
  snapshot_url: string;
  is_plausible: boolean;
}

export interface VehicleJourney {
  registration: string;
  vehicle_class: VehicleClass;
  total_sightings: number;
  first_seen: string;
  last_seen: string;
  total_distance_km: number;
  waypoints: JourneyWaypoint[];
}
