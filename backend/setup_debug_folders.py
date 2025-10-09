"""
予測結果差異デバッグ用のフォルダ構成セットアップスクリプト

使用方法:
    python setup_debug_folders.py
"""
import os
from pathlib import Path

def setup_debug_folders():
    """デバッグ用フォルダ構成を作成"""
    
    base_dir = Path("data/debug")
    
    # フォルダ構成
    folders = [
        # 旧システムのデータ
        "old_system/race_input",           # 旧: スクレイピング結果
        "old_system/predict_result/win",   # 旧: 1着確率予測結果
        "old_system/predict_result/place", # 旧: 3着以内確率予測結果
        
        # 新システムのデータ
        "new_system/race_input",           # 新: スクレイピング結果
        "new_system/features/step1_raw",   # 新: 読み込み直後
        "new_system/features/step2_jockey", # 新: 騎手勝率結合後
        "new_system/features/step3_derived", # 新: 派生特徴量計算後
        "new_system/features/step4_130features", # 新: 130特徴量
        "new_system/features/step5_101features", # 新: 101特徴量（モデル入力）
        "new_system/predict_result",       # 新: 予測結果
        
        # 比較結果
        "comparison/scraping",             # スクレイピング結果比較
        "comparison/features",             # 特徴量比較
        "comparison/predictions",          # 予測結果比較
    ]
    
    print("=" * 60)
    print("デバッグ用フォルダ構成セットアップ")
    print("=" * 60)
    
    for folder in folders:
        full_path = base_dir / folder
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ {full_path}")
    
    print("\n" + "=" * 60)
    print("セットアップ完了！")
    print("=" * 60)
    
    # 使用方法の説明
    print("\n【次のステップ】")
    print("1. 旧システムのデータを以下にコピーしてください：")
    print(f"   - race_data_*.csv → {base_dir}/old_system/race_input/")
    print(f"   - 1着確率結果 → {base_dir}/old_system/predict_result/win/")
    print(f"   - 3着以内確率結果 → {base_dir}/old_system/predict_result/place/")
    print("\n2. デバッグスクリプトを実行：")
    print("   python debug_prediction_pipeline.py --race-id 202406010101")

if __name__ == "__main__":
    setup_debug_folders()