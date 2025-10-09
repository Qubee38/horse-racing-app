# backend/scripts/test_probability_based_extraction.py
"""
確率閾値ベース統計のデータ抽出テストスクリプト

使用方法:
    python -m scripts.test_probability_based_extraction

機能:
    - 指定期間のレース結果を取得
    - 各レースで推奨された馬を表示
    - 的中/不的中を詳細に表示
    - 統計サマリーを表示
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload

from app.models.race import Race
from app.models.horse import Horse
from app.models.prediction import Prediction
from app.models.race_result import RaceResult, HorseResult, Payout
from app.services.hit_criteria import HitCriteria


# データベース接続
DATABASE_URL = "sqlite+aiosqlite:///./data/horse_racing.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_race_results_with_predictions(
    db: AsyncSession,
    start_date: date,
    end_date: date
):
    """レース結果と予測データを取得"""
    stmt = (
        select(RaceResult)
        .join(Race, RaceResult.race_id == Race.id)
        .where(
            and_(
                RaceResult.race_status == "completed",
                Race.race_date >= start_date,
                Race.race_date <= end_date,
                Race.id.isnot(None)
            )
        )
        .options(
            selectinload(RaceResult.race),
            selectinload(RaceResult.horse_results),
            selectinload(RaceResult.payouts)
        )
        .order_by(Race.race_date, Race.race_number)
    )
    
    result = await db.execute(stmt)
    race_results = result.scalars().all()
    
    # race が None でないものだけ
    return [rr for rr in race_results if rr.race is not None]


async def get_latest_predictions(db: AsyncSession, race_id: int):
    """最新の予測データを取得"""
    from sqlalchemy import func
    
    # 最新の予測日時を取得
    latest_date_stmt = (
        select(func.max(Prediction.prediction_date))
        .where(Prediction.race_id == race_id)
    )
    result = await db.execute(latest_date_stmt)
    latest_date = result.scalar_one_or_none()
    
    if not latest_date:
        return []
    
    # 最新の予測データを取得
    stmt = (
        select(Prediction)
        .where(
            and_(
                Prediction.race_id == race_id,
                Prediction.prediction_date == latest_date
            )
        )
        .order_by(Prediction.win_probability.desc())
    )
    
    result = await db.execute(stmt)
    return result.scalars().all()


async def test_probability_based_extraction(
    win_threshold: float = 80.0,
    place_threshold: float = 85.0,
    days: int = 30
):
    """確率閾値ベースの抽出テスト"""
    
    async with AsyncSessionLocal() as db:
        # 期間設定
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        print("=" * 80)
        print(f"確率閾値ベース統計 - データ抽出テスト")
        print("=" * 80)
        print(f"期間: {start_date} 〜 {end_date} ({days}日間)")
        print(f"単勝閾値: {win_threshold}%")
        print(f"複勝閾値: {place_threshold}%")
        print("=" * 80)
        print()
        
        # レース結果取得
        race_results = await get_race_results_with_predictions(db, start_date, end_date)
        print(f"対象レース数: {len(race_results)}")
        print()
        
        if not race_results:
            print("レース結果が見つかりませんでした")
            return
        
        # 統計用変数
        win_stats = {
            "total_races": 0,
            "recommended_races": 0,
            "total_horses": 0,
            "hit_horses": 0,
            "details": []
        }
        
        place_stats = {
            "total_races": 0,
            "recommended_races": 0,
            "total_horses": 0,
            "hit_horses": 0,
            "details": []
        }
        
        # 各レースを処理
        for race_result in race_results:
            race = race_result.race
            
            # 予測データ取得
            predictions = await get_latest_predictions(db, race_result.race_id)
            
            if not predictions:
                continue
            
            win_stats["total_races"] += 1
            place_stats["total_races"] += 1
            
            # 実際の結果
            actual_winner_id = None
            actual_top3_ids = []
            
            for hr in race_result.horse_results:
                if hr.finish_position == 1:
                    actual_winner_id = hr.horse_id
                if hr.finish_position is not None and hr.finish_position <= 3:
                    if hr.horse_id:
                        actual_top3_ids.append(hr.horse_id)
            
            if not actual_winner_id:
                continue
            
            # 払い戻し
            win_payout = None
            place_payout = None
            for payout in race_result.payouts:
                if payout.bet_type_ref and payout.bet_type_ref.code == "win":
                    win_payout = payout.payout_amount
                if payout.bet_type_ref and payout.bet_type_ref.code == "place":
                    place_payout = payout.payout_amount
            
            # ===== 単勝の抽出テスト =====
            win_recommended_info = HitCriteria.get_recommended_horse_info(
                predictions, win_threshold, "win"
            )
            
            if win_recommended_info:
                win_stats["recommended_races"] += 1
                recommended_count = win_recommended_info.get("count", 0)
                recommended_ids = win_recommended_info.get("horse_ids", [])
                avg_prob = win_recommended_info.get("avg_probability", 0)
                
                win_stats["total_horses"] += recommended_count
                
                # 的中判定
                win_hit = HitCriteria.is_win_hit_by_probability(
                    predictions, actual_winner_id, win_threshold
                )
                win_hit_count = HitCriteria.count_win_hits_by_probability(
                    predictions, actual_winner_id, win_threshold
                )
                
                if win_hit:
                    win_stats["hit_horses"] += win_hit_count
                
                # 推奨馬の詳細
                recommended_horses = []
                for pred in predictions:
                    if pred.horse_id in recommended_ids:
                        horse_name = f"馬ID:{pred.horse_id}"
                        is_winner = "★的中★" if pred.horse_id == actual_winner_id else ""
                        recommended_horses.append(
                            f"{horse_name} ({pred.win_probability:.1f}%) {is_winner}"
                        )
                
                win_stats["details"].append({
                    "race": f"{race.race_date} {race.venue} {race.race_number}R {race.race_name}",
                    "recommended_count": recommended_count,
                    "recommended_horses": recommended_horses,
                    "avg_probability": avg_prob,
                    "hit": win_hit,
                    "hit_count": win_hit_count,
                    "payout": win_payout
                })
            
            # ===== 複勝の抽出テスト =====
            place_recommended_info = HitCriteria.get_recommended_horse_info(
                predictions, place_threshold, "place"
            )
            
            if place_recommended_info:
                place_stats["recommended_races"] += 1
                recommended_count = place_recommended_info.get("count", 0)
                recommended_ids = place_recommended_info.get("horse_ids", [])
                avg_prob = place_recommended_info.get("avg_probability", 0)
                
                place_stats["total_horses"] += recommended_count
                
                # 的中判定
                place_hit = HitCriteria.is_place_hit_by_probability(
                    predictions, actual_top3_ids, place_threshold
                )
                place_hit_count = HitCriteria.count_place_hits_by_probability(
                    predictions, actual_top3_ids, place_threshold
                )
                
                if place_hit:
                    place_stats["hit_horses"] += place_hit_count
                
                # 推奨馬の詳細
                recommended_horses = []
                for pred in predictions:
                    if pred.horse_id in recommended_ids:
                        horse_name = f"馬ID:{pred.horse_id}"
                        is_hit = "★的中★" if pred.horse_id in actual_top3_ids else ""
                        recommended_horses.append(
                            f"{horse_name} ({pred.place_probability:.1f}%) {is_hit}"
                        )
                
                place_stats["details"].append({
                    "race": f"{race.race_date} {race.venue} {race.race_number}R {race.race_name}",
                    "recommended_count": recommended_count,
                    "recommended_horses": recommended_horses,
                    "avg_probability": avg_prob,
                    "hit": place_hit,
                    "hit_count": place_hit_count,
                    "payout": place_payout
                })
        
        # ===== 単勝の結果表示 =====
        print("=" * 80)
        print("【単勝】確率閾値ベース統計")
        print("=" * 80)
        print(f"総レース数: {win_stats['total_races']}")
        print(f"推奨レース数: {win_stats['recommended_races']}")
        print(f"推奨馬数: {win_stats['total_horses']}")
        print(f"的中馬数: {win_stats['hit_horses']}")
        if win_stats['total_horses'] > 0:
            accuracy = win_stats['hit_horses'] / win_stats['total_horses'] * 100
            print(f"的中率: {accuracy:.2f}% ({win_stats['hit_horses']}/{win_stats['total_horses']})")
        print()
        
        # 詳細表示（最初の10レースのみ）
        print("【推奨馬詳細】（最初の10レースのみ表示）")
        print("-" * 80)
        for i, detail in enumerate(win_stats["details"][:10], 1):
            print(f"\n{i}. {detail['race']}")
            print(f"   推奨馬数: {detail['recommended_count']}頭")
            print(f"   平均確率: {detail['avg_probability']:.1f}%")
            print(f"   的中: {'○' if detail['hit'] else '×'} (的中馬数: {detail['hit_count']})")
            print(f"   配当: {detail['payout']}円" if detail['payout'] else "   配当: なし")
            print("   推奨馬:")
            for horse in detail['recommended_horses']:
                print(f"     - {horse}")
        
        if len(win_stats["details"]) > 10:
            print(f"\n   ... 他 {len(win_stats['details']) - 10} レース")
        
        print()
        
        # ===== 複勝の結果表示 =====
        print("=" * 80)
        print("【複勝】確率閾値ベース統計")
        print("=" * 80)
        print(f"総レース数: {place_stats['total_races']}")
        print(f"推奨レース数: {place_stats['recommended_races']}")
        print(f"推奨馬数: {place_stats['total_horses']}")
        print(f"的中馬数: {place_stats['hit_horses']}")
        if place_stats['total_horses'] > 0:
            accuracy = place_stats['hit_horses'] / place_stats['total_horses'] * 100
            print(f"的中率: {accuracy:.2f}% ({place_stats['hit_horses']}/{place_stats['total_horses']})")
        print()
        
        # 詳細表示（最初の10レースのみ）
        print("【推奨馬詳細】（最初の10レースのみ表示）")
        print("-" * 80)
        for i, detail in enumerate(place_stats["details"][:10], 1):
            print(f"\n{i}. {detail['race']}")
            print(f"   推奨馬数: {detail['recommended_count']}頭")
            print(f"   平均確率: {detail['avg_probability']:.1f}%")
            print(f"   的中: {'○' if detail['hit'] else '×'} (的中馬数: {detail['hit_count']})")
            print(f"   配当: {detail['payout']}円" if detail['payout'] else "   配当: なし")
            print("   推奨馬:")
            for horse in detail['recommended_horses']:
                print(f"     - {horse}")
        
        if len(place_stats["details"]) > 10:
            print(f"\n   ... 他 {len(place_stats['details']) - 10} レース")
        
        print()
        print("=" * 80)
        print("テスト完了")
        print("=" * 80)


async def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="確率閾値ベース統計のデータ抽出テスト")
    parser.add_argument("--win-threshold", type=float, default=80.0, help="単勝閾値 (default: 80.0)")
    parser.add_argument("--place-threshold", type=float, default=85.0, help="複勝閾値 (default: 85.0)")
    parser.add_argument("--days", type=int, default=30, help="対象日数 (default: 30)")
    
    args = parser.parse_args()
    
    await test_probability_based_extraction(
        win_threshold=args.win_threshold,
        place_threshold=args.place_threshold,
        days=args.days
    )


if __name__ == "__main__":
    asyncio.run(main())