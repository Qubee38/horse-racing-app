import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FeatureEngineering:
    """競馬予測用特徴量エンジニアリング（130→101特徴量対応）"""
    
    def __init__(self):
        self.reference_path = self._get_reference_root()
        self.jockey_win_rate_df = None
        self.time_data = None
        self._load_reference_data()
        
        # 130個の全特徴量リスト（特徴量Sheet1.csvと同じ順序）
        self.all_features = [
            'race_id', '馬', '騎手', '馬番', '走破時間', 'オッズ', '通過順', '着順', 
            '体重', '体重変化', '性', '齢', '斤量', '上がり', '人気', 'レース名', 
            '日付', '開催', 'クラス', '芝・ダート', '距離', '回り', '馬場', '天気', 
            '場id', '場名', '日付1', '馬番1', '騎手1', '斤量1', 'オッズ1', '体重1', 
            '体重変化1', '上がり1', '通過順1', '着順1', '距離1', 'クラス1', '走破時間1', 
            '芝・ダート1', '天気1', '場id1', '馬場1', '回り1', '日付2', '馬番2', 
            '騎手2', '斤量2', 'オッズ2', '体重2', '体重変化2', '上がり2', '通過順2', 
            '着順2', '距離2', 'クラス2', '走破時間2', '芝・ダート2', '天気2', '場id2', 
            '馬場2', '回り2', '日付3', '馬番3', '騎手3', '斤量3', 'オッズ3', '体重3', 
            '体重変化3', '上がり3', '通過順3', '着順3', '距離3', 'クラス3', '走破時間3', 
            '芝・ダート3', '天気3', '場id3', '馬場3', '回り3', '日付4', '馬番4', 
            '騎手4', '斤量4', 'オッズ4', '体重4', '体重変化4', '上がり4', '通過順4', 
            '着順4', '距離4', 'クラス4', '走破時間4', '芝・ダート4', '天気4', '場id4', 
            '馬場4', '回り4', '日付5', '馬番5', '騎手5', '斤量5', 'オッズ5', '体重5', 
            '体重変化5', '上がり5', '通過順5', '着順5', '距離5', 'クラス5', '走破時間5', 
            '芝・ダート5', '天気5', '場id5', '馬場5', '回り5', '距離差', '日付差', 
            '距離差1', '日付差1', '距離差2', '日付差2', '距離差3', '日付差3', 
            '距離差4', '日付差4', '平均斤量'
        ]

        self.jockey_features = [
            '騎手', '勝率', '連対率', '複勝率'
        ]
        
        # 削除対象列（prediction.pyと同じ）
        self.drop_columns = [
            # 基本情報（削除対象）
            '馬', '騎手', 'レース名', '場名', '開催', '日付', 'race_id', 
            '体重', '体重変化',
            
            # 予測時に存在しないデータ（削除対象）
            '走破時間', 'オッズ', '通過順', '着順', '上がり', '人気',
            
            # 過去戦績の日付・騎手（削除対象）
            '日付1', '日付2', '日付3', '日付4', '日付5',
            '騎手1', '騎手2', '騎手3', '騎手4', '騎手5',
            
            # 過去戦績の場id・回り（削除対象）
            '場id1', '場id2', '場id3', '場id4', '場id5',
            '回り1', '回り2', '回り3', '回り4', '回り5'
        ]
        
        logger.info(f"FeatureEngineering initialized: {len(self.all_features)} features → {len(self.all_features) - len(self.drop_columns)} model input features")
    
    def _get_reference_root(self) -> str:
        """参照データのパスを取得"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        return os.path.join(project_root, "data", "reference")
    
    def _load_reference_data(self):
        """参照用データを読み込み"""
        try:
            # 騎手勝率データ読み込み
            jockey_path = os.path.join(self.reference_path, "jockey_win_rate.csv")
            if os.path.exists(jockey_path):
                self.jockey_win_rate_df = pd.read_csv(jockey_path)
                logger.info(f"Loaded jockey win rate data: {len(self.jockey_win_rate_df)} records")
            else:
                logger.warning(f"Jockey win rate file not found: {jockey_path}")
                self.jockey_win_rate_df = pd.DataFrame(columns=self.jockey_features)
            
            # タイム標準化データ読み込み
            time_path = os.path.join(self.reference_path, "standard_deviation.csv")
            if os.path.exists(time_path):
                time_df = pd.read_csv(time_path, index_col=0)
                self.time_data = (
                    time_df['Mean']['First Time'], time_df['Mean']['Second Time'],
                    time_df['Standard Deviation']['First Time'], time_df['Standard Deviation']['Second Time']
                )
                logger.info("Loaded time standardization data")
            else:
                logger.warning(f"Time standardization file not found: {time_path}")
                self.time_data = (120.0, 0.0, 10.0, 1.0)
                
        except Exception as e:
            logger.error(f"Failed to load reference data: {e}")
            self.jockey_win_rate_df = pd.DataFrame(columns=self.jockey_features)
            self.time_data = (120.0, 0.0, 10.0, 1.0)
    
    def create_features_from_scraping_data(self, horses_data: List[Dict], race_info: Dict) -> pd.DataFrame:
        """
        スクレイピングデータから130特徴量を作成
        
        Args:
            horses_data: 出走馬データリスト
            race_info: レース情報
            
        Returns:
            pd.DataFrame: 130特徴量データフレーム
        """
        try:
            logger.info(f"Creating 130 features for {len(horses_data)} horses")
            
            all_features_data = []
            
            for horse in horses_data:
                # 各馬の130特徴量を作成
                horse_features = self._create_horse_features(horse, race_info)
                all_features_data.append(horse_features)
            
            # DataFrameに変換
            df = pd.DataFrame(all_features_data, columns=self.all_features)
            
            # 騎手勝率データと結合
            df = self._merge_jockey_win_rates(df)
            
            # 派生特徴量計算
            df = self._calculate_derived_features(df)
            
            logger.info(f"Created feature matrix: {df.shape[0]} horses × {df.shape[1]} features")
            return df
            
        except Exception as e:
            logger.error(f"Feature creation failed: {e}")
            raise
            
        except Exception as e:
            logger.error(f"Feature creation failed: {e}")
            raise
    
    def _create_horse_features(self, horse: Dict, race_info: Dict) -> Dict:
        """単一馬の130特徴量を作成"""
        features = {}
        
        # 基本レース情報（26特徴量）
        features.update(self._create_current_race_features(horse, race_info))
        
        # 過去戦績データ（5走分 × 18特徴量 = 90特徴量）
        features.update(self._create_past_race_features(horse))
        
        # 派生特徴量（日付差・距離差など 11特徴量）- 初期値設定のみ
        features.update(self._initialize_derived_features())
        
        # 騎手勝率（3特徴量）- 初期値設定のみ（後で結合）
        # features.update(self._initialize_jockey_features())
        
        return features
    
    def _create_current_race_features(self, horse: Dict, race_info: Dict) -> Dict:
        """現在レースの基本特徴量（26個）"""
        features = {
            # レース識別・基本情報
            'race_id': race_info.get('race_id', ''),
            '馬': horse.get('horse_name', ''),
            '騎手': horse.get('jockey', ''),
            'レース名': race_info.get('race_name', ''),
            '日付': race_info.get('date', ''),
            '開催': race_info.get('race_meeting', ''),
            '場名': race_info.get('location', ''),
            
            # 馬基本情報
            '馬番': self._safe_int(horse.get('horse_number')),
            'オッズ': horse.get('odds', ''),
            '人気': horse.get('popularity', ''),
            '体重': self._safe_int(horse.get('weight')),
            '体重変化': self._safe_int(horse.get('weight_change')),
            '性': self._safe_int(horse.get('sex')),
            '齢': self._safe_int(horse.get('age')),
            '斤量': self._safe_float(horse.get('handicap')),
            
            # レース条件
            'クラス': race_info.get('race_rank', ''),
            '芝・ダート': race_info.get('track_type', ''),
            '距離': self._safe_int(race_info.get('distance')),
            '回り': race_info.get('mawari', ''),
            '馬場': race_info.get('baba', ''),
            '天気': race_info.get('weather', ''),
            '場id': race_info.get('place_id', ''),
            
            # 現在レースの実績（予測時は空）
            '走破時間': '',
            '通過順': '',
            '着順': '',
            '上がり': ''
        }
        
        return features
    
    def _create_past_race_features(self, horse: Dict) -> Dict:
        """過去戦績特徴量（5走分 × 18特徴量 = 90個）"""
        features = {}
        
        # 過去戦績データを取得
        past_results = horse.get('history_results', [])
        
        for i in range(1, 6):  # 1走前〜5走前
            suffix = str(i)
            
            if i <= len(past_results):
                # 過去戦績データが存在する場合
                past_race = past_results[i-1]
                
                features[f'日付{suffix}'] = past_race[0] if len(past_race) > 0 else ''
                features[f'馬番{suffix}'] = self._safe_int(past_race[1]) if len(past_race) > 1 else ''
                features[f'騎手{suffix}'] = past_race[2] if len(past_race) > 2 else ''
                features[f'斤量{suffix}'] = self._safe_float(past_race[3]) if len(past_race) > 3 else ''
                features[f'オッズ{suffix}'] = self._safe_float(past_race[4]) if len(past_race) > 4 else ''
                features[f'体重{suffix}'] = self._safe_int(past_race[5]) if len(past_race) > 5 else ''
                features[f'体重変化{suffix}'] = self._safe_int(past_race[6]) if len(past_race) > 6 else ''
                features[f'上がり{suffix}'] = self._safe_float(past_race[7]) if len(past_race) > 7 else ''
                features[f'通過順{suffix}'] = self._safe_float(past_race[8]) if len(past_race) > 8 else ''
                features[f'着順{suffix}'] = self._safe_int(past_race[9]) if len(past_race) > 9 else ''
                features[f'距離{suffix}'] = self._safe_int(past_race[10]) if len(past_race) > 10 else ''
                features[f'クラス{suffix}'] = self._safe_int(past_race[11]) if len(past_race) > 11 else ''
                features[f'走破時間{suffix}'] = self._safe_float(past_race[12]) if len(past_race) > 12 else ''
                features[f'芝・ダート{suffix}'] = self._safe_int(past_race[13]) if len(past_race) > 13 else ''
                features[f'天気{suffix}'] = self._safe_int(past_race[14]) if len(past_race) > 14 else ''
                features[f'場id{suffix}'] = past_race[15] if len(past_race) > 15 else ''
                features[f'馬場{suffix}'] = self._safe_int(past_race[16]) if len(past_race) > 16 else ''
                features[f'回り{suffix}'] = self._safe_int(past_race[17]) if len(past_race) > 17 else ''
                
            else:
                # 過去戦績データが不足している場合は空文字
                for feature_name in ['日付', '馬番', '騎手', '斤量', 'オッズ', '体重', '体重変化', 
                                    '上がり', '通過順', '着順', '距離', 'クラス', '走破時間', 
                                    '芝・ダート', '天気', '場id', '馬場', '回り']:
                    features[f'{feature_name}{suffix}'] = ''
        
        return features
    
    def _initialize_derived_features(self) -> Dict:
        """派生特徴量の初期化（11個）"""
        return {
            '距離差': '',
            '日付差': '',
            '距離差1': '',
            '日付差1': '',
            '距離差2': '',
            '日付差2': '',
            '距離差3': '',
            '日付差3': '',
            '距離差4': '',
            '日付差4': '',
            '平均斤量': ''
        }
    
    def _initialize_jockey_features(self) -> Dict:
        """騎手特徴量の初期化（3個）"""
        return {
            '勝率': '',
            '連対率': '',
            '複勝率': ''
        }
    
    def _merge_jockey_win_rates(self, df: pd.DataFrame) -> pd.DataFrame:
        """騎手勝率データと結合"""
        try:
            if self.jockey_win_rate_df is not None and not self.jockey_win_rate_df.empty:
                # 騎手名の表記ゆれ対策を適用
                df_cleaned = df.copy()
                df_cleaned = self._apply_jockey_name_standardization(df_cleaned)
                
                # 騎手勝率データと結合
                merged_df = df_cleaned.merge(
                    self.jockey_win_rate_df[self.jockey_features], 
                    on='騎手', 
                    how='left'
                )
                # 結合されなかった騎手のデフォルト値設定
                merged_df['勝率'] = merged_df['勝率'].fillna('')
                merged_df['連対率'] = merged_df['連対率'].fillna('')
                merged_df['複勝率'] = merged_df['複勝率'].fillna('')
                
                logger.info("Jockey win rate data merged successfully")
                return merged_df
            else:
                logger.warning("No jockey win rate data available")
                return df
                
        except Exception as e:
            logger.error(f"Jockey win rate merge failed: {e}")
            return df
    
    def _apply_jockey_name_standardization(self, df: pd.DataFrame) -> pd.DataFrame:
        """騎手名の表記ゆれ対策（scraper_integration.pyと同じロジック）"""
        df = df.replace({
                "ムルザバエフ": "ムルザバ",
                "永島まなみ": "永島まな",
                "河原田菜々": "河原田菜",
                "デムーロ": "Ｍ．デム",
                "秋山真一郎": "秋山真一",
                "マーカンド": "マーカン",
                "佐々木大輔": "佐々木大",
                "石川裕紀人": "石川裕紀",
                "ビュイック": "ビュイッ",
                "ルメートル": "ルメート",
                "野中悠太郎": "野中悠太",
                "武士沢友治": "武士沢友",
                "シュタルケ": "シュタル",
                "柴田裕一郎": "柴田裕一",
                "五十嵐雄祐": "五十嵐雄",
                "小野寺祐太": "小野寺祐",
                "吉村誠之助": "吉村誠之",
                "小牧加矢太": "小牧加矢",	
        })
        return df
    
    def _calculate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """派生特徴量計算（距離差、日付差、平均斤量など）"""
        try:
            # 数値変換
            for col in ['斤量', '斤量1', '斤量2', '斤量3', '斤量4', '斤量5']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 平均斤量計算
            kinryo_columns = ['斤量', '斤量1', '斤量2', '斤量3', '斤量4', '斤量5']
            df['平均斤量'] = df[kinryo_columns].mean(axis=1, skipna=True)
            
            # 距離差計算
            df["距離差"] = pd.to_numeric(df["距離"], errors='coerce') - pd.to_numeric(df["距離1"], errors='coerce')
            df["距離差1"] = pd.to_numeric(df["距離1"], errors='coerce') - pd.to_numeric(df["距離2"], errors='coerce')
            df["距離差2"] = pd.to_numeric(df["距離2"], errors='coerce') - pd.to_numeric(df["距離3"], errors='coerce')
            df["距離差3"] = pd.to_numeric(df["距離3"], errors='coerce') - pd.to_numeric(df["距離4"], errors='coerce')
            df["距離差4"] = pd.to_numeric(df["距離4"], errors='coerce') - pd.to_numeric(df["距離5"], errors='coerce')
            
            # 日付文字列化
            date_columns = ["日付", "日付1", "日付2", "日付3", "日付4", "日付5"]
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            
            # 日付差計算
            df["日付差"] = (pd.to_datetime(df["日付"], errors='coerce') - pd.to_datetime(df["日付1"], errors='coerce')).dt.days
            df["日付差1"] = (pd.to_datetime(df["日付1"], errors='coerce') - pd.to_datetime(df["日付2"], errors='coerce')).dt.days
            df["日付差2"] = (pd.to_datetime(df["日付2"], errors='coerce') - pd.to_datetime(df["日付3"], errors='coerce')).dt.days
            df["日付差3"] = (pd.to_datetime(df["日付3"], errors='coerce') - pd.to_datetime(df["日付4"], errors='coerce')).dt.days
            df["日付差4"] = (pd.to_datetime(df["日付4"], errors='coerce') - pd.to_datetime(df["日付5"], errors='coerce')).dt.days
            
            logger.info("Derived features calculated successfully")
            return df
            
        except Exception as e:
            logger.error(f"Derived feature calculation failed: {e}")
            return df
    
    def prepare_model_input(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        モデル入力用データを準備（130→101特徴量）
        
        Args:
            features_df: 130特徴量のデータフレーム
            
        Returns:
            pd.DataFrame: 101特徴量のモデル入力用データ
        """
        try:
            logger.info(f"Preparing model input: {features_df.shape[1]} → {features_df.shape[1] - len(self.drop_columns)} features")
            
            # 削除対象列を除外
            model_input_df = features_df.drop(columns=self.drop_columns, errors='ignore')
            
            # 欠損値を空文字のまま保持（デフォルト値は空文字指定のため）
            
            logger.info(f"Model input prepared: {model_input_df.shape[0]} horses × {model_input_df.shape[1]} features")
            return model_input_df
            
        except Exception as e:
            logger.error(f"Model input preparation failed: {e}")
            raise
    
    def create_features_for_prediction(self, horses_data: List[Dict], race_info: Dict) -> pd.DataFrame:
        """
        予測用の完全特徴量作成パイプライン
        
        Args:
            horses_data: スクレイピング出走馬データ
            race_info: レース情報
            
        Returns:
            pd.DataFrame: モデル入力用101特徴量データ
        """
        try:
            logger.info("Starting complete feature engineering pipeline")
            
            # Step 1: 130特徴量作成
            full_features_df = self.create_features_from_scraping_data(horses_data, race_info)
            
            # Step 2: モデル入力用前処理（101特徴量）
            model_input_df = self.prepare_model_input(full_features_df)
            
            logger.info("Feature engineering pipeline completed successfully")
            return model_input_df
            
        except Exception as e:
            logger.error(f"Feature engineering pipeline failed: {e}")
            raise
    
    def _safe_int(self, value) -> str:
        """安全な整数変換（失敗時は空文字）"""
        try:
            if value is None or value == '':
                return ''
            return str(int(float(str(value))))
        except (ValueError, TypeError):
            return ''
    
    def _safe_float(self, value) -> str:
        """安全な浮動小数点変換（失敗時は空文字）"""
        try:
            if value is None or value == '':
                return ''
            return str(float(value))
        except (ValueError, TypeError):
            return ''
    
    def get_feature_info(self) -> Dict:
        """特徴量情報を取得"""
        return {
            "total_features": len(self.all_features),
            "drop_features": len(self.drop_columns),
            "model_input_features": len(self.all_features) - len(self.drop_columns),
            "jockey_data_loaded": self.jockey_win_rate_df is not None and not self.jockey_win_rate_df.empty,
            "time_data_loaded": self.time_data is not None,
            "feature_categories": {
                "race_features": 37,
                "horse_features": 22,
                "performance_features": 37,
                "other_features": 5
            }
        }

# グローバルインスタンス
feature_engineering = FeatureEngineering()