import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { FanChart } from '../components/FanChart';
import { loadMockResults } from '../api/mockResults';
import { loadMockBranches } from '../api/mockBranches';
import type { PackName } from '../api/mockTerms';
import type { Results } from '../lib/results';
import type { Branch } from '../contracts';
import { variableSummary } from '../lib/branches';
import { formatInr, formatNumber, formatPercent } from '../lib/format';
import { fieldLabel } from '../lib/terms';

// Wording from the project specification. Live mode will get this from the report route.
const DISCLAIMER =
  'Fork is a decision aid, not financial, tax or insurance advice. Check important decisions with a qualified professional.';
const SOURCE_LABEL = { user: 'You', default: 'Default', data: 'Data' } as const;

export default function Report() {
  const { id = 'demo_offer_xray' } = useParams();
  const [pack, setPack] = useState<PackName>('offer_xray');
  const [results, setResults] = useState<Results | null>(null);
  const [branch, setBranch] = useState<Branch | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setResults(null);
    setBranch(null);
    setError('');
    Promise.all([loadMockResults(pack), loadMockBranches(pack)])
      .then(([r, list]) => {
        if (cancelled) return;
        setResults(r);
        setBranch(list.find((b) => b.id === r.branch_id) ?? list[0] ?? null);
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the mock report data.');
      });
    return () => {
      cancelled = true;
    };
  }, [pack]);

  const last = results ? results.x_points.length - 1 : 0;
  const medianOf = (opt: 'A' | 'B') => results?.options[opt].percentiles.p50[last] ?? 0;

  return (
    <main className="mx-auto min-h-screen max-w-4xl bg-white p-8 text-neutral-900 print:p-0">
      <nav className="mb-6 flex flex-wrap items-center gap-3 print:hidden">
        <Link to={`/s/${id}/multiverse`} className="underline">Back to results</Link>
        <div className="ml-auto flex gap-2">
          {(['offer_xray', 'fine_print'] as PackName[]).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPack(p)}
              aria-pressed={pack === p}
              className={`rounded-lg border border-neutral-400 px-3 py-1 ${pack === p ? 'bg-neutral-900 text-white' : ''}`}
            >
              {p === 'offer_xray' ? 'Offer X-ray' : 'Fine Print'}
            </button>
          ))}
          <button type="button" onClick={() => window.print()} className="rounded-lg bg-neutral-900 px-3 py-1 text-white">
            Print / Save as PDF
          </button>
        </div>
      </nav>

      {error && <p role="alert" className="text-red-700">{error}</p>}
      {!results && !error && <p>Loading report…</p>}

      {results && (
        <article>
          {results.data_kind === 'mock' && (
            <p className="mb-2 font-mono text-sm text-amber-700">
              MOCK DATA · synthetic, not a prediction or advice
            </p>
          )}
          <h1 className="font-display text-4xl font-semibold">{branch?.spec.title ?? 'Fork report'}</h1>
          <p className="mt-1 text-sm text-neutral-600">
            Scenario: {branch?.label ?? results.branch_id} · {results.horizon_years} years ·{' '}
            {results.path_count.toLocaleString()} futures per option
          </p>

          <p className="mt-6 font-display text-2xl font-semibold">
            {results.options.A.label} wins in {formatPercent(results.p_win.A)} of futures;{' '}
            {results.options.B.label} in {formatPercent(results.p_win.B)}
            {results.p_win.tie ? `; tie ${formatPercent(results.p_win.tie)}` : ''}.
          </p>
          <p className="mt-1 text-sm">
            Compared on <strong>{fieldLabel(results.primary_metric)}</strong> (
            {results.objective === 'maximize' ? 'higher is better' : 'lower is better'}). Final median:{' '}
            {results.options.A.label} {formatInr(medianOf('A'))} · {results.options.B.label} {formatInr(medianOf('B'))}.
          </p>
          <p className="mt-3">{results.story}</p>

          <div className="mt-6">
            <FanChart results={results} selected={last} highlightIndex={null} light showMarker={false} />
            <p className="text-xs text-neutral-600">
              Solid line: Option A. Dashed line: Option B. Lines show the median; shaded bands show the middle 80% of
              futures.
            </p>
          </div>

          <h2 className="mt-8 font-display text-2xl font-semibold">What flips the answer</h2>
          {results.flip_points.length === 0 ? (
            <p className="mt-2 text-sm">No flip point was reported.</p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {results.flip_points.map((fp) => (
                <li key={fp.variable}>
                  If {fieldLabel(fp.variable)} is {fp.direction} {formatNumber(fp.threshold)} {fp.unit},{' '}
                  {results.options[fp.winner_after].label} wins.
                </li>
              ))}
            </ul>
          )}

          <h2 className="mt-8 font-display text-2xl font-semibold">Assumptions and where they came from</h2>
          <table className="mt-2 w-full text-left text-sm">
            <thead>
              <tr className="border-b border-neutral-400">
                <th className="py-1">Assumption</th>
                <th>Value</th>
                <th>Unit</th>
                <th>Source</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              {results.assumptions.map((a) => (
                <tr key={a.name} className="border-b border-neutral-200">
                  <td className="py-1">{fieldLabel(a.name)}</td>
                  <td className="font-mono">{variableSummary(a)}</td>
                  <td>{a.unit}</td>
                  <td>{SOURCE_LABEL[a.source]}</td>
                  <td>{a.source_ref}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2 className="mt-8 font-display text-2xl font-semibold">Rule sources</h2>
          <p className="mt-2 text-sm">
            The mock data includes no rule sources. Live reports list each tax, gratuity or policy rule with its year
            and official link.
          </p>

          <p className="mt-8 border-t border-neutral-300 pt-3 text-xs">{DISCLAIMER}</p>
        </article>
      )}
    </main>
  );
}