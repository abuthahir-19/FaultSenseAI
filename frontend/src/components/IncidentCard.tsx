import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Clock, Timer, Tag } from 'lucide-react';
import type { Incident } from '../types';

interface IncidentCardProps {
  incident: Incident;
  rank: number;
}

const SEVERITY_STYLES: Record<string, string> = {
  CRITICAL: 'bg-red-900/60 text-red-300 border-red-700',
  HIGH: 'bg-orange-900/60 text-orange-300 border-orange-700',
  MEDIUM: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
  LOW: 'bg-green-900/60 text-green-300 border-green-700',
};

const SEVERITY_BORDER: Record<string, string> = {
  CRITICAL: 'border-l-red-500',
  HIGH: 'border-l-orange-500',
  MEDIUM: 'border-l-yellow-500',
  LOW: 'border-l-green-500',
};

const IncidentCard: React.FC<IncidentCardProps> = ({ incident, rank }) => {
  const [notesOpen, setNotesOpen] = useState(false);

  const severityStyle = SEVERITY_STYLES[incident.severity?.toUpperCase()] ?? 'bg-slate-700 text-slate-300 border-slate-600';
  const borderColor = SEVERITY_BORDER[incident.severity?.toUpperCase()] ?? 'border-l-slate-500';

  const relevancePct = incident.rrf_score != null
    ? Math.min(100, Math.round(incident.rrf_score * 1000)).toString()
    : null;

  const formatTimestamp = (ts: string) => {
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  };

  return (
    <div className={`bg-slate-800/70 border border-slate-700 border-l-4 ${borderColor} rounded-xl overflow-hidden hover:border-slate-600 transition-colors`}>
      {/* Header */}
      <div className="px-4 pt-4 pb-3 flex flex-wrap items-start gap-2">
        <span className="text-xs font-bold text-slate-500 mr-1">#{rank}</span>

        {/* Severity badge */}
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${severityStyle}`}>
          {incident.severity?.toUpperCase() ?? 'UNKNOWN'}
        </span>

        {/* Metadata chips */}
        <span className="flex items-center gap-1 text-xs bg-slate-700/70 text-slate-300 px-2 py-0.5 rounded-full">
          <Tag size={10} />
          {incident.alarm_id}
        </span>
        <span className="text-xs bg-blue-900/40 text-blue-300 px-2 py-0.5 rounded-full border border-blue-800/50">
          {incident.network_region}
        </span>
        <span className="text-xs bg-violet-900/40 text-violet-300 px-2 py-0.5 rounded-full border border-violet-800/50">
          {incident.technology_type}
        </span>
        <span className="text-xs bg-slate-700/70 text-slate-300 px-2 py-0.5 rounded-full">
          {incident.device_vendor}
        </span>

        {/* Relevance score */}
        {relevancePct !== null && (
          <span className="ml-auto text-xs text-emerald-400 font-medium bg-emerald-900/30 px-2 py-0.5 rounded-full border border-emerald-800/50">
            {relevancePct}% match
          </span>
        )}
      </div>

      {/* Body */}
      <div className="px-4 pb-3">
        <p className="text-sm text-slate-200 leading-relaxed">{incident.incident_description}</p>
      </div>

      {/* Service impact */}
      {incident.service_impact && (
        <div className="px-4 pb-3">
          <p className="text-xs text-slate-400">
            <span className="font-medium text-slate-300">Impact: </span>
            {incident.service_impact}
          </p>
        </div>
      )}

      {/* Collapsible resolution notes */}
      {incident.resolution_notes && (
        <div className="border-t border-slate-700/60">
          <button
            onClick={() => setNotesOpen(v => !v)}
            className="w-full flex items-center justify-between px-4 py-2 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700/30 transition-colors"
          >
            <span className="font-medium">Resolution Notes</span>
            {notesOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {notesOpen && (
            <div className="px-4 pb-3">
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/40 rounded-lg p-3">
                {incident.resolution_notes}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="px-4 py-2 bg-slate-900/30 border-t border-slate-700/60 flex flex-wrap items-center gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1">
          <Clock size={11} />
          {formatTimestamp(incident.timestamp)}
        </span>
        {incident.outage_duration && (
          <span className="flex items-center gap-1">
            <Timer size={11} />
            Duration: {incident.outage_duration}
          </span>
        )}
        {incident.chroma_score != null && (
          <span className="ml-auto">Semantic: {incident.chroma_score.toFixed(3)}</span>
        )}
        {incident.bm25_score != null && (
          <span>BM25: {incident.bm25_score.toFixed(3)}</span>
        )}
      </div>
    </div>
  );
};

export default IncidentCard;
