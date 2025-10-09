"""
予測パイプライン全体をデバッグするスクリプト

各段階のデータをCSV出力して、旧システムとの差異を確認する

使用方法:
    python debug_prediction_pipeline.py --race-id 202406010101
    
    オプション:
        --skip-scraping: スクレイピングをスキップ（既存データ使用）
        --compare-only: 予測実行をスキップして比較のみ実行
"""
import argparse
import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# backend配下から実行する想定
sys.path.append(str(Path(__file__).parent))

from app.ml.scraper_integration import NetkeibaRaceScraper
from app.ml.feature_engineering import FeatureEngineering
from app.ml.predictor import IntegratedHorseRacingPredictor


class PredictionPipelineDebugger:
    """予測パイプラインデバッガー"""
    
    def __init__(self, race_id: str):
        self.race_id = race_id
        self.debug_dir = Path("data/debug")
        self.new_system_dir = self.debug_dir / "new_system"
        self.old_system_dir = self.debug_dir / "old_system"
        
        # スクレイパーと予測エンジン
        self.scraper = NetkeibaRaceScraper()
        self.feature_engineer = FeatureEngineering()
        self.predictor = IntegratedHorseRacingPredictor()
        
    async def run_full_pipeline(self, skip_scraping: bool = False):
        """フルパイプラインを実行してデバッグ出力"""
        
        print("=" * 80)
        print(f"予測パイプラインデバッグ - レースID: {self.race_id}")
        print("=" * 80)
        
        # Step 1: スクレイピング（同期関数なのでawaitしない）
        if not skip_scraping:
            print("\n[Step 1] スクレイピング実行中...")
            self._run_scraping()
        else:
            print("\n[Step 1] スクレイピングスキップ（既存データ使用）")
        
        # Step 2: 特徴量エンジニアリング（同期関数）
        print("\n[Step 2] 特徴量エンジニアリング実行中...")
        self._run_feature_engineering_debug()
        
        # Step 3: 予測実行（同期関数）
        print("\n[Step 3] 予測実行中...")
        self._run_prediction()
        
        print("\n" + "=" * 80)
        print("パイプライン実行完了！")
        print("=" * 80)
        
    def _run_scraping(self):
        """スクレイピング実行"""
        try:
            # scrape_race_dataは同期関数なのでawaitしない
            result = self.scraper.scrape_race_data(self.race_id)
            csv_path = result['csv_path']
            
            # 新システムのフォルダにコピー
            output_path = self.new_system_dir / "race_input" / f"race_data_{self.race_id}.csv"
            
            if Path(csv_path).exists():
                df = pd.read_csv(csv_path)
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                print(f"✓ スクレイピング結果保存: {output_path}")
                print(f"  行数: {len(df)}, 列数: {len(df.columns)}")
            else:
                print(f"✗ スクレイピング失敗: {csv_path} が見つかりません")
                
        except Exception as e:
            print(f"✗ スクレイピングエラー: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _run_feature_engineering_debug(self):
        """特徴量エンジニアリングを段階的に実行・出力"""
        
        # スクレイピング結果のCSVパス
        csv_path = self.new_system_dir / "race_input" / f"race_data_{self.race_id}.csv"
        
        if not csv_path.exists():
            # data/race_input からコピー
            original_path = Path("data/race_input") / f"race_data_{self.race_id}.csv"
            if original_path.exists():
                df = pd.read_csv(original_path)
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"  既存データをコピー: {original_path} → {csv_path}")
            else:
                raise FileNotFoundError(f"スクレイピングデータが見つかりません: {csv_path}")
        
        # 特徴量エンジニアを修正して段階的出力
        df = self._feature_engineering_with_debug(csv_path)
        
        return df
    
    def _feature_engineering_with_debug(self, csv_path: Path) -> pd.DataFrame:
        """特徴量エンジニアリングを段階的に実行してデバッグ出力"""
        
        # Step 1: CSV読み込み（既存コードと同じデータ構造）
        print("\n  [2-1] CSV読み込み...")
        df_raw = pd.read_csv(csv_path, dtype=str)
        print(f"    カラム数: {len(df_raw.columns)}")
        print(f"    カラムサンプル: {list(df_raw.columns)[:10]}")
        self._save_debug_csv(df_raw, "step1_raw", "読み込み直後")
        
        # Step 2: 騎手勝率結合（既存メソッド使用）
        print("\n  [2-2] 騎手勝率データ結合...")
        jockey_df = pd.read_csv('../data/reference/jockey_win_rate.csv')
        print(f"    騎手データ: {len(jockey_df)}件")
        
        # 騎手名の表記ゆれ対策を適用
        df_cleaned = self.feature_engineer._apply_jockey_name_standardization(df_raw.copy())
        
        # 騎手勝率データと結合
        df_with_jockey = df_cleaned.merge(
            jockey_df[['騎手', '勝率', '連対率', '複勝率']], 
            on='騎手', 
            how='left'
        )
        # 結合されなかった騎手のデフォルト値設定
        df_with_jockey['勝率'] = df_with_jockey['勝率'].fillna('')
        df_with_jockey['連対率'] = df_with_jockey['連対率'].fillna('')
        df_with_jockey['複勝率'] = df_with_jockey['複勝率'].fillna('')
        
        print(f"    結合後カラム数: {len(df_with_jockey.columns)}")
        self._save_debug_csv(df_with_jockey, "step2_jockey", "騎手勝率結合後")
        
        # Step 3: 派生特徴量計算（既存メソッド使用）
        print("\n  [2-3] 派生特徴量計算（距離差、日付差、平均斤量）...")
        df_derived = self.feature_engineer._calculate_derived_features(df_with_jockey.copy())
        print(f"    派生特徴量計算後カラム数: {len(df_derived.columns)}")
        self._save_debug_csv(df_derived, "step3_derived", "派生特徴量計算後")
        
        # Step 4: 130特徴量（実際にはCSVに全て含まれている）
        print("\n  [2-4] 130特徴量確認...")
        df_130 = df_derived.copy()
        print(f"    130特徴量（実際は{len(df_130.columns)}列）")
        self._save_debug_csv(df_130, "step4_130features", "130特徴量")
        
        # Step 5: 101特徴量（モデル入力）- 既存メソッド使用
        print("\n  [2-5] 101特徴量作成（不要列削除）...")
        df_101 = self.feature_engineer.prepare_model_input(df_130.copy())
        print(f"    モデル入力: {len(df_101.columns)}列")
        print(f"    削除対象: {self.feature_engineer.drop_columns[:5]}...")
        self._save_debug_csv(df_101, "step5_101features", "101特徴量（モデル入力）")
        
        return df_101
    
    def _read_csv_with_encoding_detection(self, csv_path: Path) -> pd.DataFrame:
        """エンコーディング自動検出でCSV読み込み"""
        encodings = ['utf-8', 'utf-8-sig', 'shift-jis', 'cp932', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_path, encoding=encoding)
                print(f"    Successfully read {csv_path.name} with {encoding}")
                return df
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                print(f"    ⚠ Failed to read with {encoding}: {e}")
                continue
        
        # フォールバック: エラーを無視して読み込み
        print(f"    ⚠ Using fallback encoding for {csv_path.name}")
        return pd.read_csv(csv_path, encoding='utf-8', errors='ignore')
    
    def _save_debug_csv(self, df: pd.DataFrame, step_name: str, description: str):
        """デバッグ用CSV保存"""
        output_path = self.new_system_dir / "features" / step_name / f"{self.race_id}_{step_name}.csv"
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"  ✓ {description}: {output_path}")
        print(f"    行数: {len(df)}, 列数: {len(df.columns)}")
    
    def _run_prediction(self):
        """予測実行"""
        try:
            # モデル読み込み
            if not self.predictor.is_loaded:
                print("  モデルを読み込み中...")
                self.predictor.load_models()
            
            # 予測実行（既存メソッドは非同期ではない）
            results = self.predictor.predict_race_from_netkeiba(self.race_id)
            
            if not results.get('success'):
                raise ValueError(f"Prediction failed: {results.get('error')}")
            
            # 結果を保存
            output_path = self.new_system_dir / "predict_result" / f"predict_result_{self.race_id}.csv"
            predictions = results['predictions']
            results_df = pd.DataFrame(predictions)
            results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"✓ 予測結果保存: {output_path}")
            print(f"  馬数: {len(results_df)}")
            print(f"  モデルタイプ: {results.get('model_type')}")
            
            # 予測結果のサマリー表示
            print("\n  【予測結果サマリー】")
            print(f"    勝利確率 - 平均: {results_df['win_probability'].mean():.1f}%")
            print(f"    勝利確率 - 最大: {results_df['win_probability'].max():.1f}%")
            print(f"    複勝確率 - 平均: {results_df['place_probability'].mean():.1f}%")
            print(f"    複勝確率 - 最大: {results_df['place_probability'].max():.1f}%")
            
        except Exception as e:
            print(f"✗ 予測エラー: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def compare_with_old_system(self):
        """旧システムとの比較"""
        print("\n" + "=" * 80)
        print("旧システムとの比較")
        print("=" * 80)
        
        # スクレイピング結果比較
        print("\n[比較1] スクレイピング結果")
        self._compare_scraping_results()
        
        # 予測結果比較
        print("\n[比較2] 予測結果")
        self._compare_prediction_results()
    
    def _compare_scraping_results(self):
        """スクレイピング結果比較"""
        old_csv = self.old_system_dir / "race_input" / f"race_data_{self.race_id}.csv"
        new_csv = self.new_system_dir / "race_input" / f"race_data_{self.race_id}.csv"
        
        if not old_csv.exists():
            print(f"  ⚠ 旧システムデータなし: {old_csv}")
            return
        
        if not new_csv.exists():
            print(f"  ⚠ 新システムデータなし: {new_csv}")
            return
        
        old_df = pd.read_csv(old_csv)
        new_df = pd.read_csv(new_csv)
        
        print(f"\n  旧システム: {len(old_df)}行 × {len(old_df.columns)}列")
        print(f"  新システム: {len(new_df)}行 × {len(new_df.columns)}列")
        
        # カラム名比較
        old_cols = set(old_df.columns)
        new_cols = set(new_df.columns)
        
        if old_cols == new_cols:
            print("  ✓ カラム名: 一致")
        else:
            print("  ✗ カラム名: 差異あり")
            only_old = old_cols - new_cols
            only_new = new_cols - old_cols
            if only_old:
                print(f"    旧のみ: {only_old}")
            if only_new:
                print(f"    新のみ: {only_new}")
        
        # 値の比較（共通カラムのみ）
        common_cols = old_cols & new_cols
        diff_count = 0
        
        for col in sorted(common_cols):
            if not old_df[col].equals(new_df[col]):
                diff_count += 1
                print(f"  ⚠ 差異: {col}")
        
        if diff_count == 0:
            print("  ✓ 全カラムの値: 一致")
        else:
            print(f"  ⚠ {diff_count}個のカラムに差異")
    
    def _compare_prediction_results(self):
        """予測結果比較"""
        # 旧システム（win/place別ファイル）- エンコーディング自動検出
        old_win = self.old_system_dir / "predict_result" / "win" / f"predict_result_{self.race_id}_1st.csv"
        old_place = self.old_system_dir / "predict_result" / "place" / f"predict_result_{self.race_id}_3rd.csv"
        
        # 新システム
        new_pred = self.new_system_dir / "predict_result" / f"predict_result_{self.race_id}.csv"
        
        if not new_pred.exists():
            print(f"  ⚠ 新システム予測結果なし: {new_pred}")
            return
        
        new_df = pd.read_csv(new_pred)
        
        # 旧システムの結果を結合
        if old_win.exists() and old_place.exists():
            # エンコーディング自動検出で読み込み
            old_win_df = self._read_csv_with_encoding_detection(old_win)
            old_place_df = self._read_csv_with_encoding_detection(old_place)
            
            # カラム名確認
            print(f"\n  旧システムファイル情報:")
            print(f"    Win CSV カラム: {list(old_win_df.columns)[:5]}...")
            print(f"    Place CSV カラム: {list(old_place_df.columns)[:5]}...")
            
            # 予測確率が4列目にあると仮定（index=3）
            # カラム名が文字化けしている可能性があるため、位置で取得
            try:
                # 馬番は3列目（index=2）、予測確率は4列目（index=3）
                # 旧システムは0-1の範囲なので100倍してパーセント表記に変換
                old_win_result = old_win_df.iloc[:, [2, 3]].copy()
                old_win_result.columns = ['馬番', '旧_勝利確率_raw']
                old_win_result['旧_勝利確率'] = old_win_result['旧_勝利確率_raw'] * 100.0  # 0-1 → 0-100
                
                old_place_result = old_place_df.iloc[:, [2, 3]].copy()
                old_place_result.columns = ['馬番', '旧_複勝確率_raw']
                old_place_result['旧_複勝確率'] = old_place_result['旧_複勝確率_raw'] * 100.0  # 0-1 → 0-100
                
                # 結合
                old_df = pd.merge(
                    old_win_result[['馬番', '旧_勝利確率']], 
                    old_place_result[['馬番', '旧_複勝確率']], 
                    on='馬番'
                )
                
                print(f"\n  旧システム予測データ:")
                print(f"    馬数: {len(old_df)}")
                print(f"    勝利確率範囲: {old_df['旧_勝利確率'].min():.1f}% - {old_df['旧_勝利確率'].max():.1f}%")
                print(f"    複勝確率範囲: {old_df['旧_複勝確率'].min():.1f}% - {old_df['旧_複勝確率'].max():.1f}%")
                
            except Exception as e:
                print(f"  ⚠ 旧システムデータ解析エラー: {e}")
                print(f"  Win shape: {old_win_df.shape}, Place shape: {old_place_df.shape}")
                return
            
            # 新システムと結合
            comparison_df = pd.merge(
                new_df[['horse_number', 'win_probability', 'place_probability']].rename(columns={
                    'horse_number': '馬番',
                    'win_probability': '新_勝利確率',
                    'place_probability': '新_複勝確率'
                }),
                old_df,
                on='馬番',
                how='outer'
            )
            
            # 差分計算
            comparison_df['勝利確率_差'] = comparison_df['新_勝利確率'] - comparison_df['旧_勝利確率']
            comparison_df['複勝確率_差'] = comparison_df['新_複勝確率'] - comparison_df['旧_複勝確率']
            
            # 比較結果保存
            output_path = self.debug_dir / "comparison" / "predictions" / f"comparison_{self.race_id}.csv"
            comparison_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"\n  比較結果保存: {output_path}")
            print("\n  【差分サマリー】")
            print(f"    勝利確率:")
            print(f"      平均差: {comparison_df['勝利確率_差'].mean():.2f}%")
            print(f"      最大差: {comparison_df['勝利確率_差'].abs().max():.2f}%")
            print(f"      標準偏差: {comparison_df['勝利確率_差'].std():.2f}%")
            print(f"    複勝確率:")
            print(f"      平均差: {comparison_df['複勝確率_差'].mean():.2f}%")
            print(f"      最大差: {comparison_df['複勝確率_差'].abs().max():.2f}%")
            print(f"      標準偏差: {comparison_df['複勝確率_差'].std():.2f}%")
            
            # 順位比較
            comparison_df['旧_勝利順位'] = comparison_df['旧_勝利確率'].rank(ascending=False)
            comparison_df['新_勝利順位'] = comparison_df['新_勝利確率'].rank(ascending=False)
            comparison_df['順位変動'] = comparison_df['旧_勝利順位'] - comparison_df['新_勝利順位']
            
            print(f"\n  【順位変動】")
            print(f"    順位変動なし: {(comparison_df['順位変動'] == 0).sum()}頭")
            print(f"    順位変動あり: {(comparison_df['順位変動'] != 0).sum()}頭")
            print(f"    最大順位変動: {comparison_df['順位変動'].abs().max():.0f}位")
            
            # 差が大きい馬を表示（複勝確率差 > 10%）
            print("\n  【差が大きい馬（複勝確率差 > 10%）】")
            large_diff = comparison_df[comparison_df['複勝確率_差'].abs() > 10.0].sort_values('複勝確率_差', key=abs, ascending=False)
            if len(large_diff) > 0:
                for _, row in large_diff.iterrows():
                    print(f"    馬番{int(row['馬番']):2d}: "
                          f"勝利 {row['旧_勝利確率']:5.1f}% → {row['新_勝利確率']:5.1f}% "
                          f"(差{row['勝利確率_差']:+6.1f}%), "
                          f"複勝 {row['旧_複勝確率']:5.1f}% → {row['新_複勝確率']:5.1f}% "
                          f"(差{row['複勝確率_差']:+6.1f}%)")
            else:
                print("    なし（全馬10%以内の差）")
        else:
            print(f"  ⚠ 旧システムデータなし")


async def main():
    parser = argparse.ArgumentParser(description='予測パイプラインデバッグ')
    parser.add_argument('--race-id', required=True, help='レースID（例: 202406010101）')
    parser.add_argument('--skip-scraping', action='store_true', help='スクレイピングをスキップ')
    parser.add_argument('--compare-only', action='store_true', help='比較のみ実行')
    
    args = parser.parse_args()
    
    debugger = PredictionPipelineDebugger(args.race_id)
    
    if not args.compare_only:
        # awaitを削除
        await debugger.run_full_pipeline(skip_scraping=args.skip_scraping)
    
    debugger.compare_with_old_system()


if __name__ == "__main__":
    asyncio.run(main())