# backend/scripts/model_evaluation/__init__.py

"""
モデル評価パッケージ

既存の学習モデル（win_model.txt + place_model.txt）を使用して、
任意期間の全レースで投資した場合の回収率を評価します。

主要モジュール:
    - config: 評価設定
    - payback_parser: 払い戻し情報CSV解析
    - data_loader: データ収集・キャッシュ管理
    - evaluator: 評価ロジック
    - analyzer: 条件別分析
    - reporter: レポート出力

使用方法:
    python -m scripts.run_model_evaluation
"""

__version__ = "1.0.0"
__author__ = "Horse Racing Prediction Team"

from .config import EvaluationConfig
from .payback_parser import PaybackParser, PaybackInfo
from .data_loader import DataLoader, RaceData
from .evaluator import Evaluator, StrategyResult, BetResult
from .reporter import Reporter

__all__ = [
    'EvaluationConfig',
    'PaybackParser',
    'PaybackInfo',
    'DataLoader',
    'RaceData',
    'Evaluator',
    'StrategyResult',
    'BetResult',
    'ConditionalAnalyzer',
    'Reporter',
]