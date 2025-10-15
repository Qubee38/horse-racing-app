# backend/scripts/model_evaluation/data_loader.py

import os
import csv
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd
import sys

# 既存モジュールをインポート
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.ml.predictor import predictor
from app.ml.scraper_integration import scraper

# 評価用モジュールをインポート
from .config import EvaluationConfig
from .payback_parser import PaybackParser, PaybackInfo
from .payback_scraper import PaybackScraper

logger = logging.getLogger(__name__)


@dataclass
class RaceData:
    """単一レースのデータと予測結果"""
    race_id: str
    race_info: Dict
    predictions_df: pd.DataFrame  # 予測結果をDataFrame化
    payback_info: Optional[PaybackInfo] = None
    csv_path: Optional[str] = None


class DataLoader:
    """
    データ準備・予測実行クラス
    
    Phase 0: データ準備（スクレイピング・払い戻し取得）
    Phase 1: データ読み込み・予測実行
    """
    
    def __init__(self, config: EvaluationConfig):
        """
        Parameters
        ----------
        config : EvaluationConfig
            評価設定
        """
        self.config = config
        self.predictor = predictor
        self.payback_parser = PaybackParser(config.PAYBACK_DIR)
        self.payback_scraper = PaybackScraper(delay=config.DELAY_BETWEEN_REQUESTS)
        
        # モデル読み込み
        if not self.predictor.is_loaded:
            logger.info("Loading prediction models...")
            self.predictor.load_models()
    
    # ========================================
    # Phase 0: データ準備
    # ========================================
    
    def prepare_evaluation_data(
        self,
        race_ids: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """
        評価に必要なデータを準備
        
        Parameters
        ----------
        race_ids : List[str]
            評価対象のレースIDリスト
        progress_callback : Optional[callable]
            進捗報告用コールバック(current, total, message)
        
        Returns
        -------
        List[str]
            準備完了したレースIDのリスト（失敗分は除外）
        """
        logger.info(f"=== Phase 0: Data Preparation ===")
        logger.info(f"Total races to prepare: {len(race_ids)}")
        
        # Step 1: レースデータの準備
        valid_race_ids = self._prepare_race_data(race_ids, progress_callback)
        
        # Step 2: 払い戻し情報の準備
        if self.config.SCRAPE_MISSING_PAYBACK:
            self._prepare_payback_data(valid_race_ids, progress_callback)
        
        logger.info(f"Phase 0 completed: {len(valid_race_ids)}/{len(race_ids)} races ready")
        
        return valid_race_ids
    
    def _prepare_race_data(
        self,
        race_ids: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """レースデータの準備（スクレイピング）"""
        logger.info("Step 1: Preparing race data...")
        
        valid_race_ids = []
        total = len(race_ids)
        
        for i, race_id in enumerate(race_ids, 1):
            # 進捗報告
            if progress_callback:
                progress_callback(i, total, f"Checking race data: {race_id}")
            
            # 既存データの確認
            csv_path = self.config.RACE_INPUT_DIR / f"race_data_{race_id}.csv"
            
            if csv_path.exists() and self.config.USE_EXISTING_DATA and not self.config.FORCE_RESCRAPE:
                logger.info(f"[{i}/{total}] Using existing data: {race_id}")
                valid_race_ids.append(race_id)
                continue
            
            # スクレイピング（scraperが自動でCSV保存する）
            logger.info(f"[{i}/{total}] Scraping race data: {race_id}")
            
            try:
                # scraper_integration を直接使用してスクレイピングのみ実行
                from app.ml.scraper_integration import scraper
                
                scraping_result = scraper.scrape_race_data(race_id)
                
                if scraping_result and scraping_result.get('csv_path'):
                    valid_race_ids.append(race_id)
                    logger.info(f"[{i}/{total}] Success: {race_id}")
                else:
                    logger.warning(f"[{i}/{total}] Failed to scrape: {race_id}")
                
                # Rate limiting
                if i < total:
                    time.sleep(self.config.DELAY_BETWEEN_REQUESTS)
            
            except Exception as e:
                logger.error(f"[{i}/{total}] Error scraping {race_id}: {e}")
                # エラーでもスキップして続行
                continue
        
        logger.info(f"Race data preparation completed: {len(valid_race_ids)}/{total}")
        return valid_race_ids
    
    def _prepare_payback_data(
        self,
        race_ids: List[str],
        progress_callback: Optional[callable] = None
    ) -> None:
        """払い戻し情報の準備（スクレイピング）"""
        logger.info("Step 2: Preparing payback data...")
        
        # 不足分の自動取得
        result = self.payback_scraper.scrape_and_save_missing(
            required_race_ids=race_ids,
            parser=self.payback_parser,
            progress_callback=progress_callback
        )
        
        logger.info(f"Payback data preparation completed:")
        logger.info(f"  Total required: {result['total_required']}")
        logger.info(f"  Already exists: {result['already_exists']}")
        logger.info(f"  Scraped: {result['scraped']}")
        logger.info(f"  Failed: {result['failed']}")
    
    # ========================================
    # Phase 1: データ読み込み・予測実行
    # ========================================
    
    def get_all_race_data(
        self,
        race_ids: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[RaceData]:
        """
        全レースのデータと予測結果を取得
        
        Parameters
        ----------
        race_ids : List[str]
            レースIDリスト
        progress_callback : Optional[callable]
            進捗報告用コールバック
        
        Returns
        -------
        List[RaceData]
            レースデータのリスト
        """
        logger.info(f"=== Phase 1: Data Loading & Prediction ===")
        logger.info(f"Total races to process: {len(race_ids)}")
        
        race_data_list = []
        total = len(race_ids)
        
        for i, race_id in enumerate(race_ids, 1):
            # 進捗報告
            if progress_callback:
                progress_callback(i, total, f"Loading & predicting: {race_id}")
            
            logger.info(f"[{i}/{total}] Processing race {race_id}")
            
            try:
                # レースデータと予測結果を取得
                race_data = self._get_single_race_data(race_id)
                
                if race_data:
                    race_data_list.append(race_data)
                    logger.info(f"[{i}/{total}] Success: {race_id}")
                else:
                    logger.warning(f"[{i}/{total}] No data: {race_id}")
            
            except Exception as e:
                logger.error(f"[{i}/{total}] Error processing {race_id}: {e}")
                # エラーでもスキップして続行
                continue
        
        logger.info(f"Phase 1 completed: {len(race_data_list)}/{total} races loaded")
        
        return race_data_list
    
    def _get_single_race_data(self, race_id: str) -> Optional[RaceData]:
        """
        単一レースのデータと予測結果を取得
        
        Parameters
        ----------
        race_id : str
            レースID
        
        Returns
        -------
        Optional[RaceData]
            レースデータ、取得失敗時はNone
        """
        # Step 1: CSV存在確認
        csv_path = self.config.RACE_INPUT_DIR / f"race_data_{race_id}.csv"
        
        if not csv_path.exists():
            logger.warning(f"CSV not found: {csv_path}")
            return None
        
        # Step 2: CSVからレース情報と馬データを読み込み
        try:
            race_info, horses_data = self._load_race_data_from_csv(csv_path, race_id)
            
            # Step 3: 予測実行（スクレイピングなし）
            predictions = self._predict_from_loaded_data(horses_data, race_info)
            
            if not predictions:
                logger.warning(f"Prediction failed: {race_id}")
                return None
            
            # Step 4: 予測結果をDataFrameに変換
            predictions_df = self._predictions_to_dataframe(predictions, race_info)
            
            # Step 5: 払い戻し情報を取得
            payback_info = self.payback_parser.get_payback_info(race_id)
            
            if not payback_info:
                logger.warning(f"No payback info for race {race_id} - excluding from evaluation")
                return None
            
            # RaceDataオブジェクトを作成
            race_data = RaceData(
                race_id=race_id,
                race_info=race_info,
                predictions_df=predictions_df,
                payback_info=payback_info,
                csv_path=str(csv_path)
            )
            
            return race_data
        
        except Exception as e:
            logger.error(f"Error getting race data for {race_id}: {e}")
            return None
    
    def _load_race_data_from_csv(self, csv_path: Path, race_id: str) -> tuple:
        """
        CSVからレース情報と馬データを読み込み
        
        Parameters
        ----------
        csv_path : Path
            CSVファイルパス
        race_id : str
            レースID
        
        Returns
        -------
        tuple
            (race_info, horses_data)
        """
        df = pd.read_csv(csv_path)
        
        if len(df) == 0:
            raise ValueError(f"Empty CSV: {csv_path}")
        
        # レース情報を抽出（1行目から）
        first_row = df.iloc[0]
        
        race_info = {
            'race_id': race_id,
            'race_name': str(first_row.get('レース名', '')),
            'date': str(first_row.get('日付', '')),
            'distance': str(first_row.get('距離', '1600')),
            'track_type': first_row.get('芝・ダート', 0),
            'location': str(first_row.get('場名', '')),
            'place_id': str(first_row.get('場id', '')),
            'race_rank': first_row.get('クラス', 0),
            'race_meeting': str(first_row.get('開催', '')),
            'mawari': first_row.get('回り', 0),
            'weather': first_row.get('天気', 0),
            'baba': first_row.get('馬場', 0)
        }
        
        # 馬データを抽出（全行から、スクレイピング結果と同じ構造に変換）
        horses_data = []
        for idx, row in df.iterrows():
            # 基本情報（scraper_integration.pyと同じ構造）
            horse_data = {
                # 基本情報
                'horse_name': str(row.get('馬', '')),
                'jockey': str(row.get('騎手', '')),
                'horse_number': str(row.get('馬番', idx + 1)),
                'frame_number': int(row.get('枠番', 1)) if pd.notna(row.get('枠番')) else 1,
                'odds': str(row.get('オッズ', '5.0')),
                'popularity': str(row.get('人気', '')),
                'weight': str(row.get('体重', '')),
                'weight_change': str(row.get('体重変化', '')),
                'handicap': str(row.get('斤量', '')),
                'sex': int(row.get('性', 0)) if pd.notna(row.get('性')) and row.get('性') != '' else 0,
                'age': str(row.get('齢', '')),
                'agari': str(row.get('上がり', '')),
                'running_time': str(row.get('走破時間', '')),
                'through_order': str(row.get('通過順', '')),
                'finish_order': str(row.get('着順', '')),
            }
            
            # 過去5走分のデータを history_results 形式に変換
            history_results = []
            for i in range(1, 6):
                suffix = str(i)
                
                # 少なくとも日付があれば過去戦績として扱う
                date_col = f'日付{suffix}'
                if pd.notna(row.get(date_col)) and str(row.get(date_col)) != '' and str(row.get(date_col)) != 'nan':
                    # feature_engineering.py の _create_past_race_features() が期待する配列形式
                    # [日付, 馬番, 騎手, 斤量, オッズ, 体重, 体重変化, 上がり, 通過順, 着順, 
                    #  距離, クラス, 走破時間, 芝・ダート, 天気, 場id, 馬場, 回り]
                    past_race = [
                        str(row.get(f'日付{suffix}', '')),                         # 0: 日付
                        self._csv_to_int(row.get(f'馬番{suffix}')),                # 1: 馬番
                        str(row.get(f'騎手{suffix}', '')),                         # 2: 騎手
                        self._csv_to_float(row.get(f'斤量{suffix}')),              # 3: 斤量
                        self._csv_to_float(row.get(f'オッズ{suffix}')),            # 4: オッズ
                        self._csv_to_int(row.get(f'体重{suffix}')),                # 5: 体重
                        self._csv_to_int(row.get(f'体重変化{suffix}')),            # 6: 体重変化
                        self._csv_to_float(row.get(f'上がり{suffix}')),            # 7: 上がり
                        self._csv_to_float(row.get(f'通過順{suffix}')),            # 8: 通過順
                        self._csv_to_int(row.get(f'着順{suffix}')),                # 9: 着順
                        self._csv_to_int(row.get(f'距離{suffix}')),                # 10: 距離
                        self._csv_to_int(row.get(f'クラス{suffix}')),              # 11: クラス
                        self._csv_to_float(row.get(f'走破時間{suffix}')),          # 12: 走破時間
                        self._csv_to_int(row.get(f'芝・ダート{suffix}')),          # 13: 芝・ダート
                        self._csv_to_int(row.get(f'天気{suffix}')),                # 14: 天気
                        str(row.get(f'場id{suffix}', '')),                         # 15: 場id
                        self._csv_to_int_or_none(row.get(f'馬場{suffix}')),       # 16: 馬場（Noneを許容）
                        self._csv_to_int(row.get(f'回り{suffix}'))                 # 17: 回り
                    ]
                    history_results.append(past_race)
            
            horse_data['history_results'] = history_results
            horses_data.append(horse_data)
        
        return race_info, horses_data
    
    def _csv_to_int(self, value) -> int:
        """CSV値を整数に変換（空の場合は0）"""
        try:
            if pd.isna(value) or value == '' or value == 'nan':
                return 0
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def _csv_to_int_or_none(self, value):
        """CSV値を整数またはNoneに変換（scraper結果のNoneに対応）"""
        try:
            if pd.isna(value) or value == '' or value == 'nan':
                return None
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _csv_to_float(self, value):
        """CSV値を浮動小数点に変換（空の場合は空文字）"""
        try:
            if pd.isna(value) or value == '' or value == 'nan':
                return ''
            return float(value)
        except (ValueError, TypeError):
            return ''
         
    def _predict_from_loaded_data(self, horses_data: List[Dict], race_info: Dict) -> List[Dict]:
        """
        読み込み済みデータから予測実行（スクレイピングなし）
        
        Parameters
        ----------
        horses_data : List[Dict]
            馬データのリスト
        race_info : Dict
            レース情報
        
        Returns
        -------
        List[Dict]
            予測結果のリスト
        """
        if not self.predictor.is_loaded:
            logger.error("Predictor models not loaded")
            return []
        
        try:
            # predictor内部の予測ロジックを直接使用
            # _predict_with_new_models は既存CSVからの予測に対応している
            predictions = self.predictor._predict_with_new_models(horses_data, race_info)

            # 🔧 修正: 予測結果に馬番などの基本情報を追加
            for i, pred in enumerate(predictions):
                if i < len(horses_data):
                    horse = horses_data[i]
                    # 馬番が含まれていない場合は追加
                    if 'horse_number' not in pred or not pred['horse_number']:
                        pred['horse_number'] = horse.get('horse_number', str(i + 1))
                    # 馬名が含まれていない場合は追加
                    if 'horse_name' not in pred or not pred['horse_name']:
                        pred['horse_name'] = horse.get('horse_name', '')
                    # 騎手が含まれていない場合は追加
                    if 'jockey' not in pred or not pred['jockey']:
                        pred['jockey'] = horse.get('jockey', '')
                    # 枠番が含まれていない場合は追加
                    if 'frame_number' not in pred or not pred['frame_number']:
                        pred['frame_number'] = horse.get('frame_number', 1)
                    # オッズが含まれていない場合は追加
                    if 'odds' not in pred or not pred['odds']:
                        pred['odds'] = horse.get('odds', '5.0')
            
            return predictions
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return []
    
    def _predictions_to_dataframe(
        self,
        predictions: List[Dict],
        race_info: Dict
    ) -> pd.DataFrame:
        """
        予測結果リストをDataFrameに変換
        
        Parameters
        ----------
        predictions : List[Dict]
            予測結果のリスト
        race_info : Dict
            レース情報
        
        Returns
        -------
        pd.DataFrame
            予測結果DataFrame
        """
        # 予測結果をDataFrameに変換
        df = pd.DataFrame(predictions)
        
        # レース情報を追加
        for key in ['race_id', 'race_name', 'distance', 'track_type', 'location', 'race_rank']:
            if key in race_info:
                df[key] = race_info[key]
        
        # カラム名を日本語に変換（既存コードとの互換性）
        column_mapping = {
            'horse_name': '馬',
            'jockey': '騎手',
            'horse_number': '馬番',
            'frame_number': '枠番',
            'odds': 'オッズ',
            'win_probability': '1着確率',
            'place_probability': '3着以内確率',
            'expected_value': '期待値',
            'confidence_score': '信頼度',
            'distance': '距離',
            'track_type': '芝ダート',
            'location': '競馬場',
            'race_rank': 'グレード'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 必須カラムの確認
        required_columns = ['馬', '馬番', '1着確率', '3着以内確率', 'オッズ']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Missing required column: {col}")
                df[col] = 0 if col in ['1着確率', '3着以内確率'] else ''
        
        return df
    
    # ========================================
    # ユーティリティメソッド
    # ========================================
    
    def get_statistics(self, race_data_list: List[RaceData]) -> Dict:
        """
        データロードの統計情報を取得
        
        Parameters
        ----------
        race_data_list : List[RaceData]
            レースデータのリスト
        
        Returns
        -------
        Dict
            統計情報
        """
        total_races = len(race_data_list)
        total_horses = sum(len(race.predictions_df) for race in race_data_list)
        
        races_with_payback = sum(1 for race in race_data_list if race.payback_info is not None)
        
        return {
            'total_races': total_races,
            'total_horses': total_horses,
            'races_with_payback': races_with_payback,
            'average_horses_per_race': total_horses / total_races if total_races > 0 else 0
        }


# ========================================
# テスト用コード
# ========================================
if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 設定初期化
    config = EvaluationConfig()
    config.ensure_directories()
    
    # DataLoader初期化
    loader = DataLoader(config)
    
    # テスト用レースID
    test_race_ids = [
        "202506040911",  # スプリンターズS
    ]
    
    # Phase 0: データ準備
    print("\n=== Phase 0: Data Preparation ===")
    valid_race_ids = loader.prepare_evaluation_data(test_race_ids)
    print(f"Valid race IDs: {valid_race_ids}")
    
    # Phase 1: データ読み込み・予測実行
    print("\n=== Phase 1: Data Loading & Prediction ===")
    race_data_list = loader.get_all_race_data(valid_race_ids)
    
    # 結果表示
    print(f"\n=== Results ===")
    print(f"Total races loaded: {len(race_data_list)}")
    
    if race_data_list:
        sample_race = race_data_list[0]
        print(f"\nSample race: {sample_race.race_id}")
        print(f"  Race name: {sample_race.race_info.get('race_name')}")
        print(f"  Horses: {len(sample_race.predictions_df)}")
        print(f"  Payback: {sample_race.payback_info.win if sample_race.payback_info else 'N/A'}")
        print(f"\nPredictions DataFrame:")
        print(sample_race.predictions_df[['馬', '馬番', '1着確率', '3着以内確率', 'オッズ']].head())
    
    # 統計情報
    stats = loader.get_statistics(race_data_list)
    print(f"\n=== Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")