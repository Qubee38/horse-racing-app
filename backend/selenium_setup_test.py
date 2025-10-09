# backend/selenium_setup_test.py
"""
Selenium環境のセットアップとテスト用スクリプト
"""

import sys
import os
from pathlib import Path
import logging

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_selenium_dependencies():
    """Selenium関連の依存関係確認"""
    print("=" * 50)
    print("Selenium Dependencies Check")
    print("=" * 50)
    
    try:
        import selenium
        print(f"✅ Selenium installed: {selenium.__version__}")
    except ImportError:
        print("❌ Selenium not installed")
        print("   Run: pip install selenium")
        return False
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        print("✅ Selenium webdriver imports OK")
    except ImportError as e:
        print(f"❌ Selenium webdriver import failed: {e}")
        return False
    
    try:
        import lxml
        print(f"✅ lxml installed: {lxml.__version__}")
    except ImportError:
        print("❌ lxml not installed") 
        print("   Run: pip install lxml")
        return False
    
    return True

def test_chrome_driver():
    """Chrome Driver のテスト"""
    print("\n" + "=" * 50)
    print("Chrome Driver Test")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Chrome オプション設定
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        print("Starting Chrome WebDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("Testing Google access...")
        driver.get("https://www.google.com")
        
        title = driver.title
        print(f"✅ Chrome Driver working: Page title = '{title}'")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"❌ Chrome Driver test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Install Chrome browser")
        print("2. Install ChromeDriver:")
        print("   - Download from: https://chromedriver.chromium.org/")
        print("   - Or run: sudo apt-get install chromium-chromedriver")
        print("3. Make sure ChromeDriver is in PATH")
        return False

def test_netkeiba_race_finder():
    """NetkeibaRaceFinder のテスト"""
    print("\n" + "=" * 50)
    print("NetkeibaRaceFinder Test")
    print("=" * 50)
    
    try:
        from app.services.netkeiba_race_finder import netkeiba_finder
        
        # Selenium環境テスト
        print("Testing Selenium setup...")
        selenium_ok = netkeiba_finder.test_selenium_setup()
        
        if selenium_ok:
            print("✅ Selenium setup OK")
        else:
            print("⚠️  Selenium setup failed, will use requests fallback")
        
        # 実際のレース取得テスト
        test_date = "2023-12-28"  # 過去の確実に存在する日付
        print(f"\nTesting race finder for date: {test_date}")
        
        races = netkeiba_finder.get_race_ids_for_date(test_date)
        
        if races:
            print(f"✅ Found {len(races)} races")
            
            # サンプル表示
            for i, race in enumerate(races[:3]):
                print(f"  Race {i+1}:")
                print(f"    ID: {race.get('netkeiba_race_id', 'unknown')}")
                print(f"    Venue: {race.get('venue', 'unknown')}")
                print(f"    Name: {race.get('race_name', 'unknown')}")
            
            if len(races) > 3:
                print(f"    ... and {len(races) - 3} more races")
            
            return True
        else:
            print("⚠️  No races found (may be due to date or network)")
            return False
            
    except Exception as e:
        print(f"❌ NetkeibaRaceFinder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("🔧 Selenium Setup and Test Script")
    print("For Horse Racing Prediction App")
    print()
    
    # 依存関係チェック
    deps_ok = check_selenium_dependencies()
    if not deps_ok:
        print("\n❌ Dependencies check failed. Please install missing packages.")
        return False
    
    # Chrome Driver テスト
    chrome_ok = test_chrome_driver()
    if not chrome_ok:
        print("\n❌ Chrome Driver test failed. Please fix Chrome setup.")
        return False
    
    # NetkeibaRaceFinder テスト
    finder_ok = test_netkeiba_race_finder()
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    print(f"Dependencies: {'✅ PASS' if deps_ok else '❌ FAIL'}")
    print(f"Chrome Driver: {'✅ PASS' if chrome_ok else '❌ FAIL'}")
    print(f"RaceFinder: {'✅ PASS' if finder_ok else '⚠️ PARTIAL'}")
    
    if deps_ok and chrome_ok:
        print("\n🎉 Selenium setup completed successfully!")
        print("✅ Ready for enhanced race ID scraping")
        
        if finder_ok:
            print("✅ Race finding is working correctly")
        else:
            print("⚠️ Race finding may have network issues, but fallback is available")
        
        print("\nNext steps:")
        print("1. Update backend server with new NetkeibaRaceFinder")
        print("2. Test prediction API with real race data")
        print("3. Verify frontend integration")
    else:
        print("\n🔧 Setup issues detected:")
        if not deps_ok:
            print("- Install missing Python packages")
        if not chrome_ok:
            print("- Fix Chrome/ChromeDriver setup")
    
    return deps_ok and chrome_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)