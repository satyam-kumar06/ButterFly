import { useEffect, useState } from 'react';
import { ScreenStub } from '../components/ScreenStub';
import { TornadoChart } from '../components/TornadoChart';
import { FrontierMap } from '../components/FrontierMap';
import { loadMockResults } from '../api/mockResults';
import type { PackName } from '../api/mockTerms';
import type { Results } from '../lib/results';
import { formatNumber, formatPercent } from '../lib/format';
import { fieldLabel } from '../lib/terms';

export default function Flips() {
  const [pack, setPack] = useState<PackName>('offer_xray');
  const [results, setResults] = useState<Results | null>(null);
  const [error, setError] = useState('');
  const [xi, setXi] = useState(0);
  const [yi, setYi] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setResults(null);
    setError('');
    loadMockResults(pack)
      .then((r) => {
        if (cancelled) return;
        setResults(r);
        setXi(Math.floor((r.frontier?.x_values.length ?? 1) / 2));
        setYi(Math.floor((r.frontier?.y_values.length ?? 1) / 2));
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the mock results.');
      });
    return () => {
      cancelled = true;
    };
  }, [pack]);

  const frontier = results?.frontier ?? null;
  const pinValue = frontier ? (frontier.grid[yi]?.[xi] ?? 0) : 0;

  return (
    <>
      <ScreenStub title="Flip points" />
      <section className="mx-auto max-w-5xl px-8 pb-16">
        <div className="flex flex-wrap items-center gap-3">
          <p className="font-mono text-sm text-flip">
            {results?.data_kind === 'mock' ? 'MOCK DATA · synthetic, not a prediction' : ''}
          </p>
          <div className="ml-auto flex gap-2">
            {(['offer_xray', 'fine_print'] as PackName[]).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPack(p)}
                aria-pressed={pack === p}
                className={`glass px-4 py-2 ${pack === p ? 'outline outline-2 outline-white' : ''}`}
              >
                {p === 'offer_xray' ? 'Offer X-ray' : 'Fine Print'}
              </button>
            ))}
          </div>
        </div>

        {error && <p role="alert" className="mt-4 text-bad">{error}</p>}
        {!results && !error && <p className="mt-6 text-muted">Loading results…</p>}

        {results && (
          <>
            <h2 className="mt-8 font-display text-2xl font-semibold">What flips the answer</h2>
            {results.flip_points.length === 0 ? (
              <p className="mt-3 text-muted">
                No flip point was reported for these results. Either the analysis is still running or no tested
                range changed the winner.
              </p>
            ) : (
              <ul className="mt-4 grid gap-4 md:grid-cols-2">
                {results.flip_points.map((fp) => (
                  <li key={fp.variable} className="glass p-4 outline outline-2 outline-flip/60">
                    <p className="font-display text-lg font-semibold">
                      If {fieldLabel(fp.variable)} is {fp.direction} {formatNumber(fp.threshold)} {fp.unit},{' '}
                      {results.options[fp.winner_after].label} wins.
                    </p>
                    <p className="mt-1 text-xs text-muted">
                      Found between {formatNumber(fp.bracket.low)} and {formatNumber(fp.bracket.high)} {fp.unit} ·
                      swing {formatPercent(fp.swing)}
                    </p>
                  </li>
                ))}
              </ul>
            )}

            <h2 className="mt-10 font-display text-2xl font-semibold">Which assumptions matter most</h2>
            {results.sensitivities.length === 0 ? (
              <p className="mt-3 text-muted">The sensitivity sweep has not run yet.</p>
            ) : (
              <div className="glass mt-4 p-4">
                <TornadoChart sensitivities={results.sensitivities} />
              </div>
            )}

            <h2 className="mt-10 font-display text-2xl font-semibold">The flip frontier</h2>
            {!frontier ? (
              <p className="mt-3 text-muted">
                No frontier is available yet. It needs the analysis to finish, and at least two suitable variables.
              </p>
            ) : (
              <div className="glass mt-4 p-4">
                <FrontierMap frontier={frontier} xi={xi} yi={yi} />
                <p className="mt-2 text-xs text-muted">
                  Cyan: Option A wins more often. Violet: Option B does. The amber line is where it crosses 50%.
                </p>

                <label htmlFor="px" className="mt-4 block text-sm text-muted">
                  {frontier.x_var}: <strong className="text-ink">{formatNumber(frontier.x_values[xi] ?? 0)}</strong>
                </label>
                <input id="px" type="range" min={0} max={frontier.x_values.length - 1} value={xi}
                  onChange={(e) => setXi(Number(e.target.value))} className="w-full" />

                <label htmlFor="py" className="mt-3 block text-sm text-muted">
                  {frontier.y_var}: <strong className="text-ink">{formatNumber(frontier.y_values[yi] ?? 0)}</strong>
                </label>
                <input id="py" type="range" min={0} max={frontier.y_values.length - 1} value={yi}
                  onChange={(e) => setYi(Number(e.target.value))} className="w-full" />

                <p className="mt-3 font-display text-xl" aria-live="polite">
                  At this pin, {results.options.A.label} wins in {formatPercent(pinValue)} of futures.
                </p>
              </div>
            )}
          </>
        )}
      </section>
    </>
  );
}