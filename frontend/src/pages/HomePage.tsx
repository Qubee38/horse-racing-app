// frontend/src/pages/HomePage.tsx (Phase1修正版)

import React, { useEffect, useState, useCallback } from 'react';
import { Play, Calendar, ChevronDown, ChevronUp, RefreshCw, Sparkles, Settings, CheckCircle, TrendingUp, Download } from 'lucide-react';
import Header from '../components/common/Header';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import Modal from '../components/common/Modal';
import RaceList from '../components/race/RaceList';
import DatePicker from '../components/race/DatePicker';
import RaceSelector from '../components/race/RaceSelector';
import { AICommentary } from '../components/race/AICommentary';
import { useRaces } from '../hooks/useRaces';
import { usePrediction } from '../hooks/usePrediction';
import { Race, Horse, RaceResultResponse, BatchFetchRaceResultsResponse } from '../types/api';
import { raceService } from '../services/api';
import { getDateString } from '../utils/dateUtils';
import { DailyROIStats } from '../components/race/DailyROIStats';
import { raceResultService } from '../services/api';
import { useThreshold } from '../contexts/ThresholdContext';

interface HomePageProps {
  onRaceSelect: (race: Race, allRaces?: Race[]) => void; // 修正: allRacesを渡せるように
  onGoToAdmin?: () => void;
  onGoToStatistics?: () => void;
}

interface RaceDayPanel {
  date: string;
  displayDate: string;
  races: Race[];
  isExpanded: boolean;
  isLoading: boolean;
  hasError: boolean;
  raceCount: number;
  showAICommentary: boolean;
  aiCommentaryLoading: boolean;
  cachedAICommentary?: any;
  raceResults: Map<number, RaceResultResponse>;
  horsesMap: Map<number, Horse[]>;
  batchFetching: boolean;
  batchFetchProgress: string;
}

interface RaceOption {
  netkeiba_race_id: string;
  race_number: number;
  race_name: string;
  venue: string;
  start_time: string;
  distance: number;
}

// キャッシュの保存・読み込み用ヘルパー関数
const AI_COMMENTARY_CACHE_KEY = 'ai_commentary_cache';

const saveCommentaryToCache = (date: string, commentary: any) => {
  try {
    const cache = JSON.parse(localStorage.getItem(AI_COMMENTARY_CACHE_KEY) || '{}');
    cache[date] = {
      commentary,
      timestamp: Date.now()
    };
    localStorage.setItem(AI_COMMENTARY_CACHE_KEY, JSON.stringify(cache));
  } catch (error) {
    console.error('Failed to save commentary to cache:', error);
  }
};

const loadCommentaryFromCache = (date: string): any | null => {
  try {
    const cache = JSON.parse(localStorage.getItem(AI_COMMENTARY_CACHE_KEY) || '{}');
    const cached = cache[date];
    
    if (!cached) return null;
    
    const CACHE_EXPIRY = 7 * 24 * 60 * 60 * 1000; // 7日
    if (Date.now() - cached.timestamp > CACHE_EXPIRY) {
      return null;
    }
    
    return cached.commentary;
  } catch (error) {
    console.error('Failed to load commentary from cache:', error);
    return null;
  }
};

