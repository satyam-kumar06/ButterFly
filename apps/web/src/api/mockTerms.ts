import type { TermView } from '../lib/terms';

export type PackName = 'offer_xray' | 'fine_print';

export async function loadMockTerms(pack: PackName): Promise<TermView[]> {
  if (import.meta.env.VITE_MOCK !== '1') {
    throw new Error('Live mode is not implemented yet. Set VITE_MOCK=1.');
  }
  const mod =
    pack === 'offer_xray'
      ? await import('../../../../mocks/terms_offer_xray.json')
      : await import('../../../../mocks/terms_fine_print.json');
  return mod.default as unknown as TermView[];
}

// DEMO ONLY, switched on with ?demo=lowconf. Marks every 7th term as low
// confidence so the amber state can be seen. Not real extraction data.
export function withDemoLowConfidence(terms: TermView[]): TermView[] {
  return terms.map((t, i) =>
    i % 7 === 3
      ? {
          ...t,
          confidence: 0.55,
          evidence: t.evidence ? { ...t.evidence, matched: false } : t.evidence,
        }
      : t,
  );
}