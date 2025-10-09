"""
CSV構造確認スクリプト

旧システムのCSVファイルの構造を確認するための簡易ツール

使用方法:
    python inspect_csv.py race_data_202506040911.csv
    python inspect_csv.py predict_result_202506040911_1st.csv
    python inspect_csv.py predict_result_202506040911_3rd.csv
"""
import sys
import pandas as pd
from pathlib import Path

def inspect_csv(file_path: str):
    """CSVファイルの構造を詳細に確認"""
    
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {file_path}")
        return
    
    print("=" * 80)
    print(f"CSV構造確認: {path.name}")
    print("=" * 80)
    
    # 複数のエンコーディングで試行
    encodings = ['utf-8', 'utf-8-sig', 'shift-jis', 'cp932', 'iso-8859-1']
    df = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(path, encoding=encoding)
            used_encoding = encoding
            print(f"✓ エンコーディング: {encoding}")
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"⚠ {encoding} でエラー: {e}")
            continue
    
    if df is None:
        print("❌ 全てのエンコーディングで読み込み失敗")
        return
    
    # 基本情報
    print(f"\n【基本情報】")
    print(f"  行数: {len(df)}")
    print(f"  列数: {len(df.columns)}")
    print(f"  データ型の種類: {df.dtypes.value_counts().to_dict()}")
    
    # カラム一覧（最初の20個）
    print(f"\n【カラム一覧（最初の20個）】")
    for i, col in enumerate(df.columns[:20], 1):
        dtype = df[col].dtype
        non_null = df[col].notna().sum()
        sample_value = df[col].iloc[0] if len(df) > 0 else None
        print(f"  {i:2d}. {col:20s} | {str(dtype):10s} | 非NULL: {non_null:2d}/{len(df)} | サンプル: {sample_value}")
    
    if len(df.columns) > 20:
        print(f"  ... 他 {len(df.columns) - 20} 列")
    
    # 先頭5行の表示
    print(f"\n【先頭5行】")
    print(df.head().to_string())
    
    # 予測結果CSVの場合、4列目（予測確率）を詳細表示
    if 'predict_result' in path.name:
        print(f"\n【予測確率列の詳細（4列目 = index 3）】")
        if len(df.columns) > 3:
            prob_col = df.columns[3]
            probs = df.iloc[:, 3]
            print(f"  カラム名: {prob_col}")
            print(f"  データ型: {probs.dtype}")
            print(f"  最小値: {probs.min():.4f}")
            print(f"  最大値: {probs.max():.4f}")
            print(f"  平均値: {probs.mean():.4f}")
            print(f"  全データ:")
            for i, prob in enumerate(probs, 1):
                print(f"    馬{i:2d}: {prob:8.4f}%")
    
    # 統計情報
    print(f"\n【数値列の統計】")
    numeric_cols = df.select_dtypes(include=['number']).columns[:5]
    if len(numeric_cols) > 0:
        print(df[numeric_cols].describe().to_string())
    
    # 欠損値情報
    print(f"\n【欠損値情報】")
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if len(missing_cols) > 0:
        print(f"  欠損値がある列数: {len(missing_cols)}")
        for col, count in missing_cols.head(10).items():
            print(f"    {col}: {count}個 ({count/len(df)*100:.1f}%)")
    else:
        print("  欠損値なし")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python inspect_csv.py <csv_file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    inspect_csv(file_path)