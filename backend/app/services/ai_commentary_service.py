# backend/app/services/ai_commentary_service.py

from anthropic import Anthropic
from typing import List, Dict, Any
import logging
from app.models.race import Race
from app.config.ai_commentary_config import ai_commentary_config
from app.services.ai_commentary_extractors import (
    extract_overwhelming_favorite,
    extract_safe_place_bet,
    select_recommended_races,
    HorseWithPrediction
)
from app.services.ai_commentary_prompt import generate_prompt
from app.core.config import settings  # ← 追加

logger = logging.getLogger(__name__)

class AICommentaryService:
    def __init__(self):
        # ===== 修正: settingsから取得 =====
        api_key = settings.ANTHROPIC_API_KEY
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in environment variables")
        
        self.client = Anthropic(api_key=api_key)
        self.config = ai_commentary_config
    
    async def generate_daily_commentary(
        self, 
        date: str,
        races: List[Race]
    ) -> Dict[str, Any]:
        """
        日別のAI解説を生成
        """
        try:
            # 1. おすすめレース選定
            recommended_races = select_recommended_races(races)
            logger.info(f"Selected {len(recommended_races)} recommended races for {date}")
            
            # 2. ハイライト抽出
            highlights = self._extract_highlights(races)
            logger.info(f"Extracted {len(highlights)} highlights for {date}")
            
            # 3. プロンプト生成
            prompt = generate_prompt(date, recommended_races, highlights)
            logger.debug(f"Generated prompt length: {len(prompt)} characters")
            
            # 4. Claude API呼び出し
            response = self.client.messages.create(
                model=self.config.claude_model,
                max_tokens=self.config.max_tokens,
                system=self.config.system_prompt,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            commentary_text = response.content[0].text
            logger.info(f"Successfully generated commentary for {date}")
            
            return {
                "date": date,
                "commentary": commentary_text,
                "recommended_races": [
                    {
                        "race_id": r['race'].id,
                        "race_name": r['race'].race_name,
                        "venue": r['race'].venue,
                        "race_number": r['race'].race_number,
                        "score": r['score'],
                        "reasons": r['reasons']
                    }
                    for r in recommended_races
                ],
                "highlights_count": len(highlights),
                "model_used": self.config.claude_model,
                "config_used": {
                    "overwhelming_favorite_gap": self.config.overwhelming_favorite_gap,
                    "safe_place_bet_threshold": self.config.safe_place_bet_threshold,
                    "max_recommended_races": self.config.max_recommended_races
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating commentary for {date}: {str(e)}")
            raise
    
    def _extract_highlights(self, races: List[Race]) -> List[Dict]:
        """全レースからハイライトを抽出"""
        highlights = []
        
        for race in races:
            if not race.horses:
                continue
            
            # 馬データを HorseWithPrediction に変換
            horses = []
            for horse in race.horses:
                prediction = None
                if horse.predictions:
                    sorted_predictions = sorted(
                        horse.predictions, 
                        key=lambda p: p.prediction_date, 
                        reverse=True
                    )
                    prediction = sorted_predictions[0] if sorted_predictions else None
                
                horses.append(HorseWithPrediction(horse, prediction))
            
            # 圧倒的本命
            if favorite := extract_overwhelming_favorite(horses):
                highlights.append(favorite)
            
            # 鉄板複勝
            if safe := extract_safe_place_bet(horses):
                highlights.append(safe)
        
        return highlights