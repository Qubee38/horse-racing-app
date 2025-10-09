import React from 'react';
import { Horse } from '../../types/api';
import { 
  formatProbability, 
  formatExpectedValue, 
  getExpectedValueColor 
} from '../../utils/formatUtils';
import { Trophy, TrendingUp, Target, Star, ChevronRight } from 'lucide-react';

interface HorseListProps {
  horses: Horse[];
  onHorseClick: (horse: Horse) => void;
  loading?: boolean;
}

/**
 * 出走馬一覧表示コンポーネント（修正版：バー100%対応）
 */
const HorseList: React.FC<HorseListProps> = ({ 
  horses, 
  onHorseClick, 
  loading = false 
}) => {
  
  const getFrameColorClass = (frameNumber: number): string => {
    const frameColors: { [key: number]: string } = {
      1: 'bg-white text-gray-800 border-2 border-gray-400',
      2: 'bg-gray-800 text-white',
      3: 'bg-red-500 text-white',
      4: 'bg-blue-500 text-white',
      5: 'bg-yellow-400 text-gray-900',
      6: 'bg-green-500 text-white',
      7: 'bg-orange-500 text-white',
      8: 'bg-pink-500 text-white',
    };
    return frameColors[frameNumber] || 'bg-gray-500 text-white';
  };

  const getProbabilityColor = (probability: number | null | undefined, type: 'win' | 'place'): string => {
    if (!probability) return 'bg-gray-200';
    
    if (type === 'win') {
      if (probability >= 20) return 'bg-red-500';
      if (probability >= 15) return 'bg-red-400';
      if (probability >= 10) return 'bg-red-300';
      return 'bg-red-200';
    } else {
      if (probability >= 60) return 'bg-blue-500';
      if (probability >= 45) return 'bg-blue-400';
      if (probability >= 30) return 'bg-blue-300';
      return 'bg-blue-200';
    }
  };

  const getExpectedValueRank = (value: number | null | undefined): string => {
    if (!value) return '';
    if (value >= 110) return 'S';
    if (value >= 105) return 'A';
    if (value >= 100) return 'B';
    return 'C';
  };

  if (loading) {
    return (
      <div className="card animate-fade-in">
        <div className="card-body text-center py-12">
          <div className="loading-spinner-lg mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">出走馬情報を読み込んでいます...</p>
          <div className="flex justify-center space-x-1 mt-3">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="w-2 h-2 bg-primary-400 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.1}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (horses.length === 0) {
    return (
      <div className="card animate-fade-in">
        <div className="card-body text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Trophy className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500 text-lg font-medium">出走馬情報がありません</p>
          <p className="text-gray-400 text-sm mt-2">レースデータを確認してください</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      {/* ヘッダーカード */}
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg p-4 border border-primary-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-primary-600 p-2 rounded-lg">
              <Target className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-gray-800">AI予測結果</h3>
              <p className="text-sm text-gray-600">全{horses.length}頭の予測完了</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">最高期待値</div>
            <div className="font-bold text-primary-600">
              {Math.max(...horses.map(h => h.expected_value || 0)).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* メインテーブル */}
      <div className="card overflow-hidden">
        {/* テーブルヘッダー */}
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-4 py-3 border-b border-gray-200">
          <div className="grid grid-cols-12 gap-2 text-xs font-bold text-gray-600 uppercase tracking-wide">
            <div className="col-span-1 text-center">枠</div>
            <div className="col-span-1 text-center">馬番</div>
            <div className="col-span-3">馬名/騎手</div>
            <div className="col-span-2 text-center">1着確率</div>
            <div className="col-span-2 text-center">3着以内確率</div>
            <div className="col-span-2 text-center">期待値</div>
            <div className="col-span-1"></div>
          </div>
        </div>
        
        {/* 馬一覧 */}
        <div className="divide-y divide-gray-100">
          {horses.map((horse, index) => (
            <div
              key={horse.id}
              className="group p-4 hover:bg-gradient-to-r hover:from-primary-50 hover:to-transparent cursor-pointer transition-all duration-200 relative"
              onClick={() => onHorseClick(horse)}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              {/* ランキング表示（上位3頭） */}
              {index < 3 && (
                <div className="absolute -left-1 top-0 bottom-0 w-1 bg-gradient-to-b from-yellow-400 via-yellow-500 to-yellow-600"></div>
              )}
              
              <div className="grid grid-cols-12 gap-2 items-center">
                {/* 枠番 */}
                <div className="col-span-1 text-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shadow-sm ${getFrameColorClass(horse.frame_number)}`}>
                    {horse.frame_number}
                  </div>
                </div>
                
                {/* 馬番 */}
                <div className="col-span-1 text-center">
                  <div className="bg-primary-600 text-white w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shadow-sm">
                    {horse.horse_number}
                  </div>
                </div>
                
                {/* 馬名・騎手 */}
                <div className="col-span-3">
                  <div className="font-bold text-gray-800 group-hover:text-primary-700 transition-colors">
                    {horse.name}
                  </div>
                  <div className="text-sm text-gray-600 flex items-center gap-1">
                    <Star className="w-3 h-3" />
                    {horse.jockey}
                  </div>
                </div>
                
                {/* === 修正: 1着確率バー（100%基準） === */}
                <div className="col-span-2">
                  <div className="text-center">
                    <div className="font-bold text-red-600 text-sm mb-1">
                      {formatProbability(horse.win_probability)}
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-500 ${getProbabilityColor(horse.win_probability, 'win')}`}
                        style={{ width: `${horse.win_probability || 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
                
                {/* === 修正: 3着以内確率バー（100%基準） === */}
                <div className="col-span-2">
                  <div className="text-center">
                    <div className="font-bold text-blue-600 text-sm mb-1">
                      {formatProbability(horse.place_probability)}
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-500 ${getProbabilityColor(horse.place_probability, 'place')}`}
                        style={{ width: `${horse.place_probability || 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
                
                {/* 期待値 */}
                <div className="col-span-2 text-center">
                  <div className="flex flex-col items-center gap-1">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${getExpectedValueColor(horse.expected_value)} shadow-sm`}>
                      {formatExpectedValue(horse.expected_value)}
                    </span>
                    {getExpectedValueRank(horse.expected_value) && (
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                        getExpectedValueRank(horse.expected_value) === 'S' ? 'bg-red-100 text-red-700' :
                        getExpectedValueRank(horse.expected_value) === 'A' ? 'bg-orange-100 text-orange-700' :
                        getExpectedValueRank(horse.expected_value) === 'B' ? 'bg-blue-100 text-blue-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {getExpectedValueRank(horse.expected_value)}
                      </span>
                    )}
                  </div>
                </div>
                
                {/* 矢印アイコン */}
                <div className="col-span-1 text-center">
                  <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-primary-600 group-hover:translate-x-1 transition-all duration-200" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* フッター説明 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
        <div className="flex items-start gap-3">
          <TrendingUp className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
          <div>
            <h4 className="font-bold text-blue-800 mb-2">予測指標の説明</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-700">
              <div>
                <div className="font-semibold mb-1">期待値ランク</div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded text-xs font-bold">S</span>
                    <span>110%以上：非常に有望</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded text-xs font-bold">A</span>
                    <span>105-110%：有望</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-bold">B</span>
                    <span>100-105%：やや有望</span>
                  </div>
                </div>
              </div>
              
              <div>
                <div className="font-semibold mb-1">確率バー</div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-2 bg-red-500 rounded"></div>
                    <span>1着確率（赤系・最大100%）</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-2 bg-blue-500 rounded"></div>
                    <span>3着以内確率（青系・最大100%）</span>
                  </div>
                </div>
              </div>
              
              <div>
                <div className="font-semibold mb-1">使用方法</div>
                <p className="text-xs">各馬をクリックすると詳細情報を確認できます。期待値とオッズを比較して投資判断にご活用ください。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HorseList;