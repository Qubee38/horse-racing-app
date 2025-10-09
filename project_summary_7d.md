# 競馬予測アプリ開発 - レース結果機能実装（Day 7）

## プロジェクト概要

### 技術スタック
- **フロントエンド**: React + TypeScript + Tailwind CSS
- **バックエンド**: FastAPI + SQLAlchemy
- **データベース**: SQLite
- **予測モデル**: LightGBM（win_model.txt + place_model.txt）
- **データ取得**: Selenium + Netkeibaスクレイピング

---

## 今回セッションの実装内容

### Phase 1: データベーススキーマ設計

#### 新規テーブル

**1. bet_types（券種マスター）**
```sql
- id: Integer (PK)
- code: String(20) UNIQUE  # win, place
- name: String(50)          # 単勝, 複勝
- is_active: Boolean
```

**初期データ**:
- 単勝・複勝: 有効
- 馬連・馬単・ワイド・三連複・三連単: 無効（将来拡張用）

**2. race_results（レース結果メタデータ）**
```sql
- id: Integer (PK)
- race_id: Integer (FK → races.id) UNIQUE
- race_status: String(20)  # completed, cancelled, partial_data
- result_fetched_at: DateTime
```

**3. horse_results（各馬の着順）**
```sql
- id: Integer (PK)
- race_result_id: Integer (FK → race_results.id)
- race_id: Integer (FK → races.id)
- horse_id: Integer (FK → horses.id) NULLABLE
- netkeiba_horse_id: String(20) NULLABLE  # 照合用
- horse_number: Integer NOT NULL          # 照合キー
- finish_position: Integer NULLABLE
- popularity: Integer NULLABLE
```

**ユニーク制約**: `(race_id, horse_number)`

**4. payouts（払い戻し情報）**
```sql
- id: Integer (PK)
- race_result_id: Integer (FK → race_results.id)
- race_id: Integer (FK → races.id)
- bet_type_id: Integer (FK → bet_types.id)
- winning_numbers: String(50)
- payout_amount: Integer  # 100円あたり
```

#### モデルファイル修正

**race.py**: `race_result` リレーション追加（1対1）
**horse.py**: `horse_results` リレーション追加、`predictions` リレーション削除
**prediction.py**: `back_populates` 削除（Horseとの双方向リレーション解除）

---

### Phase 2: スクレイピング機能実装

#### race_result_scraper.py

**主要機能**:
- Netkeibaレース結果ページからのデータ取得
- User-Agent偽装とRate Limiting対応
- 着順・人気順位の抽出
- 払い戻し情報の抽出（単勝・複勝）

**重要な実装ポイント**:

1. **払い戻し額の正確な解析**
```python
# 問題: 複数の馬番・払い戻し額が<br>で区切られている
# 解決: brタグを改行に置換して分割処理
for br in cell.find_all('br'):
    br.replace_with('\n')

for line in text.split('\n'):
    # 各行を個別に処理
```

2. **NaNと0.0の扱い**
```python
# 重要: 欠損データはNaNのまま保持（0.0に変換しない）
values = pd.to_numeric(values, errors='coerce')
# fillna(0.0)は削除
```

3. **馬IDの扱い**
- `netkeiba_horse_id`: Netkeibaの馬ID（文字列）
- `horse_id`: アプリ内の馬ID（整数）
- 照合方法: `race_id + horse_number` で特定

---

### Phase 3: サービス層実装

#### race_result_service.py

**主要メソッド**:

```python
class RaceResultService:
    async def fetch_and_save_race_result(race_id: int)
        # スクレイピング → DB保存
    
    async def get_race_result(race_id: int)
        # 保存済み結果取得（リレーション込み）
    
    async def get_race_result_summary(race_id: int)
        # フロントエンド用サマリー
    
    async def check_race_result_exists(race_id: int)
        # 結果存在確認
```

