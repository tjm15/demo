import React from 'react';
import { Eye, Layers, Zap, CheckCircle2 } from "lucide-react";

function PrincipleCard({
  icon,
  title,
  points,
}: {
  icon: React.ReactNode;
  title: string;
  points: string[];
}) {
  return (
    <div className="rounded-xl border border-[color:var(--edge)] bg-[color:var(--panel)] p-5 shadow-sm">
      <div className="mb-2 inline-flex items-center gap-2 text-[color:var(--ink)]">
        <span className="rounded-lg bg-[color:var(--surface)] p-2">{icon}</span>
        <h3 className="text-base font-semibold">{title}</h3>
      </div>
      <ul className="mt-2 space-y-2 text-sm text-[color:var(--muted)]">
        {points.map((p, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--brand)]" />
            <span>{p}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function FoundationsContent({ usePageHeadings = false }) {
  // FIX: Added explicit prop types to fix TypeScript error about missing children.
  const Heading = ({ id, children }: { id: string, children?: React.ReactNode }) => {
    if (usePageHeadings) {
      return <h2 id={id} className="text-xl font-semibold text-[color:var(--ink)]">{children}</h2>;
    }
    return <h3 className="text-lg font-semibold text-[color:var(--ink)]">{children}</h3>;
  };

  return (
    <>
      <section aria-labelledby="why-title" className="mb-10">
        <Heading id="why-title">Why it exists</Heading>
        <div className="mt-3 max-w-3xl space-y-3 text-[color:var(--muted)]">
          <p>
            Planning depends on reasoning — but the system that supports it has become fragmented. Evidence sits in separate databases, policies in unread PDFs, and professional judgement in documents that no one revisits.
          </p>
          <p>
            The Planner’s Assistant rebuilds this foundation: a single environment where policies, data, and spatial evidence can interact, be tested, and evolve together. Its purpose is simple — to restore coherence and capability to the planning system.
          </p>
        </div>
      </section>

      <section aria-labelledby="philosophy-title">
        <Heading id="philosophy-title">Design Philosophy</Heading>
        <p className="mt-3 max-w-3xl text-[color:var(--muted)]">
          The Planner’s Assistant is built on a simple idea: technology should strengthen professional judgement, not replace it. Planning is about reasoning in public — weighing evidence, policy, and the lived character of place. The Assistant exists to make that reasoning visible and consistent, not to take it away.
        </p>

        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <PrincipleCard
            icon={<Eye className="h-5 w-5" />}
            title="Transparency by default"
            points={[
              "Every source, policy, and analytical step is recorded and explainable.",
              "Decisions can be revisited with full evidence trails.",
            ]}
          />
          <PrincipleCard
            icon={<Layers className="h-5 w-5" />}
            title="Open and adaptable"
            points={[
              "Open‑source and modular — easy to extend and integrate.",
              "Strengthens the planning ecosystem rather than fragmenting it.",
            ]}
          />
          <PrincipleCard
            icon={<CheckCircle2 className="h-5 w-5" />}
            title="Designed for real workloads"
            points={[
              "Centred on how planners actually work: reading, mapping, drafting, reviewing.",
              "Removes friction and saves time across routine tasks.",
            ]}
          />
          <PrincipleCard
            icon={<Zap className="h-5 w-5" />}
            title="Balancing speed with care"
            points={[
              "Automation is useful only when it deepens understanding.",
              "Outputs remain accountable: traceable evidence, interrogable reasoning.",
            ]}
          />
        </div>
      </section>
    </>
  );
}