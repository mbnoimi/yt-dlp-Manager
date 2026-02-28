import { writable } from 'svelte/store';
import { api } from '../api/client';

// FIXME: The app doesn't detect backend availability properly when logged in
// Need to implement proper backend monitoring with visual feedback

export interface RunningJob {
  id: number;
  name: string;
  user_id: number;
  started_at: string;
  create_symlinks: boolean;
  current_url?: string;
}

export const runningJobs = writable<RunningJob[]>([]);
export const currentJobId = writable<number | null>(null);

let eventSource: EventSource | null = null;

export function startSSE() {
  if (eventSource) {
    eventSource.close();
  }

  eventSource = api.createSSE();

  eventSource.onmessage = (event) => {
    try {
      const jobs = JSON.parse(event.data);
      runningJobs.set(jobs);
    } catch (e) {
      console.error('Failed to parse SSE data:', e);
    }
  };

  eventSource.onerror = () => {
    eventSource?.close();
    setTimeout(() => {
      if (api.getToken()) {
        startSSE();
      }
    }, 5000);
  };
}

export function stopSSE() {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  runningJobs.set([]);
}
