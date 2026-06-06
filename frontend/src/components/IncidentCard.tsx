import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Clock, Timer, Tag, MapPin, Cpu, Building2 } from 'lucide-react';
import type { Incident } from '../types';

interface IncidentCardProps {
  incident: Incident;
  rank: number;
}

const SEVERITY_CONFIG: Record<string, {
  badge: string; border: string; glow: string; dot: string; rankBg: string;
}> = {
  CRITICAL: {
    badge:   'bg-red-950/80 text-red-300 border-red-600/60 shadow-red-900/30',
    border:  'border-l-red-500',
    glow:    '0 0 28px rgba(239,68,68,0.13)',
    dot:     'bg-red-500',
    rankBg:  'bg-red-900/30 text-red-400',
  },
  HIGH: {
    badge:   'bg-orange-950/80 text-orange-300 border-orange-600/60 shadow-orange-900/30',
    border:  'border-l-orange-500',
    glow:    '0 0 28px rgba(249,115,22,0.11)',
    dot:     'bg-orange-500',
    rankBg:  'bg-orange-900/30 text-orange-400',
  },
  MEDIUM: {
    badge:   'bg-yellow-950/80 text-yellow-300 border-yellow-600/60 shadow-yellow-900/30',
    border:  'border-l-yellow-500',
    glow:    '0 0 28px rgba(234,179,8,0.09)',
    dot:     'bg-yellow-500',
    rankBg:  'bg-yellow-900/30 text-yellow-400',
  },
  LOW: {
    badge:   'bg-emerald-950/80 text-emerald-300 border-emerald-600/60 shadow-emerald-900/30',
    border:  'border-l-emerald-500',
    glow:    '0 0 28px rgba(34,197,94,0.08)',
    dot:     'bg-emerald-500',
    rankBg:  'bg-emerald-900/30 text-emerald-400',
  },
};

const DEFAULT_CONFIG = {
  badge:  'bg-slate-800 text-slate-300 border-slate-600',
  border: 'border-l-slate-500',
  glow:   'none',
  dot:    'bg-slate-500',
  rankBg: 'bg-slate-800 text-slate-400',
};

const IncidentCard: React.FC<IncidentCardProps> = ({ incident, rank }) => {
  const [notesOpen, setNotesOpen] = useState(false);
  const sev = incident.severity?.toUpperCase() ?? '';
  const cfg = SEVERITY_CONFIG[sev] ?? DEFAULT_CONFIG;

  const relevancePct = incident.rrf_score != null
    ? Math.min(100, Math.round(incident.rrf_score * 1000))
    : null;

  const formatTimestamp = (ts: string) => {
    try { return new Date(ts).toLocaleString(); } catch { return ts; }
  };

  const formatDuration = (raw: string | number): string => {
    const mins = typeof raw === 'number' ? raw : parseFloat(String(raw));
    if (isNaN(mins)) return String(raw);
    if (mins < 1)  return '< 1 min';
    if (mins < 60) return `${Math.round(mins)} min`;
    const h = Math.floor(mins / 60);
    const m = Math.round(mins % 60);
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  };

  return (
    <div
      className={`group relative bg-slate-800/50 backdrop-blur-sm border border-slate-700/80 border-l-4 ${cfg.border}
        rounded-xl overflow-hidden transition-all duration-200
        hover:-translate-y-0.5 hover:border-slate-600/80 hover:bg-slate-800/70`}
      style={{ boxShadow: cfg.glow }}
    >
      {/* Rank badge */}
      <div className={`absolute top-3.5 right-3.5 w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${cfg.rankBg}`}>
        {rank}
      </div>

      {/* Header row */}
      <div className="px-4 pt-4 pb-2 flex flex-wrap items-center gap-2 pr-10">
        {/* Severity */}
        <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-full border shadow-sm ${cfg.badge}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
          {sev || 'UNKNOWN'}
        </span>

        {/* Alarm ID */}
        <span className="flex items-center gap-1 text-xs bg-slate-700/60 text-slate-300 px-2 py-0.5 rounded-full border border-slate-600/40">
          <Tag size={9} className="text-slate-400" />
          {incident.alarm_id}
        </span>

        {/* Region */}
        <span className="flex items-center gap-1 text-xs bg-blue-950/60 text-blue-300 px-2 py-0.5 rounded-full border border-blue-800/40">
          <MapPin size={9} />
          {incident.network_region}
        </span>

        {/* Technology */}
        <span className="flex items-center gap-1 text-xs bg-violet-950/60 text-violet-300 px-2 py-0.5 rounded-full border border-violet-800/40">
          <Cpu size={9} />
          {incident.technology_type}
        </span>

        {/* Vendor */}
        <span className="flex items-center gap-1 text-xs bg-slate-700/60 text-slate-300 px-2 py-0.5 rounded-full border border-slate-600/40">
          <Building2 size={9} className="text-slate-400" />
          {incident.device_vendor}
        </span>
      </div>

      {/* Description */}
      <div className="px-4 pb-2">
        <p className="text-sm text-slate-200 leading-relaxed">{incident.incident_description}</p>
      </div>

      {/* Service impact */}
      {incident.service_impact && (
        <div className="px-4 pb-3">
          <p className="text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Impact: </span>
            {incident.service_impact}
          </p>
        </div>
      )}

      {/* Relevance bar */}
      {relevancePct !== null && (
        <div className="px-4 pb-3 flex items-center gap-2">
          <span className="text-[10px] text-slate-500 font-medium w-14 shrink-0">Relevance</span>
          <div className="flex-1 h-1.5 bg-slate-700/80 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full transition-all duration-500"
              style={{ width: `${relevancePct}%` }}
            />
          </div>
          <span className="text-xs font-semibold text-emerald-400 w-9 text-right">{relevancePct}%</span>
        </div>
      )}

      {/* Resolution notes toggle */}
      {incident.resolution_notes && (
        <div className="border-t border-slate-700/50">
          <button
            onClick={() => setNotesOpen(v => !v)}
            className="w-full flex items-center justify-between px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 transition-colors"
          >
            <span className="font-medium">Resolution Notes</span>
            {notesOpen
              ? <ChevronUp size={13} className="text-slate-500" />
              : <ChevronDown size={13} className="text-slate-500" />}
          </button>
          {notesOpen && (
            <div className="px-4 pb-3">
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 border border-slate-700/50 rounded-lg p-3">
                {incident.resolution_notes}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-2 bg-slate-900/40 border-t border-slate-700/40 flex flex-wrap items-center gap-4 text-[11px] text-slate-500">
        <span className="flex items-center gap-1">
          <Clock size={10} />
          {formatTimestamp(incident.timestamp)}
        </span>
        {incident.outage_duration && (
          <span className="flex items-center gap-1">
            <Timer size={10} />
            {formatDuration(incident.outage_duration)}
          </span>
        )}
        {(incident.chroma_score != null || incident.bm25_score != null) && (
          <span className="ml-auto flex items-center gap-3">
            {incident.chroma_score != null && (
              <span>Semantic <span className="text-slate-400">{incident.chroma_score.toFixed(3)}</span></span>
            )}
            {incident.bm25_score != null && (
              <span>BM25 <span className="text-slate-400">{incident.bm25_score.toFixed(3)}</span></span>
            )}
          </span>
        )}
      </div>
    </div>
  );
};

export default IncidentCard;
