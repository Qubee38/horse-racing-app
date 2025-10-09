// frontend/src/components/statistics/ProbabilityBreakdown.tsx

import React from 'react';
import type { ProbabilityBreakdown } from '../../types/api';

interface ProbabilityBreakdownProps {
  breakdown: ProbabilityBreakdown;
}

export const ProbabilityBreakdownComponent: React.FC<ProbabilityBreakdownProps> = ({ breakdown }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-800">確率範囲別の詳細分析</h2>
        <p className="text-sm text-gray-600 mt-1">
          予測確率と的中率・ROIの関係
        </p>
      </div>

      <div className="space-y-6">
        {/* 単勝 */}
        <div>
          <h3 className="text-lg font-semibold text-blue-800 mb-3">単勝予測確率と的中率の関係</h3>
          
          {breakdown.win.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-blue-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-blue-800">確率範囲</th>
                    <th className="px-4 py-2 text-right text-blue-800">レース数</th>
                    <th className="px-4 py-2 text-right text-blue-800">的中数</th>
                    <th className="px-4 py-2 text-right text-blue-800">的中率</th>
                    <th className="px-4 py-2 text-right text-blue-800">平均配当</th>
                    <th className="px-4 py-2 text-right text-blue-800">ROI</th>
                  </tr>
                </thead>
                <tbody>
                  {breakdown.win.map((range, index) => (
                    <tr 
                      key={range.range}
                      className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                    >
                      <td className="px-4 py-2 font-medium text-gray-900">{range.range}</td>
                      <td className="px-4 py-2 text-right text-gray-700">{range.races}</td>
                      <td className="px-4 py-2 text-right text-gray-700">{range.hits}</td>
                      <td className="px-4 py-2 text-right">
                        <span className="font-semibold text-blue-900">
                          {range.accuracy.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right text-gray-700">
                        {range.avg_payout.toFixed(0)}円
                      </td>
                      <td className="px-4 py-2 text-right">
                        <span className={`font-semibold ${
                          range.roi >= 100 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {range.roi.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">データがありません</p>
          )}
        </div>

        {/* 複勝 */}
        <div>
          <h3 className="text-lg font-semibold text-red-800 mb-3">複勝予測確率と的中率の関係</h3>
          
          {breakdown.place.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-red-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-red-800">確率範囲</th>
                    <th className="px-4 py-2 text-right text-red-800">レース数</th>
                    <th className="px-4 py-2 text-right text-red-800">的中数</th>
                    <th className="px-4 py-2 text-right text-red-800">的中率</th>
                    <th className="px-4 py-2 text-right text-red-800">平均配当</th>
                    <th className="px-4 py-2 text-right text-red-800">ROI</th>
                  </tr>
                </thead>
                <tbody>
                  {breakdown.place.map((range, index) => (
                    <tr 
                      key={range.range}
                      className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                    >
                      <td className="px-4 py-2 font-medium text-gray-900">{range.range}</td>
                      <td className="px-4 py-2 text-right text-gray-700">{range.races}</td>
                      <td className="px-4 py-2 text-right text-gray-700">{range.hits}</td>
                      <td className="px-4 py-2 text-right">
                        <span className="font-semibold text-red-900">
                          {range.accuracy.toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right text-gray-700">
                        {range.avg_payout.toFixed(0)}円
                      </td>
                      <td className="px-4 py-2 text-right">
                        <span className={`font-semibold ${
                          range.roi >= 100 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {range.roi.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">データがありません</p>
          )}
        </div>
      </div>

      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-sm text-blue-800">
          📊 <strong>分析:</strong> 確率が高いほど的中率も高くなる傾向があります。確率が低いほど配当が高く、期待値（ROI）も向上する可能性があります。
        </p>
      </div>
    </div>
  );
};