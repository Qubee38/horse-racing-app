# backend/app/services/accuracy_calculation_service.py
"""
的中率計算サービス（Phase1修正版）

変更点:
    1. 順位ベース的中率を馬単位で計算
    2. 合計配当（total_payout）を追加
    3. 的中馬数・対象馬数を返却
    4. 馬場条件別統計を追加
"""

import logging
from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.race import Race
from app.models.horse import Horse
from app.models.prediction import Prediction
from app.models.race_result import RaceResult, HorseResult, Payout, BetType
from app.services.hit_criteria import HitCriteria

logger = logging.getLogger(__name__)


class AccuracyCalculationService:
    """的中率計算サービス"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_summary(
        self,
        start_date: date,
        end_date: date,
        win_threshold: float = 80.0,
        place_threshold: float = 85.0
    ) -> Dict:
        """
        全体サマリーを計算
        """
        logger.info(f"統計計算開始: {start_date} to {end_date}")
        
        # レース結果データ取得
        race_results = await self._get_race_results(start_date, end_date)
        logger.info(f"取得レース数: {len(race_results)}")
        
        if not race_results:
            return self._empty_summary(start_date, end_date)
        
        # 各レースの的中判定
        results = []
        for race_result in race_results:
            result = await self._judge_race(
                race_result,
                win_threshold,
                place_threshold
            )
            if result:
                results.append(result)
        
        logger.info(f"判定完了レース数: {len(results)}")
        
        if not results:
            logger.warning("判定可能なレースがありません")
            return self._empty_summary(start_date, end_date)
        
        # 統計計算
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_days": (end_date - start_date).days + 1
            },
            "by_rank": self._calculate_rank_based_stats(results),
            "by_probability": self._calculate_probability_based_stats(results, win_threshold, place_threshold),
            "probability_breakdown": self._calculate_probability_breakdown(results),
            "by_venue": self._calculate_by_venue(results, win_threshold, place_threshold),
            "by_grade": self._calculate_by_grade(results, win_threshold, place_threshold),
            "by_track_type": self._calculate_by_track_type(results, win_threshold, place_threshold),
            "by_distance": self._calculate_by_distance(results, win_threshold, place_threshold),
            "by_track_condition": self._calculate_by_track_condition(results, win_threshold, place_threshold)
        }
    
    async def _get_race_results(
        self,
        start_date: date,
        end_date: date
    ) -> List[RaceResult]:
        """
        レース結果データ取得
        
        完了済みレースのみを対象とし、削除されていないレースのみ取得
        """
        stmt = (
            select(RaceResult)
            .join(Race, RaceResult.race_id == Race.id)
            .where(
                and_(
                    RaceResult.race_status == "completed",
                    Race.race_date >= start_date,
                    Race.race_date <= end_date,
                    Race.id.isnot(None)  # レースが存在する（削除されていない）
                )
            )
            .options(
                selectinload(RaceResult.race),
                selectinload(RaceResult.horse_results).selectinload(HorseResult.horse),
                selectinload(RaceResult.payouts).selectinload(Payout.bet_type_ref)
            )
            .order_by(Race.race_date)
        )
        
        result = await self.db.execute(stmt)
        race_results = result.scalars().all()
        
        # さらに race が None でないものだけをフィルタ（念のため）
        return [rr for rr in race_results if rr.race is not None]
    
    async def _get_latest_predictions(self, race_id: int) -> List[Prediction]:
        """
        最新の予測データを取得（修正版）
        
        同じ予測バッチ内の全馬を取得するため、prediction_dateの前後1秒以内を対象
        """
        # 最新の予測日時を取得
        latest_date_stmt = (
            select(func.max(Prediction.prediction_date))
            .where(Prediction.race_id == race_id)
        )
        result = await self.db.execute(latest_date_stmt)
        latest_date = result.scalar_one_or_none()
        
        if not latest_date:
            return []
        
        # 最新予測の前後1秒以内の全データを取得
        # （マイクロ秒単位の差異を吸収するため）
        stmt = (
            select(Prediction)
            .where(
                and_(
                    Prediction.race_id == race_id,
                    Prediction.prediction_date >= latest_date - timedelta(seconds=1),
                    Prediction.prediction_date <= latest_date
                )
            )
            .order_by(Prediction.prediction_date.desc(), Prediction.win_probability.desc())
        )
        
        result = await self.db.execute(stmt)
        predictions = result.scalars().all()
        
        logger.debug(f"Race {race_id}: 取得した予測数 = {len(predictions)}, 最新日時 = {latest_date}")
        
        return predictions
    
    def _get_payout(self, payouts: List[Payout], bet_type_code: str) -> Optional[int]:
        """払い戻し額を取得"""
        for payout in payouts:
            if payout.bet_type_ref and payout.bet_type_ref.code == bet_type_code:
                return payout.payout_amount
        return None

    async def _judge_race(
        self,
        race_result: RaceResult,
        win_threshold: float,
        place_threshold: float
    ) -> Optional[Dict]:
        """1レースの的中判定"""
        try:
            # 予測データ取得
            predictions = await self._get_latest_predictions(race_result.race_id)
            if not predictions:
                logger.warning(f"予測データなし: race_id={race_result.race_id}")
                return None
            
            # 実際の結果を取得
            actual_winner_id = None
            actual_top3_ids = []
            
            for hr in race_result.horse_results:
                if hr.finish_position == 1:
                    actual_winner_id = hr.horse_id
                if hr.finish_position is not None and hr.finish_position <= 3:
                    if hr.horse_id:
                        actual_top3_ids.append(hr.horse_id)
            
            if not actual_winner_id:
                logger.warning(f"1着馬が見つからない: race_id={race_result.race_id}")
                return None
            
            # 配当情報
            win_payout = self._get_payout(race_result.payouts, "win")
            place_payout = self._get_payout(race_result.payouts, "place")
            
            # 【順位ベース】判定
            predicted_winner_id = predictions[0].horse_id if predictions else None
            predicted_top3_ids = [p.horse_id for p in predictions[:3] if p.horse_id]
            
            rank_win_hit = HitCriteria.is_win_hit_by_rank(
                predicted_winner_id,
                actual_winner_id
            )
            
            rank_place_hit_count = HitCriteria.count_place_hits_by_rank(
                predicted_top3_ids,
                actual_top3_ids
            )
            
            # 【確率閾値ベース】判定
            prob_win_hit = HitCriteria.is_win_hit_by_probability(
                predictions,
                actual_winner_id,
                win_threshold
            )
            
            # 【確率閾値ベース】単勝の的中馬数を取得
            prob_win_hit_count = HitCriteria.count_win_hits_by_probability(
                predictions,
                actual_winner_id,
                win_threshold
            )
            
            prob_place_hit = HitCriteria.is_place_hit_by_probability(
                predictions,
                actual_top3_ids,
                place_threshold
            )
            
            # 【確率閾値ベース】複勝の的中馬数を取得
            prob_place_hit_count = HitCriteria.count_place_hits_by_probability(
                predictions,
                actual_top3_ids,
                place_threshold
            )
            
            # 推奨馬の情報
            win_recommended_info = HitCriteria.get_recommended_horse_info(
                predictions, win_threshold, "win"
            )
            place_recommended_info = HitCriteria.get_recommended_horse_info(
                predictions, place_threshold, "place"
            )
            
            # デバッグログ
            if win_recommended_info:
                logger.debug(f"Race {race_result.race_id}: Win recommended info = {win_recommended_info}")
            if place_recommended_info:
                logger.debug(f"Race {race_result.race_id}: Place recommended info = {place_recommended_info}")
            
            # race オブジェクトから情報を取得
            race = race_result.race
            
            return {
                "race_id": race_result.race_id,
                "date": race.race_date,
                "venue": race.venue,
                "race_name": race.race_name,
                "grade": race.grade,
                "track_type": race.surface,
                "distance": race.distance,
                "track_condition": race.track_condition,  # 追加
                
                # 順位ベース
                "rank": {
                    "win_hit": rank_win_hit,
                    "place_hit": rank_place_hit_count > 0,
                    "place_hit_count": rank_place_hit_count,
                    "win_payout": win_payout if rank_win_hit else None,
                    "place_payout": place_payout if rank_place_hit_count > 0 else None
                },
                
                # 確率閾値ベース
                "probability": {
                    "win": {
                        "hit": prob_win_hit,
                        "hit_count": prob_win_hit_count if prob_win_hit_count is not None else 0,
                        "recommended": win_recommended_info is not None,
                        "count": win_recommended_info.get("count", 0) if win_recommended_info else 0,
                        "avg_probability": win_recommended_info.get("avg_probability") if win_recommended_info else None,
                        "payout": win_payout if prob_win_hit else None
                    },
                    "place": {
                        "hit": prob_place_hit,
                        "hit_count": prob_place_hit_count if prob_place_hit_count is not None else 0,
                        "recommended": place_recommended_info is not None,
                        "count": place_recommended_info.get("count", 0) if place_recommended_info else 0,
                        "avg_probability": place_recommended_info.get("avg_probability") if place_recommended_info else None,
                        "payout": place_payout if prob_place_hit else None
                    }
                },
                
                "payouts": {
                    "win": win_payout,
                    "place": place_payout
                }
            }
            
        except Exception as e:
            logger.error(f"レース判定エラー: race_id={race_result.race_id}, error={e}", exc_info=True)
            return None

    
    def _calculate_rank_based_stats(self, results: List[Dict]) -> Dict:
        """順位ベースの統計計算（馬単位）"""
        if not results:
            return self._empty_rank_stats()
        
        total_races = len(results)
        
        # ===== 単勝統計（馬単位） =====
        win_hit_horses = sum(1 for r in results if r["rank"]["win_hit"])
        total_win_horses = total_races  # 1レース = 1頭
        win_accuracy = (win_hit_horses / total_win_horses * 100) if total_win_horses > 0 else 0
        
        win_payouts = [r["rank"]["win_payout"] for r in results if r["rank"]["win_hit"] and r["rank"]["win_payout"]]
        win_total_payout = sum(win_payouts)
        win_avg_payout = win_total_payout / len(win_payouts) if win_payouts else 0
        win_roi = (win_total_payout / (total_races * 100) * 100) if total_races > 0 else 0
        
        # ===== 複勝統計（馬単位） =====
        place_hit_horses = sum(r["rank"]["place_hit_count"] for r in results)
        total_place_horses = total_races * 3  # 1レース = 3頭
        place_accuracy = (place_hit_horses / total_place_horses * 100) if total_place_horses > 0 else 0
        
        place_payouts = [r["rank"]["place_payout"] for r in results if r["rank"]["place_hit"] and r["rank"]["place_payout"]]
        place_total_payout = sum(place_payouts)
        place_avg_payout = place_total_payout / len(place_payouts) if place_payouts else 0
        place_roi = (place_total_payout / (total_races * 3 * 100) * 100) if total_races > 0 else 0
        
        return {
            "total_races": total_races,
            "win": {
                "hit_horses": win_hit_horses,
                "total_horses": total_win_horses,
                "hits": win_hit_horses,  # 後方互換性
                "accuracy": round(win_accuracy, 2),
                "total_payout": int(win_total_payout),
                "average_payout": round(win_avg_payout, 0),
                "roi": round(win_roi, 2)
            },
            "place": {
                "hit_horses": place_hit_horses,
                "total_horses": total_place_horses,
                "hits": len([r for r in results if r["rank"]["place_hit"]]),  # レース単位（後方互換性）
                "accuracy": round(place_accuracy, 2),
                "total_payout": int(place_total_payout),
                "average_payout": round(place_avg_payout, 0),
                "roi": round(place_roi, 2)
            }
        }

    def _calculate_probability_based_stats(
        self,
        results: List[Dict],
        win_threshold: float,
        place_threshold: float
    ) -> Dict:
        """確率閾値ベースの統計計算（馬単位）"""
        if not results:
            return self._empty_probability_stats(win_threshold, place_threshold)
        
        total_races = len(results)
        
        # ===== 単勝統計（馬単位）- 修正版 =====
        total_win_bets = 0
        win_hit_count = 0
        win_payouts_total = []
        win_probabilities = []
        
        for r in results:
            if r["probability"]["win"]["recommended"]:
                count = r["probability"]["win"]["count"]
                avg_prob = r["probability"]["win"].get("avg_probability")
                hit_count = r["probability"]["win"].get("hit_count", 0)
                
                # 推奨馬数を加算
                total_win_bets += count
                
                # 平均確率を記録
                if avg_prob is not None:
                    for _ in range(count):
                        win_probabilities.append(avg_prob)
                
                # 的中判定 - 実際に1着になった馬数を使用（0 or 1）
                if r["probability"]["win"]["hit"] and hit_count > 0:
                    win_hit_count += hit_count
                    
                    if r["probability"]["win"]["payout"] is not None:
                        win_payouts_total.append(r["probability"]["win"]["payout"])
        
        win_avg_prob = sum(win_probabilities) / len(win_probabilities) if win_probabilities else 0
        win_total_payout = sum(win_payouts_total)
        win_avg_payout = win_total_payout / len(win_payouts_total) if win_payouts_total else 0
        win_roi = (win_total_payout / (total_win_bets * 100) * 100) if total_win_bets > 0 else 0
        
        # ===== 複勝統計（馬単位） =====
        total_place_bets = 0
        place_hit_count = 0
        place_payouts_total = []
        place_probabilities = []
        
        for r in results:
            if r["probability"]["place"]["recommended"]:
                count = r["probability"]["place"]["count"]
                avg_prob = r["probability"]["place"]["avg_probability"]
                
                total_place_bets += count
                
                if avg_prob is not None:
                    for _ in range(count):
                        place_probabilities.append(avg_prob)
                
                if r["probability"]["place"]["hit"]:
                    place_hit_count += count
                    if r["probability"]["place"]["payout"] is not None:
                        place_payouts_total.append(r["probability"]["place"]["payout"])
        
        place_avg_prob = sum(place_probabilities) / len(place_probabilities) if place_probabilities else 0
        place_total_payout = sum(place_payouts_total)
        place_avg_payout = place_total_payout / len(place_payouts_total) if place_payouts_total else 0
        place_roi = (place_total_payout / (total_place_bets * 100) * 100) if total_place_bets > 0 else 0
        
        win_recommended_races = len([r for r in results if r["probability"]["win"]["recommended"]])
        place_recommended_races = len([r for r in results if r["probability"]["place"]["recommended"]])
        
        return {
            "win": {
                "threshold": win_threshold,
                "recommended_races": win_recommended_races,
                "recommended_horses": total_win_bets,
                "hit_horses": win_hit_count,
                "hits": win_hit_count,  # 後方互換性
                "accuracy": round((win_hit_count / total_win_bets * 100) if total_win_bets > 0 else 0, 2),
                "average_probability": round(win_avg_prob, 2),
                "total_payout": int(win_total_payout),
                "average_payout": round(win_avg_payout, 0),
                "roi": round(win_roi, 2),
                "no_recommendation_races": total_races - win_recommended_races
            },
            "place": {
                "threshold": place_threshold,
                "recommended_races": place_recommended_races,
                "recommended_horses": total_place_bets,
                "hit_horses": place_hit_count,
                "hits": place_hit_count,  # 後方互換性
                "accuracy": round((place_hit_count / total_place_bets * 100) if total_place_bets > 0 else 0, 2),
                "average_probability": round(place_avg_prob, 2),
                "total_payout": int(place_total_payout),
                "average_payout": round(place_avg_payout, 0),
                "roi": round(place_roi, 2),
                "no_recommendation_races": total_races - place_recommended_races
            }
        }

    def _calculate_probability_breakdown(self, results: List[Dict]) -> Dict:
        """確率範囲別の詳細統計"""
        win_ranges = {
            "90-100%": (90, 100),
            "80-90%": (80, 90),
            "70-80%": (70, 80),
            "60-70%": (60, 70),
            "50-60%": (50, 60),
            "40-50%": (40, 50)
        }
        
        place_ranges = {
            "95-100%": (95, 100),
            "85-95%": (85, 95),
            "75-85%": (75, 85),
            "65-75%": (65, 75),
            "55-65%": (55, 65)
        }
        
        def calc_range_stats(results, prob_key, ranges):
            breakdown = []
            for range_name, (min_prob, max_prob) in ranges.items():
                range_results = [
                    r for r in results
                    if "probability" in r
                    and prob_key in r["probability"]
                    and "probability" in r["probability"][prob_key]
                    and r["probability"][prob_key]["probability"] is not None
                    and min_prob <= r["probability"][prob_key]["probability"] < max_prob
                ]
                
                if range_results:
                    hits = [
                        r for r in range_results 
                        if "hit" in r["probability"][prob_key]
                        and r["probability"][prob_key]["hit"]
                    ]
                    payouts = [
                        r["probability"][prob_key]["payout"] 
                        for r in hits 
                        if "payout" in r["probability"][prob_key]
                        and r["probability"][prob_key]["payout"] is not None
                    ]
                    
                    breakdown.append({
                        "range": range_name,
                        "races": len(range_results),
                        "hits": len(hits),
                        "accuracy": round(len(hits) / len(range_results) * 100, 2),
                        "avg_payout": round(sum(payouts) / len(payouts), 0) if payouts else 0,
                        "roi": round(sum(payouts) / (len(range_results) * 100) * 100, 2) if range_results else 0
                    })
            
            return breakdown
    
        return {
            "win": calc_range_stats(results, "win", win_ranges),
            "place": calc_range_stats(results, "place", place_ranges)
        }

    
    def _calculate_by_venue(
        self,
        results: List[Dict],
        win_threshold: float,
        place_threshold: float
    ) -> List[Dict]:
        """競馬場別の統計"""
        venue_groups = defaultdict(list)
        for r in results:
            if r.get("venue"):
                venue_groups[r["venue"]].append(r)
        
        venue_stats = []
        for venue, venue_results in venue_groups.items():
            venue_stats.append({
                "venue": venue,
                "by_rank": self._calculate_rank_based_stats(venue_results),
                "by_probability": self._calculate_probability_based_stats(
                    venue_results, win_threshold, place_threshold
                )
            })
        
        # 総レース数でソート
        venue_stats.sort(key=lambda x: x["by_rank"]["total_races"], reverse=True)
        
        return venue_stats
    
    def _calculate_by_grade(
        self,
        results: List[Dict],
        win_threshold: float,
        place_threshold: float
    ) -> List[Dict]:
        """グレード別の統計"""
        grade_groups = defaultdict(list)
        for r in results:
            grade = r.get("grade") or "一般"
            grade_groups[grade].append(r)
        
        grade_stats = []
        for grade, grade_results in grade_groups.items():
            grade_stats.append({
                "grade": grade,
                "by_rank": self._calculate_rank_based_stats(grade_results),
                "by_probability": self._calculate_probability_based_stats(
                    grade_results, win_threshold, place_threshold
                )
            })
        
        # グレード順でソート（0〜10の数値順、それ以外は最後）
        def grade_sort_key(x):
            grade = x["grade"]
            # 数値に変換できる場合はその値、できない場合は99（最後）
            try:
                return int(grade)
            except (ValueError, TypeError):
                # G1, G2, G3などの場合も数値に変換
                grade_map = {"G1": 10, "G2": 9, "G3": 8, "OP": 7, "一般": 99}
                return grade_map.get(grade, 99)
        
        grade_stats.sort(key=grade_sort_key)
        
        return grade_stats
    
    def _calculate_by_track_type(
        self,
        results: List[Dict],
        win_threshold: float,
        place_threshold: float
    ) -> List[Dict]:
        """馬場種別の統計（ROI追加版）"""
        track_groups = defaultdict(list)
        for r in results:
            track_type = r.get("track_type")
            if track_type:
                track_groups[track_type].append(r)
        
        track_stats = []
        for track_type, track_results in track_groups.items():
            rank_stats = self._calculate_rank_based_stats(track_results)
            prob_stats = self._calculate_probability_based_stats(track_results, win_threshold, place_threshold)
            
            track_stats.append({
                "track_type": track_type,
                "total_races": rank_stats["total_races"],
                "win": {
                    "hit_horses": rank_stats["win"]["hit_horses"],
                    "total_horses": rank_stats["win"]["total_horses"],
                    "accuracy": rank_stats["win"]["accuracy"],
                    "roi": rank_stats["win"]["roi"]
                },
                "place": {
                    "hit_horses": rank_stats["place"]["hit_horses"],
                    "total_horses": rank_stats["place"]["total_horses"],
                    "accuracy": rank_stats["place"]["accuracy"],
                    "roi": rank_stats["place"]["roi"]
                }
            })
        
        return track_stats
    
    def _calculate_by_distance(
        self,
        results: List[Dict],
        win_threshold: float,
        place_threshold: float
    ) -> List[Dict]:
        """距離別の統計（ROI追加版）"""
        distance_ranges = {
            "1000-1200m": (1000, 1200),
            "1200-1400m": (1200, 1400),
            "1400-1600m": (1400, 1600),
            "1600-1800m": (1600, 1800),
            "1800-2000m": (1800, 2000),
            "2000-2200m": (2000, 2200),
            "2200-2400m": (2200, 2400),
            "2400m以上": (2400, 9999)
        }
        
        distance_stats = []
        for range_name, (min_dist, max_dist) in distance_ranges.items():
            range_results = [
                r for r in results
                if r.get("distance") and min_dist <= r["distance"] < max_dist
            ]
            
            if range_results:
                rank_stats = self._calculate_rank_based_stats(range_results)
                distance_stats.append({
                    "distance_range": range_name,
                    "total_races": rank_stats["total_races"],
                    "win": {
                        "hit_horses": rank_stats["win"]["hit_horses"],
                        "total_horses": rank_stats["win"]["total_horses"],
                        "accuracy": rank_stats["win"]["accuracy"],
                        "roi": rank_stats["win"]["roi"]
                    },
                    "place": {
                        "hit_horses": rank_stats["place"]["hit_horses"],
                        "total_horses": rank_stats["place"]["total_horses"],
                        "accuracy": rank_stats["place"]["accuracy"],
                        "roi": rank_stats["place"]["roi"]
                    }
                })
        
        return distance_stats
    
    def _calculate_by_track_condition(
        self,
        results: List[Dict],
        win_threshold: float,
        place_threshold: float
    ) -> List[Dict]:
        """馬場条件別の統計（新規追加）"""
        condition_groups = defaultdict(list)
        for r in results:
            condition = r.get("track_condition") or "不明"
            condition_groups[condition].append(r)
        
        condition_stats = []
        for condition, condition_results in condition_groups.items():
            rank_stats = self._calculate_rank_based_stats(condition_results)
            
            condition_stats.append({
                "track_condition": condition,
                "total_races": rank_stats["total_races"],
                "win": {
                    "hit_horses": rank_stats["win"]["hit_horses"],
                    "total_horses": rank_stats["win"]["total_horses"],
                    "accuracy": rank_stats["win"]["accuracy"],
                    "roi": rank_stats["win"]["roi"]
                },
                "place": {
                    "hit_horses": rank_stats["place"]["hit_horses"],
                    "total_horses": rank_stats["place"]["total_horses"],
                    "accuracy": rank_stats["place"]["accuracy"],
                    "roi": rank_stats["place"]["roi"]
                }
            })
        
        # 馬場条件の順序でソート
        condition_order = {"良": 0, "稍重": 1, "重": 2, "不良": 3, "不明": 99}
        condition_stats.sort(key=lambda x: condition_order.get(x["track_condition"], 99))
        
        return condition_stats
    
    def _empty_summary(self, start_date: date, end_date: date) -> Dict:
        """空のサマリー"""
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_days": (end_date - start_date).days + 1
            },
            "by_rank": self._empty_rank_stats(),
            "by_probability": self._empty_probability_stats(80.0, 85.0),
            "probability_breakdown": {"win": [], "place": []},
            "by_venue": [],
            "by_grade": [],
            "by_track_type": [],
            "by_distance": [],
            "by_track_condition": []
        }
    
    def _empty_rank_stats(self) -> Dict:
        """空の順位ベース統計"""
        return {
            "total_races": 0,
            "win": {
                "hit_horses": 0,
                "total_horses": 0,
                "hits": 0,
                "accuracy": 0.0,
                "total_payout": 0,
                "average_payout": 0.0,
                "roi": 0.0
            },
            "place": {
                "hit_horses": 0,
                "total_horses": 0,
                "hits": 0,
                "accuracy": 0.0,
                "total_payout": 0,
                "average_payout": 0.0,
                "roi": 0.0
            }
        }
    
    def _empty_probability_stats(self, win_threshold: float, place_threshold: float) -> Dict:
        """空の確率閾値ベース統計"""
        return {
            "win": {
                "threshold": win_threshold,
                "recommended_races": 0,
                "recommended_horses": 0,
                "hit_horses": 0,
                "hits": 0,
                "accuracy": 0.0,
                "average_probability": 0.0,
                "total_payout": 0,
                "average_payout": 0.0,
                "roi": 0.0,
                "no_recommendation_races": 0
            },
            "place": {
                "threshold": place_threshold,
                "recommended_races": 0,
                "recommended_horses": 0,
                "hit_horses": 0,
                "hits": 0,
                "accuracy": 0.0,
                "average_probability": 0.0,
                "total_payout": 0,
                "average_payout": 0.0,
                "roi": 0.0,
                "no_recommendation_races": 0
            }
        }