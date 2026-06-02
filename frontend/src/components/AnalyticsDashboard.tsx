import React, { useEffect, useState } from 'react';
import { BarChart2, TrendingUp, AlertTriangle, Cpu, Globe, Zap, RefreshCw, Brain } from 'lucide-react';
import { getAnalyticsSummary, getAnalyticsTrends, getPredictiveInsights } from '../api/client';
import type { AnalyticsSummary, TrendsResponse, PredictiveReport } from '../types';

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-orange-400',
  MEDIUM: 'bg-yellow-400',
  LOW: 'bg-green-400',
};

const SEVERITY_TEXT: Record<string, string> = {
  CRITICAL: 'text-red-400',
  HIGH: 'text-orange-400',
  MEDIUM: 'text-yellow-400',
  LOW: 'text-green-400',
};

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: string | number; icon: React.ElementType; color: string;
}) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-slate-400 text-xs uppercase tracking-wide">{label}</p>
        <p className="text-white text-2xl font-bold">{value}</p>
      </div>
    </div>
  );
}

function BarRow({ label, value, max, colorClass }: {
  label: string; value: number; max: number; colorClass: string;
}) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-2 mb-1">
      <span className="text-slate-400 text-xs w-28 truncate">{label}</span>
      <div className="flex-1 bg-slate-700 rounded-full h-2">
        <div className={`h-2 rounded-full ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-slate-300 text-xs w-8 text-right">{value}</span>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [trends, setTrends] = useState<TrendsResponse | null>(null);
  const [forecast, setForecast] = useState<PredictiveReport | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forecastRegion, setForecastRegion] = useState('');
  const [forecastTech, setForecastTech] = useState('');

  const loadSummary = async () => {
    setLoadingSummary(true);
    setError(null);
    try {
      const [s, t] = await Promise.all([getAnalyticsSummary(), getAnalyticsTrends(30)]);
      setSummary(s);
      setTrends(t);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load analytics');
    } finally {
      setLoadingSummary(false);
    }
  };

  const loadForecast = async () => {
    setLoadingForecast(true);
    try {
      const p = await getPredictiveInsights(forecastRegion || undefined, forecastTech || undefined);
      setForecast(p);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Forecast failed');
    } finally {
      setLoadingForecast(false);
    }
  };

  useEffect(() => { loadSummary(); }, []);

  const severityOrder = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const totalSev = summary ? Object.values(summary.severity_distribution).reduce((a, b) => a + b, 0) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart2 size={22} className="text-blue-400" />
          <h2 className="text-xl font-semibold text-white">Telecom Analytics Dashboard</h2>
        </div>
        <button
          onClick={loadSummary}
          disabled={loadingSummary}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-300 text-sm transition-colors"
        >
          <RefreshCw size={14} className={loadingSummary ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-900/30 border border-red-700 rounded-lg p-3 text-red-300 text-sm">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {loadingSummary && !summary && (
        <div className="text-center py-10 text-slate-400">Loading analytics...</div>
      )}

      {summary && (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="Total Incidents" value={summary.total_incidents.toLocaleString()} icon={BarChart2} color="bg-blue-600" />
            <StatCard label="Critical" value={summary.critical_count} icon={AlertTriangle} color="bg-red-600" />
            <StatCard label="High Severity" value={summary.high_count} icon={Zap} color="bg-orange-600" />
            <StatCard label="Technologies" value={Object.keys(summary.technology_breakdown).length} icon={Cpu} color="bg-purple-600" />
          </div>

          {/* Severity breakdown */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white font-medium mb-3 flex items-center gap-2">
              <AlertTriangle size={16} className="text-yellow-400" /> Severity Distribution
            </h3>
            <div className="flex gap-2 mb-3">
              {severityOrder.map(sev => {
                const count = summary.severity_distribution[sev] ?? 0;
                const pct = totalSev > 0 ? Math.round((count / totalSev) * 100) : 0;
                return (
                  <div key={sev} className="flex-1 text-center">
                    <div className={`h-2 rounded-full mb-1 ${SEVERITY_COLORS[sev] ?? 'bg-slate-500'}`} />
                    <div className={`text-xs font-bold ${SEVERITY_TEXT[sev] ?? 'text-slate-300'}`}>{pct}%</div>
                    <div className="text-xs text-slate-500">{sev}</div>
                    <div className="text-xs text-slate-300">{count}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Technology & Vendor breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <Cpu size={16} className="text-blue-400" /> Technology Breakdown
              </h3>
              {Object.entries(summary.technology_breakdown)
                .sort((a, b) => b[1] - a[1])
                .map(([tech, count]) => (
                  <BarRow key={tech} label={tech} value={count}
                    max={Math.max(...Object.values(summary.technology_breakdown))}
                    colorClass="bg-blue-500" />
                ))}
            </div>
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <Globe size={16} className="text-green-400" /> Vendor Breakdown
              </h3>
              {Object.entries(summary.vendor_breakdown)
                .sort((a, b) => b[1] - a[1])
                .map(([vendor, count]) => (
                  <BarRow key={vendor} label={vendor} value={count}
                    max={Math.max(...Object.values(summary.vendor_breakdown))}
                    colorClass="bg-green-500" />
                ))}
            </div>
          </div>

          {/* Top regions */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white font-medium mb-3 flex items-center gap-2">
              <Globe size={16} className="text-purple-400" /> Top Affected Regions
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {Object.entries(summary.top_regions).slice(0, 10).map(([region, count]) => (
                <div key={region} className="bg-slate-700/50 rounded-lg p-2 text-center">
                  <p className="text-white text-sm font-medium">{count}</p>
                  <p className="text-slate-400 text-xs truncate">{region}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Avg outage duration */}
          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-white font-medium mb-3">Avg Outage Duration (minutes) by Severity</h3>
            <div className="flex gap-4">
              {Object.entries(summary.avg_outage_minutes_by_severity).map(([sev, mins]) => (
                <div key={sev} className="flex-1 text-center bg-slate-700/50 rounded-lg p-3">
                  <p className={`text-lg font-bold ${SEVERITY_TEXT[sev] ?? 'text-white'}`}>{mins}</p>
                  <p className="text-slate-400 text-xs">{sev}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Trend sparkline (simplified text view) */}
      {trends && (
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
          <h3 className="text-white font-medium mb-2 flex items-center gap-2">
            <TrendingUp size={16} className="text-teal-400" />
            Incident Trend — Last 30 Days ({trends.total_in_period} total)
          </h3>
          <div className="flex items-end gap-0.5 h-16">
            {trends.trend_data.slice(-30).map((pt) => {
              const max = Math.max(...trends.trend_data.map(d => d.total), 1);
              const h = Math.round((pt.total / max) * 56);
              const hasC = pt.CRITICAL > 0;
              return (
                <div key={pt.date} title={`${pt.date}: ${pt.total} (${pt.CRITICAL} critical)`}
                  className={`flex-1 rounded-sm ${hasC ? 'bg-red-500' : 'bg-blue-600'}`}
                  style={{ height: `${Math.max(h, 2)}px` }} />
              );
            })}
          </div>
          <p className="text-slate-500 text-xs mt-1">Red = day with critical incidents</p>
        </div>
      )}

      {/* Predictive Intelligence */}
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
        <h3 className="text-white font-medium mb-3 flex items-center gap-2">
          <Brain size={16} className="text-violet-400" /> Predictive Outage Intelligence
        </h3>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            placeholder="Region filter (optional)"
            value={forecastRegion}
            onChange={e => setForecastRegion(e.target.value)}
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm placeholder-slate-500 focus:outline-none focus:border-violet-500"
          />
          <input
            type="text"
            placeholder="Technology filter (optional)"
            value={forecastTech}
            onChange={e => setForecastTech(e.target.value)}
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm placeholder-slate-500 focus:outline-none focus:border-violet-500"
          />
          <button
            onClick={loadForecast}
            disabled={loadingForecast}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-600 rounded-lg text-white text-sm font-medium transition-colors flex items-center gap-2"
          >
            {loadingForecast ? <RefreshCw size={14} className="animate-spin" /> : <Brain size={14} />}
            {loadingForecast ? 'Analysing...' : 'Generate Forecast'}
          </button>
        </div>

        {forecast && (
          <div className="space-y-2">
            <div className="flex gap-4 text-xs text-slate-400 mb-2">
              <span>Incidents analysed: <strong className="text-slate-200">{forecast.analyzed_incidents}</strong></span>
              {forecast.patterns?.hotspots?.[0] && (
                <span>Top hotspot: <strong className="text-orange-300">{forecast.patterns.hotspots[0].region} / {forecast.patterns.hotspots[0].technology}</strong></span>
              )}
            </div>
            <div className="bg-slate-900/60 rounded-lg p-3 text-slate-200 text-sm whitespace-pre-wrap border border-slate-600">
              {forecast.forecast}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
