# backend/scripts/test_statistics_api.py
"""
統計API テストスクリプト

使い方:
    python -m scripts.test_statistics_api
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from app.core.database import AsyncSessionLocal
from app.services.accuracy_calculation_service import AccuracyCalculationService


async def test_statistics():
    """統計計算のテスト"""
    
    async with AsyncSessionLocal() as session:
        service = AccuracyCalculationService(session)
        
        # テスト期間: 過去30日間
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        print(f"\n{'='*60}")
        print(f"統計計算テスト")
        print(f"期間: {start_date} to {end_date}")
        print(f"{'='*60}\n")
        
        try:
            # サマリー計算
            summary = await service.calculate_summary(
                start_date=start_date,
                end_date=end_date,
                win_threshold=80.0,
                place_threshold=85.0
            )
            
            # 結果表示
            print("【期間情報】")
            print(f"  開始日: {summary['period']['start_date']}")
            print(f"  終了日: {summary['period']['end_date']}")
            print(f"  日数: {summary['period']['total_days']}日")
            print()
            
            print("【順位ベース統計】")
            rank_stats = summary['by_rank']
            print(f"  総レース数: {rank_stats['total_races']}")
            print(f"  単勝:")
            print(f"    的中数: {rank_stats['win']['hits']}")
            print(f"    的中率: {rank_stats['win']['accuracy']}%")
            print(f"    平均配当: {rank_stats['win']['average_payout']}円")
            print(f"    ROI: {rank_stats['win']['roi']}%")
            print(f"  複勝:")
            print(f"    的中数: {rank_stats['place']['hits']}")
            print(f"    的中率: {rank_stats['place']['accuracy']}%")
            print(f"    平均配当: {rank_stats['place']['average_payout']}円")
            print(f"    ROI: {rank_stats['place']['roi']}%")
            print()
            
            print("【確率閾値ベース統計】")
            prob_stats = summary['by_probability']
            print(f"  単勝 (≥{prob_stats['win']['threshold']}%):")
            print(f"    推奨レース数: {prob_stats['win']['recommended_races']}")
            print(f"    的中数: {prob_stats['win']['hits']}")
            print(f"    的中率: {prob_stats['win']['accuracy']}%")
            print(f"    平均確率: {prob_stats['win']['average_probability']}%")
            print(f"    平均配当: {prob_stats['win']['average_payout']}円")
            print(f"    ROI: {prob_stats['win']['roi']}%")
            print(f"    推奨なし: {prob_stats['win']['no_recommendation_races']}レース")
            print()
            print(f"  複勝 (≥{prob_stats['place']['threshold']}%):")
            print(f"    推奨レース数: {prob_stats['place']['recommended_races']}")
            print(f"    的中数: {prob_stats['place']['hits']}")
            print(f"    的中率: {prob_stats['place']['accuracy']}%")
            print(f"    平均確率: {prob_stats['place']['average_probability']}%")
            print(f"    平均配当: {prob_stats['place']['average_payout']}円")
            print(f"    ROI: {prob_stats['place']['roi']}%")
            print(f"    推奨なし: {prob_stats['place']['no_recommendation_races']}レース")
            print()
            
            print("【確率範囲別統計 - 単勝】")
            for range_stat in summary['probability_breakdown']['win']:
                print(f"  {range_stat['range']}: {range_stat['races']}レース, 的中率{range_stat['accuracy']}%, ROI{range_stat['roi']}%")
            print()
            
            print("【確率範囲別統計 - 複勝】")
            for range_stat in summary['probability_breakdown']['place']:
                print(f"  {range_stat['range']}: {range_stat['races']}レース, 的中率{range_stat['accuracy']}%, ROI{range_stat['roi']}%")
            print()
            
            print("【競馬場別統計】")
            for venue_stat in summary['by_venue'][:5]:  # 上位5競馬場のみ
                print(f"  {venue_stat['venue']}:")
                print(f"    総レース数: {venue_stat['by_rank']['total_races']}")
                print(f"    順位ベース単勝的中率: {venue_stat['by_rank']['win']['accuracy']}%")
                print(f"    確率ベース単勝的中率: {venue_stat['by_probability']['win']['accuracy']}% ({venue_stat['by_probability']['win']['recommended_races']}レース推奨)")
            print()
            
            print("【グレード別統計】")
            for grade_stat in summary['by_grade']:
                print(f"  {grade_stat['grade']}:")
                print(f"    総レース数: {grade_stat['by_rank']['total_races']}")
                print(f"    順位ベース単勝的中率: {grade_stat['by_rank']['win']['accuracy']}%")
                print(f"    確率ベース単勝的中率: {grade_stat['by_probability']['win']['accuracy']}% ({grade_stat['by_probability']['win']['recommended_races']}レース推奨)")
            print()
            
            print("\n✅ 統計計算テスト成功")
            
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()


async def test_api_endpoint():
    """APIエンドポイントのテスト（手動確認用）"""
    import httpx
    
    base_url = "http://localhost:8000"
    
    print(f"\n{'='*60}")
    print(f"統計API エンドポイントテスト")
    print(f"{'='*60}\n")
    
    try:
        async with httpx.AsyncClient() as client:
            # サマリー取得
            print("【GET /api/statistics/summary】")
            response = await client.get(
                f"{base_url}/api/statistics/summary",
                params={
                    "win_threshold": 80.0,
                    "place_threshold": 85.0
                },
                timeout=60.0
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"総レース数: {data['by_rank']['total_races']}")
                print(f"順位ベース単勝的中率: {data['by_rank']['win']['accuracy']}%")
                print(f"確率ベース単勝的中率: {data['by_probability']['win']['accuracy']}%")
                print("\n✅ APIテスト成功")
            else:
                print(f"❌ エラー: {response.text}")
    
    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        print("※ サーバーが起動しているか確認してください")


if __name__ == "__main__":
    print("\n統計機能テスト")
    print("=" * 60)
    
    # 統計計算テスト
    asyncio.run(test_statistics())
    
    print("\n" + "=" * 60)
    print("APIエンドポイントテストを実行しますか？ (y/n)")
    print("※ 事前に 'python main.py' でサーバーを起動してください")
    
    choice = input("> ").lower()
    if choice == 'y':
        asyncio.run(test_api_endpoint())
    else:
        print("APIテストをスキップしました")