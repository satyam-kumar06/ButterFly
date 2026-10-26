import type { StreamEvent } from '../api/mockEvents';

type Data = Record<string, unknown>;
const str = (v: unknown, fallback = '') => (typeof v === 'string' ? v : fallback);
const num = (v: unknown, fallback = 0) => (typeof v === 'number' ? v : fallback);

export type TestRow = { key: string; name: string; passed: boolean; message: string; attempt: number };
export type ForkRow = { id: string; purpose: string; optionId: string | null; done: number; total: number };
export type LlmTally = Record<string, { calls: number; tokens: number }>;

// Turns the list of events received so far into what the Forge screen shows.
export function deriveForge(events: StreamEvent[]) {
  let statusText = 'Waiting for the build to start';
  const code: Record<string, string> = {};
  const tests: TestRow[] = [];
  const forks = new Map<string, ForkRow>();
  const llm: LlmTally = {};
  let resultsReady = false;
  let flipReady = false;

  for (const e of events) {
    const d = e.data as unknown as Data;
    switch (e.event) {
      case 'agent.status':
        statusText = str(d.text, statusText);
        break;
      case 'code.chunk': {
        const file = str(d.file, 'model.py');
        // "reset" means: replace the panel before the first chunk of a retry.
        const previous = d.reset === true ? '' : (code[file] ?? '');
        code[file] = previous + str(d.text);
        break;
      }
      case 'test.result': {
        const attempt = num(d.attempt, 1);
        const name = str(d.name, 'unnamed test');
        tests.push({ key: `${attempt}:${name}:${tests.length}`, name, passed: d.passed === true, message: str(d.message), attempt });
        break;
      }
      case 'sandbox.fork': {
        const id = str(d.fork_id);
        forks.set(id, {
          id,
          purpose: str(d.purpose),
          optionId: typeof d.option_id === 'string' ? d.option_id : null,
          done: 0,
          total: 0,
        });
        break;
      }
      case 'sim.progress': {
        const id = str(d.fork_id);
        const row = forks.get(id) ?? { id, purpose: 'unknown', optionId: null, done: 0, total: 0 };
        forks.set(id, { ...row, done: num(d.done), total: num(d.total) });
        break;
      }
      case 'llm.call': {
        const tier = str(d.tier, 'unknown');
        const entry = llm[tier] ?? { calls: 0, tokens: 0 };
        llm[tier] = { calls: entry.calls + 1, tokens: entry.tokens + num(d.tokens_in) + num(d.tokens_out) };
        break;
      }
      case 'results.ready':
        resultsReady = true;
        break;
      case 'flip.ready':
        flipReady = true;
        break;
      default:
        break;
    }
  }

  return { statusText, code, tests, forks: [...forks.values()], llm, resultsReady, flipReady };
}