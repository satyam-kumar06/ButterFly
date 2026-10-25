import { Link } from 'react-router-dom';
import { motion, MotionConfig } from 'framer-motion';

const PACKS = [
  { name: 'Offer X-ray', text: 'Compare job offers by what actually lands in your hand.', beta: false },
  { name: 'Fine Print', text: 'Compare health insurance policies by what they really cover.', beta: false },
  { name: 'Open mode', text: 'For money decisions outside the packs.', beta: true },
];

export default function Landing() {
  return (
    <MotionConfig reducedMotion="user">
      <main className="mx-auto max-w-5xl px-6 py-24">
        <motion.h1
          className="max-w-3xl font-display text-5xl font-semibold leading-tight md:text-7xl"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
        >
          Every decision splits your future. See both sides before you choose.
        </motion.h1>

        <ul className="mt-16 grid gap-4 md:grid-cols-3">
          {PACKS.map((pack, i) => (
            <motion.li
              key={pack.name}
              className="glass p-6 transition-shadow duration-[180ms] hover:shadow-[0_0_32px_rgb(255_255_255/0.12)]"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1], delay: 0.2 + i * 0.06 }}
            >
              <h2 className="flex items-center gap-2 font-display text-2xl font-semibold">
                {pack.name}
                {pack.beta && (
                  <span className="rounded-full border border-white/20 px-2 py-0.5 font-body text-xs font-normal text-muted">
                    beta
                  </span>
                )}
              </h2>
              <p className="mt-3 text-muted">{pack.text}</p>
            </motion.li>
          ))}
        </ul>

        <motion.div
          className="mt-12 inline-block"
          animate={{ scale: [1, 1.04, 1] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Link
            to="/s/demo_offer_xray/describe"
            className="glass inline-block px-6 py-3 font-display text-lg font-semibold focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
          >
            Start a fork
          </Link>
        </motion.div>
      </main>
    </MotionConfig>
  );
}