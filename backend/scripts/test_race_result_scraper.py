# backend/scripts/test_race_result_scraper.py
"""
レース結果スクレイパーの動作確認スクリプト

使用方法:
    cd backend
    python -m scripts.test_race_result_scraper
"""

import sys
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.race_result_scraper import RaceResultScraper

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_scraper():
    """スクレイパーのテスト"""
    
    print("=" * 60)
    print("レース結果スクレイパー 動作確認")
    print("=" * 60)
    
    scraper = RaceResultScraper()
    
    # テストケース
    test_cases = [
        {
            "race_id": "202406040911",
            "description": "2024年スプリンターズS（G1）"
        },
        {
            "race_id": "202405010112",
            "description": "2024年東京1回1日12R（通常レース）"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"テストケース {i}: {test_case['description']}")
        print(f"レースID: {test_case['race_id']}")
        print(f"{'=' * 60}")
        
        try:
            result = scraper.scrape_race_result(test_case['race_id'])
            
            if result is None:
                print("❌ スクレイピング失敗")
                continue
            
            print(f"\n✅ スクレイピング成功")
            print(f"\n【レース情報】")
            print(f"  ステータス: {result['race_status']}")
            print(f"  出走頭数: {len(result['horse_results'])}頭")
            print(f"  払い戻し情報: {len(result['payouts'])}件")
            
            # 馬結果の表示
            print(f"\n【着順結果】")
            print(f"  {'着順':<6} {'馬番':<6} {'人気':<6} {'Netkeiba馬ID':<15}")
            print(f"  {'-' * 45}")
            
            for hr in result['horse_results'][:5]:  # 上位5頭のみ表示
                finish_pos = hr['finish_position'] if hr['finish_position'] else '-'
                horse_num = hr['horse_number']
                popularity = hr['popularity'] if hr['popularity'] else '-'
                netkeiba_horse_id = hr['netkeiba_horse_id'] if hr['netkeiba_horse_id'] else '-'
                
                print(f"  {str(finish_pos):<6} {str(horse_num):<6} {str(popularity):<6} {str(netkeiba_horse_id):<15}")
            
            if len(result['horse_results']) > 5:
                print(f"  ... 他 {len(result['horse_results']) - 5}頭")
            
            # 払い戻しの表示
            print(f"\n【払い戻し情報】")
            print(f"  {'券種':<10} {'馬番':<10} {'払い戻し額':<15}")
            print(f"  {'-' * 40}")
            
            for payout in result['payouts']:
                bet_type_ja = "単勝" if payout['bet_type'] == 'win' else "複勝"
                print(f"  {bet_type_ja:<10} {payout['winning_numbers']:<10} {payout['payout_amount']:>10}円")
            
            # データ整合性チェック
            print(f"\n【データ整合性チェック】")
            
            # 1. 馬IDが取得できているか
            horses_with_id = [hr for hr in result['horse_results'] if hr['netkeiba_horse_id'] is not None]
            id_ratio = len(horses_with_id) / len(result['horse_results']) * 100 if result['horse_results'] else 0
            print(f"  馬ID取得率: {id_ratio:.1f}% ({len(horses_with_id)}/{len(result['horse_results'])})")
            
            # 2. 着順が連続しているか
            positions = [hr['finish_position'] for hr in result['horse_results'] if hr['finish_position'] is not None]
            positions.sort()
            expected_positions = list(range(1, len(positions) + 1))
            positions_ok = positions == expected_positions
            print(f"  着順連続性: {'✅ OK' if positions_ok else '⚠️ NG'}")
            
            # 3. 人気順位の範囲チェック
            popularities = [hr['popularity'] for hr in result['horse_results'] if hr['popularity'] is not None]
            if popularities:
                min_pop = min(popularities)
                max_pop = max(popularities)
                print(f"  人気順位範囲: {min_pop}番人気 ～ {max_pop}番人気")
            
            # 4. 払い戻しデータの存在確認
            has_win = any(p['bet_type'] == 'win' for p in result['payouts'])
            has_place = any(p['bet_type'] == 'place' for p in result['payouts'])
            print(f"  単勝データ: {'✅ あり' if has_win else '❌ なし'}")
            print(f"  複勝データ: {'✅ あり' if has_place else '❌ なし'}")
            
            print(f"\n✅ テストケース {i} 完了")
            
        except Exception as e:
            print(f"\n❌ エラー発生: {e}")
            logger.error(f"テストケース {i} でエラー", exc_info=True)
    
    print(f"\n{'=' * 60}")
    print("全テスト完了")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    test_scraper()