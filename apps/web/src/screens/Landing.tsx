import { Link } from 'react-router-dom';

export default function Landing() {
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="font-display text-6xl font-semibold">Fork your life.</h1>
      <p className="mt-4 text-muted">Landing page placeholder.</p>
      <Link className="glass mt-8 inline-block px-5 py-3" to="/s/demo_offer_xray/describe">
        Start a fork
      </Link>
    </main>
  );
}