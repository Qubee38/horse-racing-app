// frontend/src/components/race/RaceResultDisplay.tsx
import React from 'react';
import { RaceResultResponse, Horse } from '../../types/api';
import { Trophy, Medal, DollarSign, CheckCircle, XCircle } from 'lucide-react';

interface RaceResultDisplayProps {
  result: RaceResultResponse;
  horses: Horse[];  // 予測データ付き馬一覧
}

/**
 * レース結果表示コンポーネント
 */
const RaceResultDisplay: React.FC<RaceResultDisplayProps> = ({ result, horses }) => {
  
  /**
   * 枠色クラスを取得
   */
  // const getFrameColorClass = (frameNumber: number): string => {
  //   const frameColors: { [key: number]: string } = {
  //     1: 'bg-white text-gray-800 border-2 border-gray-400',
  //     2: 'bg-gray-800 text-white',
  //     3: 'bg-red-500 text-white',
  //     4: 'bg-blue-500 text-white',
  //     5: 'bg-yellow-400 text-gray-900',
  //     6: 'bg-green-500 text-white',
  //     7: 'bg-orange-500 text-white',
  //     8: 'bg-pink-500 text-white',
  //   };
  //   return frameColors[frameNumber] || 'bg-gray-500 text-white';
  // };

  /**
   * 予測と実際の結果を比較
   */
  const getPredictionAccuracy = (horseResult: any): {
    predicted: boolean;
    actualPosition: number | null;
    predictedTop3: boolean;
  } => {
    const horse = horses.find(h => h.horse_number === horseResult.horse_number);
    if (!horse || !horseResult.finish_position) {
      return { predicted: false, actualPosition: null, predictedTop3: false };
    }

    // 勝利予測（確率が高い順で1位だったか）
    const sortedByWin = [...horses].sort((a, b) => 
      (b.win_probability || 0) - (a.win_probability || 0)
    );
    const predictedWinner = sortedByWin[0]?.horse_number === horseResult.horse_number;

    // 3着以内予測
    const sortedByPlace = [...horses].sort((a, b) => 
      (b.place_probability || 0) - (a.place_probability || 0)
    );
    const predictedTop3 = sortedByPlace.slice(0, 3).some(h => h.horse_number === horseResult.horse_number);

    return {
      predicted: predictedWinner && horseResult.finish_position === 1,
      actualPosition: horseResult.finish_position,
      predictedTop3: predictedTop3 && horseResult.finish_position <= 3
    };
  };

  /**
   * 馬結果アイテムを描画
   */
  const renderHorseResultItem = (horseResult: any, index: number) => {
    const accuracy = getPredictionAccuracy(horseResult);
    const horse = horses.find(h => h.horse_number === horseResult.horse_number);

    return (
      <div
        key={horseResult.id}
        className={`p-4 border-l-4 ${
          horseResult.finish_position === 1 ? 'border-yellow-500 bg-yellow-50' :
          horseResult.finish_position === 2 ? 'border-gray-400 bg-gray-50' :
          horseResult.finish_position === 3 ? 'border-orange-500 bg-orange-50' :
          'border-gray-200 bg-white'
        }`}
      >
        <div className="grid grid-cols-12 gap-2 items-center">
          {/* 着順 */}
          <div className="col-span-1 text-center">
            {horseResult.finish_position && (
              <div className="flex items-center justify-center">
                {horseResult.finish_position === 1 && <Trophy className="w-6 h-6 text-yellow-600" />}
                {horseResult.finish_position === 2 && <Medal className="w-6 h-6 text-gray-600" />}
                {horseResult.finish_position === 3 && <Medal className="w-6 h-6 text-orange-600" />}
                {horseResult.finish_position > 3 && (
                  <span className="text-lg font-bold text-gray-600">
                    {horseResult.finish_position}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* 馬番 */}
          <div className="col-span-1 text-center">
            <div className="bg-primary-600 text-white w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shadow-sm">
              {horseResult.horse_number}
            </div>
          </div>

          {/* 馬名 */}
          <div className="col-span-4">
            <div className="font-bold text-gray-800">
              {horseResult.horse_name || '不明'}
            </div>
            {horse && (
              <div className="text-sm text-gray-600">
                騎手: {horse.jockey}
              </div>
            )}
          </div>

          {/* 予測確率 */}
          <div className="col-span-3">
            {horse && (
              <div className="text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">勝利:</span>
                  <span className="font-semibold text-red-600">
                    {horse.win_probability?.toFixed(1)}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">複勝:</span>
                  <span className="font-semibold text-blue-600">
                    {horse.place_probability?.toFixed(1)}%
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* 的中判定 */}
          <div className="col-span-3 text-center">
            {horseResult.finish_position && (
              <div className="space-y-1">
                {horseResult.finish_position === 1 && (
                  <div className={`flex items-center justify-center gap-1 text-sm ${
                    accuracy.predicted ? 'text-green-600' : 'text-gray-500'
                  }`}>
                    {accuracy.predicted ? (
                      <>
                        <CheckCircle className="w-4 h-4" />
                        <span className="font-semibold">勝利的中</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4" />
                        <span>勝利不的中</span>
                      </>
                    )}
                  </div>
                )}
                {horseResult.finish_position <= 3 && (
                  <div className={`flex items-center justify-center gap-1 text-sm ${
                    accuracy.predictedTop3 ? 'text-green-600' : 'text-gray-500'
                  }`}>
                    {accuracy.predictedTop3 ? (
                      <>
                        <CheckCircle className="w-4 h-4" />
                        <span className="font-semibold">複勝的中</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="w-4 h-4" />
                        <span>複勝不的中</span>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ヘッダー */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 border border-green-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-green-600 p-2 rounded-lg">
              <Trophy className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-gray-800">レース結果</h3>
              <p className="text-sm text-gray-600">
                取得日時: {new Date(result.result_fetched_at).toLocaleString('ja-JP')}
              </p>
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
            result.race_status === 'completed' ? 'bg-green-100 text-green-700' :
            result.race_status === 'cancelled' ? 'bg-red-100 text-red-700' :
            'bg-yellow-100 text-yellow-700'
          }`}>
            {result.race_status === 'completed' ? '確定' :
             result.race_status === 'cancelled' ? '中止' : '一部データ'}
          </div>
        </div>
      </div>

      {/* 着順結果 */}
      <div className="card overflow-hidden">
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-4 py-3 border-b border-gray-200">
          <h4 className="font-bold text-gray-800">着順</h4>
        </div>
        <div className="divide-y divide-gray-100">
          {result.horse_results.map((hr, index) => renderHorseResultItem(hr, index))}
        </div>
      </div>

      {/* 払い戻し */}
      {result.payouts.length > 0 && (
        <div className="card overflow-hidden">
          <div className="bg-gradient-to-r from-green-50 to-green-100 px-4 py-3 border-b border-green-200">
            <div className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-600" />
              <h4 className="font-bold text-gray-800">払い戻し</h4>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <tbody>
                {/* 単勝 */}
                {result.payouts.filter(p => p.bet_type === 'win').map((payout) => (
                  <tr key={payout.id} className="border-b border-gray-100">
                    <td className="bg-blue-600 text-white font-bold text-center py-3 px-4 w-24">
                      単勝
                    </td>
                    <td className="text-center py-3 px-4 font-bold text-lg">
                      {payout.winning_numbers}
                    </td>
                    <td className="text-right py-3 px-4 font-bold text-lg">
                      {payout.payout_amount.toLocaleString()}円
                    </td>
                  </tr>
                ))}
                
                {/* 複勝 */}
                {result.payouts.filter(p => p.bet_type === 'place').map((payout, index, array) => (
                  <tr key={payout.id} className="border-b border-gray-100">
                    {index === 0 && (
                      <td 
                        className="bg-red-600 text-white font-bold text-center py-3 px-4 w-24" 
                        rowSpan={array.length}
                      >
                        複勝
                      </td>
                    )}
                    <td className="text-center py-3 px-4 font-bold text-lg">
                      {payout.winning_numbers}
                    </td>
                    <td className="text-right py-3 px-4 font-bold text-lg">
                      {payout.payout_amount.toLocaleString()}円
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default RaceResultDisplay;