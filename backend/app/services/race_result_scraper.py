# backend/app/services/race_result_scraper.py
"""
Netkeibaからレース結果を取得するスクレイピングサービス

機能:
    1. レース結果（着順・人気）の取得
    2. 払い戻し情報（単勝・複勝）の取得
    3. User-Agent偽装とRate Limiting対応
"""

import logging
import random
import time
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RaceResultScraper:
    """レース結果スクレイピングクラス"""
    
    # User-Agent リスト
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:115.0) Gecko/20100101 Firefox/115.0",
    ]
    
    BASE_URL = "https://db.netkeiba.com/race/"
    MAX_RETRIES = 2
    SLEEP_TIME = 2.0
    RETRY_SLEEP_TIME = 10.0
    
    def __init__(self):
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """ランダムなUser-Agentを含むヘッダーを生成"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        }
    
    def _fetch_url(self, url: str) -> Optional[requests.Response]:
        """URLからHTMLを取得（リトライ機能付き）"""
        for attempt in range(self.MAX_RETRIES):
            try:
                if attempt > 0:
                    logger.info(f"リトライ {attempt}/{self.MAX_RETRIES}: {url}")
                    time.sleep(self.RETRY_SLEEP_TIME)
                else:
                    time.sleep(self.SLEEP_TIME)
                
                response = self.session.get(url, headers=self._get_headers(), timeout=30)
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                logger.error(f"URL取得エラー {url}: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    logger.error(f"最大リトライ回数に達しました: {url}")
                    return None
        
        return None
    
    def scrape_race_result(self, race_id: str) -> Optional[Dict]:
        """
        レース結果を取得
        
        Args:
            race_id: NetkeibaレースID (例: 202506040911)
        
        Returns:
            {
                'race_status': 'completed' | 'cancelled',
                'horse_results': [
                    {
                        'netkeiba_horse_id': str,  # NetkeibaのID
                        'horse_number': int,
                        'finish_position': int,
                        'popularity': int
                    },
                    ...
                ],
                'payouts': [
                    {
                        'bet_type': 'win' | 'place',
                        'winning_numbers': str,
                        'payout_amount': int
                    },
                    ...
                ]
            }
        """
        url = f"{self.BASE_URL}{race_id}"
        logger.info(f"レース結果取得開始: {url}")
        
        response = self._fetch_url(url)
        if not response:
            return None
        
        try:
            # EUC-JPでデコード
            soup = BeautifulSoup(response.content.decode("euc-jp", "ignore"), "html.parser")
            
            # レース結果テーブルを確認
            race_table = soup.find("table", class_="race_table_01")
            if not race_table:
                logger.warning(f"レース結果テーブルが見つかりません: {race_id}")
                return {
                    'race_status': 'cancelled',
                    'horse_results': [],
                    'payouts': []
                }
            
            # 各馬の結果を抽出
            horse_results = self._extract_horse_results(race_table, race_id)
            
            # 払い戻し情報を抽出
            payouts = self._extract_payouts(soup)
            
            return {
                'race_status': 'completed',
                'horse_results': horse_results,
                'payouts': payouts
            }
            
        except Exception as e:
            logger.error(f"レース結果解析エラー {race_id}: {e}", exc_info=True)
            return None
    
    def _extract_horse_results(self, race_table, race_id: str) -> List[Dict]:
        """各馬の着順・人気を抽出"""
        horse_results = []
        
        try:
            rows = race_table.find_all("tr")
            for row in rows[1:]:  # ヘッダー行をスキップ
                cells = row.find_all("td")
                if len(cells) < 8:
                    continue
                
                try:
                    # 着順（1列目）
                    finish_position_text = cells[0].get_text(strip=True)
                    finish_position = int(finish_position_text) if finish_position_text.isdigit() else None
                    
                    # 馬番（3列目）
                    horse_number = int(cells[2].get_text(strip=True))
                    
                    # 人気（8列目）
                    popularity_text = cells[7].get_text(strip=True)
                    popularity = int(popularity_text) if popularity_text.isdigit() else None
                    
                    # 馬IDをURLから抽出（4列目の馬名リンク）
                    horse_link = cells[3].find("a")
                    netkeiba_horse_id = None
                    if horse_link and 'href' in horse_link.attrs:
                        href = horse_link['href']
                        # /horse/2019105481/ のような形式から抽出
                        parts = href.split('/')
                        if len(parts) >= 3 and parts[2].isdigit():
                            netkeiba_horse_id = parts[2]  # 文字列として保持
                    
                    horse_results.append({
                        'netkeiba_horse_id': netkeiba_horse_id,  # Netkeibaの馬ID（文字列）
                        'horse_number': horse_number,
                        'finish_position': finish_position,
                        'popularity': popularity
                    })
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"馬データ抽出エラー {race_id}: {e}")
                    continue
            
            logger.info(f"馬結果抽出完了: {len(horse_results)}頭")
            
        except Exception as e:
            logger.error(f"馬結果抽出エラー {race_id}: {e}", exc_info=True)
        
        return horse_results
    
    def _extract_payouts(self, soup) -> List[Dict]:
        """払い戻し情報を抽出（単勝・複勝のみ）"""
        payouts = []
        
        try:
            # 払い戻しテーブルを取得
            payback_table = soup.find("table", class_="pay_block")
            if not payback_table:
                # 代替: summary属性で検索
                payback_table = soup.find("table", summary="払い戻し")
            
            if not payback_table:
                logger.warning("払い戻しテーブルが見つかりません")
                return payouts
            
            # テーブル内のtrを全て取得
            rows = payback_table.find_all("tr")
            
            for row in rows:
                # th（券種名）を確認
                th = row.find("th")
                if not th:
                    continue
                
                bet_type_text = th.get_text(strip=True)
                
                # 単勝の処理
                if bet_type_text == "単勝":
                    win_payout = self._extract_payout_from_row(row, 'win')
                    if win_payout:
                        payouts.append(win_payout)
                
                # 複勝の処理
                elif bet_type_text == "複勝":
                    place_payouts = self._extract_multiple_payouts_from_row(row, 'place')
                    payouts.extend(place_payouts)
            
            logger.info(f"払い戻し情報抽出完了: {len(payouts)}件")
            
        except Exception as e:
            logger.error(f"払い戻し抽出エラー: {e}", exc_info=True)
        
        return payouts
    
    def _extract_payout_from_row(self, row, bet_type: str) -> Optional[Dict]:
        """1つの払い戻し行から情報を抽出（単勝用）"""
        try:
            tds = row.find_all("td")
            if len(tds) < 2:
                return None
            
            # 馬番（1列目）
            winning_numbers = tds[0].get_text(strip=True)
            
            # 払い戻し額（2列目）- カンマと円を除去
            payout_text = tds[1].get_text(strip=True)
            payout_text = re.sub(r'[,円]', '', payout_text)
            
            # 数字のみ抽出
            match = re.search(r'\d+', payout_text)
            if not match:
                return None
            
            payout_amount = int(match.group())
            
            return {
                'bet_type': bet_type,
                'winning_numbers': winning_numbers,
                'payout_amount': payout_amount
            }
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"{bet_type}抽出エラー: {e}")
            return None
    
    def _extract_multiple_payouts_from_row(self, row, bet_type: str) -> List[Dict]:
        """複数の払い戻し行から情報を抽出（複勝用）"""
        payouts = []
        
        try:
            tds = row.find_all("td")
            if len(tds) < 2:
                return payouts
            
            # 馬番セル（1列目）
            horse_numbers_cell = tds[0]
            horse_numbers = []
            
            # brタグで分割されている場合
            for br in horse_numbers_cell.find_all('br'):
                br.replace_with('\n')
            
            # テキストを取得して分割
            text = horse_numbers_cell.get_text()
            for line in text.split('\n'):
                line = line.strip()
                if line and line.isdigit():
                    horse_numbers.append(line)
            
            # 払い戻し額セル（2列目）
            payout_cell = tds[1]
            payout_amounts = []
            
            # brタグで分割
            for br in payout_cell.find_all('br'):
                br.replace_with('\n')
            
            # テキストを取得して分割
            text = payout_cell.get_text()
            for line in text.split('\n'):
                line = line.strip()
                # カンマと円を除去して数字のみ抽出
                line = re.sub(r'[,円]', '', line)
                match = re.search(r'\d+', line)
                if match:
                    payout_amounts.append(int(match.group()))
            
            # 馬番と払い戻し額をペアリング
            for horse_num, payout_amount in zip(horse_numbers, payout_amounts):
                payouts.append({
                    'bet_type': bet_type,
                    'winning_numbers': horse_num,
                    'payout_amount': payout_amount
                })
            
        except Exception as e:
            logger.warning(f"{bet_type}（複数）抽出エラー: {e}")
        
        return payouts


# 使用例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scraper = RaceResultScraper()
    
    # テスト
    race_id = "202506040911"
    result = scraper.scrape_race_result(race_id)
    
    if result:
        print(f"レースステータス: {result['race_status']}")
        print(f"馬結果: {len(result['horse_results'])}頭")
        print(f"払い戻し: {len(result['payouts'])}件")
        
        for i, hr in enumerate(result['horse_results'][:3]):
            print(f"{i+1}着: 馬番{hr['horse_number']}, 人気{hr['popularity']}")
        
        for payout in result['payouts']:
            print(f"{payout['bet_type']}: {payout['winning_numbers']}番 → {payout['payout_amount']}円")