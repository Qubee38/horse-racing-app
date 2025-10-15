# backend/scripts/model_evaluation/reporter.py

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .config import EvaluationConfig
from .evaluator import StrategyResult

logger = logging.getLogger(__name__)


class Reporter:
    """レポート出力クラス"""
    
    def __init__(self, config: EvaluationConfig):
        """
        Parameters
        ----------
        config : EvaluationConfig
            評価設定
        """
        self.config = config
        self.timestamp = datetime.now().strftime(config.TIMESTAMP_FORMAT)
    
    # ========================================
    # コンソール出力
    # ========================================
    
    def print_summary(self, results: Dict[str, StrategyResult]):
        """
        評価結果のサマリーをコンソール出力
        
        Parameters
        ----------
        results : Dict[str, StrategyResult]
            戦略名 -> 評価結果のマップ
        """
        print("\n" + "=" * 80)
        print("Model Evaluation Summary")
        print("=" * 80)
        
        # 予想順位ベース
        print("\n【予想順位ベース】")
        self._print_rank_based_results(results)
        
        # 確率閾値ベース
        print("\n【確率閾値ベース】")
        self._print_threshold_based_results(results)
        
        print("\n" + "=" * 80)
    
    def _print_rank_based_results(self, results: Dict[str, StrategyResult]):
        """予想順位ベースの結果を出力"""
        # 単勝
        if 'rank_based_win' in results:
            result = results['rank_based_win']
            print("\n■単勝:")
            print(f"  レース数: {result.total_races}")
            print(f"  推奨馬数: {result.total_horses}")
            print(f"  的中馬数: {result.hit_horses}")
            print(f"  的中率: {result.accuracy:.2f}%")
            print(f"  投資額: {result.total_investment:,}円")
            print(f"  払戻額: {result.total_payout:,}円")
            print(f"  収支: {result.profit:+,}円")
            print(f"  ROI: {result.roi:.2f}%")
        
        # 複勝
        if 'rank_based_place' in results:
            result = results['rank_based_place']
            print("\n■複勝:")
            print(f"  レース数: {result.total_races}")
            print(f"  推奨馬数: {result.total_horses}")
            print(f"  的中馬数: {result.hit_horses}")
            print(f"  的中率: {result.accuracy:.2f}%")
            print(f"  投資額: {result.total_investment:,}円")
            print(f"  払戻額: {result.total_payout:,}円")
            print(f"  収支: {result.profit:+,}円")
            print(f"  ROI: {result.roi:.2f}%")
    
    def _print_threshold_based_results(self, results: Dict[str, StrategyResult]):
        """確率閾値ベースの結果を出力"""
        # 単勝
        print("\n■単勝")
        
        for model_type in ['win_model', 'place_model']:
            print(f"\n  {model_type}:")
            
            thresholds = self.config.PROBABILITY_THRESHOLDS['win'][model_type]
            for threshold in thresholds:
                strategy_name = f"threshold_{model_type}_{int(threshold)}_win"
                
                if strategy_name in results:
                    result = results[strategy_name]
                    
                    if result.total_races > 0:
                        print(f"    閾値{int(threshold)}%: "
                              f"ROI {result.roi:6.2f}% "
                              f"({result.hit_horses}/{result.total_horses}, "
                              f"投資{result.total_investment:,}円)")
                    else:
                        print(f"    閾値{int(threshold)}%: 推奨なし")
        
        # 複勝
        print("\n■複勝")
        
        for model_type in ['win_model', 'place_model']:
            print(f"\n  {model_type}:")
            
            thresholds = self.config.PROBABILITY_THRESHOLDS['place'][model_type]
            for threshold in thresholds:
                strategy_name = f"threshold_{model_type}_{int(threshold)}_place"
                
                if strategy_name in results:
                    result = results[strategy_name]
                    
                    if result.total_races > 0:
                        print(f"    閾値{int(threshold)}%: "
                              f"ROI {result.roi:6.2f}% "
                              f"({result.hit_horses}/{result.total_horses}, "
                              f"投資{result.total_investment:,}円)")
                    else:
                        print(f"    閾値{int(threshold)}%: 推奨なし")
    
    # ========================================
    # CSVレポート生成
    # ========================================
    
    def generate_summary_report(self, results: Dict[str, StrategyResult]) -> Path:
        """
        サマリーレポートを生成
        
        Parameters
        ----------
        results : Dict[str, StrategyResult]
            戦略名 -> 評価結果のマップ
        
        Returns
        -------
        Path
            生成されたCSVファイルのパス
        """
        csv_path = self.config.get_report_filename('summary', self.timestamp)
        
        try:
            with open(csv_path, 'w', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f)
                
                # ヘッダー
                writer.writerow([
                    '戦略名',
                    '券種',
                    'モデル',
                    '閾値(%)',
                    'レース数',
                    '推奨馬数',
                    '的中馬数',
                    '的中率(%)',
                    '投資額(円)',
                    '払戻額(円)',
                    '収支(円)',
                    'ROI(%)'
                ])
                
                # データ行
                for strategy_name, result in results.items():
                    model_type = result.model_type if result.model_type else '-'
                    threshold = int(result.threshold) if result.threshold else '-'
                    
                    writer.writerow([
                        strategy_name,
                        result.bet_type,
                        model_type,
                        threshold,
                        result.total_races,
                        result.total_horses,
                        result.hit_horses,
                        f"{result.accuracy:.2f}",
                        result.total_investment,
                        result.total_payout,
                        result.profit,
                        f"{result.roi:.2f}"
                    ])
            
            logger.info(f"Summary report generated: {csv_path}")
            return csv_path
        
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            raise
    
    def generate_race_details_report(self, results: Dict[str, StrategyResult]) -> Path:
        """
        レース別詳細レポートを生成
        
        Parameters
        ----------
        results : Dict[str, StrategyResult]
            戦略名 -> 評価結果のマップ
        
        Returns
        -------
        Path
            生成されたCSVファイルのパス
        """
        csv_path = self.config.get_report_filename('race_details', self.timestamp)
        
        try:
            with open(csv_path, 'w', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f)
                
                # ヘッダー
                writer.writerow([
                    'レースID',
                    '戦略名',
                    '券種',
                    '推奨馬番',
                    '的中馬番',
                    '投資額(円)',
                    '払戻額(円)',
                    'ROI(%)'
                ])
                
                # データ行
                for strategy_name, result in results.items():
                    for bet_result in result.bet_results:
                        recommended_str = ','.join(map(str, bet_result.recommended_horses))
                        hit_str = ','.join(map(str, bet_result.hit_horses)) if bet_result.hit_horses else '-'
                        
                        writer.writerow([
                            bet_result.race_id,
                            strategy_name,
                            bet_result.bet_type,
                            recommended_str,
                            hit_str,
                            bet_result.investment,
                            bet_result.payout,
                            f"{bet_result.roi:.2f}"
                        ])
            
            logger.info(f"Race details report generated: {csv_path}")
            return csv_path
        
        except Exception as e:
            logger.error(f"Failed to generate race details report: {e}")
            raise
    
    # ========================================
    # 🔧 条件別レポート生成（新規追加）
    # ========================================
    
    def generate_conditional_report(
        self,
        condition_name: str,
        conditional_results: Dict[str, Dict[str, StrategyResult]]
    ) -> Path:
        """
        条件別レポートを生成
        
        Parameters
        ----------
        condition_name : str
            条件名（'venue', 'grade', 'track_type', 'distance', 'condition'）
        conditional_results : Dict[str, Dict[str, StrategyResult]]
            条件値 -> {戦略名 -> 評価結果} のマップ
        
        Returns
        -------
        Path
            生成されたCSVファイルのパス
        """
        csv_path = self.config.get_report_filename(f'by_{condition_name}', self.timestamp)
        
        try:
            with open(csv_path, 'w', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f)
                
                # ヘッダー
                writer.writerow([
                    condition_name,
                    '戦略名',
                    '券種',
                    'モデル',
                    '閾値(%)',
                    'レース数',
                    '推奨馬数',
                    '的中馬数',
                    '的中率(%)',
                    '投資額(円)',
                    '払戻額(円)',
                    '収支(円)',
                    'ROI(%)'
                ])
                
                # データ行
                for condition_value, strategies in conditional_results.items():
                    for strategy_name, result in strategies.items():
                        model_type = result.model_type if result.model_type else '-'
                        threshold = int(result.threshold) if result.threshold else '-'
                        
                        writer.writerow([
                            condition_value,
                            strategy_name,
                            result.bet_type,
                            model_type,
                            threshold,
                            result.total_races,
                            result.total_horses,
                            result.hit_horses,
                            f"{result.accuracy:.2f}",
                            result.total_investment,
                            result.total_payout,
                            result.profit,
                            f"{result.roi:.2f}"
                        ])
            
            logger.info(f"Conditional report ({condition_name}) generated: {csv_path}")
            return csv_path
        
        except Exception as e:
            logger.error(f"Failed to generate conditional report ({condition_name}): {e}")
            raise
    
    # ========================================
    # 🔧 全レポート生成（修正版）
    # ========================================
    
    def generate_all_reports(
        self,
        overall_results: Dict[str, StrategyResult],
        venue_results: Optional[Dict[str, Dict[str, StrategyResult]]] = None,
        grade_results: Optional[Dict[str, Dict[str, StrategyResult]]] = None,
        track_results: Optional[Dict[str, Dict[str, StrategyResult]]] = None,
        distance_results: Optional[Dict[str, Dict[str, StrategyResult]]] = None,
        condition_results: Optional[Dict[str, Dict[str, StrategyResult]]] = None
    ) -> Dict[str, Path]:
        """
        全てのレポートを生成
        
        Parameters
        ----------
        overall_results : Dict[str, StrategyResult]
            全体評価結果（戦略名 -> 評価結果）
        venue_results : Optional[Dict]
            競馬場別分析結果
        grade_results : Optional[Dict]
            グレード別分析結果
        track_results : Optional[Dict]
            トラック別分析結果
        distance_results : Optional[Dict]
            距離別分析結果
        condition_results : Optional[Dict]
            馬場状態別分析結果
        
        Returns
        -------
        Dict[str, Path]
            レポート種類 -> ファイルパスのマップ
        """
        logger.info("=== Generating Reports ===")
        
        report_paths = {}
        
        # 1. 全体評価レポート
        logger.info("Generating overall reports...")
        report_paths['summary'] = self.generate_summary_report(overall_results)
        report_paths['race_details'] = self.generate_race_details_report(overall_results)
        
        # 2. 条件別レポート
        if venue_results:
            logger.info("Generating venue report...")
            report_paths['by_venue'] = self.generate_conditional_report('venue', venue_results)
        
        if grade_results:
            logger.info("Generating grade report...")
            report_paths['by_grade'] = self.generate_conditional_report('grade', grade_results)
        
        if track_results:
            logger.info("Generating track type report...")
            report_paths['by_track_type'] = self.generate_conditional_report('track_type', track_results)
        
        if distance_results:
            logger.info("Generating distance report...")
            report_paths['by_distance'] = self.generate_conditional_report('distance', distance_results)
        
        if condition_results:
            logger.info("Generating track condition report...")
            report_paths['by_track_condition'] = self.generate_conditional_report('track_condition', condition_results)
        
        logger.info(f"All reports generated: {len(report_paths)} files")
        
        return report_paths


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
    from .data_loader import DataLoader
    from .evaluator import Evaluator
    
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
    
    # Reporter初期化
    reporter = Reporter(config)
    
    # コンソール出力
    reporter.print_summary(results)
    
    # CSVレポート生成
    print("\n=== Generating Reports ===")
    report_paths = reporter.generate_all_reports(results)
    
    print("\n=== Generated Reports ===")
    for report_type, path in report_paths.items():
        print(f"{report_type}: {path}")