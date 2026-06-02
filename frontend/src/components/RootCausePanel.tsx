import React from 'react';
import { AlertTriangle, Activity, Network, Users, MapPin, Cpu } from 'lucide-react';
import type { CorrelationCluster } from '../types';

interface RootCausePanelProps {
  rootCause: string;
  serviceImpact: string;
  correlations: CorrelationCluster[];
  escalated: boolean;
}

const SEVERITY_BADGE: Record<string, string> = {
  CRITICAL: 'bg-red-900/60 text-red-300 border-red-700',
  HIGH: 'bg-orange-900/60 text-orange-300 border-orange-700',
  MEDIUM: 'bg-yellow-900/60 text-yellow-300 border-yellow-700',
  LOW: 'bg-green-900/60 text-green-300 border-green-700',
};

const RootCausePanel: React.FC<RootCausePanelProps> = ({ rootCause, serviceImpact, correlations, escalated }) => {
  return (
    <div className="space-y-4">
      {/* Root Cause Analysis */}
      <div className={`rounded-xl border-2 p-5 ${escalated
        ? 'border-red-500/60 bg-red-950/20'
        : 'border-amber-600/50 bg-amber-950/10'}`}>
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg shrink-0 ${escalated ? 'bg-red-900/40' : 'bg-amber-900/40'}`}>
            <AlertTriangle size={18} className={escalated ? 'text-red-400' : 'text-amber-400'} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className={`text-sm font-bold mb-2 ${escalated ? 'text-red-300' : 'text-amber-300'}`}>
              Root Cause Analysis
              {escalated && (
                <span className="ml-2 text-xs bg-red-800/60 text-red-200 px-2 py-0.5 rounded-full border border-red-700">
                  ESCALATED
                </span>
              )}
            </h3>
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {rootCause || 'No root cause analysis available.'}
            </p>
          </div>
        </div>
      </div>

      {/* Service Impact */}
      {serviceImpact && (
        <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-blue-900/40 shrink-0">
              <Activity size={18} className="text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-blue-300 mb-2">Service Impact Assessment</h3>
              <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">{serviceImpact}</p>
            </div>
          </div>
        </div>
      )}

      {/* Correlation Clusters */}
      {correlations && correlations.length > 0 && (
        <div className="rounded-xl border border-slate-700 bg-slate-800/50 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <Network size={16} className="text-violet-400" />
            <h3 className="text-sm font-bold text-violet-300">
              Alarm Correlation Clusters
              <span className="ml-2 text-xs text-slate-500 font-normal">({correlations.length} cluster{correlations.length !== 1 ? 's' : ''})</span>
            </h3>
          </div>

          <div className="space-y-3">
            {correlations.map((cluster) => {
              const sevStyle = SEVERITY_BADGE[cluster.max_severity?.toUpperCase()] ?? 'bg-slate-700 text-slate-300 border-slate-600';
              return (
                <div
                  key={cluster.cluster_id}
                  className={`rounded-lg border p-4 space-y-3 ${cluster.has_critical
                    ? 'border-red-800/60 bg-red-950/10'
                    : 'border-slate-700/60 bg-slate-900/30'}`}
                >
                  {/* Cluster header */}
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-slate-400">Cluster {cluster.cluster_id}</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${sevStyle}`}>
                      {cluster.max_severity}
                    </span>
                    {cluster.has_critical && (
                      <span className="text-xs bg-red-900/50 text-red-300 border border-red-700/50 px-2 py-0.5 rounded-full font-medium">
                        CRITICAL
                      </span>
                    )}
                    <span className="ml-auto text-xs text-slate-500">
                      {cluster.incident_count} incident{cluster.incident_count !== 1 ? 's' : ''}
                    </span>
                  </div>

                  {/* Cluster details */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    <div className="flex items-center gap-1.5 text-slate-400">
                      <MapPin size={11} className="text-slate-500" />
                      <span>{cluster.network_region}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-400">
                      <Activity size={11} className="text-slate-500" />
                      <span>{cluster.technology_type}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-400">
                      <Cpu size={11} className="text-slate-500" />
                      <span>{cluster.dominant_vendor}</span>
                    </div>
                    {cluster.time_span_hours != null && (
                      <div className="flex items-center gap-1.5 text-slate-400">
                        <Users size={11} className="text-slate-500" />
                        <span>{cluster.time_span_hours.toFixed(1)}h span</span>
                      </div>
                    )}
                  </div>

                  {/* Summary */}
                  <p className="text-xs text-slate-300 leading-relaxed">{cluster.summary}</p>

                  {/* Alarm IDs */}
                  {cluster.alarm_ids && cluster.alarm_ids.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {cluster.alarm_ids.slice(0, 8).map(id => (
                        <span key={id} className="text-[10px] bg-slate-700/70 text-slate-400 px-1.5 py-0.5 rounded font-mono">
                          {id}
                        </span>
                      ))}
                      {cluster.alarm_ids.length > 8 && (
                        <span className="text-[10px] text-slate-500 px-1.5 py-0.5">
                          +{cluster.alarm_ids.length - 8} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default RootCausePanel;
