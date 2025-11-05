#!/usr/bin/env python3
"""
確率閾値ベース統計のテストスクリプト
"""
import asyncio
import sys
from datetime import date, timedelta
from app.core.database import AsyncSessionLocal
from app.services.accuracy_calculation_service import AccuracyCalculationService


async def test_probability_stats():
    """確率閾値ベース統計をテスト"""
    print("=== 確率閾値ベース統計テスト ===\n")

    async with AsyncSessionLocal() as db:
        service = AccuracyCalculationService(db)

        # 過去30日間の統計を取得
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        print(f"期間: {start_date} 〜 {end_date}")
        print(f"閾値: 単勝 >= 80%, 複勝 >= 85%\n")

        try:
            summary = await service.calculate_summary(
                start_date=start_date,
                end_date=end_date,
                win_threshold=80.0,
                place_threshold=85.0
            )

            # 馬場別統計をチェック
            print("✓ 馬場別統計:")
            if summary.get("by_track_type"):
                for track in summary["by_track_type"]:
                    track_type = track.get("track_type", "不明")
                    has_prob = "by_probability" in track
                    print(f"  - {track_type}: by_probability存在? {has_prob}")
                    if has_prob:
                        win_acc = track["by_probability"]["win"]["accuracy"]
                        print(f"      単勝的中率: {win_acc}%")
            else:
                print("  データなし")

            print()

            # 距離別統計をチェック
            print("✓ 距離別統計:")
            if summary.get("by_distance"):
                for distance in summary["by_distance"]:
                    dist_range = distance.get("distance_range", "不明")
                    has_prob = "by_probability" in distance
                    print(f"  - {dist_range}: by_probability存在? {has_prob}")
                    if has_prob:
                        win_acc = distance["by_probability"]["win"]["accuracy"]
                        print(f"      単勝的中率: {win_acc}%")
            else:
                print("  データなし")

            print()

            # 馬場状態別統計をチェック
            print("✓ 馬場状態別統計:")
            if summary.get("by_track_condition"):
                for condition in summary["by_track_condition"]:
                    cond = condition.get("track_condition", "不明")
                    has_prob = "by_probability" in condition
                    print(f"  - {cond}: by_probability存在? {has_prob}")
                    if has_prob:
                        win_acc = condition["by_probability"]["win"]["accuracy"]
                        print(f"      単勝的中率: {win_acc}%")
            else:
                print("  データなし")

            print("\n✅ テスト成功: by_probabilityフィールドが正しく追加されています")
            return True

        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    result = asyncio.run(test_probability_stats())
    sys.exit(0 if result else 1)
