import { useCallback, useEffect, useState } from 'react';
import { loadBuildRecording, type StreamEvent } from '../api/mockEvents';

type Status = 'loading' | 'playing' | 'done' | 'error';

// Plays the recorded build with its original timing. speed=2 plays twice as fast.
export function useEventReplay(speed = 1) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [status, setStatus] = useState<Status>('loading');
  const [run, setRun] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const timers: number[] = [];
    setEvents([]);
    setStatus('loading');

    loadBuildRecording()
      .then((recording) => {
        if (cancelled) return;
        setStatus('playing');
        recording.forEach((event, i) => {
          const isLast = i === recording.length - 1;
          timers.push(
            window.setTimeout(() => {
              // Skip any event id we already have (the contract says to dedupe).
              setEvents((prev) =>
                prev.some((e) => e.id === event.id) ? prev : [...prev, event],
              );
              if (isLast) setStatus('done');
            }, event.elapsed_ms / speed),
          );
        });
      })
      .catch(() => {
        if (!cancelled) setStatus('error');
      });

    return () => {
      cancelled = true;
      timers.forEach((t) => window.clearTimeout(t));
    };
  }, [run, speed]);

  const restart = useCallback(() => setRun((n) => n + 1), []);
  return { events, status, restart };
}