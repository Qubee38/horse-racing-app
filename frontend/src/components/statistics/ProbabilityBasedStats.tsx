// frontend/src/components/statistics/ProbabilityBasedStats.tsx (Phase1修正版)

import React, { useState } from 'react';
import type { ProbabilityBasedStats, VenueStats, GradeStats } from '../../types/api';

interface ProbabilityBasedStatsProps {
  stats: ProbabilityBasedStats;
  byVenue: VenueStats[];
  byGrade: GradeStats[];
}

type TabType = 'overall' | 'venue' | 'grade';

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

const convertGradeName = (grade: string): string => {
  return GRADE_MAPPING[grade] || grade;
};

export const ProbabilityBasedStatsComponent: React.FC<ProbabilityBasedStatsProps> = ({ 
  stats, 
  byVenue, 
  byGrade 
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overall');

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-800">確率閾値ベース統計</h2>
        <p className="text-sm text-gray-600 mt-1">
          高確率推奨馬のみに絞った場合の的中率（馬単位）
        </p>
      </div>

      {/* タブナビゲーション */}
      <div className="flex border-b border-gray-200 mb-4 overflow-x-auto">
        <button
          onClick={() => setActiveTab('overall')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'overall'
              ? 'border-b-2 border-purple-500 text-purple-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          全体
        </button>
        <button
          onClick={() => setActiveTab('venue')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'venue'
              ? 'border-b-2 border-purple-500 text-purple-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          競馬場別
        </button>
        <button
          onClick={() => setActiveTab('grade')}
          className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
            activeTab === 'grade'
              ? 'border-b-2 border-purple-500 text-purple-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          グレード別
        </button>
      </div>

      {/* タブコンテンツ */}
      {activeTab === 'overall' && <OverallContent stats={stats} />}
      {activeTab === 'venue' && <VenueContent data={byVenue} />}
      {activeTab === 'grade' && <GradeContent data={byGrade} />}

      <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-sm text-yellow-800">
          推奨馬数ベースの的中率です。1レースで複数馬を推奨する場合、推奨馬数が増えます。
        </p>
      </div>
    </div>
  );
};

// 全体統計コンテンツ
const OverallContent: React.FC<{ stats: ProbabilityBasedStats }> = ({ stats }) => (
  <div className="grid grid-cols-2 gap-4">
    {/* 単勝 */}
    <div className="border-2 border-blue-200 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-blue-800 mb-3">
        単勝（≥{stats.win.threshold}%）
      </h3>
      
      <div className="space-y-3">
        <div className="bg-blue-50 rounded p-3">
          <p className="text-xs text-blue-600 mb-1">推奨馬数</p>
          <p className="text-xl font-bold text-blue-900">
            {stats.win.recommended_horses}頭
          </p>
          <p className="text-xs text-gray-500 mt-1">
            推奨レース: {stats.win.recommended_races}レース
          </p>
          <p className="text-xs text-gray-500">
            推奨なし: {stats.win.no_recommendation_races}レース
          </p>
        </div>
        
        <div>
          <p className="text-xs text-blue-600 mb-1">的中馬数</p>
          <p className="text-2xl font-bold text-blue-900">{stats.win.hit_horses}頭</p>
        </div>
        
        <div>
          <p className="text-xs text-blue-600 mb-1">的中率</p>
          <p className="text-2xl font-bold text-blue-900">
            {stats.win.accuracy.toFixed(1)}%
          </p>
          <p className="text-xs text-blue-600">
            ({stats.win.hit_horses}/{stats.win.recommended_horses})
          </p>
        </div>
        
        <div>
          <p className="text-xs text-blue-600 mb-1">ROI（回収率）</p>
          <p className={`text-xl font-semibold ${
            stats.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
          }`}>
            {stats.win.roi.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500 mt-1">
            投資額: {(stats.win.recommended_horses * 100).toLocaleString()}円
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
    <div className="border-2 border-red-200 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-red-800 mb-3">
        複勝（≥{stats.place.threshold}%）
      </h3>
      
      <div className="space-y-3">
        <div className="bg-red-50 rounded p-3">
          <p className="text-xs text-red-600 mb-1">推奨馬数</p>
          <p className="text-xl font-bold text-red-900">
            {stats.place.recommended_horses}頭
          </p>
          <p className="text-xs text-gray-500 mt-1">
            推奨レース: {stats.place.recommended_races}レース
          </p>
          {stats.place.recommended_races > 0 && (
            <p className="text-xs text-gray-500">
              平均 {(stats.place.recommended_horses / stats.place.recommended_races).toFixed(1)}頭/レース
            </p>
          )}
          <p className="text-xs text-gray-500">
            推奨なし: {stats.place.no_recommendation_races}レース
          </p>
        </div>
        
        <div>
          <p className="text-xs text-red-600 mb-1">的中馬数</p>
          <p className="text-2xl font-bold text-red-900">{stats.place.hit_horses}頭</p>
        </div>
        
        <div>
          <p className="text-xs text-red-600 mb-1">的中率</p>
          <p className="text-2xl font-bold text-red-900">
            {stats.place.accuracy.toFixed(1)}%
          </p>
          <p className="text-xs text-red-600">
            ({stats.place.hit_horses}/{stats.place.recommended_horses})
          </p>
        </div>
        
        <div>
          <p className="text-xs text-red-600 mb-1">ROI（回収率）</p>
          <p className={`text-xl font-semibold ${
            stats.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
          }`}>
            {stats.place.roi.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500 mt-1">
            投資額: {(stats.place.recommended_horses * 100).toLocaleString()}円
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
            <th className="px-4 py-2 text-right text-gray-800">推奨馬数</th>
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
              <td className="px-4 py-2 text-right text-gray-700">
                {venue.by_probability.win.recommended_horses + venue.by_probability.place.recommended_horses}
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {venue.by_probability.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({venue.by_probability.win.hit_horses}/{venue.by_probability.win.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  venue.by_probability.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {venue.by_probability.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {venue.by_probability.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({venue.by_probability.place.hit_horses}/{venue.by_probability.place.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  venue.by_probability.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {venue.by_probability.place.roi.toFixed(1)}%
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
            <th className="px-4 py-2 text-right text-gray-800">推奨馬数</th>
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
              <td className="px-4 py-2 text-right text-gray-700">
                {grade.by_probability.win.recommended_horses + grade.by_probability.place.recommended_horses}
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {grade.by_probability.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({grade.by_probability.win.hit_horses}/{grade.by_probability.win.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  grade.by_probability.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {grade.by_probability.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {grade.by_probability.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({grade.by_probability.place.hit_horses}/{grade.by_probability.place.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  grade.by_probability.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {grade.by_probability.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};