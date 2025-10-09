// frontend/src/components/race/RaceList.tsx (Phase1修正版v2)

import React from 'react';
import { Race, Horse, RaceResultResponse } from '../../types/api';
import { Clock, MapPin, Ruler, CircleDot, Users, ChevronRight, CheckCircle, TrendingUp } from 'lucide-react';

interface RaceListProps {
  races: Race[];
  onRaceClick: (race: Race) => void;
  loading?: boolean;
  raceResults?: Map<number, RaceResultResponse>;
  horsesMap?: Map<number, Horse[]>;
  winThreshold?: number;
  placeThreshold?: number;
}

const RaceList: React.FC<RaceListProps> = ({ 
  races, 
  onRaceClick, 
  loading = false,
  raceResults = new Map(),
  horsesMap = new Map(),
  winThreshold = 80,
  placeThreshold = 85
}) => {
  
  // レースの頭数を取得
  const getHorseCount = (raceId: number): number => {
    const horses = horsesMap.get(raceId);
    return horses ? horses.length : 0;
  };

  // レース結果が存在するかチェック
  const hasResult = (raceId: number): boolean => {
    return raceResults.has(raceId);
  };

  // 高確率馬が存在するかチェック
  const hasHighProbabilityHorse = (raceId: number): boolean => {
    const horses = horsesMap.get(raceId);
    if (!horses || horses.length === 0) return false;

    const hasHighWin = horses.some((h: Horse) => (h.win_probability || 0) >= winThreshold);
    const hasHighPlace = horses.some((h: Horse) => (h.place_probability || 0) >= placeThreshold);
    
    return hasHighWin || hasHighPlace;
  };

  const getSurfaceColor = (surface: string): string => {
    switch (surface) {
      case '芝':
        return 'text-green-600 bg-green-100';
      case 'ダート':
        return 'text-yellow-700 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const renderGrade = (grade?: string) => {
    if (!grade || grade === '未設定') return null;
    
    const getGradeStyle = (g: string) => {
      if (g.includes('G1')) return 'bg-red-500 text-white';
      if (g.includes('G2')) return 'bg-blue-500 text-white';
      if (g.includes('G3')) return 'bg-green-500 text-white';
      return 'bg-gray-400 text-white';
    };

    return (
      <span className={`px-2 py-1 rounded text-xs font-bold ${getGradeStyle(grade)}`}>
        {grade}
      </span>
    );
  };

  const formatDistance = (distance: string | number): string => {
    if (typeof distance === 'string') {
      return distance;
    }
    return `${distance}m`;
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, index) => (
          <div key={index} className="animate-pulse">
            <div className="bg-gray-200 rounded-lg h-20"></div>
          </div>
        ))}
      </div>
    );
  }

  if (races.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-400 mb-2">
          <CircleDot className="w-12 h-12 mx-auto" />
        </div>
        <p className="text-gray-500">この日はレースがありません</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {races.map((race, index) => {
        const horseCount = getHorseCount(race.id);
        const resultExists = hasResult(race.id);
        const highProbHorse = hasHighProbabilityHorse(race.id);

        return (
          <div
            key={race.id}
            onClick={() => onRaceClick(race)}
            className="bg-white border border-gray-200 rounded-lg p-4 cursor-pointer hover:shadow-md hover:border-blue-300 transition-all duration-200 group"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex items-center justify-between">
              {/* 左側：レース基本情報 */}
              <div className="flex-1">
                {/* ヘッダー行：レース名、グレード、バッジ */}
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <h3 className="font-bold text-lg text-gray-800 group-hover:text-blue-700 transition-colors">
                    {race.race_name}
                  </h3>
                  {renderGrade(race.grade)}
                  
                  {/* 結果取得済みバッジ */}
                  {resultExists && (
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1">
                      <CheckCircle className="w-3 h-3" />
                      結果
                    </span>
                  )}
                  
                  {/* 高確率馬存在バッジ */}
                  {highProbHorse && (
                    <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      注目
                    </span>
                  )}
                </div>

                {/* 詳細情報行 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  {/* 開催場 */}
                  <div className="flex items-center gap-1 text-gray-600">
                    <MapPin className="w-4 h-4" />
                    <span>{race.venue}</span>
                  </div>

                  {/* 発走時刻 */}
                  <div className="flex items-center gap-1 text-gray-600">
                    <Clock className="w-4 h-4" />
                    <span>{race.start_time}</span>
                  </div>

                  {/* 距離・馬場 */}
                  <div className="flex items-center gap-1 text-gray-600">
                    <Ruler className="w-4 h-4" />
                    <span>{formatDistance(race.distance)}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getSurfaceColor(race.surface)}`}>
                      {race.surface}
                    </span>
                  </div>

                  {/* 出走頭数 */}
                  <div className="flex items-center gap-1 text-gray-600">
                    <Users className="w-4 h-4" />
                    <span>{horseCount}頭</span>
                  </div>
                </div>
              </div>

              {/* 右側：レース番号と矢印 */}
              <div className="flex items-center gap-3 ml-4">
                {/* レース番号 */}
                <div className="text-center">
                  <div className="bg-blue-600 text-white rounded-lg px-3 py-2 font-bold">
                    {race.race_number}R
                  </div>
                </div>

                {/* 矢印アイコン */}
                <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all duration-200" />
              </div>
            </div>

            {/* 追加情報 */}
            {race.netkeiba_race_id && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="text-xs text-gray-500">
                  Netkeiba ID: {race.netkeiba_race_id}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default RaceList;