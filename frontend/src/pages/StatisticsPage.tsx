// frontend/src/pages/StatisticsPage.tsx (Phase1完成版 - パターンC実装)

import React, { useEffect, useState } from 'react';
import { Calendar, Sliders } from 'lucide-react';
import { useStatistics } from '../hooks/useStatistics';
import { useThreshold } from '../contexts/ThresholdContext';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import Header from '../components/common/Header';
import Modal from '../components/common/Modal';
import type { 
  RankBasedStats, 
  ProbabilityBasedStats, 
  VenueStats, 
  GradeStats, 
  TrackTypeStats, 
  DistanceRangeStats,
  TrackConditionStats 
} from '../types/api';

interface FilterSettings {
  startDate: string;
  endDate: string;
  winThreshold: number;
  placeThreshold: number;
}

type StatType = 'rank' | 'probability';
type TabType = 'overall' | 'venue' | 'grade' | 'track' | 'distance' | 'condition';

// 日付を YYYY-MM-DD 形式にフォーマット（タイムゾーン問題を回避）
function formatDateToYYYYMMDD(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// デフォルト開始日（30日前）
function getDefaultStartDate(): string {
  const date = new Date();
  date.setDate(date.getDate() - 30);
  return formatDateToYYYYMMDD(date);
}

// 今日の日付
function getTodayString(): string {
  return formatDateToYYYYMMDD(new Date());
}

// グレード名変換
const GRADE_MAPPING: Record<string, string> = {
  '0': '障害', '1': '未勝利', '2': '2', '3': '新馬',
  '4': '1勝', '5': '2勝', '6': '3勝', '7': 'OP',
  '8': 'G3', '9': 'G2', '10': 'G1'
};

const convertGradeName = (grade: string): string => {
  return GRADE_MAPPING[grade] || grade;
};

export const StatisticsPage: React.FC = () => {
  const { summary, loading, error, fetchSummary, clearError } = useStatistics();
  const { winThreshold, placeThreshold, setWinThreshold, setPlaceThreshold } = useThreshold();
  const [showFilterModal, setShowFilterModal] = useState(false);
  
  // 統計方法の選択
  const [statType, setStatType] = useState<StatType>('rank');
  // タブ選択
  const [activeTab, setActiveTab] = useState<TabType>('overall');
  
  // フィルター設定
  const [filters, setFilters] = useState<FilterSettings>({
    startDate: getDefaultStartDate(),
    endDate: getTodayString(),
    winThreshold: winThreshold,
    placeThreshold: placeThreshold
  });

  // 初回読み込み
  useEffect(() => {
    loadStatistics(filters);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 統計読み込み
  const loadStatistics = (settings: FilterSettings) => {
    fetchSummary({
      start_date: settings.startDate,
      end_date: settings.endDate,
      win_threshold: settings.winThreshold,
      place_threshold: settings.placeThreshold
    });
  };

  // フィルター適用
  const handleApplyFilter = () => {
    setShowFilterModal(false);
    setWinThreshold(filters.winThreshold);
    setPlaceThreshold(filters.placeThreshold);
    loadStatistics(filters);
  };

  // プリセット期間選択
  const handlePresetPeriod = (days: number) => {
    const endDate = getTodayString();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const newFilters = {
      ...filters,
      startDate: formatDateToYYYYMMDD(startDate),
      endDate: endDate
    };
    
    setFilters(newFilters);
  };

  // リセット
  const handleReset = () => {
    const defaultFilters = {
      startDate: getDefaultStartDate(),
      endDate: getTodayString(),
      winThreshold: 80,
      placeThreshold: 85
    };
    setFilters(defaultFilters);
  };

  if (loading && !summary) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Header title="統計" showBackButton={false} />
        <Loading 
          message="統計データを読み込んでいます..." 
          size="large"
          variant="spinner"
        />
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Header title="統計" showBackButton={false} />
        <div className="container-responsive py-4">
          <ErrorMessage 
            message={error} 
            onRetry={() => loadStatistics(filters)}
            showRetryButton={true}
          />
        </div>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* ヘッダー */}
      <Header 
        title="予測精度ダッシュボード" 
        showBackButton={false}
      >
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilterModal(true)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium flex items-center gap-2"
          >
            <Sliders className="w-4 h-4" />
            フィルター
          </button>
          <button
            onClick={() => loadStatistics(filters)}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            {loading ? '読み込み中...' : '更新'}
          </button>
        </div>
      </Header>

      <div className="container-responsive py-4">
        {/* 現在の設定表示 */}
        <div className="mb-6 bg-white rounded-lg shadow-md p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-700 text-sm mb-1">
                <span className="font-semibold">期間:</span> {filters.startDate} 〜 {filters.endDate}
                {summary && <span className="ml-2 text-gray-500">({summary.period.total_days}日間)</span>}
              </p>
              <p className="text-gray-700 text-sm">
                <span className="font-semibold">閾値:</span> 単勝 ≥ {filters.winThreshold}%, 複勝 ≥ {filters.placeThreshold}%
              </p>
            </div>
            <button
              onClick={() => setShowFilterModal(true)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
            >
              <Sliders className="w-4 h-4" />
              変更
            </button>
          </div>
        </div>

        {/* エラー表示 */}
        {error && (
          <ErrorMessage 
            message={error} 
            onRetry={clearError}
            showRetryButton={false}
          />
        )}

        {/* 統計コンテンツ */}
        <div className="bg-white rounded-lg shadow-md p-6">
          {/* 統計方法トグル */}
          <div className="mb-6 flex items-center justify-center gap-4">
            <span className="text-sm text-gray-600">統計方法:</span>
            <div className="inline-flex rounded-lg border border-gray-300 p-1">
              <button
                onClick={() => setStatType('rank')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  statType === 'rank'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                予想順位
              </button>
              <button
                onClick={() => setStatType('probability')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                  statType === 'probability'
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                確率閾値
              </button>
            </div>
          </div>

          {/* タブナビゲーション */}
          <div className="flex border-b border-gray-200 mb-4 overflow-x-auto">
            <button
              onClick={() => setActiveTab('overall')}
              className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'overall'
                  ? `border-b-2 ${statType === 'rank' ? 'border-blue-500 text-blue-600' : 'border-purple-500 text-purple-600'}`
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              全体
            </button>
            <button
              onClick={() => setActiveTab('venue')}
              className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'venue'
                  ? `border-b-2 ${statType === 'rank' ? 'border-blue-500 text-blue-600' : 'border-purple-500 text-purple-600'}`
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              競馬場別
            </button>
            <button
              onClick={() => setActiveTab('grade')}
              className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'grade'
                  ? `border-b-2 ${statType === 'rank' ? 'border-blue-500 text-blue-600' : 'border-purple-500 text-purple-600'}`
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              グレード別
            </button>
            <button
              onClick={() => setActiveTab('track')}
              className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'track'
                  ? `border-b-2 ${statType === 'rank' ? 'border-blue-500 text-blue-600' : 'border-purple-500 text-purple-600'}`
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              馬場別
            </button>
            <button
              onClick={() => setActiveTab('distance')}
              className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'distance'
                  ? `border-b-2 ${statType === 'rank' ? 'border-blue-500 text-blue-600' : 'border-purple-500 text-purple-600'}`
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              距離別
            </button>
            <button
              onClick={() => setActiveTab('condition')}
              className={`px-4 py-2 font-medium text-sm whitespace-nowrap ${
                activeTab === 'condition'
                  ? `border-b-2 ${statType === 'rank' ? 'border-blue-500 text-blue-600' : 'border-purple-500 text-purple-600'}`
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              馬場条件別
            </button>
          </div>

          {/* タブコンテンツ */}
          {statType === 'rank' ? (
            <RankBasedContent 
              activeTab={activeTab}
              stats={summary.by_rank}
              byVenue={summary.by_venue}
              byGrade={summary.by_grade}
              byTrackType={summary.by_track_type}
              byDistance={summary.by_distance}
              byTrackCondition={summary.by_track_condition}
            />
          ) : (
            <ProbabilityBasedContent
              activeTab={activeTab}
              stats={summary.by_probability}
              byVenue={summary.by_venue}
              byGrade={summary.by_grade}
              byTrackType={summary.by_track_type}
              byDistance={summary.by_distance}
              byTrackCondition={summary.by_track_condition}
            />
          )}
        </div>
      </div>

      {/* フィルターモーダル */}
      <Modal
        isOpen={showFilterModal}
        onClose={() => setShowFilterModal(false)}
        title="統計フィルター設定"
        maxWidth="max-w-2xl"
      >
        <div className="space-y-6">
          {/* 期間選択 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              期間選択
            </h3>
            
            {/* プリセットボタン */}
            <div className="mb-4 flex flex-wrap gap-2">
              <button
                onClick={() => handlePresetPeriod(7)}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors"
              >
                過去7日
              </button>
              <button
                onClick={() => handlePresetPeriod(30)}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors"
              >
                過去30日
              </button>
              <button
                onClick={() => handlePresetPeriod(90)}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors"
              >
                過去90日
              </button>
              <button
                onClick={() => handlePresetPeriod(365)}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition-colors"
              >
                過去1年
              </button>
            </div>

            {/* 日付入力 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  開始日
                </label>
                <input
                  type="date"
                  value={filters.startDate}
                  onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                  max={filters.endDate}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  終了日
                </label>
                <input
                  type="date"
                  value={filters.endDate}
                  onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
                  min={filters.startDate}
                  max={getTodayString()}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* 確率閾値設定 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Sliders className="w-5 h-5" />
              確率閾値設定
            </h3>
            
            {/* 単勝閾値 */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">
                  単勝推奨閾値
                </label>
                <span className="text-lg font-bold text-blue-600">
                  {filters.winThreshold}%
                </span>
              </div>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={filters.winThreshold}
                onChange={(e) => setFilters({ ...filters, winThreshold: Number(e.target.value) })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-blue"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>50%</span>
                <span>95%</span>
              </div>
            </div>

            {/* 複勝閾値 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">
                  複勝推奨閾値
                </label>
                <span className="text-lg font-bold text-red-600">
                  {filters.placeThreshold}%
                </span>
              </div>
              <input
                type="range"
                min="60"
                max="98"
                step="5"
                value={filters.placeThreshold}
                onChange={(e) => setFilters({ ...filters, placeThreshold: Number(e.target.value) })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-red"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>60%</span>
                <span>98%</span>
              </div>
            </div>
          </div>

          {/* ボタン */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              onClick={handleReset}
              className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg transition-colors font-medium"
            >
              リセット
            </button>
            <button
              onClick={() => setShowFilterModal(false)}
              className="flex-1 px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors font-medium"
            >
              キャンセル
            </button>
            <button
              onClick={handleApplyFilter}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
            >
              適用
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

// ========================================
// 順位ベース統計コンテンツ
// ========================================

interface RankBasedContentProps {
  activeTab: TabType;
  stats: RankBasedStats;
  byVenue: VenueStats[];
  byGrade: GradeStats[];
  byTrackType: TrackTypeStats[];
  byDistance: DistanceRangeStats[];
  byTrackCondition: TrackConditionStats[];
}

const RankBasedContent: React.FC<RankBasedContentProps> = ({
  activeTab,
  stats,
  byVenue,
  byGrade,
  byTrackType,
  byDistance,
  byTrackCondition
}) => {
  if (activeTab === 'overall') {
    return <RankOverallContent stats={stats} />;
  } else if (activeTab === 'venue') {
    return <RankVenueContent data={byVenue} />;
  } else if (activeTab === 'grade') {
    return <RankGradeContent data={byGrade} />;
  } else if (activeTab === 'track') {
    return <RankTrackContent data={byTrackType} />;
  } else if (activeTab === 'distance') {
    return <RankDistanceContent data={byDistance} />;
  } else if (activeTab === 'condition') {
    return <RankConditionContent data={byTrackCondition} />;
  }
  return null;
};

const RankOverallContent: React.FC<{ stats: RankBasedStats }> = ({ stats }) => (
  <>
    <div className="mb-4">
      <p className="text-gray-600 text-sm mb-2">総レース数</p>
      <p className="text-3xl font-bold text-gray-900">{stats.total_races}</p>
    </div>

    <div className="grid grid-cols-2 gap-4">
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

const RankVenueContent: React.FC<{ data: VenueStats[] }> = ({ data }) => {
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

const RankGradeContent: React.FC<{ data: GradeStats[] }> = ({ data }) => {
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

const RankTrackContent: React.FC<{ data: TrackTypeStats[] }> = ({ data }) => {
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
              <td className="px-4 py-2 text-right text-gray-700">{track.by_rank.total_races}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {track.by_rank.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({track.by_rank.win.hit_horses}/{track.by_rank.win.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  track.by_rank.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {track.by_rank.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {track.by_rank.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({track.by_rank.place.hit_horses}/{track.by_rank.place.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  track.by_rank.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {track.by_rank.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const RankDistanceContent: React.FC<{ data: DistanceRangeStats[] }> = ({ data }) => {
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
              <td className="px-4 py-2 text-right text-gray-700">{distance.by_rank.total_races}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {distance.by_rank.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({distance.by_rank.win.hit_horses}/{distance.by_rank.win.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  distance.by_rank.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {distance.by_rank.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {distance.by_rank.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({distance.by_rank.place.hit_horses}/{distance.by_rank.place.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  distance.by_rank.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {distance.by_rank.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const RankConditionContent: React.FC<{ data: TrackConditionStats[] }> = ({ data }) => {
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
              <td className="px-4 py-2 text-right text-gray-700">{condition.by_rank.total_races}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {condition.by_rank.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({condition.by_rank.win.hit_horses}/{condition.by_rank.win.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  condition.by_rank.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {condition.by_rank.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {condition.by_rank.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({condition.by_rank.place.hit_horses}/{condition.by_rank.place.total_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  condition.by_rank.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {condition.by_rank.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ========================================
// 確率閾値ベース統計コンテンツ
// ========================================

interface ProbabilityBasedContentProps {
  activeTab: TabType;
  stats: ProbabilityBasedStats;
  byVenue: VenueStats[];
  byGrade: GradeStats[];
  byTrackType: TrackTypeStats[];
  byDistance: DistanceRangeStats[];
  byTrackCondition: TrackConditionStats[];
}

const ProbabilityBasedContent: React.FC<ProbabilityBasedContentProps> = ({
  activeTab,
  stats,
  byVenue,
  byGrade,
  byTrackType,
  byDistance,
  byTrackCondition
}) => {
  if (activeTab === 'overall') {
    return <ProbOverallContent stats={stats} />;
  } else if (activeTab === 'venue') {
    return <ProbVenueContent data={byVenue} />;
  } else if (activeTab === 'grade') {
    return <ProbGradeContent data={byGrade} />;
  } else if (activeTab === 'track') {
    return <ProbTrackContent data={byTrackType} />;
  } else if (activeTab === 'distance') {
    return <ProbDistanceContent data={byDistance} />;
  } else if (activeTab === 'condition') {
    return <ProbConditionContent data={byTrackCondition} />;
  }
  return <p className="text-gray-500 text-center py-4">このタブでは確率閾値ベース統計は表示されません</p>;
};

const ProbOverallContent: React.FC<{ stats: ProbabilityBasedStats }> = ({ stats }) => (
  <div className="grid grid-cols-2 gap-4">
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
        </div>
        
        <div>
          <p className="text-xs text-blue-600 mb-1">合計配当</p>
          <p className="text-lg font-semibold text-blue-900">
            {stats.win.total_payout.toLocaleString()}円
          </p>
        </div>
      </div>
    </div>

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

const ProbVenueContent: React.FC<{ data: VenueStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">競馬場</th>
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

const ProbGradeContent: React.FC<{ data: GradeStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">グレード</th>
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

const ProbTrackContent: React.FC<{ data: TrackTypeStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  // by_probabilityが存在するデータのみフィルタリング
  const validData = data.filter(track => track.by_probability);

  if (validData.length === 0) {
    return <p className="text-gray-500 text-center py-4">確率閾値ベースのデータがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">馬場種別</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝ROI</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝ROI</th>
          </tr>
        </thead>
        <tbody>
          {validData.map((track, index) => (
            <tr key={track.track_type} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">{track.track_type}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {track.by_probability.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({track.by_probability.win.hit_horses}/{track.by_probability.win.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  track.by_probability.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {track.by_probability.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {track.by_probability.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({track.by_probability.place.hit_horses}/{track.by_probability.place.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  track.by_probability.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {track.by_probability.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const ProbDistanceContent: React.FC<{ data: DistanceRangeStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  // by_probabilityが存在するデータのみフィルタリング
  const validData = data.filter(distance => distance.by_probability);

  if (validData.length === 0) {
    return <p className="text-gray-500 text-center py-4">確率閾値ベースのデータがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">距離範囲</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝ROI</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝ROI</th>
          </tr>
        </thead>
        <tbody>
          {validData.map((distance, index) => (
            <tr key={distance.distance_range} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">{distance.distance_range}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {distance.by_probability.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({distance.by_probability.win.hit_horses}/{distance.by_probability.win.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  distance.by_probability.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {distance.by_probability.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {distance.by_probability.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({distance.by_probability.place.hit_horses}/{distance.by_probability.place.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  distance.by_probability.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {distance.by_probability.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const ProbConditionContent: React.FC<{ data: TrackConditionStats[] }> = ({ data }) => {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-4">データがありません</p>;
  }

  // by_probabilityが存在するデータのみフィルタリング
  const validData = data.filter(condition => condition.by_probability);

  if (validData.length === 0) {
    return <p className="text-gray-500 text-center py-4">確率閾値ベースのデータがありません</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-2 text-left text-gray-800">馬場条件</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">単勝ROI</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝的中率</th>
            <th className="px-4 py-2 text-right text-gray-800">複勝ROI</th>
          </tr>
        </thead>
        <tbody>
          {validData.map((condition, index) => (
            <tr key={condition.track_condition} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-4 py-2 font-medium text-gray-900">{condition.track_condition}</td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-blue-600">
                  {condition.by_probability.win.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({condition.by_probability.win.hit_horses}/{condition.by_probability.win.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  condition.by_probability.win.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {condition.by_probability.win.roi.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2 text-right">
                <span className="font-semibold text-red-600">
                  {condition.by_probability.place.accuracy.toFixed(1)}%
                </span>
                <p className="text-xs text-gray-500">
                  ({condition.by_probability.place.hit_horses}/{condition.by_probability.place.recommended_horses})
                </p>
              </td>
              <td className="px-4 py-2 text-right">
                <span className={`font-semibold ${
                  condition.by_probability.place.roi >= 100 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {condition.by_probability.place.roi.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StatisticsPage;