import React from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';

import { CredibilityStrip } from '../components/CredibilityStrip';
import { useMediaQuery } from '../hooks/useMediaQuery';
import { FoundationsContent } from './content/FoundationsContent';
import { PillarsContent } from './content/PillarsContent';
import { ArchitectureContent } from './content/ArchitectureContent';

// AccordionItem is now a controlled component, receiving its state from the parent.
const AccordionItem = ({ title, children, isOpen, onToggle }: { title: string, children?: React.ReactNode, isOpen: boolean, onToggle: () => void }) => {
    return (
        <div className="border-b border-[color:var(--edge)] last:border-b-0">
            <button
                onClick={onToggle}
                className="flex w-full items-center justify-between py-4 text-left font-semibold text-[color:var(--ink)]"
                aria-expanded={isOpen}
            >
                <span className="text-lg">{title}</span>
                <motion.div
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                >
                    <ChevronDown className="h-5 w-5" />
                </motion.div>
            </button>
            <AnimatePresence initial={false}>
                {isOpen && (
                    <motion.div
                        key="content"
                        initial="collapsed"
                        animate="open"
                        exit="collapsed"
                        variants={{
                            open: { opacity: 1, height: 'auto', y: 0 },
                            collapsed: { opacity: 0, height: 0, y: -10 }
                        }}
                        transition={{ duration: 0.4, ease: [0.04, 0.62, 0.23, 0.98] }}
                        className="overflow-hidden"
                    >
                        <div className="pb-4 text-base">
                            {children}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

// MobileInfoSection now manages the state for the exclusive accordion and scrolls into view.
const MobileInfoSection = () => {
    const [openItem, setOpenItem] = React.useState<string | null>(null);
    const sectionRef = React.useRef<HTMLDivElement>(null);

    const handleToggle = (title: string) => {
        setOpenItem(prev => (prev === title ? null : title));
    };

    React.useEffect(() => {
        // Only scroll when an item is OPENED. If null, an item was closed.
        if (openItem !== null && sectionRef.current) {
            // The exit animation for the previous item is 400ms.
            // We scroll after a short delay to allow the layout to settle.
            const timer = setTimeout(() => {
                if (sectionRef.current) {
                    // Approximate height of the sticky header in pixels.
                    const headerHeight = 70; 
                    const elementTop = sectionRef.current.getBoundingClientRect().top + window.scrollY;
                    const offsetPosition = elementTop - headerHeight;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth',
                    });
                }
            }, 150);

            return () => clearTimeout(timer); // Cleanup timeout.
        }
    }, [openItem]);

    return (
        <div ref={sectionRef} className="mt-8 rounded-2xl bg-[color:var(--panel)] border border-[color:var(--edge)] shadow-sm px-4">
            <AccordionItem
                title="Foundations"
                isOpen={openItem === 'Foundations'}
                onToggle={() => handleToggle('Foundations')}
            >
                <FoundationsContent />
            </AccordionItem>
            <AccordionItem
                title="Pillars"
                isOpen={openItem === 'Pillars'}
                onToggle={() => handleToggle('Pillars')}
            >
                <PillarsContent />
            </AccordionItem>
            <AccordionItem
                title="Architecture"
                isOpen={openItem === 'Architecture'}
                onToggle={() => handleToggle('Architecture')}
            >
                <ArchitectureContent />
            </AccordionItem>
        </div>
    );
};

export function HomePage() {
  const isDesktop = useMediaQuery('(min-width: 768px)');

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* HERO */}
      <section id="hero" aria-labelledby="hero-title" className="relative py-20 md:py-28">
        <div className="relative mx-auto px-6 w-full max-w-[1180px]">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-7">
              <h1 id="hero-title" className="text-[color:var(--ink)] text-4xl md:text-5xl lg:text-6xl font-semibold leading-tight">The Planner’s Assistant</h1>
              <p className="mt-3 text-lg md:text-xl">Designing the future of planning. A unified, explainable AI for the public good.</p>
              <p className="mt-6 max-w-prose">
                An open-source environment for spatial planning — built to restore coherence, capacity, and trust in how decisions about place are made. It brings evidence, policy, and spatial data into one workspace, helping officers and policy teams reason clearly across strategy and development management. Designed for use inside government, it strengthens professional judgement rather than replacing it: supporting day-to-day casework, adaptive plan-making, and a transparent link between national policy, local plans, and individual decisions.
              </p>
              <div className="mt-8">
                  {isDesktop ? (
                    <div className="flex flex-wrap items-center gap-4">
                      <Link to="/app" className="px-5 py-3 rounded-2xl bg-[color:var(--accent)] text-white font-medium shadow-md hover:shadow-lg focus:outline-none focus:[box-shadow:var(--ring)] transition-shadow">Demo</Link>
                      <a href="https://github.com/tjm15" target="_blank" rel="noopener noreferrer" className="px-5 py-3 rounded-2xl border border-[color:var(--accent)] text-[color:var(--accent)] font-medium hover:bg-[color:var(--accent)]/10 transition-colors">GitHub</a>
                      <Link to="/foundations" className="text-[color:var(--muted)] hover:text-[color:var(--ink)] transition-colors font-medium">Learn more →</Link>
                    </div>
                  ) : (
                    <div className="w-full">
                        <a href="https://github.com/tjm15" target="_blank" rel="noopener noreferrer" className="inline-flex items-center justify-center w-full px-5 py-3 rounded-2xl border border-[color:var(--accent)] text-[color:var(--accent)] font-medium">GitHub</a>
                        <p className="text-sm text-[color:var(--muted)] mt-4 text-center">The interactive demo is available on desktop.</p>
                        <MobileInfoSection />
                    </div>
                  )}
              </div>
            </div>
            <div className="lg:col-span-5">
               <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
                className="relative hidden lg:block"
              >
                <img 
                  src="https://i.postimg.cc/DwGW68WX/Chat-GPT-Image-Oct-24-2025-03-34-39-PM.png" 
                  alt="A stylized user interface for The Planner's Assistant, showing maps and data analysis."
                  className="rounded-2xl bg-[color:var(--panel)]/80 border border-[color:var(--edge)] shadow-xl w-full h-auto object-cover" 
                />
              </motion.div>
            </div>
          </div>

          <div className="mt-12 lg:mt-20">
            <h3 className="text-center text-xl text-[color:var(--ink)] font-semibold">
              Built for the people who make planning work
            </h3>
            <CredibilityStrip />
          </div>
        </div>
      </section>
    </motion.div>
  );
}