import { useEffect, useState } from 'react';
import { ScreenStub } from '../components/ScreenStub';
import { FanChart } from '../components/FanChart';
import { loadMockResults } from '../api/mockResults';
import type { PackName } from '../api/mockTerms';
import type { Results } from '../lib/results';
import { formatInr, formatPercent } from '../lib/format';
import { fieldLabel } from '../lib/terms';

const at = (a: number[], i: number) => a[i] ?? 0;

export default function Multiverse() {
  const [pack, setPack] = useState<PackName>('offer_xray');
  const [results, setResults] = useState<Results | null>(null);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(0);
  const [highlight, setHighlight] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setResults(null);
    setError('');
    setHighlight(null);
    loadMockResults(pack)
      .then((r) => {
        if (cancelled) return;
        if (r.options.A.percentiles.p50.length !== r.x_points.length) {
          setError('The results do not match the contract: percentile length differs from x_points.');
          return;
        }
        setResults(r);
        setSelected(r.x_points.length - 1);
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the mock results.');
      });
    return () => {
      cancelled = true;
    };
  }, [pack]);

  function showRandomFuture() {
    if (!results) return;
    setHighlight(Math.floor(Math.random() * results.options.A.sampled_paths.length));
  }

  return (
    <>
      <ScreenStub title="The Multiverse" />
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
            <div className="glass mt-6 p-6">
              <p className="font-display text-3xl font-semibold">
                {results.options.A.label}{' '}
                <span className="text-option-a">wins</span> in {formatPercent(results.p_win.A)} of futures
              </p>
              <p className="mt-2 text-muted">
                {results.options.B.label} wins in {formatPercent(results.p_win.B)}
                {results.p_win.tie ? `, ties in ${formatPercent(results.p_win.tie)}` : ''}.
              </p>
              <p className="mt-2 text-sm">
                Compared on: <strong>{fieldLabel(results.primary_metric)}</strong> (
                {results.objective === 'maximize' ? 'higher is better' : 'lower is better'}) ·{' '}
                {results.path_count.toLocaleString()} futures per option
              </p>
              <p className="mt-3 text-sm text-muted">{results.story}</p>
            </div>

            <div className="glass mt-6 p-4">
              <FanChart results={results} selected={selected} highlightIndex={highlight} />
              <p className="mt-2 text-xs text-muted">
                Solid line: {results.options.A.label} (Option A). Dashed line: {results.options.B.label} (Option B).
                Lines show the median, the shaded band the middle 80% of futures.
              </p>

              <label htmlFor="scrub" className="mt-4 block text-sm text-muted">
                Look at a point in time: <strong className="text-ink">{results.x_points[selected]}</strong>
              </label>
              <input
                id="scrub"
                type="range"
                min={0}
                max={results.x_points.length - 1}
                value={selected}
                onChange={(e) => setSelected(Number(e.target.value))}
                className="mt-1 w-full"
              />

              <div className="mt-3 grid gap-4 md:grid-cols-2">
                {(['A', 'B'] as const).map((id) => {
                  const o = results.options[id];
                  return (
                    <div key={id} className="rounded-control bg-white/5 p-3">
                      <p className={id === 'A' ? 'text-option-a' : 'text-option-b'}>
                        Option {id} · {o.label}
                      </p>
                      <p className="mt-1 font-mono text-sm">
                        low (p10) {formatInr(at(o.percentiles.p10, selected))} · median{' '}
                        {formatInr(at(o.percentiles.p50, selected))} · high (p90){' '}
                        {formatInr(at(o.percentiles.p90, selected))}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="glass mt-6 p-4">
              <button type="button" onClick={showRandomFuture} className="glass px-4 py-2">
                Show a random future
              </button>
              {highlight !== null && (
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {(['A', 'B'] as const).map((id) => {
                    const o = results.options[id];
                    const path = o.sampled_paths[highlight] ?? [];
                    const story = o.path_stories[highlight];
                    return (
                      <div key={id}>
                        <p className={id === 'A' ? 'text-option-a' : 'text-option-b'}>
                          Option {id} · future #{story?.id ?? highlight}
                        </p>
                        <p className="font-mono text-sm">ends with {formatInr(at(path, path.length - 1))}</p>
                        <ul className="mt-1 list-disc pl-5 text-sm text-muted">
                          {(story?.events ?? []).map((ev, k) => (
                            <li key={k}>{ev}</li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <p className="mt-6 text-xs text-muted">
              Fork is a decision aid, not financial, tax or insurance advice. Check important decisions with a
              qualified professional.
            </p>
          </>
        )}
      </section>
    </>
  );
}