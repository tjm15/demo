import React from 'react';

type Props = { children: React.ReactNode };

type State = { hasError: boolean; message?: string };

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: any) {
    return { hasError: true, message: String(error?.message || error) };
  }

  componentDidCatch(error: any, errorInfo: any) {
    console.error('Panel error boundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-[600px] bg-white rounded-xl border-2 border-dashed border-slate-300 shadow-sm">
          <div className="text-center px-6 max-w-md">
            <p className="text-lg font-semibold text-slate-900 mb-1">Something went wrong</p>
            <p className="text-sm text-slate-500 mb-2">A panel failed to render. Please adjust your query or try again.</p>
            {this.state.message && (
              <pre className="text-xs text-slate-400 bg-slate-50 p-3 rounded border border-slate-200 overflow-auto max-h-40">{this.state.message}</pre>
            )}
          </div>
        </div>
      );
    }
    // Avoid TS config friction by accessing props via any
    return (this as any).props.children as any;
  }
}
