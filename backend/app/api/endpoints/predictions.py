from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, date
from typing import Dict, List
import time
import asyncio

from app.core.database import get_db
from app.models.race import Race
from app.models.horse import Horse
from app.models.prediction import Prediction, PredictionBatch
from app.ml.predictor import predictor
from app.services.race_service import RaceService
from app.services.netkeiba_race_finder import netkeiba_finder

import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/predictions/execute-selected-races")
async def execute_selected_races_prediction(
    request: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    選択された複数レースの予測実行エンドポイント（新規）
    
    Body:
        {
            "date": "2025-09-22",
            "race_ids": ["202509220101", "202509220105", "202509220112"]
        }
    """
    try:
        target_date = request.get("date")
        race_ids = request.get("race_ids", [])
        
        if not target_date:
            raise HTTPException(status_code=400, detail="Date parameter is required")
        
        if not race_ids or len(race_ids) == 0:
            raise HTTPException(status_code=400, detail="At least one race_id is required")
        
        logger.info(f"Executing prediction for {len(race_ids)} selected races on {target_date}")
        
        # バッチレコードを作成
        batch = PredictionBatch(
            target_date=target_date,
            status="RUNNING",
            start_time=datetime.utcnow()
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        
        # バックグラウンドで予測実行
        background_tasks.add_task(
            run_selected_races_prediction_batch,
            batch.id,
            target_date,
            race_ids
        )
        
        return {
            "success": True,
            "message": f"選択された{len(race_ids)}レースの予測実行を開始しました",
            "batch_id": batch.id,
            "target_date": target_date,
            "selected_race_count": len(race_ids),
            "race_ids": race_ids,
            "status": "RUNNING"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Selected races prediction execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"予測実行に失敗しました: {str(e)}")


async def run_selected_races_prediction_batch(
    batch_id: int,
    target_date: str,
    race_ids: List[str]
):
    """
    選択されたレースのみ予測実行（バックグラウンド処理）
    """
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            stmt = select(PredictionBatch).where(PredictionBatch.id == batch_id)
            result = await db.execute(stmt)
            batch = result.scalar_one()
            
            logger.info(f"Starting selected races prediction batch {batch_id} with {len(race_ids)} races")
            
            # モデルを読み込み
            if not predictor.is_loaded:
                success = predictor.load_models()
                if not success:
                    raise Exception("モデルの読み込みに失敗しました")
            
            batch.total_races = len(race_ids)
            batch.completed_predictions = 0
            batch.failed_predictions = 0
            total_horses = 0
            
            # 各レースを処理（負荷対策付き）
            for i, race_id in enumerate(race_ids):
                try:
                    logger.info(f"Processing race {i+1}/{len(race_ids)}: {race_id}")
                    
                    # レース間待機処理
                    if i > 0:
                        wait_time = 2.0
                        logger.info(f"Waiting {wait_time} seconds before next race...")
                        await asyncio.sleep(wait_time)
                    
                    # 予測実行
                    prediction_result = predictor.predict_race_from_netkeiba(race_id)
                    
                    if not prediction_result.get('success'):
                        logger.warning(f"Prediction failed for race {race_id}: {prediction_result.get('error')}")
                        batch.failed_predictions += 1
                        continue
                    
                    predictions = prediction_result['predictions']
                    total_horses += len(predictions)
                    
                    # データベースに結果を保存
                    race_info_dict = {
                        'netkeiba_race_id': race_id,
                        'location': prediction_result['race_info'].get('location', '未定'),
                        'race_name': prediction_result['race_info'].get('race_name', ''),
                        'race_number': prediction_result['race_info'].get('race_number', 1),
                        'date': target_date
                    }
                    await save_single_race_prediction_results(db, race_id, prediction_result)
                    
                    batch.completed_predictions += 1
                    await db.commit()
                    
                    logger.info(f"Completed race {race_id} with {len(predictions)} horses")
                    
                except Exception as e:
                    logger.error(f"Failed to process race {race_id}: {e}")
                    batch.failed_predictions += 1
                    continue
            
            batch.total_horses = total_horses
            batch.status = "COMPLETED"
            batch.end_time = datetime.utcnow()
            batch.processing_time_seconds = (batch.end_time - batch.start_time).total_seconds()
            
            await db.commit()
            logger.info(f"Selected races prediction batch {batch_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Selected races prediction batch {batch_id} failed: {e}")
            
            batch.status = "FAILED"
            batch.end_time = datetime.utcnow()
            batch.error_message = str(e)
            batch.processing_time_seconds = (batch.end_time - batch.start_time).total_seconds()
            
            await db.commit()


@router.post("/predictions/execute")
async def execute_prediction(
    request: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    日別統合予測実行エンドポイント
    
    Body:
        {
            "date": "2025-09-22",           # 対象日
            "method": "netkeiba_scraping"   # 実行方法: "netkeiba_scraping" | "database_only"
        }
    """
    try:
        target_date = request.get("date")
        method = request.get("method", "netkeiba_scraping")
        
        if not target_date:
            raise HTTPException(status_code=400, detail="Date parameter is required")
        
        # Netkeibaレース ID取得を統合
        if method == "netkeiba_scraping":
            logger.info(f"Finding races for date {target_date} from Netkeiba")
            netkeiba_races = netkeiba_finder.get_race_ids_for_date(target_date)
            
            if not netkeiba_races:
                raise HTTPException(
                    status_code=404, 
                    detail=f"指定日 {target_date} にレースが見つかりませんでした"
                )
            
            logger.info(f"Found {len(netkeiba_races)} races from Netkeiba")
        
        # バッチレコードを作成
        batch = PredictionBatch(
            target_date=target_date,
            status="RUNNING",
            start_time=datetime.utcnow()
        )
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        
        # バックグラウンドで予測実行
        if method == "netkeiba_scraping":
            background_tasks.add_task(
                run_netkeiba_prediction_batch_enhanced,
                batch.id,
                target_date,
                netkeiba_races
            )
        else:
            background_tasks.add_task(
                run_database_prediction_batch,
                batch.id,
                target_date
            )
        
        return {
            "success": True,
            "message": f"予測実行を開始しました ({method})",
            "batch_id": batch.id,
            "target_date": target_date,
            "method": method,
            "status": "RUNNING",
            "found_races": len(netkeiba_races) if method == "netkeiba_scraping" else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"予測実行に失敗しました: {str(e)}")

@router.post("/predictions/execute-race")
async def execute_single_race_prediction(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    単一レース予測実行（Netkeibaスクレイピング）
    
    Body:
        {
            "race_id": "202509220101"  # Netkeibaレース ID
        }
    """
    try:
        race_id = request.get("race_id")
        if not race_id:
            raise HTTPException(status_code=400, detail="race_id parameter is required")
        
        # モデルが読み込まれていない場合は読み込み
        if not predictor.is_loaded:
            success = predictor.load_models()
            if not success:
                raise HTTPException(status_code=500, detail="モデルの読み込みに失敗しました")
        
        # Netkeibaから予測実行
        logger.info(f"Executing single race prediction for race_id: {race_id}")
        result = predictor.predict_race_from_netkeiba(race_id)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=f"予測実行に失敗しました: {result.get('error', 'Unknown error')}"
            )
        
        # データベースに結果を保存（オプション）
        try:
            await save_single_race_prediction_results(db, race_id, result)
        except Exception as e:
            logger.warning(f"Failed to save prediction results to database: {e}")
        
        return {
            "success": True,
            "race_id": race_id,
            "race_info": result['race_info'],
            "predictions": result['predictions'],
            "model_type": result.get('model_type', 'unknown'),
            "message": "単一レース予測が完了しました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Single race prediction failed for {race_id}: {e}")
        raise HTTPException(status_code=500, detail=f"予測実行に失敗しました: {str(e)}")

@router.get("/predictions/status/{batch_id}")
async def get_prediction_status(
    batch_id: int,
    db: AsyncSession = Depends(get_db)
):
    """予測実行状況を取得"""
    try:
        stmt = select(PredictionBatch).where(PredictionBatch.id == batch_id)
        result = await db.execute(stmt)
        batch = result.scalar_one_or_none()
        
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return {
            "batch_id": batch.id,
            "target_date": batch.target_date,
            "status": batch.status,
            "total_races": batch.total_races,
            "total_horses": batch.total_horses,
            "completed_predictions": batch.completed_predictions,
            "failed_predictions": batch.failed_predictions,
            "start_time": batch.start_time,
            "end_time": batch.end_time,
            "processing_time_seconds": batch.processing_time_seconds,
            "error_message": batch.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/model/info")
async def get_model_info():
    """統合モデル情報を取得"""
    try:
        if not predictor.is_loaded:
            success = predictor.load_models()
            if not success:
                return {
                    "status": "failed_to_load",
                    "message": "モデルの読み込みに失敗しました",
                    "models_path": predictor.models_path
                }
        
        model_info = predictor.get_model_info()
        return model_info
        
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_netkeiba_prediction_batch_enhanced(
    batch_id: int, 
    target_date: str, 
    netkeiba_races: List[Dict]
):
    """
    強化版Netkeibaスクレイピング予測バッチ処理（負荷対策付き）
    """
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # バッチレコードを取得
            stmt = select(PredictionBatch).where(PredictionBatch.id == batch_id)
            result = await db.execute(stmt)
            batch = result.scalar_one()
            
            logger.info(f"Starting enhanced Netkeiba prediction batch {batch_id} for date {target_date}")
            
            # モデルを読み込み
            if not predictor.is_loaded:
                success = predictor.load_models()
                if not success:
                    raise Exception("モデルの読み込みに失敗しました")
            
            batch.total_races = len(netkeiba_races)
            batch.completed_predictions = 0
            batch.failed_predictions = 0
            total_horses = 0
            
            # 各レースを処理（負荷対策付き）
            for i, race_info in enumerate(netkeiba_races):
                try:
                    netkeiba_race_id = race_info['netkeiba_race_id']
                    logger.info(f"Processing race {i+1}/{len(netkeiba_races)}: {netkeiba_race_id}")
                    
                    # === 負荷対策: レース間待機処理 ===
                    if i > 0:  # 最初のレース以外で待機
                        wait_time = 2.0  # 2秒間待機
                        logger.info(f"Waiting {wait_time} seconds before next race...")
                        await asyncio.sleep(wait_time)
                    
                    # Netkeibaから予測実行
                    prediction_result = predictor.predict_race_from_netkeiba(netkeiba_race_id)
                    
                    if not prediction_result.get('success'):
                        logger.warning(f"Prediction failed for race {netkeiba_race_id}: {prediction_result.get('error')}")
                        batch.failed_predictions += 1
                        continue
                    
                    predictions = prediction_result['predictions']
                    total_horses += len(predictions)
                    
                    # データベースに結果を保存
                    await save_batch_prediction_results(db, race_info, prediction_result)
                    
                    batch.completed_predictions += 1
                    await db.commit()
                    
                    logger.info(f"Completed race {netkeiba_race_id} with {len(predictions)} horses")
                    
                except Exception as e:
                    logger.error(f"Failed to process race {race_info.get('netkeiba_race_id', 'unknown')}: {e}")
                    batch.failed_predictions += 1
                    continue
            
            batch.total_horses = total_horses
            batch.status = "COMPLETED"
            batch.end_time = datetime.utcnow()
            batch.processing_time_seconds = (batch.end_time - batch.start_time).total_seconds()
            
            await db.commit()
            logger.info(f"Enhanced Netkeiba prediction batch {batch_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Enhanced Netkeiba prediction batch {batch_id} failed: {e}")
            
            batch.status = "FAILED"
            batch.end_time = datetime.utcnow()
            batch.error_message = str(e)
            batch.processing_time_seconds = (batch.end_time - batch.start_time).total_seconds()
            
            await db.commit()

async def save_single_race_prediction_results(
    db: AsyncSession, 
    race_id: str, 
    prediction_result: Dict
):
    """単一レース予測結果をデータベースに保存（レース詳細情報対応版）"""
    try:
        race_info = prediction_result['race_info']
        predictions = prediction_result['predictions']
        
        # === 修正: レース詳細情報を正確に保存 ===
        # 日付の解析
        race_date_str = race_info.get('date', '')
        try:
            if race_date_str and len(race_date_str) == 8:
                # YYYYMMDD形式をdateオブジェクトに変換
                race_date = datetime.strptime(race_date_str, '%Y%m%d').date()
            else:
                race_date = datetime.now().date()
        except:
            race_date = datetime.now().date()
        
        # 馬場状態のマッピング（数値→文字列）
        baba_mapping = {0: '良', 1: '稍', 2: '重', 3: '不'}
        baba_code = race_info.get('baba', 0)
        track_condition = baba_mapping.get(baba_code, '良')
        
        # 芝/ダートのマッピング（数値→文字列）
        track_type_mapping = {0: '芝', 1: 'ダート', 2: '障害'}
        track_type_code = race_info.get('track_type', 0)
        surface = track_type_mapping.get(track_type_code, '芝')
        
        # 天気のマッピング（数値→文字列）
        weather_mapping = {0: '晴', 1: '曇', 2: '小雨', 3: '雨', 4: '雪'}
        weather_code = race_info.get('weather', 0)
        weather = weather_mapping.get(weather_code, '晴')
        
        # レース情報を保存または更新
        race = Race(
            venue=race_info.get('location', '未定'),
            race_name=race_info.get('race_name', f'Race {race_id}'),
            race_number=race_info.get('race_number', 1),
            race_date=race_date,
            start_time=race_info.get('start_time', '未定'),  # 発走時刻
            distance=int(race_info.get('distance', 1600)),    # 距離
            surface=surface,                                  # 芝/ダート
            weather=weather,                                  # 天気
            track_condition=track_condition,                  # 馬場状態
            grade=race_info.get('race_rank', 0),             # レースグレード
            netkeiba_race_id=race_id
        )
        
        logger.info(f"Saving race: {race.race_name} (R{race.race_number}) - {race.start_time}, {race.distance}m, {race.surface}, {race.weather}, {race.track_condition}")
        
        db.add(race)
        await db.flush()
        
        # 各馬の予測結果を保存
        for pred in predictions:
            # 馬情報を保存
            horse = Horse(
                race_id=race.id,
                name=pred.get('horse_name', '未定'),
                jockey=pred.get('jockey', '未定'),
                frame_number=pred.get('frame_number', 0),  # 修正: 実際の値を使用
                horse_number=pred.get('horse_number', 0),
                odds=pred.get('odds', 0.0)
            )
            db.add(horse)
            await db.flush()
            
            # 予測結果を保存
            prediction = Prediction(
                horse_id=horse.id,
                race_id=race.id,
                win_probability=pred.get('win_probability', 0.0),
                place_probability=pred.get('place_probability', 0.0),
                expected_value=pred.get('expected_value', 0.0),
                model_version="integrated_v1.0",
                confidence_score=pred.get('confidence_score', 0.5),
                prediction_date=datetime.utcnow()
            )
            db.add(prediction)
        
        await db.commit()
        logger.info(f"Saved single race prediction results for {race_id}")
        
    except Exception as e:
        logger.error(f"Failed to save single race prediction results: {e}")
        await db.rollback()

async def save_batch_prediction_results(
    db: AsyncSession, 
    race_info: Dict, 
    prediction_result: Dict
):
    """バッチ予測結果をデータベースに保存"""
    # save_single_race_prediction_resultsと同様の処理
    # 必要に応じて拡張
    await save_single_race_prediction_results(
        db, 
        race_info['netkeiba_race_id'], 
        prediction_result
    )

# レガシー関数（既存コード互換性のため残す）
async def run_database_prediction_batch(batch_id: int, target_date: str):
    """データベースのみによる予測バッチ処理（レガシー）"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # バッチレコードを取得
            stmt = select(PredictionBatch).where(PredictionBatch.id == batch_id)
            result = await db.execute(stmt)
            batch = result.scalar_one()
            
            logger.info(f"Running database-only prediction batch {batch_id} for {target_date}")
            
            # モデルを読み込み
            if not predictor.is_loaded:
                success = predictor.load_models()
                if not success:
                    raise Exception("モデルの読み込みに失敗しました")
            
            # 対象日のレース一覧をデータベースから取得
            race_service = RaceService(db)
            races = await race_service.get_races_by_date(target_date)
            
            if not races:
                raise Exception(f"対象日 {target_date} にレースが見つかりません")
            
            batch.total_races = len(races)
            batch.completed_predictions = 0
            batch.failed_predictions = 0
            total_horses = 0
            
            # 各レースを処理
            for race_dict in races:
                try:
                    race_id = race_dict['id']
                    logger.info(f"Processing database race {race_id}")
                    
                    # データベースから出走馬を取得
                    horses = await race_service.get_race_horses(race_id)
                    
                    if not horses:
                        logger.warning(f"No horses found for race {race_id}")
                        batch.failed_predictions += 1
                        continue
                    
                    total_horses += len(horses)
                    
                    # 各馬に対してダミー予測を実行（データベースのみの場合）
                    for horse in horses:
                        prediction = Prediction(
                            horse_id=horse.id,
                            race_id=race_id,
                            win_probability=10.0,  # ダミー値
                            place_probability=35.0,  # ダミー値
                            expected_value=80.0,
                            model_version="database_only_v1.0",
                            confidence_score=0.3,
                            prediction_date=datetime.utcnow()
                        )
                        db.add(prediction)
                    
                    await db.commit()
                    batch.completed_predictions += 1
                    
                    logger.info(f"Completed database race {race_id} with {len(horses)} horses")
                    
                except Exception as e:
                    logger.error(f"Failed to process database race {race_dict.get('id', 'unknown')}: {e}")
                    batch.failed_predictions += 1
                    continue
            
            batch.total_horses = total_horses
            batch.status = "COMPLETED"
            batch.end_time = datetime.utcnow()
            batch.processing_time_seconds = (batch.end_time - batch.start_time).total_seconds()
            
            await db.commit()
            logger.info(f"Database prediction batch {batch_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Database prediction batch {batch_id} failed: {e}")
            
            batch.status = "FAILED"
            batch.end_time = datetime.utcnow()
            batch.error_message = str(e)
            batch.processing_time_seconds = (batch.end_time - batch.start_time).total_seconds()
            
            await db.commit()