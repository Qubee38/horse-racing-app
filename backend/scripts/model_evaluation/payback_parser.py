# backend/scripts/model_evaluation/payback_parser.py

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PaybackInfo:
    """払い戻し情報"""
    race_id: str
    win: Optional[Tuple[str, int]] = None  # (馬番, 配当)
    place: Optional[List[Tuple[str, int]]] = None  # [(馬番, 配当), ...]
    
    def __post_init__(self):
        """初期化後処理"""
        if self.place is None:
            self.place = []


class PaybackParser:
    """払い戻し情報の年別CSV管理クラス"""
    
    def __init__(self, payback_dir: Path):
        """
        Parameters
        ----------
        payback_dir : Path
            払い戻し情報ディレクトリ（年別CSV配置場所）
        """
        self.payback_dir = Path(payback_dir)
        self.payback_dir.mkdir(parents=True, exist_ok=True)
        
        # メモリキャッシュ（年別）
        self._cache: Dict[int, Dict[str, PaybackInfo]] = {}
    
    def get_csv_path(self, year: int) -> Path:
        """年別CSVのパスを取得"""
        return self.payback_dir / f"payback_{year}.csv"
    
    def load_year_data(self, year: int, force_reload: bool = False) -> Dict[str, PaybackInfo]:
        """
        指定年の払い戻し情報を読み込み
        
        Parameters
        ----------
        year : int
            対象年
        force_reload : bool
            キャッシュを無視して再読み込み
        
        Returns
        -------
        Dict[str, PaybackInfo]
            レースID -> PaybackInfo のマップ
        """
        # キャッシュチェック
        if not force_reload and year in self._cache:
            logger.debug(f"Using cached data for year {year}")
            return self._cache[year]
        
        csv_path = self.get_csv_path(year)
        
        if not csv_path.exists():
            logger.info(f"Payback CSV not found for year {year}: {csv_path}")
            self._cache[year] = {}
            return {}
        
        # CSV読み込み
        payback_data = {}
        
        try:
            # 複数のエンコーディングを試行
            encodings = ['utf-8', 'shift-jis', 'cp932', 'euc-jp']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(csv_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                logger.error(f"Failed to decode CSV with any encoding: {csv_path}")
                return {}
            
            logger.debug(f"Successfully read CSV with encoding: {used_encoding}")
            
            # StringIOでDictReaderを使用
            from io import StringIO
            f = StringIO(content)
            reader = csv.DictReader(f)
            
            for row in reader:
                race_id = row.get('レースID') or row.get('race_id')
                payback_str = row.get('払戻情報') or row.get('payback_info')
                
                if not race_id or not payback_str:
                    continue
                
                # 払い戻し情報をパース
                payback_info = self._parse_payback_string(race_id, payback_str)
                payback_data[race_id] = payback_info
            
            logger.info(f"Loaded {len(payback_data)} payback records from {csv_path}")
            
        except Exception as e:
            logger.error(f"Error loading payback CSV {csv_path}: {e}")
            payback_data = {}
        
        # キャッシュに保存
        self._cache[year] = payback_data
        
        return payback_data
    
    def _parse_payback_string(self, race_id: str, payback_str: str) -> PaybackInfo:
        """
        払い戻し文字列をパース
        
        Parameters
        ----------
        race_id : str
            レースID
        payback_str : str
            払い戻し情報の文字列（JSON形式）
            例: "[['7', '760'], ['7', '330', '4', '340', '10', '1370'], ...]"
        
        Returns
        -------
        PaybackInfo
            パース結果
        """
        payback_info = PaybackInfo(race_id=race_id)
        
        try:
            # 🔧 修正: シングルクォートをダブルクォートに置換
            # Pythonのリスト表記 → JSON形式に変換
            payback_str_json = payback_str.replace("'", '"')
            
            # JSON文字列をパース
            data = json.loads(payback_str_json)
            
            if not isinstance(data, list) or len(data) == 0:
                return payback_info
            
            # 単勝（最初の要素）
            if len(data) >= 1 and isinstance(data[0], list) and len(data[0]) >= 2:
                horse_num = str(data[0][0])
                payout = self._parse_payout_amount(data[0][1])
                if payout is not None:
                    payback_info.win = (horse_num, payout)
            
            # 複勝（2番目の要素）
            if len(data) >= 2 and isinstance(data[1], list):
                place_list = []
                # 複勝は [馬番, 配当, 馬番, 配当, ...] の形式
                for i in range(0, len(data[1]), 2):
                    if i + 1 < len(data[1]):
                        horse_num = str(data[1][i])
                        payout = self._parse_payout_amount(data[1][i + 1])
                        if payout is not None:
                            place_list.append((horse_num, payout))
                
                payback_info.place = place_list
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error for race {race_id}: {e}")
            logger.debug(f"  Original string: {payback_str}")
        except Exception as e:
            logger.warning(f"Error parsing payback string for race {race_id}: {e}")
        
        return payback_info
    
    def _parse_payout_amount(self, amount_str: str) -> Optional[int]:
        """
        配当額文字列を整数に変換
        
        Parameters
        ----------
        amount_str : str
            配当額文字列（例: "760", "1,370"）
        
        Returns
        -------
        Optional[int]
            配当額（円）、変換失敗時はNone
        """
        try:
            # カンマを削除して整数に変換
            amount = int(str(amount_str).replace(',', '').replace('円', ''))
            return amount
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse payout amount: {amount_str}")
            return None
    
    def get_payback_info(self, race_id: str) -> Optional[PaybackInfo]:
        """
        指定レースの払い戻し情報を取得
        
        Parameters
        ----------
        race_id : str
            レースID（12桁）
        
        Returns
        -------
        Optional[PaybackInfo]
            払い戻し情報、存在しない場合はNone
        """
        if len(race_id) != 12:
            logger.warning(f"Invalid race ID format: {race_id}")
            return None
        
        # 年を抽出
        year = int(race_id[:4])
        
        # 年別データを読み込み
        year_data = self.load_year_data(year)
        
        return year_data.get(race_id)
    
    def get_missing_race_ids(self, required_race_ids: List[str]) -> List[str]:
        """
        払い戻し情報が不足しているレースIDを検出
        
        Parameters
        ----------
        required_race_ids : List[str]
            必要なレースIDのリスト
        
        Returns
        -------
        List[str]
            払い戻し情報が存在しないレースIDのリスト
        """
        missing = []
        
        # 年別にグループ化
        by_year: Dict[int, List[str]] = {}
        for race_id in required_race_ids:
            if len(race_id) != 12:
                continue
            year = int(race_id[:4])
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(race_id)
        
        # 年別に確認
        for year, race_ids in by_year.items():
            year_data = self.load_year_data(year)
            for race_id in race_ids:
                if race_id not in year_data:
                    missing.append(race_id)
        
        return missing
        
    def save_payback_info(self, payback_info: PaybackInfo):
        """
        払い戻し情報を年別CSVに保存（追記）
        
        Parameters
        ----------
        payback_info : PaybackInfo
            保存する払い戻し情報
        """
        race_id = payback_info.race_id
        if len(race_id) != 12:
            logger.warning(f"Invalid race ID format: {race_id}")
            return
        
        year = int(race_id[:4])

        # 🔧 重複チェック: 既存データを確認
        existing_info = self.get_payback_info(race_id)
        if existing_info:
            logger.debug(f"Race {race_id} already exists, skipping")
            return        
        
        csv_path = self.get_csv_path(year)
        
        # 🔧 修正: 既存データを読み込まず、単純に追記
        try:
            # ファイルが存在しない場合はヘッダーを書き込み
            file_exists = csv_path.exists()
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # ヘッダー（ファイルが新規の場合のみ）
                if not file_exists:
                    writer.writerow(['レースID', '払戻情報'])
                
                # データ行を追記
                payback_str = self._format_payback_info(payback_info)
                writer.writerow([race_id, payback_str])
            
            logger.debug(f"Appended payback info for race {race_id} to {csv_path}")
            
            # 🔧 修正: キャッシュも更新（追記のみ）
            if year in self._cache:
                self._cache[year][race_id] = payback_info
            
        except Exception as e:
            logger.error(f"Error appending payback info to {csv_path}: {e}")


    def save_batch_payback_info(self, payback_infos: List[PaybackInfo]):
        """
        複数の払い戻し情報をバッチ保存（追記）
        
        Parameters
        ----------
        payback_infos : List[PaybackInfo]
            保存する払い戻し情報のリスト
        """
        if not payback_infos:
            return
        
        # 年別にグループ化
        by_year: Dict[int, List[PaybackInfo]] = {}
        for info in payback_infos:
            if len(info.race_id) != 12:
                continue
            year = int(info.race_id[:4])
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(info)
        
        # 🔧 修正: 年別に追記
        for year, infos in by_year.items():
            csv_path = self.get_csv_path(year)
            
            try:
                # ファイルが存在しない場合はヘッダーを書き込み
                file_exists = csv_path.exists()
                
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # ヘッダー（ファイルが新規の場合のみ）
                    if not file_exists:
                        writer.writerow(['レースID', '払戻情報'])
                    
                    # データ行を追記
                    for info in infos:
                        payback_str = self._format_payback_info(info)
                        writer.writerow([info.race_id, payback_str])
                
                logger.info(f"Appended {len(infos)} payback records for year {year}")
                
                # 🔧 修正: キャッシュも更新（追記のみ）
                if year in self._cache:
                    for info in infos:
                        self._cache[year][info.race_id] = info
            
            except Exception as e:
                logger.error(f"Error appending payback batch to {csv_path}: {e}")
    
    def _format_payback_info(self, payback_info: PaybackInfo) -> str:
        """
        PaybackInfoをJSON文字列に変換
        
        Parameters
        ----------
        payback_info : PaybackInfo
            払い戻し情報
        
        Returns
        -------
        str
            JSON文字列
        """
        data = []
        
        # 単勝
        if payback_info.win:
            horse_num, payout = payback_info.win
            data.append([horse_num, str(payout)])
        else:
            data.append([])
        
        # 複勝
        if payback_info.place:
            place_flat = []
            for horse_num, payout in payback_info.place:
                place_flat.append(horse_num)
                place_flat.append(str(payout))
            data.append(place_flat)
        else:
            data.append([])
        
        return json.dumps(data, ensure_ascii=False)
    
    def get_statistics(self, year: int) -> Dict:
        """
        指定年の統計情報を取得
        
        Parameters
        ----------
        year : int
            対象年
        
        Returns
        -------
        Dict
            統計情報
        """
        year_data = self.load_year_data(year)
        
        total_races = len(year_data)
        races_with_win = sum(1 for info in year_data.values() if info.win is not None)
        races_with_place = sum(1 for info in year_data.values() if info.place)
        
        return {
            'year': year,
            'total_races': total_races,
            'races_with_win': races_with_win,
            'races_with_place': races_with_place
        }
    
    def clear_cache(self):
        """メモリキャッシュをクリア"""
        self._cache.clear()
        logger.debug("Cleared payback cache")


# ========================================
# テスト用コード
# ========================================
if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # テスト実行
    from pathlib import Path
    
    # テスト用ディレクトリ
    test_dir = Path(__file__).parent.parent.parent / "data" / "payback"
    
    parser = PaybackParser(test_dir)
    
    # 2025年のデータを読み込み
    year_data = parser.load_year_data(2025)
    print(f"\nLoaded {len(year_data)} races for 2025")
    
    # 統計情報
    stats = parser.get_statistics(2025)
    print(f"\nStatistics for 2025:")
    print(f"  Total races: {stats['total_races']}")
    print(f"  Races with win: {stats['races_with_win']}")
    print(f"  Races with place: {stats['races_with_place']}")
    
    # サンプルデータを取得
    if year_data:
        sample_race_id = list(year_data.keys())[0]
        sample_info = parser.get_payback_info(sample_race_id)
        
        print(f"\nSample payback info for race {sample_race_id}:")
        print(f"  Win: {sample_info.win}")
        print(f"  Place: {sample_info.place}")
    
    # 不足レースIDのテスト
    test_race_ids = ["202505010101", "202505010102", "202505010199"]
    missing = parser.get_missing_race_ids(test_race_ids)
    print(f"\nMissing race IDs: {missing}")