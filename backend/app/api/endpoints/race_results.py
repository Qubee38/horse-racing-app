# backend/app/api/endpoints/race_results.py (一括取得API追加版)
"""
レース結果API

機能:
    1. レース結果の取得・保存
    2. 保存済み結果の取得
    3. 予測との比較サマリー取得
    4. 日別一括取得（NEW）
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional, List
import logging
import asyncio
from datetime import date

from app.core.database import get_db
from app.services.race_result_service import RaceResultService
from app.schemas.race_result import (
    RaceResultResponse,
    RaceResultSummaryResponse,
    RaceResultFetchRequest
)
from app.models.race_result import RaceResult
from app.models.race import Race
from app.models.prediction import Prediction

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/fetch/{race_id}", response_model=Dict)
async def fetch_race_result(
    race_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    レース結果を取得してDBに保存
    
    Args:
        race_id: アプリ内のrace.id
    
    Returns:
        {
            "status": "processing" | "completed" | "error",
            "message": str,
            "race_id": int
        }
    """
    try:
        service = RaceResultService(db)
        
        # レースの存在確認
        race = await service._get_race(race_id)
        if not race:
            raise HTTPException(status_code=404, detail="レースが見つかりません")
        
        if not race.netkeiba_race_id:
            raise HTTPException(
                status_code=400,
                detail="NetkeibaレースIDが設定されていません"
            )
        
        # 既に結果が存在するか確認
        exists = await service.check_race_result_exists(race_id)
        
        # バックグラウンドで実行
        background_tasks.add_task(
            _fetch_and_save_in_background,
            race_id,
            race.netkeiba_race_id
        )
        
        return {
            "status": "processing",
            "message": "レース結果の取得を開始しました" if not exists else "レース結果を再取得します（既存データは上書きされます）",
            "race_id": race_id,
            "already_exists": exists
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"レース結果取得APIエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="レース結果取得に失敗しました")


async def _fetch_and_save_in_background(race_id: int, netkeiba_race_id: str):
    """バックグラウンドでレース結果を取得・保存"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        try:
            service = RaceResultService(session)
            result = await service.fetch_and_save_race_result(race_id)
            
            if result:
                logger.info(f"レース結果保存完了: race_id={race_id}")
            else:
                logger.error(f"レース結果保存失敗: race_id={race_id}")
                
        except Exception as e:
            logger.error(f"バックグラウンド処理エラー: race_id={race_id}, error={e}", exc_info=True)


@router.post("/batch-fetch/{race_date}")
async def batch_fetch_race_results(
    race_date: str,
    db: AsyncSession = Depends(get_db)
):
    """
    指定日のレース結果を一括取得
    
    - 予測結果があるレースのみ対象
    - 既存結果があるレースはスキップ
    - 各レース間に5秒待機
    
    Args:
        race_date: YYYY-MM-DD形式の日付
    
    Returns:
        {
            "date": str,
            "total_races": int,
            "target_races": int,
            "skipped_races": int,
            "results": [
                {
                    "race_id": int,
                    "race_number": int,
                    "race_name": str,
                    "status": "success" | "skipped" | "failed",
                    "message": str
                }
            ],
            "summary": {
                "success": int,
                "skipped": int,
                "failed": int
            }
        }
    """
    try:
        # 日付をパース
        try:
            parsed_date = date.fromisoformat(race_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        logger.info(f"Starting batch fetch for date: {race_date}")
        
        # その日のレース一覧を取得
        stmt = select(Race).where(Race.race_date == parsed_date).order_by(Race.race_number)
        result = await db.execute(stmt)
        all_races = result.scalars().all()
        
        if not all_races:
            return {
                "date": race_date,
                "total_races": 0,
                "target_races": 0,
                "skipped_races": 0,
                "results": [],
                "summary": {"success": 0, "skipped": 0, "failed": 0}
            }
        
        # 予測結果があるレースを抽出
        target_races = []
        for race in all_races:
            # 予測結果があるか確認
            pred_stmt = select(Prediction).where(Prediction.race_id == race.id).limit(1)
            pred_result = await db.execute(pred_stmt)
            has_prediction = pred_result.scalar_one_or_none() is not None
            
            if has_prediction:
                target_races.append(race)
        
        logger.info(f"Found {len(target_races)} races with predictions out of {len(all_races)} total races")
        
        # 既に結果があるレースを確認
        service = RaceResultService(db)
        results = []
        skipped_count = 0
        
        for race in target_races:
            exists = await service.check_race_result_exists(race.id)
            if exists:
                results.append({
                    "race_id": race.id,
                    "race_number": race.race_number,
                    "race_name": race.race_name,
                    "status": "skipped",
                    "message": "既に結果が存在します"
                })
                skipped_count += 1
        
        # 取得対象のレース
        fetch_targets = [r for r in target_races if not await service.check_race_result_exists(r.id)]
        
        logger.info(f"Will fetch {len(fetch_targets)} races (skipping {skipped_count} already fetched)")
        
        # 各レースの結果を取得
        success_count = 0
        failed_count = 0
        
        for i, race in enumerate(fetch_targets):
            try:
                # 5秒待機（最初のレースを除く）
                if i > 0:
                    logger.info(f"Waiting 5 seconds before fetching race {race.id}...")
                    await asyncio.sleep(5.0)
                
                logger.info(f"Fetching result for race {race.id} ({i+1}/{len(fetch_targets)})")
                
                # レース結果を取得
                result = await service.fetch_and_save_race_result(race.id)
                
                if result:
                    results.append({
                        "race_id": race.id,
                        "race_number": race.race_number,
                        "race_name": race.race_name,
                        "status": "success",
                        "message": "取得成功"
                    })
                    success_count += 1
                else:
                    results.append({
                        "race_id": race.id,
                        "race_number": race.race_number,
                        "race_name": race.race_name,
                        "status": "failed",
                        "message": "取得失敗（データが見つかりません）"
                    })
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to fetch result for race {race.id}: {e}")
                results.append({
                    "race_id": race.id,
                    "race_number": race.race_number,
                    "race_name": race.race_name,
                    "status": "failed",
                    "message": f"取得失敗: {str(e)}"
                })
                failed_count += 1
        
        # 結果をまとめる
        response = {
            "date": race_date,
            "total_races": len(all_races),
            "target_races": len(target_races),
            "skipped_races": skipped_count,
            "results": results,
            "summary": {
                "success": success_count,
                "skipped": skipped_count,
                "failed": failed_count
            }
        }
        
        logger.info(f"Batch fetch completed: {success_count} success, {skipped_count} skipped, {failed_count} failed")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch fetch error for date {race_date}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"一括取得に失敗しました: {str(e)}")


@router.get("/{race_id}", response_model=Optional[RaceResultResponse])
async def get_race_result(
    race_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    保存済みレース結果を取得
    
    Args:
        race_id: アプリ内のrace.id
    
    Returns:
        RaceResultResponse or None
    """
    try:
        service = RaceResultService(db)
        race_result = await service.get_race_result(race_id)
        
        if not race_result:
            return None
        
        return RaceResultResponse(
            id=race_result.id,
            race_id=race_result.race_id,
            race_status=race_result.race_status,
            result_fetched_at=race_result.result_fetched_at,
            horse_results=[
                {
                    "id": hr.id,
                    "horse_id": hr.horse_id,
                    "horse_name": hr.horse.name if hr.horse else None,
                    "horse_number": hr.horse_number,
                    "finish_position": hr.finish_position,
                    "popularity": hr.popularity
                }
                for hr in race_result.horse_results
            ],
            payouts=[
                {
                    "id": p.id,
                    "bet_type": p.bet_type_ref.code if p.bet_type_ref else None,
                    "bet_type_name": p.bet_type_ref.name if p.bet_type_ref else None,
                    "winning_numbers": p.winning_numbers,
                    "payout_amount": p.payout_amount
                }
                for p in race_result.payouts
            ]
        )
        
    except Exception as e:
        logger.error(f"レース結果取得エラー: race_id={race_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="レース結果の取得に失敗しました")


@router.get("/summary/{race_id}", response_model=Optional[RaceResultSummaryResponse])
async def get_race_result_summary(
    race_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    レース結果サマリーを取得（予測との比較用）
    
    Args:
        race_id: アプリ内のrace.id
    
    Returns:
        RaceResultSummaryResponse or None
    """
    try:
        service = RaceResultService(db)
        summary = await service.get_race_result_summary(race_id)
        
        if not summary:
            return None
        
        return RaceResultSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"レース結果サマリー取得エラー: race_id={race_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="レース結果サマリーの取得に失敗しました")


@router.get("/exists/{race_id}", response_model=Dict)
async def check_race_result_exists(
    race_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    レース結果が保存済みか確認
    
    Args:
        race_id: アプリ内のrace.id
    
    Returns:
        {
            "exists": bool,
            "race_id": int
        }
    """
    try:
        service = RaceResultService(db)
        exists = await service.check_race_result_exists(race_id)
        
        return {
            "exists": exists,
            "race_id": race_id
        }
        
    except Exception as e:
        logger.error(f"レース結果存在確認エラー: race_id={race_id}, error={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="確認に失敗しました")


@router.put("/refetch/{race_id}")
async def refetch_race_result(
    race_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    レース結果再取得API
    - 既存の結果データを削除して再取得
    - バックグラウンドで実行
    """
    try:
        service = RaceResultService(db)
        
        # レースの存在確認
        race = await service._get_race(race_id)
        if not race:
            raise HTTPException(status_code=404, detail="レースが見つかりません")
        
        if not race.netkeiba_race_id:
            raise HTTPException(
                status_code=400,
                detail="NetkeibaレースIDが設定されていません"
            )
        
        # 既存の結果データを削除
        stmt = select(RaceResult).where(RaceResult.race_id == race_id)
        result_data = await db.execute(stmt)
        existing_result = result_data.scalar_one_or_none()
        
        if existing_result:
            await db.delete(existing_result)
            await db.commit()
            logger.info(f"Deleted existing result for race {race_id}")
        
        # バックグラウンドで再取得
        background_tasks.add_task(
            _fetch_and_save_in_background,
            race_id,
            race.netkeiba_race_id
        )
        
        return {
            "status": "processing",
            "message": "レース結果の再取得を開始しました",
            "race_id": race_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"結果再取得APIエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="結果再取得の開始に失敗しました")