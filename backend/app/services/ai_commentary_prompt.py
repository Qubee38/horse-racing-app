# backend/app/services/ai_commentary_prompt.py

from typing import List, Dict, Any
from app.config.ai_commentary_config import ai_commentary_config

def generate_prompt(date: str, recommended_races: List[Dict], highlights: List[Dict]) -> str:
    """Claudeに渡すプロンプトを生成"""
    prompt = f"""# {date} 競馬予想解説

## 本日のおすすめレース
{format_recommended_races(recommended_races)}

## 注目ポイント
{format_highlights(highlights)}

上記の情報を元に、以下の形式で解説を生成してください：

### 1. 本日の総評（100文字程度）
今日のレース全体の特徴や見どころ

### 2. おすすめレース詳細（各レース200文字程度）
各おすすめレースについて：
- レースの特徴
- 本命馬とその理由
- 対抗馬の評価
- 購入戦略の提案（単勝・複勝など堅実な買い方中心）

### 3. 今日の狙い目（100文字程度）
本日特に注目すべきポイント
"""
    return prompt


def format_recommended_races(races: List[Dict]) -> str:
    """おすすめレース情報を整形"""
    if not races:
        return "（本日は特におすすめのレースはありません）"
    
    formatted = []
    for idx, race_info in enumerate(races, 1):
        race = race_info['race']
        reasons = ', '.join(race_info['reasons']) if race_info['reasons'] else '注目レース'
        horses = race_info.get('horses', [])
        
        # 上位3頭
        top3 = sorted(horses, key=lambda h: h.win_probability or 0, reverse=True)[:3]
        
        horses_info = '\n'.join([
            f"  - {h.name}（{h.frame_number}枠{h.horse_number}番）"
            f"勝率{h.win_probability:.1f}% 複勝率{h.place_probability:.1f}%"
            for h in top3 if h.name
        ])
        
        formatted.append(f"""
【レース{idx}】{race.venue} {race.race_number}R {race.race_name}
- 距離: {race.distance}m ({race.surface})
- 馬場: {race.track_condition or '不明'}
- 注目理由: {reasons}
- 上位予想:
{horses_info if horses_info else '  （データなし）'}
""")
    
    return '\n'.join(formatted)


def format_highlights(highlights: List[Dict]) -> str:
    """ハイライト情報を整形"""
    if not highlights:
        return "（特になし）"
    
    formatted = []
    
    for highlight in highlights:
        if highlight['type'] == 'overwhelming_favorite':
            h = highlight['horse']
            race = h.race
            formatted.append(
                f"・圧倒的本命: {race.venue}{race.race_number}R "
                f"{h.name}（勝率{h.win_probability:.1f}%、"
                f"2位と{highlight['gap']:.1f}ポイント差）"
            )
        
        elif highlight['type'] == 'safe_place_bet':
            horses_list = highlight['horses']
            if horses_list:
                h = horses_list[0]
                race = h.race
                formatted.append(
                    f"・鉄板複勝候補: {race.venue}{race.race_number}R "
                    f"{h.name}（複勝率{h.place_probability:.1f}%）"
                )
    
    return '\n'.join(formatted)