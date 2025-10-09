#!/usr/bin/env python3
"""
NetkeibaRaceFinderの動作テストスクリプト
実際の過去の開催日でレースID取得をテスト
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_netkeiba_race_finder():
    """NetkeibaRaceFinderのテスト"""
    print("=" * 60)
    print("NetkeibaRaceFinder Test")
    print("=" * 60)
    
    try:
        # 改良版を使用
        from app.services.netkeiba_race_finder import netkeiba_finder
        
        # 実際の過去の開催日でテスト
        test_dates = [
            "2024-12-01",  # 最近の日付
            "2024-11-24",  # ジャパンカップ等の大レース開催日
            "2024-10-27",  # 天皇賞秋
            "2023-12-28"   # 有馬記念
        ]
        
        for test_date in test_dates:
            print(f"\n🧪 Testing date: {test_date}")
            print("-" * 40)
            
            try:
                races = netkeiba_finder.get_race_ids_for_date(test_date)
                
                if races:
                    print(f"✅ Found {len(races)} races")
                    
                    # 最初の3レースの詳細を表示
                    for i, race in enumerate(races[:3]):
                        print(f"  Race {i+1}:")
                        print(f"    ID: {race.get('netkeiba_race_id', 'unknown')}")
                        print(f"    Venue: {race.get('venue', 'unknown')}")
                        print(f"    Name: {race.get('race_name', 'unknown')}")
                        print(f"    URL: {race.get('url', 'unknown')}")
                    
                    if len(races) > 3:
                        print(f"    ... and {len(races) - 3} more races")
                    
                    # 1つ目のレースの詳細情報取得テスト
                    if races:
                        first_race = races[0]
                        race_id = first_race.get('netkeiba_race_id')
                        
                        print(f"\n  🔍 Getting details for race {race_id}...")
                        details = netkeiba_finder.get_race_details(race_id)
                        
                        if details:
                            print(f"    Start time: {details.get('start_time', 'unknown')}")
                            print(f"    Distance: {details.get('distance', 0)}m")
                            print(f"    Surface: {details.get('surface', 'unknown')}")
                            print(f"    Horse count: {details.get('horse_count', 0)}")
                        else:
                            print("    ⚠️ Could not get race details")
                
                else:
                    print("❌ No races found")
                
            except Exception as e:
                print(f"❌ Error testing date {test_date}: {e}")
                continue
        
        print("\n" + "=" * 60)
        print("Test Summary:")
        print("- If you see races found for any date, the finder is working")
        print("- If all dates return empty, there may be connectivity issues")
        print("- Check the logs above for specific error messages")
        print("=" * 60)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure the improved netkeiba_race_finder.py is in the correct location:")
        print("  backend/app/services/netkeiba_race_finder.py")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

def test_race_id_validation():
    """レースIDフォーマットの検証テスト"""
    print("\n" + "=" * 60)
    print("Race ID Format Validation Test")
    print("=" * 60)
    
    # 有効と思われるレースIDのテスト
    test_race_ids = [
        "202412010101",  # 2024年12月1日 1回目1日目 1レース
        "202411240901",  # ジャパンカップ候補
        "202410270505",  # 天皇賞秋候補
        "202312281107"   # 有馬記念候補
    ]
    
    try:
        from app.services.netkeiba_race_finder import netkeiba_finder
        
        for race_id in test_race_ids:
            print(f"\n🔍 Testing Race ID: {race_id}")
            
            try:
                # URLの構築確認
                url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
                print(f"  URL: {url}")
                
                # 軽量な検証
                is_valid = netkeiba_finder._validate_race_id(race_id)
                print(f"  Valid: {is_valid}")
                
            except Exception as e:
                print(f"  Error: {e}")
    
    except Exception as e:
        print(f"❌ Validation test error: {e}")

if __name__ == "__main__":
    print("Starting Netkeiba Race Finder Tests...")
    
    # 基本的なレース取得テスト
    test_netkeiba_race_finder()
    
    # レースIDフォーマット検証テスト
    test_race_id_validation()
    
    print("\nTest completed. Check results above.")
    print("If no races found, try running during Japanese daytime hours for better connectivity.")