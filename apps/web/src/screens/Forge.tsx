import { ScreenStub } from '../components/ScreenStub';
import { useEventReplay } from '../hooks/useEventReplay';

export default function Forge() {
  const { events, status, restart } = useEventReplay();
  return (
    <>
      <ScreenStub title="Forge" />
      <section className="mx-auto max-w-3xl px-8 pb-16">
        <p className="mb-4 font-mono text-sm text-flip">
          MOCK replay · {status} · {events.length} events
        </p>
        <button onClick={restart} className="glass mb-4 px-4 py-2">Replay</button>
        <ol className="space-y-1 font-mono text-sm">
          {events.map((e) => (
            <li key={e.id}>
              <span className="text-muted">{e.elapsed_ms} ms</span> {e.event}
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}