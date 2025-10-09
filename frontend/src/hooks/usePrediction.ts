// frontend/src/hooks/usePrediction.ts (拡張版)
import { useState, useCallback } from 'react';
import { predictionService } from '../services/api';

interface PredictionProgress {
  totalRaces: number;
  completedRaces: number;
  currentRace?: string;
}

interface PredictionState {
  isRunning: boolean;
  progress: PredictionProgress | null;
  error: string | null;
  batchId: number | null;
}

/**
 * 予測実行の状態管理を行うカスタムフック（拡張版）
 */
export const usePrediction = () => {
  const [state, setState] = useState<PredictionState>({
    isRunning: false,
    progress: null,
    error: null,
    batchId: null,
  });

  /**
   * 日別予測を実行（全レース）
   */
  const executePrediction = useCallback(async (
    date: string, 
    method: 'netkeiba_scraping' | 'database_only' = 'netkeiba_scraping'
  ) => {
    setState({
      isRunning: true,
      progress: { totalRaces: 0, completedRaces: 0 },
      error: null,
      batchId: null,
    });

    try {
      const response = await predictionService.executePrediction({ date, method });
      
      setState(prev => ({
        ...prev,
        batchId: response.batch_id,
      }));

      // ポーリングで進捗確認（簡易版）
      if (response.batch_id) {
        await pollPredictionStatus(response.batch_id);
      }

      setState(prev => ({
        ...prev,
        isRunning: false,
        progress: null,
      }));

    } catch (error: any) {
      setState({
        isRunning: false,
        progress: null,
        error: error.message || '予測の実行に失敗しました',
        batchId: null,
      });
      throw error;
    }
  }, []);

  /**
   * 選択されたレースのみ予測実行（新規）
   */
  const executeSelectedRacesPrediction = useCallback(async (
    date: string, 
    raceIds: string[]
  ) => {
    setState({
      isRunning: true,
      progress: { totalRaces: raceIds.length, completedRaces: 0 },
      error: null,
      batchId: null,
    });

    try {
      console.log(`Executing prediction for ${raceIds.length} selected races`);
      
      const response = await predictionService.executeSelectedRacesPrediction(date, raceIds);
      
      setState(prev => ({
        ...prev,
        batchId: response.batch_id,
      }));

      // ポーリングで進捗確認
      if (response.batch_id) {
        await pollPredictionStatus(response.batch_id, raceIds.length);
      }

      setState(prev => ({
        ...prev,
        isRunning: false,
        progress: null,
      }));

      return response;

    } catch (error: any) {
      setState({
        isRunning: false,
        progress: null,
        error: error.message || '選択レース予測の実行に失敗しました',
        batchId: null,
      });
      throw error;
    }
  }, []);

  /**
   * 予測状況をポーリング
   */
  const pollPredictionStatus = async (batchId: number, expectedTotal?: number) => {
    const maxPolls = 60; // 最大60回（5分）
    let pollCount = 0;

    while (pollCount < maxPolls) {
      try {
        await new Promise(resolve => setTimeout(resolve, 5000)); // 5秒待機
        
        const status = await predictionService.getPredictionStatus(batchId);
        
        setState(prev => ({
          ...prev,
          progress: {
            totalRaces: expectedTotal || status.total_races || 0,
            completedRaces: status.completed_predictions || 0,
            currentRace: `処理中... (${status.completed_predictions}/${status.total_races})`
          }
        }));

        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          break;
        }

        pollCount++;
      } catch (error) {
        console.error('Failed to poll prediction status:', error);
        break;
      }
    }
  };

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
      isRunning: false,
      progress: null,
      error: null,
      batchId: null,
    });
  }, []);

  return {
    isRunning: state.isRunning,
    progress: state.progress,
    error: state.error,
    batchId: state.batchId,
    executePrediction,
    executeSelectedRacesPrediction,
    clearError,
    resetState,
  };
};