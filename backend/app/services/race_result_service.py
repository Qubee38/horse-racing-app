# backend/app/services/race_result_service.py
"""
レース結果の保存・取得サービス

機能:
    1. スクレイピング結果のDB保存
    2. レース結果の取得
    3. 馬IDの照合（race_id + horse_number）
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.race import Race
from app.models.horse import Horse
from app.models.race_result import RaceResult, HorseResult, Payout, BetType
from app.services.race_result_scraper import RaceResultScraper

logger = logging.getLogger(__name__)


class RaceResultService:
    """レース結果サービス"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.scraper = RaceResultScraper()
    
    async def fetch_and_save_race_result(self, race_id: int) -> Optional[RaceResult]:
        """
        レース結果を取得してDBに保存
        
        Args:
            race_id: アプリ内のrace.id
        
        Returns:
            保存されたRaceResult、失敗時はNone
        """
        try:
            # レース情報を取得
            race = await self._get_race(race_id)
            if not race:
                logger.error(f"レースが見つかりません: race_id={race_id}")
                return None
            
            if not race.netkeiba_race_id:
                logger.error(f"NetkeibaレースIDが設定されていません: race_id={race_id}")
                return None
            
            logger.info(f"レース結果取得開始: race_id={race_id}, netkeiba_race_id={race.netkeiba_race_id}")
            
            # スクレイピング実行
            scraped_data = self.scraper.scrape_race_result(race.netkeiba_race_id)
            if not scraped_data:
                logger.error(f"スクレイピング失敗: netkeiba_race_id={race.netkeiba_race_id}")
                return None
            
            # DB保存
            race_result = await self._save_race_result(race, scraped_data)
            
            logger.info(f"レース結果保存完了: race_id={race_id}")
            return race_result
            
        except Exception as e:
            logger.error(f"レース結果取得・保存エラー: race_id={race_id}, error={e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def _get_race(self, race_id: int) -> Optional[Race]:
        """レース情報を取得"""
        stmt = select(Race).where(Race.id == race_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _save_race_result(self, race: Race, scraped_data: Dict) -> RaceResult:
        """スクレイピング結果をDBに保存"""
        
        # 既存のレース結果を確認
        existing_result = await self._get_existing_race_result(race.id)
        if existing_result:
            logger.info(f"既存のレース結果を削除: race_id={race.id}")
            await self.db.delete(existing_result)
            await self.db.flush()
        
        # RaceResult作成
        race_result = RaceResult(
            race_id=race.id,
            race_status=scraped_data['race_status'],
            result_fetched_at=datetime.utcnow()
        )
        self.db.add(race_result)
        await self.db.flush()  # IDを取得するためflush
        
        # HorseResult保存
        for horse_data in scraped_data['horse_results']:
            await self._save_horse_result(race_result.id, race.id, horse_data)
        
        # Payout保存
        for payout_data in scraped_data['payouts']:
            await self._save_payout(race_result.id, race.id, payout_data)
        
        await self.db.commit()
        
        return race_result
    
    async def _get_existing_race_result(self, race_id: int) -> Optional[RaceResult]:
        """既存のレース結果を取得"""
        stmt = select(RaceResult).where(RaceResult.race_id == race_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _save_horse_result(self, race_result_id: int, race_id: int, horse_data: Dict):
        """各馬の結果を保存"""
        
        # 馬番からhorse.idを取得
        horse_id = await self._find_horse_by_number(race_id, horse_data['horse_number'])
        if not horse_id:
            logger.warning(
                f"馬が見つかりません: race_id={race_id}, horse_number={horse_data['horse_number']}"
            )
            # 馬が見つからなくてもレコードは作成する（horse_idはnullable=True）
        
        horse_result = HorseResult(
            race_result_id=race_result_id,
            race_id=race_id,
            horse_id=horse_id,  # 見つからない場合はNone
            netkeiba_horse_id=horse_data.get('netkeiba_horse_id'),  # 追加
            horse_number=horse_data['horse_number'],  # 追加
            finish_position=horse_data['finish_position'],
            popularity=horse_data.get('popularity')
        )
        self.db.add(horse_result)
    
    async def _find_horse_by_number(self, race_id: int, horse_number: int) -> Optional[int]:
        """馬番からhorse.idを取得"""
        stmt = select(Horse.id).where(
            and_(
                Horse.race_id == race_id,
                Horse.horse_number == horse_number
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _save_payout(self, race_result_id: int, race_id: int, payout_data: Dict):
        """払い戻し情報を保存"""
        
        # bet_typeコードからbet_type_idを取得
        bet_type_id = await self._get_bet_type_id(payout_data['bet_type'])
        if not bet_type_id:
            logger.warning(f"券種が見つかりません: bet_type={payout_data['bet_type']}")
            return
        
        payout = Payout(
            race_result_id=race_result_id,
            race_id=race_id,
            bet_type_id=bet_type_id,
            winning_numbers=payout_data['winning_numbers'],
            payout_amount=payout_data['payout_amount']
        )
        self.db.add(payout)
    
    async def _get_bet_type_id(self, bet_type_code: str) -> Optional[int]:
        """券種コードからbet_type.idを取得"""
        stmt = select(BetType.id).where(BetType.code == bet_type_code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_race_result(self, race_id: int) -> Optional[RaceResult]:
        """
        レース結果を取得（リレーション込み）
        
        Args:
            race_id: アプリ内のrace.id
        
        Returns:
            RaceResult（horse_results, payouts込み）
        """
        stmt = (
            select(RaceResult)
            .where(RaceResult.race_id == race_id)
            .options(
                selectinload(RaceResult.horse_results).selectinload(HorseResult.horse),
                selectinload(RaceResult.payouts).selectinload(Payout.bet_type_ref)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_race_result_summary(self, race_id: int) -> Optional[Dict]:
        """
        レース結果サマリーを取得（フロントエンド用）
        
        Returns:
            {
                'race_status': str,
                'result_fetched_at': str,
                'horse_results': [
                    {
                        'horse_id': int,
                        'horse_name': str,
                        'horse_number': int,
                        'finish_position': int,
                        'popularity': int
                    },
                    ...
                ],
                'payouts': [
                    {
                        'bet_type_name': str,
                        'winning_numbers': str,
                        'payout_amount': int
                    },
                    ...
                ]
            }
        """
        race_result = await self.get_race_result(race_id)
        if not race_result:
            return None
        
        # 馬結果を整形
        horse_results = []
        for hr in race_result.horse_results:
            horse_results.append({
                'horse_id': hr.horse_id,
                'horse_name': hr.horse.name if hr.horse else None,
                'horse_number': hr.horse.horse_number if hr.horse else None,
                'finish_position': hr.finish_position,
                'popularity': hr.popularity
            })
        
        # 着順でソート
        horse_results.sort(key=lambda x: x['finish_position'] if x['finish_position'] else 999)
        
        # 払い戻しを整形
        payouts = []
        for payout in race_result.payouts:
            payouts.append({
                'bet_type_name': payout.bet_type_ref.name if payout.bet_type_ref else None,
                'winning_numbers': payout.winning_numbers,
                'payout_amount': payout.payout_amount
            })
        
        return {
            'race_status': race_result.race_status,
            'result_fetched_at': race_result.result_fetched_at.isoformat() if race_result.result_fetched_at else None,
            'horse_results': horse_results,
            'payouts': payouts
        }
    
    async def check_race_result_exists(self, race_id: int) -> bool:
        """レース結果が保存済みか確認"""
        stmt = select(RaceResult.id).where(RaceResult.race_id == race_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None