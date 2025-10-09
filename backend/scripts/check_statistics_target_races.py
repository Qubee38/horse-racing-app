# backend/scripts/check_statistics_target_races.py
"""
統計対象レースの確認

使い方:
    python -m scripts.check_statistics_target_races
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from sqlalchemy import select, and_, func, exists
from app.core.database import AsyncSessionLocal
from app.models.race import Race
from app.models.race_result import RaceResult
from app.models.prediction import Prediction


async def check_target_races():
    """統計対象レースを確認"""
    
    async with AsyncSessionLocal() as session:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        print(f"\n{'='*60}")
        print(f"統計対象レース確認")
        print(f"期間: {start_date} to {end_date}")
        print(f"{'='*60}\n")
        
        # 1. 全レース数
        total_races_stmt = select(func.count(Race.id)).where(
            and_(
                Race.race_date >= start_date,
                Race.race_date <= end_date
            )
        )
        result = await session.execute(total_races_stmt)
        total_races = result.scalar()
        
        # 2. 予測があるレース数
        races_with_prediction_stmt = select(func.count(Race.id.distinct())).where(
            and_(
                Race.race_date >= start_date,
                Race.race_date <= end_date,
                exists(select(1).where(Prediction.race_id == Race.id))
            )
        )
        result = await session.execute(races_with_prediction_stmt)
        races_with_prediction = result.scalar()
        
        # 3. レース結果があるレース数
        races_with_result_stmt = select(func.count(RaceResult.id)).join(
            Race, RaceResult.race_id == Race.id
        ).where(
            and_(
                Race.race_date >= start_date,
                Race.race_date <= end_date,
                RaceResult.race_status == "completed"
            )
        )
        result = await session.execute(races_with_result_stmt)
        races_with_result = result.scalar()
        
        # 4. 予測とレース結果の両方があるレース数（統計対象）
        target_races_stmt = select(func.count(RaceResult.id)).join(
            Race, RaceResult.race_id == Race.id
        ).where(
            and_(
                Race.race_date >= start_date,
                Race.race_date <= end_date,
                RaceResult.race_status == "completed",
                exists(select(1).where(Prediction.race_id == Race.id))
            )
        )
        result = await session.execute(target_races_stmt)
        target_races = result.scalar()
        
        # 結果表示
        print(f"【レース集計】")
        print(f"  全レース数: {total_races}")
        print(f"  予測あり: {races_with_prediction}")
        print(f"  結果あり: {races_with_result}")
        print(f"  統計対象（予測+結果）: {target_races}")
        print()
        
        print(f"【除外されるレース】")
        print(f"  予測のみ（結果なし）: {races_with_prediction - target_races}")
        print(f"  結果のみ（予測なし）: {races_with_result - target_races}")
        print(f"  予測も結果もなし: {total_races - races_with_prediction - races_with_result + target_races}")
        print()
        
        # 5. 重複予測のあるレース
        duplicate_predictions_stmt = select(
            Prediction.race_id,
            func.count(func.distinct(Prediction.prediction_date)).label('prediction_count')
        ).where(
            exists(
                select(1).where(
                    and_(
                        Race.id == Prediction.race_id,
                        Race.race_date >= start_date,
                        Race.race_date <= end_date
                    )
                )
            )
        ).group_by(
            Prediction.race_id
        ).having(
            func.count(func.distinct(Prediction.prediction_date)) > 1
        )
        
        result = await session.execute(duplicate_predictions_stmt)
        duplicate_races = result.all()
        
        if duplicate_races:
            print(f"【重複予測のあるレース】")
            print(f"  重複レース数: {len(duplicate_races)}")
            for race_id, count in duplicate_races[:5]:  # 上位5件のみ表示
                print(f"    Race ID {race_id}: {count}回予測")
            if len(duplicate_races) > 5:
                print(f"    ... 他 {len(duplicate_races) - 5} レース")
            print(f"  ※ 統計では各レースの最新予測のみを使用")
        else:
            print(f"【重複予測のあるレース】")
            print(f"  なし")
        
        print(f"\n{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(check_target_races())