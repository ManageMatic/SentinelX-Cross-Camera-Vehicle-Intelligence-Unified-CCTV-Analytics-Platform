import { SystemHealthResponse } from '../types';

const API_BASE_URL = '';

interface APIResponseWrapper<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
  request_id?: string;
}

export async function fetchSystemHealth(): Promise<SystemHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  const envelope: APIResponseWrapper<SystemHealthResponse> = await response.json();
  return envelope.data || (envelope as unknown as SystemHealthResponse);
}
