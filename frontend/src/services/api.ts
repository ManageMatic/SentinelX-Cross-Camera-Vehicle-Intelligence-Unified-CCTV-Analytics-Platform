import { SystemHealthResponse } from '../types';

const API_BASE_URL = '';

export async function fetchSystemHealth(): Promise<SystemHealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}
