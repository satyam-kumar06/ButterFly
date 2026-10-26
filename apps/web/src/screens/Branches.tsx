import { useEffect, useMemo, useState } from 'react';
import { ScreenStub } from '../components/ScreenStub';
import { loadMockBranches } from '../api/mockBranches';
import type { PackName } from '../api/mockTerms';
import type { Branch } from '../contracts';
import { orderBranches, variableSummary } from '../lib/branches';
import { fieldLabel } from '../lib/terms';

export default function Branches() {
  const [pack, setPack] = useState<PackName>('offer_xray');
  const [branches, setBranches] = useState<Branch[]>([]);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const [compareId, setCompareId] = useState('');

  useEffect(() => {
    let cancelled = false;
    setBranches([]);
    setError('');
    setCompareId('');
    loadMockBranches(pack)
      .then((list) => {
        if (cancelled) return;
        setBranches(list);
        setSelectedId(list[0]?.id ?? '');
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the mock branches.');
      });
    return () => {
      cancelled = true;
    };
  }, [pack]);

  const ordered = useMemo(() => orderBranches(branches), [branches]);
  const selected = branches.find((b) => b.id === selectedId);
  const other = branches.find((b) => b.id === compareId);

  // Variables whose value differs between the two selected branches.
  const differences = useMemo(() => {
    if (!selected || !other) return [];
    const a = new Map(selected.spec.variables.map((v) => [v.name, variableSummary(v)]));
    const b = new Map(other.spec.variables.map((v) => [v.name, variableSummary(v)]));
    const names = Array.from(new Set([...a.keys(), ...b.keys()]));
    return names
      .map((name) => ({ name, left: a.get(name) ?? '(not set)', right: b.get(name) ?? '(not set)' }))
      .filter((row) => row.left !== row.right);
  }, [selected, other]);

  return (
    <>
      <ScreenStub title="Branches" />
      <section className="mx-auto max-w-5xl px-8 pb-16">
        <div className="flex flex-wrap items-center gap-3">
          <p className="font-mono text-sm text-flip">MOCK DATA · one branch per pack so far</p>
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

        <div className="mt-6 grid gap-6 md:grid-cols-[minmax(0,320px)_1fr]">
          <ul className="glass space-y-1 p-3" aria-label="Scenario tree">
            {ordered.map(({ branch, depth }) => (
              <li key={branch.id} style={{ paddingLeft: depth * 20 }}>
                <button
                  type="button"
                  onClick={() => setSelectedId(branch.id)}
                  aria-current={branch.id === selectedId}
                  className={`w-full rounded-control px-3 py-2 text-left ${
                    branch.id === selectedId ? 'bg-white/15' : 'hover:bg-white/10'
                  }`}
                >
                  <span className="block font-display">{branch.label}</span>
                  <span className="block text-xs text-muted">
                    {branch.change_type} · {branch.status}
                    {branch.model_status === 'fallback' ? ' · fallback model' : ''}
                  </span>
                </button>
              </li>
            ))}
          </ul>

          {selected && (
            <div className="glass p-5">
              <h2 className="font-display text-2xl font-semibold">{selected.label}</h2>
              <p className="mt-1 text-sm text-muted">{selected.spec.title}</p>
              <p className="mt-3 font-mono text-sm">
                {selected.change_type} · status {selected.status}
                {selected.model_status ? ` · model ${selected.model_status}` : ''}
              </p>
              {selected.model_status === 'fallback' && (
                <p className="mt-2 text-sm text-flip">
                  This branch used the pack's built-in template model, not an AI-written one.
                </p>
              )}
              {selected.change_summary && <p className="mt-3">{selected.change_summary}</p>}

              <h3 className="mt-5 font-display text-lg font-semibold">Changes from its parent</h3>
              {!selected.diff || selected.diff.length === 0 ? (
                <p className="mt-2 text-sm text-muted">None. This is the starting scenario.</p>
              ) : (
                <ul className="mt-2 space-y-1 text-sm">
                  {selected.diff.map((d) => (
                    <li key={d.variable}>
                      {fieldLabel(d.variable)}: {String(d.before)} → {String(d.after)}
                    </li>
                  ))}
                </ul>
              )}

              <h3 className="mt-5 font-display text-lg font-semibold">Compare with another branch</h3>
              {branches.length < 2 ? (
                <p className="mt-2 text-sm text-muted">
                  There is only one branch in the mock data. Comparing needs at least two, which come from
                  what-if questions (not built yet).
                </p>
              ) : (
                <>
                  <label htmlFor="cmp" className="sr-only">Compare with</label>
                  <select
                    id="cmp"
                    value={compareId}
                    onChange={(e) => setCompareId(e.target.value)}
                    className="glass mt-2 px-3 py-2"
                  >
                    <option value="">Choose a branch</option>
                    {branches.filter((b) => b.id !== selectedId).map((b) => (
                      <option key={b.id} value={b.id}>{b.label}</option>
                    ))}
                  </select>
                  {other && (
                    <table className="mt-3 w-full text-left text-sm">
                      <thead>
                        <tr className="text-muted">
                          <th className="py-1">Variable</th>
                          <th>{selected.label}</th>
                          <th>{other.label}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {differences.length === 0 ? (
                          <tr><td colSpan={3} className="py-2 text-muted">No differences in assumptions.</td></tr>
                        ) : (
                          differences.map((row) => (
                            <tr key={row.name}>
                              <td className="py-1">{fieldLabel(row.name)}</td>
                              <td className="font-mono">{row.left}</td>
                              <td className="font-mono">{row.right}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </section>
    </>
  );
}