**馬IDの照合ロジック**:
```python
async def _find_horse_by_number(race_id: int, horse_number: int):
    stmt = select(Horse.id).where(
        and_(
            Horse.race_id == race_id,
            Horse.horse_number == horse_number
        )
    )
```

**最新予測のみ取得**:
- 複数回予測実行時は最新の予測結果のみを返す
- `prediction_date.desc()` でソート

---

### Phase 4: API実装

#### race_results.py（エンドポイント）

**実装したAPI**:

| エンドポイント | メソッド | 用途 |
|--------------|---------|------|
| `/api/race-results/fetch/{race_id}` | POST | レース結果取得・保存（バックグラウンド） |
| `/api/race-results/{race_id}` | GET | 保存済み結果取得 |
| `/api/race-results/summary/{race_id}` | GET | サマリー取得 |
| `/api/race-results/exists/{race_id}` | GET | 存在確認 |

**バックグラウンド処理**:
```python
@router.post("/fetch/{race_id}")
async def fetch_race_result(
    race_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    background_tasks.add_task(
        _fetch_and_save_in_background,
        race_id,
        race.netkeiba_race_id
    )
```

---

### Phase 5: フロントエンド実装

#### 型定義追加（types/api.ts）

```typescript
export interface RaceResultResponse {
  id: number;
  race_id: number;
  race_status: string;
  result_fetched_at: string;
  horse_results: HorseResult[];
  payouts: Payout[];
}

export interface HorseResult {
  id: number;
  horse_id: number | null;
  horse_name: string | null;
  horse_number: number;
  finish_position: number | null;
  popularity: number | null;
}

export interface Payout {
  id: number;
  bet_type: string | null;
  bet_type_name: string | null;
  winning_numbers: string;
  payout_amount: number;
}
```

#### API通信関数追加（services/api.ts）

```typescript
export const raceResultService = {
  checkResultExists: async (raceId: number): Promise<boolean>
  fetchRaceResult: async (raceId: number): Promise<{...}>
  getRaceResult: async (raceId: number): Promise<RaceResultResponse | null>
  getRaceResultSummary: async (raceId: number): Promise<RaceResultSummaryResponse | null>
}
```

#### カスタムフック（hooks/useRaceResult.ts）

```typescript
export const useRaceResult = () => {
  // 状態
  result: RaceResultResponse | null
  loading: boolean
  error: string | null
  exists: boolean
  fetching: boolean
  
  // アクション
  checkResultExists()
  fetchRaceResult()
  getRaceResult()
  clearError()
  resetState()
}
```

#### 結果表示コンポーネント（RaceResultDisplay.tsx）

**主要機能**:
- 着順表示（1-3着は金・銀・銅メダル）
- 予測との比較（的中/不的中表示）
- 払い戻し表示（シンプルな表形式）

**払い戻し表示**:
```tsx
<table>
  <tbody>
    {/* 単勝: 青色背景 */}
    <tr>
      <td className="bg-blue-600">単勝</td>
      <td>{馬番}</td>
      <td>{払い戻し額}円</td>
    </tr>
    
    {/* 複勝: 赤色背景（rowSpan統合） */}
    <tr>
      <td className="bg-red-600" rowSpan={3}>複勝</td>
      <td>{馬番}</td>
      <td>{払い戻し額}円</td>
    </tr>
  </tbody>
</table>
```

#### RaceDetailPage統合

**追加機能**:
1. レース結果存在確認（ページ読み込み時）
2. 「レース結果を取得」ボタン（結果が未保存の場合）
3. 「レース結果を表示」ボタン（結果が保存済みの場合）
4. 結果表示/非表示切り替え
5. バックグラウンド取得中の表示

---

## ディレクトリ構造（追加・修正ファイル）

