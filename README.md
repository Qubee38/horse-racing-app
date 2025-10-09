# 競馬予測アプリ

LightGBM機械学習モデルを使用した競馬予測Webアプリケーション

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![React](https://img.shields.io/badge/react-18.0+-blue.svg)

## 概要

Netkeibaからレースデータを取得し、LightGBMモデルで予測を行う競馬予測システムです。
130個の特徴量から各馬の勝利確率・複勝確率・期待値を算出し、レース結果との照合による回収率分析、AI解説生成機能を提供します。

## 主要機能

### 🏇 予測機能
- **レース予測**: 勝利確率・複勝確率・期待値の算出
- **特徴量エンジニアリング**: 130特徴量から101モデル入力特徴量への変換
- **バッチ予測**: 複数レースの一括予測実行

### 📊 結果分析
- **レース結果取得**: Netkeibaからの自動取得
- **的中判定**: 予測との照合
- **回収率統計**: 確率閾値ベースの投資シミュレーション
- **日別・レース別集計**: 馬数ベースの詳細統計

### 🤖 AI機能
- **AI解説生成**: Claude APIによる当日レースの解説
- **注目情報抽出**: 圧倒的本命・鉄板複勝の自動検出
- **おすすめレース選定**: スコアリングによる推奨レース表示

### 🎨 UI/UX
- **レスポンシブデザイン**: Tailwind CSSによるモダンなUI
- **インタラクティブ**: ソート機能、展開/折りたたみ、ナビゲーション
- **リアルタイム進捗表示**: 予測実行・結果取得の詳細表示

## 技術スタック

### フロントエンド
- **React** 18.0+ - UIライブラリ
- **TypeScript** 4.9+ - 型安全な開発
- **Tailwind CSS** - スタイリング
- **Axios** - HTTP通信
- **Lucide React** - アイコン

### バックエンド
- **FastAPI** - 非同期Webフレームワーク
- **SQLAlchemy** - ORM（非同期対応）
- **Pydantic** - データバリデーション
- **Uvicorn** - ASGIサーバー

### データベース
- **SQLite** - 開発環境
- **PostgreSQL** - 本番環境推奨

### 機械学習
- **LightGBM** - 予測モデル（勝利・複勝）
- **Pandas** - データ処理
- **NumPy** - 数値計算

### データ取得
- **Selenium** - 動的Webスクレイピング
- **BeautifulSoup4** - HTML解析
- **Requests** - HTTP通信（フォールバック）

### AI
- **Anthropic Claude API** - AI解説生成（Sonnet 4.5）

## セットアップ手順

### 前提条件
- Python 3.10以上
- Node.js 18以上
- npm または yarn

### 1. リポジトリのクローン
```bash
git clone https://github.com/your-username/horse-racing-app.git
cd horse-racing-app
```

### 2. バックエンドのセットアップ
```bash
cd backend

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化（Windows）
venv\Scripts\activate
# 仮想環境の有効化（Mac/Linux）
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPIキーなどを設定
```

### 3. データベースの初期化
```bash
python scripts/init_database.py
```

### 4. 必須データファイルの配置
以下のファイルが`data/`ディレクトリに存在することを確認：
```
data/
├── models/
│   ├── win_model.txt
│   └── place_model.txt
├── reference/
│   ├── jockey_win_rate.csv
│   └── standard_deviation.csv
```

### 5. フロントエンドのセットアップ
```bash
cd ../frontend

# 依存関係のインストール
npm install

# 環境変数の設定（任意）
# .env.local を作成して API_BASE_URL を設定
echo "REACT_APP_API_BASE_URL=http://localhost:8000" > .env.local
```

## 起動方法

### 開発環境

#### バックエンド起動
```bash
cd backend
python main.py
```
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### フロントエンド起動
```bash
cd frontend
npm start
```
- アプリ: http://localhost:3000

### 本番環境

#### バックエンド
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### フロントエンド
```bash
cd frontend
npm run build
# buildフォルダをWebサーバーにデプロイ
```

## 環境変数

### バックエンド（backend/.env）
```
DATABASE_URL=sqlite:///./data/horse_racing.db
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:3000
```

### フロントエンド（frontend/.env.local）
```
REACT_APP_API_BASE_URL=http://localhost:8000
```

## API エンドポイント

### レース関連
- `GET /api/races/available-dates` - 開催日一覧取得
- `GET /api/races/{date}` - 日別レース一覧取得
- `GET /api/races/{race_id}/horses` - 出走馬一覧取得
- `GET /api/races/netkeiba/{date}` - Netkeibaから直接レース一覧取得
- `DELETE /api/races/{race_id}` - レース削除

### 予測関連
- `POST /api/predictions/execute` - 日別予測実行
- `POST /api/predictions/execute-race` - 単一レース予測実行
- `POST /api/predictions/execute-selected-races` - 選択レース予測実行
- `GET /api/predictions/model/info` - モデル情報取得

### レース結果関連
- `POST /api/race-results/fetch/{race_id}` - レース結果取得
- `PUT /api/race-results/refetch/{race_id}` - レース結果再取得
- `POST /api/race-results/batch-fetch/{date}` - 日別一括取得
- `GET /api/race-results/{race_id}` - レース結果取得（保存済み）
- `GET /api/race-results/summary/{race_id}` - レース結果サマリー
- `GET /api/race-results/exists/{race_id}` - レース結果存在確認

### 統計関連
- `GET /api/statistics` - 統計情報取得
- `GET /api/statistics/accuracy` - 的中率統計

### AI解説関連
- `GET /api/races/{date}/ai-commentary` - AI解説生成
- `GET /api/admin/ai-commentary/config` - AI解説設定取得
- `PUT /api/admin/ai-commentary/config` - AI解説設定更新

## プロジェクト構造

```
horse-racing-app/
├── frontend/                    # React フロントエンド
│   ├── public/
│   ├── src/
│   │   ├── components/          # UIコンポーネント
│   │   │   ├── common/          # 共通コンポーネント
│   │   │   ├── race/            # レース関連コンポーネント
│   │   │   ├── statistic/       # 統計関連コンポーネント
│   │   │   └── horse/           # 馬関連コンポーネント
│   │   ├── pages/               # ページコンポーネント
│   │   ├── hooks/               # カスタムフック
│   │   ├── services/            # API通信
│   │   ├── contexts/            # React Context
│   │   ├── types/               # TypeScript型定義
│   │   └── utils/               # ユーティリティ
│   └── package.json
├── backend/                     # FastAPI バックエンド
│   ├── app/
│   │   ├── api/                 # APIエンドポイント
│   │   │   └── endpoints/       # 各種エンドポイント
│   │   ├── core/                # コア設定
│   │   ├── models/              # SQLAlchemyモデル
│   │   ├── schemas/             # Pydanticスキーマ
│   │   ├── services/            # ビジネスロジック
│   │   ├── ml/                  # 機械学習関連
│   │   │   ├── predictor.py     # 予測エンジン
│   │   │   ├── feature_engineering.py
│   │   │   ├── feature_processor.py
│   │   │   └── scraper_integration.py
│   │   └── config/              # 設定管理
│   ├── data/                    # データディレクトリ
│   │   ├── models/              # LightGBMモデル
│   │   ├── reference/           # 参照データ
│   │   ├── config/              # 設定ファイル
│   │   ├── race_input/          # スクレイピング結果
│   │   └── horse_racing.db      # SQLiteデータベース
│   ├── scripts/                 # 管理スクリプト
│   ├── main.py                  # アプリケーションエントリーポイント
│   └── requirements.txt
├── .gitignore
└── README.md
```

## 注意事項

- Netkeibaの利用規約を遵守してください
- スクレイピング時は適切な間隔（2-5秒）を設けてサーバー負荷を考慮してください
- 本アプリケーションは教育・勉強目的での使用を想定しています
- 実際の馬券購入における損失について、開発者は一切の責任を負いません

## トラブルシューティング

### データベース初期化エラー
```bash
# データベースファイルを削除して再作成
rm data/horse_racing.db
python backend/scripts/init_database.py
```

### スクレイピングエラー
- Chromeドライバーのバージョンを確認
- User-Agent設定を確認
- ネットワーク接続を確認

### API接続エラー
- バックエンドが起動していることを確認
- CORS設定を確認
- 環境変数を確認