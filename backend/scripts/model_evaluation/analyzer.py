# backend/scripts/model_evaluation/analyzer.py

import logging
from typing import List, Dict
from collections import defaultdict

from .config import EvaluationConfig
from .data_loader import RaceData
from .evaluator import Evaluator, StrategyResult

logger = logging.getLogger(__name__)


class ConditionalAnalyzer:
    """
    条件別分析クラス
    
    5種類の条件でレースをグループ化し、各条件で14パターンの投資戦略を評価
    """
    
    def __init__(self, config: EvaluationConfig, evaluator: Evaluator):
        """
        Parameters
        ----------
        config : EvaluationConfig
            評価設定
        evaluator : Evaluator
            評価器（14パターンの評価ロジック）
        """
        self.config = config
        self.evaluator = evaluator
    
    # ========================================
    # 1. 競馬場別分析
    # ========================================
    
    def analyze_by_venue(self, race_data_list: List[RaceData]) -> Dict[str, Dict[str, StrategyResult]]:
        """
        競馬場別に分析
        
        Parameters
        ----------
        race_data_list : List[RaceData]
            全レースデータ
        
        Returns
        -------
        Dict[str, Dict[str, StrategyResult]]
            {"東京": {"rank_based_win": StrategyResult, ...}, ...}
        """
        logger.info("=== Analyzing by Venue ===")
        
        # レースを競馬場ごとにグループ化
        races_by_venue = self._group_by_venue(race_data_list)
        
        logger.info(f"Found {len(races_by_venue)} venues")
        for venue, races in races_by_venue.items():
            logger.info(f"  {venue}: {len(races)} races")
        
        # 各競馬場で14パターン評価
        results = {}
        for venue, races in races_by_venue.items():
            if len(races) > 0:
                logger.info(f"Evaluating venue: {venue}")
                results[venue] = self.evaluator.evaluate_all_strategies(races)
        
        return results
    
    def _group_by_venue(self, race_data_list: List[RaceData]) -> Dict[str, List[RaceData]]:
        """レースを競馬場ごとにグループ化"""
        grouped = defaultdict(list)
        
        for race_data in race_data_list:
            # predictions_dfから競馬場を取得
            if '競馬場' in race_data.predictions_df.columns:
                venue = str(race_data.predictions_df['競馬場'].iloc[0])
            else:
                venue = race_data.race_info.get('location', '不明')
            
            grouped[venue].append(race_data)
        
        return dict(grouped)
    
    # ========================================
    # 2. グレード別分析
    # ========================================
    
    def analyze_by_grade(self, race_data_list: List[RaceData]) -> Dict[str, Dict[str, StrategyResult]]:
        """
        グレード別に分析
        
        Returns
        -------
        Dict[str, Dict[str, StrategyResult]]
            {"G1": {"rank_based_win": StrategyResult, ...}, ...}
        """
        logger.info("=== Analyzing by Grade ===")
        
        # レースをグレードごとにグループ化
        races_by_grade = self._group_by_grade(race_data_list)
        
        logger.info(f"Found {len(races_by_grade)} grades")
        for grade, races in races_by_grade.items():
            logger.info(f"  {grade}: {len(races)} races")
        
        # 各グレードで14パターン評価
        results = {}
        for grade, races in races_by_grade.items():
            if len(races) > 0:
                logger.info(f"Evaluating grade: {grade}")
                results[grade] = self.evaluator.evaluate_all_strategies(races)
        
        return results
    
    def _group_by_grade(self, race_data_list: List[RaceData]) -> Dict[str, List[RaceData]]:
        """レースをグレードごとにグループ化"""
        grouped = defaultdict(list)
        
        for race_data in race_data_list:
            # predictions_dfからグレードを取得
            if 'グレード' in race_data.predictions_df.columns:
                grade_value = race_data.predictions_df['グレード'].iloc[0]
            else:
                grade_value = race_data.race_info.get('race_rank', 0)
            
            # 数値をグレード名に変換
            grade_str = str(int(grade_value)) if grade_value is not None else "0"
            grade_name = self.config.GRADE_MAPPING.get(grade_str, f"不明({grade_str})")
            
            grouped[grade_name].append(race_data)
        
        return dict(grouped)
    
    # ========================================
    # 3. トラック別分析
    # ========================================
    
    def analyze_by_track_type(self, race_data_list: List[RaceData]) -> Dict[str, Dict[str, StrategyResult]]:
        """
        トラック別（芝/ダート）に分析
        
        Returns
        -------
        Dict[str, Dict[str, StrategyResult]]
            {"芝": {"rank_based_win": StrategyResult, ...}, ...}
        """
        logger.info("=== Analyzing by Track Type ===")
        
        # レースをトラック種別ごとにグループ化
        races_by_track = self._group_by_track_type(race_data_list)
        
        logger.info(f"Found {len(races_by_track)} track types")
        for track_type, races in races_by_track.items():
            logger.info(f"  {track_type}: {len(races)} races")
        
        # 各トラック種別で14パターン評価
        results = {}
        for track_type, races in races_by_track.items():
            if len(races) > 0:
                logger.info(f"Evaluating track type: {track_type}")
                results[track_type] = self.evaluator.evaluate_all_strategies(races)
        
        return results
    
    def _group_by_track_type(self, race_data_list: List[RaceData]) -> Dict[str, List[RaceData]]:
        """レースをトラック種別ごとにグループ化"""
        grouped = defaultdict(list)
        
        for race_data in race_data_list:
            # predictions_dfからトラック種別を取得
            if '芝ダート' in race_data.predictions_df.columns:
                track_type_value = race_data.predictions_df['芝ダート'].iloc[0]
            else:
                track_type_value = race_data.race_info.get('track_type', 0)
            
            # 数値をトラック種別名に変換
            # 0: 芝, 1: ダート（StatisticsPageの定義に従う）
            if track_type_value == 0 or track_type_value == '0':
                track_type = '芝'
            elif track_type_value == 1 or track_type_value == '1':
                track_type = 'ダート'
            else:
                track_type = f'不明({track_type_value})'
            
            grouped[track_type].append(race_data)
        
        return dict(grouped)
    
    # ========================================
    # 4. 距離別分析
    # ========================================
    
    def analyze_by_distance(self, race_data_list: List[RaceData]) -> Dict[str, Dict[str, StrategyResult]]:
        """
        距離別に分析
        
        Returns
        -------
        Dict[str, Dict[str, StrategyResult]]
            {"1000m-1400m": {"rank_based_win": StrategyResult, ...}, ...}
        """
        logger.info("=== Analyzing by Distance ===")
        
        # レースを距離範囲ごとにグループ化
        races_by_distance = self._group_by_distance(race_data_list)
        
        logger.info(f"Found {len(races_by_distance)} distance ranges")
        for distance_range, races in races_by_distance.items():
            logger.info(f"  {distance_range}: {len(races)} races")
        
        # 各距離範囲で14パターン評価
        results = {}
        for distance_range, races in races_by_distance.items():
            if len(races) > 0:
                logger.info(f"Evaluating distance range: {distance_range}")
                results[distance_range] = self.evaluator.evaluate_all_strategies(races)
        
        return results
    
    def _group_by_distance(self, race_data_list: List[RaceData]) -> Dict[str, List[RaceData]]:
        """レースを距離範囲ごとにグループ化"""
        grouped = defaultdict(list)
        
        for race_data in race_data_list:
            # predictions_dfから距離を取得
            if '距離' in race_data.predictions_df.columns:
                distance_value = race_data.predictions_df['距離'].iloc[0]
            else:
                distance_value = race_data.race_info.get('distance', 1600)
            
            # 距離を整数に変換
            try:
                distance = int(float(str(distance_value)))
            except (ValueError, TypeError):
                distance = 1600  # デフォルト
            
            # 距離範囲を特定
            distance_range = self._get_distance_range(distance)
            grouped[distance_range].append(race_data)
        
        return dict(grouped)
    
    def _get_distance_range(self, distance: int) -> str:
        """距離から距離範囲名を取得"""
        for range_name, min_dist, max_dist in self.config.DISTANCE_RANGES:
            if min_dist <= distance <= max_dist:
                return range_name
        
        return f"不明({distance}m)"
    
    # ========================================
    # 5. 馬場状態別分析（オプション）
    # ========================================
    
    def analyze_by_track_condition(self, race_data_list: List[RaceData]) -> Dict[str, Dict[str, StrategyResult]]:
        """
        馬場状態別に分析
        
        注意: predictions_dfに馬場状態が含まれていない場合はスキップ
        
        Returns
        -------
        Dict[str, Dict[str, StrategyResult]]
            {"良": {"rank_based_win": StrategyResult, ...}, ...}
        """
        logger.info("=== Analyzing by Track Condition ===")
        
        # レースを馬場状態ごとにグループ化
        races_by_condition = self._group_by_track_condition(race_data_list)
        
        if not races_by_condition:
            logger.warning("No track condition data available, skipping analysis")
            return {}
        
        logger.info(f"Found {len(races_by_condition)} track conditions")
        for condition, races in races_by_condition.items():
            logger.info(f"  {condition}: {len(races)} races")
        
        # 各馬場状態で14パターン評価
        results = {}
        for condition, races in races_by_condition.items():
            if len(races) > 0:
                logger.info(f"Evaluating track condition: {condition}")
                results[condition] = self.evaluator.evaluate_all_strategies(races)
        
        return results
    
    def _group_by_track_condition(self, race_data_list: List[RaceData]) -> Dict[str, List[RaceData]]:
        """レースを馬場状態ごとにグループ化"""
        grouped = defaultdict(list)
        
        for race_data in race_data_list:
            # predictions_dfから馬場状態を取得
            if '馬場' in race_data.predictions_df.columns:
                condition_value = race_data.predictions_df['馬場'].iloc[0]
            elif 'baba' in race_data.predictions_df.columns:
                condition_value = race_data.predictions_df['baba'].iloc[0]
            else:
                # 馬場状態データがない場合はスキップ
                continue
            
            # 数値を馬場状態名に変換
            # 0: 良, 1: 稍重, 2: 重, 3: 不良
            condition_mapping = {
                0: '良', 1: '稍重', 2: '重', 3: '不良',
                '0': '良', '1': '稍重', '2': '重', '3': '不良'
            }
            
            condition = condition_mapping.get(condition_value, f'不明({condition_value})')
            grouped[condition].append(race_data)
        
        return dict(grouped)
    
    # ========================================
    # ユーティリティメソッド
    # ========================================
    
    def get_statistics(self, conditional_results: Dict[str, Dict[str, StrategyResult]]) -> Dict:
        """
        条件別分析の統計情報を取得
        
        Parameters
        ----------
        conditional_results : Dict
            条件別分析結果
        
        Returns
        -------
        Dict
            統計情報
        """
        total_conditions = len(conditional_results)
        total_races = sum(
            list(strategies.values())[0].total_races 
            for strategies in conditional_results.values() 
            if strategies
        )
        
        return {
            'total_conditions': total_conditions,
            'total_races': total_races,
            'conditions': list(conditional_results.keys())
        }


