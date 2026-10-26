import type { Branch, FixedVariable, DistributionVariable } from '../contracts';

export function variableSummary(v: FixedVariable | DistributionVariable): string {
  if ('value' in v) return String(v.value);
  return `distribution ${JSON.stringify(v.dist)}`;
}

// Puts branches in tree order: each branch is followed by its children.
export function orderBranches(branches: Branch[]): { branch: Branch; depth: number }[] {
  const children = new Map<string | null, Branch[]>();
  for (const b of branches) {
    const key = b.parent_id ?? null;
    children.set(key, [...(children.get(key) ?? []), b]);
  }
  const out: { branch: Branch; depth: number }[] = [];
  const seen = new Set<string>();
  const walk = (parent: string | null, depth: number) => {
    for (const b of children.get(parent) ?? []) {
      if (seen.has(b.id)) continue;
      seen.add(b.id);
      out.push({ branch: b, depth });
      walk(b.id, depth + 1);
    }
  };
  walk(null, 0);
  // Any branch whose parent is missing still gets shown, at the top level.
  for (const b of branches) {
    if (!seen.has(b.id)) out.push({ branch: b, depth: 0 });
  }
  return out;
}