const HomePage: React.FC<HomePageProps> = ({ onRaceSelect, onGoToAdmin, onGoToStatistics }) => {
  const { fetchRacesByDate } = useRaces();
  const { winThreshold, placeThreshold } = useThreshold();
  
  const { 
    isRunning: predictionRunning, 
    executeSelectedRacesPrediction,
    progress,
    error: predictionError,
    clearError: clearPredictionError
  } = usePrediction();

  const [showDatePicker, setShowDatePicker] = useState(false);
  const [currentDate, setCurrentDate] = useState<string>('');
  const [raceDayPanels, setRaceDayPanels] = useState<RaceDayPanel[]>([]);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [isLoadingDates, setIsLoadingDates] = useState(false);
  const [datesError, setDatesError] = useState<string | null>(null);
  
  const [showRaceSelector, setShowRaceSelector] = useState(false);
  const [selectedDateForPrediction, setSelectedDateForPrediction] = useState<string>('');
  const [availableRacesForSelection, setAvailableRacesForSelection] = useState<RaceOption[]>([]);
  const [loadingRacesForSelection, setLoadingRacesForSelection] = useState(false);
  // === HomePage コンポーネント内に追加する state ===
  const [showBatchFetchConfirm, setShowBatchFetchConfirm] = useState<string | null>(null);

  const handleHomeClick = () => {
    window.location.reload();
  };

  // レース結果とホースデータを一緒に取得
  const loadRacesForDate = useCallback(async (date: string) => {
    try {
      setRaceDayPanels(prev => prev.map(panel => 
        panel.date === date 
          ? { ...panel, isLoading: true, hasError: false }
          : panel
      ));

      const raceData = await fetchRacesByDate(date);
      
      const raceResults = new Map<number, RaceResultResponse>();
      const horsesMap = new Map<number, Horse[]>();
      
      for (const race of raceData) {
        try {
          const horsesResponse = await raceService.getRaceHorses(race.id);
          horsesMap.set(race.id, horsesResponse);
        } catch (e) {
          console.warn(`Failed to load horses for race ${race.id}`);
        }
        
        try {
          const resultExists = await raceResultService.checkResultExists(race.id);
          if (resultExists) {
            const result = await raceResultService.getRaceResult(race.id);
            if (result) {
              raceResults.set(race.id, result);
            }
          }
        } catch (e) {
          console.warn(`Failed to load result for race ${race.id}`);
        }
      }
      
      setRaceDayPanels(prev => prev.map(panel => 
        panel.date === date 
          ? { 
              ...panel, 
              races: raceData,
              raceCount: raceData.length,
              isLoading: false,
              hasError: false,
              raceResults,
              horsesMap
            }
          : panel
      ));

    } catch (error: any) {
      setRaceDayPanels(prev => prev.map(panel => 
        panel.date === date 
          ? { ...panel, isLoading: false, hasError: true, raceCount: 0 }
          : panel
      ));
    }
  }, [fetchRacesByDate]);

  // === 修正: デフォルトで閉じた状態に変更 ===
  const loadAvailableRaceDates = useCallback(async () => {
    setIsLoadingDates(true);
    setDatesError(null);
    
    try {
      const response = await raceService.getAvailableRaceDates(30, true);
      const datesWithCount = response.dates;
      
      setAvailableDates(datesWithCount.map(d => d.date));
      
      const panels: RaceDayPanel[] = datesWithCount.map((dateInfo) => ({
        date: dateInfo.date,
        displayDate: formatDisplayDate(dateInfo.date),
        races: [],
        isExpanded: false, // ← 修正: すべてfalseに変更（デフォルトで閉じる）
        isLoading: false,
        hasError: false,
        raceCount: dateInfo.race_count,
        showAICommentary: false,
        aiCommentaryLoading: false,
        cachedAICommentary: loadCommentaryFromCache(dateInfo.date),
        raceResults: new Map(),
        horsesMap: new Map(),
        batchFetching: false,  // 追加
        batchFetchProgress: '',  // 追加
      }));
      
      setRaceDayPanels(panels);
      
      // 最初の日付のデータも自動では読み込まない（ユーザーが開いたときに読み込む）
      
    } catch (error: any) {
      setDatesError(error.message || 'レース開催日の取得に失敗しました');
    } finally {
      setIsLoadingDates(false);
    }
  }, []);

  useEffect(() => {
    const today = getDateString(0);
    setCurrentDate(today);
    loadAvailableRaceDates();
  }, [loadAvailableRaceDates]);

  const formatDisplayDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr + 'T00:00:00');
      const weekdays = ['日', '月', '火', '水', '木', '金', '土'];
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const day = date.getDate();
      const weekday = weekdays[date.getDay()];
      
      return `${year}年${month}月${day}日(${weekday})`;
    } catch (error) {
      return dateStr;
    }
  };

  const handlePredictionClick = () => {
    clearPredictionError();
    setShowDatePicker(true);
  };

  const handleDateSelect = (selectedDate: string) => {
    setCurrentDate(selectedDate);
    setSelectedDateForPrediction(selectedDate);
  };

  const handleDateConfirm = async (selectedDate: string) => {
    try {
      setShowDatePicker(false);
      setSelectedDateForPrediction(selectedDate);
      setLoadingRacesForSelection(true);
      setShowRaceSelector(true);
      
      const response = await raceService.getNetkeibaRacesForDate(selectedDate);
      
      const raceOptions: RaceOption[] = response.races.map(race => ({
        netkeiba_race_id: race.netkeiba_race_id,
        race_number: race.race_number,
        race_name: race.race_name,
        venue: race.venue,
        start_time: race.start_time || '未定',
        distance: race.distance || 0
      })).sort((a, b) => a.race_number - b.race_number);
      
      setAvailableRacesForSelection(raceOptions);
      setLoadingRacesForSelection(false);
      
    } catch (error: any) {
      setLoadingRacesForSelection(false);
      setShowRaceSelector(false);
      alert(`レース一覧の取得に失敗しました: ${error.message}`);
    }
  };

  const handleExecuteSelectedRacesPrediction = async (selectedRaceIds: string[]) => {
    try {
      setShowRaceSelector(false);
      
      await executeSelectedRacesPrediction(selectedDateForPrediction, selectedRaceIds);
      
      await loadRacesForDate(selectedDateForPrediction);
      await loadAvailableRaceDates();
      
      alert(`${selectedRaceIds.length}レースの予測が完了しました!`);
      
    } catch (error: any) {
      alert(`予測の実行に失敗しました: ${error.message}`);
    }
  };

  const togglePanel = async (date: string) => {
    const panel = raceDayPanels.find(p => p.date === date);
    
    if (panel && !panel.isExpanded && panel.races.length === 0 && !panel.isLoading) {
      await loadRacesForDate(date);
    }
    
    setRaceDayPanels(prev => prev.map(panel => 
      panel.date === date 
        ? { ...panel, isExpanded: !panel.isExpanded }
        : panel
    ));
  };

  const toggleAICommentary = (date: string) => {
    setRaceDayPanels(prev => prev.map(panel => 
      panel.date === date 
        ? { ...panel, showAICommentary: !panel.showAICommentary }
        : panel
    ));
  };

  const handleCommentaryLoaded = (date: string, commentary: any) => {
    setRaceDayPanels(prev => prev.map(panel => 
      panel.date === date 
        ? { ...panel, cachedAICommentary: commentary }
        : panel
    ));
    
    saveCommentaryToCache(date, commentary);
  };

  const handleRaceClick = (race: Race) => {
    // 修正: 同じ日付のレース一覧を取得して渡す
    const panel = raceDayPanels.find(p => p.races.some(r => r.id === race.id));
    const allRacesForDate = panel?.races || [];
    onRaceSelect(race, allRacesForDate);
  };

  const handleGoToAdmin = () => {
    if (onGoToAdmin) {
      onGoToAdmin();
    }
  };

  const handleRetry = (date: string) => {
    loadRacesForDate(date);
  };

  const handleRefreshDates = () => {
    loadAvailableRaceDates();
  };

  // === 追加: 結果取得済みかどうかを判定 ===
  const hasResultsForDate = (panel: RaceDayPanel): boolean => {
    return panel.raceResults.size > 0;
  };

  // === 追加: 高確率馬が存在するかを判定 ===
  const hasHighProbabilityHorse = (panel: RaceDayPanel): boolean => {
    const horsesArrays = Array.from(panel.horsesMap.values());
    for (const horses of horsesArrays) {
      const hasHighWin = horses.some((h: Horse) => (h.win_probability || 0) >= winThreshold);
      const hasHighPlace = horses.some((h: Horse) => (h.place_probability || 0) >= placeThreshold);
      if (hasHighWin || hasHighPlace) return true;
    }
    return false;
  };

  // === 一括取得関連の関数 ===

  /**
   * 一括取得対象レース数を取得
   */
  const getBatchFetchTargetCount = async (date: string, races: Race[]): Promise<{
    targetCount: number;
    skippedCount: number;
  }> => {
    let targetCount = 0;
    let skippedCount = 0;
    
    for (const race of races) {
      const horses = await raceService.getRaceHorses(race.id);
      const hasPrediction = horses.some(h => h.win_probability !== undefined && h.win_probability !== null);
      
      if (hasPrediction) {
        const exists = await raceResultService.checkResultExists(race.id);
        if (exists) {
          skippedCount++;
        } else {
          targetCount++;
        }
      }
    }
    
    return { targetCount, skippedCount };
  };

  /**
   * 一括取得ボタンクリック
   */
  const handleBatchFetchClick = async (date: string, races: Race[]) => {
    try {
      setRaceDayPanels(prev => prev.map(panel => 
        panel.date === date 
          ? { ...panel, batchFetching: true, batchFetchProgress: '対象レースを確認中...' }
          : panel
      ));
      
      const { targetCount, skippedCount } = await getBatchFetchTargetCount(date, races);
      
      setRaceDayPanels(prev => prev.map(panel => 
        panel.date === date 
          ? { ...panel, batchFetching: false, batchFetchProgress: '' }
          : panel
      ));
      
      if (targetCount === 0 && skippedCount > 0) {
        alert('このレース日のレース結果は全て取得済みです');
        return;
      }
      
      if (targetCount === 0 && skippedCount === 0) {
        alert('予測結果があるレースがありません');
        return;
      }
      
      setShowBatchFetchConfirm(date);
      
    } catch (error: any) {
      setRaceDayPanels(prev => prev.map(panel => 
        panel.date === date 
          ? { ...panel, batchFetching: false, batchFetchProgress: '' }
          : panel
      ));
      alert(`エラー: ${error.message}`);
    }
  };

  /**
   * 一括取得実行
   */
  const executeBatchFetch = async (date: string) => {
    setShowBatchFetchConfirm(null);
    
    try {
      setRaceDayPanels(prev => prev.map(panel => 
        panel.date === date 
          ? { ...panel, batchFetching: true, batchFetchProgress: 'レース結果を取得中...' }
          : panel
      ));
      
      const response: BatchFetchRaceResultsResponse = await raceResultService.batchFetchRaceResults(date);
      
      for (let i = 0; i < response.results.length; i++) {
        const result = response.results[i];
        const progress = `${i + 1}/${response.results.length} ${result.race_number}R ${result.status === 'success' ? '✓' : result.status === 'skipped' ? '⊘' : '✗'}`;
        
        setRaceDayPanels(prev => prev.map(panel => 
          panel.date === date 
            ? { ...panel, batchFetchProgress: progress }
            : panel
        ));
        
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      const { success, skipped, failed } = response.summary;
      const message = `${response.target_races}レース中 ${success}レース取得完了\n${skipped > 0 ? `${skipped}レーススキップ` : ''}${failed > 0 ? `\n${failed}レース失敗` : ''}`;
      
      if (failed > 0) {
        const failedRaces = response.results
          .filter(r => r.status === 'failed')
          .map(r => `${r.race_number}R: ${r.message}`)
          .join('\n');
        
        alert(`${message}\n\n失敗レース:\n${failedRaces}`);
      } else {
        alert(message);
      }
      
      await loadRacesForDate(date);
      
    } catch (error: any) {
      alert(`一括取得エラー: ${error.message}`);
    } finally {
      setRaceDayPanels(prev => prev.map(panel => 
        panel.date === date 
          ? { ...panel, batchFetching: false, batchFetchProgress: '' }
          : panel
      ));
    }
  };

  /**
   * 一括取得ボタンの表示判定
   */
  const shouldShowBatchFetchButton = (panel: RaceDayPanel): boolean => {
    const horsesArrays = Array.from(panel.horsesMap.values());
    return horsesArrays.some(horses => 
      horses.some(h => h.win_probability !== undefined && h.win_probability !== null)
    );
  };

  /**
   * 一括取得ボタンが無効かどうか
   */
  const isBatchFetchButtonDisabled = (panel: RaceDayPanel): boolean => {
    if (panel.races.length === 0) return true;
    
    const resultCount = panel.raceResults.size;
    const horsesArrays = Array.from(panel.horsesMap.values());
    const predictionCount = horsesArrays.filter(horses => 
      horses.some(h => h.win_probability !== undefined && h.win_probability !== null)
    ).length;
    
    return predictionCount > 0 && resultCount >= predictionCount;
  };

  /**
   * 一括取得ボタンのレンダリング
   */
  const renderBatchFetchButton = (panel: RaceDayPanel) => {
    if (!shouldShowBatchFetchButton(panel)) return null;
    
    const isDisabled = isBatchFetchButtonDisabled(panel) || panel.batchFetching;
    const allFetched = isBatchFetchButtonDisabled(panel);
    
    return (
      <div className="px-4 pt-4">
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleBatchFetchClick(panel.date, panel.races);
          }}
          disabled={isDisabled}
          className={`w-full py-2 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors ${
            isDisabled
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {panel.batchFetching ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              {panel.batchFetchProgress || '処理中...'}
            </>
          ) : allFetched ? (
            <>
              <CheckCircle className="w-5 h-5" />
              全て取得済み
            </>
          ) : (
            <>
              <Download className="w-5 h-5" />
              レース結果一括取得
            </>
          )}
        </button>
      </div>
    );
  };

  const renderProgress = () => {
    if (!progress) return null;

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-blue-800 font-medium">予測実行中...</span>
          <span className="text-blue-600 text-sm">
            {progress.completedRaces}/{progress.totalRaces} 完了
          </span>
        </div>
        
        {progress.totalRaces > 0 && (
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{
                width: `${(progress.completedRaces / progress.totalRaces) * 100}%`
              }}
            />
          </div>
        )}
        
        {progress.currentRace && (
          <p className="text-blue-700 text-sm mt-2">
            {progress.currentRace}
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="レース一覧" onHomeClick={handleHomeClick}>
        <div className="flex items-center space-x-2">
          {onGoToStatistics && (
            <button
              onClick={onGoToStatistics}
              className="bg-purple-600 hover:bg-purple-700 text-white py-2 px-3 rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              統計
            </button>
          )}
          <button
            onClick={handleGoToAdmin}
            className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-3 rounded-lg text-sm font-semibold flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            設定
          </button>
          <button
            onClick={handleRefreshDates}
            disabled={isLoadingDates || predictionRunning}
            className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white py-2 px-3 rounded-lg text-sm font-semibold flex items-center gap-2 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${isLoadingDates ? 'animate-spin' : ''}`} />
            更新
          </button>
          <button
            onClick={handlePredictionClick}
            disabled={predictionRunning}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-2 px-3 rounded-lg text-sm font-semibold flex items-center gap-2 disabled:cursor-not-allowed transition-colors"
          >
            {predictionRunning ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                実行中...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                予測実行
              </>
            )}
          </button>
        </div>
      </Header>

      <div className="p-4 max-w-6xl mx-auto">
        {renderProgress()}

        {predictionError && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-medium mb-2">予測実行エラー</p>
            <p className="text-red-700 text-sm">{predictionError}</p>
            <button
              onClick={clearPredictionError}
              className="mt-2 text-red-600 hover:text-red-800 text-sm underline"
            >
              エラーを閉じる
            </button>
          </div>
        )}

        {isLoadingDates && (
          <div className="mb-4">
            <Loading message="レース開催日を読み込んでいます..." size="medium" />
          </div>
        )}

        {datesError && (
          <div className="mb-4">
            <ErrorMessage 
              message={datesError} 
              onRetry={handleRefreshDates}
            />
          </div>
        )}

        <div className="space-y-4">
          {!isLoadingDates && !datesError && raceDayPanels.length === 0 ? (
            <div className="text-center py-8">
              <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">
                レースデータが見つかりませんでした
              </p>
              <button
                onClick={handlePredictionClick}
                className="text-blue-600 hover:text-blue-800 underline"
              >
                予測実行ボタンから新しい日付のデータを作成
              </button>
            </div>
          ) : (
            raceDayPanels.map((panel) => (
              <div
                key={panel.date}
                className="bg-white rounded-lg shadow-md border border-gray-200"
              >
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => togglePanel(panel.date)}
                >
                  <div className="flex items-center space-x-3">
                    <Calendar className="w-5 h-5 text-blue-600" />
                    <div>
                      <h3 className="font-bold text-lg text-gray-800">
                        {panel.displayDate}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {panel.isLoading 
                          ? 'ローディング中...'
                          : panel.hasError
                          ? 'エラーが発生しました'
                          : `${panel.raceCount}レース`
                        }
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {/* === 追加: 結果取得済みバッジ === */}
                    {hasResultsForDate(panel) && (
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" />
                        結果あり
                      </span>
                    )}
                    
                    {/* === 追加: 高確率馬存在バッジ === */}
                    {hasHighProbabilityHorse(panel) && (
                      <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1">
                        <TrendingUp className="w-3 h-3" />
                        注目馬
                      </span>
                    )}
                    
                    {panel.raceCount > 0 && (
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                        {panel.raceCount}
                      </span>
                    )}
                    {panel.isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>

                {panel.isExpanded && (
                  <div className="border-t border-gray-200">
                    {/* AI解説ボタン */}
                    {panel.races.length > 0 && (
                      <div className="px-4 pt-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleAICommentary(panel.date);
                          }}
                          className="w-full bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white py-2 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
                        >
                          <Sparkles className="w-5 h-5" />
                          {panel.showAICommentary ? 'AI解説を閉じる' : 'AI解説を見る'}
                        </button>
                      </div>
                    )}

                    {/* AI解説コンポーネント */}
                    {panel.showAICommentary && (
                      <div className="px-4 pt-4">
                        <AICommentary 
                          date={panel.date} 
                          onCommentaryLoaded={(commentary) => handleCommentaryLoaded(panel.date, commentary)}
                          cachedCommentary={panel.cachedAICommentary}
                        />
                      </div>
                    )}

                    {/* 本日の回収率 */}
                    {panel.races.length > 0 && (
                      <div className="px-4 pt-4">
                        <DailyROIStats
                          races={panel.races}
                          raceResults={panel.raceResults}
                          horsesMap={panel.horsesMap}
                        />
                      </div>
                    )}

                    {/* レース結果一括取得ボタン */}
                    {renderBatchFetchButton(panel)}

                    {/* レース一覧 */}
                    {panel.isLoading ? (
                      <div className="p-4">
                        <Loading message="レース情報を読み込んでいます..." size="medium" />
                      </div>
                    ) : panel.hasError ? (
                      <div className="p-4">
                        <ErrorMessage 
                          message="レース情報の取得に失敗しました" 
                          onRetry={() => handleRetry(panel.date)}
                        />
                      </div>
                    ) : panel.races.length === 0 ? (
                      <div className="p-4 text-center text-gray-500">
                        この日はレースがありません
                      </div>
                    ) : (
                      <div className="p-4 max-h-96 overflow-y-auto">
                        <RaceList 
                          races={panel.races} 
                          onRaceClick={handleRaceClick}
                          raceResults={panel.raceResults}
                          horsesMap={panel.horsesMap}
                          winThreshold={winThreshold}
                          placeThreshold={placeThreshold}
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {availableDates.length > 0 && (
          <div className="mt-6 text-center text-sm text-gray-500">
            <p>データベースに {availableDates.length} 日分のレースデータがあります</p>
          </div>
        )}
      </div>

      <Modal
        isOpen={showDatePicker}
        onClose={() => setShowDatePicker(false)}
        title="予測実行日を選択"
        maxWidth="max-w-lg"
      >
        <div className="space-y-4">
          <div className="text-sm text-gray-600 text-center">
            <p>予測を実行する日付を選択してください</p>
            <p>日付選択後、レース選択画面が表示されます</p>
          </div>

          <DatePicker
            selectedDate={currentDate}
            onDateSelect={handleDateSelect}
            onExecutePrediction={handleDateConfirm}
            minDate="2020-01-01"
            maxDate={getDateString(30)}
            executingPrediction={predictionRunning}
          />
          
          <div className="flex justify-center pt-4">
            <button
              onClick={() => setShowDatePicker(false)}
              disabled={predictionRunning}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 underline disabled:text-gray-400"
            >
              キャンセル
            </button>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={showRaceSelector}
        onClose={() => setShowRaceSelector(false)}
        title={`レース選択 - ${formatDisplayDate(selectedDateForPrediction)}`}
        maxWidth="max-w-2xl"
      >
        <RaceSelector
          date={selectedDateForPrediction}
          races={availableRacesForSelection}
          loading={loadingRacesForSelection}
          onExecutePrediction={handleExecuteSelectedRacesPrediction}
          executingPrediction={predictionRunning}
        />
        
        {!predictionRunning && (
          <div className="flex justify-center pt-4 border-t mt-4">
            <button
              onClick={() => setShowRaceSelector(false)}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 underline"
            >
              キャンセル
            </button>
          </div>
        )}
      </Modal>
      {/* 一括取得確認ダイアログ（NEW） */}
      <Modal
        isOpen={showBatchFetchConfirm !== null}
        onClose={() => setShowBatchFetchConfirm(null)}
        title="レース結果一括取得"
        maxWidth="max-w-md"
      >
        {showBatchFetchConfirm && (
          <div className="space-y-4">
            <div className="text-center">
              <p className="text-gray-700 mb-4">
                {(() => {
                  const panel = raceDayPanels.find(p => p.date === showBatchFetchConfirm);
                  if (!panel) return '';
                  
                  const horsesArrays = Array.from(panel.horsesMap.values());
                  const predictionCount = horsesArrays.filter(horses => 
                    horses.some(h => h.win_probability !== undefined && h.win_probability !== null)
                  ).length;
                  
                  const resultCount = panel.raceResults.size;
                  const targetCount = predictionCount - resultCount;
                  
                  return `${targetCount}レース分の結果を取得します`;
                })()}
              </p>
              <p className="text-sm text-gray-500">
                取得には時間がかかる場合があります
              </p>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => setShowBatchFetchConfirm(null)}
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded-lg font-medium transition-colors"
              >
                キャンセル
              </button>
              <button
                onClick={() => executeBatchFetch(showBatchFetchConfirm!)}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors"
              >
                取得開始
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default HomePage;