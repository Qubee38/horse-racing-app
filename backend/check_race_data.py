#!/usr/bin/env python3
"""
データベース内のレース結果の期間を確認するスクリプト
"""
import asyncio
import sys
import os

# プロジェクトのルートをPYTHONPATHに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, func
from app.core.database import AsyncSessionLocal
from app.models.race import Race
from app.models.race_result import RaceResult


async def check_race_data():
    """レース結果の期間を確認"""
    print("=== データベース内のレース結果確認 ===\n")

    async with AsyncSessionLocal() as db:
        # レース結果の総数
        stmt = select(func.count(RaceResult.id)).where(
            RaceResult.race_status == "completed"
        )
        result = await db.execute(stmt)
        total_results = result.scalar_one()

        print(f"✓ 完了済みレース結果: {total_results}件")

        if total_results == 0:
            print("\n❌ レース結果が1件も存在しません。")
            print("   レース結果を取得してください。\n")
            return False

        # レース結果の日付範囲を取得
        stmt = (
            select(
                func.min(Race.race_date).label("min_date"),
                func.max(Race.race_date).label("max_date")
            )
            .join(RaceResult, RaceResult.race_id == Race.id)
            .where(RaceResult.race_status == "completed")
        )
        result = await db.execute(stmt)
        row = result.one()

        min_date = row.min_date
        max_date = row.max_date

        print(f"✓ 最古のレース日: {min_date}")
        print(f"✓ 最新のレース日: {max_date}")

        # 競馬場別のレース数
        stmt = (
            select(
                Race.venue,
                func.count(RaceResult.id).label("count")
            )
            .join(RaceResult, RaceResult.race_id == Race.id)
            .where(RaceResult.race_status == "completed")
            .group_by(Race.venue)
            .order_by(func.count(RaceResult.id).desc())
        )
        result = await db.execute(stmt)
        venues = result.all()

        print(f"\n✓ 競馬場別レース数:")
        for venue, count in venues[:10]:  # 上位10件
            print(f"  - {venue}: {count}件")

        print(f"\n推奨する統計取得期間:")
        print(f"  start_date={min_date}&end_date={max_date}")
        print(f"\nブラウザでアクセス:")
        print(f"  http://localhost:8000/api/statistics/summary?start_date={min_date}&end_date={max_date}")

        return True


if __name__ == "__main__":
    result = asyncio.run(check_race_data())
    sys.exit(0 if result else 1)
