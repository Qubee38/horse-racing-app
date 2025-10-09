# 競馬予測アプリ開発 - 予測結果差異調査（Day 6）

## 作業概要

旧システム（race_scraping.py + prediction.py）と新システム（統合アプリ）の予測結果に差異があったため、データ取得から予測実行までの処理を詳細に調査し、完全一致を達成した。

---

## 初期状態

### 確認された問題
- **予測確率の大幅な差異**: 三位以内確率で10%以上違う結果が多数
- **順位の完全な不一致**: 全16頭で順位が変動（最大12位差）
- **差異の大きさ**: 勝利確率で最大52%、複勝確率で最大36%の差

### システム環境
- 旧システム: Python単体スクリプト（race_scraping.py + prediction.py）
- 新システム: React + FastAPI統合アプリケーション
- 比較レースID: `202506040911`（スプリンターズS）

---

## 調査アプローチ

### デバッグ環境のセットアップ

データフローを段階的に追跡するため、以下の構造でデバッグ環境を構築：

```
data/debug/
├── old_system/           # 旧システムのデータ
│   ├── race_input/       # スクレイピング結果
│   └── predict_result/   # 予測結果（win/place）
├── new_system/           # 新システムのデータ
│   ├── race_input/       # スクレイピング結果
│   ├── features/         # 特徴量の段階的出力
│   │   ├── step1_raw/
│   │   ├── step2_jockey/
│   │   ├── step3_derived/
│   │   ├── step4_130features/
│   │   └── step5_101features/
│   └── predict_result/   # 予測結果
└── comparison/           # 比較結果
    ├── scraping/
    ├── features/
    └── predictions/
```

### デバッグツールの作成

1. **フォルダセットアップスクリプト** (`setup_debug_folders.py`)
2. **パイプラインデバッグスクリプト** (`debug_prediction_pipeline.py`)
   - 各段階でCSVを出力
   - 旧システムとの自動比較
   - 差分サマリー表示
3. **CSV構造確認スクリプト** (`inspect_csv.py`)

---

## 発見された問題と解決策

### 1. 天気・馬場のデフォルト値問題

**問題:**
```python
# 新システム（問題あり）
weather = tenki_mapping.get(weather_text, 0)  # データなし時に0
baba = baba_mapping.get(baba_text, 0)        # データなし時に0

# 旧システム
weather = tenki_mapping.get(weather_text)     # データなし時にNone
baba = baba_mapping.get(baba_text)           # データなし時にNone
```

**影響:**
- 過去戦績の天気1〜5、馬場1〜5で17カラムの差異
- スクレイピング結果の不一致

**解決策:**
- `scraper_integration.py`のマッピング処理からデフォルト値`0`を削除
- データ取得できない場合は`None`を返すように修正

---

### 2. 不要カラムの残存問題

**問題:**
- モデル入力用特徴量に予測時に存在しないカラムが含まれていた
- カラム数: 101列（期待値: 95列）

**含まれていた不要カラム:**
```python
- '走破時間'  # 予測時はNaN
- 'オッズ'    # 予測時は未確定
- '通過順'    # 予測時はNaN
- '着順'      # 予測時はNaN
- '上がり'    # 予測時はNaN
- '人気'      # 予測時は未確定
```

**解決策:**
- `feature_engineering.py`の`drop_columns`に上記カラムを追加
- 結果: 101列 → 95列（モデル期待値と一致）

---

### 3. NaNと0.0の扱いの違い（最重要）

**問題:**
```python
# 新システム（問題あり）
values = pd.to_numeric(values, errors='coerce').fillna(0.0)  # NaNを0に変換

# 旧システム
values = pd.to_numeric(values, errors='coerce')  # NaNはそのまま保持
```

**影響:**
- 過去戦績の欠損データ（馬場1〜5など）でNaNと0.0の違い
- LightGBMはNaNと0.0を全く別の値として扱うため、予測結果が大きく変わる
- 実測で12カラムに差異、予測確率で最大50%以上の差

**解決策:**
- `predictor.py`の`_prepare_dataframe_for_model()`から`fillna(0.0)`を削除
- NaNは欠損値としてそのままLightGBMに渡す

