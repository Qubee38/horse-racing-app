# backend/app/api/endpoints/ai_commentary.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.ai_commentary_service import AICommentaryService
from app.services.race_service import RaceService
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/races/{date}/ai-commentary")
async def get_daily_ai_commentary(
    date: str,
    db: AsyncSession = Depends(get_db)
):
    """
    指定日のAI予想解説を取得
    
    Args:
        date: YYYY-MM-DD形式の日付
    
    Returns:
        {
            "date": "2024-03-15",
            "commentary": "本日の総評...",
            "recommended_races": [...],
            "highlights_count": 5,
            "model_used": "claude-sonnet-4-5-20250929",
            "config_used": {...}
        }
    """
    try:
        # 日付フォーマット検証
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # レースデータ取得（予測結果込み）
        race_service = RaceService(db)
        races = await race_service.get_races_by_date_with_predictions(date_obj)
        
        if not races:
            raise HTTPException(
                status_code=404, 
                detail=f"No races found for date: {date}"
            )
        
        # 予測結果がないレースをチェック
        races_with_predictions = [
            r for r in races 
            if r.horses and any(h.predictions for h in r.horses)
        ]
        
        if not races_with_predictions:
            raise HTTPException(
                status_code=404,
                detail=f"No prediction results found for date: {date}. Please execute prediction first."
            )
        
        logger.info(f"Generating AI commentary for {date} with {len(races_with_predictions)} races")
        
        # AI解説生成
        ai_service = AICommentaryService()
        commentary = await ai_service.generate_daily_commentary(date, races_with_predictions)
        
        return commentary
    
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=500, detail="API configuration error. Please check ANTHROPIC_API_KEY.")
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error generating AI commentary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))