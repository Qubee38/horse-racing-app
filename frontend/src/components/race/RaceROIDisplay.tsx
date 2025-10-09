// frontend/src/components/race/RaceROIDisplay.tsx (新規作成)

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { Horse, RaceResultResponse } from '../../types/api';
import {
  calculateRankBasedWinROI,
  calculateRankBasedPlaceROI,
  calculateThresholdBasedWinROI,
  calculateThresholdBasedPlaceROI,
  ROIResult
} from '../../utils/roiCalculator';
import { useThreshold } from '../../contexts/ThresholdContext';

interface RaceROIDisplayProps {
  horses: Horse[];
  raceResult: RaceResultResponse | null;
}

export const RaceROIDisplay: React.FC<RaceROIDisplayProps> = ({ horses, raceResult }) => {
  const { winThreshold, placeThreshold } = useThreshold();

  if (!raceResult) {
    return null;
  }

  // ROI計算
  const rankWinROI = calculateRankBasedWinROI(horses, raceResult);
  const rankPlaceROI = calculateRankBasedPlaceROI(horses, raceResult);
  const thresholdWinROI = calculateThresholdBasedWinROI(horses, raceResult, winThreshold);
  const thresholdPlaceROI = calculateThresholdBasedPlaceROI(horses, raceResult, placeThreshold);

  const ROIBadge: React.FC<{ roi: number }> = ({ roi }) => {
    const isProfit = roi >= 100;
    return (
      <div className={`flex items-center gap-1 ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
        {isProfit ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
        <span className="font-bold text-lg">{roi.toFixed(1)}%</span>
      </div>
    );
  };

  const ROIRow: React.FC<{ label: string; result: ROIResult | null }> = ({ label, result }) => {
    if (!result) {
      return (
        <div className="text-sm text-gray-500">
          {label}: 推奨なし
        </div>
      );
    }

    return (
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-700">{label}</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            {result.hits > 0 ? '的中' : '不的中'} (投資{result.investment}円)
          </span>
          <ROIBadge roi={result.roi} />
        </div>
      </div>
    );
  };

  return (
    <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4 border border-purple-200">
      <h3 className="text-lg font-bold text-gray-800 mb-3">回収率</h3>
      
      <div className="space-y-3">
        {/* 予想順位ベース */}
        <div className="bg-white rounded-lg p-3">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">【予想順位ベース】</h4>
          <div className="space-y-2">
            <ROIRow label="単勝" result={rankWinROI} />
            <ROIRow label="複勝" result={rankPlaceROI} />
          </div>
        </div>

        {/* 確率閾値ベース */}
        <div className="bg-white rounded-lg p-3">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            【確率閾値ベース】
            <span className="text-xs text-gray-500 ml-2">
              (単勝≥{winThreshold}%, 複勝≥{placeThreshold}%)
            </span>
          </h4>
          <div className="space-y-2">
            <ROIRow label="単勝" result={thresholdWinROI} />
            <ROIRow label="複勝" result={thresholdPlaceROI} />
          </div>
        </div>
      </div>
    </div>
  );
};