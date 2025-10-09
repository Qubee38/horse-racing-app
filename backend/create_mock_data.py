import asyncio
import sys
import os

# パスを追加してappモジュールをインポート可能にする
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.race_service import RaceService

async def create_mock_data():
    """モックデータを作成してデータベースに投入"""
    async with AsyncSessionLocal() as db:
        service = RaceService(db)
        
        # レースデータ
        mock_races = [
            {
                "date": date(2025, 9, 22),
                "venue": "東京",
                "race_name": "第1R",
                "race_number": 1,
                "distance": 1400,
                "surface": "芝",
                "start_time": "10:10"
            },
            {
                "date": date(2025, 9, 22),
                "venue": "東京",
                "race_name": "第2R",
                "race_number": 2,
                "distance": 1600,
                "surface": "芝",
                "start_time": "10:40"
            },
            {
                "date": date(2025, 9, 22),
                "venue": "京都",
                "race_name": "第1R",
                "race_number": 1,
                "distance": 1200,
                "surface": "ダート",
                "start_time": "10:15"
            },
            {
                "date": date(2025, 9, 23),
                "venue": "阪神",
                "race_name": "第1R",
                "race_number": 1,
                "distance": 1800,
                "surface": "芝",
                "start_time": "10:05"
            }
        ]
        
        # レースを作成
        created_races = []
        for race_data in mock_races:
            try:
                result = await service.create_race(race_data)
                created_races.append(result["id"])
                print(f"Created race: {race_data['venue']} {race_data['race_name']} (ID: {result['id']})")
            except Exception as e:
                print(f"Error creating race {race_data}: {e}")
        
        # 各レースに馬を追加
        mock_horses_data = [
            # 東京第1R の馬
            [
                {"name": "サンプルホース1", "jockey": "武豊", "frame_number": 1, "horse_number": 1, "odds": 3.2},
                {"name": "テストホース2", "jockey": "川田将雅", "frame_number": 2, "horse_number": 3, "odds": 4.1},
                {"name": "モックホース3", "jockey": "福永祐一", "frame_number": 3, "horse_number": 5, "odds": 5.8},
                {"name": "デモホース4", "jockey": "戸崎圭太", "frame_number": 4, "horse_number": 7, "odds": 7.2},
                {"name": "サンプル馬5", "jockey": "ルメール", "frame_number": 5, "horse_number": 9, "odds": 8.5},
            ],
            # 東京第2R の馬
            [
                {"name": "スピードスター", "jockey": "横山武史", "frame_number": 1, "horse_number": 2, "odds": 2.8},
                {"name": "ライトニング", "jockey": "坂井瑠星", "frame_number": 2, "horse_number": 4, "odds": 3.5},
                {"name": "ファイヤーボール", "jockey": "吉田隼人", "frame_number": 3, "horse_number": 6, "odds": 6.2},
                {"name": "アイスブレイク", "jockey": "松山弘平", "frame_number": 4, "horse_number": 8, "odds": 9.1},
            ],
            # 京都第1R の馬
            [
                {"name": "ダートキング", "jockey": "幸英明", "frame_number": 1, "horse_number": 1, "odds": 2.1},
                {"name": "マッドランナー", "jockey": "和田竜二", "frame_number": 2, "horse_number": 3, "odds": 4.8},
                {"name": "サンドストーム", "jockey": "藤岡康太", "frame_number": 3, "horse_number": 5, "odds": 7.5},
            ],
            # 阪神第1R の馬
            [
                {"name": "ロングディスタンス", "jockey": "岩田康誠", "frame_number": 1, "horse_number": 2, "odds": 3.9},
                {"name": "マラソンランナー", "jockey": "西村淳也", "frame_number": 2, "horse_number": 4, "odds": 5.2},
                {"name": "エンデュランス", "jockey": "団野大成", "frame_number": 3, "horse_number": 6, "odds": 8.7},
                {"name": "スタミナキング", "jockey": "斎藤新", "frame_number": 4, "horse_number": 8, "odds": 12.3},
            ]
        ]
        
        # 各レースに馬を追加
        for i, race_id in enumerate(created_races):
            if i < len(mock_horses_data):
                horses = mock_horses_data[i]
                for horse_data in horses:
                    horse_data["race_id"] = race_id
                    try:
                        result = await service.create_horse(horse_data)
                        print(f"  Created horse: {horse_data['name']} (ID: {result['id']})")
                    except Exception as e:
                        print(f"  Error creating horse {horse_data}: {e}")

async def main():
    print("Creating mock data...")
    try:
        await create_mock_data()
        print("Mock data creation completed!")
    except Exception as e:
        print(f"Error during mock data creation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())