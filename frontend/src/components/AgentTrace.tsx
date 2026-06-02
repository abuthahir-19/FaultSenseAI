import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, Bot } from 'lucide-react';

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

const AGENT_STYLES: Record<number, { bg: string; border: string; text: string; dot: string }> = {
  1: { bg: 'bg-blue-900/30', border: 'border-blue-700/50', text: 'text-blue-300', dot: 'bg-blue-500' },
  2: { bg: 'bg-violet-900/30', border: 'border-violet-700/50', text: 'text-violet-300', dot: 'bg-violet-500' },
  3: { bg: 'bg-orange-900/30', border: 'border-orange-700/50', text: 'text-orange-300', dot: 'bg-orange-500' },
  4: { bg: 'bg-green-900/30', border: 'border-green-700/50', text: 'text-green-300', dot: 'bg-green-500' },
};

const DEFAULT_STYLE = { bg: 'bg-slate-800/50', border: 'border-slate-700', text: 'text-slate-300', dot: 'bg-slate-500' };

function parseTraceEntry(raw: string): ParsedEntry {
  // Match patterns like "[Agent 1 - Alarm Retrieval]" or "[Agent1]" etc.
  const agentMatch = raw.match(/\[Agent\s*(\d+)[^\]]*\]/i);
  const agentNum = agentMatch ? parseInt(agentMatch[1], 10) : 0;
  const agentName = agentMatch ? agentMatch[0].replace(/^\[|\]$/g, '') : 'System';
  const content = raw.replace(/\[Agent\s*\d+[^\]]*\]\s*[-:]?\s*/i, '').trim();
  return { agentName, agentNum, content, raw };
}

const TraceEntry: React.FC<{ entry: ParsedEntry; index: number }> = ({ entry, index }) => {
  const [open, setOpen] = useState(true);
  const style = AGENT_STYLES[entry.agentNum] ?? DEFAULT_STYLE;

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} overflow-hidden`}>
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/5 transition-colors text-left"
      >
        <span className={`w-2 h-2 rounded-full shrink-0 ${style.dot}`} />
        <Bot size={14} className={style.text} />
        <span className={`text-sm font-semibold ${style.text} flex-1`}>
          Step {index + 1}: {entry.agentName}
        </span>
        {open ? (
          <ChevronUp size={14} className="text-slate-400" />
        ) : (
          <ChevronDown size={14} className="text-slate-400" />
        )}
      </button>
      {open && (
        <div className="px-4 pb-4 pt-1">
          <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{entry.content || entry.raw}</p>
        </div>
      )}
    </div>
  );
};

const AgentTrace: React.FC<AgentTraceProps> = ({ trace, severityEscalated }) => {
  const [allOpen, setAllOpen] = useState(true);

  if (!trace || trace.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic text-center py-6">No reasoning trace available.</div>
    );
  }

  const parsed = trace.map(parseTraceEntry);

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Bot size={16} className="text-violet-400" />
          Agent Reasoning Trace
          <span className="text-xs text-slate-500 font-normal">({trace.length} steps)</span>
        </h3>
        <div className="flex items-center gap-3">
          {severityEscalated && (
            <div className="flex items-center gap-1.5 bg-red-900/40 border border-red-700/50 rounded-full px-3 py-1 text-xs text-red-300 font-medium">
              <AlertTriangle size={12} />
              Severity Escalated
            </div>
          )}
          <button
            onClick={() => setAllOpen(v => !v)}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            {allOpen ? 'Collapse All' : 'Expand All'}
          </button>
        </div>
      </div>

      {/* Agent legend */}
      <div className="flex flex-wrap gap-3 text-xs">
        {[
          { num: 1, label: 'Alarm Retrieval' },
          { num: 2, label: 'Correlation' },
          { num: 3, label: 'Root Cause' },
          { num: 4, label: 'Recommendation' },
        ].map(({ num, label }) => {
          const s = AGENT_STYLES[num];
          return (
            <span key={num} className={`flex items-center gap-1.5 ${s.text}`}>
              <span className={`w-2 h-2 rounded-full ${s.dot}`} />
              Agent {num}: {label}
            </span>
          );
        })}
      </div>

      {/* Trace entries */}
      <div className={`space-y-2 ${allOpen ? '' : 'hidden'}`}>
        {parsed.map((entry, i) => (
          <TraceEntry key={i} entry={entry} index={i} />
        ))}
      </div>
      {!allOpen && (
        <button
          onClick={() => setAllOpen(true)}
          className="w-full text-center text-xs text-slate-500 hover:text-slate-300 py-2 border border-slate-700 rounded-xl transition-colors"
        >
          Show {trace.length} trace steps
        </button>
      )}
    </div>
  );
};

export default AgentTrace;
