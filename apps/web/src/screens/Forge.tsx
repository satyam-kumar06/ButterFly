import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { ScreenStub } from '../components/ScreenStub';
import { useEventReplay } from '../hooks/useEventReplay';
import { deriveForge } from '../lib/forgeState';

export default function Forge() {
  const { events, status, restart } = useEventReplay();
  const f = useMemo(() => deriveForge(events), [events]);

  const passed = f.tests.filter((t) => t.passed).length;
  const running = f.forks.filter((k) => k.total === 0 || k.done < k.total).length;
  const barColor = (optionId: string | null) =>
    optionId === 'A' ? 'bg-option-a' : optionId === 'B' ? 'bg-option-b' : 'bg-white/50';

  return (
    <>
      <ScreenStub title="Forge" />
      <section className="mx-auto max-w-5xl px-8 pb-16">
        <p className="font-mono text-sm text-flip">MOCK replay · {status} · {events.length} events</p>
        <p className="mt-2 font-mono text-sm" aria-live="polite">
          {f.statusText} · {passed}/{f.tests.length} tests passing · {running} forks running
        </p>
        <button type="button" onClick={restart} className="glass mt-3 px-4 py-2">Replay</button>

        <div className="mt-8 grid gap-6 md:grid-cols-2">
          <div className="glass p-4">
            <h2 className="font-display text-xl font-semibold">Model code</h2>
            {Object.keys(f.code).length === 0 ? (
              <p className="mt-3 text-sm text-muted">No code yet.</p>
            ) : (
              Object.entries(f.code).map(([file, text]) => (
                <div key={file} className="mt-3">
                  <p className="font-mono text-xs text-muted">{file}</p>
                  <pre className="mt-1 max-h-72 overflow-auto whitespace-pre-wrap rounded-control bg-black/40 p-3 font-mono text-xs">{text}</pre>
                </div>
              ))
            )}
          </div>

          <div className="glass p-4">
            <h2 className="font-display text-xl font-semibold">Tests</h2>
            {f.tests.length === 0 ? (
              <p className="mt-3 text-sm text-muted">No test results yet.</p>
            ) : (
              <ul className="mt-3 space-y-2">
                {f.tests.map((t) => (
                  <li key={t.key} className={t.passed ? 'text-good' : 'text-bad'}>
                    <span aria-hidden="true">{t.passed ? '✓' : '✗'}</span>{' '}
                    <span className="font-mono text-sm">{t.name}</span>{' '}
                    <span className="text-xs text-muted">(attempt {t.attempt})</span>
                    {!t.passed && (
                      <p className="ml-5 text-xs">
                        {t.message}
                        {f.tests.some((x) => x.attempt > t.attempt) && ' · Ultra is fixing this'}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="glass mt-6 p-4">
          <h2 className="font-display text-xl font-semibold">Sandbox forks</h2>
          {f.forks.length === 0 ? (
            <p className="mt-3 text-sm text-muted">No forks yet.</p>
          ) : (
            <ul className="mt-3 grid gap-3 md:grid-cols-2">
              {f.forks.map((k) => (
                <li key={k.id}>
                  <p className="font-mono text-xs">
                    {k.id} · {k.purpose}
                    {k.optionId ? ` · option ${k.optionId}` : ''} · {k.done}/{k.total}
                  </p>
                  <div className="mt-1 h-2 rounded-full bg-white/10">
                    <div
                      className={`h-2 rounded-full ${barColor(k.optionId)}`}
                      style={{ width: `${k.total ? Math.min(100, (k.done / k.total) * 100) : 0}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="glass mt-6 p-4">
          <h2 className="font-display text-xl font-semibold">Engine Room</h2>
          <p className="mt-2 font-mono text-sm text-muted">
            {Object.keys(f.llm).length === 0
              ? 'No model calls yet.'
              : Object.entries(f.llm).map(([tier, v]) => `${tier}: ${v.calls} calls, ${v.tokens} tokens`).join(' · ')}
          </p>
        </div>

        {f.resultsReady && (
          <Link to="../multiverse" relative="path" className="glass mt-6 inline-block px-5 py-3">
            Results ready: open the Multiverse{f.flipReady ? ' (flip points ready too)' : ''}
          </Link>
        )}
      </section>
    </>
  );
}