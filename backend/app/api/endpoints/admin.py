# backend/app/api/endpoints/admin.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from app.config.ai_commentary_config import (
    ai_commentary_config,
    save_config_to_file,
    AICommentaryConfig
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class AICommentaryConfigUpdate(BaseModel):
    """AI解説設定の更新リクエスト"""
    overwhelming_favorite_gap: float = Field(ge=5.0, le=30.0, description="圧倒的本命の判定基準（5-30）")
    safe_place_bet_threshold: float = Field(ge=70.0, le=100.0, description="鉄板複勝の判定基準（70-100）")
    grade_race_scores: Dict[str, int] = Field(description="重賞レースのスコア")
    overwhelming_favorite_score: int = Field(ge=0, le=10, description="本命明確スコア（0-10）")
    max_recommended_races: int = Field(ge=1, le=10, description="おすすめレース最大数（1-10）")
    max_tokens: int = Field(ge=1000, le=4000, description="最大トークン数（1000-4000）")

class AICommentaryConfigResponse(BaseModel):
    """AI解説設定のレスポンス"""
    overwhelming_favorite_gap: float
    safe_place_bet_threshold: float
    grade_race_scores: Dict[str, int]
    overwhelming_favorite_score: int
    max_recommended_races: int
    claude_model: str
    max_tokens: int
    system_prompt: str

@router.get("/admin/ai-commentary/config", response_model=AICommentaryConfigResponse)
async def get_ai_commentary_config():
    """
    AI解説設定を取得
    """
    try:
        return AICommentaryConfigResponse(
            overwhelming_favorite_gap=ai_commentary_config.overwhelming_favorite_gap,
            safe_place_bet_threshold=ai_commentary_config.safe_place_bet_threshold,
            grade_race_scores=ai_commentary_config.grade_race_scores,
            overwhelming_favorite_score=ai_commentary_config.overwhelming_favorite_score,
            max_recommended_races=ai_commentary_config.max_recommended_races,
            claude_model=ai_commentary_config.claude_model,
            max_tokens=ai_commentary_config.max_tokens,
            system_prompt=ai_commentary_config.system_prompt
        )
    except Exception as e:
        logger.error(f"Failed to get AI commentary config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/admin/ai-commentary/config")
async def update_ai_commentary_config(config_update: AICommentaryConfigUpdate):
    """
    AI解説設定を更新
    """
    try:
        # グローバル設定を更新
        ai_commentary_config.overwhelming_favorite_gap = config_update.overwhelming_favorite_gap
        ai_commentary_config.safe_place_bet_threshold = config_update.safe_place_bet_threshold
        ai_commentary_config.grade_race_scores = config_update.grade_race_scores
        ai_commentary_config.overwhelming_favorite_score = config_update.overwhelming_favorite_score
        ai_commentary_config.max_recommended_races = config_update.max_recommended_races
        ai_commentary_config.max_tokens = config_update.max_tokens
        
        # ファイルに保存
        save_config_to_file(ai_commentary_config)
        
        logger.info("AI commentary config updated successfully")
        
        return {
            "success": True,
            "message": "設定を更新しました",
            "config": AICommentaryConfigResponse(
                overwhelming_favorite_gap=ai_commentary_config.overwhelming_favorite_gap,
                safe_place_bet_threshold=ai_commentary_config.safe_place_bet_threshold,
                grade_race_scores=ai_commentary_config.grade_race_scores,
                overwhelming_favorite_score=ai_commentary_config.overwhelming_favorite_score,
                max_recommended_races=ai_commentary_config.max_recommended_races,
                claude_model=ai_commentary_config.claude_model,
                max_tokens=ai_commentary_config.max_tokens,
                system_prompt=ai_commentary_config.system_prompt
            )
        }
    
    except Exception as e:
        logger.error(f"Failed to update AI commentary config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/ai-commentary/config/reset")
async def reset_ai_commentary_config():
    """
    AI解説設定をデフォルトに戻す
    """
    try:
        # デフォルト設定を作成
        default_config = AICommentaryConfig()
        
        # グローバル設定を更新
        ai_commentary_config.overwhelming_favorite_gap = default_config.overwhelming_favorite_gap
        ai_commentary_config.safe_place_bet_threshold = default_config.safe_place_bet_threshold
        ai_commentary_config.grade_race_scores = default_config.grade_race_scores
        ai_commentary_config.overwhelming_favorite_score = default_config.overwhelming_favorite_score
        ai_commentary_config.max_recommended_races = default_config.max_recommended_races
        ai_commentary_config.max_tokens = default_config.max_tokens
        
        # ファイルに保存
        save_config_to_file(ai_commentary_config)
        
        logger.info("AI commentary config reset to default")
        
        return {
            "success": True,
            "message": "設定をデフォルトに戻しました"
        }
    
    except Exception as e:
        logger.error(f"Failed to reset AI commentary config: {e}")
        raise HTTPException(status_code=500, detail=str(e))