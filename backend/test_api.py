import asyncio
import httpx
from datetime import date

async def test_api():
    """APIの動作をテスト"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # ヘルスチェック
        print("Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        
        # レース一覧取得
        print("\nTesting races endpoint...")
        test_date = "2025-09-22"
        response = await client.get(f"{base_url}/api/races/{test_date}")
        print(f"Races for {test_date}: {response.status_code}")
        if response.status_code == 200:
            races = response.json()
            print(f"Found {len(races)} races")
            for race in races:
                print(f"  - {race['venue']} {race['race_name']}: {race['horse_count']} horses")
                
                # 各レースの馬情報を取得
                race_id = race['id']
                horse_response = await client.get(f"{base_url}/api/races/{race_id}/horses")
                if horse_response.status_code == 200:
                    horses = horse_response.json()
                    print(f"    Horses in race {race_id}: {len(horses)}")
                    for horse in horses[:2]:  # 最初の2頭だけ表示
                        print(f"      {horse['horse_number']}. {horse['name']} ({horse['jockey']}) - {horse['odds']}倍")

if __name__ == "__main__":
    print("Testing API endpoints...")
    asyncio.run(test_api())