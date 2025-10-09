import os
import csv
import re
import random
import logging
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class NetkeibaRaceScraper:
    """Netkeibaからのレースデータ取得"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.0.0",
    ]
    
    # マッピング定数（既存コードと同じ）
    SHIBA_MAPPING = {'芝': 0, 'ダ': 1, '障': 2}
    MAWARI_MAPPING = {'右': 0, '左': 1, '芝': 2, '直': 3}
    BABA_MAPPING = {'良': 0, '稍': 1, '重': 2, '不': 3}
    TENKI_MAPPING = {'晴': 0, '曇': 1, '小': 2, '雨': 3, '雪': 4}
    LOCATION_MAPPING = {
        "札幌": "01", "函館": "02", "福島": "03", "新潟": "04",
        "東京": "05", "中山": "06", "中京": "07", "京都": "08",
        "阪神": "09", "小倉": "10"
    }
    
    # 既存コードのcolumn_list
    COLUMN_LIST = [
        "race_id","馬","騎手","馬番","走破時間","オッズ","通過順","着順","体重","体重変化","性","齢","斤量","上がり","人気","レース名","日付","開催","クラス","芝・ダート","距離","回り","馬場","天気","場id","場名",
        "日付1","馬番1","騎手1","斤量1","オッズ1","体重1","体重変化1","上がり1","通過順1","着順1","距離1","クラス1","走破時間1","芝・ダート1","天気1","場id1","馬場1","回り1",
        "日付2","馬番2","騎手2","斤量2","オッズ2","体重2","体重変化2","上がり2","通過順2","着順2","距離2","クラス2","走破時間2","芝・ダート2","天気2","場id2","馬場2","回り2",
        "日付3","馬番3","騎手3","斤量3","オッズ3","体重3","体重変化3","上がり3","通過順3","着順3","距離3","クラス3","走破時間3","芝・ダート3","天気3","場id3","馬場3","回り3",
        "日付4","馬番4","騎手4","斤量4","オッズ4","体重4","体重変化4","上がり4","通過順4","着順4","距離4","クラス4","走破時間4","芝・ダート4","天気4","場id4","馬場4","回り4",
        "日付5","馬番5","騎手5","斤量5","オッズ5","体重5","体重変化5","上がり5","通過順5","着順5","距離5","クラス5","走破時間5","芝・ダート5","天気5","場id5","馬場5","回り5",
    ]
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # backend/app/ml/ から ../../../data への相対パス
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            data_dir = os.path.join(project_root, "data")
        
        self.data_dir = data_dir
        self.base_url = "https://race.netkeiba.com/race/shutuba.html?race_id="
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': random.choice(self.USER_AGENTS)})
        
        # データディレクトリ作成
        os.makedirs(os.path.join(self.data_dir, "race_input"), exist_ok=True)
        
        # 時間データ読み込み（既存コードと同じ）
        self.time_data = self._load_time_data()
        
        logger.info(f"Scraper initialized with data dir: {self.data_dir}")
    
    def _load_time_data(self):
        """時間標準化用データを読み込み"""
        try:
            # data/reference/standard_deviation.csv を読み込む
            time_csv_path = os.path.join(self.data_dir, "reference", "standard_deviation.csv")
            logger.info(f"Loading time data from: {time_csv_path}")
            
            if os.path.exists(time_csv_path):
                time_df = pd.read_csv(time_csv_path, index_col=0)
                time_data = (
                    time_df['Mean']['First Time'], 
                    time_df['Mean']['Second Time'],
                    time_df['Standard Deviation']['First Time'], 
                    time_df['Standard Deviation']['Second Time']
                )
                logger.info(f"Time data loaded successfully: {time_data}")
                return time_data
            else:
                logger.warning(f"Time data file not found: {time_csv_path}")
        except Exception as e:
            logger.warning(f"Could not load time data: {e}")
        
        # デフォルト値
        logger.warning("Using default time data values")
        return (120.0, 0.0, 10.0, 1.0)
    
    def scrape_race_data(self, race_id: str) -> Dict:
        """
        レースIDからレースデータを取得（既存コード準拠）
        
        Args:
            race_id: Netkeibaのレース ID
            
        Returns:
            Dict: レース情報と出走馬データ
        """
        try:
            logger.info(f"Scraping race data for race_id: {race_id}")
            
            # レースページを取得
            soup = self._fetch_race_page(race_id)
            
            # レース基本情報を取得
            race_info = self._extract_race_info(soup, race_id)
            
            # 出走馬データを取得（基本情報のみ）
            horses_basic_data = self._extract_horses_basic_data(soup, race_info)
            
            # 過去戦績データを取得（既存コードロジック使用）
            horses_data_with_history = self._fetch_horses_history_legacy(horses_basic_data, race_info['date'])
            
            # CSVファイルとして保存（既存フォーマット）
            csv_path = self._save_to_csv_legacy(race_id, race_info, horses_data_with_history)
            
            return {
                'race_info': race_info,
                'horses_data': horses_data_with_history,
                'csv_path': csv_path
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape race data for {race_id}: {e}")
            raise
    
    def _fetch_race_page(self, race_id: str) -> BeautifulSoup:
        """レースページを取得"""
        url = self.base_url + race_id
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    
    def _extract_race_info(self, soup: BeautifulSoup, race_id: str) -> Dict:
        """レース基本情報を抽出（修正版：レース番号・詳細情報強化）"""
        # レース名
        race_name_element = soup.find("h1", class_="RaceName")
        race_name = race_name_element.text.strip() if race_name_element else ""
        
        # レース日付
        try:
            race_date = re.findall('=(.*)&', soup.find("dd", class_="Active").find("a").attrs['href'])[0]
        except:
            # フォールバック: 現在日付を使用
            race_date = datetime.now().strftime('%Y%m%d')
        
        # === 修正1: レース番号を抽出 ===
        race_number = 1  # デフォルト値
        try:
            # レース番号をURLから抽出（最後の2桁）
            race_number_match = re.search(r'(\d{2})$', race_id)
            if race_number_match:
                race_number = int(race_number_match.group(1))
                logger.info(f"Extracted race number: {race_number} from race_id: {race_id}")
            
            # 代替: レース名からも抽出を試行
            if race_number == 1 and race_name:
                name_race_number_match = re.search(r'(\d+)R', race_name)
                if name_race_number_match:
                    race_number = int(name_race_number_match.group(1))
                    logger.info(f"Extracted race number: {race_number} from race name")
        except Exception as e:
            logger.warning(f"Failed to extract race number: {e}")
        
        # コース情報
        race_data_element = soup.find("div", class_="RaceData01")
        race_text = race_data_element.text if race_data_element else ""
        
        # === 修正2: 発走時刻を抽出 ===
        start_time = "未定"
        try:
            # 発走時刻を RaceData01 から抽出
            time_match = re.search(r'(\d{2}:\d{2})', race_text)
            if time_match:
                start_time = time_match.group(1)
                logger.info(f"Extracted start time: {start_time}")
        except Exception as e:
            logger.warning(f"Failed to extract start time: {e}")
        
        span = race_data_element.find("span").text.strip() if race_data_element and race_data_element.find("span") else ""
        
        # === 修正3: 距離抽出の強化 ===
        distance = "1600"  # デフォルト値
        track_type = 0  # デフォルト値（芝）
        
        if span:
            try:
                distance = span[1:-1]  # 距離
                track_type = self.SHIBA_MAPPING.get(span[0], 0)  # 芝・ダート
                logger.info(f"Extracted distance: {distance}, track_type: {track_type}")
            except Exception as e:
                logger.warning(f"Failed to parse span data: {span}, error: {e}")
        
        # 方向
        direction = re.search(r"(左|右|直|芝)", race_text)
        mawari = self.MAWARI_MAPPING.get(direction.group() if direction else "", 0)
        
        # === 修正4: 天気抽出の強化 ===
        weather = ""
        tenki = 0
        try:
            weather_match = re.search(r"天候[：:](\w+)", race_text) or re.search(r"天気[：:](\w+)", race_text)
            if weather_match:
                weather = weather_match.group(1)
                tenki = self.TENKI_MAPPING.get(weather)
                logger.info(f"Extracted weather: {weather}, tenki: {tenki}")
        except Exception as e:
            logger.warning(f"Failed to extract weather: {e}")
        
        # === 修正5: 馬場状態抽出の強化 ===
        baba_text = ""
        baba = 0
        try:
            # 複数のパターンでバ場状態を検索
            baba_element = soup.find("span", class_="Item03") or soup.find("span", class_="Item04")
            if baba_element:
                baba_text = baba_element.text.strip()[-1] if baba_element.text.strip() else ""
            else:
                # race_textからも検索
                baba_match = re.search(r"馬場[：:]([良稍重不]+)", race_text)
                if baba_match:
                    baba_text = baba_match.group(1)[-1]  # 最後の文字を取得
            
            baba = self.BABA_MAPPING.get(baba_text)
            logger.info(f"Extracted baba: {baba_text}, baba: {baba}")
        except Exception as e:
            logger.warning(f"Failed to extract baba: {e}")
        
        # 開催情報
        race_data2 = soup.find("div", class_="RaceData02")
        spans = race_data2.find_all('span') if race_data2 else []
        location = spans[1].text if len(spans) > 1 else ""
        place_id = self.LOCATION_MAPPING.get(location, "00")
        race_meeting = spans[0].text + spans[1].text + spans[2].text if len(spans) >= 3 else ""
        
        # レースランク
        race_rank = self._extract_race_rank(soup, race_name)
        
        return {
            'race_id': race_id,
            'race_name': race_name,
            'race_number': race_number,  # 追加
            'start_time': start_time,    # 追加
            'date': race_date,
            'distance': distance,
            'track_type': track_type,
            'mawari': mawari,
            'weather': tenki,
            'baba': baba,
            'location': location,
            'place_id': place_id,
            'race_rank': race_rank,
            'race_meeting': race_meeting
        }
    
    def _extract_horses_basic_data(self, soup: BeautifulSoup, race_info: Dict) -> List[Dict]:
        """出走馬基本データを抽出（修正版：枠番追加）"""
        horses_data = []
        
        table = soup.find("table", {"class": "Shutuba_Table"})
        if not table:
            return horses_data
        
        rows = table.find_all("tr")[2:]  # ヘッダー行をスキップ
        
        for i, row in enumerate(rows):
            cols = row.find_all("td")
            if len(cols) < 11:
                continue
            
            # 除外馬をスキップ
            sign = cols[2].text.strip()
            if sign == "除外":
                continue
            
            # === 修正6: 枠番を抽出 ===
            frame_number = 1  # デフォルト値
            try:
                # 枠番は通常0番目のカラムに表示される
                frame_text = cols[0].text.strip()
                if frame_text.isdigit():
                    frame_number = int(frame_text)
                else:
                    # 枠番がない場合は馬番から推測（8枠制の場合）
                    horse_number_int = int(cols[1].text.strip())
                    frame_number = ((horse_number_int - 1) // 2) + 1
                    if frame_number > 8:
                        frame_number = 8
                
                # logger.info(f"Extracted frame number: {frame_number}")
            except Exception as e:
                logger.warning(f"Failed to extract frame number: {e}")
            
            # 基本情報
            horse_number = cols[1].text.strip()
            horse_name = cols[3].text.strip()
            
            # 馬データURL（過去戦績取得用）
            horse_url = cols[3].find('a').get('href') if cols[3].find('a') else ""
            
            # 騎手情報取得（既存コードのロジック使用）
            jockey_name = self._extract_jockey_name_legacy(cols[6])
            
            # オッズと人気
            odds_text = cols[9].find("span").text.strip() if cols[9].find("span") else "0"
            popularity = cols[10].find("span").text.strip() if cols[10].find("span") else "0"
            
            # 体重情報（既存コードロジック）
            horse_weight = cols[8].text.strip()
            weight, weight_change = self._parse_weight_legacy(horse_weight)
            
            # その他情報
            handicap = cols[5].text.strip()  # 斤量
            sex_age = cols[4].text.strip()
            sex = self._map_sex_legacy(sex_age[0] if sex_age else "")
            age = sex_age[1] if len(sex_age) > 1 else "0"
            
            horse_data = {
                'horse_number': horse_number,
                'frame_number': frame_number,  # 追加
                'horse_name': horse_name,
                'jockey': jockey_name,
                'odds': odds_text,
                'popularity': popularity,
                'weight': weight,
                'weight_change': weight_change,
                'handicap': handicap,
                'sex': sex,
                'age': age,
                'horse_url': horse_url,
                # 既存コード準拠の初期値
                'running_time': '',
                'through_order': '',
                'finish_order': '',
                'agari': ''
            }
            
            horses_data.append(horse_data)
        
        return horses_data
    
    def _extract_race_rank(self, soup: BeautifulSoup, race_name: str) -> int:
        """レースランクを抽出（既存コード準拠）"""
        if soup.find("span", class_="Icon_GradeType1"):
            return 10  # G1
        elif soup.find("span", class_="Icon_GradeType2"):
            return 9   # G2
        elif soup.find("span", class_="Icon_GradeType3"):
            return 8   # G3
        elif soup.find("span", class_="Icon_GradeType15"):
            return 7   # L, OP
        elif soup.find("span", class_="Icon_GradeType16"):
            return 6   # 3勝
        elif soup.find("span", class_="Icon_GradeType17"):
            return 5   # 2勝
        elif soup.find("span", class_="Icon_GradeType18"):
            return 4   # 1勝
        else:
            return self._class_mapping(race_name)
    
    def _class_mapping(self, race_name: str) -> int:
        """レース名からクラス判定（既存コード準拠）"""
        mappings = {
            '障害': 0, 'G1': 10, 'G2': 9, 'G3': 8, '(L)': 7, 'オープン': 7, 'OP': 7,
            '3勝': 6, '1600': 6, '2勝': 5, '1000': 5, '1勝': 4, '500': 4,
            '新馬': 3, '未勝利': 1
        }
        for key, value in mappings.items():
            if key in race_name:
                return value
        return 0
    
    def _extract_jockey_name_legacy(self, jockey_cell) -> str:
        """騎手名を抽出・正規化（既存コード準拠）"""
        a_tag = jockey_cell.find('a')
        if not a_tag:
            return ""
        
        try:
            jockey_url = a_tag.get('href')
            response = self.session.get(jockey_url)
            soup = BeautifulSoup(response.content, "html.parser")
            
            element = soup.find("div", class_="db_head_name")
            if element:
                h1_text = element.find('h1').get_text(strip=True)
                name = h1_text.split("\u00a0")[0]
                # 全角英字を除去
                name = re.sub(r'[Ａ-Ｚａ-ｚ．]', '', name)
                # ☆を除去（追加）
                name = name.replace('☆', '')
                return name
        except:
            pass
        
        # フォールバック: セルのテキストから取得
        jockey_name = a_tag.text.strip()
        # ☆を除去（追加）
        jockey_name = jockey_name.replace('☆', '')
        return jockey_name

    def _parse_weight_legacy(self, weight_text: str) -> Tuple[str, str]:
        """体重情報を解析（既存コード準拠）"""
        weight = 0
        weight_change = 0
        
        try:
            weight = int(weight_text.split("(")[0])
        except:
            weight = ''
        
        try:
            weight_change = int(weight_text.split("(")[1][0:-1])
        except:
            weight_change = ''
        
        return str(weight), str(weight_change)
    
    def _map_sex_legacy(self, sex_char: str) -> int:
        """性別をマッピング（既存コード準拠）"""
        sex_mapping = {'牡': 0, '牝': 1, 'セ': 2}
        return sex_mapping.get(sex_char, 0)
    
    def _fetch_horses_history_legacy(self, horses_data: List[Dict], race_date: str) -> List[Dict]:
        """各馬の過去戦績を取得（既存コード完全準拠）"""
        cutoff_date = datetime.strptime(race_date, '%Y%m%d')
        
        for index, horse_data in enumerate(horses_data):
            if not horse_data['horse_url']:
                continue
            
            try:
                # 既存コードのロジックを完全再現
                results = []
                modified_url = horse_data['horse_url'].replace("horse/", "horse/result/")
                response = self.session.get(modified_url)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch history for {horse_data['horse_name']}")
                    continue
                
                soup = BeautifulSoup(response.content, "html.parser")
                table = soup.find("table", {"class": "db_h_race_results nk_tb_common"})
                
                if not table:
                    continue
                
                rows = table.find_all("tr")
                
                # 各行から必要な情報を取り出し（既存コード準拠）
                for i, row in enumerate(rows[1:], start=1):
                    cols = row.find_all("td")
                    if len(cols) < 24:
                        continue
                    
                    # 日付を解析
                    str_date = cols[0].text.strip()
                    try:
                        date = datetime.strptime(str_date, '%Y/%m/%d')
                        # 特定の日付より前のデータのみを取得
                        if date >= cutoff_date:
                            continue
                    except:
                        continue
                    
                    # 既存コードの完全再現
                    result = self._extract_history_record_legacy(cols, str_date)
                    results.append(result)
                    
                    # 5行取得したら終了
                    if len(results) >= 5:
                        break
                
                # 結果をhorse_dataに格納
                horse_data['history_results'] = results
                
            except Exception as e:
                logger.warning(f"Failed to fetch history for {horse_data['horse_name']}: {e}")
                horse_data['history_results'] = []
        
        return horses_data
    
    def _extract_history_record_legacy(self, cols, str_date: str) -> List:
        """過去戦績レコードを抽出（既存コード完全準拠）"""
        # 体重
        horse_weight = cols[24].text.strip()
        weight = 0
        weight_change = 0
        
        try:
            weight = int(horse_weight.split("(")[0])
        except:
            weight = ''
        
        try:
            weight_change = int(horse_weight.split("(")[1][0:-1])
        except:
            weight_change = ''
        
        # 上がり
        agari = cols[23].text.strip()
        
        # 通過順
        through_order = cols[21].text.strip()
        try:
            numbers = list(map(int, through_order.split('-')))
            through_order = sum(numbers) / len(numbers)
        except ValueError:
            through_order = ''
        
        # 着順
        finish_order = cols[11].text.strip()
        try:
            finish_order = str(int(finish_order))
        except ValueError:
            finish_order = ""
        
        # 馬番
        past_horse_number = cols[8].text.strip()
        
        # 騎手
        past_jockey = cols[12].text.strip()
        
        # 斤量
        past_handicap = cols[13].text.strip()
        
        # 距離
        distance_text = cols[14].text.strip()
        
        # 芝・ダート
        track = distance_text[0] if distance_text else ''
        shiba_mapping = {'芝': 0, 'ダ': 1, '障': 2}
        track_mapped = shiba_mapping.get(track, 0)
        
        # 距離
        distance = distance_text[1:] if len(distance_text) > 1 else ''
        
        # レース名
        race_name = cols[4].text.strip()
        race_rank = self._class_mapping(race_name)
        
        # タイム（既存コードの時間標準化ロジック）
        time_text = cols[18].text.strip()
        try:
            time_value = float(time_text.split(':')[0]) * 60 + sum(float(x) / 10**i for i, x in enumerate(time_text.split(':')[1].split('.')))
        except:
            time_value = ''
        
        if time_value != '':
            # 1回目の平均と標準偏差で標準化
            time_value = -((time_value - self.time_data[0]) / self.time_data[2])
            # 外れ値の処理：-3より小さい値は-3に、2.5より大きい値は2.5に変換
            time_value = -3 if time_value < -3 else (2.5 if time_value > 2.5 else time_value)
            # 2回目の平均と標準偏差で標準化
            time_value = (time_value - self.time_data[1]) / self.time_data[3]
        
        # 天気
        weather_text = cols[2].text.strip()
        tenki_mapping = {'晴': 0, '曇': 1, '小': 2, '雨': 3, '雪': 4}
        weather = tenki_mapping.get(weather_text)
        
        # オッズ
        odds = cols[9].text.strip()
        
        # 馬場状態
        track_condition_text = cols[15].text.strip()
        baba_mapping = {'良': 0, '稍': 1, '重': 2, '不': 3}
        track_condition = baba_mapping.get(track_condition_text)
        
        # 競馬場ID、回り（既存コードのロジック完全再現）
        past_location = cols[1].text.strip()[1:3]
        if past_location == "札幌":
            past_place = "01"
            past_mawari = 0
        elif past_location == "函館":
            past_place = "02"
            past_mawari = 0
        elif past_location == "福島":
            past_place = "03"
            past_mawari = 0
        elif past_location == "新潟":
            past_place = "04"
            past_mawari = 1
        elif past_location == "東京":
            past_place = "05"
            past_mawari = 1
        elif past_location == "中山":
            past_place = "06"
            past_mawari = 0
        elif past_location == "中京":
            past_place = "07"
            past_mawari = 1
        elif past_location == "京都":
            past_place = "08"
            past_mawari = 0
        elif past_location == "阪神":
            past_place = "09"
            past_mawari = 0
        elif past_location == "小倉":
            past_place = "10"
            past_mawari = 0
        else:
            past_place = ""
            past_mawari = ""
        
        # 既存コードと同じフォーマットでreturn
        result = [
            str_date, past_horse_number, past_jockey, past_handicap, odds, 
            weight, weight_change, agari, through_order, finish_order, 
            distance, race_rank, time_value, track_mapped, weather, 
            past_place, track_condition, past_mawari
        ]
        
        return result
    
    def _save_to_csv_legacy(self, race_id: str, race_info: Dict, horses_data: List[Dict]) -> str:
        """データをCSVファイルに保存（既存コード完全準拠）"""
        csv_path = os.path.join(self.data_dir, "race_input", f"race_data_{race_id}.csv")
        
        # 既存コードのall_resultsフォーマットを完全再現
        all_results = []
        all_results.append(self.COLUMN_LIST)
        
        for index, horse in enumerate(horses_data):
            # 基本レース情報
            result = [
                race_info['race_id'], horse['horse_name'], horse['jockey'], 
                horse['horse_number'], horse['running_time'], horse['odds'], 
                horse['through_order'], horse['finish_order'], horse['weight'], 
                horse['weight_change'], horse['sex'], horse['age'], horse['handicap'], 
                horse['agari'], horse['popularity'], race_info['race_name'], 
                race_info['date'], race_info['race_meeting'], race_info['race_rank'], 
                race_info['track_type'], race_info['distance'], race_info['mawari'], 
                race_info['baba'], race_info['weather'], race_info['place_id'], 
                race_info['location']
            ]
            
            # 過去戦績データを追加（最大5走分）
            history_results = horse.get('history_results', [])
            
            # 過去戦績を平坦化して追加
            if history_results:
                results_array = np.array(history_results)
                flattened_results = results_array.ravel()
                result.extend(flattened_results)
            
            all_results.append(result)
        
        # DataFrameに変換して後処理（既存コード準拠）
        df_all_results = pd.DataFrame(all_results)
        df_all_results.columns = df_all_results.iloc[0]
        df_all_results = df_all_results.drop(df_all_results.index[0])
        
        # 既存コードの後処理ロジック
        self._apply_legacy_postprocessing(df_all_results)
        
        # CSVに保存
        array_data = df_all_results.values
        columns = df_all_results.columns
        all_results_final = np.insert(array_data, 0, columns, axis=0)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for data in all_results_final:
                writer.writerow(data)
        
        logger.info(f"Data saved to: {csv_path}")
        return csv_path
    
    def _apply_legacy_postprocessing(self, df: pd.DataFrame):
        """既存コードの後処理を適用"""
        try:
            # 斤量に関連する列を数値に変換
            kinryo_columns = ['斤量', '斤量1', '斤量2', '斤量3', '斤量4', '斤量5']
            for col in kinryo_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 平均斤量を計算
            df['平均斤量'] = df[kinryo_columns].mean(axis=1)
            
            # 騎手名の表記ゆれ修正（既存コード準拠）
            df.replace({
                "ムルザバエフ": "ムルザ",
                "永島まなみ": "永島まな",
                "河原田菜々": "河原田菜",
                "デムーロ": "Ｍ．デ",
                "秋山真一郎": "秋山真一",
                "マーカンド": "マーカン",
                "佐々木大輔": "佐々木大",
                "石川裕紀人": "石川裕紀",
                "ビュイック": "ビュイッ",
                "ルメートル": "ルメート",
                "野中悠太郎": "野中悠太",
                "武士沢友治": "武士沢友",
                "シュタルケ": "シュタル",
                "柴田裕一郎": "柴田裕一",
                "五十嵐雄祐": "五十嵐雄",
                "小野寺祐太": "小野寺祐",
                "吉村誠之助": "吉村誠之",
                "小牧加矢太": "小牧加矢",	
            }, inplace=True)
            
            # 距離差・日付差の計算（既存コード準拠）
            df["距離差"] = pd.to_numeric(df["距離"], errors='coerce') - pd.to_numeric(df["距離1"], errors='coerce')
            
            # 日付を文字列に変換
            date_columns = ["日付", "日付1", "日付2", "日付3", "日付4", "日付5"]
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str)
            
            # 日付差の計算
            df["日付差"] = (pd.to_datetime(df["日付"], errors='coerce') - pd.to_datetime(df["日付1"], errors='coerce')).dt.days
            df["距離差1"] = pd.to_numeric(df["距離1"], errors='coerce') - pd.to_numeric(df["距離2"], errors='coerce')
            df["日付差1"] = (pd.to_datetime(df["日付1"], errors='coerce') - pd.to_datetime(df["日付2"], errors='coerce')).dt.days
            df["距離差2"] = pd.to_numeric(df["距離2"], errors='coerce') - pd.to_numeric(df["距離3"], errors='coerce')
            df["日付差2"] = (pd.to_datetime(df["日付2"], errors='coerce') - pd.to_datetime(df["日付3"], errors='coerce')).dt.days
            df["距離差3"] = pd.to_numeric(df["距離3"], errors='coerce') - pd.to_numeric(df["距離4"], errors='coerce')
            df["日付差3"] = (pd.to_datetime(df["日付3"], errors='coerce') - pd.to_datetime(df["日付4"], errors='coerce')).dt.days
            df["距離差4"] = pd.to_numeric(df["距離4"], errors='coerce') - pd.to_numeric(df["距離5"], errors='coerce')
            df["日付差4"] = (pd.to_datetime(df["日付4"], errors='coerce') - pd.to_datetime(df["日付5"], errors='coerce')).dt.days
            
        except Exception as e:
            logger.warning(f"Legacy postprocessing failed: {e}")
    
    def get_legacy_csv_data(self, race_id: str) -> str:
        """既存コード互換のCSVデータ文字列を取得"""
        try:
            csv_path = os.path.join(self.data_dir, "race_input", f"race_data_{race_id}.csv")
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            logger.error(f"Failed to read CSV data: {e}")
            return ""

# インスタンス作成
scraper = NetkeibaRaceScraper()