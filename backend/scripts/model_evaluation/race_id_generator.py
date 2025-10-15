#!/usr/bin/env python3
"""
Netkeiba レースID生成スクリプト

JSONファイルからスケジュールを読み込み、レースIDを生成します。

使用方法:
    python generate_race_ids.py schedule.json
    python generate_race_ids.py schedule.json --output race_ids.json
    python generate_race_ids.py schedule.json --format csv
"""

import json
import csv
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any


class NetkeibaRaceIDGenerator:
    """NetkeibaのレースIDを生成するクラス"""
    
    # JRA競馬場コード
    PLACE_NAMES = {
        1: '札幌', 2: '函館', 3: '福島', 4: '新潟', 5: '東京',
        6: '中山', 7: '中京', 8: '京都', 9: '阪神', 10: '小倉'
    }
    
    def __init__(self, year: int):
        """
        Parameters
        ----------
        year : int
            対象年
        """
        self.year = year
    
    def generate_from_schedule(self, schedule: Dict[str, Any]) -> List[str]:
        """
        スケジュールからレースIDを生成
        
        Parameters
        ----------
        schedule : dict
            開催スケジュール
            例: {
                "5": {
                    "1": [1, 2, 3, 4],
                    "2": [1, 2, 3, 4, 5, 6]
                },
                ...
            }
        
        Returns
        -------
        List[str]
            レースIDのリスト
        """
        race_ids = []
        
        # キーが文字列の場合も対応
        for place_str, kai_schedule in schedule.items():
            place = int(place_str)
            
            for kai_str, days in kai_schedule.items():
                kai = int(kai_str)
                
                for day in days:
                    for race_num in range(1, 13):  # 1-12R
                        race_id = (
                            f"{self.year}"
                            f"{place:02d}"
                            f"{kai:02d}"
                            f"{day:02d}"
                            f"{race_num:02d}"
                        )
                        race_ids.append(race_id)
        
        return race_ids
    
    def parse_race_id(self, race_id: str) -> Dict[str, Any]:
        """
        レースIDを解析
        
        Parameters
        ----------
        race_id : str
            12桁のレースID
        
        Returns
        -------
        dict
            解析結果
        """
        if len(race_id) != 12:
            raise ValueError(f"レースIDは12桁である必要があります: {race_id}")
        
        place_code = int(race_id[4:6])
        
        return {
            'race_id': race_id,
            'year': int(race_id[0:4]),
            'place_code': place_code,
            'place_name': self.PLACE_NAMES.get(place_code, '不明'),
            'kai': int(race_id[6:8]),
            'day': int(race_id[8:10]),
            'race_num': int(race_id[10:12])
        }


def load_schedule(json_path: str) -> Dict[str, Any]:
    """
    JSONファイルからスケジュールを読み込む
    
    Parameters
    ----------
    json_path : str
        JSONファイルのパス
    
    Returns
    -------
    dict
        スケジュールデータ
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # スケジュールデータの取得
        if 'year' in data and 'schedule' in data:
            return data
        elif isinstance(data, dict) and all(k.isdigit() for k in data.keys()):
            # スケジュールのみの場合
            return {'schedule': data}
        else:
            raise ValueError("JSONフォーマットが不正です")
            
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {json_path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"エラー: JSONの解析に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


def save_as_json(race_ids: List[str], output_path: str, 
                 detailed: bool = False, generator: NetkeibaRaceIDGenerator = None):
    """
    JSON形式で保存
    
    Parameters
    ----------
    race_ids : List[str]
        レースIDのリスト
    output_path : str
        出力ファイルパス
    detailed : bool
        詳細情報も含めるか
    generator : NetkeibaRaceIDGenerator
        生成器（詳細情報用）
    """
    if detailed and generator:
        output_data = {
            'count': len(race_ids),
            'race_ids': [generator.parse_race_id(rid) for rid in race_ids]
        }
    else:
        output_data = {
            'count': len(race_ids),
            'race_ids': race_ids
        }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ {output_path} に保存しました ({len(race_ids):,}件)")


def save_as_csv(race_ids: List[str], output_path: str, 
                detailed: bool = False, generator: NetkeibaRaceIDGenerator = None):
    """
    CSV形式で保存
    
    Parameters
    ----------
    race_ids : List[str]
        レースIDのリスト
    output_path : str
        出力ファイルパス
    detailed : bool
        詳細情報も含めるか
    generator : NetkeibaRaceIDGenerator
        生成器（詳細情報用）
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if detailed and generator:
            writer = csv.writer(f)
            writer.writerow(['race_id', 'year', 'place_code', 'place_name', 'kai', 'day', 'race_num'])
            for race_id in race_ids:
                parsed = generator.parse_race_id(race_id)
                writer.writerow([
                    parsed['race_id'],
                    parsed['year'],
                    f"{parsed['place_code']:02d}",
                    parsed['place_name'],
                    parsed['kai'],
                    parsed['day'],
                    parsed['race_num']
                ])
        else:
            writer = csv.writer(f)
            writer.writerow(['race_id'])
            for race_id in race_ids:
                writer.writerow([race_id])
    
    print(f"✓ {output_path} に保存しました ({len(race_ids):,}件)")


