import React from "react";
import { Link } from "react-router-dom";
import { useMediaQuery } from '../hooks/useMediaQuery';

const items = [
  { t: "Planners and policy officers", d: "Integrated evidence bases, automated synthesis, explainable reasoning." },
  { t: "Councils and civil servants", d: "Measurable plan delivery, alignment, and performance." },
  { t: "Researchers and practitioners", d: "A working platform for spatial reasoning, AI‑assisted governance, and open digital planning infrastructure." },
  { t: "Collaborators and technologists", d: "A modular, open‑source architecture ready to extend and deploy." },
];

export function CredibilityStrip() {
  const isDesktop = useMediaQuery('(min-width: 640px)'); // 'sm' breakpoint

  if (isDesktop) {
    // Current desktop/tablet implementation (grid of links)
    return (
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {items.map((it) => (
          <Link 
            key={it.t} 
            to="/involved"
            className="block rounded-2xl bg-[color:var(--panel)]/90 backdrop-blur border border-[color:var(--edge)] p-5 shadow-sm transition-all hover:shadow-lg hover:-translate-y-1 focus:outline-none focus:[box-shadow:var(--ring)]"
          >
            <div className="text-[color:var(--ink)] font-medium">{it.t}</div>
            <div className="text-[color:var(--muted)] mt-1">{it.d}</div>
          </Link>
        ))}
      </div>
    );
  }

  // New mobile implementation (single card with list and button)
  return (
    <div className="mt-6 rounded-2xl bg-[color:var(--panel)]/90 backdrop-blur border border-[color:var(--edge)] p-6 shadow-sm">
      <ul className="space-y-4">
        {items.map((it) => (
          <li key={it.t}>
            <p className="text-[color:var(--ink)] font-medium">{it.t}</p>
            <p className="text-[color:var(--muted)] text-sm mt-0.5">{it.d}</p>
          </li>
        ))}
      </ul>
      <div className="mt-6 text-center">
        <Link 
          to="/involved" 
          className="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-[color:var(--accent)] text-white font-medium shadow-md hover:shadow-lg transition-shadow focus:outline-none focus:[box-shadow:var(--ring)]"
        >
          Get Involved
        </Link>
      </div>
    </div>
  );
}