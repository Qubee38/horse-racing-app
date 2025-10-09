// frontend/src/hooks/useRaces.ts (修正版)
import { useState, useCallback } from 'react';
import { Race, Horse } from '../types/api';
import { raceService } from '../services/api';

// レース関連の状態管理
interface RaceState {
  races: Race[];                    // レース一覧
  selectedRace: Race | null;        // 選択されたレース
  horses: Horse[];                  // 選択されたレースの出走馬
  loading: boolean;                 // ローディング状態
  error: string | null;            // エラーメッセージ
}

/**
 * レース関連データの状態管理を行うカスタムフック（修正版）
 * - レース一覧の取得
 * - 出走馬一覧の取得  
 * - ローディング・エラー状態の管理
 * - 戻り値の修正（HomePageとの統合改善）
 */
export const useRaces = () => {
  // 状態の初期化
  const [state, setState] = useState<RaceState>({
    races: [],
    selectedRace: null,
    horses: [],
    loading: false,
    error: null,
  });

  /**
   * 指定日のレース一覧を取得（修正版：戻り値を返す）
   */
  const fetchRacesByDate = useCallback(async (date: string): Promise<Race[]> => {
    console.log(`useRaces: Starting fetchRacesByDate for ${date}`);
    
    setState(prev => ({ 
      ...prev,        
      loading: true,  
      error: null     
    }));

    try {
      // APIからレース一覧を取得
      console.log(`useRaces: Calling raceService.getRacesByDate(${date})`);
      const races = await raceService.getRacesByDate(date);
      
      console.log(`useRaces: Received ${Array.isArray(races) ? races.length : 'non-array'} races`);
      console.log('useRaces: Race data:', races);
      
      setState(prev => ({
        ...prev,
        races,           
        loading: false,  
        error: null
      }));

      // 重要：取得したデータを戻り値として返す
      return races;
      
    } catch (error: any) {
      console.error(`useRaces: Error fetching races for ${date}:`, error);
      
      // エラーハンドリング
      setState(prev => ({
        ...prev,
        races: [],
        loading: false,
        error: error.message || 'レース情報の取得に失敗しました'
      }));

      // エラー時は空配列を返す
      return [];
    }
  }, []);

  /**
   * 特定のレースの出走馬一覧を取得（戻り値追加）
   */
  const fetchRaceHorses = useCallback(async (raceId: number): Promise<Horse[]> => {
    console.log(`useRaces: Starting fetchRaceHorses for race ${raceId}`);
    
    setState(prev => ({ 
      ...prev, 
      loading: true, 
      error: null 
    }));

    try {
      const horses = await raceService.getRaceHorses(raceId);
      
      console.log(`useRaces: Received ${Array.isArray(horses) ? horses.length : 'non-array'} horses`);
      
      setState(prev => ({
        ...prev,
        horses,
        loading: false,
        error: null
      }));

      // 取得したデータを戻り値として返す
      return horses;
      
    } catch (error: any) {
      console.error(`useRaces: Error fetching horses for race ${raceId}:`, error);
      
      setState(prev => ({
        ...prev,
        horses: [],
        loading: false,
        error: error.message || '出走馬情報の取得に失敗しました'
      }));

      // エラー時は空配列を返す
      return [];
    }
  }, []);

  /**
   * レースを選択
   */
  const selectRace = useCallback((race: Race) => {
    console.log(`useRaces: Selecting race:`, race);
    setState(prev => ({
      ...prev,
      selectedRace: race,
      horses: []  // 馬一覧をクリア（新しいレースの馬を取得するため）
    }));
  }, []);

  /**
   * エラーをクリア
   */
  const clearError = useCallback(() => {
    console.log('useRaces: Clearing error');
    setState(prev => ({ ...prev, error: null }));
  }, []);

  /**
   * 状態をリセット
   */
  const resetState = useCallback(() => {
    console.log('useRaces: Resetting state');
    setState({
      races: [],
      selectedRace: null,
      horses: [],
      loading: false,
      error: null,
    });
  }, []);

  // デバッグ用：現在の状態をログ出力
  console.log('useRaces current state:', {
    racesCount: state.races.length,
    selectedRace: state.selectedRace?.id || null,
    horsesCount: state.horses.length,
    loading: state.loading,
    hasError: !!state.error
  });

  // フックが返す値と関数
  return {
    // 状態
    races: state.races,
    selectedRace: state.selectedRace,
    horses: state.horses,
    loading: state.loading,
    error: state.error,
    
    // アクション関数
    fetchRacesByDate,
    fetchRaceHorses,
    selectRace,
    clearError,
    resetState,
  };
};