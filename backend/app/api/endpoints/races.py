# backend/app/api/endpoints/races.py (レース開催日API追加版)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from datetime import datetime, date
from typing import List, Optional

from app.core.database import get_db
from app.services.race_service import RaceService
from app.models.race import Race
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/races/netkeiba/{race_date}")
async def get_netkeiba_races_for_date(
    race_date: str
):
    """
    Netkeibaから指定日のレース一覧を取得（スクレイピング）
    
    Args:
        race_date: YYYY-MM-DD形式の日付
    """
    try:
        logger.info(f"Getting races from Netkeiba for date: {race_date}")
        
        from app.services.netkeiba_race_finder import netkeiba_finder
        
        # Netkeibaからレース一覧を取得
        netkeiba_races = netkeiba_finder.get_race_ids_for_date(race_date)
        
        if not netkeiba_races:
            logger.warning(f"No races found on Netkeiba for {race_date}")
            return {
                "success": True,
                "date": race_date,
                "races": [],
                "total_count": 0
            }
        
        logger.info(f"Found {len(netkeiba_races)} races on Netkeiba for {race_date}")
        
        return {
            "success": True,
            "date": race_date,
            "races": netkeiba_races,
            "total_count": len(netkeiba_races)
        }
        
    except Exception as e:
        logger.error(f"Error getting Netkeiba races for {race_date}: {e}")
        raise HTTPException(status_code=500, detail=f"Netkeibaからのレース取得に失敗しました: {str(e)}")


@router.get("/races/available-dates")
async def get_available_race_dates(
    limit: int = Query(30, description="取得する日付数の上限"),
    include_count: bool = Query(True, description="各日付のレース数を含めるか"),
    db: AsyncSession = Depends(get_db)
):
    """
    レースデータが存在する開催日一覧を取得（レース数付き）
    """
    try:
        logger.info(f"Getting available race dates with limit: {limit}, include_count: {include_count}")
        
        if include_count:
            # レース数を含める場合
            from sqlalchemy import func
            
            stmt = (
                select(Race.race_date, func.count(Race.id).label('race_count'))
                .group_by(Race.race_date)
                .order_by(Race.race_date.desc())
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            rows = result.all()
            
            dates_with_count = [
                {
                    "date": row.race_date.isoformat(),
                    "race_count": row.race_count
                }
                for row in rows
            ]
            
            logger.info(f"Found {len(dates_with_count)} available race dates with counts")
            
            return {
                "success": True,
                "dates": dates_with_count,
                "total_count": len(dates_with_count)
            }
        else:
            # レース数を含めない場合（既存の動作）
            stmt = (
                select(distinct(Race.race_date))
                .order_by(Race.race_date.desc())
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            race_dates = result.scalars().all()
            available_dates = [date.isoformat() for date in race_dates]
            
            return {
                "success": True,
                "dates": available_dates,
                "total_count": len(available_dates)
            }
        
    except Exception as e:
        logger.error(f"Error getting available race dates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available race dates")


@router.get("/races/{race_date}")
async def get_races_by_date(
    race_date: str,
    db: AsyncSession = Depends(get_db)
):
    """
    指定日のレース一覧を取得
    
    Args:
        race_date: YYYY-MM-DD形式の日付
    """
    try:
        # 日付フォーマットを検証
        try:
            parsed_date = datetime.strptime(race_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        logger.info(f"Getting races for date: {race_date}")
        
        race_service = RaceService(db)
        races = await race_service.get_races_by_date(parsed_date)
        
        logger.info(f"Found {len(races)} races for {race_date}")
        return races
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting races for date {race_date}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/races/{race_id}/horses")
async def get_race_horses(
    race_id: int,
    include_predictions: bool = Query(True, description="予測結果を含めるかどうか"),
    use_join_query: bool = Query(False, description="JOINクエリを使用するかどうか（パフォーマンス重視）"),
    db: AsyncSession = Depends(get_db)
):
    """
    指定レースの出走馬一覧を取得（予測結果込み）
    
    Args:
        race_id: レースID
        include_predictions: 予測結果を含めるかどうか
        use_join_query: JOINクエリを使用するかどうか
    """
    try:
        logger.info(f"Getting horses for race {race_id} (predictions: {include_predictions}, join: {use_join_query})")
        
        race_service = RaceService(db)
        
        if use_join_query:
            # JOINクエリ版（パフォーマンス重視）
            horses = await race_service.get_race_horses_with_predictions_join(race_id)
        else:
            # 通常版（関係性活用）
            horses = await race_service.get_race_horses(race_id)
        
        if not horses:
            logger.warning(f"No horses found for race {race_id}")
            return []
        
        # 予測結果を含めない場合は削除
        if not include_predictions:
            for horse in horses:
                horse.update({
                    "win_probability": None,
                    "place_probability": None,
                    "expected_value": None,
                    "confidence_score": None,
                    "model_version": None,
                    "prediction_date": None,
                    "has_prediction": False
                })
        
        # 統計ログ
        predicted_count = sum(1 for horse in horses if horse.get("has_prediction"))
        logger.info(f"Race {race_id}: Returning {len(horses)} horses, {predicted_count} with predictions")
        
        return horses
        
    except Exception as e:
        logger.error(f"Error getting horses for race {race_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/races/{race_id}/detail")
async def get_race_detail(
    race_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    レースの詳細情報を取得
    """
    try:
        race_service = RaceService(db)
        race_detail = await race_service.get_race_detail(race_id)
        
        if not race_detail:
            raise HTTPException(status_code=404, detail="Race not found")
        
        return race_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting race detail for {race_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/races/{race_id}/predictions/summary")
async def get_race_prediction_summary(
    race_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    レースの予測結果サマリーを取得
    """
    try:
        race_service = RaceService(db)
        summary = await race_service.get_prediction_summary(race_id)
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting prediction summary for race {race_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 既存のエンドポイント（後方互換性のため残す）
@router.get("/races/{race_id}")
async def get_race_by_id(
    race_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    レースの基本情報を取得（後方互換性のため）
    """
    try:
        race_service = RaceService(db)
        race_detail = await race_service.get_race_detail(race_id)
        
        if not race_detail:
            raise HTTPException(status_code=404, detail="Race not found")
        
        return race_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting race by id {race_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.delete("/races/{race_id}")
async def delete_race(
    race_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    レース削除API
    - レースと関連データ（馬、予測、結果）をすべて削除
    - カスケード削除により関連データも自動削除される
    """
    try:
        # レースの存在確認
        stmt = select(Race).where(Race.id == race_id)
        result = await db.execute(stmt)
        race = result.scalar_one_or_none()
        
        if not race:
            raise HTTPException(status_code=404, detail="Race not found")
        
        race_name = race.race_name
        race_date = race.race_date
        
        # レース削除（カスケードで関連データも削除）
        await db.delete(race)
        await db.commit()
        
        logger.info(f"Deleted race: {race_id} - {race_name} ({race_date})")
        
        return {
            "success": True,
            "message": f"レース「{race_name}」を削除しました",
            "deleted_race_id": race_id,
            "race_name": race_name,
            "race_date": str(race_date)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete race {race_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"レース削除に失敗しました: {str(e)}")