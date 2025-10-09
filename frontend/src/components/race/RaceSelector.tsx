import React, { useState, useEffect } from 'react';
import { CheckSquare, Square, Play, Loader } from 'lucide-react';

interface RaceOption {
  netkeiba_race_id: string;
  race_number: number;
  race_name: string;
  venue: string;
  start_time: string;
  distance: number;
}

interface RaceSelectorProps {
  date: string;
  races: RaceOption[];
  loading: boolean;
  onExecutePrediction: (selectedRaceIds: string[]) => void;
  executingPrediction: boolean;
}

/**
 * レース選択コンポーネント
 * - チェックボックスで複数レース選択
 * - 全選択/全解除機能
 * - 選択したレースのみ予測実行
 */
const RaceSelector: React.FC<RaceSelectorProps> = ({
  date,
  races,
  loading,
  onExecutePrediction,
  executingPrediction
}) => {
  const [selectedRaceIds, setSelectedRaceIds] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(false);

  // レース一覧が変更されたらリセット
  useEffect(() => {
    setSelectedRaceIds(new Set());
    setSelectAll(false);
  }, [date, races]);

  // 個別レースの選択切り替え
  const toggleRaceSelection = (raceId: string) => {
    const newSelected = new Set(selectedRaceIds);
    
    if (newSelected.has(raceId)) {
      newSelected.delete(raceId);
    } else {
      newSelected.add(raceId);
    }
    
    setSelectedRaceIds(newSelected);
    setSelectAll(newSelected.size === races.length);
  };

  // 全選択/全解除
  const toggleSelectAll = () => {
    if (selectAll) {
      setSelectedRaceIds(new Set());
      setSelectAll(false);
    } else {
      const allIds = new Set(races.map(r => r.netkeiba_race_id));
      setSelectedRaceIds(allIds);
      setSelectAll(true);
    }
  };

  // 予測実行ボタンクリック
  const handleExecute = () => {
    const selectedIds = Array.from(selectedRaceIds);
    if (selectedIds.length > 0) {
      onExecutePrediction(selectedIds);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">レース一覧を読み込み中...</span>
      </div>
    );
  }

  if (races.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">この日はレースがありません</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ヘッダー: 全選択チェックボックス */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-200">
        <button
          onClick={toggleSelectAll}
          disabled={executingPrediction}
          className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {selectAll ? (
            <CheckSquare className="w-5 h-5 text-blue-600" />
          ) : (
            <Square className="w-5 h-5" />
          )}
          <span>全選択 ({races.length}レース)</span>
        </button>
        
        <span className="text-sm text-gray-500">
          {selectedRaceIds.size}件選択中
        </span>
      </div>

      {/* レース一覧 */}
      <div className="max-h-96 overflow-y-auto space-y-2">
        {races.map((race) => {
          const isSelected = selectedRaceIds.has(race.netkeiba_race_id);
          
          return (
            <button
              key={race.netkeiba_race_id}
              onClick={() => toggleRaceSelection(race.netkeiba_race_id)}
              disabled={executingPrediction}
              className={`
                w-full p-3 rounded-lg border-2 transition-all duration-200
                ${isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-blue-300'
                }
                ${executingPrediction ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-start gap-3">
                {/* チェックボックス */}
                <div className="flex-shrink-0 mt-1">
                  {isSelected ? (
                    <CheckSquare className="w-5 h-5 text-blue-600" />
                  ) : (
                    <Square className="w-5 h-5 text-gray-400" />
                  )}
                </div>
                
                {/* レース情報 */}
                <div className="flex-1 text-left">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-gray-800">
                      {race.race_number}R
                    </span>
                    <span className="text-sm text-gray-600">
                      {race.start_time}
                    </span>
                    <span className="text-sm text-gray-500">
                      {race.venue}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-700 font-medium">
                    {race.race_name}
                  </div>
                  
                  <div className="text-xs text-gray-500 mt-1">
                    {race.distance}m • ID: {race.netkeiba_race_id}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* 実行ボタン */}
      <div className="pt-3 border-t border-gray-200">
        <button
          onClick={handleExecute}
          disabled={selectedRaceIds.size === 0 || executingPrediction}
          className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg font-semibold flex items-center justify-center gap-2 disabled:cursor-not-allowed transition-colors"
        >
          {executingPrediction ? (
            <>
              <Loader className="w-5 h-5 animate-spin" />
              予測実行中...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              選択した{selectedRaceIds.size}レースを予測実行
            </>
          )}
        </button>
        
        {selectedRaceIds.size === 0 && !executingPrediction && (
          <p className="text-xs text-gray-500 text-center mt-2">
            レースを選択してください
          </p>
        )}
      </div>
    </div>
  );
};

export default RaceSelector;