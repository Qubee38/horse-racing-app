# backend/scripts/model_evaluation/evaluator.py

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import pandas as pd

from .config import EvaluationConfig
from .data_loader import RaceData
from .payback_parser import PaybackInfo

logger = logging.getLogger(__name__)


@dataclass
class BetResult:
    """単一レースの賭け結果"""
    race_id: str
    strategy_name: str
    bet_type: str  # 'win' or 'place'
    recommended_horses: List[int]  # 推奨馬番のリスト
    hit_horses: List[int]  # 的中した馬番のリスト
    investment: int  # 投資額（円）
    payout: int  # 払戻額（円）
    roi: float  # 回収率（%）


@dataclass
class StrategyResult:
    """投資戦略の評価結果"""
    strategy_name: str
    bet_type: str  # 'win' or 'place'
    model_type: Optional[str] = None  # 'win_model' or 'place_model' (閾値ベースの場合)
    threshold: Optional[float] = None  # 確率閾値（閾値ベースの場合）
    
    total_races: int = 0
    total_horses: int = 0  # 推奨馬数の合計
    hit_horses: int = 0  # 的中馬数の合計
    total_investment: int = 0
    total_payout: int = 0
    
    bet_results: List[BetResult] = field(default_factory=list)
    
    @property
    def accuracy(self) -> float:
        """的中率（%）"""
        if self.total_horses == 0:
            return 0.0
        return (self.hit_horses / self.total_horses) * 100
    
    @property
    def roi(self) -> float:
        """回収率（%）"""
        if self.total_investment == 0:
            return 0.0
        return (self.total_payout / self.total_investment) * 100
    
    @property
    def profit(self) -> int:
        """収支（円）"""
        return self.total_payout - self.total_investment


