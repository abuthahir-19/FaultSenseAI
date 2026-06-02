export interface MetadataFilters {
  network_region?: string;
  severity?: string;
  device_vendor?: string;
  technology_type?: string;
}

export interface Incident {
  alarm_id: string;
  incident_description: string;
  network_region: string;
  technology_type: string;
  severity: string;
  outage_duration: string;
  device_vendor: string;
  resolution_notes: string;
  timestamp: string;
  service_impact: string;
  rrf_score?: number;
  chroma_score?: number;
  bm25_score?: number;
}

export interface CorrelationCluster {
  cluster_id: string;
  network_region: string;
  technology_type: string;
  incident_count: number;
  alarm_ids: string[];
  dominant_vendor: string;
  max_severity: string;
  has_critical: boolean;
  time_span_hours?: number;
  summary: string;
}

export interface QueryResponse {
  query: string;
  guardrail_warnings: string[];
  incidents: Incident[];
  root_cause_suggestion: string;
  total_results: number;
}

export interface AnalysisResponse {
  query: string;
  guardrail_result: Record<string, unknown>;
  retrieved_incidents: Incident[];
  correlated_alarms: CorrelationCluster[];
  root_cause: string;
  service_impact: string;
  recommendations: string[];
  reasoning_trace: string[];
  severity_escalated: boolean;
}

export type AppMode = 'query' | 'analyze' | 'dashboard';

export interface AnalyticsSummary {
  total_incidents: number;
  severity_distribution: Record<string, number>;
  technology_breakdown: Record<string, number>;
  vendor_breakdown: Record<string, number>;
  top_regions: Record<string, number>;
  top_service_impacts: Record<string, number>;
  avg_outage_minutes_by_severity: Record<string, number>;
  critical_count: number;
  high_count: number;
}

export interface TrendPoint {
  date: string;
  total: number;
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
}

export interface TrendsResponse {
  days: number;
  trend_data: TrendPoint[];
  total_in_period: number;
}

export interface PredictiveReport {
  analyzed_incidents: number;
  filters_applied: Record<string, string | null>;
  patterns: {
    total_incidents: number;
    severity_distribution: Record<string, number>;
    hotspots: Array<{ region: string; technology: string; incident_count: number }>;
    vendor_failure_patterns: Array<{ vendor: string; technology: string; incident_count: number }>;
    peak_hours: number[];
    peak_days: string[];
  };
  forecast: string;
}

export interface EvaluationResult {
  query: string;
  faithfulness: { faithfulness_score: number; grounding_assessment: string; issues: string[] };
  answer_relevance: { relevance_score: number; relevance_assessment: string; missing_aspects: string[] };
  context_precision: { context_precision_score: number; precision_assessment: string };
  overall_score: number;
  evaluation_summary: string;
}