```
backend/
├── app/
│   ├── models/
│   │   ├── race_result.py           # 新規
│   │   ├── race.py                  # 修正: race_result リレーション追加
│   │   ├── horse.py                 # 修正: horse_results リレーション追加
│   │   └── prediction.py            # 修正: back_populates 削除
│   ├── services/
│   │   ├── race_result_scraper.py   # 新規
│   │   └── race_result_service.py   # 新規
│   ├── api/endpoints/
│   │   └── race_results.py          # 新規
│   └── schemas/
│       └── race_result.py           # 新規
├── scripts/
│   ├── init_race_results.py         # 新規: マイグレーション
│   ├── test_race_result_scraper.py  # 新規
│   ├── test_race_result_service.py  # 新規
│   └── test_race_results_api.py     # 新規
└── main.py                          # 修正: race_results ルーター追加

frontend/
├── src/
│   ├── types/
│   │   └── api.ts                   # 修正: レース結果型追加
│   ├── services/
│   │   └── api.ts                   # 修正: raceResultService 追加
│   ├── hooks/
│   │   └── useRaceResult.ts         # 新規
│   ├── components/race/
│   │   └── RaceResultDisplay.tsx    # 新規
│   └── pages/
│       └── RaceDetailPage.tsx       # 修正: 結果表示統合
```

---

## トラブルシューティング履歴

### 1. SQLAlchemyリレーションシップエラー

**問題**: `Mapper 'Mapper[Horse(horses)]' has no property 'predictions'`

**原因**: 
- `horse.py` で `predictions` リレーションシップを削除
- `prediction.py` で `back_populates="predictions"` が残っていた

**解決**: 
```python
# prediction.py
horse = relationship("Horse")  # back_populates削除
```

### 2. 払い戻し額の解析エラー

**問題**: 複数の馬番・金額が連結されて異常な値になる

**原因**: `<br>` タグで区切られたデータを正しく分割していない

**解決**:
```python
for br in cell.find_all('br'):
    br.replace_with('\n')

for line in text.split('\n'):
    # 各行を個別処理
```

### 3. 非同期セッション外でのリレーションアクセス

**問題**: `greenlet_spawn has not been called`

**解決**: リレーションシップを明示的に読み込み
```python
await session.refresh(race_result, ['horse_results', 'payouts'])
```

### 4. データベースカラム不足

**問題**: `no such column: horses.netkeiba_horse_id`

**解決**: 
```sql
ALTER TABLE horses ADD COLUMN netkeiba_horse_id VARCHAR(20);
```

---

## テスト実行手順

### バックエンドテスト

```bash
cd backend

# 1. データベース初期化
python -m scripts.init_race_results

# 2. スクレイパーテスト
python -m scripts.test_race_result_scraper

# 3. サービステスト
python -m scripts.test_race_result_service

# 4. サーバー起動
python main.py

# 5. APIテスト（別ターミナル）
python -m scripts.test_race_results_api
```

### フロントエンドテスト

```bash
cd frontend
npm start

# ブラウザで動作確認
# 1. レース詳細画面を開く
# 2. 「レース結果を取得」ボタンをクリック
# 3. 10秒待機後、結果が表示される
# 4. 予測との比較が表示される
```

---

## 完成した機能

### バックエンド
- ✅ データベーススキーマ（4テーブル）
- ✅ Netkeibaスクレイピング（結果・払い戻し）
- ✅ レース結果保存サービス
- ✅ 馬ID照合ロジック
- ✅ REST API（4エンドポイント）
- ✅ バックグラウンド処理

### フロントエンド
- ✅ レース結果型定義
- ✅ API通信関数
- ✅ カスタムフック
- ✅ 結果表示コンポーネント
- ✅ レース詳細画面統合
- ✅ 的中/不的中判定表示
- ✅ シンプルな払い戻し表

---

## 今後の実装予定（優先順位順）

### 短期（次回セッション推奨）

**1. 的中率計算機能**
- レース単位の的中率
- 期間別集計（日別・月別・年別）
- 競馬場別・距離別の分析
- 所要時間: 1-1.5時間

**2. バッチ処理機能**
- 複数レースの結果を一括取得
- スケジュール実行
- 進捗状況の管理UI
- 所要時間: 1時間

