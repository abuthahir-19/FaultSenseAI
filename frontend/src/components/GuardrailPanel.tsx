import React from 'react';
import { ShieldCheck, ShieldAlert, ShieldX, CheckCircle2, AlertTriangle, XCircle, MinusCircle } from 'lucide-react';
import type { GuardrailResult } from '../types';

interface Props { result: GuardrailResult; }
type CheckStatus = 'pass' | 'warn' | 'fail' | 'skip';
interface Check { name: string; desc: string; status: CheckStatus; }

function inferChecks(result: GuardrailResult): Check[] {
  const isLengthErr   = result.error?.includes('empty') || result.error?.includes('short') || result.error?.includes('long');
  const isInjectErr   = result.error?.includes('disallowed');
  return [
    { name: 'Input Validation',   desc: 'Length · format · empty-check',                status: isLengthErr ? 'fail' : 'pass' },
    { name: 'Injection Detection',desc: 'Prompt injection · SQL · script patterns',      status: isLengthErr ? 'skip' : isInjectErr ? 'fail' : 'pass' },
    { name: 'Telecom Relevance',  desc: 'Domain keyword presence',
      status: isLengthErr || isInjectErr ? 'skip' : result.warnings.length > 0 ? 'warn' : 'pass' },
  ];
}

const STATUS_ICON: Record<CheckStatus, React.ReactNode> = {
  pass: <CheckCircle2  size={16} className="text-emerald-400 shrink-0" />,
  warn: <AlertTriangle size={16} className="text-yellow-400 shrink-0" />,
  fail: <XCircle       size={16} className="text-red-400 shrink-0" />,
  skip: <MinusCircle   size={16} className="text-slate-600 shrink-0" />,
};

const STATUS_META: Record<CheckStatus, { label: string; text: string; bg: string; border: string }> = {
  pass: { label: 'Passed',  text: 'text-emerald-400', bg: 'bg-emerald-950/40', border: 'border-emerald-800/40' },
  warn: { label: 'Warning', text: 'text-yellow-400',  bg: 'bg-yellow-950/40',  border: 'border-yellow-800/40' },
  fail: { label: 'Failed',  text: 'text-red-400',     bg: 'bg-red-950/40',     border: 'border-red-800/40' },
  skip: { label: 'Skipped', text: 'text-slate-500',   bg: 'bg-slate-800/40',   border: 'border-slate-700/40' },
};

const GuardrailPanel: React.FC<Props> = ({ result }) => {
  const checks       = inferChecks(result);
  const hasWarnings  = result.warnings.length > 0;
  const isBlocked    = !result.valid;
  const status       = isBlocked ? 'blocked' : hasWarnings ? 'warned' : 'passed';

  const BANNER = {
    passed:  { icon: <ShieldCheck size={18} className="text-emerald-400 shrink-0" />, label: 'All guardrail checks passed',  bg: 'bg-emerald-950/30 border-emerald-700/40', text: 'text-emerald-300' },
    warned:  { icon: <ShieldAlert size={18} className="text-yellow-400 shrink-0" />,  label: 'Passed with warnings',          bg: 'bg-yellow-950/30 border-yellow-700/40',  text: 'text-yellow-300' },
    blocked: { icon: <ShieldX     size={18} className="text-red-400 shrink-0" />,     label: 'Query blocked by guardrail',    bg: 'bg-red-950/30 border-red-700/40',        text: 'text-red-300' },
  }[status];

  return (
    <div className="bg-slate-900/60 backdrop-blur-sm border border-slate-700/80 rounded-2xl p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="p-1.5 rounded-lg bg-slate-800 border border-slate-700">
          <ShieldCheck size={14} className="text-slate-400" />
        </div>
        <h3 className="text-sm font-semibold text-slate-200">Guardrail Validation</h3>
        <span className="text-xs text-slate-500 bg-slate-800 border border-slate-700/60 px-2 py-0.5 rounded-full ml-1">
          3 checks
        </span>
      </div>

      {/* Status banner */}
      <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border ${BANNER.bg}`}>
        {BANNER.icon}
        <span className={`text-sm font-semibold ${BANNER.text}`}>{BANNER.label}</span>
      </div>

      {/* Check cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {checks.map((chk) => {
          const meta = STATUS_META[chk.status];
          return (
            <div
              key={chk.name}
              className={`flex items-start gap-3 ${meta.bg} border ${meta.border} rounded-xl px-3.5 py-3 transition-all`}
            >
              <div className="mt-0.5">{STATUS_ICON[chk.status]}</div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-slate-200 leading-tight">{chk.name}</p>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{chk.desc}</p>
                <p className={`text-[11px] font-semibold mt-1.5 ${meta.text}`}>{meta.label}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Warnings */}
      {hasWarnings && (
        <div className="space-y-1.5">
          {result.warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-2 bg-yellow-950/20 border border-yellow-800/30 rounded-lg px-3 py-2">
              <AlertTriangle size={12} className="text-yellow-400 shrink-0 mt-0.5" />
              <p className="text-xs text-yellow-300 leading-relaxed">{w}</p>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
      {isBlocked && result.error && (
        <div className="flex items-start gap-2 bg-red-950/20 border border-red-800/30 rounded-lg px-3 py-2">
          <XCircle size={12} className="text-red-400 shrink-0 mt-0.5" />
          <p className="text-xs text-red-300 leading-relaxed">{result.error}</p>
        </div>
      )}
    </div>
  );
};

export default GuardrailPanel;
