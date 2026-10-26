import type { PackName } from './mockTerms';
import type { Results } from '../lib/results';

export async function loadMockResults(pack: PackName): Promise<Results> {
  if (import.meta.env.VITE_MOCK !== '1') {
    throw new Error('Live mode is not implemented yet. Set VITE_MOCK=1.');
  }
  const mod =
    pack === 'offer_xray'
      ? await import('../../../../mocks/results_offer_xray.json')
      : await import('../../../../mocks/results_fine_print.json');
  return mod.default as unknown as Results;
}