**3. 結果一覧画面**
- 過去のレース結果一覧
- フィルタ機能（日付・競馬場・的中/不的中）
- 所要時間: 1時間

### 中期

**4. 投資シミュレーション**
- 投資額入力
- ROI計算
- 累積収支グラフ
- 所要時間: 2時間

**5. 予測精度の可視化**
- 的中率グラフ
- 確率分布の分析
- モデル性能評価
- 所要時間: 2時間

### 長期

**6. 馬連・ワイドなど他券種対応**
- bet_typesの有効化
- スクレイピング拡張
- 払い戻し表示拡張
- 所要時間: 3時間

**7. WebSocket対応**
- リアルタイム進捗通知
- バックグラウンド処理の可視化
- 所要時間: 2時間

---

## 技術的知見

### 1. SQLAlchemyのリレーションシップ

**双方向リレーションは片側で定義**:
```python
# NG: 両方で定義
class Horse:
    predictions = relationship("Prediction", back_populates="horse")

class Prediction:
    horse = relationship("Horse", back_populates="predictions")

# OK: 片側で定義
class Horse:
    pass  # リレーション定義なし

class Prediction:
    horse = relationship("Horse")  # back_populatesなし
```

### 2. LightGBMの欠損値処理

**NaNと0.0は別物**:
- LightGBMはNaNを欠損値として正しく処理
- `fillna(0.0)` は予測結果に大きな影響を与える
- 欠損データは**NaNのまま保持**すること

### 3. 非同期SQLAlchemyのリレーション読み込み

**Eager Loading**:
```python
# selectinload でリレーションを事前読み込み
stmt = (
    select(RaceResult)
    .options(
        selectinload(RaceResult.horse_results),
        selectinload(RaceResult.payouts)
    )
)
```

### 4. Reactのカスタムフック設計

**状態とアクションを分離**:
```typescript
return {
  // 状態（読み取り専用）
  result, loading, error,
  
  // アクション（関数）
  fetchResult, getResult, clearError
}
```

---

## パフォーマンス特性

### レース結果取得時間
- **スクレイピング**: 2-5秒
- **データ保存**: 1秒未満
- **合計**: 3-6秒/レース

### API応答時間
- **存在確認**: 10ms以下
- **結果取得**: 50-100ms
- **バックグラウンド取得**: 非同期（ユーザー待機なし）

---

## セキュリティ・制約事項

### スクレイピング制限
- Rate Limiting: 2秒間隔
- User-Agent偽装
- 最大リトライ: 2回
- タイムアウト: 30秒

### データ整合性
- ユニーク制約: `(race_id, horse_number)`
- 外部キー制約: 全テーブル
- NOT NULL制約: 必須フィールドのみ

---

## 次回セッションで行うこと

### 推奨: 的中率計算機能の実装

**実装内容**:
1. 的中率計算サービス（バックエンド）
   - レース単位の的中/不的中判定
   - 期間別集計（日別・月別・年別）
   - 競馬場別・グレード別の分析

2. 統計情報API（バックエンド）
   - GET `/api/statistics/accuracy?start_date=...&end_date=...`
   - GET `/api/statistics/summary`

3. 統計画面（フロントエンド）
   - 的中率の可視化（グラフ）
   - フィルタ機能
   - ダッシュボード

**所要時間**: 1-1.5時間

---

## 開発環境情報

### バックエンド
- Python 3.10+
- FastAPI
- SQLAlchemy (async)
- aiosqlite
- requests
- beautifulsoup4
- pandas

### フロントエンド
- React 18
- TypeScript 4.9+
- Tailwind CSS
- Axios
- lucide-react

### データベース
- SQLite (開発)
- PostgreSQL (本番想定)

---

**作業期間**: 1日（Day 7）  
**最終状態**: レース結果機能完成  
**コード品質**: TypeScript/ESLint完全準拠  
**動作確認**: エンドツーエンド動作確認済み  
**次回推奨作業**: 的中率計算機能の実装