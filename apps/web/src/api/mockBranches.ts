import type { Branch } from '../contracts';
import type { PackName } from './mockTerms';

export async function loadMockBranches(pack: PackName): Promise<Branch[]> {
  if (import.meta.env.VITE_MOCK !== '1') {
    throw new Error('Live mode is not implemented yet. Set VITE_MOCK=1.');
  }
  const mod =
    pack === 'offer_xray'
      ? await import('../../../../mocks/branches_offer_xray.json')
      : await import('../../../../mocks/branches_fine_print.json');
  return (mod.default as unknown as { branches: Branch[] }).branches;
}