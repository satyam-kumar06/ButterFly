import type { ContractBundle } from '../contracts';

export type StreamEvent = ContractBundle['stream_event'];

// Mock mode only. Live mode will use the real event stream (not built yet).
export async function loadBuildRecording(): Promise<StreamEvent[]> {
  if (import.meta.env.VITE_MOCK !== '1') {
    throw new Error('Live mode is not implemented yet. Set VITE_MOCK=1.');
  }
  const recording = await import('../../../../mocks/events_build.jsonl?raw');
  return recording.default
    .trim()
    .split('\n')
    .map((line) => JSON.parse(line) as StreamEvent);
}