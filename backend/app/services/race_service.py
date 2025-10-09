# backend/app/services/race_service.py（完全版）

from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict
from datetime import datetime, date

from app.models.race import Race
from app.models.horse import Horse
from app.models.prediction import Prediction
import logging

logger = logging.getLogger(__name__)

class RaceService:
    """レース関連のビジネスロジック"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_races_by_date(self, race_date: date) -> List[dict]:
        """
        指定日のレース一覧を取得
        
        Args:
            race_date: レース開催日（date型）
            
        Returns:
            レース一覧（辞書形式）
        """
        try:
            logger.info(f"Getting races for date: {race_date}")
            
            stmt = (
                select(Race)
                .where(Race.race_date == race_date)
                .order_by(Race.race_number)
            )
            result = await self.db.execute(stmt)
            races = result.scalars().all()
            
            logger.info(f"Found {len(races)} races for {race_date}")
            return [race.to_dict() for race in races]
            
        except Exception as e:
            logger.error(f"Failed to get races for date {race_date}: {e}")
            raise
    
    async def get_race_horses(self, race_id: int) -> List[dict]:
        """
        指定レースの出走馬一覧を取得（最新予測結果のみ）
        
        Args:
            race_id: レースID
            
        Returns:
            出走馬一覧（予測結果は最新のもののみ）
        """
        try:
            logger.info(f"Getting horses for race {race_id} with latest predictions only")
            
            # 馬情報を取得
            stmt = (
                select(Horse)
                .where(Horse.race_id == race_id)
                .order_by(Horse.horse_number)
            )
            result = await self.db.execute(stmt)
            horses = result.scalars().all()
            
            if not horses:
                logger.warning(f"No horses found for race {race_id}")
                return []
            
            # 各馬の最新予測結果を取得
            horses_data = []
            for horse in horses:
                horse_dict = {
                    "id": horse.id,
                    "race_id": horse.race_id,
                    "name": horse.name,
                    "jockey": horse.jockey,
                    "frame_number": horse.frame_number,
                    "horse_number": horse.horse_number,
                    "odds": horse.odds,
                    "weight": getattr(horse, 'weight', None),  # 修正: 安全な属性取得
                    "age": getattr(horse, 'age', None),        # 修正: 安全な属性取得
                    "sex": getattr(horse, 'sex', None),        # 修正: 安全な属性取得
                    "popularity": getattr(horse, 'popularity', None),  # 追加
                    "weight_change": getattr(horse, 'weight_change', None),  # 追加
                    "handicap": getattr(horse, 'handicap', None),  # 追加
                    # 予測結果のデフォルト値
                    "win_probability": None,
                    "place_probability": None,
                    "expected_value": None,
                    "confidence_score": None,
                    "model_version": None,
                    "prediction_date": None,
                    "has_prediction": False
                }
                
                # === 修正: 最新の予測結果のみ取得 ===
                latest_prediction_stmt = (
                    select(Prediction)
                    .where(
                        and_(
                            Prediction.horse_id == horse.id,
                            Prediction.race_id == race_id
                        )
                    )
                    .order_by(Prediction.prediction_date.desc())
                    .limit(1)
                )
                
                prediction_result = await self.db.execute(latest_prediction_stmt)
                latest_prediction = prediction_result.scalar_one_or_none()
                
                if latest_prediction:
                    horse_dict.update({
                        "win_probability": latest_prediction.win_probability,
                        "place_probability": latest_prediction.place_probability,
                        "expected_value": latest_prediction.expected_value,
                        "confidence_score": latest_prediction.confidence_score,
                        "model_version": latest_prediction.model_version,
                        "prediction_date": latest_prediction.prediction_date.isoformat() if latest_prediction.prediction_date else None,
                        "has_prediction": True
                    })
                    logger.debug(f"Horse {horse.name}: Latest prediction from {latest_prediction.prediction_date}")
                
                horses_data.append(horse_dict)
            
            logger.info(f"Returned {len(horses_data)} horses for race {race_id}")
            return horses_data
            
        except Exception as e:
            logger.error(f"Failed to get horses for race {race_id}: {e}")
            raise
    
    async def get_race_horses_with_predictions_join(self, race_id: int) -> List[dict]:
        """
        JOINクエリ版: 指定レースの出走馬一覧を取得（最新予測結果のみ）
        
        パフォーマンス重視版 - 単一クエリで取得
        
        Args:
            race_id: レースID
            
        Returns:
            出走馬一覧（予測結果は最新のもののみ）
        """
        try:
            logger.info(f"Getting horses with JOIN for race {race_id} (latest predictions only)")
            
            # === 修正: 最新予測のみを取得するサブクエリ ===
            # 各馬の最新予測日時を取得
            latest_prediction_subquery = (
                select(
                    Prediction.horse_id,
                    func.max(Prediction.prediction_date).label('latest_date')
                )
                .where(Prediction.race_id == race_id)
                .group_by(Prediction.horse_id)
                .subquery()
            )
            
            # 馬情報と最新予測を結合
            stmt = (
                select(Horse, Prediction)
                .outerjoin(
                    latest_prediction_subquery,
                    Horse.id == latest_prediction_subquery.c.horse_id
                )
                .outerjoin(
                    Prediction,
                    and_(
                        Prediction.horse_id == Horse.id,
                        Prediction.race_id == race_id,
                        Prediction.prediction_date == latest_prediction_subquery.c.latest_date
                    )
                )
                .where(Horse.race_id == race_id)
                .order_by(Horse.horse_number)
            )
            
            result = await self.db.execute(stmt)
            rows = result.all()
            
            horses_data = []
            for horse, prediction in rows:
                horse_dict = {
                    "id": horse.id,
                    "race_id": horse.race_id,
                    "name": horse.name,
                    "jockey": horse.jockey,
                    "frame_number": horse.frame_number,
                    "horse_number": horse.horse_number,
                    "odds": horse.odds,
                    "weight": horse.weight,
                    "age": horse.age,
                    "sex": horse.sex,
                    "win_probability": prediction.win_probability if prediction else None,
                    "place_probability": prediction.place_probability if prediction else None,
                    "expected_value": prediction.expected_value if prediction else None,
                    "confidence_score": prediction.confidence_score if prediction else None,
                    "model_version": prediction.model_version if prediction else None,
                    "prediction_date": prediction.prediction_date.isoformat() if prediction and prediction.prediction_date else None,
                    "has_prediction": prediction is not None
                }
                horses_data.append(horse_dict)
            
            logger.info(f"JOIN query returned {len(horses_data)} horses for race {race_id}")
            return horses_data
            
        except Exception as e:
            logger.error(f"Failed to get horses with JOIN for race {race_id}: {e}")
            raise
    
    async def get_race_detail(self, race_id: int) -> Optional[dict]:
        """
        レース詳細情報を取得
        
        Args:
            race_id: レースID
            
        Returns:
            レース詳細情報（存在しない場合はNone）
        """
        try:
            stmt = select(Race).where(Race.id == race_id)
            result = await self.db.execute(stmt)
            race = result.scalar_one_or_none()
            
            if not race:
                return None
            
            return race.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to get race detail for {race_id}: {e}")
            raise
    
    async def get_prediction_summary(self, race_id: int) -> Dict:
        """
        レースの予測結果サマリーを取得
        
        Args:
            race_id: レースID
            
        Returns:
            予測サマリー情報
        """
        try:
            # 馬の総数を取得
            horses_stmt = select(func.count(Horse.id)).where(Horse.race_id == race_id)
            horses_result = await self.db.execute(horses_stmt)
            total_horses = horses_result.scalar()
            
            # 予測済みの馬の数を取得（最新のみ）
            # サブクエリで各馬の最新予測を特定
            latest_predictions_subquery = (
                select(
                    Prediction.horse_id,
                    func.max(Prediction.prediction_date).label('latest_date')
                )
                .join(Horse, Prediction.horse_id == Horse.id)
                .where(Horse.race_id == race_id)
                .group_by(Prediction.horse_id)
                .subquery()
            )
            
            predicted_stmt = (
                select(func.count(distinct(Prediction.horse_id)))
                .join(
                    latest_predictions_subquery,
                    and_(
                        Prediction.horse_id == latest_predictions_subquery.c.horse_id,
                        Prediction.prediction_date == latest_predictions_subquery.c.latest_date
                    )
                )
            )
            predicted_result = await self.db.execute(predicted_stmt)
            predicted_horses = predicted_result.scalar()
            
            return {
                "race_id": race_id,
                "total_horses": total_horses,
                "predicted_horses": predicted_horses,
                "completion_rate": (predicted_horses / total_horses * 100) if total_horses > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get prediction summary for race {race_id}: {e}")
            raise
    
    async def create_race(self, race_data: dict) -> Race:
        """
        新しいレースを作成
        
        Args:
            race_data: レース情報
            
        Returns:
            作成されたRaceオブジェクト
        """
        try:
            race = Race(**race_data)
            self.db.add(race)
            await self.db.commit()
            await self.db.refresh(race)
            
            logger.info(f"Created race: {race.id} - {race.race_name}")
            return race
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create race: {e}")
            raise
    
    async def update_race(self, race_id: int, race_data: dict) -> Optional[Race]:
        """
        レース情報を更新
        
        Args:
            race_id: レースID
            race_data: 更新するデータ
            
        Returns:
            更新されたRaceオブジェクト（存在しない場合はNone）
        """
        try:
            stmt = select(Race).where(Race.id == race_id)
            result = await self.db.execute(stmt)
            race = result.scalar_one_or_none()
            
            if not race:
                return None
            
            for key, value in race_data.items():
                if hasattr(race, key):
                    setattr(race, key, value)
            
            await self.db.commit()
            await self.db.refresh(race)
            
            logger.info(f"Updated race: {race.id}")
            return race
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update race {race_id}: {e}")
            raise
    
    async def delete_race(self, race_id: int) -> bool:
        """
        レースを削除
        
        Args:
            race_id: レースID
            
        Returns:
            削除成功の場合True、レースが存在しない場合False
        """
        try:
            stmt = select(Race).where(Race.id == race_id)
            result = await self.db.execute(stmt)
            race = result.scalar_one_or_none()
            
            if not race:
                return False
            
            await self.db.delete(race)
            await self.db.commit()
            
            logger.info(f"Deleted race: {race_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete race {race_id}: {e}")
            raise

    async def get_races_by_date_with_predictions(self, race_date: date) -> List[Race]:
        """
        指定日のレース一覧を取得（予測結果とリレーション込み）
        
        Args:
            race_date: レース開催日（date型）
            
        Returns:
            Race オブジェクトのリスト（horses と predictions を eager load）
        """
        try:
            logger.info(f"Getting races with predictions for date: {race_date}")
            
            stmt = (
                select(Race)
                .options(
                    selectinload(Race.horses).selectinload(Horse.predictions)
                )
                .where(Race.race_date == race_date)
                .order_by(Race.race_number)
            )
            result = await self.db.execute(stmt)
            races = result.scalars().all()
            
            logger.info(f"Found {len(races)} races with predictions for {race_date}")
            return races
            
        except Exception as e:
            logger.error(f"Failed to get races with predictions for date {race_date}: {e}")
            raise