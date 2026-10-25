import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import type { ContractBundle } from './contracts';
import './styles/base.css';

type Results = ContractBundle['results'];
type StreamEvent = ContractBundle['stream_event'];

function App() {
  const [results, setResults] = useState<Results | null>(null);
  const [pack, setPack] = useState('');
  const [eventCount, setEventCount] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function loadPack(name: 'offer_xray' | 'fine_print') {
    setLoading(true); setError('');
    try {
      // Fixtures are checked by Pydantic in CI. Production will validate API responses.
      const fixture = name === 'offer_xray'
        ? await import('../../../mocks/results_offer_xray.json')
        : await import('../../../mocks/results_fine_print.json');
      setResults(fixture.default as unknown as Results);
      const recording = await import('../../../mocks/events_build.jsonl?raw');
      const events: StreamEvent[] = recording.default.trim().split('\n').map(line => JSON.parse(line));
      setEventCount(events.length); setPack(name);
    } catch { setError('Could not load fixtures. Run python -m mocks.make_mocks.'); }
    finally { setLoading(false); }
  }

  return <main>
    <p className="eyebrow">FORK / DEVELOPMENT FOUNDATION</p>
    <h1>One contract.<br />Three builders.</h1>
    <p className="intro">Phase 0 fixture inspector. The production journey and simulations come next.</p>
    <div className="notice">Synthetic data only. No model calls, sandbox execution, or decision advice.</div>
    {import.meta.env.VITE_MOCK !== '1' ? <p>Live mode is not implemented in Phase 0. Set VITE_MOCK=1.</p> : <>
      <div className="actions">
        <button disabled={loading} onClick={() => loadPack('offer_xray')}>Inspect Offer X-ray</button>
        <button disabled={loading} onClick={() => loadPack('fine_print')}>Inspect Fine Print</button>
      </div>
      <section aria-live="polite">
        {error && <p role="alert">{error}</p>}
        {results && <>
          <h2>{pack === 'offer_xray' ? 'Offer X-ray' : 'Fine Print'}</h2>
          <dl>
            <div><dt>Contract</dt><dd>v{results.schema_version}</dd></div>
            <div><dt>Synthetic futures / option</dt><dd>{results.path_count.toLocaleString()}</dd></div>
            <div><dt>Display paths / option</dt><dd>{results.options.A.sampled_paths.length.toLocaleString()}</dd></div>
            <div><dt>Quarterly points</dt><dd>{results.x_points.length}</dd></div>
            <div><dt>Frontier grid</dt><dd>{results.frontier?.x_values.length} × {results.frontier?.y_values.length}</dd></div>
            <div><dt>Offer build replay events</dt><dd>{eventCount}</dd></div>
          </dl>
          <p>{results.story}</p>
        </>}
      </section>
    </>}
    <footer>Contract source: apps/api/contracts.py · Generated types: src/contracts.ts</footer>
  </main>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
