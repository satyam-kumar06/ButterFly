import type { Results } from '../lib/results';
import { formatNumber } from '../lib/format';

type Frontier = NonNullable<Results['frontier']>;

const CELL = 32;
const PAD_L = 56;
const PAD_B = 44;

// 0 -> violet (Option B), 1 -> cyan (Option A)
function colorFor(p: number): string {
  const t = Math.max(0, Math.min(1, p));
  const mix = (a: number, b: number) => Math.round(a + (b - a) * t);
  return `rgb(${mix(169, 45)}, ${mix(112, 226)}, ${mix(255, 230)})`;
}

export function FrontierMap({ frontier, xi, yi }: { frontier: Frontier; xi: number; yi: number }) {
  const nx = frontier.x_values.length;
  const ny = frontier.y_values.length;
  const width = PAD_L + nx * CELL + 8;
  const height = ny * CELL + PAD_B;
  const value = (j: number, i: number) => frontier.grid[j]?.[i] ?? 0;
  const top = (j: number) => (ny - 1 - j) * CELL; // row 0 is drawn at the bottom
  const left = (i: number) => PAD_L + i * CELL;

  const edges: { x1: number; y1: number; x2: number; y2: number }[] = [];
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const v = value(j, i) >= 0.5;
      if (i + 1 < nx && v !== value(j, i + 1) >= 0.5) {
        edges.push({ x1: left(i + 1), y1: top(j), x2: left(i + 1), y2: top(j) + CELL });
      }
      if (j + 1 < ny && v !== value(j + 1, i) >= 0.5) {
        edges.push({ x1: left(i), y1: top(j), x2: left(i) + CELL, y2: top(j) });
      }
    }
  }

  const firstX = frontier.x_values[0] ?? 0;
  const lastX = frontier.x_values[nx - 1] ?? 0;
  const firstY = frontier.y_values[0] ?? 0;
  const lastY = frontier.y_values[ny - 1] ?? 0;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Heat map of how often Option A wins for combinations of two assumptions"
      className="w-full max-w-xl"
    >
      {Array.from({ length: ny }, (_, j) =>
        Array.from({ length: nx }, (_, i) => (
          <rect key={`${j}-${i}`} x={left(i)} y={top(j)} width={CELL} height={CELL} fill={colorFor(value(j, i))} />
        )),
      )}

      {edges.map((e, k) => (
        <line key={k} {...e} stroke="#ffb547" strokeWidth="3" strokeLinecap="round" />
      ))}

      <circle cx={left(xi) + CELL / 2} cy={top(yi) + CELL / 2} r="9" fill="none" stroke="white" strokeWidth="3" />

      <text x={left(0)} y={ny * CELL + 16} fontSize="11" fill="#9a9ab0">{formatNumber(firstX)}</text>
      <text x={left(nx - 1) + CELL} y={ny * CELL + 16} fontSize="11" fill="#9a9ab0" textAnchor="end">
        {formatNumber(lastX)}
      </text>
      <text x={PAD_L + (nx * CELL) / 2} y={ny * CELL + 34} fontSize="12" fill="#ededf5" textAnchor="middle">
        {frontier.x_var}
      </text>
      <text x={PAD_L - 6} y={ny * CELL - 4} fontSize="11" fill="#9a9ab0" textAnchor="end">{formatNumber(firstY)}</text>
      <text x={PAD_L - 6} y={14} fontSize="11" fill="#9a9ab0" textAnchor="end">{formatNumber(lastY)}</text>
    </svg>
  );
}