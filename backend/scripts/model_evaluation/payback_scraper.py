# backend/scripts/model_evaluation/payback_scraper.py

import logging
import time
from typing import List, Optional, Callable
from pathlib import Path
import sys

# 既存のスクレイピングクラスをインポート
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from app.services.race_result_scraper import RaceResultScraper

# payback_parserをインポート
from .payback_parser import PaybackInfo, PaybackParser

logger = logging.getLogger(__name__)


class PaybackScraper:
    """
    払い戻し情報スクレイピングクラス
    
    既存のRaceResultScraperを活用して払い戻し情報のみを取得し、
    PaybackParserのフォーマットに変換する
    """
    
    def __init__(self, delay: float = 5.0):
        """
        Parameters
        ----------
        delay : float
            リクエスト間の待機時間（秒）
        """
        self.scraper = RaceResultScraper()
        self.delay = delay
        self._last_request_time = 0.0
    
    def _rate_limit(self):
        """Rate Limiting: 前回のリクエストから指定時間待機"""
        if self._last_request_time > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def scrape_payback_info(self, race_id: str) -> Optional[PaybackInfo]:
        """
        指定レースの払い戻し情報を取得
        
        Parameters
        ----------
        race_id : str
            NetkeibaレースID（12桁）
        
        Returns
        -------
        Optional[PaybackInfo]
            払い戻し情報、取得失敗時はNone
        """
        # Rate Limiting
        self._rate_limit()
        
        logger.info(f"Scraping payback info for race {race_id}")
        
        # 既存スクレイパーでレース結果取得
        result = self.scraper.scrape_race_result(race_id)
        
        if not result:
            logger.warning(f"Failed to scrape race result: {race_id}")
            return None
        
        # レースがキャンセルされた場合
        if result.get('race_status') == 'cancelled':
            logger.info(f"Race was cancelled: {race_id}")
            return None
        
        # 払い戻し情報を変換
        payback_info = self._convert_to_payback_info(race_id, result.get('payouts', []))
        
        return payback_info
    
    def _convert_to_payback_info(self, race_id: str, payouts: List[dict]) -> PaybackInfo:
        """
        スクレイピング結果をPaybackInfoに変換
        
        Parameters
        ----------
        race_id : str
            レースID
        payouts : List[dict]
            スクレイピング結果の払い戻し情報
            [
                {
                    'bet_type': 'win' | 'place',
                    'winning_numbers': str,
                    'payout_amount': int
                },
                ...
            ]
        
        Returns
        -------
        PaybackInfo
            変換後の払い戻し情報
        """
        payback_info = PaybackInfo(race_id=race_id)
        
        for payout in payouts:
            bet_type = payout.get('bet_type')
            winning_numbers = payout.get('winning_numbers')
            payout_amount = payout.get('payout_amount')
            
            if not winning_numbers or payout_amount is None:
                continue
            
            # 単勝
            if bet_type == 'win':
                payback_info.win = (str(winning_numbers), int(payout_amount))
            
            # 複勝
            elif bet_type == 'place':
                if payback_info.place is None:
                    payback_info.place = []
                payback_info.place.append((str(winning_numbers), int(payout_amount)))
        
        return payback_info
    
    def scrape_multiple(
        self, 
        race_ids: List[str],
        save_callback: Optional[Callable[[PaybackInfo], None]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[PaybackInfo]:
        """
        複数レースの払い戻し情報を一括取得
        
        Parameters
        ----------
        race_ids : List[str]
            レースIDのリスト
        save_callback : Optional[Callable]
            各レース取得後に呼び出すコールバック関数
            引数: PaybackInfo
        progress_callback : Optional[Callable]
            進捗報告用コールバック関数
            引数: (current, total, race_id)
        
        Returns
        -------
        List[PaybackInfo]
            取得成功した払い戻し情報のリスト
        """
        payback_infos = []
        total = len(race_ids)
        
        logger.info(f"Starting batch scraping: {total} races")
        
        for i, race_id in enumerate(race_ids, 1):
            # 進捗報告
            if progress_callback:
                progress_callback(i, total, race_id)
            
            logger.info(f"[{i}/{total}] Scraping race {race_id}")
            
            try:
                # 払い戻し情報取得
                payback_info = self.scrape_payback_info(race_id)
                
                if payback_info:
                    payback_infos.append(payback_info)
                    
                    # コールバック実行（保存など）
                    if save_callback:
                        save_callback(payback_info)
                    
                    logger.info(f"[{i}/{total}] Success: race {race_id}")
                else:
                    logger.warning(f"[{i}/{total}] No payback info: race {race_id}")
            
            except Exception as e:
                logger.error(f"[{i}/{total}] Error scraping race {race_id}: {e}")
                # エラーがあっても続行
                continue
        
        logger.info(f"Batch scraping completed: {len(payback_infos)}/{total} races")
        
        return payback_infos
    
    def scrape_and_save_missing(
        self, 
        required_race_ids: List[str],
        parser: PaybackParser,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> dict:
        """
        不足している払い戻し情報をスクレイピングして保存
        
        Parameters
        ----------
        required_race_ids : List[str]
            必要なレースIDのリスト
        parser : PaybackParser
            払い戻し情報パーサー（保存先）
        progress_callback : Optional[Callable]
            進捗報告用コールバック
        
        Returns
        -------
        dict
            実行結果の統計
            {
                'total_required': int,
                'already_exists': int,
                'scraped': int,
                'failed': int
            }
        """
        # 不足しているレースIDを検出
        missing_race_ids = parser.get_missing_race_ids(required_race_ids)
        
        total_required = len(required_race_ids)
        already_exists = total_required - len(missing_race_ids)
        
        logger.info(f"Total required: {total_required}")
        logger.info(f"Already exists: {already_exists}")
        logger.info(f"Missing: {len(missing_race_ids)}")
        
        if not missing_race_ids:
            logger.info("No missing payback data")
            return {
                'total_required': total_required,
                'already_exists': already_exists,
                'scraped': 0,
                'failed': 0
            }
        
        # 保存用コールバック
        def save_callback(payback_info: PaybackInfo):
            parser.save_payback_info(payback_info)
        
        # スクレイピング実行
        scraped_infos = self.scrape_multiple(
            missing_race_ids,
            save_callback=save_callback,
            progress_callback=progress_callback
        )
        
        scraped = len(scraped_infos)
        failed = len(missing_race_ids) - scraped
        
        logger.info(f"Scraping summary:")
        logger.info(f"  Total required: {total_required}")
        logger.info(f"  Already exists: {already_exists}")
        logger.info(f"  Scraped: {scraped}")
        logger.info(f"  Failed: {failed}")
        
        return {
            'total_required': total_required,
            'already_exists': already_exists,
            'scraped': scraped,
            'failed': failed
        }


# ========================================
# テスト用コード
# ========================================
if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    from pathlib import Path
    
    # テスト用ディレクトリ
    test_dir = Path(__file__).parent.parent.parent / "data" / "payback"
    
    # PaybackParserを初期化
    parser = PaybackParser(test_dir)
    
    # PaybackScraperを初期化
    scraper = PaybackScraper(delay=5.0)
    
    # テスト用レースID（実際に存在するレース）
    test_race_ids = [
        "202506040911",  # スプリンターズS
    ]
    
    # 単一レースのテスト
    print("\n=== Single Race Test ===")
    payback_info = scraper.scrape_payback_info(test_race_ids[0])
    
    if payback_info:
        print(f"Race ID: {payback_info.race_id}")
        print(f"Win: {payback_info.win}")
        print(f"Place: {payback_info.place}")
        
        # 保存テスト
        parser.save_payback_info(payback_info)
        print("✓ Saved to CSV")
    
    # バッチスクレイピングのテスト
    print("\n=== Batch Scraping Test ===")
    
    # 進捗コールバック
    def progress_callback(current, total, race_id):
        print(f"Progress: [{current}/{total}] {race_id}")
    
    # 不足分の自動取得テスト
    result = scraper.scrape_and_save_missing(
        required_race_ids=test_race_ids,
        parser=parser,
        progress_callback=progress_callback
    )
    
    print("\n=== Scraping Summary ===")
    print(f"Total required: {result['total_required']}")
    print(f"Already exists: {result['already_exists']}")
    print(f"Scraped: {result['scraped']}")
    print(f"Failed: {result['failed']}")