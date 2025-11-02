
import React from 'react';
import { Link } from 'react-router-dom';
import { Logo } from './Logo';

const navLinks = [
    { to: "/foundations", label: "Foundations" },
    { to: "/pillars", label: "Pillars" },
    { to: "/architecture", label: "Architecture" },
    { to: "/involved", label: "Get Involved" },
];

export function Footer() {
  return (
    <footer className="sticky bottom-0 border-t border-[color:var(--edge)] py-4 bg-[color:var(--surface)] backdrop-blur-sm bg-opacity-95">
      <div className="max-w-[1180px] mx-auto px-6">
        {/* Disclaimer */}
        <div className="mb-3 text-center">
          <p className="text-xs text-[color:var(--muted)] italic">
            ⚠️ This tool provides informational assistance only and does not constitute professional planning advice. 
            Always consult qualified planning professionals and relevant local planning authorities.
          </p>
        </div>
        
        {/* Footer content */}
        <div className="flex flex-col md:flex-row items-center gap-4">
          <div className="flex items-center gap-3 text-[color:var(--ink)] font-medium text-sm">
            <Logo />
            <span>Built openly for the public good.</span>
          </div>
          <div className="md:ml-auto flex flex-wrap gap-x-4 gap-y-2 text-sm">
              <Link to="/" className="hover:underline">Home</Link>
              {navLinks.map(link => (
                  <Link key={link.to} to={link.to} className="hover:underline">{link.label}</Link>
              ))}
          </div>
        </div>
      </div>
    </footer>
  );
}