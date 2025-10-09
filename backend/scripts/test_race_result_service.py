# backend/scripts/test_race_result_service.py
"""
レース結果サービスの動作確認スクリプト

前提条件:
    - データベースが初期化済み（init_race_results.py実行済み）
    - テスト対象のレースがracesテーブルに存在すること
    - 該当レースの出走馬がhorsesテーブルに存在すること

使用方法:
    cd backend
    python -m scripts.test_race_result_service
"""

import sys
import asyncio
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.race import Race
from app.models.horse import Horse
from app.services.race_result_service import RaceResultService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def check_prerequisites():
    """前提条件の確認"""
    print("=" * 60)
    print("前提条件チェック")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # レースデータの確認
        stmt = select(Race).limit(1)
        result = await session.execute(stmt)
        race = result.scalar_one_or_none()
        
        if not race:
            print("❌ レースデータが存在しません")
            print("   対処: レースデータを登録してください")
            return False
        
        print(f"✅ レースデータ存在確認")
        print(f"   サンプルレース: {race.race_name} (ID: {race.id})")
        
        # netkeiba_race_idの確認
        if not race.netkeiba_race_id:
            print("❌ netkeiba_race_idが設定されていません")
            return False
        
        print(f"   Netkeiba ID: {race.netkeiba_race_id}")
        
        # 出走馬データの確認
        stmt = select(Horse).where(Horse.race_id == race.id)
        result = await session.execute(stmt)
        horses = result.scalars().all()
        
        if not horses:
            print(f"❌ 出走馬データが存在しません (race_id={race.id})")
            print("   対処: 予測実行で出走馬データを登録してください")
            return False
        
        print(f"✅ 出走馬データ存在確認: {len(horses)}頭")
        
        return True


async def test_fetch_and_save():
    """レース結果取得・保存のテスト"""
    print("\n" + "=" * 60)
    print("レース結果取得・保存テスト")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        service = RaceResultService(session)
        
        # テスト対象レースを取得
        stmt = select(Race).where(Race.netkeiba_race_id.isnot(None)).limit(1)
        result = await session.execute(stmt)
        race = result.scalar_one_or_none()
        
        if not race:
            print("❌ テスト対象レースが見つかりません")
            return
        
        print(f"\nテスト対象レース:")
        print(f"  ID: {race.id}")
        print(f"  名前: {race.race_name}")
        print(f"  開催日: {race.race_date}")
        print(f"  Netkeiba ID: {race.netkeiba_race_id}")
        
        # レース結果が既に存在するか確認
        exists = await service.check_race_result_exists(race.id)
        if exists:
            print(f"\n⚠️ レース結果が既に存在します（上書き保存されます）")
        
        # レース結果取得・保存
        print(f"\nレース結果取得開始...")
        race_result = await service.fetch_and_save_race_result(race.id)
        
        if not race_result:
            print("❌ レース結果取得・保存失敗")
            return
        
        # リレーションを再読み込み（eager load）
        await session.refresh(race_result, ['horse_results', 'payouts'])
        
        print(f"✅ レース結果保存成功")
        print(f"\n【保存結果】")
        print(f"  RaceResult ID: {race_result.id}")
        print(f"  ステータス: {race_result.race_status}")
        print(f"  取得日時: {race_result.result_fetched_at}")
        print(f"  出走馬結果: {len(race_result.horse_results)}件")
        print(f"  払い戻し: {len(race_result.payouts)}件")


async def test_get_race_result():
    """レース結果取得のテスト"""
    print("\n" + "=" * 60)
    print("レース結果取得テスト")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        service = RaceResultService(session)
        
        # レース結果が存在するレースを取得
        stmt = select(Race).where(Race.netkeiba_race_id.isnot(None)).limit(1)
        result = await session.execute(stmt)
        race = result.scalar_one_or_none()
        
        if not race:
            print("❌ テスト対象レースが見つかりません")
            return
        
        # レース結果サマリー取得
        summary = await service.get_race_result_summary(race.id)
        
        if not summary:
            print("❌ レース結果が見つかりません")
            print("   対処: 先に fetch_and_save_race_result を実行してください")
            return
        
        print(f"✅ レース結果取得成功")
        print(f"\n【レース結果サマリー】")
        print(f"  ステータス: {summary['race_status']}")
        print(f"  取得日時: {summary['result_fetched_at']}")
        
        print(f"\n【着順結果】(上位5頭)")
        print(f"  {'着順':<6} {'馬番':<6} {'馬名':<20}")
        print(f"  {'-' * 40}")
        
        for hr in summary['horse_results'][:5]:
            finish_pos = hr['finish_position'] if hr['finish_position'] else '-'
            horse_num = hr['horse_number'] if hr['horse_number'] else '-'
            horse_name = hr['horse_name'] if hr['horse_name'] else '-'
            
            print(f"  {str(finish_pos):<6} {str(horse_num):<6} {horse_name:<20}")
        
        print(f"\n【払い戻し情報】")
        print(f"  {'券種':<10} {'馬番':<10} {'払い戻し額':<15}")
        print(f"  {'-' * 40}")
        
        for payout in summary['payouts']:
            print(f"  {payout['bet_type_name']:<10} {payout['winning_numbers']:<10} {payout['payout_amount']:>10}円")


async def main():
    """メインテスト実行"""
    
    print("\n" + "=" * 60)
    print("レース結果サービス 動作確認")
    print("=" * 60)
    
    # 前提条件チェック
    if not await check_prerequisites():
        print("\n❌ 前提条件を満たしていません")
        return
    
    print("\n✅ 前提条件クリア")
    
    # テスト実行
    try:
        await test_fetch_and_save()
        await test_get_race_result()
        
        print("\n" + "=" * 60)
        print("✅ 全テスト完了")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        logger.error("テスト実行エラー", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())