def save_as_text(race_ids: List[str], output_path: str):
    """
    テキスト形式で保存（1行1ID）
    
    Parameters
    ----------
    race_ids : List[str]
        レースIDのリスト
    output_path : str
        出力ファイルパス
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for race_id in race_ids:
            f.write(race_id + '\n')
    
    print(f"✓ {output_path} に保存しました ({len(race_ids):,}件)")


def print_summary(race_ids: List[str], generator: NetkeibaRaceIDGenerator):
    """サマリー情報を表示"""
    from collections import Counter
    
    print("\n" + "=" * 70)
    print("生成結果サマリー")
    print("=" * 70)
    print(f"総レースID数: {len(race_ids):,}件")
    print()
    
    # 競馬場別集計
    places = [generator.parse_race_id(rid)['place_code'] for rid in race_ids]
    place_counter = Counter(places)
    
    print("競馬場別レース数:")
    for place_code, count in sorted(place_counter.items()):
        place_name = generator.PLACE_NAMES.get(place_code, '不明')
        print(f"  {place_name:4s} ({place_code:02d}): {count:4d}レース ({count//12:2d}日間)")
    
    print("=" * 70)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='NetkeibaのレースIDを生成します',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # JSONファイルから生成（標準出力）
  python generate_race_ids.py schedule.json

  # JSONファイルに出力
  python generate_race_ids.py schedule.json --output race_ids.json

  # CSV形式で出力
  python generate_race_ids.py schedule.json --output race_ids.csv --format csv

  # テキスト形式で出力（1行1ID）
  python generate_race_ids.py schedule.json --output race_ids.txt --format text

  # 詳細情報付きで出力
  python generate_race_ids.py schedule.json --output race_ids.json --detailed

スケジュールJSONフォーマット:
  {
    "year": 2024,
    "schedule": {
      "5": {
        "1": [1, 2, 3, 4],
        "2": [1, 2, 3, 4, 5, 6]
      },
      "6": {
        "1": [1, 2, 3, 4, 5]
      }
    }
  }

または、スケジュールのみ:
  {
    "5": {
      "1": [1, 2, 3, 4]
    }
  }
        """
    )
    
    parser.add_argument('input', help='スケジュールJSONファイルのパス')
    parser.add_argument('-o', '--output', help='出力ファイルパス（指定しない場合は標準出力）')
    parser.add_argument('-f', '--format', 
                       choices=['json', 'csv', 'text'], 
                       default='json',
                       help='出力フォーマット (default: json)')
    parser.add_argument('-d', '--detailed', 
                       action='store_true',
                       help='詳細情報を含める（JSON/CSV形式のみ）')
    parser.add_argument('-y', '--year', 
                       type=int,
                       help='年を指定（JSONに含まれていない場合）')
    parser.add_argument('-s', '--summary', 
                       action='store_true',
                       help='サマリー情報を表示')
    parser.add_argument('--no-summary',
                       action='store_true',
                       help='サマリー情報を非表示')
    
    args = parser.parse_args()
    
    # スケジュールの読み込み
    data = load_schedule(args.input)
    
    # 年の決定
    if 'year' in data:
        year = data['year']
    elif args.year:
        year = args.year
    else:
        print("エラー: 年が指定されていません。JSONに'year'を含めるか、--yearオプションで指定してください", 
              file=sys.stderr)
        sys.exit(1)
    
    schedule = data.get('schedule', data)
    
    # レースID生成
    generator = NetkeibaRaceIDGenerator(year)
    race_ids = generator.generate_from_schedule(schedule)
    
    # 出力
    if args.output:
        output_path = args.output
        
        if args.format == 'json':
            save_as_json(race_ids, output_path, args.detailed, generator)
        elif args.format == 'csv':
            save_as_csv(race_ids, output_path, args.detailed, generator)
        elif args.format == 'text':
            save_as_text(race_ids, output_path)
        
        # サマリー表示
        if args.summary or (not args.no_summary and not args.output):
            print_summary(race_ids, generator)
            
    else:
        # 標準出力
        if args.format == 'json':
            output_data = {'count': len(race_ids), 'race_ids': race_ids}
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
        else:
            for race_id in race_ids:
                print(race_id)


if __name__ == "__main__":
    main()
