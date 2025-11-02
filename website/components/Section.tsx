import React from "react";

interface SectionProps {
  id: string;
  title?: string;
  // Fix: Make children optional to address TypeScript error.
  children?: React.ReactNode;
  tone?: "plain" | "tint" | "panel";
}

export function Section({ id, title, children, tone = "plain" }: SectionProps) {
  const toneClass = tone === "tint"
    ? "bg-[color:var(--surface)]"
    : tone === "panel"
      ? "bg-[color:var(--panel)]"
      : "bg-transparent";
  return (
    <section id={id} aria-labelledby={title ? `${id}-title` : undefined} className={`py-16 md:py-20 lg:py-28 ${toneClass}`}>
      <div className="mx-auto px-6 w-full max-w-[1180px]">
        {title && (
          <h2 id={`${id}-title`} className="text-[color:var(--ink)] text-2xl md:text-3xl font-semibold mb-6">
            {title}
          </h2>
        )}
        {children}
      </div>
    </section>
  );
}
