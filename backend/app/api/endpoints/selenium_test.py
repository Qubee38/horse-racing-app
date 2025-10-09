# backend/app/api/endpoints/selenium_test.py
"""
Selenium機能テスト用のAPIエンドポイント
一時的なテスト用として追加し、動作確認後に削除予定
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test/selenium/setup")
async def test_selenium_setup():
    """Selenium環境のセットアップテスト"""
    try:
        from app.services.netkeiba_race_finder import netkeiba_finder
        
        # Selenium環境テスト
        selenium_ok = netkeiba_finder.test_selenium_setup()
        
        return {
            "success": True,
            "selenium_status": "working" if selenium_ok else "failed",
            "message": "Selenium setup test completed",
            "use_selenium": netkeiba_finder.use_selenium,
            "fallback_available": netkeiba_finder.fallback_to_requests
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Import error: {str(e)}",
            "message": "Selenium dependencies not installed"
        }
    except Exception as e:
        logger.error(f"Selenium setup test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Selenium test failed: {str(e)}")

@router.post("/test/selenium/race-finder")
async def test_selenium_race_finder(request: dict):
    """
    Seleniumレースファインダーのテスト
    
    Body:
        {
            "date": "2023-12-28"  # テスト対象日
        }
    """
    try:
        date_str = request.get("date")
        if not date_str:
            raise HTTPException(status_code=400, detail="Date parameter is required")
        
        from app.services.netkeiba_race_finder import netkeiba_finder
        
        logger.info(f"Testing race finder for date: {date_str}")
        
        # レース検索実行
        races = netkeiba_finder.get_race_ids_for_date(date_str)
        
        # 結果の要約
        summary = {
            "total_races": len(races),
            "venues": list(set(race.get('venue', 'unknown') for race in races)),
            "race_numbers": [race.get('race_number', 0) for race in races[:10]]  # 最初の10レース
        }
        
        return {
            "success": True,
            "date": date_str,
            "races_found": len(races),
            "summary": summary,
            "sample_races": races[:5],  # 最初の5レースを返す
            "method_used": "selenium" if netkeiba_finder.use_selenium else "requests",
            "message": f"Found {len(races)} races for {date_str}"
        }
        
    except Exception as e:
        logger.error(f"Race finder test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Race finder test failed: {str(e)}")

@router.get("/test/selenium/dependencies")
async def check_selenium_dependencies():
    """Selenium関連の依存関係チェック"""
    dependencies = {}
    
    try:
        import selenium
        dependencies["selenium"] = {
            "installed": True,
            "version": selenium.__version__
        }
    except ImportError:
        dependencies["selenium"] = {
            "installed": False,
            "error": "Package not installed"
        }
    
    try:
        from selenium import webdriver
        dependencies["webdriver"] = {
            "installed": True,
            "available": True
        }
    except ImportError as e:
        dependencies["webdriver"] = {
            "installed": False,
            "error": str(e)
        }
    
    try:
        import lxml
        dependencies["lxml"] = {
            "installed": True,
            "version": lxml.__version__
        }
    except ImportError:
        dependencies["lxml"] = {
            "installed": False,
            "error": "Package not installed"
        }
    
    try:
        from bs4 import BeautifulSoup
        dependencies["beautifulsoup4"] = {
            "installed": True,
            "available": True
        }
    except ImportError:
        dependencies["beautifulsoup4"] = {
            "installed": False,
            "error": "Package not installed"
        }
    
    # 全体的な状況判定
    all_installed = all(dep.get("installed", False) for dep in dependencies.values())
    
    return {
        "success": all_installed,
        "dependencies": dependencies,
        "ready_for_selenium": all_installed,
        "message": "All dependencies ready" if all_installed else "Some dependencies missing"
    }