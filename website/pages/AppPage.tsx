import React from 'react';
import { AppWorkspace } from '../components/app/AppWorkspace';
import { useMediaQuery } from '../hooks/useMediaQuery';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const DesktopIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 text-[color:var(--muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-1.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25A2.25 2.25 0 015.25 3h13.5A2.25 2.25 0 0121 5.25z" />
    </svg>
);

const DesktopOnlyView = () => (
    <div className="flex flex-col items-center justify-center text-center py-20 px-6 bg-[color:var(--surface)] min-h-screen">
        <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, type: 'spring' }}
            className="w-full max-w-md bg-[color:var(--panel)] rounded-2xl border border-[color:var(--edge)] shadow-lg p-8 md:p-12"
        >
            <DesktopIcon />
            <h1 className="text-2xl md:text-3xl font-bold text-[color:var(--ink)] mt-6">Desktop Experience</h1>
            <p className="text-lg text-[color:var(--muted)] mt-4 max-w-md mx-auto">
                The interactive demo for The Planner's Assistant is designed for larger screens.
            </p>
            <div className="mt-8">
                <Link
                    to="/"
                    className="px-6 py-3 rounded-xl bg-[color:var(--accent)] text-white font-medium shadow-md hover:shadow-lg transition-all focus:outline-none focus:[box-shadow:var(--ring)]"
                >
                    Back to Homepage
                </Link>
            </div>
        </motion.div>
    </div>
);

export function AppPage() {
    const isDesktop = useMediaQuery('(min-width: 1024px)');
    
    return isDesktop ? <AppWorkspace /> : <DesktopOnlyView />;
}