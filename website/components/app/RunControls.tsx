import React from 'react';
import { Settings, Globe } from 'lucide-react';

interface RunControlsProps {
  runMode: 'stable' | 'deep';
  setRunMode: (mode: 'stable' | 'deep') => void;
  allowWebFetch: boolean;
  setAllowWebFetch: (allow: boolean) => void;
  disabled: boolean;
}

export function RunControls({
  runMode,
  setRunMode,
  allowWebFetch,
  setAllowWebFetch,
  disabled,
}: RunControlsProps) {
  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Settings className="w-4 h-4 text-[color:var(--accent)]" />
        <h3 className="text-sm font-semibold text-[color:var(--ink)]">Run Controls</h3>
      </div>

      {/* Run Mode */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-[color:var(--muted)] mb-2">
          Analysis Depth
        </label>
        <div className="flex gap-2">
          <button
            onClick={() => setRunMode('stable')}
            disabled={disabled}
            className={`flex-1 px-3 py-2 rounded-lg text-sm transition-all ${
              runMode === 'stable'
                ? 'bg-[color:var(--accent)] text-white'
                : 'bg-[color:var(--surface)] text-[color:var(--muted)] hover:bg-[color:var(--edge)]'
            } disabled:opacity-50`}
          >
            Stable
          </button>
          <button
            onClick={() => setRunMode('deep')}
            disabled={disabled}
            className={`flex-1 px-3 py-2 rounded-lg text-sm transition-all ${
              runMode === 'deep'
                ? 'bg-[color:var(--accent)] text-white'
                : 'bg-[color:var(--surface)] text-[color:var(--muted)] hover:bg-[color:var(--edge)]'
            } disabled:opacity-50`}
          >
            Deep Dive
          </button>
        </div>
        <p className="text-xs text-[color:var(--muted)] mt-2">
          {runMode === 'stable'
            ? 'Faster results with local data only'
            : 'More comprehensive analysis with additional tools'}
        </p>
      </div>

      {/* Web Fetch Toggle */}
      <div>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={allowWebFetch}
            onChange={(e) => setAllowWebFetch(e.target.checked)}
            disabled={disabled}
            className="w-4 h-4 text-[color:var(--accent)] rounded focus:ring-[color:var(--accent)]"
          />
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-[color:var(--muted)]" />
            <span className="text-sm text-[color:var(--ink)]">Allow web fetch</span>
          </div>
        </label>
        <p className="text-xs text-[color:var(--muted)] mt-2 ml-7">
          Retrieve documents from allow-listed sources when needed
        </p>
      </div>
    </div>
  );
}
