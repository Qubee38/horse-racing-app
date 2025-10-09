import os
import json
import logging
from typing import Dict, List, Tuple, Optional
import lightgbm as lgb
import pandas as pd
import numpy as np
from datetime import datetime

from .scraper_integration import scraper
from .feature_processor import feature_processor
from .feature_engineering import feature_engineering

logger = logging.getLogger(__name__)

class IntegratedHorseRacingPredictor:
    """統合競馬予測エンジン（枠番対応版）"""
    
    def __init__(self, models_path: str = None):
        # プロジェクトルートからの相対パスでモデルディレクトリを指定
        if models_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            models_path = os.path.join(project_root, "data", "models")
        
        self.models_path = models_path
        self.win_model = None
        self.place_model = None
        self.legacy_model = None
        self.feature_columns = None
        self.is_loaded = False
        self.use_legacy = False  # 既存モデル使用フラグ
        
        logger.info(f"Integrated predictor initialized with models path: {self.models_path}")
        
    def load_models(self) -> bool:
        """モデルを読み込み（新モデル優先、フォールバック対応）"""
        try:
            # 新しいモデルファイルの確認
            win_model_path = os.path.join(self.models_path, "win_model.txt")
            place_model_path = os.path.join(self.models_path, "place_model.txt")
            legacy_model_path = os.path.join(self.models_path, "model.txt")
            
            logger.info(f"Checking model files:")
            logger.info(f"  Win model: {win_model_path} (exists: {os.path.exists(win_model_path)})")
            logger.info(f"  Place model: {place_model_path} (exists: {os.path.exists(place_model_path)})")
            logger.info(f"  Legacy model: {legacy_model_path} (exists: {os.path.exists(legacy_model_path)})")
            
            # 新しいモデル（win + place）を優先的に読み込み
            if os.path.exists(win_model_path) and os.path.exists(place_model_path):
                logger.info("Loading new models (win + place)")
                self.win_model = lgb.Booster(model_file=win_model_path)
                self.place_model = lgb.Booster(model_file=place_model_path)
                self.feature_columns = self.win_model.feature_name()
                self.use_legacy = False
                
            elif os.path.exists(legacy_model_path):
                logger.info("Loading legacy model")
                self.legacy_model = lgb.Booster(model_file=legacy_model_path)
                self.feature_columns = self.legacy_model.feature_name()
                self.use_legacy = True
                
            else:
                raise FileNotFoundError("No model files found")
            
            self.is_loaded = True
            logger.info(f"Models loaded successfully. Mode: {'legacy' if self.use_legacy else 'new'}, Features: {len(self.feature_columns)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            self.is_loaded = False
            return False
    
    def predict_race_from_netkeiba(self, race_id: str) -> Dict:
        """
        Netkeibaからデータをスクレイピングしてレース予測を実行（枠番対応版）
        
        Args:
            race_id: Netkeibaのレース ID
            
        Returns:
            Dict: 予測結果（枠番情報を含む）
        """
        try:
            logger.info(f"Starting integrated prediction for race {race_id}")
            
            # Step 1: スクレイピング
            logger.info("Step 1: Scraping race data from Netkeiba")
            scraping_result = scraper.scrape_race_data(race_id)
            
            if not scraping_result:
                raise ValueError("Failed to scrape race data")
            
            race_info = scraping_result['race_info']
            horses_data = scraping_result['horses_data']
            csv_path = scraping_result['csv_path']
            
            logger.info(f"Scraped {len(horses_data)} horses for race {race_info['race_name']}")
            
            # === 新機能: 枠番・馬番情報を別途抽出・保持 ===
            frame_number_mapping = {}
            for horse in horses_data:
                horse_name = horse.get('horse_name', '')
                frame_number = horse.get('frame_number', 1)
                horse_number = horse.get('horse_number', '1')
                
                frame_number_mapping[horse_name] = {
                    'frame_number': int(frame_number),
                    'horse_number': int(horse_number)
                }
            
            logger.info(f"Extracted frame/horse numbers for {len(frame_number_mapping)} horses")
            logger.debug(f"Frame mapping sample: {list(frame_number_mapping.items())[:3]}")
            
            # Step 2: 特徴量処理
            logger.info("Step 2: Processing features")
            if self.use_legacy:
                # 既存ロジックで特徴量処理
                logger.info("Using legacy feature processing")
                
                try:
                    processed_features = feature_processor.process_race_features_from_csv(csv_path)
                    if processed_features is None:
                        raise ValueError("Failed to process features with legacy processor")
                    
                    # 既存モデルで予測
                    prediction_results = feature_processor.predict_with_legacy_model(processed_features, race_id)
                    
                except Exception as e:
                    logger.warning(f"Legacy processing failed: {e}, using fallback")
                    prediction_results = self._create_fallback_predictions(horses_data, race_info)
                
            else:
                # 新しいロジックで特徴量処理
                logger.info("Using new feature processing")
                prediction_results = self._predict_with_new_models(horses_data, race_info)
            
            # Step 3: 結果の統合と後処理（枠番情報を統合）
            logger.info("Step 3: Post-processing results with frame numbers")
            final_results = self._post_process_results_with_frame_numbers(
                prediction_results, 
                horses_data, 
                race_info,
                frame_number_mapping  # 枠番マッピングを渡す
            )
            
            return {
                'success': True,
                'race_id': race_id,
                'race_info': race_info,
                'predictions': final_results,
                'model_type': 'legacy' if self.use_legacy else 'new',
                'csv_path': csv_path
            }
            
        except Exception as e:
            logger.error(f"Integrated prediction failed for race {race_id}: {e}")
            return {
                'success': False,
                'race_id': race_id,
                'error': str(e),
                'predictions': []
            }
    
    def _predict_with_new_models(self, horses_data: List[Dict], race_info: Dict) -> List[Dict]:
        """新しいモデル（win + place）で予測実行"""
        if not self.is_loaded or self.use_legacy:
            return self._create_dummy_predictions(len(horses_data))
        
        try:
            logger.info("Starting new model prediction with feature_engineering")
            
            # Step 1: 特徴量エンジニアリングで101特徴量を作成
            model_input_df = feature_engineering.create_features_for_prediction(horses_data, race_info)
            logger.info(f"Feature engineering completed: {model_input_df.shape}")
            
            # Step 2: 全馬まとめて予測実行（DataFrameを直接モデルに入力）
            win_probs, place_probs = self.predict_all_horses(model_input_df)
            
            # Step 3: 予測結果を整理
            predictions = []
            for i, (win_prob, place_prob) in enumerate(zip(win_probs, place_probs)):
                # 馬名を取得（DataFrameから）
                horse_name = model_input_df.iloc[i].get('馬', f'horse_{i}')
                
                # 信頼度計算（全体データから）
                confidence = self._calculate_confidence_from_df(model_input_df.iloc[[i]])
                
                predictions.append({
                    'horse_index': i,
                    'horse_id': horse_name,  # 馬名を保持
                    'win_probability': win_prob,
                    'place_probability': place_prob,
                    'confidence_score': confidence
                })
                
                logger.debug(f"Horse {i} ({horse_name}): Win={win_prob:.1f}%, Place={place_prob:.1f}%, Confidence={confidence:.2f}")
            
            logger.info(f"New model predictions completed for {len(predictions)} horses")
            return predictions
            
        except Exception as e:
            logger.error(f"New model prediction failed: {e}")
            return self._create_dummy_predictions(len(horses_data))
    
    def _create_fallback_predictions(self, horses_data: List[Dict], race_info: Dict) -> List[Dict]:
        """フォールバック予測（オッズベース）"""
        logger.info("Creating fallback predictions based on odds")
        predictions = []
        
        for i, horse in enumerate(horses_data):
            try:
                # オッズベースの簡易予測
                odds = float(horse.get('odds', 5.0)) if horse.get('odds') else 5.0
                
                # オッズから確率を逆算（簡易版）
                if odds > 0:
                    win_prob = max(1.0, min(50.0, 100.0 / odds))
                    place_prob = min(80.0, win_prob * 3.5)
                else:
                    win_prob = 15.0
                    place_prob = 40.0
                
                predictions.append({
                    'horse_index': i,
                    'horse_id': horse.get('horse_name', f'horse_{i}'),
                    'win_probability': win_prob,
                    'place_probability': place_prob,
                    'confidence_score': 0.6
                })
                
            except Exception as e:
                logger.warning(f"Fallback prediction failed for horse {i}: {e}")
                predictions.append({
                    'horse_index': i,
                    'horse_id': horse.get('horse_name', f'horse_{i}'),
                    'win_probability': 10.0,
                    'place_probability': 35.0,
                    'confidence_score': 0.3
                })
        
        return predictions
    
    def predict_all_horses(self, model_input_df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """全馬まとめて予測実行（新モデル用）"""
        if not self.is_loaded or self.use_legacy:
            raise RuntimeError("New models not loaded")
        
        try:
            logger.info(f"Predicting all horses: {model_input_df.shape}")
            
            # DataFrameを直接モデルに入力可能な形式に準備
            prepared_df = self._prepare_dataframe_for_model(model_input_df)
            
            # 勝利確率予測（全馬まとめて）
            win_probs_raw = self.win_model.predict(prepared_df)
            
            # 複勝確率予測（全馬まとめて）
            place_probs_raw = self.place_model.predict(prepared_df)
            
            # 確率を0-100の範囲に変換
            win_probs = [max(0.0, min(100.0, prob * 100)) for prob in win_probs_raw]
            place_probs = [max(0.0, min(100.0, prob * 100)) for prob in place_probs_raw]
            
            logger.info(f"Batch prediction completed: {len(win_probs)} horses")
            logger.debug(f"Win probabilities range: {min(win_probs):.1f}% - {max(win_probs):.1f}%")
            logger.debug(f"Place probabilities range: {min(place_probs):.1f}% - {max(place_probs):.1f}%")
            
            return win_probs, place_probs
            
        except Exception as e:
            logger.error(f"Batch horse prediction failed: {e}")
            num_horses = len(model_input_df)
            return [10.0] * num_horses, [35.0] * num_horses
    
    def _prepare_dataframe_for_model(self, model_input_df: pd.DataFrame) -> pd.DataFrame:
        """DataFrameをモデル入力形式に準備"""
        try:
            # モデルが期待する特徴量順序に合わせる
            prepared_df = pd.DataFrame()
            
            for col in self.feature_columns:
                if col in model_input_df.columns:
                    values = model_input_df[col].copy()
                else:
                    values = pd.Series([0.0] * len(model_input_df))
                
                # === 修正: NaNを0.0に変換しない ===
                # 空文字のみを数値変換し、NaNはそのまま保持
                values = values.replace('', np.nan)  # 空文字をNaNに
                values = pd.to_numeric(values, errors='coerce')  # 数値変換
                # fillna(0.0)を削除 - NaNはLightGBMが正しく処理する
                
                prepared_df[col] = values
            
            logger.debug(f"Prepared DataFrame: {prepared_df.shape}, dtypes: {prepared_df.dtypes.value_counts().to_dict()}")
            return prepared_df
            
        except Exception as e:
            logger.error(f"DataFrame preparation failed: {e}")
            num_rows = len(model_input_df)
            dummy_data = pd.DataFrame(
                [[0.0] * len(self.feature_columns)] * num_rows,
                columns=self.feature_columns
            )
            return dummy_data
    
    def _calculate_confidence_from_df(self, horse_df: pd.DataFrame) -> float:
        """DataFrameから信頼度を計算"""
        try:
            if len(horse_df) == 0:
                return 0.5
                
            # 非ゼロ特徴量の割合から信頼度計算
            horse_row = horse_df.iloc[0]
            non_zero_features = (horse_row != 0.0).sum()
            total_features = len(horse_row)
            completeness_score = non_zero_features / total_features
            confidence = 0.3 + (completeness_score * 0.6)
            return min(0.9, max(0.3, confidence))
        except:
            return 0.5
    
    def _post_process_results_with_frame_numbers(
        self, 
        predictions: List[Dict], 
        horses_data: List[Dict], 
        race_info: Dict,
        frame_number_mapping: Dict[str, Dict]
    ) -> List[Dict]:
        """
        予測結果の後処理（枠番対応版）
        
        Args:
            predictions: 予測結果リスト
            horses_data: 馬データリスト
            race_info: レース情報
            frame_number_mapping: 馬名→{frame_number, horse_number}のマッピング
        """
        final_results = []
        
        for i, pred in enumerate(predictions):
            if i < len(horses_data):
                horse = horses_data[i]
                horse_name = horse.get('horse_name', f'Horse_{i+1}')
                
                # === 枠番・馬番情報を取得 ===
                frame_info = frame_number_mapping.get(horse_name, {
                    'frame_number': 1,
                    'horse_number': i + 1
                })
                
                # オッズの安全な変換
                odds_raw = horse.get('odds', '5.0')
                odds = self._safe_convert_odds(odds_raw)
                
                # 期待値計算
                win_prob = pred.get('win_probability', 10.0) / 100.0
                expected_value = self._calculate_expected_value(win_prob, odds)
                
                result = {
                    'horse_id': i + 1,
                    'horse_name': horse_name,
                    'jockey': horse.get('jockey', '未定'),
                    'horse_number': frame_info['horse_number'],  # 正確な馬番
                    'frame_number': frame_info['frame_number'],  # 正確な枠番
                    'odds': odds,
                    'win_probability': pred.get('win_probability', 10.0),
                    'place_probability': pred.get('place_probability', 35.0),
                    'expected_value': expected_value,
                    'confidence_score': pred.get('confidence_score', 0.5)
                }
                
                logger.debug(f"Processed horse: {horse_name}, Frame={frame_info['frame_number']}, Horse#={frame_info['horse_number']}")
                
                final_results.append(result)
        
        logger.info(f"Post-processed {len(final_results)} horses with frame numbers")
        return final_results
    
    def _safe_convert_odds(self, odds_value) -> float:
        """オッズを安全に数値変換"""
        try:
            if odds_value is None:
                return 5.0
                
            # 文字列の場合
            if isinstance(odds_value, str):
                # 空文字、'---.-'、'-.--' などの無効値をチェック
                if odds_value == '' or '---' in odds_value or '-.' in odds_value or odds_value == 'nan':
                    return 5.0
                
                # 数値変換を試行
                odds_float = float(odds_value)
                
                # 有効な範囲かチェック（競馬オッズは通常1.0〜999.9）
                if odds_float <= 0 or odds_float > 1000:
                    return 5.0
                    
                return odds_float
                
            # 数値の場合
            elif isinstance(odds_value, (int, float)):
                odds_float = float(odds_value)
                if odds_float <= 0 or odds_float > 1000:
                    return 5.0
                return odds_float
                
            else:
                return 5.0
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert odds '{odds_value}': {e}")
            return 5.0
    
    def _calculate_expected_value(self, win_probability: float, odds: float) -> float:
        """期待値計算"""
        try:
            if odds <= 1.0:
                return 50.0
            expected_return = (win_probability * odds) - 1
            expected_value_percentage = expected_return * 100
            return max(0.0, min(200.0, expected_value_percentage))
        except:
            return 80.0
    
    def _create_dummy_predictions(self, num_horses: int) -> List[Dict]:
        """ダミー予測結果を作成"""
        results = []
        for i in range(num_horses):
            base_prob = max(5, 20 - i * 1.5)
            win_prob = base_prob + np.random.uniform(-2, 2)
            place_prob = min(win_prob * 3, 70) + np.random.uniform(-5, 5)
            
            results.append({
                'horse_index': i,
                'win_probability': float(max(1, win_prob)),
                'place_probability': float(max(10, place_prob)),
                'confidence_score': 0.5
            })
        
        return results
    
    def get_model_info(self) -> Dict:
        """モデル情報を取得"""
        if not self.is_loaded:
            return {
                "status": "not_loaded",
                "models_path": self.models_path,
                "path_exists": os.path.exists(self.models_path) if self.models_path else False
            }
        
        # 特徴量エンジニアリング情報も含める
        feature_info = feature_engineering.get_feature_info()
        
        return {
            "status": "loaded",
            "model_type": "legacy" if self.use_legacy else "new",
            "models_path": self.models_path,
            "feature_count": len(self.feature_columns),
            "model_files": {
                "win_model": "win_model.txt" if not self.use_legacy else None,
                "place_model": "place_model.txt" if not self.use_legacy else None,
                "legacy_model": "model.txt" if self.use_legacy else None
            },
            "feature_names_sample": self.feature_columns[:10] if self.feature_columns else [],
            "loaded_at": datetime.utcnow().isoformat(),
            "feature_engineering": feature_info
        }

# グローバル予測器インスタンス（統合版）
predictor = IntegratedHorseRacingPredictor()