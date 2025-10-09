// frontend/src/utils/roiCalculator.ts (完全修正版)

import { Horse, RaceResultResponse } from '../types/api';

export interface ROIResult {
  roi: number;
  investment: number;
  return: number;
  hits: number;
  total: number;
}

/**
 * 予想順位ベースの単勝ROI計算
 */
export function calculateRankBasedWinROI(
  horses: Horse[],
  raceResult: RaceResultResponse | null
): ROIResult | null {
  if (!raceResult || horses.length === 0) return null;

  // 予測1位の馬を特定
  const sortedByWinProb = [...horses].sort((a, b) => 
    (b.win_probability || 0) - (a.win_probability || 0)
  );
  const predictedWinner = sortedByWinProb[0];

  // 実際の1着馬を取得
  const actualWinner = raceResult.horse_results.find(hr => hr.finish_position === 1);
  
  if (!actualWinner) return null;

  // 的中判定
  const isHit = predictedWinner.horse_number === actualWinner.horse_number;

  // 単勝配当を取得
  const winPayout = raceResult.payouts.find(p => p.bet_type === 'win');
  
  const investment = 100; // 100円購入
  const returnAmount = isHit && winPayout ? winPayout.payout_amount : 0;
  const roi = (returnAmount / investment) * 100;

  return {
    roi,
    investment,
    return: returnAmount,
    hits: isHit ? 1 : 0,
    total: 1
  };
}

/**
 * 予想順位ベースの複勝ROI計算（修正版）
 */
export function calculateRankBasedPlaceROI(
  horses: Horse[],
  raceResult: RaceResultResponse | null
): ROIResult | null {
  if (!raceResult || horses.length === 0) return null;

  // 予測上位3頭を特定
  const sortedByPlaceProb = [...horses].sort((a, b) => 
    (b.place_probability || 0) - (a.place_probability || 0)
  );
  const predictedTop3 = sortedByPlaceProb.slice(0, 3);

  // 実際の3着以内馬を取得
  const actualTop3 = raceResult.horse_results.filter(hr => 
    hr.finish_position !== null && hr.finish_position <= 3
  );

  // 的中した馬を特定
  const hitHorses = predictedTop3.filter(ph => 
    actualTop3.some(ah => ah.horse_number === ph.horse_number)
  );

  const investment = 300; // 3頭 × 100円
  
  // 的中した馬それぞれの複勝配当を取得して合計
  let returnAmount = 0;
  for (const hitHorse of hitHorses) {
    // この馬の複勝配当を探す
    const payout = raceResult.payouts.find(p => 
      p.bet_type === 'place' && 
      p.winning_numbers.includes(hitHorse.horse_number.toString())
    );
    if (payout) {
      returnAmount += payout.payout_amount;
    }
  }
  
  const roi = (returnAmount / investment) * 100;

  return {
    roi,
    investment,
    return: returnAmount,
    hits: hitHorses.length > 0 ? 1 : 0,
    total: 1
  };
}

/**
 * 確率閾値ベースの単勝ROI計算（修正版：複数馬対応）
 */
export function calculateThresholdBasedWinROI(
  horses: Horse[],
  raceResult: RaceResultResponse | null,
  threshold: number
): ROIResult | null {
  if (!raceResult || horses.length === 0) return null;

  // 閾値以上の馬を全て抽出
  const recommendedHorses = horses.filter(h => 
    (h.win_probability || 0) >= threshold
  );

  if (recommendedHorses.length === 0) return null;

  // 実際の1着馬を取得
  const actualWinner = raceResult.horse_results.find(hr => hr.finish_position === 1);
  
  if (!actualWinner) return null;

  // 推奨馬のうち1着になった馬を特定
  const hitHorses = recommendedHorses.filter(rh => 
    rh.horse_number === actualWinner.horse_number
  );

  // 単勝配当を取得
  const winPayout = raceResult.payouts.find(p => p.bet_type === 'win');
  
  const investment = recommendedHorses.length * 100; // 推奨馬数 × 100円
  const returnAmount = hitHorses.length > 0 && winPayout ? winPayout.payout_amount : 0;
  const roi = (returnAmount / investment) * 100;

  return {
    roi,
    investment,
    return: returnAmount,
    hits: hitHorses.length > 0 ? 1 : 0,
    total: 1
  };
}

/**
 * 確率閾値ベースの複勝ROI計算（修正版：複数馬対応 + 個別配当対応）
 */
export function calculateThresholdBasedPlaceROI(
  horses: Horse[],
  raceResult: RaceResultResponse | null,
  threshold: number
): ROIResult | null {
  if (!raceResult || horses.length === 0) return null;

  // 閾値以上の馬を全て抽出
  const recommendedHorses = horses.filter(h => 
    (h.place_probability || 0) >= threshold
  );

  if (recommendedHorses.length === 0) return null;

  // 実際の3着以内馬を取得
  const actualTop3 = raceResult.horse_results.filter(hr => 
    hr.finish_position !== null && hr.finish_position <= 3
  );

  // 推奨馬のうち3着以内になった馬を特定
  const hitHorses = recommendedHorses.filter(rh => 
    actualTop3.some(ah => ah.horse_number === rh.horse_number)
  );

  const investment = recommendedHorses.length * 100; // 推奨馬数 × 100円
  
  // 的中した馬それぞれの複勝配当を取得して合計
  let returnAmount = 0;
  for (const hitHorse of hitHorses) {
    // この馬の複勝配当を探す
    const payout = raceResult.payouts.find(p => 
      p.bet_type === 'place' && 
      p.winning_numbers.includes(hitHorse.horse_number.toString())
    );
    if (payout) {
      returnAmount += payout.payout_amount;
    }
  }
  
  const roi = (returnAmount / investment) * 100;

  return {
    roi,
    investment,
    return: returnAmount,
    hits: hitHorses.length > 0 ? 1 : 0,
    total: 1
  };
}