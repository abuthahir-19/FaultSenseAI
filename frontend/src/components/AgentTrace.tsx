import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, Zap } from 'lucide-react';

interface AgentTraceProps {
  trace: string[];
  severityEscalated: boolean;
}

interface ParsedEntry {
  agentName: string;
  agentNum: number;
  content: string;
  raw: string;
}

const AGENT_CFG: Record<number, {
  bg: string; border: string; text: string; numBg: string; glow: string; label: string; emoji: string;
}> = {
  1: { bg: 'bg-blue-950/40',   border: 'border-blue-700/40',   text: 'text-blue-300',   numBg: 'bg-blue-600',   glow: 'shadow-blue-900/40',   label: 'Alarm Retrieval',  emoji: '🔍' },
  2: { bg: 'bg-violet-950/40', border: 'border-violet-700/40', text: 'text-violet-300', numBg: 'bg-violet-600', glow: 'shadow-violet-900/40', label: 'Cross-Correlation', emoji: '🔗' },
  3: { bg: 'bg-orange-950/40', border: 'border-orange-700/40', text: 'text-orange-300', numBg: 'bg-orange-600', glow: 'shadow-orange-900/40', label: 'Root Cause',         emoji: '🧠' },
  4: { bg: 'bg-emerald-950/40',border: 'border-emerald-700/40',text: 'text-emerald-300',numBg: 'bg-emerald-600',glow: 'shadow-emerald-900/40',label: 'Service Impact',    emoji: '📡' },
  5: { bg: 'bg-teal-950/40',   border: 'border-teal-700/40',   text: 'text-teal-300',   numBg: 'bg-teal-600',   glow: 'shadow-teal-900/40',   label: 'Resolution',        emoji: '🛠' },
};

const DEFAULT_CFG = {
  bg: 'bg-slate-800/40', border: 'border-slate-700/50', text: 'text-slate-300',
  numBg: 'bg-slate-600', glow: '', label: 'System', emoji: '⚙️',
};

function parseTraceEntry(raw: string): ParsedEntry {
  const agentMatch = raw.match(/\[Agent\s*(\d+)[^\]]*\]/i);
  const agentNum = agentMatch ? parseInt(agentMatch[1], 10) : 0;
  const agentName = agentMatch ? agentMatch[0].replace(/^\[|\]$/g, '') : 'System';
  const content = raw.replace(/\[Agent\s*\d+[^\]]*\]\s*[-:]?\s*/i, '').trim();
  return { agentName, agentNum, content, raw };
}

const TraceEntry: React.FC<{ entry: ParsedEntry; index: number; isLast: boolean }> = ({ entry, index, isLast }) => {
  const [open, setOpen] = useState(true);
  const cfg = AGENT_CFG[entry.agentNum] ?? DEFAULT_CFG;

  return (
    <div className="flex gap-4">
      {/* Timeline column */}
      <div className="flex flex-col items-center shrink-0">
        {/* Numbered circle */}
        <div className={`w-8 h-8 rounded-full ${cfg.numBg} flex items-center justify-center z-10 shadow-lg text-xs font-bold text-white`}>
          {index + 1}
        </div>
        {/* Connector line */}
        {!isLast && (
          <div className="w-px flex-1 mt-1 bg-gradient-to-b from-slate-600/60 to-transparent min-h-[16px]" />
        )}
      </div>

      {/* Card */}
      <div className={`flex-1 min-w-0 mb-3 rounded-xl border ${cfg.border} ${cfg.bg} overflow-hidden`}>
        <button
          onClick={() => setOpen(v => !v)}
          className="w-full flex items-center gap-2.5 px-4 py-3 hover:bg-white/5 transition-colors text-left"
        >
          <span className="text-base">{cfg.emoji}</span>
          <div className="flex-1 min-w-0">
            <span className={`text-xs font-bold ${cfg.text}`}>{entry.agentName}</span>
            {!open && (
              <p className="text-[11px] text-slate-500 truncate mt-0.5">{entry.content || entry.raw}</p>
            )}
          </div>
          {open
            ? <ChevronUp size={13} className="text-slate-500 shrink-0" />
            : <ChevronDown size={13} className="text-slate-500 shrink-0" />}
        </button>
        {open && (
          <div className="px-4 pb-4 pt-0 border-t border-white/5">
            <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap mt-3">
              {entry.content || entry.raw}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

const AgentTrace: React.FC<AgentTraceProps> = ({ trace, severityEscalated }) => {
  const [allOpen, setAllOpen] = useState(true);

  if (!trace || trace.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic text-center py-8">No reasoning trace available.</div>
    );
  }

  const parsed = trace.map(parseTraceEntry);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-violet-600/20 border border-violet-600/30">
            <Zap size={13} className="text-violet-400" />
          </div>
          Agent Reasoning Trace
          <span className="text-xs text-slate-500 font-normal bg-slate-800 px-2 py-0.5 rounded-full">
            {trace.length} steps
          </span>
        </h3>
        <div className="flex items-center gap-2">
          {severityEscalated && (
            <div className="flex items-center gap-1.5 bg-red-950/60 border border-red-700/50 rounded-full px-3 py-1 text-xs text-red-300 font-semibold">
              <AlertTriangle size={11} />
              CRITICAL Escalation
            </div>
          )}
          <button
            onClick={() => setAllOpen(v => !v)}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors bg-slate-800/80 border border-slate-700 px-3 py-1 rounded-full"
          >
            {allOpen ? 'Collapse all' : 'Expand all'}
          </button>
        </div>
      </div>

      {/* Agent legend chips */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(AGENT_CFG).map(([num, cfg]) => (
          <span key={num} className={`flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-full border ${cfg.border} ${cfg.bg} ${cfg.text}`}>
            {cfg.emoji} {cfg.label}
          </span>
        ))}
      </div>

      {/* Timeline */}
      {allOpen ? (
        <div className="pt-1">
          {parsed.map((entry, i) => (
            <TraceEntry key={i} entry={entry} index={i} isLast={i === parsed.length - 1} />
          ))}
        </div>
      ) : (
        <button
          onClick={() => setAllOpen(true)}
          className="w-full text-center text-xs text-slate-500 hover:text-slate-300 py-3 border border-dashed border-slate-700 rounded-xl transition-colors hover:border-slate-600"
        >
          Show {trace.length} trace steps
        </button>
      )}
    </div>
  );
};

export default AgentTrace;