class Evaluator:
    """回収率計算クラス"""
    
    def __init__(self, config: EvaluationConfig):
        """
        Parameters
        ----------
        config : EvaluationConfig
            評価設定
        """
        self.config = config
    
    def evaluate_all_strategies(self, race_data_list: List[RaceData]) -> Dict[str, StrategyResult]:
        """
        全ての投資戦略で評価
        
        Parameters
        ----------
        race_data_list : List[RaceData]
            レースデータのリスト
        
        Returns
        -------
        Dict[str, StrategyResult]
            戦略名 -> 評価結果のマップ
        """
        logger.info(f"=== Phase 2: Strategy Evaluation ===")
        logger.info(f"Evaluating {len(race_data_list)} races with 14 strategies")
        
        results = {}
        
        # 1. 予想順位ベース（2パターン）
        results['rank_based_win'] = self.evaluate_rank_based_win(race_data_list)
        results['rank_based_place'] = self.evaluate_rank_based_place(race_data_list)
        
        # 2. 確率閾値ベース（12パターン）
        for bet_type in ['win', 'place']:
            for model_type in ['win_model', 'place_model']:
                thresholds = self.config.PROBABILITY_THRESHOLDS[bet_type][model_type]
                
                for threshold in thresholds:
                    strategy_name = f"threshold_{model_type}_{int(threshold)}_{bet_type}"
                    
                    if bet_type == 'win':
                        results[strategy_name] = self.evaluate_threshold_based_win(
                            race_data_list, model_type, threshold
                        )
                    else:
                        results[strategy_name] = self.evaluate_threshold_based_place(
                            race_data_list, model_type, threshold
                        )
        
        logger.info(f"Strategy evaluation completed: {len(results)} strategies")
        
        return results
    
    # ========================================
    # 予想順位ベース
    # ========================================
    
    def evaluate_rank_based_win(self, race_data_list: List[RaceData]) -> StrategyResult:
        """予想順位ベースの単勝評価"""
        strategy_name = "rank_based_win"
        result = StrategyResult(
            strategy_name=strategy_name,
            bet_type='win'
        )
        
        for race_data in race_data_list:
            if not race_data.payback_info or not race_data.payback_info.win:
                continue
            
            df = race_data.predictions_df
            
            # 予測1位の馬を特定
            if '1着確率' not in df.columns or len(df) == 0:
                continue
            
            sorted_df = df.sort_values('1着確率', ascending=False)
            predicted_winner = sorted_df.iloc[0]
            predicted_horse_number = int(predicted_winner['馬番'])
            
            # 実際の1着馬番と配当
            actual_winner_number = predicted_winner['馬番']
            win_horse_number, win_payout = race_data.payback_info.win
            
            # 的中判定
            is_hit = str(predicted_horse_number) == str(win_horse_number)
            
            # 投資額と払戻額
            investment = self.config.BASE_BET_AMOUNT  # 100円
            payout = win_payout if is_hit else 0
            roi = (payout / investment) * 100 if investment > 0 else 0
            
            # BetResult作成
            bet_result = BetResult(
                race_id=race_data.race_id,
                strategy_name=strategy_name,
                bet_type='win',
                recommended_horses=[predicted_horse_number],
                hit_horses=[predicted_horse_number] if is_hit else [],
                investment=investment,
                payout=payout,
                roi=roi
            )
            
            result.bet_results.append(bet_result)
            result.total_races += 1
            result.total_horses += 1
            result.hit_horses += 1 if is_hit else 0
            result.total_investment += investment
            result.total_payout += payout
        
        logger.info(f"{strategy_name}: ROI={result.roi:.2f}%, Accuracy={result.accuracy:.2f}%")
        
        return result
    
    def evaluate_rank_based_place(self, race_data_list: List[RaceData]) -> StrategyResult:
        """予想順位ベースの複勝評価"""
        strategy_name = "rank_based_place"
        result = StrategyResult(
            strategy_name=strategy_name,
            bet_type='place'
        )
        
        for race_data in race_data_list:
            if not race_data.payback_info or not race_data.payback_info.place:
                continue
            
            df = race_data.predictions_df
            
            # 予測上位3頭を特定
            if '3着以内確率' not in df.columns or len(df) == 0:
                continue
            
            sorted_df = df.sort_values('3着以内確率', ascending=False)
            predicted_top3 = sorted_df.head(3)
            predicted_horse_numbers = [int(h) for h in predicted_top3['馬番'].tolist()]
            
            # 実際の複勝配当（複数）
            place_payouts = race_data.payback_info.place  # [(馬番, 配当), ...]
            
            # 的中した馬を特定
            hit_horses = []
            total_payout = 0
            
            for predicted_num in predicted_horse_numbers:
                # この馬が複勝圏内か確認
                for place_horse_num, place_payout in place_payouts:
                    if str(predicted_num) == str(place_horse_num):
                        hit_horses.append(predicted_num)
                        total_payout += place_payout
                        break
            
            # 投資額と払戻額
            investment = self.config.BASE_BET_AMOUNT * 3  # 3頭 × 100円 = 300円
            roi = (total_payout / investment) * 100 if investment > 0 else 0
            
            # BetResult作成
            bet_result = BetResult(
                race_id=race_data.race_id,
                strategy_name=strategy_name,
                bet_type='place',
                recommended_horses=predicted_horse_numbers,
                hit_horses=hit_horses,
                investment=investment,
                payout=total_payout,
                roi=roi
            )
            
            result.bet_results.append(bet_result)
            result.total_races += 1
            result.total_horses += 3
            result.hit_horses += len(hit_horses)
            result.total_investment += investment
            result.total_payout += total_payout
        
        logger.info(f"{strategy_name}: ROI={result.roi:.2f}%, Accuracy={result.accuracy:.2f}%")
        
        return result
    
    # ========================================
    # 確率閾値ベース
    # ========================================
    
    def evaluate_threshold_based_win(
        self, 
        race_data_list: List[RaceData],
        model_type: str,
        threshold: float
    ) -> StrategyResult:
        """確率閾値ベースの単勝評価"""
        strategy_name = f"threshold_{model_type}_{int(threshold)}_win"
        result = StrategyResult(
            strategy_name=strategy_name,
            bet_type='win',
            model_type=model_type,
            threshold=threshold
        )
        
        # 使用する確率カラムを決定
        prob_column = '1着確率' if model_type == 'win_model' else '3着以内確率'
        
        for race_data in race_data_list:
            if not race_data.payback_info or not race_data.payback_info.win:
                continue
            
            df = race_data.predictions_df
            
            if prob_column not in df.columns or len(df) == 0:
                continue
            
            # 閾値以上の馬を全て抽出
            recommended_df = df[df[prob_column] >= threshold]
            
            if len(recommended_df) == 0:
                continue
            
            recommended_horse_numbers = [int(h) for h in recommended_df['馬番'].tolist()]
            
            # 実際の1着馬番と配当
            win_horse_number, win_payout = race_data.payback_info.win
            
            # 推奨馬のうち1着になった馬を特定
            hit_horses = []
            total_payout = 0
            
            for rec_num in recommended_horse_numbers:
                if str(rec_num) == str(win_horse_number):
                    hit_horses.append(rec_num)
                    total_payout = win_payout
                    break
            
            # 投資額と払戻額
            investment = self.config.BASE_BET_AMOUNT * len(recommended_horse_numbers)
            roi = (total_payout / investment) * 100 if investment > 0 else 0
            
            # BetResult作成
            bet_result = BetResult(
                race_id=race_data.race_id,
                strategy_name=strategy_name,
                bet_type='win',
                recommended_horses=recommended_horse_numbers,
                hit_horses=hit_horses,
                investment=investment,
                payout=total_payout,
                roi=roi
            )
            
            result.bet_results.append(bet_result)
            result.total_races += 1
            result.total_horses += len(recommended_horse_numbers)
            result.hit_horses += len(hit_horses)
            result.total_investment += investment
            result.total_payout += total_payout
        
        logger.info(f"{strategy_name}: ROI={result.roi:.2f}%, Accuracy={result.accuracy:.2f}%")
        
        return result
    
    def evaluate_threshold_based_place(
        self,
        race_data_list: List[RaceData],
        model_type: str,
        threshold: float
    ) -> StrategyResult:
        """確率閾値ベースの複勝評価"""
        strategy_name = f"threshold_{model_type}_{int(threshold)}_place"
        result = StrategyResult(
            strategy_name=strategy_name,
            bet_type='place',
            model_type=model_type,
            threshold=threshold
        )
        
        # 使用する確率カラムを決定
        prob_column = '1着確率' if model_type == 'win_model' else '3着以内確率'
        
        for race_data in race_data_list:
            if not race_data.payback_info or not race_data.payback_info.place:
                continue
            
            df = race_data.predictions_df
            
            if prob_column not in df.columns or len(df) == 0:
                continue
            
            # 閾値以上の馬を全て抽出
            recommended_df = df[df[prob_column] >= threshold]
            
            if len(recommended_df) == 0:
                continue
            
            recommended_horse_numbers = [int(h) for h in recommended_df['馬番'].tolist()]
            
            # 実際の複勝配当（複数）
            place_payouts = race_data.payback_info.place  # [(馬番, 配当), ...]
            
            # 推奨馬のうち3着以内になった馬を特定
            hit_horses = []
            total_payout = 0
            
            for rec_num in recommended_horse_numbers:
                # この馬が複勝圏内か確認
                for place_horse_num, place_payout in place_payouts:
                    if str(rec_num) == str(place_horse_num):
                        hit_horses.append(rec_num)
                        total_payout += place_payout
                        break
            
            # 投資額と払戻額
            investment = self.config.BASE_BET_AMOUNT * len(recommended_horse_numbers)
            roi = (total_payout / investment) * 100 if investment > 0 else 0
            
            # BetResult作成
            bet_result = BetResult(
                race_id=race_data.race_id,
                strategy_name=strategy_name,
                bet_type='place',
                recommended_horses=recommended_horse_numbers,
                hit_horses=hit_horses,
                investment=investment,
                payout=total_payout,
                roi=roi
            )
            
            result.bet_results.append(bet_result)
            result.total_races += 1
            result.total_horses += len(recommended_horse_numbers)
            result.hit_horses += len(hit_horses)
            result.total_investment += investment
            result.total_payout += total_payout
        
        logger.info(f"{strategy_name}: ROI={result.roi:.2f}%, Accuracy={result.accuracy:.2f}%")
        
        return result


