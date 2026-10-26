export type TermValue = string | number | boolean | null;

// Local shape that matches the mock files. I haven't confirmed the generated
// type's name in contracts.ts yet, so we can swap this for it later.
export type TermView = {
  option_id: 'A' | 'B';
  field: string;
  value: TermValue;
  unit: string;
  confidence: number | null;
  evidence: { document_id: string; page: number; quote: string; matched: boolean } | null;
  confirmed: boolean;
};

const UPPER = new Set(['ctc', 'pf', 'hra', 'esop', 'rsu', 'rsus']);

// "annual_ctc" -> "Annual CTC". Dotted policy fields join with " › ".
export function fieldLabel(field: string): string {
  const text = field
    .split('.')
    .map((part) =>
      part.split('_').map((w) => (UPPER.has(w) ? w.toUpperCase() : w)).join(' '),
    )
    .join(' › ');
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// Proposed rule, not yet agreed with Person A.
export function needsCheck(term: TermView): boolean {
  if (term.confirmed) return false;
  if (!term.evidence || !term.evidence.matched) return true;
  return term.confidence !== null && term.confidence < 0.8;
}