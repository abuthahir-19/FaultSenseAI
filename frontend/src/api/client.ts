import axios from 'axios';
import type {
  QueryResponse, AnalysisResponse, MetadataFilters,
  AnalyticsSummary, TrendsResponse, PredictiveReport, EvaluationResult,
} from '../types';

const api = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,
});

export interface QueryPayload {
  query: string;
  filters?: MetadataFilters;
  top_k?: number;
}

export async function queryIncidents(payload: QueryPayload): Promise<QueryResponse> {
  const response = await api.post<QueryResponse>('/api/query', payload);
  return response.data;
}

export async function analyzeIncident(payload: QueryPayload): Promise<AnalysisResponse> {
  const response = await api.post<AnalysisResponse>('/api/analyze', payload);
  return response.data;
}

export async function getHealth(): Promise<{ status: string; documents_indexed: number }> {
  const response = await api.get('/health');
  return response.data;
}

export async function triggerIngest(): Promise<void> {
  await api.post('/api/ingest');
}

export interface IngestStatus {
  running: boolean;
  step: string;
  step_index: number;
  total_steps: number;
  docs_done: number;
  docs_total: number;
  percent: number;
  last_count: number;
  last_error: string | null;
}

export async function getIngestStatus(): Promise<IngestStatus> {
  const response = await api.get<IngestStatus>('/api/ingest/status');
  return response.data;
}

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const response = await api.get<AnalyticsSummary>('/api/analytics/summary');
  return response.data;
}

export async function getAnalyticsTrends(days = 30): Promise<TrendsResponse> {
  const response = await api.get<TrendsResponse>(`/api/analytics/trends?days=${days}`);
  return response.data;
}

export async function getPredictiveInsights(
  region?: string, technology?: string
): Promise<PredictiveReport> {
  const response = await api.post<PredictiveReport>('/api/analytics/predict', {
    region: region || null,
    technology: technology || null,
  });
  return response.data;
}

export async function getSummarize(
  query?: string, region?: string, technology?: string, severity?: string
): Promise<{ incidents_analyzed: number; summary: string }> {
  const response = await api.post('/api/summarize', {
    query: query || null,
    region: region || null,
    technology: technology || null,
    severity: severity || null,
  });
  return response.data;
}

export async function evaluateAnalysis(payload: {
  query: string;
  retrieved_incidents: unknown[];
  root_cause: string;
  recommendations: string[];
}): Promise<EvaluationResult> {
  const response = await api.post<EvaluationResult>('/api/evaluate', payload);
  return response.data;
}
