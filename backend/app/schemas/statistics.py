# backend/app/schemas/statistics.py
"""
統計データのスキーマ定義（Phase1修正版）

変更点:
    1. BetTypeStatsに hit_horses, total_horses, total_payout 追加
    2. TrackTypeStats, DistanceRangeStats を詳細化
    3. TrackConditionStats を新規追加
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class PeriodInfo(BaseModel):
    """期間情報"""
    start_date: str
    end_date: str
    total_days: int


class BetTypeStats(BaseModel):
    """券種別統計（順位ベース）"""
    hit_horses: int = Field(description="的中馬数")
    total_horses: int = Field(description="対象馬数")
    hits: int = Field(description="的中数（後方互換性）")
    accuracy: float = Field(description="的中率（%）")
    total_payout: int = Field(description="合計配当（円）")
    average_payout: float = Field(description="平均配当（円）")
    roi: float = Field(description="回収率（%）")


class RankBasedStats(BaseModel):
    """順位ベースの統計"""
    total_races: int = Field(description="総レース数")
    win: BetTypeStats = Field(description="単勝統計")
    place: BetTypeStats = Field(description="複勝統計")


class ProbabilityBasedBetStats(BaseModel):
    """確率閾値ベースの券種別統計（馬単位）"""
    threshold: float = Field(description="使用した閾値（%）")
    recommended_races: int = Field(description="推奨基準を満たしたレース数（参考）")
    recommended_horses: int = Field(description="推奨馬数（メイン指標）")
    hit_horses: int = Field(description="的中馬数")
    hits: int = Field(description="的中数（後方互換性）")
    accuracy: float = Field(description="的中率（%）= 的中馬数 / 推奨馬数")
    average_probability: float = Field(description="推奨時の平均確率（%）")
    total_payout: int = Field(description="合計配当（円）")
    average_payout: float = Field(description="平均配当（円）")
    roi: float = Field(description="回収率（%）")
    no_recommendation_races: int = Field(description="推奨しなかったレース数")


class ProbabilityBasedStats(BaseModel):
    """確率閾値ベースの統計"""
    win: ProbabilityBasedBetStats = Field(description="単勝統計")
    place: ProbabilityBasedBetStats = Field(description="複勝統計")


class ProbabilityRangeStats(BaseModel):
    """確率範囲別の統計"""
    range: str = Field(description="確率範囲（例: 80-90%）")
    races: int = Field(description="レース数")
    hits: int = Field(description="的中数")
    accuracy: float = Field(description="的中率（%）")
    avg_payout: float = Field(description="平均配当（円）")
    roi: float = Field(description="回収率（%）")


class ProbabilityBreakdown(BaseModel):
    """確率範囲別の詳細統計"""
    win: List[ProbabilityRangeStats] = Field(description="単勝の確率範囲別統計")
    place: List[ProbabilityRangeStats] = Field(description="複勝の確率範囲別統計")


class VenueStats(BaseModel):
    """競馬場別統計"""
    venue: str = Field(description="競馬場名")
    by_rank: RankBasedStats = Field(description="順位ベース統計")
    by_probability: ProbabilityBasedStats = Field(description="確率閾値ベース統計")


class GradeStats(BaseModel):
    """グレード別統計"""
    grade: str = Field(description="グレード（G1/G2/G3/一般）")
    by_rank: RankBasedStats = Field(description="順位ベース統計")
    by_probability: ProbabilityBasedStats = Field(description="確率閾値ベース統計")


class DetailedBetStats(BaseModel):
    """詳細な券種別統計（馬場・距離・馬場条件用）"""
    hit_horses: int = Field(description="的中馬数")
    total_horses: int = Field(description="対象馬数")
    accuracy: float = Field(description="的中率（%）")
    roi: float = Field(description="回収率（%）")


class TrackTypeStats(BaseModel):
    """馬場種別統計"""
    track_type: str = Field(description="馬場種別（芝/ダート）")
    by_rank: RankBasedStats = Field(description="順位ベース統計")
    by_probability: ProbabilityBasedStats = Field(description="確率閾値ベース統計")


class DistanceRangeStats(BaseModel):
    """距離別統計"""
    distance_range: str = Field(description="距離範囲（例: 1200-1400m）")
    by_rank: RankBasedStats = Field(description="順位ベース統計")
    by_probability: ProbabilityBasedStats = Field(description="確率閾値ベース統計")


class TrackConditionStats(BaseModel):
    """馬場条件別統計（新規追加）"""
    track_condition: str = Field(description="馬場条件（良/稍重/重/不良/不明）")
    by_rank: RankBasedStats = Field(description="順位ベース統計")
    by_probability: ProbabilityBasedStats = Field(description="確率閾値ベース統計")


class StatisticsSummaryResponse(BaseModel):
    """統計サマリーレスポンス"""
    period: PeriodInfo
    by_rank: RankBasedStats
    by_probability: ProbabilityBasedStats
    probability_breakdown: ProbabilityBreakdown
    by_venue: List[VenueStats]
    by_grade: List[GradeStats]
    by_track_type: List[TrackTypeStats]
    by_distance: List[DistanceRangeStats]
    by_track_condition: List[TrackConditionStats]


class RaceDetailForStats(BaseModel):
    """統計用レース詳細"""
    race_id: int
    date: str
    venue: str
    race_name: str
    grade: Optional[str]
    predicted_winner: Dict
    actual_winner: Dict
    win_correct: bool
    place_correct: bool
    win_payout: Optional[int]
    place_payout: Optional[int]


class RaceListResponse(BaseModel):
    """レース一覧レスポンス"""
    total_count: int
    races: List[RaceDetailForStats]


class TimeSeriesData(BaseModel):
    """時系列データ"""
    date: str
    total_races: int
    win_accuracy: float
    place_accuracy: float
    win_roi: float
    place_roi: float


class TimeSeriesResponse(BaseModel):
    """時系列レスポンス"""
    timeseries: List[TimeSeriesData]