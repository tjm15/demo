import React from "react";
import { motion } from "framer-motion";

interface ModuleCardProps {
    title: string;
    desc: string;
    onClick?: () => void;
}

export function ModuleCard({ title, desc, onClick }: ModuleCardProps) {
  return (
    <motion.div
      onClick={onClick}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.5 }}
      whileHover={{ y: -5, boxShadow: "0 10px 15px -3px rgba(0,0,0,0.05), 0 4px 6px -2px rgba(0,0,0,0.05)" }}
      className={`rounded-2xl bg-[color:var(--panel)]/95 backdrop-blur border border-[color:var(--edge)] p-5 shadow-sm h-full ${onClick ? 'cursor-pointer' : ''}`}
    >
      <div className="text-[color:var(--ink)] font-semibold">{title}</div>
      <p className="text-[color:var(--muted)] mt-2">{desc}</p>
    </motion.div>
  );
}