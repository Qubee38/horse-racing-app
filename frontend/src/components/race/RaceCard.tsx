import React from 'react';
import { Calendar, Clock, MapPin, Users, ChevronDown, ChevronUp } from 'lucide-react';
import { Race } from '../../types/api';
import { formatDate } from '../../utils/dateUtils';
import { formatDistance, formatSurface } from '../../utils/formatUtils';

// RaceCardコンポーネントのプロパティ型定義
interface RaceCardProps {
  race: Race;                    // レース情報
  isExpanded: boolean;           // 展開されているかどうか
  onToggleExpand: () => void;    // 展開/折り畳みの切り替え
  onRaceClick: (race: Race) => void;  // レースがクリックされた時の処理
  races: Race[];                 // 同じ日付のレース一覧（グループ化用）
}

/**
 * 個別レースカードコンポーネント
 * - 美しいカードデザイン
 * - アニメーション効果
 * - レスポンシブ対応
 */
const RaceCard: React.FC<RaceCardProps> = ({ 
  race, 
  isExpanded, 
  onToggleExpand, 
  onRaceClick, 
  races 
}) => {
  
  /**
   * 馬場に応じた背景色を取得
   */
  const getSurfaceColor = (surface: string) => {
    switch (surface) {
      case '芝': return 'from-green-50 to-emerald-50 border-green-200';
      case 'ダート': return 'from-amber-50 to-orange-50 border-amber-200';
      default: return 'from-gray-50 to-slate-50 border-gray-200';
    }
  };

  /**
   * 開催地に応じたアクセントカラーを取得
   */
  const getVenueAccent = (venue: string) => {
    const venueColors: { [key: string]: string } = {
      '東京': 'bg-red-500',
      '京都': 'bg-purple-500',
      '阪神': 'bg-blue-500',
      '中山': 'bg-green-500',
      '中京': 'bg-yellow-500',
      '新潟': 'bg-pink-500',
    };
    return venueColors[venue] || 'bg-gray-500';
  };

  return (
    <div className="card-hover animate-fade-in">
      {/* レース日付ヘッダー（展開/折り畳み可能） */}
      <div 
        className={`bg-gradient-to-r ${getSurfaceColor(race.surface)} p-4 cursor-pointer transition-all duration-300 relative overflow-hidden`}
        onClick={onToggleExpand}
      >
        {/* 装飾的な背景パターン */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white rounded-full -translate-y-16 translate-x-16"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-white rounded-full translate-y-12 -translate-x-12"></div>
        </div>
        
        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* カレンダーアイコンと日付 */}
            <div className="flex items-center gap-3">
              <div className="bg-white bg-opacity-80 p-2 rounded-lg shadow-sm">
                <Calendar className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <div className="font-bold text-gray-800 text-lg">
                  {formatDate(race.race_date)}
                </div>
                <div className="text-sm text-gray-600 flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  <span>{races.length}レース開催</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* 展開/折り畳みアイコン */}
          <div className="flex items-center gap-2">
            <div className="text-sm text-gray-500 hidden sm:block">
              {isExpanded ? '折り畳む' : '展開する'}
            </div>
            <div className={`transform transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
              <ChevronDown className="w-5 h-5 text-gray-600" />
            </div>
          </div>
        </div>
      </div>
      
      {/* レース一覧（展開時のみ表示） */}
      <div className={`transition-all duration-300 ease-in-out overflow-hidden ${
        isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        <div className="divide-y divide-gray-100 bg-white">
          {races.map((raceItem, index) => (
            <div
              key={raceItem.id}
              className="group p-4 hover:bg-gradient-to-r hover:from-primary-50 hover:to-transparent cursor-pointer transition-all duration-200 relative"
              onClick={() => onRaceClick(raceItem)}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              {/* レース項目の左側装飾 */}
              <div className={`absolute left-0 top-0 bottom-0 w-1 ${getVenueAccent(raceItem.venue)} opacity-0 group-hover:opacity-100 transition-opacity duration-200`}></div>
              
              <div className="flex justify-between items-center pl-2">
                <div className="flex-1">
                  {/* レース名と会場 */}
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-3 h-3 rounded-full ${getVenueAccent(raceItem.venue)}`}></div>
                    <div className="font-semibold text-gray-800 group-hover:text-primary-700 transition-colors">
                      {raceItem.venue} {raceItem.race_name}
                    </div>
                  </div>
                  
                  {/* レース詳細情報 */}
                  <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      <span>{formatDistance(raceItem.distance)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className={`w-3 h-3 rounded-full ${
                        raceItem.surface === '芝' ? 'bg-green-400' : 'bg-amber-400'
                      }`}></div>
                      <span>{formatSurface(raceItem.surface)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      <span>{raceItem.horse_count}頭</span>
                    </div>
                  </div>
                </div>
                
                {/* 発走時刻 */}
                <div className="text-right">
                  <div className="flex items-center gap-2 text-primary-600 font-bold text-lg">
                    <Clock className="w-5 h-5" />
                    <span>{raceItem.start_time}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    クリックで詳細
                  </div>
                </div>
              </div>
              
              {/* ホバー時の矢印 */}
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-200">
                <ChevronUp className="w-4 h-4 text-primary-500 rotate-90" />
              </div>
            </div>
          ))}
        </div>
        
        {/* フッター情報 */}
        <div className="bg-gray-50 px-4 py-3 border-t">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
              <span>予測データ準備完了</span>
            </div>
            <div className="text-xs">
              {races.length}レース • 全{races.reduce((sum, r) => sum + r.horse_count, 0)}頭出走予定
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RaceCard;