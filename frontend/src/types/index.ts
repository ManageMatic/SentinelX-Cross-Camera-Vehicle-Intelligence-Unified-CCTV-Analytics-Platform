export type NavigationTab =
  | 'dashboard'
  | 'cameras'
  | 'live'
  | 'search'
  | 'investigation'
  | 'watchlist'
  | 'alerts'
  | 'gis'
  | 'evidence'
  | 'audit'
  | 'health';

export interface SystemHealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export interface SystemStats {
  totalCameras: number;
  onlineCameras: number;
  offlineCameras: number;
  activeAlerts: number;
  detectionsToday: number;
  recentSearches: number;
}
