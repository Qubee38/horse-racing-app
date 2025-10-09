# backend/app/api/endpoints/statistics.py
"""
統計API

機能:
    1. 的中率サマリー取得
    2. 時系列データ取得
    3. 詳細レース一覧取得
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, datetime, timedelta
import logging

from app.core.database import get_db
from app.services.accuracy_calculation_service import AccuracyCalculationService
from app.schemas.statistics import (
    StatisticsSummaryResponse,
    TimeSeriesResponse,
    RaceListResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summary", response_model=StatisticsSummaryResponse)
async def get_statistics_summary(
    start_date: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    win_threshold: float = Query(80.0, ge=0, le=100, description="単勝推奨閾値 (%)"),
    place_threshold: float = Query(85.0, ge=0, le=100, description="複勝推奨閾値 (%)"),
    db: AsyncSession = Depends(get_db)
):
    """
    統計サマリーを取得
    
    Args:
        start_date: 開始日（省略時: 30日前）
        end_date: 終了日（省略時: 今日）
        win_threshold: 単勝推奨閾値
        place_threshold: 複勝推奨閾値
    
    Returns:
        StatisticsSummaryResponse
    """
    try:
        # デフォルト期間設定
        if end_date is None:
            end_date_obj = date.today()
        else:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start_date is None:
            start_date_obj = end_date_obj - timedelta(days=30)
        else:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        # バリデーション
        if start_date_obj > end_date_obj:
            raise HTTPException(status_code=400, detail="開始日は終了日より前である必要があります")
        
        logger.info(f"統計サマリー取得: {start_date_obj} to {end_date_obj}, win_threshold={win_threshold}, place_threshold={place_threshold}")
        
        # サービス実行
        service = AccuracyCalculationService(db)
        summary = await service.calculate_summary(
            start_date_obj,
            end_date_obj,
            win_threshold,
            place_threshold
        )
        
        return StatisticsSummaryResponse(**summary)
        
    except ValueError as e:
        logger.error(f"日付フォーマットエラー: {e}")
        raise HTTPException(status_code=400, detail="日付フォーマットが不正です (YYYY-MM-DD)")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"統計サマリー取得エラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="統計サマリーの取得に失敗しました")


@router.get("/timeseries", response_model=TimeSeriesResponse)
async def get_statistics_timeseries(
    start_date: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    group_by: str = Query("month", regex="^(day|week|month)$", description="集計単位"),
    db: AsyncSession = Depends(get_db)
):
    """
    時系列データを取得
    
    Args:
        start_date: 開始日
        end_date: 終了日
        group_by: 集計単位 (day, week, month)
    
    Returns:
        TimeSeriesResponse
    """
    try:
        # デフォルト期間設定
        if end_date is None:
            end_date_obj = date.today()
        else:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start_date is None:
            # 集計単位に応じてデフォルト期間を変更
            if group_by == "day":
                start_date_obj = end_date_obj - timedelta(days=30)
            elif group_by == "week":
                start_date_obj = end_date_obj - timedelta(days=90)
            else:  # month
                start_date_obj = end_date_obj - timedelta(days=365)
        else:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        logger.info(f"時系列データ取得: {start_date_obj} to {end_date_obj}, group_by={group_by}")
        
        # TODO: 時系列データ計算サービスを実装
        # 現在は空のレスポンスを返す
        return TimeSeriesResponse(timeseries=[])
        
    except ValueError as e:
        logger.error(f"日付フォーマットエラー: {e}")
        raise HTTPException(status_code=400, detail="日付フォーマットが不正です (YYYY-MM-DD)")
    except Exception as e:
        logger.error(f"時系列データ取得エラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="時系列データの取得に失敗しました")


@router.get("/races", response_model=RaceListResponse)
async def get_statistics_races(
    start_date: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    hit_only: bool = Query(False, description="的中レースのみ"),
    miss_only: bool = Query(False, description="外れレースのみ"),
    venue: Optional[str] = Query(None, description="競馬場フィルタ"),
    grade: Optional[str] = Query(None, description="グレードフィルタ"),
    limit: int = Query(50, ge=1, le=200, description="取得件数"),
    offset: int = Query(0, ge=0, description="オフセット"),
    db: AsyncSession = Depends(get_db)
):
    """
    レース一覧を取得（統計用）
    
    Args:
        start_date: 開始日
        end_date: 終了日
        hit_only: 的中レースのみ
        miss_only: 外れレースのみ
        venue: 競馬場フィルタ
        grade: グレードフィルタ
        limit: 取得件数
        offset: オフセット
    
    Returns:
        RaceListResponse
    """
    try:
        # デフォルト期間設定
        if end_date is None:
            end_date_obj = date.today()
        else:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if start_date is None:
            start_date_obj = end_date_obj - timedelta(days=30)
        else:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        
        logger.info(f"レース一覧取得: {start_date_obj} to {end_date_obj}, limit={limit}, offset={offset}")
        
        # TODO: レース一覧取得サービスを実装
        # 現在は空のレスポンスを返す
        return RaceListResponse(total_count=0, races=[])
        
    except ValueError as e:
        logger.error(f"日付フォーマットエラー: {e}")
        raise HTTPException(status_code=400, detail="日付フォーマットが不正です (YYYY-MM-DD)")
    except Exception as e:
        logger.error(f"レース一覧取得エラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="レース一覧の取得に失敗しました")