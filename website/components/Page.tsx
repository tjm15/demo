import React from 'react';
import { motion } from 'framer-motion';

interface PageProps {
  title: string;
  // FIX: Made children optional to address multiple TypeScript errors.
  children?: React.ReactNode;
  className?: string;
}

export function Page({ title, children, className = '' }: PageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4, ease: 'easeInOut' }}
      className={`py-16 md:py-20 lg:py-24 ${className}`}
    >
      <div className="mx-auto px-6 w-full max-w-[1180px]">
        <h1 className="text-[color:var(--ink)] text-3xl md:text-4xl font-semibold mb-8 border-b border-[color:var(--edge)] pb-4">
          {title}
        </h1>
        {children}
      </div>
    </motion.div>
  );
}
