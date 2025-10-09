# backend/app/schemas/race_result.py
"""
レース結果のPydanticスキーマ
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class HorseResultSchema(BaseModel):
    """馬結果スキーマ"""
    id: int
    horse_id: Optional[int]
    horse_name: Optional[str]
    horse_number: int
    finish_position: Optional[int]
    popularity: Optional[int]
    
    class Config:
        from_attributes = True


class PayoutSchema(BaseModel):
    """払い戻しスキーマ"""
    id: int
    bet_type: Optional[str]
    bet_type_name: Optional[str]
    winning_numbers: str
    payout_amount: int
    
    class Config:
        from_attributes = True


class RaceResultResponse(BaseModel):
    """レース結果レスポンス"""
    id: int
    race_id: int
    race_status: str = Field(description="completed, cancelled, partial_data")
    result_fetched_at: datetime
    horse_results: List[HorseResultSchema]
    payouts: List[PayoutSchema]
    
    class Config:
        from_attributes = True


class RaceResultSummaryResponse(BaseModel):
    """レース結果サマリーレスポンス（フロントエンド用）"""
    race_status: str
    result_fetched_at: str
    horse_results: List[dict]
    payouts: List[dict]
    
    class Config:
        from_attributes = True


class RaceResultFetchRequest(BaseModel):
    """レース結果取得リクエスト"""
    race_id: int = Field(..., description="アプリ内のrace.id")