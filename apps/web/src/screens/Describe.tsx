import { useState } from 'react';
import { ScreenStub } from '../components/ScreenStub';
import { TermCard } from '../components/TermCard';
import { loadMockTerms, withDemoLowConfidence } from '../api/mockTerms';
import type { TermView } from '../lib/terms';

export default function Describe() {
  const [dilemma, setDilemma] = useState('');
  const [terms, setTerms] = useState<TermView[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function loadDemo() {
    setLoading(true);
    setError('');
    try {
      const loaded = await loadMockTerms('offer_xray');
      const demo = new URLSearchParams(window.location.search).get('demo') === 'lowconf';
      setTerms(demo ? withDemoLowConfidence(loaded) : loaded);
    } catch {
      setError('Could not load the demo terms.');
    } finally {
      setLoading(false);
    }
  }

  function changeValue(index: number, raw: string) {
    setTerms((prev) =>
      prev.map((t, i) => {
        if (i !== index) return t;
        const n = Number(raw);
        const keepNumber = typeof t.value === 'number' && raw.trim() !== '' && !Number.isNaN(n);
        return { ...t, value: keepNumber ? n : raw, confirmed: false };
      }),
    );
  }

  function confirm(index: number) {
    setTerms((prev) => prev.map((t, i) => (i === index ? { ...t, confirmed: true } : t)));
  }

  const groups = [
    { id: 'A' as const, title: 'Option A', color: 'text-option-a' },
    { id: 'B' as const, title: 'Option B', color: 'text-option-b' },
  ];

  return (
    <>
      <ScreenStub title="Describe" />
      <section className="mx-auto max-w-5xl px-8 pb-16">
        <p className="mb-4 font-mono text-sm text-flip">MOCK DATA · edits are not saved anywhere yet</p>

        <label htmlFor="dilemma" className="text-sm text-muted">Describe your decision</label>
        <textarea
          id="dilemma"
          value={dilemma}
          onChange={(e) => setDilemma(e.target.value)}
          rows={3}
          placeholder="Offer A at 18 LPA or Offer B at 14 LPA?"
          className="glass mt-2 w-full p-4"
        />

        <button type="button" onClick={loadDemo} disabled={loading} className="glass mt-4 px-5 py-3">
          {loading ? 'Loading…' : 'Load demo offers'}
        </button>
        {error && <p role="alert" className="mt-4 text-bad">{error}</p>}

        {groups.map((g) => {
          const items = terms.map((t, i) => ({ t, i })).filter(({ t }) => t.option_id === g.id);
          if (items.length === 0) return null;
          return (
            <div key={g.id} className="mt-10">
              <h2 className={`font-display text-2xl font-semibold ${g.color}`}>{g.title}</h2>
              <ul className="mt-4 grid gap-4 md:grid-cols-2">
                {items.map(({ t, i }) => (
                  <TermCard
                    key={`${t.option_id}-${t.field}`}
                    term={t}
                    onChange={(v) => changeValue(i, v)}
                    onConfirm={() => confirm(i)}
                  />
                ))}
              </ul>
            </div>
          );
        })}
      </section>
    </>
  );
}