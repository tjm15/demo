
import React from 'react';
import { HashRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { FoundationsPage } from './pages/FoundationsPage';
import { PillarsPage } from './pages/PillarsPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { InvolvedPage } from './pages/InvolvedPage';
import { AppPage } from './pages/AppPage';


// A simple component to handle scroll restoration on navigation
const ScrollToTop = () => {
    const { pathname } = useLocation();

    React.useEffect(() => {
        window.scrollTo(0, 0);
    }, [pathname]);

    return null;
}

const AnimatedRoutes = () => {
    const location = useLocation();
    return (
        <AnimatePresence mode="wait">
      <Routes location={location}>
                <Route path="/" element={<HomePage />} />
                <Route path="/foundations" element={<FoundationsPage />} />
                <Route path="/pillars" element={<PillarsPage />} />
                <Route path="/architecture" element={<ArchitecturePage />} />
                <Route path="/involved" element={<InvolvedPage />} />
                <Route path="/app" element={<AppPage />} />
            </Routes>
        </AnimatePresence>
    );
};

export default function App() {
  return (
    <HashRouter>
      <ScrollToTop />
      <Layout>
        <AnimatedRoutes />
      </Layout>
    </HashRouter>
  );
}