import React, { useState } from 'react';
import { Search, Zap, Loader2, AlertCircle, SlidersHorizontal } from 'lucide-react';
import { queryIncidents, analyzeIncident } from '../api/client';
import type { QueryResponse, AnalysisResponse, MetadataFilters } from '../types';

interface QueryInputProps {
  onQueryResult: (result: QueryResponse) => void;
  onAnalysisResult: (result: AnalysisResponse) => void;
  isLoading: boolean;
  setIsLoading: (v: boolean) => void;
}

const REGIONS = ['', 'North', 'South', 'East', 'West', 'Central', 'Northeast', 'Northwest', 'Southeast', 'Southwest'];
const SEVERITIES = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const VENDORS = ['', 'Ericsson', 'Nokia', 'Huawei', 'Cisco', 'Juniper', 'ZTE', 'Samsung'];
const TECHNOLOGIES = ['', '5G', '4G LTE', '3G', '2G', 'Fiber', 'Microwave', 'MPLS', 'SDH'];

const QueryInput: React.FC<QueryInputProps> = ({ onQueryResult, onAnalysisResult, isLoading, setIsLoading }) => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<MetadataFilters>({});
  const [topK, setTopK] = useState(10);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const updateFilter = (key: keyof MetadataFilters, value: string) => {
    setFilters(prev => {
      const updated = { ...prev };
      if (value === '') {
        delete updated[key];
      } else {
        updated[key] = value;
      }
      return updated;
    });
  };

  const cleanFilters = (): MetadataFilters | undefined => {
    const cleaned: MetadataFilters = {};
    (Object.keys(filters) as (keyof MetadataFilters)[]).forEach(k => {
      if (filters[k]) cleaned[k] = filters[k];
    });
    return Object.keys(cleaned).length > 0 ? cleaned : undefined;
  };

  const handleQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a query.');
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const result = await queryIncidents({ query: query.trim(), filters: cleanFilters(), top_k: topK });
      onQueryResult(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Query failed. Is the backend running?';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!query.trim()) {
      setError('Please enter a query.');
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const result = await analyzeIncident({ query: query.trim(), filters: cleanFilters(), top_k: topK });
      onAnalysisResult(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Analysis failed. Is the backend running?';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleQuery();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Main query textarea */}
      <div className="relative">
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe the fault or network issue you want to investigate...&#10;e.g. '5G call drops in North region during peak hours' or 'Huawei RRU hardware failure causing service outage'"
          rows={4}
          className="w-full rounded-xl bg-slate-800 border border-slate-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 text-slate-100 placeholder-slate-500 px-4 py-3 text-sm resize-none transition-all outline-none"
          disabled={isLoading}
        />
        <span className="absolute bottom-3 right-3 text-xs text-slate-600">Ctrl+Enter to search</span>
      </div>

      {/* Filter toggle */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setShowFilters(v => !v)}
          className="flex items-center gap-2 text-xs text-slate-400 hover:text-blue-400 transition-colors"
        >
          <SlidersHorizontal size={14} />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
          {Object.keys(filters).length > 0 && (
            <span className="bg-blue-600 text-white rounded-full px-1.5 py-0.5 text-[10px]">
              {Object.keys(filters).length}
            </span>
          )}
        </button>
        <div className="flex items-center gap-2 ml-auto text-xs text-slate-400">
          <label htmlFor="topk">Top K:</label>
          <input
            id="topk"
            type="number"
            min={1}
            max={50}
            value={topK}
            onChange={e => setTopK(Number(e.target.value))}
            className="w-16 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-100 text-xs focus:outline-none focus:border-blue-500"
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Collapsible filters */}
      {showFilters && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 bg-slate-800/50 rounded-xl border border-slate-700">
          <div className="space-y-1">
            <label className="text-xs text-slate-400 font-medium">Region</label>
            <select
              value={filters.network_region ?? ''}
              onChange={e => updateFilter('network_region', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
              disabled={isLoading}
            >
              {REGIONS.map(r => <option key={r} value={r}>{r || 'All Regions'}</option>)}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-slate-400 font-medium">Severity</label>
            <select
              value={filters.severity ?? ''}
              onChange={e => updateFilter('severity', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
              disabled={isLoading}
            >
              {SEVERITIES.map(s => <option key={s} value={s}>{s || 'All Severities'}</option>)}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-slate-400 font-medium">Vendor</label>
            <select
              value={filters.device_vendor ?? ''}
              onChange={e => updateFilter('device_vendor', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
              disabled={isLoading}
            >
              {VENDORS.map(v => <option key={v} value={v}>{v || 'All Vendors'}</option>)}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-slate-400 font-medium">Technology</label>
            <select
              value={filters.technology_type ?? ''}
              onChange={e => updateFilter('technology_type', e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-slate-100 focus:outline-none focus:border-blue-500"
              disabled={isLoading}
            >
              {TECHNOLOGIES.map(t => <option key={t} value={t}>{t || 'All Technologies'}</option>)}
            </select>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleQuery}
          disabled={isLoading || !query.trim()}
          className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-xl px-6 py-3 transition-all text-sm"
        >
          {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
          Quick Search
        </button>
        <button
          onClick={handleAnalyze}
          disabled={isLoading || !query.trim()}
          className="flex-1 flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-xl px-6 py-3 transition-all text-sm"
        >
          {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
          Deep Analysis
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 bg-red-900/30 border border-red-700/50 rounded-xl px-4 py-3 text-red-300 text-sm">
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};

export default QueryInput;