# ========================================
# テスト用コード
# ========================================
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # パス設定
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    
    from .config import EvaluationConfig
    from ._data_loader import DataLoader
    
    # 設定初期化
    config = EvaluationConfig()
    config.ensure_directories()
    
    # DataLoader初期化
    loader = DataLoader(config)
    
    # テスト用レースID
    test_race_ids = ["202506040911"]
    
    # データ読み込み
    print("\n=== Loading Data ===")
    race_data_list = loader.get_all_race_data(test_race_ids)
    print(f"Loaded {len(race_data_list)} races")
    
    # Evaluator初期化
    evaluator = Evaluator(config)
    
    # 全戦略で評価
    print("\n=== Evaluating Strategies ===")
    results = evaluator.evaluate_all_strategies(race_data_list)
    
    # 結果表示
    print("\n=== Evaluation Results ===")
    for strategy_name, result in results.items():
        print(f"\n{strategy_name}:")
        print(f"  Races: {result.total_races}")
        print(f"  Horses: {result.total_horses}")
        print(f"  Hit Horses: {result.hit_horses}")
        print(f"  Accuracy: {result.accuracy:.2f}%")
        print(f"  Investment: {result.total_investment:,}円")
        print(f"  Payout: {result.total_payout:,}円")
        print(f"  ROI: {result.roi:.2f}%")
        print(f"  Profit: {result.profit:,}円")