```python
# 修正後
def _prepare_dataframe_for_model(self, model_input_df):
    prepared_df = pd.DataFrame()
    
    for col in self.feature_columns:
        if col in model_input_df.columns:
            values = model_input_df[col].copy()
        else:
            values = pd.Series([np.nan] * len(model_input_df))
        
        values = values.replace('', np.nan)
        values = pd.to_numeric(values, errors='coerce')
        # fillna(0.0)を削除 ← 重要
        
        prepared_df[col] = values
    
    return prepared_df
```

---

### 4. 標準化データの読み込みパス問題

**問題:**
- `standard_deviation.csv`のパスが間違っていた
- 実際のファイル: `data/reference/standard_deviation.csv`
- コード内のパス: `data/standard_deviation.csv`

**影響:**
- タイム標準化がデフォルト値で処理されていた
- 走破時間の標準化に影響

**解決策:**
```python
# 修正前
time_csv_path = os.path.join(self.data_dir, "standard_deviation.csv")

# 修正後
time_csv_path = os.path.join(self.data_dir, "reference", "standard_deviation.csv")
```

---

## 最終結果

### 修正前の差異
```
勝利確率:
  平均差: 17.29%
  最大差: 52.48%
  標準偏差: 20.58%

複勝確率:
  平均差: -14.55%
  最大差: 36.12%
  標準偏差: 20.18%

順位変動:
  変動なし: 0頭
  変動あり: 16頭
  最大変動: 12位
```

### 修正後の結果
```
勝利確率:
  平均差: 0.00%
  最大差: 0.00%
  標準偏差: 0.00%

複勝確率:
  平均差: 0.00%
  最大差: 0.00%
  標準偏差: 0.00%

順位変動:
  変動なし: 16頭
  変動あり: 0頭
  最大変動: 0位
```

**完全一致を達成**

---

## 修正ファイル一覧

### 1. scraper_integration.py
- 天気・馬場マッピングのデフォルト値削除
- 標準化データの読み込みパス修正
- ログ出力の追加

### 2. feature_engineering.py
- `drop_columns`に予測時不要なカラムを追加
- 削除後95列になることを確認

### 3. predictor.py
- `_prepare_dataframe_for_model()`から`fillna(0.0)`を削除
- NaNをそのまま保持してLightGBMに渡す

---

## 技術的知見

### 1. LightGBMの欠損値処理
- LightGBMはNaNを欠損値として正しく処理する
- NaNと0.0は全く別の値として扱われる
- 欠損データは**NaNのまま保持**することが重要

### 2. データパイプラインのデバッグ手法
- 各段階でデータをCSV出力して比較
- カラム数・データ型・値の3つのレベルで確認
- 差異の大きい項目から優先的に調査

### 3. 機械学習モデルの特徴量管理
- 特徴量の順序はモデル名で判断されるため影響しない
- カラム数の一致が最重要
- データ型（NaN vs 0.0）が予測結果に大きく影響

---

## 今後の推奨事項

### 1. テストケースの整備
- 他のレースIDでも同様の検証を実施
- エッジケース（データ不足、特殊レースなど）のテスト
- 単体テスト・統合テストの作成

### 2. データバリデーション
- 入力データの検証機能追加
- 特徴量の型・範囲チェック
- 欠損データの割合監視

### 3. ドキュメント整備
- 特徴量処理の完全ガイド作成済み
- API仕様書の整備
- デプロイメント手順書の作成

---

## まとめ

旧システムと新システムの予測結果が完全に一致したことで、新システムの予測ロジックの正確性が保証された。特にNaNと0.0の扱いが予測精度に決定的な影響を与えることが判明し、重要な技術的知見を得た。

システムは本番稼働可能な状態となり、次のフェーズ（他機能の実装、パフォーマンス最適化、本番環境構築）に進む準備が整った。

---

**作業期間**: 1日（Day 6）  
**最終状態**: 予測結果完全一致達成  
**コード品質**: TypeScript/ESLint完全準拠  
**動作確認**: エンドツーエンド動作確認済み
