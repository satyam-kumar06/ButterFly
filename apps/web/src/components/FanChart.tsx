import type { Results } from '../lib/results';
import { formatInr } from '../lib/format';

const W = 800;
const H = 360;
const PAD = { l: 72, r: 16, t: 16, b: 36 };
const SAMPLE_LINES = 40;

type Props = {
  results: Results;
  selected: number;
  highlightIndex: number | null;
  light?: boolean;
  showMarker?: boolean;
};

export function FanChart({ results, selected, highlightIndex, light = false, showMarker = true }: Props) {
  const n = results.x_points.length;
  const colorA = light ? '#0e8a8f' : '#2de2e6';
  const colorB = light ? '#6b2fd1' : '#a970ff';
  const text = light ? '#555555' : '#9a9ab0';
  const gridColor = light ? '#000000' : '#ffffff';
  const hiColor = light ? '#111111' : '#ffffff';
  const markerColor = light ? '#c77700' : '#ffb547';

  const opts = [
    { id: 'A' as const, data: results.options.A, color: colorA, dash: undefined },
    { id: 'B' as const, data: results.options.B, color: colorB, dash: '8 5' },
  ];

  const lows = opts.map((o) => Math.min(...o.data.percentiles.p5));
  const highs = opts.map((o) => Math.max(...o.data.percentiles.p95));
  const minV = Math.min(...lows);
  const maxV = Math.max(...highs);
  const pad = (maxV - minV) * 0.05 || 1;
  const lo = minV - pad;
  const hi = maxV + pad;

  const x = (i: number) => PAD.l + (n > 1 ? (i * (W - PAD.l - PAD.r)) / (n - 1) : 0);
  const y = (v: number) => PAD.t + (1 - (v - lo) / (hi - lo)) * (H - PAD.t - PAD.b);

  const line = (values: number[]) =>
    values.map((v, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');

  const band = (low: number[], high: number[]) => {
    const forward = high.map((v, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)}`);
    const back = low.map((v, i) => `L${x(i).toFixed(1)},${y(v).toFixed(1)}`).reverse();
    return `${forward.join(' ')} ${back.join(' ')} Z`;
  };

  const yTicks = Array.from({ length: 5 }, (_, k) => lo + ((hi - lo) * k) / 4);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Fan chart: median and middle 80 percent range of money over time for both options"
      className="w-full"
    >
      <defs>
        <clipPath id="plot">
          <rect x={PAD.l} y={PAD.t} width={W - PAD.l - PAD.r} height={H - PAD.t - PAD.b} />
        </clipPath>
      </defs>

      {yTicks.map((t) => (
        <g key={t}>
          <line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} stroke={gridColor} strokeOpacity="0.1" />
          <text x={PAD.l - 8} y={y(t) + 4} textAnchor="end" fontSize="11" fill={text}>
            {formatInr(t)}
          </text>
        </g>
      ))}

      {results.x_points.map((label, i) =>
        i % 4 === 0 ? (
          <text key={label} x={x(i)} y={H - 10} textAnchor="middle" fontSize="11" fill={text}>
            {label}
          </text>
        ) : null,
      )}

      <g clipPath="url(#plot)">
        {opts.map((o) => (
          <g key={o.id}>
            {o.data.sampled_paths.slice(0, SAMPLE_LINES).map((p, k) => (
              <path key={k} d={line(p)} fill="none" stroke={o.color} strokeOpacity="0.12" />
            ))}
            <path d={band(o.data.percentiles.p10, o.data.percentiles.p90)} fill={o.color} fillOpacity="0.15" />
            <path d={line(o.data.percentiles.p50)} fill="none" stroke={o.color} strokeWidth="3" strokeDasharray={o.dash} />
          </g>
        ))}

        {highlightIndex !== null &&
          opts.map((o) => {
            const p = o.data.sampled_paths[highlightIndex];
            return p ? (
              <path key={`h-${o.id}`} d={line(p)} fill="none" stroke={hiColor} strokeWidth="2" strokeDasharray={o.dash} />
            ) : null;
          })}
      </g>

      {showMarker && (
        <line x1={x(selected)} x2={x(selected)} y1={PAD.t} y2={H - PAD.b} stroke={markerColor} strokeWidth="1.5" />
      )}
    </svg>
  );
}