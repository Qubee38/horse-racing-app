// frontend/src/components/statistics/OverallSummary.tsx (Phase1修正版)

import React, { useState } from 'react';
import type { RankBasedStats, VenueStats, GradeStats, TrackTypeStats, DistanceRangeStats, TrackConditionStats } from '../../types/api';

interface OverallSummaryProps {
  stats: RankBasedStats;
  byVenue: VenueStats[];
  byGrade: GradeStats[];
  byTrackType: TrackTypeStats[];
  byDistance: DistanceRangeStats[];
  byTrackCondition: TrackConditionStats[];
}

type TabType = 'overall' | 'venue' | 'grade' | 'track' | 'distance' | 'condition';

// グレード名変換マッピング
const GRADE_MAPPING: Record<string, string> = {
  '0': '障害',
  '1': '未勝利',
  '2': '2',
  '3': '新馬',
  '4': '1勝',
  '5': '2勝',
  '6': '3勝',
  '7': 'OP',
  '8': 'G3',
  '9': 'G2',
  '10': 'G1'
};

// グレード名を変換
const convertGradeName = (grade: string): string => {
  return GRADE_MAPPING[grade] || grade;
};

export const OverallSummary: React.FC<OverallSummaryProps> = ({ 
  stats, 
  byVenue, 
  byGrade, 
  byTrackType, 
  byDistance,
  byTrackCondition
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overall');

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">予想順位統計</h2>

      {/* タブナビゲーション */}
      <div className="flex border-b border-gray-200 mb-4 overflow-x-auto">
        <button
          onClick={() => setActiveTab('overall')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'overall'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          全体
        </button>
        <button
          onClick={() => setActiveTab('venue')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'venue'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          競馬場別
        </button>
        <button
          onClick={() => setActiveTab('grade')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'grade'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          グレード別
        </button>
        <button
          onClick={() => setActiveTab('track')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'track'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          馬場別
        </button>
        <button
          onClick={() => setActiveTab('distance')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'distance'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          距離別
        </button>
        <button
          onClick={() => setActiveTab('condition')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'condition'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          馬場条件別
        </button>
      </div>

      {/* タブコンテンツ */}
      {activeTab === 'overall' && <OverallContent stats={stats} />}
      {activeTab === 'venue' && <VenueContent data={byVenue} />}
      {activeTab === 'grade' && <GradeContent data={byGrade} />}
      {activeTab === 'track' && <TrackContent data={byTrackType} />}
      {activeTab === 'distance' && <DistanceContent data={byDistance} />}
      {activeTab === 'condition' && <TrackConditionContent data={byTrackCondition} />}
    </div>
  );
};

// 全体統計コンテンツ
const OverallContent: React.FC<{ stats: RankBasedStats }> = ({ stats }) => (
  <>
    <div className="mb-4">
      <p className="text-gray-600 text-sm mb-2">総レース数</p>
      <p className="text-3xl font-bold text-gray-900">{stats.total_races}</p>
    </div>

    <div className="grid grid-cols-2 gap-4">
      {/* 単勝 */}
      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-800 mb-3">単勝</h3>
        <div className="space-y-2">
          <div>
            <p className="text-xs text-blue-600 mb-1">的中率</p>
            <p className="text-2xl font-bold text-blue-900">
              {stats.win.accuracy.toFixed(1)}%
            </p>
            <p className="text-xs text-blue-600">
              {stats.win.hit_horses}/{stats.win.total_horses}
            </p>
          </div>
          <div>
            <p className="text-xs text-blue-600 mb-1">ROI（回収率）</p>
            <p className={`text-xl font-semibold ${
              stats.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
            }`}>
              {stats.win.roi.toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-blue-600 mb-1">合計配当</p>
            <p className="text-lg font-semibold text-blue-900">
              {stats.win.total_payout.toLocaleString()}円
            </p>
          </div>
        </div>
      </div>

      {/* 複勝 */}
      <div className="bg-red-50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-red-800 mb-3">複勝</h3>
        <div className="space-y-2">
          <div>
            <p className="text-xs text-red-600 mb-1">的中率</p>
            <p className="text-2xl font-bold text-red-900">
              {stats.place.accuracy.toFixed(1)}%
            </p>
            <p className="text-xs text-red-600">
              {stats.place.hit_horses}/{stats.place.total_horses}
            </p>
          </div>
          <div>
            <p className="text-xs text-red-600 mb-1">ROI（回収率）</p>
            <p className={`text-xl font-semibold ${
              stats.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
            }`}>
              {stats.place.roi.toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-red-600 mb-1">合計配当</p>
            <p className="text-lg font-semibold text-red-900">
              {stats.place.total_payout.toLocaleString()}円
            </p>
          </div>
        </div>
      </div>
    </div>
  </>
);

// 競馬場別コンテンツ
const VenueContent: React.FC<{ data: VenueStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">競馬場</th>
            <th className="px-4 py-2 text-right text-gray-800">レース数</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝ROI</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝ROI</th>
          </tr>
        </thead>
        <tbody>
          {data.map((venue, index) => (
            <tr key={venue.venue} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">{venue.venue}</td>
              <td className="px-4 py-2 text-right text-gray-700">{venue.by_rank.total_races}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {venue.by_rank.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({venue.by_rank.win.hit_horses}/{venue.by_rank.win.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  venue.by_rank.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {venue.by_rank.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {venue.by_rank.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({venue.by_rank.place.hit_horses}/{venue.by_rank.place.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  venue.by_rank.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {venue.by_rank.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// グレード別コンテンツ
const GradeContent: React.FC<{ data: GradeStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">グレード</th>
            <th className="px-4 py-2 text-right text-gray-800">レース数</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝ROI</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝ROI</th>
          </tr>
        </thead>
        <tbody>
          {data.map((grade, index) => (
            <tr key={grade.grade} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">
                {convertGradeName(grade.grade)}
              </td>
              <td className="px-4 py-2 text-right text-gray-700">{grade.by_rank.total_races}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {grade.by_rank.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({grade.by_rank.win.hit_horses}/{grade.by_rank.win.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  grade.by_rank.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {grade.by_rank.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {grade.by_rank.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({grade.by_rank.place.hit_horses}/{grade.by_rank.place.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  grade.by_rank.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {grade.by_rank.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// 馬場別コンテンツ
const TrackContent: React.FC<{ data: TrackTypeStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">馬場種別</th>
            <th className="px-4 py-2 text-right text-gray-800">レース数</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝ROI</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝ROI</th>
          </tr>
        </thead>
        <tbody>
          {data.map((track, index) => (
            <tr key={track.track_type} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">{track.track_type}</td>
              <td className="px-4 py-2 text-right text-gray-700">{track.total_races}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {track.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({track.win.hit_horses}/{track.win.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  track.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {track.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {track.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({track.place.hit_horses}/{track.place.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  track.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {track.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// 距離別コンテンツ
const DistanceContent: React.FC<{ data: DistanceRangeStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">距離範囲</th>
            <th className="px-4 py-2 text-right text-gray-800">レース数</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝ROI</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝ROI</th>
          </tr>
        </thead>
        <tbody>
          {data.map((distance, index) => (
            <tr key={distance.distance_range} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">{distance.distance_range}</td>
              <td className="px-4 py-2 text-right text-gray-700">{distance.total_races}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {distance.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({distance.win.hit_horses}/{distance.win.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  distance.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {distance.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {distance.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({distance.place.hit_horses}/{distance.place.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  distance.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {distance.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// 馬場条件別コンテンツ（新規追加）
const TrackConditionContent: React.FC<{ data: TrackConditionStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">馬場条件</th>
            <th className="px-4 py-2 text-right text-gray-800">レース数</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝ROI</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝ROI</th>
          </tr>
        </thead>
        <tbody>
          {data.map((condition, index) => (
            <tr key={condition.track_condition} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">{condition.track_condition}</td>
              <td className="px-4 py-2 text-right text-gray-700">{condition.total_races}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {condition.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({condition.win.hit_horses}/{condition.win.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  condition.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {condition.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {condition.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({condition.place.hit_horses}/{condition.place.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  condition.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {condition.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};