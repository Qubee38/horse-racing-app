import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FeatureProcessor:
    """既存のprediction.pyロジックと統合するための特徴量処理クラス"""
    
    def __init__(self):
        self.base_path = self._get_project_root()
        logger.info(f"FeatureProcessor initialized with base path: {self.base_path}")
    
    def _get_project_root(self) -> str:
        """プロジェクトルートパスを取得"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    
    def process_race_features_from_csv(self, csv_path: str) -> Optional[pd.DataFrame]:
        """
        CSVファイルから特徴量を処理（既存prediction.pyロジック統合）
        
        Args:
            csv_path: レースデータCSVファイルのパス
            
        Returns:
            pd.DataFrame: 処理済み特徴量データ
        """
        try:
            if not os.path.exists(csv_path):
                logger.error(f"CSV file not found: {csv_path}")
                return None
            
            logger.info(f"Processing features from CSV: {csv_path}")
            
            # CSVファイルを読み込み
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # 既存のprediction.pyで使用している前処理を適用
            processed_df = self._apply_legacy_preprocessing(df)
            
            return processed_df
            
        except Exception as e:
            logger.error(f"Failed to process features from CSV: {e}")
            return None
    
    def _apply_legacy_preprocessing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        既存コードの前処理を適用
        ここでは簡略化版を実装、実際には既存のprediction.pyのロジックを統合
        """
        try:
            logger.info("Applying legacy preprocessing")
            
            # 数値列の変換
            numeric_columns = [
                'オッズ', '人気', '体重', '体重変化', '斤量', '距離', '馬番',
                'オッズ1', 'オッズ2', 'オッズ3', 'オッズ4', 'オッズ5',
                '体重1', '体重2', '体重3', '体重4', '体重5',
                '距離1', '距離2', '距離3', '距離4', '距離5'
            ]
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 欠損値の処理
            df = df.fillna(0)
            
            # 既存コードで使用している特徴量エンジニアリング
            if '平均斤量' not in df.columns:
                kinryo_cols = [c for c in df.columns if c.startswith('斤量')]
                if kinryo_cols:
                    df['平均斤量'] = df[kinryo_cols].mean(axis=1, skipna=True)
            
            # 距離差、日付差などの計算（既存コードロジック）
            self._calculate_derived_features(df)
            
            logger.info("Legacy preprocessing completed")
            return df
            
        except Exception as e:
            logger.error(f"Legacy preprocessing failed: {e}")
            return df
    
    def _calculate_derived_features(self, df: pd.DataFrame):
        """派生特徴量の計算"""
        try:
            # 距離差の計算
            if '距離' in df.columns and '距離1' in df.columns:
                df['距離差'] = df['距離'] - df['距離1']
            
            # 平均オッズの計算
            odds_cols = [c for c in df.columns if c.startswith('オッズ') and c != 'オッズ']
            if odds_cols:
                df['平均過去オッズ'] = df[odds_cols].mean(axis=1, skipna=True)
            
            # 人気の平均
            if '人気' in df.columns:
                df['人気順位'] = df['人気'].rank(method='min')
            
        except Exception as e:
            logger.warning(f"Derived feature calculation failed: {e}")
    
    def predict_with_legacy_model(self, features_df: pd.DataFrame, race_id: str) -> List[Dict]:
        """
        既存モデルで予測実行（prediction.pyロジック統合）
        
        Args:
            features_df: 処理済み特徴量DataFrame
            race_id: レースID
            
        Returns:
            List[Dict]: 予測結果リスト
        """
        try:
            logger.info(f"Predicting with legacy model for race {race_id}")
            
            # 既存のprediction.pyロジックを呼び出し
            # ここでは簡略化版を実装
            predictions = self._execute_legacy_prediction(features_df)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Legacy model prediction failed: {e}")
            return self._create_fallback_predictions(len(features_df))
    
    def _execute_legacy_prediction(self, df: pd.DataFrame) -> List[Dict]:
        """
        既存予測ロジックの実行（簡略化版）
        実際の実装では既存のprediction.pyのメインロジックを統合
        """
        predictions = []
        
        for i, row in df.iterrows():
            try:
                # 既存ロジックベースの予測計算
                # オッズベースの簡易計算（実際には機械学習モデルを使用）
                odds = float(row.get('オッズ', 5.0))
                popularity = int(row.get('人気', 5)) if pd.notna(row.get('人気')) else 5
                
                # 人気とオッズから確率を推定
                if odds > 0:
                    base_win_prob = 100.0 / odds
                    # 人気順位による調整
                    popularity_factor = max(0.5, 1.0 - (popularity - 1) * 0.1)
                    win_prob = base_win_prob * popularity_factor
                    win_prob = max(1.0, min(50.0, win_prob))
                else:
                    win_prob = 10.0
                
                place_prob = min(80.0, win_prob * 3.5)
                
                # 過去戦績による調整
                past_performance_factor = self._calculate_past_performance_factor(row)
                win_prob *= past_performance_factor
                place_prob *= past_performance_factor
                
                # 信頼度計算
                confidence = self._calculate_confidence_legacy(row)
                
                prediction = {
                    'horse_index': i,
                    'horse_id': row.get('馬', f'horse_{i}'),
                    'win_probability': max(1.0, min(50.0, win_prob)),
                    'place_probability': max(10.0, min(80.0, place_prob)),
                    'confidence_score': confidence
                }
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.warning(f"Prediction failed for horse {i}: {e}")
                predictions.append({
                    'horse_index': i,
                    'horse_id': row.get('馬', f'horse_{i}'),
                    'win_probability': 10.0,
                    'place_probability': 35.0,
                    'confidence_score': 0.3
                })
        
        return predictions
    
    def _calculate_past_performance_factor(self, row: pd.Series) -> float:
        """過去戦績による調整係数を計算"""
        try:
            # 過去の着順から調整係数を計算
            past_finishes = []
            for i in range(1, 6):  # 過去5走
                finish_col = f'着順{i}' if f'着順{i}' in row.index else f'着順{i}'
                if finish_col in row.index and pd.notna(row[finish_col]):
                    try:
                        finish = int(row[finish_col])
                        if 1 <= finish <= 18:  # 有効な着順範囲
                            past_finishes.append(finish)
                    except (ValueError, TypeError):
                        continue
            
            if not past_finishes:
                return 1.0  # デフォルト
            
            # 平均着順による調整
            avg_finish = sum(past_finishes) / len(past_finishes)
            if avg_finish <= 3:
                return 1.3  # 好成績馬は上昇
            elif avg_finish <= 6:
                return 1.1
            elif avg_finish <= 10:
                return 0.9
            else:
                return 0.7  # 不調馬は下降
            
        except Exception:
            return 1.0
    
    def _calculate_confidence_legacy(self, row: pd.Series) -> float:
        """レガシー方式での信頼度計算"""
        try:
            confidence_factors = []
            
            # オッズの信頼性
            odds = row.get('オッズ', 0)
            if pd.notna(odds) and odds > 0:
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.3)
            
            # 人気の信頼性
            popularity = row.get('人気', 0)
            if pd.notna(popularity) and 1 <= popularity <= 18:
                confidence_factors.append(0.9)
            else:
                confidence_factors.append(0.4)
            
            # 過去戦績データの豊富さ
            past_data_count = 0
            for i in range(1, 6):
                if pd.notna(row.get(f'着順{i}', None)):
                    past_data_count += 1
            
            data_confidence = min(0.9, 0.3 + (past_data_count * 0.12))
            confidence_factors.append(data_confidence)
            
            # 総合信頼度
            avg_confidence = sum(confidence_factors) / len(confidence_factors)
            return max(0.3, min(0.95, avg_confidence))
            
        except Exception:
            return 0.5
    
    def _create_fallback_predictions(self, num_horses: int) -> List[Dict]:
        """フォールバック予測を作成"""
        predictions = []
        
        for i in range(num_horses):
            base_prob = max(5, 25 - i * 2)
            win_prob = base_prob + np.random.uniform(-3, 3)
            place_prob = min(win_prob * 3.2, 75) + np.random.uniform(-5, 5)
            
            predictions.append({
                'horse_index': i,
                'horse_id': f'horse_{i}',
                'win_probability': float(max(1, win_prob)),
                'place_probability': float(max(10, place_prob)),
                'confidence_score': 0.4
            })
        
        return predictions
    
    def process_race_features(self, race_id: str) -> Optional[pd.DataFrame]:
        """
        レースIDから特徴量を処理（レガシー用インターフェース）
        
        Args:
            race_id: レースID
            
        Returns:
            pd.DataFrame: 処理済み特徴量
        """
        try:
            # race_inputディレクトリからCSVファイルを検索
            race_input_dir = os.path.join(self.base_path, "data", "race_input")
            csv_path = os.path.join(race_input_dir, f"race_data_{race_id}.csv")
            
            if os.path.exists(csv_path):
                return self.process_race_features_from_csv(csv_path)
            else:
                logger.error(f"Race data CSV not found for race_id: {race_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to process race features for {race_id}: {e}")
            return None
    
    def integrate_with_legacy_prediction(self, race_id: str) -> Optional[Dict]:
        """
        既存のprediction.pyとの統合インターフェース
        
        Args:
            race_id: レースID
            
        Returns:
            Dict: 統合予測結果
        """
        try:
            # 既存のprediction.pyスクリプトを実行
            prediction_script = os.path.join(self.base_path, "prediction.py")
            
            if os.path.exists(prediction_script):
                # システムコール経由で既存スクリプトを実行
                import subprocess
                result = subprocess.run([
                    sys.executable, prediction_script, race_id
                ], capture_output=True, text=True, cwd=self.base_path)
                
                if result.returncode == 0:
                    logger.info("Legacy prediction script executed successfully")
                    return {
                        'success': True,
                        'output': result.stdout,
                        'method': 'legacy_script'
                    }
                else:
                    logger.error(f"Legacy script failed: {result.stderr}")
                    return None
            else:
                logger.warning("Legacy prediction script not found")
                return None
                
        except Exception as e:
            logger.error(f"Legacy integration failed: {e}")
            return None
    
    def validate_features(self, df: pd.DataFrame) -> bool:
        """特徴量データの妥当性検証"""
        try:
            # 基本的な妥当性チェック
            if df is None or df.empty:
                return False
            
            required_columns = ['馬', '騎手', 'オッズ', '人気']
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                logger.warning(f"Missing required columns: {missing_cols}")
                return False
            
            # データ型チェック
            numeric_cols = ['オッズ', '人気', '体重', '斤量']
            for col in numeric_cols:
                if col in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        logger.warning(f"Column {col} is not numeric")
                        return False
            
            logger.info("Feature validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Feature validation failed: {e}")
            return False

# グローバルインスタンス
feature_processor = FeatureProcessor()