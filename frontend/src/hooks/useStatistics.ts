// frontend/src/hooks/useStatistics.ts

import { useState, useCallback } from 'react';
import { statisticsService } from '../services/api';
import type { StatisticsSummaryResponse } from '../types/api';

interface UseStatisticsParams {
  start_date?: string;
  end_date?: string;
  win_threshold?: number;
  place_threshold?: number;
}

export const useStatistics = () => {
  const [summary, setSummary] = useState<StatisticsSummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async (params?: UseStatisticsParams) => {
    setLoading(true);
    setError(null);

    try {
      const data = await statisticsService.getSummary(params);
      setSummary(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '統計データの取得に失敗しました';
      setError(errorMessage);
      console.error('統計取得エラー:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDefaultSummary = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await statisticsService.getDefaultSummary();
      setSummary(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '統計データの取得に失敗しました';
      setError(errorMessage);
      console.error('統計取得エラー:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const resetState = useCallback(() => {
    setSummary(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    summary,
    loading,
    error,
    fetchSummary,
    fetchDefaultSummary,
    clearError,
    resetState
  };
};