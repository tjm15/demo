import React from 'react';
import { motion } from 'framer-motion';
import { FoundationsContent } from './content/FoundationsContent';

export function FoundationsPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4, ease: 'easeInOut' }}
    >
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 pb-24 pt-10">
        {/* Page title */}
        <header className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight text-[color:var(--ink)] sm:text-4xl">
            Foundations
          </h1>
          <p className="mt-2 max-w-3xl text-[color:var(--muted)]">
            Why the Planner’s Assistant exists — and the design choices that make it trustworthy in public decision‑making.
          </p>
        </header>

        <FoundationsContent usePageHeadings={true} />
        
        {/* Closing statement */}
        <section aria-labelledby="foundation-title" className="mt-10 rounded-2xl border border-[color:var(--edge)] bg-[color:var(--ink)] p-6 text-white">
          <h2 id="foundation-title" className="text-xl font-semibold">A new foundation for planning</h2>
          <p className="mt-2 text-white/90 max-w-4xl">
            The Planner’s Assistant is not another portal or dashboard — it is shared civic infrastructure. A digital environment that helps planners, officers, and the public see planning decisions as part of a coherent whole — transparent, explainable, and built for the common good.
          </p>
        </section>
      </div>
    </motion.div>
  );
}