import React, { useState, useEffect, useRef } from 'react';
import { Radio, Activity, AlertCircle, CheckCircle2, RefreshCcw, Database, BarChart2 } from 'lucide-react';
import StatusDisplay from './components/StatusDisplay';
import type { StatusStep } from './components/StatusDisplay';
import QueryInput from './components/QueryInput';
import IncidentCard from './components/IncidentCard';
import AgentTrace from './components/AgentTrace';
import RootCausePanel from './components/RootCausePanel';
import RecommendationList from './components/RecommendationList';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import ErrorBoundary from './components/ErrorBoundary';
import EvaluationPanel from './components/EvaluationPanel';
import GuardrailPanel from './components/GuardrailPanel';
import { getHealth, triggerIngest, getIngestStatus, evaluateAnalysis } from './api/client';
import type { QueryResponse, AnalysisResponse, AppMode, EvaluationResult } from './types';
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
  const [evalResult, setEvalResult] = useState<EvaluationResult | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [statusStep, setStatusStep] = useState(-1);
  const statusTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const QUERY_STEPS: StatusStep[] = [
    { emoji: '🛡', label: 'Guardrail Validation',        sublabel: 'Input length · Injection detection · Telecom relevance' },
    { emoji: '🔍', label: 'Hybrid Search',               sublabel: 'ChromaDB semantic + BM25 keyword search' },
    { emoji: '🔀', label: 'RRF Fusion',                  sublabel: 'Reciprocal Rank Fusion (k=60) · Re-ranking results' },
    { emoji: '💡', label: 'Root Cause Suggestion',       sublabel: 'GPT-4o quick analysis on top incidents' },
  ];

  const ANALYSIS_STEPS: StatusStep[] = [
    { emoji: '🛡', label: 'Guardrail Validation',        sublabel: 'Input length · Injection detection · Telecom relevance' },
    { emoji: '🔍', label: 'Alarm Retrieval Agent',       sublabel: 'Hybrid RAG search · RRF fusion · Severity escalation check' },
    { emoji: '🔗', label: 'Cross-Correlation Agent',     sublabel: 'Clustering by region + technology · Dominant vendor' },
    { emoji: '🧠', label: 'Root Cause Analysis Agent',   sublabel: 'GPT-4o chain-of-thought · Grounded in alarm IDs' },
    { emoji: '📡', label: 'Service Impact Agent',        sublabel: 'Blast radius · SLA breach risk · Cascading failures' },
    { emoji: '🛠', label: 'Resolution Agent',            sublabel: 'Structured JSON · IMMEDIATE / DIAGNOSTIC / PREVENTIVE' },
  ];

  // Advance step indicators while API call is in flight
  useEffect(() => {
    statusTimers.current.forEach(clearTimeout);
    statusTimers.current = [];

    if (!isLoading) {
      const t = setTimeout(() => setStatusStep(-1), 1800);
      statusTimers.current = [t];
      return () => clearTimeout(t);
    }

    setStatusStep(0);
    const delays = mode === 'analyze'
      ? [1200, 3600, 5800, 10500, 15000]   // cumulative ms for steps 1-5
      : [800,  1800, 3000];                 // cumulative ms for steps 1-3

    const timers = delays.map((delay, i) =>
      setTimeout(() => setStatusStep(i + 1), delay)
    );
    statusTimers.current = timers;
    return () => timers.forEach(clearTimeout);
  }, [isLoading]); // eslint-disable-line react-hooks/exhaustive-deps

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
    document.title = 'FaultSense — Telecom Network Intelligence';
  }, []);

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
    setEvalResult(null);
    setMode('query');
  };

  const handleAnalysisResult = async (result: AnalysisResponse) => {
    setAnalysisResult(result);
    setQueryResult(null);
    setEvalResult(null);
    setMode('analyze');
    // Auto-run DeepEval metrics right after analysis
    setEvalLoading(true);
    try {
      const ev = await evaluateAnalysis({
        query: result.query,
        retrieved_incidents: result.retrieved_incidents,
        root_cause: result.root_cause,
        recommendations: result.recommendations,
      });
      setEvalResult(ev);
    } catch {
      // evaluation failure is non-critical — analysis results are still shown
    } finally {
      setEvalLoading(false);
    }
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

      {/* Ambient background glows */}
      <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-blue-600/6 rounded-full blur-3xl" />
        <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] bg-violet-600/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-teal-600/4 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/70 backdrop-blur-xl sticky top-0 z-10">
        {/* Gradient accent line */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/40 to-transparent" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 relative flex items-center">

          {/* ── Left: brand ── */}
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-600/30 to-violet-600/20 border border-blue-500/30 shadow-lg shadow-blue-900/20">
              <Radio size={18} className="text-blue-400" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight">
                <span className="bg-gradient-to-r from-blue-400 to-blue-300 bg-clip-text text-transparent">Fault</span>
                <span className="text-white">Sense</span>
                <span className="ml-1.5 text-[11px] font-semibold text-slate-500 align-middle">AI</span>
              </h1>
              <p className="text-xs text-slate-500 hidden lg:block">Telecom Network Intelligence · RAG + LangGraph</p>
            </div>
          </div>

          {/* ── Centre: mode navigation tabs — absolutely centred ── */}
          <nav className="hidden md:flex items-center gap-1 absolute left-1/2 -translate-x-1/2 bg-slate-800/60 border border-slate-700/50 rounded-xl p-1">
            <button
              onClick={() => setMode('query')}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all ${
                mode === 'query'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-900/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/60'
              }`}
            >
              Query Mode
            </button>
            <button
              onClick={() => setMode('analyze')}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg transition-all ${
                mode === 'analyze'
                  ? 'bg-gradient-to-r from-violet-600 to-violet-500 text-white shadow-lg shadow-violet-900/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/60'
              }`}
            >
              Deep Analysis
            </button>
            <button
              onClick={() => setMode('dashboard')}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg flex items-center gap-1.5 transition-all ${
                mode === 'dashboard'
                  ? 'bg-gradient-to-r from-teal-600 to-teal-500 text-white shadow-lg shadow-teal-900/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/60'
              }`}
            >
              <BarChart2 size={13} />
              Analytics
            </button>
            <button
              onClick={() => setMode('evaluate')}
              className={`px-4 py-1.5 text-sm font-medium rounded-lg flex items-center gap-1.5 transition-all ${
                mode === 'evaluate'
                  ? 'bg-gradient-to-r from-violet-600 to-purple-500 text-white shadow-lg shadow-violet-900/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/60'
              }`}
            >
              Evaluation
              {(evalLoading || evalResult) && (
                <span className={`w-2 h-2 rounded-full shrink-0 ${evalLoading ? 'bg-yellow-400 animate-pulse' : 'bg-violet-300'}`} />
              )}
            </button>
          </nav>

          {/* ── Right: status + action buttons ── */}
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

        {/* Mobile-only tab bar (navbar tabs hidden on small screens) */}
        <div className="flex md:hidden gap-1 bg-slate-800/50 rounded-xl p-1 w-fit flex-wrap">
          <button onClick={() => setMode('query')}    className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-all ${mode === 'query'    ? 'bg-blue-600 text-white'   : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'}`}>Query</button>
          <button onClick={() => setMode('analyze')}  className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-all ${mode === 'analyze'  ? 'bg-violet-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'}`}>Analysis</button>
          <button onClick={() => setMode('dashboard')} className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-all ${mode === 'dashboard'? 'bg-teal-600 text-white'   : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'}`}>Analytics</button>
          <button onClick={() => setMode('evaluate')} className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-all flex items-center gap-1 ${mode === 'evaluate' ? 'bg-violet-600 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'}`}>
            Eval{(evalLoading || evalResult) && <span className={`w-1.5 h-1.5 rounded-full ${evalLoading ? 'bg-yellow-400 animate-pulse' : 'bg-violet-400'}`} />}
          </button>
        </div>

        {/* Analytics Dashboard tab */}
        {mode === 'dashboard' && (
          <ErrorBoundary fallbackLabel="Analytics failed to load">
            <AnalyticsDashboard />
          </ErrorBoundary>
        )}

        {/* Evaluation tab */}
        {mode === 'evaluate' && (
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold text-slate-200">RAG Evaluation Metrics</h2>
              {analysisResult && (
                <span className="text-xs text-slate-500 bg-slate-800 px-2.5 py-1 rounded-full">
                  Query: <span className="text-slate-300 italic">"{analysisResult.query}"</span>
                </span>
              )}
            </div>
            {!analysisResult ? (
              <div className="text-center py-16 space-y-3">
                <div className="mx-auto w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center">
                  <BarChart2 size={24} className="text-slate-600" />
                </div>
                <p className="text-slate-500 text-sm">No evaluation data yet</p>
                <p className="text-slate-600 text-xs">Run a Deep Analysis first — evaluation metrics will appear here automatically.</p>
              </div>
            ) : (
              <EvaluationPanel result={evalResult} loading={evalLoading} />
            )}
          </div>
        )}

        {/* Query input */}
        {mode !== 'dashboard' && mode !== 'evaluate' && (
          <div className="flex flex-col items-center gap-2">
            {!hasResults && (
              <div className="text-center mb-6">
                <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent mb-2 tracking-tight">
                  FaultSense AI
                </h2>
                <p className="text-slate-400 text-sm max-w-xl leading-relaxed">
                  Query your incident knowledge base with natural language. Run deep analysis to get
                  AI-powered root cause, correlation clusters, and remediation steps.
                </p>
              </div>
            )}
            <QueryInput
              onQueryResult={handleQueryResult}
              onAnalysisResult={handleAnalysisResult}
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              mode={mode}
            />
          </div>
        )}

        {/* Empty state */}
        {mode !== 'dashboard' && mode !== 'evaluate' && !hasResults && !isLoading && (
          <div className="text-center py-10 space-y-8">
            {/* Glowing orb */}
            <div className="relative mx-auto w-24 h-24">
              <div className="absolute inset-0 rounded-full bg-blue-500/20 blur-2xl animate-pulse" />
              <div className="absolute inset-3 rounded-full bg-blue-500/10 blur-xl animate-pulse" style={{ animationDelay: '0.4s' }} />
              <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700/80 flex items-center justify-center shadow-2xl">
                <Radio size={36} className="text-blue-400" />
              </div>
            </div>

            <div className="space-y-1.5">
              <p className="text-slate-300 text-sm font-semibold">Ready to analyse faults</p>
              <p className="text-slate-600 text-xs">Type a fault description above, or try one of these examples:</p>
            </div>

            {/* Example chips */}
            <div className="flex flex-wrap justify-center gap-2 max-w-2xl mx-auto">
              {[
                { label: '5G call drops in North region',  emoji: '📡' },
                { label: 'Ericsson RRU hardware failure',  emoji: '🏭' },
                { label: 'LTE packet loss high severity',  emoji: '⚠️' },
                { label: 'Nokia core network outage',      emoji: '🔴' },
                { label: 'Fiber cut service disruption',   emoji: '✂️' },
              ].map(({ label, emoji }) => (
                <button
                  key={label}
                  className="flex items-center gap-1.5 text-xs bg-slate-800/70 hover:bg-slate-700/80 border border-slate-700 hover:border-blue-600/50 text-slate-400 hover:text-slate-200 rounded-full px-4 py-2 transition-all hover:shadow-[0_0_14px_rgba(37,99,235,0.18)]"
                  onClick={() => {
                    const ta = document.querySelector('textarea');
                    if (ta) {
                      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
                      setter?.call(ta, label);
                      ta.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                  }}
                >
                  <span>{emoji}</span> {label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Loading state — animated step-by-step status */}
        {mode !== 'dashboard' && mode !== 'evaluate' && isLoading && (
          <StatusDisplay
            steps={mode === 'analyze' ? ANALYSIS_STEPS : QUERY_STEPS}
            activeStep={Math.min(statusStep, (mode === 'analyze' ? ANALYSIS_STEPS : QUERY_STEPS).length - 1)}
            done={false}
            mode={mode === 'analyze' ? 'analyze' : 'query'}
          />
        )}

        {/* Results */}
        {mode !== 'dashboard' && mode !== 'evaluate' && !isLoading && hasResults && (
          <div className="space-y-6">
            {/* Query mode results */}
            {mode === 'query' && queryResult && (
              <div className="space-y-4">
                {/* Guardrail panel — always shown; uses real guardrail_result from backend */}
                <GuardrailPanel result={queryResult.guardrail_result} />

                {/* Only show search results when the guardrail passed */}
                {queryResult.guardrail_result.valid && (
                  <>
                    {/* Root cause suggestion */}
                    {queryResult.root_cause_suggestion && (
                      <div className="bg-amber-950/20 border border-amber-700/40 rounded-xl p-4">
                        <p className="text-xs font-semibold text-amber-400 mb-1">Quick Root Cause Suggestion</p>
                        <p className="text-sm text-slate-200">{queryResult.root_cause_suggestion}</p>
                      </div>
                    )}

                    {/* Results count */}
                    <p className="text-xs text-slate-500">
                      {queryResult.total_results} incident{queryResult.total_results !== 1 ? 's' : ''} found for:{' '}
                      <span className="text-slate-300 italic">"{queryResult.query}"</span>
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
                  </>
                )}
              </div>
            )}

            {/* Analysis mode results */}
            {mode === 'analyze' && analysisResult && (
              <div className="space-y-6">
                {/* Guardrail validation — always shown */}
                <GuardrailPanel result={analysisResult.guardrail_result} />

                {/* Only show pipeline results when the guardrail passed */}
                {analysisResult.guardrail_result.valid && (
                  <>
                    {/* Agent trace */}
                    <div className="bg-slate-900/60 backdrop-blur-sm border border-slate-700/80 rounded-2xl p-5 shadow-xl">
                      <AgentTrace
                        trace={analysisResult.reasoning_trace}
                        severityEscalated={analysisResult.severity_escalated}
                      />
                    </div>

                    {/* Root cause + correlations */}
                    <div className="bg-slate-900/60 backdrop-blur-sm border border-slate-700/80 rounded-2xl p-5 shadow-xl">
                      <RootCausePanel
                        rootCause={analysisResult.root_cause}
                        serviceImpact={analysisResult.service_impact}
                        correlations={analysisResult.correlated_alarms}
                        escalated={analysisResult.severity_escalated}
                      />
                    </div>

                    {/* Recommendations */}
                    <div className="bg-slate-900/60 backdrop-blur-sm border border-slate-700/80 rounded-2xl p-5 shadow-xl">
                      <RecommendationList recommendations={analysisResult.recommendations} />
                    </div>

                    {/* Retrieved incidents */}
                    {incidents.length > 0 && (
                      <div className="space-y-3">
                        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-400">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                          Retrieved Incidents
                          <span className="text-xs font-normal text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">{incidents.length}</span>
                        </h3>
                        {incidents.map((incident, i) => (
                          <IncidentCard key={incident.alarm_id ?? i} incident={incident} rank={i + 1} />
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-4 text-center text-xs text-slate-600">
        <span className="bg-gradient-to-r from-blue-500/60 to-violet-500/60 bg-clip-text text-transparent font-medium">FaultSense AI</span>
        {' '}— Telecom Network Intelligence · RAG + LangGraph
      </footer>
    </div>
  );
};

export default App;
