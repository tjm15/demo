
import React from "react";
import { motion } from "framer-motion";

interface PillarCardProps {
    title: string;
    subtitle: string;
    accentColor?: string;
    children?: React.ReactNode;
}

export function PillarCard({ title, subtitle, children, accentColor = 'var(--accent)' }: PillarCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.5 }}
      whileHover={{ y: -5, boxShadow: "0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.05)" }}
      className="rounded-2xl bg-[color:var(--panel)]/95 backdrop-blur border border-[color:var(--edge)] p-6 shadow-sm overflow-hidden h-full flex flex-col"
      style={{ borderTop: `4px solid ${accentColor}` }}
    >
      <div className="text-[color:var(--ink)] text-xl font-semibold">{title}</div>
      <div className="text-[color:var(--muted)] mt-1">{subtitle}</div>
      <div className="mt-4 text-[color:var(--muted)] flex-grow">{children}</div>
    </motion.div>
  );
}
