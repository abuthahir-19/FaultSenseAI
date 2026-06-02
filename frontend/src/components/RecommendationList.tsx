import React, { useState } from 'react';
import { Copy, Check, Wrench, Stethoscope, CheckCircle, Shield, ArrowUpCircle, HelpCircle } from 'lucide-react';

interface RecommendationListProps {
  recommendations: string[];
}

interface ParsedRec {
  category: string;
  text: string;
  raw: string;
}

const CATEGORY_CONFIG: Record<string, { color: string; bg: string; border: string; label: string; icon: React.ReactNode }> = {
  IMMEDIATE: {
    color: 'text-red-300',
    bg: 'bg-red-900/30',
    border: 'border-red-700/50',
    label: 'Immediate Action',
    icon: <ArrowUpCircle size={14} />,
  },
  DIAGNOSTIC: {
    color: 'text-blue-300',
    bg: 'bg-blue-900/30',
    border: 'border-blue-700/50',
    label: 'Diagnostic',
    icon: <Stethoscope size={14} />,
  },
  RESOLUTION: {
    color: 'text-green-300',
    bg: 'bg-green-900/30',
    border: 'border-green-700/50',
    label: 'Resolution',
    icon: <Wrench size={14} />,
  },
  PREVENTIVE: {
    color: 'text-teal-300',
    bg: 'bg-teal-900/30',
    border: 'border-teal-700/50',
    label: 'Preventive',
    icon: <Shield size={14} />,
  },
  ESCALATION: {
    color: 'text-purple-300',
    bg: 'bg-purple-900/30',
    border: 'border-purple-700/50',
    label: 'Escalation',
    icon: <CheckCircle size={14} />,
  },
  GENERAL: {
    color: 'text-slate-300',
    bg: 'bg-slate-800/50',
    border: 'border-slate-700',
    label: 'General',
    icon: <HelpCircle size={14} />,
  },
};

const CATEGORY_ORDER = ['IMMEDIATE', 'ESCALATION', 'DIAGNOSTIC', 'RESOLUTION', 'PREVENTIVE', 'GENERAL'];

function parseRecommendation(raw: string): ParsedRec {
  // Match [CATEGORY] prefix
  const match = raw.match(/^\[([A-Z]+)\]\s*/);
  if (match) {
    const category = match[1].toUpperCase();
    const knownCategory = Object.keys(CATEGORY_CONFIG).includes(category) ? category : 'GENERAL';
    return { category: knownCategory, text: raw.slice(match[0].length).trim(), raw };
  }
  return { category: 'GENERAL', text: raw.trim(), raw };
}

const RecommendationList: React.FC<RecommendationListProps> = ({ recommendations }) => {
  const [copied, setCopied] = useState(false);

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="text-sm text-slate-500 italic text-center py-6">No recommendations available.</div>
    );
  }

  const parsed = recommendations.map(parseRecommendation);

  // Group by category, preserving order
  const grouped: Record<string, ParsedRec[]> = {};
  parsed.forEach(rec => {
    if (!grouped[rec.category]) grouped[rec.category] = [];
    grouped[rec.category].push(rec);
  });

  const orderedCategories = CATEGORY_ORDER.filter(c => grouped[c]);

  const handleCopy = async () => {
    const text = recommendations.join('\n');
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Wrench size={16} className="text-green-400" />
          Recommendations
          <span className="text-xs text-slate-500 font-normal">({recommendations.length} steps)</span>
        </h3>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg px-3 py-1.5 transition-all"
        >
          {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
          {copied ? 'Copied!' : 'Copy All'}
        </button>
      </div>

      {/* Category legend */}
      <div className="flex flex-wrap gap-2 text-xs">
        {orderedCategories.map(cat => {
          const cfg = CATEGORY_CONFIG[cat];
          return (
            <span key={cat} className={`flex items-center gap-1.5 ${cfg.color} ${cfg.bg} ${cfg.border} border rounded-full px-2 py-0.5`}>
              {cfg.icon}
              {cfg.label}
            </span>
          );
        })}
      </div>

      {/* Grouped recommendations */}
      <div className="space-y-4">
        {orderedCategories.map(category => {
          const cfg = CATEGORY_CONFIG[category];
          const recs = grouped[category];
          return (
            <div key={category} className={`rounded-xl border ${cfg.border} ${cfg.bg} overflow-hidden`}>
              <div className={`px-4 py-2 border-b ${cfg.border} flex items-center gap-2`}>
                <span className={cfg.color}>{cfg.icon}</span>
                <span className={`text-xs font-bold uppercase tracking-wider ${cfg.color}`}>{cfg.label}</span>
                <span className="text-xs text-slate-500 font-normal ml-auto">{recs.length} item{recs.length !== 1 ? 's' : ''}</span>
              </div>
              <ol className="divide-y divide-slate-700/40">
                {recs.map((rec, i) => (
                  <li key={i} className="flex gap-3 px-4 py-3">
                    <span className={`shrink-0 w-6 h-6 rounded-full ${cfg.bg} ${cfg.border} border flex items-center justify-center text-xs font-bold ${cfg.color}`}>
                      {i + 1}
                    </span>
                    <p className="text-sm text-slate-200 leading-relaxed">{rec.text}</p>
                  </li>
                ))}
              </ol>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RecommendationList;
