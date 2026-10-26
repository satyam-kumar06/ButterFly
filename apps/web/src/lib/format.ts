// Money in the results is in plain rupees. Show lakhs for big numbers.
export function formatInr(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
  return `₹${Math.round(value).toLocaleString('en-IN')}`;
}

export function formatPercent(p: number): string {
  return `${(p * 100).toFixed(1)}%`;
}
export function formatNumber(value: number): string {
  return Number.isInteger(value) ? value.toLocaleString('en-IN') : value.toFixed(2);
}