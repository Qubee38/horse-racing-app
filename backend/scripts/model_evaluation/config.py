# backend/scripts/model_evaluation/config.py

from datetime import date
from pathlib import Path
from typing import List, Dict

class EvaluationConfig:
    """モデル評価の設定"""
    
    # ========================================
    # プロジェクト構造
    # ========================================
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
    DATA_DIR = BASE_DIR / "data"
    
    # ========================================
    # 評価期間（使用しない - schedule.jsonから決定）
    # ========================================
    # START_DATE と END_DATE は schedule.json から自動決定されるため、
    # ここでの定義は参考値として残す
    START_DATE = date(2025, 1, 1)
    END_DATE = date(2025, 12, 31)
    
    # ========================================
    # モデル設定
    # ========================================
    WIN_MODEL_PATH = DATA_DIR / "models" / "win_model.txt"
    PLACE_MODEL_PATH = DATA_DIR / "models" / "place_model.txt"
    
    # ========================================
    # 投資戦略設定
    # ========================================
    # 基本投資額（円）
    BASE_BET_AMOUNT = 100
    
    # 予想順位ベース
    RANK_BASED = {
        "win": {
            "top_n": 1  # 予測1位の馬
        },
        "place": {
            "top_n": 3  # 予測上位3頭
        }
    }
    
    # 確率閾値ベース
    PROBABILITY_THRESHOLDS = {
        "win": {
            "win_model": [80, 83, 87],    # win_modelの閾値
            "place_model": [80, 83, 87]   # place_modelの閾値
        },
        "place": {
            "win_model": [80, 85, 90],    # win_modelの閾値
            "place_model": [80, 85, 90]   # place_modelの閾値
        }
    }
    
    # ========================================
    # データパス設定
    # ========================================
    # スクレイピング結果（既存データ）
    RACE_INPUT_DIR = DATA_DIR / "race_input"
    
    # 払い戻し情報ディレクトリ（年別管理）
    PAYBACK_DIR = DATA_DIR / "payback"
    
    # モデル評価用ディレクトリ
    EVALUATION_DIR = DATA_DIR / "evaluation"

    # スケジュールディレクトリ（schedule.json配置場所）
    SCHEDULE_DIR = EVALUATION_DIR / "schedules"

    # レースIDディレクトリ（生成されたrace_id.csv配置場所）
    RACE_ID_DIR = EVALUATION_DIR / "race_ids"

    # キャッシュディレクトリ
    CACHE_DIR = EVALUATION_DIR / "cache"
    
    # レポート出力ディレクトリ
    REPORT_DIR = EVALUATION_DIR / "result_reports"
    
    # ログディレクトリ
    LOG_DIR = EVALUATION_DIR / "logs"
    
    # ========================================
    # スクレイピング設定
    # ========================================
    # 既存データ優先使用
    USE_EXISTING_DATA = True
    
    # 既存データを無視して強制再取得
    FORCE_RESCRAPE = False
    
    # レース間待機時間（秒）
    DELAY_BETWEEN_REQUESTS = 5.0
    
    # キャッシュ使用
    USE_CACHE = True
    
    # 払い戻し情報スクレイピング
    SCRAPE_MISSING_PAYBACK = True  # 不足分を自動スクレイピング
    
    # ========================================
    # 条件別分析設定
    # ========================================
    # 条件別分析を実行するか
    ENABLE_CONDITIONAL_ANALYSIS = True
    
    # 競馬場リスト
    VENUES = ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]
    
    # グレードマッピング（StatisticsPageと同じ）
    GRADE_MAPPING = {
        "0": "障害", "1": "未勝利", "2": "1勝", "3": "新馬",
        "4": "1勝", "5": "2勝", "6": "3勝", "7": "OP",
        "8": "G3", "9": "G2", "10": "G1"
    }
    
    # 馬場種別
    TRACK_TYPES = ["芝", "ダート"]
    
    # 距離範囲（メートル）
    DISTANCE_RANGES = [
        ("1000m-1400m", 1000, 1400),
        ("1400m-1800m", 1401, 1800),
        ("1800m-2200m", 1801, 2200),
        ("2200m以上", 2201, 9999)
    ]
    
    # 馬場状態
    TRACK_CONDITIONS = ["良", "稍", "重", "不良"]
    
    # ========================================
    # 出力設定
    # ========================================
    # CSV出力フォーマット
    CSV_ENCODING = "utf-8-sig"  # Excel対応
    
    # レポート名プレフィックス
    REPORT_PREFIX = "model_evaluation"
    
    # タイムスタンプフォーマット
    TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
    
    # ========================================
    # 参照データ
    # ========================================
    JOCKEY_WIN_RATE_CSV = DATA_DIR / "reference" / "jockey_win_rate.csv"
    STANDARD_DEVIATION_CSV = DATA_DIR / "reference" / "standard_deviation.csv"
    
    # ========================================
    # ヘルパーメソッド
    # ========================================
    @classmethod
    def ensure_directories(cls):
        """必要なディレクトリを作成"""
        cls.EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
        cls.SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)
        cls.RACE_ID_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
        cls.PAYBACK_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_payback_csv_path(cls, year: int) -> Path:
        """年別払い戻しCSVのパスを取得"""
        return cls.PAYBACK_DIR / f"payback_{year}.csv"
    
    @classmethod
    def get_schedule_json_path(cls) -> Path:
        """スケジュールJSONのパスを取得"""
        return cls.SCHEDULE_DIR / "schedule.json"
    
    @classmethod
    def get_race_id_csv_path(cls) -> Path:
        """レースID CSVのパスを取得"""
        return cls.RACE_ID_DIR / "race_ids.csv"
    
    @classmethod
    def get_report_filename(cls, report_type: str, timestamp: str = None) -> Path:
        """レポートファイル名を生成"""
        from datetime import datetime
        if timestamp is None:
            timestamp = datetime.now().strftime(cls.TIMESTAMP_FORMAT)
        
        filename = f"{cls.REPORT_PREFIX}_{report_type}_{timestamp}.csv"
        return cls.REPORT_DIR / filename
    
    @classmethod
    def get_log_filename(cls, log_type: str = "evaluation", timestamp: str = None) -> Path:
        """ログファイル名を生成"""
        from datetime import datetime
        if timestamp is None:
            timestamp = datetime.now().strftime(cls.TIMESTAMP_FORMAT)
        
        filename = f"{log_type}_{timestamp}.log"
        return cls.LOG_DIR / filename
    
    @classmethod
    def get_all_thresholds(cls) -> List[Dict]:
        """
        全ての閾値設定を返す
        
        Returns:
            [
                {
                    "bet_type": "win",
                    "model_type": "win_model",
                    "threshold": 80
                },
                ...
            ]
        """
        thresholds = []
        
        for bet_type in ["win", "place"]:
            for model_type in ["win_model", "place_model"]:
                for threshold in cls.PROBABILITY_THRESHOLDS[bet_type][model_type]:
                    thresholds.append({
                        "bet_type": bet_type,
                        "model_type": model_type,
                        "threshold": threshold
                    })
        
        return thresholds
    
    @classmethod
    def validate_config(cls) -> bool:
        """設定の妥当性チェック"""
        errors = []
        
        # モデルファイル存在確認
        if not cls.WIN_MODEL_PATH.exists():
            errors.append(f"Win model not found: {cls.WIN_MODEL_PATH}")
        
        if not cls.PLACE_MODEL_PATH.exists():
            errors.append(f"Place model not found: {cls.PLACE_MODEL_PATH}")
        
        # 参照データ存在確認
        if not cls.JOCKEY_WIN_RATE_CSV.exists():
            errors.append(f"Jockey win rate CSV not found: {cls.JOCKEY_WIN_RATE_CSV}")
        
        if not cls.STANDARD_DEVIATION_CSV.exists():
            errors.append(f"Standard deviation CSV not found: {cls.STANDARD_DEVIATION_CSV}")
        
        # スケジュールファイル存在確認
        if not cls.get_schedule_json_path().exists():
            errors.append(f"Schedule JSON not found: {cls.get_schedule_json_path()}")
        
        if errors:
            print("Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """設定内容を表示"""
        print("=" * 80)
        print("Model Evaluation Configuration")
        print("=" * 80)
        print(f"Win Model: {cls.WIN_MODEL_PATH}")
        print(f"Place Model: {cls.PLACE_MODEL_PATH}")
        print(f"Schedule JSON: {cls.get_schedule_json_path()}")
        print(f"Race ID CSV: {cls.get_race_id_csv_path()}")
        print(f"Payback Directory: {cls.PAYBACK_DIR}")
        print(f"Report Directory: {cls.REPORT_DIR}")
        print(f"\nInvestment Strategies:")
        print(f"  - Rank Based: Top {cls.RANK_BASED['win']['top_n']} for Win, Top {cls.RANK_BASED['place']['top_n']} for Place")
        print(f"  - Probability Thresholds:")
        print(f"    Win: {cls.PROBABILITY_THRESHOLDS['win']}")
        print(f"    Place: {cls.PROBABILITY_THRESHOLDS['place']}")
        print(f"\nData Handling:")
        print(f"  - Use Existing Data: {cls.USE_EXISTING_DATA}")
        print(f"  - Force Rescrape: {cls.FORCE_RESCRAPE}")
        print(f"  - Scrape Missing Payback: {cls.SCRAPE_MISSING_PAYBACK}")
        print(f"  - Conditional Analysis: {cls.ENABLE_CONDITIONAL_ANALYSIS}")
        print("=" * 80)