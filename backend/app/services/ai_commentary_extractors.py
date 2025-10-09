# backend/app/services/ai_commentary_extractors.py

from typing import List, Optional, Dict, Any
from app.models.race import Race
from app.models.horse import Horse
from app.models.prediction import Prediction
from app.config.ai_commentary_config import ai_commentary_config
import logging

logger = logging.getLogger(__name__)

# ===== 馬データ型（予測結果含む） =====
class HorseWithPrediction:
    """出走馬 + 予測結果のデータクラス"""
    def __init__(self, horse: Horse, prediction: Optional[Prediction] = None):
        self.id = horse.id
        self.race = horse.race
        self.name = horse.name
        self.jockey = horse.jockey
        self.frame_number = horse.frame_number
        self.horse_number = horse.horse_number
        self.odds = horse.odds
        self.weight = horse.weight
        self.weight_change = horse.weight_change
        self.handicap = horse.handicap
        
        # 予測結果
        if prediction:
            self.win_probability = prediction.win_probability
            self.place_probability = prediction.place_probability
            self.expected_value = prediction.expected_value
            self.model_version = prediction.model_version
        else:
            self.win_probability = 0.0
            self.place_probability = 0.0
            self.expected_value = 0.0
            self.model_version = None


# ===== 高確率馬の抽出 =====

def extract_overwhelming_favorite(horses: List[HorseWithPrediction]) -> Optional[Dict[str, Any]]:
    """
    圧倒的本命の抽出
    1着確率が2位と{overwhelming_favorite_gap}以上差がある馬
    """
    if len(horses) < 2:
        return None
    
    sorted_horses = sorted(horses, key=lambda h: h.win_probability or 0, reverse=True)
    top = sorted_horses[0]
    second = sorted_horses[1]
    
    gap = (top.win_probability or 0) - (second.win_probability or 0)
    threshold = ai_commentary_config.overwhelming_favorite_gap
    
    if gap >= threshold:
        return {
            'type': 'overwhelming_favorite',
            'horse': top,
            'gap': gap
        }
    return None

# def extract_safe_win_bet(horses: List[HorseWithPrediction]) -> Optional[Dict[str, Any]]:
#     """
#     鉄板複勝候補の抽出
#     1着確率が90%以上の馬
#     """
#     threshold = ai_commentary_config.safe_win_bet_threshold
#     safe_horses = [h for h in horses if (h.place_probability or 0) >= threshold]
    
#     if safe_horses:
#         return {
#             'type': 'safe_place_bet',
#             'horses': safe_horses
#         }
#     return None


def extract_safe_place_bet(horses: List[HorseWithPrediction]) -> Optional[Dict[str, Any]]:
    """
    鉄板複勝候補の抽出
    3着以内確率が{safe_place_bet_threshold}%以上の馬
    """
    threshold = ai_commentary_config.safe_place_bet_threshold
    safe_horses = [h for h in horses if (h.place_probability or 0) >= threshold]
    
    if safe_horses:
        return {
            'type': 'safe_place_bet',
            'horses': safe_horses
        }
    return None


# TODO: オッズ取得後に実装
def extract_dark_horse(horses: List[HorseWithPrediction]) -> Optional[Dict[str, Any]]:
    """TODO: 高確率穴馬の抽出（オッズ取得後に有効化）"""
    return None


def extract_high_value_horses(horses: List[HorseWithPrediction]) -> Optional[Dict[str, Any]]:
    """TODO: 高期待値馬の抽出（オッズ取得後に有効化）"""
    return None


# ===== レース特徴の抽出 =====

def extract_race_characteristics(race: Race, horses: List[HorseWithPrediction]) -> List[Dict[str, Any]]:
    """レースの特徴的な要素を抽出"""
    characteristics = []
    
    # 重賞レースかどうか
    race_name = race.race_name or ""
    for grade in ['G1', 'G2', 'G3']:
        if grade in race_name:
            characteristics.append({
                'type': 'grade_race',
                'grade': grade
            })
            break
    
    # 馬場状態が特殊
    if race.track_condition in ['重', '不良']:
        characteristics.append({
            'type': 'heavy_track',
            'condition': race.track_condition
        })
    
    # 多頭数レース
    if len(horses) >= 16:
        characteristics.append({
            'type': 'large_field',
            'count': len(horses)
        })
    
    # 距離が特殊
    distance = race.distance or 0
    if distance > 0:
        if distance <= 1200:
            characteristics.append({'type': 'sprint', 'distance': distance})
        elif distance >= 2400:
            characteristics.append({'type': 'long_distance', 'distance': distance})
    
    return characteristics


# ===== おすすめレース選定 =====

def select_recommended_races(races: List[Race]) -> List[Dict[str, Any]]:
    """
    その日のレースから特におすすめのレースを選定
    設定値に基づいてスコアリング
    """
    config = ai_commentary_config
    scored_races = []
    
    for race in races:
        score = 0
        reasons = []
        
        # 馬データを取得（予測結果含む）
        horses = []
        if race.horses:
            for horse in race.horses:
                # 最新の予測結果を取得
                prediction = None
                if horse.predictions:
                    sorted_predictions = sorted(
                        horse.predictions, 
                        key=lambda p: p.prediction_date, 
                        reverse=True
                    )
                    prediction = sorted_predictions[0] if sorted_predictions else None
                
                horses.append(HorseWithPrediction(horse, prediction))
        
        # スコアリング
        race_name = race.race_name or ""
        
        # 1. 重賞レース
        for grade, grade_score in config.grade_race_scores.items():
            if grade in race_name:
                score += grade_score
                reasons.append(f'{grade}重賞')
                break
        
        # 2. 圧倒的本命あり
        if extract_overwhelming_favorite(horses):
            score += config.overwhelming_favorite_score
            reasons.append('本命明確')
        
        scored_races.append({
            'race': race,
            'score': score,
            'reasons': reasons,
            'horses': horses
        })
    
    # スコア順にソート
    sorted_races = sorted(scored_races, key=lambda r: r['score'], reverse=True)
    return sorted_races[:config.max_recommended_races]