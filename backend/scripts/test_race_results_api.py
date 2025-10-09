# backend/scripts/test_race_results_api.py
"""
レース結果API テストスクリプト

使用方法:
    1. バックエンドサーバーを起動
       cd backend
       python main.py
    
    2. 別ターミナルでテスト実行
       cd backend
       python -m scripts.test_race_results_api
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000/api"


def print_section(title):
    """セクション区切りを表示"""
    print(f"\n{'=' * 60}")
    print(title)
    print('=' * 60)


def test_check_exists():
    """レース結果存在確認APIのテスト"""
    print_section("1. レース結果存在確認")
    
    race_id = 1
    url = f"{BASE_URL}/race-results/exists/{race_id}"
    
    try:
        response = requests.get(url)
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"結果: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data.get('exists', False)
        else:
            print(f"エラー: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ バックエンドサーバーに接続できません")
        print("   対処: python main.py でサーバーを起動してください")
        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def test_fetch_race_result():
    """レース結果取得APIのテスト"""
    print_section("2. レース結果取得・保存")
    
    race_id = 1
    url = f"{BASE_URL}/race-results/fetch/{race_id}"
    
    try:
        response = requests.post(url)
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"結果: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("\n⏳ バックグラウンド処理を待機中（10秒）...")
            time.sleep(10)
            return True
        else:
            print(f"エラー: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def test_get_race_result():
    """保存済みレース結果取得APIのテスト"""
    print_section("3. 保存済みレース結果取得")
    
    race_id = 1
    url = f"{BASE_URL}/race-results/{race_id}"
    
    try:
        response = requests.get(url)
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data is None:
                print("結果: レース結果が見つかりません")
                return False
            
            print(f"\n【レース結果】")
            print(f"  ステータス: {data['race_status']}")
            print(f"  取得日時: {data['result_fetched_at']}")
            print(f"  出走馬: {len(data['horse_results'])}頭")
            print(f"  払い戻し: {len(data['payouts'])}件")
            
            print(f"\n【着順結果】(上位3頭)")
            for i, hr in enumerate(data['horse_results'][:3], 1):
                print(f"  {hr['finish_position']}着: {hr['horse_name']} (馬番{hr['horse_number']})")
            
            print(f"\n【払い戻し】")
            for payout in data['payouts']:
                print(f"  {payout['bet_type_name']}: {payout['winning_numbers']}番 → {payout['payout_amount']}円")
            
            return True
        else:
            print(f"エラー: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def test_get_race_result_summary():
    """レース結果サマリー取得APIのテスト"""
    print_section("4. レース結果サマリー取得")
    
    race_id = 1
    url = f"{BASE_URL}/race-results/summary/{race_id}"
    
    try:
        response = requests.get(url)
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data is None:
                print("結果: レース結果が見つかりません")
                return False
            
            print(f"\n【サマリー】")
            print(f"  ステータス: {data['race_status']}")
            print(f"  出走馬数: {len(data['horse_results'])}頭")
            print(f"  払い戻し数: {len(data['payouts'])}件")
            
            return True
        else:
            print(f"エラー: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def main():
    """メインテスト実行"""
    print_section("レース結果API テスト")
    print("前提条件: バックエンドサーバーが起動していること")
    
    results = []
    
    # 1. 存在確認
    exists = test_check_exists()
    if exists is None:
        return
    results.append(("存在確認", exists is not None))
    
    # 2. 結果が存在しない場合は取得
    if not exists:
        print("\n💡 レース結果が存在しないため、取得を実行します")
        success = test_fetch_race_result()
        results.append(("結果取得・保存", success))
        
        if not success:
            print("\n❌ レース結果取得に失敗したため、テストを中断します")
            return
    else:
        print("\n✅ レース結果が既に存在します（取得をスキップ）")
    
    # 3. 保存済み結果取得
    success = test_get_race_result()
    results.append(("保存済み結果取得", success))
    
    # 4. サマリー取得
    success = test_get_race_result_summary()
    results.append(("サマリー取得", success))
    
    # 結果サマリー
    print_section("テスト結果サマリー")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    print(f"\n{'✅ 全テスト成功' if all_passed else '❌ 一部テスト失敗'}")


if __name__ == "__main__":
    main()