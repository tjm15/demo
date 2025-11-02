import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { useThemeInstall } from '../hooks/useThemeInstall';
import { AmbientNetwork } from './AmbientNetwork';

interface LayoutProps {
  // Fix: Make children optional to address TypeScript error.
  children?: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  useThemeInstall();
  
  return (
    <div style={{ background: "var(--surface)", color: "var(--muted)" }}>
      <div className="fixed inset-0 z-0 pointer-events-none">
        <AmbientNetwork />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_60%,_var(--surface)_95%)]" />
      </div>
      
      <div className="relative z-10 min-h-screen flex flex-col" style={{ scrollBehavior: "smooth" }}>
        <Header />
        <main className="flex-grow">
          {children}
        </main>
        <Footer />
      </div>
    </div>
  );
}