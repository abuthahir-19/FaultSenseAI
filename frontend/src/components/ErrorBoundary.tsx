import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: React.ReactNode;
  fallbackLabel?: string;
}

interface State {
  hasError: boolean;
  message: string;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, message: '' };

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : 'An unexpected error occurred.',
    };
  }

  handleReset = () => this.setState({ hasError: false, message: '' });

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
          <div className="p-4 rounded-full bg-red-900/30 border border-red-700">
            <AlertTriangle size={28} className="text-red-400" />
          </div>
          <div>
            <p className="text-red-300 font-medium">{this.props.fallbackLabel ?? 'Something went wrong'}</p>
            <p className="text-slate-500 text-sm mt-1 max-w-sm">{this.state.message}</p>
          </div>
          <button
            onClick={this.handleReset}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-200 text-sm transition-colors"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