# ========================================
# テスト用コード
# ========================================
if __name__ == "__main__":
    import logging
    from .config import EvaluationConfig
    from .data_loader import DataLoader
    from .evaluator import Evaluator
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 設定初期化
    config = EvaluationConfig()
    config.ensure_directories()
    
    # データローダー初期化
    loader = DataLoader(config)
    
    # テスト用レースID
    test_race_ids = [
        "202506040901",
        "202506040902",
        "202506040903"
    ]
    
    # データ準備
    print("=== Phase 0: Data Preparation ===")
    valid_race_ids = loader.prepare_evaluation_data(test_race_ids)
    
    # データ読み込み
    print("\n=== Phase 1: Data Loading ===")
    race_data_list = loader.get_all_race_data(valid_race_ids)
    
    # 評価器初期化
    evaluator = Evaluator(config)
    
    # 条件別分析器初期化
    analyzer = ConditionalAnalyzer(config, evaluator)
    
    # 条件別分析実行
    print("\n=== Phase 3: Conditional Analysis ===")
    
    # 競馬場別
    venue_results = analyzer.analyze_by_venue(race_data_list)
    print(f"\nVenue analysis: {len(venue_results)} venues")
    
    # グレード別
    grade_results = analyzer.analyze_by_grade(race_data_list)
    print(f"Grade analysis: {len(grade_results)} grades")
    
    # トラック別
    track_results = analyzer.analyze_by_track_type(race_data_list)
    print(f"Track type analysis: {len(track_results)} track types")
    
    # 距離別
    distance_results = analyzer.analyze_by_distance(race_data_list)
    print(f"Distance analysis: {len(distance_results)} distance ranges")
    
    # 馬場状態別
    condition_results = analyzer.analyze_by_track_condition(race_data_list)
    print(f"Track condition analysis: {len(condition_results)} conditions")