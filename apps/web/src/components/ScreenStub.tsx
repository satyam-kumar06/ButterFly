import { Link, useParams } from 'react-router-dom';

const STEPS = [
  ['describe', 'Describe'],
  ['interview', 'Interview'],
  ['forge', 'Forge'],
  ['multiverse', 'Multiverse'],
  ['flips', 'Flip points'],
  ['branches', 'Branches'],
  ['report', 'Report'],
] as const;

export function ScreenStub({ title }: { title: string }) {
  const { id = 'demo_offer_xray' } = useParams();
  return (
    <main className="mx-auto max-w-3xl p-8">
      <p className="font-mono text-sm text-muted">session: {id}</p>
      <h1 className="mt-2 font-display text-5xl font-semibold">{title}</h1>
      <nav className="mt-8 flex flex-wrap gap-3">
        <Link className="glass px-4 py-2" to="/">Home</Link>
        {STEPS.map(([path, label]) => (
          <Link key={path} className="glass px-4 py-2" to={`/s/${id}/${path}`}>{label}</Link>
        ))}
      </nav>
    </main>
  );
}