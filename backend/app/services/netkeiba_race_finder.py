# backend/app/services/netkeiba_race_finder.py (詳細情報抽出修正版)
import re
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup, Tag

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class NetkeibaRaceFinder:
    """
    Selenium対応 NetkeibaレースID取得サービス
    - 動的なJavaScriptページに対応
    - フォールバック機能付き
    """
    
    def __init__(self):
        self.base_url = "https://race.netkeiba.com"
        self.use_selenium = True
        self.fallback_to_requests = True
        
        # Selenium設定
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Requests用のセッション（フォールバック）
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_race_ids_for_date(self, date_str: str) -> List[Dict]:
        """
        指定日のレース一覧とレースIDを取得（Selenium優先、フォールバック対応）
        
        Args:
            date_str: 日付文字列 (YYYY-MM-DD形式)
            
        Returns:
            List[Dict]: レース情報のリスト
        """
        try:
            # YYYY-MM-DD → YYYYMMDD に変換
            formatted_date = date_str.replace('-', '')
            
            logger.info(f"Searching races for date: {date_str} (formatted: {formatted_date})")
            
            # Seleniumでレース取得を試行
            if self.use_selenium:
                try:
                    races = self._get_races_with_selenium(formatted_date)
                    if races:
                        logger.info(f"Successfully found {len(races)} races with Selenium")
                        return races
                    else:
                        logger.warning("Selenium returned no races, trying fallback")
                        
                except Exception as e:
                    logger.error(f"Selenium method failed: {e}")
                    if not self.fallback_to_requests:
                        raise
            
            # フォールバック: requestsでレース取得
            if self.fallback_to_requests:
                logger.info("Falling back to requests method")
                races = self._get_races_with_requests(formatted_date)
                if races:
                    logger.info(f"Successfully found {len(races)} races with requests fallback")
                    return races
                else:
                    logger.warning("Requests fallback also returned no races")
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get race IDs for date {date_str}: {e}")
            return []
    
    def _get_races_with_selenium(self, formatted_date: str) -> List[Dict]:
        """Seleniumを使用してレースID一覧を取得"""
        driver = None
        try:
            # WebDriverを初期化
            driver = webdriver.Chrome(options=self.chrome_options)
            wait = WebDriverWait(driver, 30)
            
            # 開催一覧ページにアクセス
            url = f"{self.base_url}/top/race_list.html?kaisai_date={formatted_date}"
            logger.info(f"Accessing Netkeiba URL: {url}")
            
            driver.get(url)
            
            # ページが完全に読み込まれるまで待機
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#RaceTopRace')))
            
            # 少し追加で待機（JavaScriptの実行完了を確実にする）
            time.sleep(2)
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # レースIDを抽出
            races = self._extract_races_from_page(soup, formatted_date)
            
            return races
            
        except TimeoutException:
            logger.error("Timeout waiting for page elements")
            return []
        except WebDriverException as e:
            logger.error(f"WebDriver error: {e}")
            return []
        except Exception as e:
            logger.error(f"Selenium scraping failed: {e}")
            return []
        finally:
            if driver:
                driver.quit()
    
    def _extract_races_from_page(self, soup: BeautifulSoup, formatted_date: str) -> List[Dict]:
        """ページからレース情報を抽出（改善版）"""
        races = []
        
        try:
            # レースリストアイテムを取得
            race_items = soup.select('.RaceList_DataItem')
            
            logger.info(f"Found {len(race_items)} race items")
            
            for item in race_items:
                try:
                    # レースリンクを取得
                    race_link = item.select_one('a[href*="race_id="]')
                    if not race_link:
                        continue
                    
                    href = race_link.get('href', '')
                    if not href:
                        continue
                    
                    # レースIDを抽出
                    race_id_match = re.search(r'race_id=(.+?)(&|$)', href)
                    if not race_id_match:
                        continue
                    
                    netkeiba_race_id = race_id_match.group(1)
                    
                    # レース番号をIDから抽出（下2桁）
                    race_number = self._extract_race_number_from_id(netkeiba_race_id)
                    
                    # 競馬場をIDから抽出（5-6桁目）
                    venue = self._extract_venue_from_race_id(netkeiba_race_id)
                    
                    # レース名を取得
                    race_name_elem = item.select_one('.ItemTitle')
                    race_name = race_name_elem.get_text().strip() if race_name_elem else f"{race_number}R"
                    
                    # クリーンなレース名（番号を除去）
                    clean_race_name = re.sub(r'^\d+R\s*', '', race_name).strip()
                    if not clean_race_name:
                        clean_race_name = f"{race_number}R"
                    
                    # 発走時刻（span.RaceList_Itemtime）
                    start_time = self._extract_start_time_from_item(item)
                    
                    # 距離と馬場（span.RaceList_ItemLong）
                    distance, surface = self._extract_distance_and_surface_from_item(item)
                    
                    # 頭数（span.RaceList_Itemnumber）
                    horse_count = self._extract_horse_count_from_item(item)
                    
                    race_info = {
                        "netkeiba_race_id": netkeiba_race_id,
                        "venue": venue,
                        "race_number": race_number,
                        "race_name": clean_race_name,
                        "start_time": start_time,
                        "distance": distance,
                        "surface": surface,
                        "horse_count": horse_count,
                        "url": f"{self.base_url}{href}" if not href.startswith('http') else href
                    }
                    
                    races.append(race_info)
                    logger.debug(f"Extracted race: {race_info}")
                    
                except Exception as e:
                    logger.warning(f"Failed to parse race item: {e}")
                    continue
            
            # レース番号でソート
            races.sort(key=lambda x: (x.get('venue', ''), x.get('race_number', 0)))
            
        except Exception as e:
            logger.error(f"Failed to extract races from page: {e}")
        
        return races
    
    def _extract_race_number_from_id(self, race_id: str) -> int:
        """レースIDから レース番号を抽出（下2桁）"""
        try:
            if len(race_id) >= 12:
                # 下2桁を取得
                race_num_str = race_id[-2:]
                return int(race_num_str)
            return 0
        except (ValueError, IndexError):
            return 0
    
    def _extract_start_time_from_item(self, item: Tag) -> str:
        """発走時刻を抽出（span.RaceList_Itemtime）"""
        try:
            time_elem = item.select_one('.RaceList_Itemtime')
            if time_elem:
                time_text = time_elem.get_text().strip()
                # HH:MM形式を確認
                time_match = re.search(r'(\d{1,2}:\d{2})', time_text)
                if time_match:
                    return time_match.group(1)
        except Exception as e:
            logger.debug(f"Failed to extract start time: {e}")
        
        return "未定"
    
    def _extract_distance_and_surface_from_item(self, item: Tag) -> tuple:
        """距離と馬場を抽出（span.RaceList_ItemLong）"""
        distance = 0
        surface = "未定"
        
        try:
            # .RaceList_ItemLong を探す（Dart/Turf クラスがある場合もある）
            long_elem = item.select_one('.RaceList_ItemLong')
            if long_elem:
                text = long_elem.get_text().strip()
                
                # 馬場を判定（ダ/芝）
                if 'ダ' in text or 'ダート' in text:
                    surface = "ダート"
                elif '芝' in text:
                    surface = "芝"
                elif '障' in text:
                    surface = "障害"
                
                # 距離を抽出（数字 + m）
                distance_match = re.search(r'(\d{3,4})m', text)
                if distance_match:
                    distance = int(distance_match.group(1))
        except Exception as e:
            logger.debug(f"Failed to extract distance/surface: {e}")
        
        return distance, surface
    
    def _extract_horse_count_from_item(self, item: Tag) -> int:
        """頭数を抽出（span.RaceList_Itemnumber）"""
        try:
            count_elem = item.select_one('.RaceList_Itemnumber')
            if count_elem:
                text = count_elem.get_text().strip()
                # 数字 + 頭 の形式
                count_match = re.search(r'(\d+)頭', text)
                if count_match:
                    return int(count_match.group(1))
        except Exception as e:
            logger.debug(f"Failed to extract horse count: {e}")
        
        return 0
    
    def _extract_venue_from_race_id(self, race_id: str) -> str:
        """レースIDから開催場を推測（5-6桁目）"""
        try:
            if len(race_id) >= 10:
                # 5-6桁目を取得（0-indexedなので4:6）
                place_code = race_id[4:6]
                
                venue_map = {
                    '01': '札幌', '02': '函館', '03': '福島', '04': '新潟',
                    '05': '東京', '06': '中山', '07': '中京', '08': '京都',
                    '09': '阪神', '10': '小倉'
                }
                
                venue = venue_map.get(place_code, "未定")
                logger.debug(f"Extracted venue '{venue}' from race_id place_code '{place_code}'")
                return venue
        except Exception as e:
            logger.debug(f"Failed to extract venue from race_id: {e}")
        
        return "未定"
    
    def _get_races_with_requests(self, formatted_date: str) -> List[Dict]:
        """requestsを使用してレースID一覧を取得（フォールバック）"""
        try:
            url = f"{self.base_url}/top/race_list.html?kaisai_date={formatted_date}"
            logger.info(f"Trying requests fallback with URL: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            races = self._extract_races_from_page(soup, formatted_date)
            
            return races
            
        except Exception as e:
            logger.error(f"Requests fallback failed: {e}")
            return []
    
    def get_race_details(self, netkeiba_race_id: str) -> Optional[Dict]:
        """
        特定のレースの詳細情報を取得
        """
        try:
            url = f"{self.base_url}/race/shutuba.html?race_id={netkeiba_race_id}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            details = self._extract_race_details_from_page(soup)
            details['netkeiba_race_id'] = netkeiba_race_id
            details['url'] = url
            
            return details
            
        except Exception as e:
            logger.error(f"Failed to get race details for {netkeiba_race_id}: {e}")
            return None
    
    def _extract_race_details_from_page(self, soup: BeautifulSoup) -> Dict:
        """レース詳細ページから情報を抽出"""
        details = {
            "start_time": "未定",
            "distance": 0,
            "surface": "未定",
            "grade": "",
            "horse_count": 0
        }
        
        try:
            # レース情報エリアを探索
            race_data_area = soup.find('div', class_='race_otherdata')
            
            if race_data_area:
                race_data_text = race_data_area.get_text()
                
                # 発走時刻を抽出
                time_match = re.search(r'(\d{2}:\d{2})', race_data_text)
                if time_match:
                    details["start_time"] = time_match.group(1)
                
                # 距離を抽出
                distance_match = re.search(r'(\d+)m', race_data_text)
                if distance_match:
                    details["distance"] = int(distance_match.group(1))
                
                # 馬場を抽出
                if '芝' in race_data_text:
                    details["surface"] = "芝"
                elif 'ダート' in race_data_text:
                    details["surface"] = "ダート"
            
            # 出走馬数を取得
            horse_rows = soup.find_all('tr', class_=['horseNo', 'horse_number'])
            details["horse_count"] = len(horse_rows)
            
        except Exception as e:
            logger.warning(f"Failed to extract race details: {e}")
        
        return details
    
    def test_selenium_setup(self) -> bool:
        """Selenium環境のテスト"""
        driver = None
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get("https://www.google.com")
            return True
        except Exception as e:
            logger.error(f"Selenium setup test failed: {e}")
            return False
        finally:
            if driver:
                driver.quit()

# グローバルインスタンス
netkeiba_finder = NetkeibaRaceFinder()