import React from 'react';
import { Horse } from '../../types/api';
import { 
  formatOdds, 
  formatProbability, 
  formatExpectedValue, 
  getExpectedValueColor,
  getFrameColor 
} from '../../utils/formatUtils';

// HorseCardコンポーネントのプロパティ型定義
interface HorseCardProps {
  horse: Horse;                           // 馬情報
  onClick?: () => void;                   // カードがクリックされた時の処理
  showDetailedInfo?: boolean;             // 詳細情報の表示/非表示
  className?: string;                     // 追加のCSSクラス
}

/**
 * 個別馬情報カードコンポーネント
 * - 馬の基本情報を見やすく表示
 * - 予測結果のハイライト
 * - クリック可能なカード形式
 */
const HorseCard: React.FC<HorseCardProps> = ({ 
  horse, 
  onClick, 
  showDetailedInfo = false,
  className = '' 
}) => {
  
  return (
    <div 
      className={`bg-white rounded-lg shadow-md p-4 ${onClick ? 'cursor-pointer hover:bg-gray-50 transition-colors' : ''} ${className}`}
      onClick={onClick}
    >
      {/* カードヘッダー：馬名と馬番 */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="font-bold text-lg text-gray-800">
            {horse.name}
          </h3>
          <p className="text-sm text-gray-600">
            騎手: {horse.jockey}
          </p>
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          {/* 枠番 */}
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${getFrameColor(horse.frame_number)}`}>
            {horse.frame_number}
          </div>
          
          {/* 馬番 */}
          <div className="bg-blue-600 text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold">
            {horse.horse_number}
          </div>
        </div>
      </div>

      {/* 基本情報 */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <span className="text-xs text-gray-500">オッズ</span>
          <div className="font-semibold text-gray-800">
            {formatOdds(horse.odds)}
          </div>
        </div>
        
        {showDetailedInfo && (
          <div>
            <span className="text-xs text-gray-500">枠番・馬番</span>
            <div className="font-semibold text-gray-800">
              {horse.frame_number}枠 {horse.horse_number}番
            </div>
          </div>
        )}
      </div>

      {/* 予測結果 */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">1着確率</span>
          <span className="font-bold text-red-600">
            {formatProbability(horse.win_probability)}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">3着以内確率</span>
          <span className="font-bold text-blue-600">
            {formatProbability(horse.place_probability)}
          </span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">期待値</span>
          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getExpectedValueColor(horse.expected_value)}`}>
            {formatExpectedValue(horse.expected_value)}
          </span>
        </div>
      </div>

      {/* 詳細情報（オプション） */}
      {showDetailedInfo && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 mb-2">詳細情報</div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-500">馬ID:</span>
              <span className="ml-1 text-gray-700">{horse.id}</span>
            </div>
            
            {/* 将来的に追加される情報用のプレースホルダー */}
            <div>
              <span className="text-gray-500">状態:</span>
              <span className="ml-1 text-green-600">良好</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HorseCard;