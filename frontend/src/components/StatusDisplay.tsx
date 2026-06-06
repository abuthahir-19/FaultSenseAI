import React from 'react';
import { CheckCircle2, Loader2, Circle, AlertCircle } from 'lucide-react';

export interface StatusStep {
  emoji: string;
  label: string;
  sublabel: string;
}

interface Props {
  steps: StatusStep[];
  activeStep: number;   // index of the step currently running
  done: boolean;
  error?: string | null;
  mode: 'query' | 'analyze';
}

const StatusDisplay: React.FC<Props> = ({ steps, activeStep, done, error, mode }) => {
  const progress = done ? 100 : Math.round((activeStep / steps.length) * 100);

  return (
    <div className="w-full max-w-xl mx-auto py-8 space-y-6">

      {/* Header */}
      <div className="text-center space-y-1">
        <p className={`text-sm font-semibold ${error ? 'text-red-400' : done ? 'text-emerald-400' : 'text-blue-300'}`}>
          {error
            ? '⚠ Operation failed'
            : done
            ? `✓ ${mode === 'analyze' ? 'Analysis complete' : 'Search complete'}`
            : mode === 'analyze'
            ? 'Running LangGraph agent pipeline…'
            : 'Searching incident knowledge base…'}
        </p>
        {!done && !error && (
          <p className="text-xs text-slate-500">
            Step {Math.min(activeStep + 1, steps.length)} of {steps.length}
          </p>
        )}
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${
            error ? 'bg-red-500' : done ? 'bg-emerald-500' : 'bg-blue-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-2.5">
        {steps.map((step, i) => {
          const isActive  = i === activeStep && !done && !error;
          const isComplete = done || i < activeStep;
          const isPending  = !done && i > activeStep;

          return (
            <div
              key={i}
              className={`flex items-center gap-3 p-3 rounded-xl border transition-all duration-300 ${
                isActive
                  ? 'bg-blue-950/40 border-blue-700/40'
                  : isComplete
                  ? 'bg-emerald-950/20 border-emerald-800/30'
                  : 'bg-slate-900/30 border-slate-800/50 opacity-35'
              }`}
            >
              {/* Step icon */}
              <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                isActive   ? 'bg-blue-600/25 border border-blue-500/50' :
                isComplete ? 'bg-emerald-600/25 border border-emerald-500/50' :
                             'bg-slate-800 border border-slate-700'
              }`}>
                {isActive   ? <Loader2    size={13} className="text-blue-400 animate-spin" /> :
                 isComplete ? <CheckCircle2 size={13} className="text-emerald-400" /> :
                              <Circle     size={13} className="text-slate-600" />}
              </div>

              {/* Emoji + labels */}
              <div className="flex-1 min-w-0">
                <div className={`text-xs font-semibold leading-tight ${
                  isActive   ? 'text-blue-200' :
                  isComplete ? 'text-emerald-300' :
                               'text-slate-500'
                }`}>
                  <span className="mr-1.5">{step.emoji}</span>
                  {step.label}
                </div>
                {(isActive || isComplete) && (
                  <div className="text-[10px] text-slate-500 mt-0.5 truncate">{step.sublabel}</div>
                )}
              </div>

              {/* Right badge */}
              {isActive && (
                <span className="text-[10px] font-semibold text-blue-400 bg-blue-900/40 border border-blue-700/40 px-2 py-0.5 rounded-full shrink-0 animate-pulse">
                  Running
                </span>
              )}
              {isComplete && !error && (
                <span className="text-[10px] font-semibold text-emerald-400 shrink-0">Done</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Error detail */}
      {error && (
        <div className="flex items-start gap-2 bg-red-900/20 border border-red-700/40 rounded-xl px-4 py-3 text-red-300 text-xs">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

export default StatusDisplay;
