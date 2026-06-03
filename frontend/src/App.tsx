import React, { useState, useEffect } from 'react';
import { Radio, Activity, AlertCircle, CheckCircle2, RefreshCcw, Database, BarChart2 } from 'lucide-react';
import QueryInput from './components/QueryInput';
import IncidentCard from './components/IncidentCard';
import AgentTrace from './components/AgentTrace';
import RootCausePanel from './components/RootCausePanel';
import RecommendationList from './components/RecommendationList';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ErrorBoundary from './components/ErrorBoundary';
import { getHealth, triggerIngest, getIngestStatus } from './api/client';
import type { QueryResponse, AnalysisResponse, AppMode } from './types';
import type { IngestStatus } from './api/client';

interface HealthState {
  status: string;
  documents_indexed: number;
}

const App: React.FC = () => {
  const [mode, setMode] = useState<AppMode>('query');
  const [isLoading, setIsLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [health, setHealth] = useState<HealthState | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus | null>(null);

  const fetchHealth = async () => {
    try {
      const h = await getHealth();
      setHealth(h);
      setHealthError(false);
    } catch {
      setHealthError(true);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Poll ingest status every 400 ms while ingestion is running
  useEffect(() => {
    if (!ingesting) return;
    let active = true;

    const tick = async () => {
      if (!active) return;
      try {
        const s = await getIngestStatus();
        if (!active) return;
        setIngestStatus(s);
        if (!s.running) {
          setIngesting(false);
          await fetchHealth();
          setTimeout(() => { if (active) setIngestStatus(null); }, 3000);
          return; // stop scheduling
        }
      } catch {
        // ignore transient errors
      }
      if (active) setTimeout(tick, 400);
    };

    // First tick after 400 ms
    const timer = setTimeout(tick, 400);
    return () => { active = false; clearTimeout(timer); };
  }, [ingesting]);

  const handleQueryResult = (result: QueryResponse) => {
    setQueryResult(result);
    setAnalysisResult(null);
    setMode('query');
  };

  const handleAnalysisResult = (result: AnalysisResponse) => {
    setAnalysisResult(result);
    setQueryResult(null);
    setMode('analyze');
  };

  const handleIngest = async () => {
    // Show the progress bar immediately — don't wait for the first poll
    setIngestStatus({
      running: true, step: 'Starting…', step_index: 0, total_steps: 5,
      docs_done: 0, docs_total: 0, percent: 0, last_count: 0, last_error: null,
    });
    setIngesting(true);
    try {
      await triggerIngest();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to start ingestion';
      setIngestStatus(prev => prev ? { ...prev, running: false, step: 'Failed', last_error: msg } : null);
      setIngesting(false);
    }
  };

  const hasResults = (mode === 'query' && queryResult !== null) || (mode === 'analyze' && analysisResult !== null);
  const incidents = mode === 'query' ? (queryResult?.incidents ?? []) : (analysisResult?.retrieved_incidents ?? []);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-600/20 border border-blue-600/30">
              <Radio size={20} className="text-blue-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">TelecomNetworkFaultIntel</h1>
              <p className="text-xs text-slate-500 hidden sm:block">AI-powered telecom fault analysis with RAG + LangGraph agents</p>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-3">

            {/* ── Ingestion progress (replaces health indicator while running) ── */}
            {ingestStatus ? (
              <div className="flex items-center gap-2 min-w-0">
                {/* Progress bar + label */}
                <div className="flex flex-col gap-0.5 min-w-0 max-w-[220px]">
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-xs font-medium truncate ${
                      ingestStatus.last_error   ? 'text-red-400'
                      : ingestStatus.step === 'Complete' ? 'text-emerald-400'
                      : 'text-blue-300'
                    }`}>
                      {ingestStatus.last_error
                        ? 'Ingestion failed'
                        : ingestStatus.step || 'Starting…'}
                    </span>
                    <span className="text-xs text-slate-400 shrink-0">
                      {ingestStatus.percent}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        ingestStatus.last_error   ? 'bg-red-500'
                        : ingestStatus.step === 'Complete' ? 'bg-emerald-500'
                        : 'bg-blue-500'
                      }`}
                      style={{ width: `${ingestStatus.percent}%` }}
                    />
                  </div>
                  {ingestStatus.docs_total > 0 && (
                    <span className="text-[10px] text-slate-500">
                      {ingestStatus.docs_done.toLocaleString()} / {ingestStatus.docs_total.toLocaleString()} docs
                    </span>
                  )}
                </div>
              </div>
            ) : (
              /* ── Static health indicator ── */
              <div className="flex items-center gap-2 text-xs">
                {healthError ? (
                  <span className="flex items-center gap-1.5 text-red-400">
                    <AlertCircle size={13} />
                    <span className="hidden sm:inline">Backend offline</span>
                  </span>
                ) : health ? (
                  <span className="flex items-center gap-1.5 text-emerald-400">
                    <CheckCircle2 size={13} />
                    <span className="hidden sm:inline">{health.documents_indexed.toLocaleString()} docs indexed</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-slate-500">
                    <Activity size={13} className="animate-pulse" />
                    <span className="hidden sm:inline">Connecting…</span>
                  </span>
                )}
              </div>
            )}

            {/* Ingest button */}
            <button
              onClick={handleIngest}
              disabled={ingesting}
              title="Re-ingest data"
              className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              <Database size={16} className={ingesting ? 'animate-pulse' : ''} />
            </button>

            {/* Refresh health */}
            <button
              onClick={fetchHealth}
              disabled={ingesting}
              title="Refresh health"
              className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              <RefreshCcw size={16} />
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Mode tabs — always visible */}
        <div className="flex gap-1 bg-slate-800/50 rounded-xl p-1 w-fit">
          <button
            onClick={() => setMode('query')}
            className={`text-sm px-4 py-2 rounded-lg transition-all font-medium ${
              mode === 'query'
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            Query Mode
          </button>
          <button
            onClick={() => setMode('analyze')}
            className={`text-sm px-4 py-2 rounded-lg transition-all font-medium ${
              mode === 'analyze'
                ? 'bg-violet-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            Deep Analysis
          </button>
          <button
            onClick={() => setMode('dashboard')}
            className={`text-sm px-4 py-2 rounded-lg transition-all font-medium flex items-center gap-1.5 ${
              mode === 'dashboard'
                ? 'bg-teal-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
            }`}
          >
            <BarChart2 size={14} />
            Analytics
          </button>
        </div>

        {/* Analytics Dashboard tab */}
        {mode === 'dashboard' && (
          <ErrorBoundary fallbackLabel="Analytics failed to load">
            <AnalyticsDashboard />
          </ErrorBoundary>
        )}

        {/* Query input */}
        {mode !== 'dashboard' && (
          <div className="flex flex-col items-center gap-2">
            {!hasResults && (
              <div className="text-center mb-4">
                <h2 className="text-2xl font-bold text-white mb-1">Telecom Fault Intelligence</h2>
                <p className="text-slate-400 text-sm max-w-xl">
                  Query your incident knowledge base with natural language. Run deep analysis to get AI-powered root cause, correlation clusters, and remediation steps.
                </p>
              </div>
            )}
            <QueryInput
              onQueryResult={handleQueryResult}
              onAnalysisResult={handleAnalysisResult}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
            />
          </div>
        )}

        {/* Empty state */}
        {mode !== 'dashboard' && !hasResults && !isLoading && (
          <div className="text-center py-12 space-y-4">
            <div className="mx-auto w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center">
              <Radio size={28} className="text-slate-600" />
            </div>
            <div>
              <p className="text-slate-500 text-sm font-medium">No results yet</p>
              <p className="text-slate-600 text-xs mt-1">Enter a fault query above to get started</p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 max-w-2xl mx-auto pt-2">
              {[
                '5G call drops in North region',
                'Ericsson RRU hardware failure',
                'LTE packet loss high severity',
                'Nokia core network outage',
                'Fiber cut service disruption',
              ].map(example => (
                <button
                  key={example}
                  className="text-xs bg-slate-800/70 hover:bg-slate-700 border border-slate-700 text-slate-400 hover:text-slate-200 rounded-full px-3 py-1.5 transition-all"
                  onClick={() => {
                    const ta = document.querySelector('textarea');
                    if (ta) {
                      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
                      nativeInputValueSetter?.call(ta, example);
                      ta.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                  }}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Loading state */}
        {mode !== 'dashboard' && isLoading && (
          <div className="text-center py-12">
            <div className="mx-auto w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
              <Activity size={28} className="text-blue-400 animate-pulse" />
            </div>
            <p className="text-slate-400 text-sm">
              {mode === 'analyze' ? 'Running LangGraph agent pipeline...' : 'Searching incident knowledge base...'}
            </p>
            <p className="text-slate-600 text-xs mt-1">This may take up to 30 seconds for deep analysis</p>
          </div>
        )}

        {/* Results */}
        {mode !== 'dashboard' && !isLoading && hasResults && (
          <div className="space-y-6">
            {/* Query mode results */}
            {mode === 'query' && queryResult && (
              <div className="space-y-4">
                {/* Guardrail warnings */}
                {queryResult.guardrail_warnings && queryResult.guardrail_warnings.length > 0 && (
                  <div className="bg-yellow-900/20 border border-yellow-700/40 rounded-xl p-4 space-y-1">
                    <p className="text-xs font-semibold text-yellow-400">Guardrail Warnings</p>
                    {queryResult.guardrail_warnings.map((w, i) => (
                      <p key={i} className="text-xs text-yellow-300">{w}</p>
                    ))}
                  </div>
                )}

                {/* Root cause suggestion */}
                {queryResult.root_cause_suggestion && (
                  <div className="bg-amber-950/20 border border-amber-700/40 rounded-xl p-4">
                    <p className="text-xs font-semibold text-amber-400 mb-1">Quick Root Cause Suggestion</p>
                    <p className="text-sm text-slate-200">{queryResult.root_cause_suggestion}</p>
                  </div>
                )}

                {/* Results count */}
                <p className="text-xs text-slate-500">
                  {queryResult.total_results} incident{queryResult.total_results !== 1 ? 's' : ''} found for: <span className="text-slate-300 italic">"{queryResult.query}"</span>
                </p>

                {/* Incident cards */}
                <div className="space-y-3">
                  {incidents.map((incident, i) => (
                    <IncidentCard key={incident.alarm_id ?? i} incident={incident} rank={i + 1} />
                  ))}
                </div>

                {incidents.length === 0 && (
                  <div className="text-center py-8 text-slate-500 text-sm">
                    No incidents matched your query and filters.
                  </div>
                )}
              </div>
            )}

            {/* Analysis mode results */}
            {mode === 'analyze' && analysisResult && (
              <div className="space-y-6">
                {/* Agent trace */}
                <div className="bg-slate-900/50 border border-slate-700 rounded-2xl p-5">
                  <AgentTrace
                    trace={analysisResult.reasoning_trace}
                    severityEscalated={analysisResult.severity_escalated}
                  />
                </div>

                {/* Root cause + correlations */}
                <div className="bg-slate-900/50 border border-slate-700 rounded-2xl p-5">
                  <RootCausePanel
                    rootCause={analysisResult.root_cause}
                    serviceImpact={analysisResult.service_impact}
                    correlations={analysisResult.correlated_alarms}
                    escalated={analysisResult.severity_escalated}
                  />
                </div>

                {/* Recommendations */}
                <div className="bg-slate-900/50 border border-slate-700 rounded-2xl p-5">
                  <RecommendationList recommendations={analysisResult.recommendations} />
                </div>

                {/* Retrieved incidents */}
                {incidents.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-sm font-semibold text-slate-400">
                      Retrieved Incidents ({incidents.length})
                    </h3>
                    {incidents.map((incident, i) => (
                      <IncidentCard key={incident.alarm_id ?? i} incident={incident} rank={i + 1} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-600">
        TelecomNetworkFaultIntel — RAG + LangGraph Fault Intelligence Platform
      </footer>
    </div>
  );
};

export default App;
