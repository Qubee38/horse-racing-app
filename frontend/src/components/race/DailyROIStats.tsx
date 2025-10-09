// frontend/src/components/race/DailyROIStats.tsx (展開/閉じ対応版)

import React, { useState } from 'react';
import { TrendingUp, TrendingDown, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { Race, Horse, RaceResultResponse } from '../../types/api';
import { useThreshold } from '../../contexts/ThresholdContext';

interface DailyROIStatsProps {
  races: Race[];
  raceResults: Map<number, RaceResultResponse>;
  horsesMap: Map<number, Horse[]>;
}

export const DailyROIStats: React.FC<DailyROIStatsProps> = ({ 
  races, 
  raceResults, 
  horsesMap 
}) => {
  const { winThreshold, placeThreshold } = useThreshold();
  const [isExpanded, setIsExpanded] = useState(false); // デフォルトで閉じた状態

  // 結果が取得されているレースのみ対象
  const racesWithResults = races.filter(race => raceResults.has(race.id));

  if (racesWithResults.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
        <div className="flex items-center gap-2 text-yellow-800 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>レース結果未取得</span>
        </div>
      </div>
    );
  }

  // より正確な馬数計算のための改良版集計関数
  const aggregateROIDetailed = (
    isWin: boolean,
    useThreshold: boolean,
    threshold?: number
  ): { 
    roi: number; 
    hitHorses: number;
    totalHorses: number;
    investment: number; 
    return: number;
  } => {
    let totalInvestment = 0;
    let totalReturn = 0;
    let totalHitHorses = 0;
    let totalHorses = 0;

    racesWithResults.forEach(race => {
      const horses = horsesMap.get(race.id) || [];
      const result = raceResults.get(race.id) || null;
      
      if (!result || horses.length === 0) return;

      // このレースの推奨馬を取得
      let recommendedHorses: Horse[] = [];
      
      if (useThreshold && threshold !== undefined) {
        recommendedHorses = horses.filter(h => 
          isWin 
            ? (h.win_probability || 0) >= threshold
            : (h.place_probability || 0) >= threshold
        );
      } else {
        const sorted = [...horses].sort((a, b) => 
          isWin
            ? (b.win_probability || 0) - (a.win_probability || 0)
            : (b.place_probability || 0) - (a.place_probability || 0)
        );
        recommendedHorses = isWin ? [sorted[0]] : sorted.slice(0, 3);
      }

      if (recommendedHorses.length === 0) return;

      totalHorses += recommendedHorses.length;
      totalInvestment += recommendedHorses.length * 100;

      // 的中判定と払戻計算
      if (isWin) {
        const actualWinner = result.horse_results.find(hr => hr.finish_position === 1);
        if (actualWinner) {
          const hitHorse = recommendedHorses.find(rh => rh.horse_number === actualWinner.horse_number);
          if (hitHorse) {
            totalHitHorses += 1;
            const payout = result.payouts.find(p => p.bet_type === 'win');
            if (payout) {
              totalReturn += payout.payout_amount;
            }
          }
        }
      } else {
        const actualTop3 = result.horse_results.filter(hr => 
          hr.finish_position !== null && hr.finish_position <= 3
        );
        
        const hitHorses = recommendedHorses.filter(rh => 
          actualTop3.some(ah => ah.horse_number === rh.horse_number)
        );
        
        totalHitHorses += hitHorses.length;
        
        for (const hitHorse of hitHorses) {
          const payout = result.payouts.find(p => 
            p.bet_type === 'place' && 
            p.winning_numbers.includes(hitHorse.horse_number.toString())
          );
          if (payout) {
            totalReturn += payout.payout_amount;
          }
        }
      }
    });

    const roi = totalInvestment > 0 ? (totalReturn / totalInvestment) * 100 : 0;

    return {
      roi,
      hitHorses: totalHitHorses,
      totalHorses,
      investment: totalInvestment,
      return: totalReturn
    };
  };

  // 各統計を計算（展開時のみ計算を実行するため、ここでは常に計算）
  const rankWin = aggregateROIDetailed(true, false);
  const rankPlace = aggregateROIDetailed(false, false);
  const thresholdWin = aggregateROIDetailed(true, true, winThreshold);
  const thresholdPlace = aggregateROIDetailed(false, true, placeThreshold);

  const ROIBadge: React.FC<{ roi: number }> = ({ roi }) => {
    const isProfit = roi >= 100;
    return (
      <div className={`flex items-center gap-1 ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
        {isProfit ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
        <span className="font-bold">{roi.toFixed(1)}%</span>
      </div>
    );
  };

  return (
    <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200 mb-4">
      {/* ヘッダー（クリック可能） */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-green-100 transition-colors rounded-lg"
      >
        <div className="flex items-center gap-2">
          <h3 className="text-base font-bold text-gray-800">
            本日の回収率
          </h3>
          <span className="text-xs text-gray-500">
            (対象: {racesWithResults.length}/{races.length}レース)
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-600" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-600" />
        )}
      </button>

      {/* 展開時のコンテンツ */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* 予想順位ベース */}
          <div className="bg-white rounded-lg p-3">
            <h4 className="text-xs font-semibold text-gray-600 mb-2">【予想順位ベース】</h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs text-gray-600 mb-1">単勝</div>
                <ROIBadge roi={rankWin.roi} />
                <div className="text-xs text-gray-500 mt-1">
                  {rankWin.hitHorses}/{rankWin.totalHorses}頭的中
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-600 mb-1">複勝</div>
                <ROIBadge roi={rankPlace.roi} />
                <div className="text-xs text-gray-500 mt-1">
                  {rankPlace.hitHorses}/{rankPlace.totalHorses}頭的中
                </div>
              </div>
            </div>
          </div>

          {/* 確率閾値ベース */}
          <div className="bg-white rounded-lg p-3">
            <h4 className="text-xs font-semibold text-gray-600 mb-2">
              【確率閾値ベース】
              <span className="text-xs text-gray-500 ml-1">
                (単勝≥{winThreshold}%, 複勝≥{placeThreshold}%)
              </span>
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs text-gray-600 mb-1">単勝</div>
                {thresholdWin.totalHorses > 0 ? (
                  <>
                    <ROIBadge roi={thresholdWin.roi} />
                    <div className="text-xs text-gray-500 mt-1">
                      {thresholdWin.hitHorses}/{thresholdWin.totalHorses}頭的中
                    </div>
                  </>
                ) : (
                  <div className="text-xs text-gray-500">推奨なし</div>
                )}
              </div>
              <div>
                <div className="text-xs text-gray-600 mb-1">複勝</div>
                {thresholdPlace.totalHorses > 0 ? (
                  <>
                    <ROIBadge roi={thresholdPlace.roi} />
                    <div className="text-xs text-gray-500 mt-1">
                      {thresholdPlace.hitHorses}/{thresholdPlace.totalHorses}頭的中
                    </div>
                  </>
                ) : (
                  <div className="text-xs text-gray-500">推奨なし</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};