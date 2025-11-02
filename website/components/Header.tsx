
import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Logo } from './Logo';

const navLinks = [
    { to: "/foundations", label: "Foundations" },
    { to: "/pillars", label: "Pillars" },
    { to: "/architecture", label: "Architecture" },
    { to: "/involved", label: "Get Involved" },
];

export function Header() {
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);
  
  const activeLinkStyle: React.CSSProperties = {
      color: 'var(--accent)',
      fontWeight: '600',
  };

  return (
    <header className={`sticky top-0 z-40 bg-[color:var(--panel)]/80 backdrop-blur border-b border-[color:var(--edge)] transition-shadow duration-300 ${scrolled ? 'shadow-sm' : ''}`}>
      <nav className="max-w-[1180px] mx-auto px-6 py-3 flex items-center gap-6">
        <Link to="/" className="flex items-center gap-3 group">
          <Logo />
          <span className="text-[color:var(--ink)] font-semibold tracking-tight group-hover:text-[color:var(--accent)] transition-colors">
            The Planner’s Assistant
          </span>
        </Link>

        <div className="ml-auto flex items-center gap-2">
            <div className="hidden md:flex items-center gap-6 text-sm">
                {navLinks.map(link => (
                    <NavLink 
                        key={link.to} 
                        to={link.to}
                        style={({ isActive }) => isActive ? activeLinkStyle : undefined }
                        className="hover:text-[color:var(--accent)] transition-colors"
                    >
                        {link.label}
                    </NavLink>
                ))}
            </div>
            <Link to="/app" className="hidden md:inline-flex items-center justify-center px-3 py-1.5 rounded-xl bg-[color:var(--accent)] text-white shadow-md hover:shadow-lg transition-shadow focus:outline-none focus:[box-shadow:var(--ring)]">Demo</Link>
        </div>
      </nav>
    </header>
  );
}