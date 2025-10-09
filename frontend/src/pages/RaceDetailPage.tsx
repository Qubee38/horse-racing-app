// frontend/src/pages/RaceDetailPage.tsx (Phase1修正版 - 完全版)

import React, { useEffect, useState } from 'react';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import HorseList from '../components/horse/HorseList';
import RaceResultDisplay from '../components/race/RaceResultDisplay';
import { RaceROIDisplay } from '../components/race/RaceROIDisplay';
import { useRaces } from '../hooks/useRaces';
import { useRaceResult } from '../hooks/useRaceResult';
import { Race, Horse } from '../types/api';
import { formatDistance, formatSurface } from '../utils/formatUtils';
import { Download, CheckCircle, ChevronRight, ArrowUpDown, Trash2, RefreshCw } from 'lucide-react';
import { deleteRace, refetchRaceResult } from '../services/api';

interface RaceDetailPageProps {
  race: Race;
  onBack: () => void;
  onHorseSelect: (horse: Horse) => void;
  allRaces?: Race[];
  onRaceSelect?: (race: Race, racesForDate?: Race[]) => void;
}

type SortField = 'horse_number' | 'win_probability' | 'place_probability';
type SortOrder = 'asc' | 'desc';

const RaceDetailPage: React.FC<RaceDetailPageProps> = ({ 
  race, 
  onBack, 
  onHorseSelect,
  allRaces = [],
  onRaceSelect
}) => {
  const {
    horses,
    loading: horsesLoading,
    error: horsesError,
    fetchRaceHorses,
    clearError: clearHorsesError
  } = useRaces();

  const {
    result,
    loading: resultLoading,
    error: resultError,
    exists: resultExists,
    fetching: resultFetching,
    checkResultExists,
    fetchRaceResult,
    getRaceResult,
    clearError: clearResultError
  } = useRaceResult();

  const [dataFetched, setDataFetched] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [sortField, setSortField] = useState<SortField>('horse_number');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [sortedHorses, setSortedHorses] = useState<Horse[]>([]);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isRefetching, setIsRefetching] = useState(false);

  // ソート機能
  useEffect(() => {
    if (horses.length > 0) {
      const sorted = [...horses].sort((a, b) => {
        let aValue: number;
        let bValue: number;

        switch (sortField) {
          case 'horse_number':
            aValue = a.horse_number || 0;
            bValue = b.horse_number || 0;
            break;
          case 'win_probability':
            aValue = a.win_probability || 0;
            bValue = b.win_probability || 0;
            break;
          case 'place_probability':
            aValue = a.place_probability || 0;
            bValue = b.place_probability || 0;
            break;
          default:
            aValue = a.horse_number || 0;
            bValue = b.horse_number || 0;
        }

        if (sortOrder === 'asc') {
          return aValue - bValue;
        } else {
          return bValue - aValue;
        }
      });

      setSortedHorses(sorted);
    } else {
      setSortedHorses([]);
    }
  }, [horses, sortField, sortOrder]);

  // ソート変更ハンドラー
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder(field === 'horse_number' ? 'asc' : 'desc');
    }
  };

  // 前のレースを取得
  const getPreviousRace = (): Race | null => {
    if (!allRaces || allRaces.length === 0) return null;
    
    const currentIndex = allRaces.findIndex(r => r.id === race.id);
    if (currentIndex === -1 || currentIndex === 0) return null;
    
    return allRaces[currentIndex - 1];
  };

  // 次のレースを取得
  const getNextRace = (): Race | null => {
    if (!allRaces || allRaces.length === 0) return null;
    
    const currentIndex = allRaces.findIndex(r => r.id === race.id);
    if (currentIndex === -1 || currentIndex === allRaces.length - 1) return null;
    
    return allRaces[currentIndex + 1];
  };

  const previousRace = getPreviousRace();
  const nextRace = getNextRace();

  // データ読み込み
  useEffect(() => {
    const loadData = async () => {
      try {
        await fetchRaceHorses(race.id);
        await checkResultExists(race.id);
        setDataFetched(true);
      } catch (error) {
        console.error('Failed to load data:', error);
        setDataFetched(true);
      }
    };

    if (race && !dataFetched) {
      loadData();
    }
  }, [race, dataFetched, fetchRaceHorses, checkResultExists]);

  // レースが変わったらリセット（追加）
  useEffect(() => {
    setDataFetched(false);
    setShowResult(false);
    setShowDeleteConfirm(false);
  }, [race.id]);

  // レース結果取得
  const handleFetchResult = async () => {
    try {
      const success = await fetchRaceResult(race.id);
      
      if (success) {
        setTimeout(async () => {
          await getRaceResult(race.id);
          setShowResult(true);
        }, 10000);
      }
    } catch (error) {
      console.error('Failed to fetch result:', error);
    }
  };

  const handleShowResult = async () => {
    await getRaceResult(race.id);
    setShowResult(true);
  };

  const handleHideResult = () => {
    setShowResult(false);
  };

  const handleHorseClick = (horse: Horse) => {
    console.log('Horse clicked:', horse);
    onHorseSelect(horse);
  };

  const handleRetry = () => {
    clearHorsesError();
    clearResultError();
    setDataFetched(false);
  };

  // レース削除ハンドラー
  const handleDeleteRace = async () => {
    if (!showDeleteConfirm) {
      setShowDeleteConfirm(true);
      return;
    }

      setIsDeleting(true);
    try {
      const result = await deleteRace(race.id);
      alert(result.message || 'レースを削除しました');
      onBack();
    } catch (error: any) {
      alert(`削除エラー: ${error.message}`);
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  // レース結果再取得ハンドラー
  const handleRefetchResult = async () => {
    setIsRefetching(true);
    try {
      const result = await refetchRaceResult(race.id);
      alert(result.message || '結果の再取得を開始しました。10秒後に自動で更新されます。');
      
      setTimeout(async () => {
        await getRaceResult(race.id);
        setShowResult(true);
        setIsRefetching(false);
      }, 10000);
    } catch (error: any) {
      alert(`再取得エラー: ${error.message}`);
      setIsRefetching(false);
    }
  };

  // 日付フォーマット
  const formatRaceDate = (dateStr: string | Date | undefined): string => {
    if (!dateStr) return '';
    
    try {
      const date = typeof dateStr === 'string' ? new Date(dateStr) : dateStr;
      const year = date.getFullYear();
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return `${year}/${month}/${day}`;
    } catch {
      return '';
    }
  };

  // レース情報セクション
  const renderRaceInfo = () => (
    <div className="bg-blue-50 p-4 rounded-lg mb-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-800">
        <div>
          <span className="font-semibold">発走時刻:</span>
          <div className="text-lg font-bold">{race.start_time}</div>
        </div>
        
        <div>
          <span className="font-semibold">距離・馬場:</span>
          <div className="text-lg font-bold">
            {formatDistance(race.distance)} ({formatSurface(race.surface)})
          </div>
        </div>
        
        <div>
          <span className="font-semibold">出走頭数:</span>
          <div className="text-lg font-bold">{sortedHorses.length}頭</div>
        </div>
      </div>
    </div>
  );

  // ソートボタン
  const renderSortButtons = () => {
    if (showResult || sortedHorses.length === 0) return null;

    return (
      <div className="mb-4 bg-white rounded-lg shadow-md p-4">
        <div className="flex items-center gap-2 mb-2">
          <ArrowUpDown className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-semibold text-gray-700">並び替え:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => handleSort('horse_number')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              sortField === 'horse_number'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            馬番 {sortField === 'horse_number' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
          <button
            onClick={() => handleSort('win_probability')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              sortField === 'win_probability'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            1着確率 {sortField === 'win_probability' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
          <button
            onClick={() => handleSort('place_probability')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              sortField === 'place_probability'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            3着以内確率 {sortField === 'place_probability' && (sortOrder === 'asc' ? '↑' : '↓')}
          </button>
        </div>
      </div>
    );
  };

  // レース管理ボタン（削除・結果再取得）
  const renderManagementButtons = () => {
    return (
      <div className="mb-6 flex gap-2">
        {/* レース削除ボタン */}
        <button
          onClick={handleDeleteRace}
          disabled={isDeleting}
          className={`flex-1 ${
            showDeleteConfirm
              ? 'bg-red-600 hover:bg-red-700'
              : 'bg-gray-500 hover:bg-gray-600'
          } text-white py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isDeleting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              削除中...
            </>
          ) : showDeleteConfirm ? (
            <>
              <Trash2 className="w-4 h-4" />
              本当に削除しますか？
            </>
          ) : (
            <>
              <Trash2 className="w-4 h-4" />
              レース削除
            </>
          )}
        </button>

        {/* 結果再取得ボタン（結果が存在する場合のみ） */}
        {resultExists && (
          <button
            onClick={handleRefetchResult}
            disabled={isRefetching}
            className="flex-1 bg-orange-500 hover:bg-orange-600 text-white py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRefetching ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                再取得中...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                結果再取得
              </>
            )}
          </button>
        )}

        {/* 削除確認キャンセル */}
        {showDeleteConfirm && (
          <button
            onClick={() => setShowDeleteConfirm(false)}
            className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded-lg font-medium transition-colors"
          >
            キャンセル
          </button>
        )}
      </div>
    );
  };
  const renderResultButton = () => {
    if (!dataFetched || horsesLoading) return null;

    return (
      <div className="mb-6">
        {resultFetching && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="loading-spinner"></div>
              <div>
                <div className="font-semibold text-yellow-800">レース結果を取得中...</div>
                <div className="text-sm text-yellow-600">完了まで10秒ほどお待ちください</div>
              </div>
            </div>
          </div>
        )}

        {!resultFetching && !showResult && resultExists && (
          <button
            onClick={handleShowResult}
            className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-green-600 hover:to-green-700 transition-all duration-200 flex items-center justify-center gap-2 shadow-md"
          >
            <CheckCircle className="w-5 h-5" />
            レース結果を表示
          </button>
        )}

        {!resultFetching && !showResult && !resultExists && (
          <button
            onClick={handleFetchResult}
            className="w-full bg-gradient-to-r from-primary-500 to-primary-600 text-white py-3 px-4 rounded-lg font-semibold hover:from-primary-600 hover:to-primary-700 transition-all duration-200 flex items-center justify-center gap-2 shadow-md"
          >
            <Download className="w-5 h-5" />
            レース結果を取得
          </button>
        )}

        {showResult && (
          <button
            onClick={handleHideResult}
            className="w-full bg-gray-500 text-white py-3 px-4 rounded-lg font-semibold hover:bg-gray-600 transition-all duration-200"
          >
            レース結果を非表示
          </button>
        )}
      </div>
    );
  };

  // メインコンテンツ
  const renderContent = () => {
    if (horsesError || resultError) {
      return (
        <ErrorMessage 
          message={horsesError || resultError || 'エラーが発生しました'} 
          onRetry={handleRetry}
          showRetryButton={true}
        />
      );
    }

    if (horsesLoading || !dataFetched) {
      return (
        <Loading 
          message="出走馬情報を読み込んでいます..." 
          size="large" 
        />
      );
    }

    return (
      <>
        {!showResult && (
          <HorseList
            horses={sortedHorses}
            onHorseClick={handleHorseClick}
            loading={horsesLoading}
          />
        )}

        {showResult && result && (
          <div className="space-y-4">
            {resultLoading ? (
              <Loading message="レース結果を読み込んでいます..." size="large" />
            ) : (
              <>
                <RaceResultDisplay result={result} horses={horses} />
                <RaceROIDisplay
                  horses={horses}
                  raceResult={result}
                />
              </>
            )}
          </div>
        )}
      </>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* カスタムヘッダー（タイトル + ナビゲーションボタン） */}
      <div className="bg-blue-600 text-white">
        {/* 戻るボタン行 */}
        <div className="flex items-center px-4 py-3">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-white hover:text-blue-100 transition-colors"
          >
            <ChevronRight className="w-5 h-5 rotate-180" />
            <span className="font-medium">戻る</span>
          </button>
        </div>

        {/* タイトル + ナビゲーションボタン行 */}
        <div className="flex items-center justify-between px-4 pb-4 pt-1">
          <h1 className="text-xl font-bold flex-1">
            {formatRaceDate(race.race_date)} {race.venue} {race.race_number}R {race.race_name}
          </h1>
          
          {/* ナビゲーションボタン */}
          <div className="flex items-center gap-2 ml-4">
            {previousRace && onRaceSelect && (
              <button
                onClick={() => onRaceSelect(previousRace, allRaces)}
                className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
              >
                前のレース
              </button>
            )}
            
            {nextRace && onRaceSelect && (
              <button
                onClick={() => onRaceSelect(nextRace, allRaces)}
                className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
              >
                次のレース
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="p-4">
        {renderRaceInfo()}
        {renderManagementButtons()}
        {renderResultButton()}
        {renderSortButtons()}

        <div className="mb-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">
            {showResult ? 'レース結果' : '出走馬一覧'}
          </h2>
          {renderContent()}
        </div>

        {sortedHorses.length > 0 && !showResult && (
          <div className="bg-white rounded-lg shadow-md p-4">
            <h3 className="font-semibold text-gray-800 mb-2">
              ご利用上の注意
            </h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• 予測確率は過去データに基づく推定値です</li>
              <li>• 実際の競馬では様々な要因が結果に影響します</li>
              <li>• 投資は自己責任で行ってください</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default RaceDetailPage;