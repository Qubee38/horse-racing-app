# backend/app/services/hit_criteria.py
"""
的中判定基準（修正版）

順位ベースと確率閾値ベースの2つの判定方式を提供
"""

from typing import List, Optional, Dict
from app.models.prediction import Prediction


class HitCriteria:
    """的中判定基準"""
    
    # デフォルト閾値
    DEFAULT_WIN_THRESHOLD = 80.0   # 単勝推奨閾値（%）
    DEFAULT_PLACE_THRESHOLD = 85.0 # 複勝推奨閾値（%）
    
    @staticmethod
    def is_win_hit_by_rank(predicted_horse_id: Optional[int], actual_winner_id: Optional[int]) -> bool:
        """
        【順位ベース】単勝的中: 予測1位が実際の1着
        
        Args:
            predicted_horse_id: 予測1位の馬ID
            actual_winner_id: 実際の1着馬ID
        
        Returns:
            True: 的中, False: 不的中
        """
        if predicted_horse_id is None or actual_winner_id is None:
            return False
        return predicted_horse_id == actual_winner_id
    
    @staticmethod
    def is_place_hit_by_rank(
        predicted_top3_ids: List[int],
        actual_top3_ids: List[int]
    ) -> bool:
        """
        【順位ベース】複勝的中: 予測上位3頭のいずれかが実際の3着以内
        
        Args:
            predicted_top3_ids: 予測上位3頭の馬ID
            actual_top3_ids: 実際の3着以内の馬ID
        
        Returns:
            True: 的中（1頭以上）, False: 不的中
        """
        if not predicted_top3_ids or not actual_top3_ids:
            return False
        return any(pid in actual_top3_ids for pid in predicted_top3_ids)
    
    @staticmethod
    def count_place_hits_by_rank(
        predicted_top3_ids: List[int],
        actual_top3_ids: List[int]
    ) -> int:
        """
        【順位ベース】複勝的中数: 何頭的中したか
        
        Returns:
            0-3の整数
        """
        if not predicted_top3_ids or not actual_top3_ids:
            return 0
        return sum(1 for pid in predicted_top3_ids if pid in actual_top3_ids)
    
    @staticmethod
    def is_win_hit_by_probability(
        predictions: List[Prediction],
        actual_winner_id: Optional[int],
        threshold: float = DEFAULT_WIN_THRESHOLD
    ) -> Optional[bool]:
        """
        【確率閾値ベース】単勝的中
        
        Args:
            predictions: 予測結果リスト
            actual_winner_id: 実際の1着馬ID
            threshold: 推奨閾値（%）
        
        Returns:
            True: 高確率推奨馬のいずれかが的中
            False: 高確率推奨馬が外れ
            None: 推奨基準を満たす馬がいない（判定対象外）
        """
        if not predictions or actual_winner_id is None:
            return None
        
        # 閾値を超える馬を全て抽出
        high_prob_horses = [
            p for p in predictions 
            if p.win_probability is not None and p.win_probability >= threshold
        ]
        
        if not high_prob_horses:
            return None  # 推奨馬なし
        
        # 推奨馬のいずれかが1着なら的中
        recommended_ids = [p.horse_id for p in high_prob_horses]
        return actual_winner_id in recommended_ids
    
    @staticmethod
    def count_win_hits_by_probability(
        predictions: List[Prediction],
        actual_winner_id: Optional[int],
        threshold: float = DEFAULT_WIN_THRESHOLD
    ) -> Optional[int]:
        """
        【確率閾値ベース】単勝的中数
        
        Returns:
            int: 的中した推奨馬の数（0 or 1）
            None: 推奨馬がいない
        """
        if not predictions or actual_winner_id is None:
            return None
        
        high_prob_horses = [
            p for p in predictions 
            if p.win_probability is not None and p.win_probability >= threshold
        ]
        
        if not high_prob_horses:
            return None
        
        # 推奨馬のいずれかが1着なら1、外れなら0
        recommended_ids = [p.horse_id for p in high_prob_horses]
        return 1 if actual_winner_id in recommended_ids else 0
    
    @staticmethod
    def is_place_hit_by_probability(
        predictions: List[Prediction],
        actual_top3_ids: List[int],
        threshold: float = DEFAULT_PLACE_THRESHOLD
    ) -> Optional[bool]:
        """
        【確率閾値ベース】複勝的中
        
        Args:
            predictions: 予測結果リスト
            actual_top3_ids: 実際の3着以内の馬ID
            threshold: 推奨閾値（%）
        
        Returns:
            True: 高確率推奨馬が3着以内
            False: 高確率推奨馬が4着以下
            None: 推奨基準を満たす馬がいない
        """
        if not predictions or not actual_top3_ids:
            return None
        
        high_prob_horses = [
            p for p in predictions 
            if p.place_probability is not None and p.place_probability >= threshold
        ]
        
        if not high_prob_horses:
            return None
        
        # 推奨馬のIDリスト
        recommended_ids = [p.horse_id for p in high_prob_horses]
        
        # 少なくとも1頭が3着以内なら的中
        return any(horse_id in actual_top3_ids for horse_id in recommended_ids)
    
    @staticmethod
    def count_place_hits_by_probability(
        predictions: List[Prediction],
        actual_top3_ids: List[int],
        threshold: float = DEFAULT_PLACE_THRESHOLD
    ) -> Optional[int]:
        """
        【確率閾値ベース】複勝的中数
        
        Returns:
            int: 的中した推奨馬の数（0-3）
            None: 推奨馬がいない
        """
        if not predictions or not actual_top3_ids:
            return None
        
        high_prob_horses = [
            p for p in predictions 
            if p.place_probability is not None and p.place_probability >= threshold
        ]
        
        if not high_prob_horses:
            return None
        
        recommended_ids = [p.horse_id for p in high_prob_horses]
        return sum(1 for horse_id in recommended_ids if horse_id in actual_top3_ids)
    
    @staticmethod
    def get_recommended_horse_info(
        predictions: List[Prediction],
        threshold: float,
        prob_type: str = "win"
    ) -> Optional[Dict]:
        """
        推奨馬の情報を取得（修正版: 単勝も複数頭対応）
        
        Args:
            predictions: 予測結果リスト
            threshold: 閾値
            prob_type: "win" or "place"
        
        Returns:
            推奨馬情報 or None
        """
        if not predictions:
            return None
        
        if prob_type == "win":
            high_prob_horses = [
                p for p in predictions 
                if p.win_probability is not None and p.win_probability >= threshold
            ]
            if not high_prob_horses:
                return None
            
            # 全ての推奨馬の平均確率を返す
            avg_prob = sum(p.win_probability for p in high_prob_horses) / len(high_prob_horses)
            return {
                "count": len(high_prob_horses),
                "avg_probability": avg_prob,
                "horse_ids": [p.horse_id for p in high_prob_horses]
            }
        else:  # place
            high_prob_horses = [
                p for p in predictions 
                if p.place_probability is not None and p.place_probability >= threshold
            ]
            if not high_prob_horses:
                return None
            
            avg_prob = sum(p.place_probability for p in high_prob_horses) / len(high_prob_horses)
            return {
                "count": len(high_prob_horses),
                "avg_probability": avg_prob,
                "horse_ids": [p.horse_id for p in high_prob_horses]
            }