import type { Results } from '../lib/results';
import { fieldLabel } from '../lib/terms';
import { formatNumber, formatPercent } from '../lib/format';

export function TornadoChart({ sensitivities }: { sensitivities: Results['sensitivities'] }) {
  const rows = Array.from(sensitivities).sort((a, b) => b.swing - a.swing);

  return (
    <ul className="mt-4 space-y-5">
      {rows.map((s) => {
        const wins = s.points.map((p) => p.p_win_A);
        const lo = Math.min(...wins);
        const hi = Math.max(...wins);
        const first = s.points[0];
        const last = s.points[s.points.length - 1];
        return (
          <li key={s.variable}>
            <p className="text-sm">
              {fieldLabel(s.variable)}{' '}
              <span className="text-muted">
                ({first ? formatNumber(first.value) : '?'} to {last ? formatNumber(last.value) : '?'} {s.unit})
              </span>
            </p>
            <div
              className="relative mt-1 h-4 rounded-full bg-white/10"
              role="img"
              aria-label={`P(A wins) ranges from ${formatPercent(lo)} to ${formatPercent(hi)}`}
            >
              <div
                className="absolute top-0 h-4 rounded-full bg-flip/70"
                style={{ left: `${lo * 100}%`, width: `${Math.max((hi - lo) * 100, 1)}%` }}
              />
              <div className="absolute top-0 h-4 w-px bg-white" style={{ left: '50%' }} />
            </div>
            <p className="mt-1 text-xs text-muted">
              Option A wins from {formatPercent(lo)} to {formatPercent(hi)} · swing {formatPercent(s.swing)} · white line
              = 50%
            </p>
          </li>
        );
      })}
    </ul>
  );
}