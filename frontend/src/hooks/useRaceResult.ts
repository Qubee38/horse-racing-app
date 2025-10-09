// frontend/src/hooks/useRaceResult.ts
import { useState, useCallback } from 'react';
import { RaceResultResponse } from '../types/api';
import { raceResultService } from '../services/api';

interface RaceResultState {
  result: RaceResultResponse | null;
  loading: boolean;
  error: string | null;
  exists: boolean;
  fetching: boolean;  // バックグラウンド取得中
}

/**
 * レース結果の状態管理を行うカスタムフック
 */
export const useRaceResult = () => {
  const [state, setState] = useState<RaceResultState>({
    result: null,
    loading: false,
    error: null,
    exists: false,
    fetching: false,
  });

  /**
   * レース結果が存在するか確認
   */
  const checkResultExists = useCallback(async (raceId: number): Promise<boolean> => {
    try {
      const exists = await raceResultService.checkResultExists(raceId);
      setState(prev => ({ ...prev, exists }));
      return exists;
    } catch (error: any) {
      console.error('Error checking result existence:', error);
      return false;
    }
  }, []);

  /**
   * レース結果を取得してDBに保存
   */
  const fetchRaceResult = useCallback(async (raceId: number): Promise<boolean> => {
    setState(prev => ({ ...prev, fetching: true, error: null }));

    try {
      const response = await raceResultService.fetchRaceResult(raceId);
      
      console.log('Fetch race result response:', response);
      
      setState(prev => ({ 
        ...prev, 
        fetching: false,
        exists: true  // 取得開始したので存在する（または間もなく存在する）
      }));

      return true;
    } catch (error: any) {
      console.error('Error fetching race result:', error);
      setState(prev => ({
        ...prev,
        fetching: false,
        error: error.message || 'レース結果の取得に失敗しました'
      }));
      return false;
    }
  }, []);

  /**
   * 保存済みレース結果を取得
   */
  const getRaceResult = useCallback(async (raceId: number): Promise<void> => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const result = await raceResultService.getRaceResult(raceId);
      
      if (result) {
        // 着順でソート
        const sortedHorseResults = [...result.horse_results].sort((a, b) => {
          if (a.finish_position === null) return 1;
          if (b.finish_position === null) return -1;
          return a.finish_position - b.finish_position;
        });

        setState(prev => ({
          ...prev,
          result: { ...result, horse_results: sortedHorseResults },
          loading: false,
          exists: true
        }));
      } else {
        setState(prev => ({
          ...prev,
          result: null,
          loading: false,
          exists: false
        }));
      }
    } catch (error: any) {
      console.error('Error getting race result:', error);
      setState(prev => ({
        ...prev,
        result: null,
        loading: false,
        error: error.message || 'レース結果の取得に失敗しました'
      }));
    }
  }, []);

  /**
   * エラーをクリア
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  /**
   * 状態をリセット
   */
  const resetState = useCallback(() => {
    setState({
      result: null,
      loading: false,
      error: null,
      exists: false,
      fetching: false,
    });
  }, []);

  return {
    // 状態
    result: state.result,
    loading: state.loading,
    error: state.error,
    exists: state.exists,
    fetching: state.fetching,
    
    // アクション
    checkResultExists,
    fetchRaceResult,
    getRaceResult,
    clearError,
    resetState,
  };
};