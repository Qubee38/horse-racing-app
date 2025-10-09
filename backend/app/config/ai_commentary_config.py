# backend/app/config/ai_commentary_config.py

from pydantic_settings import BaseSettings
from typing import Dict, Optional
import json
import os
from pathlib import Path

class AICommentaryConfig(BaseSettings):
    """AI解説生成の設定"""
    
    # ===== 注目情報抽出の閾値 =====
    overwhelming_favorite_gap: float = 15.0
    safe_place_bet_threshold: float = 90.0
    
    # ===== レース選定のスコアリング設定 =====
    grade_race_scores: Dict[str, int] = {
        "G1": 10,
        "G2": 7,
        "G3": 5
    }
    
    overwhelming_favorite_score: int = 2
    max_recommended_races: int = 3
    
    # ===== Claude API設定 =====
    claude_model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 2000
    
    system_prompt: str = """あなたは競馬予想の専門家です。
機械学習モデルの予測結果を元に、初心者にもわかりやすく
レースの見どころと購入戦略を解説してください。

【解説の方針】
- 親しみやすく、わかりやすい言葉で説明
- 予測の根拠を明確に示す
- リスクとリターンのバランスを考慮
- 具体的な購入プランを提示

【避けるべき表現】
- 「絶対」「確実」などの断定的表現
- 過度に射幸心を煽る表現
- 専門用語の過度な使用
"""
    
    class Config:
        env_file = None
        env_prefix = "AI_COMMENTARY_"
        extra = "ignore"

# 設定ファイルのパス
CONFIG_FILE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "config" / "ai_commentary_config.json"

def load_config_from_file() -> AICommentaryConfig:
    """JSONファイルから設定を読み込み"""
    if CONFIG_FILE_PATH.exists():
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return AICommentaryConfig(**data)
        except Exception as e:
            print(f"Failed to load config from file: {e}")
    
    return AICommentaryConfig()

def save_config_to_file(config: AICommentaryConfig):
    """設定をJSONファイルに保存"""
    CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    config_dict = {
        "overwhelming_favorite_gap": config.overwhelming_favorite_gap,
        "safe_place_bet_threshold": config.safe_place_bet_threshold,
        "grade_race_scores": config.grade_race_scores,
        "overwhelming_favorite_score": config.overwhelming_favorite_score,
        "max_recommended_races": config.max_recommended_races,
        "claude_model": config.claude_model,
        "max_tokens": config.max_tokens,
        "system_prompt": config.system_prompt
    }
    
    with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)

# グローバルインスタンス（ファイルから読み込み）
ai_commentary_config = load_config_from_file()