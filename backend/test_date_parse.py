#!/usr/bin/env python3
"""日付パースのテスト"""

from datetime import datetime

# ユーザーが提供したURLパラメータと同じ値
start_date_str = "2025-09-01"
end_date_str = "2025-11-04"

print("テスト開始...")
print(f"開始日文字列: {start_date_str}")
print(f"終了日文字列: {end_date_str}")

try:
    start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    print(f"✓ 開始日パース成功: {start_date_obj}")
except ValueError as e:
    print(f"✗ 開始日パース失敗: {e}")

try:
    end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    print(f"✓ 終了日パース成功: {end_date_obj}")
except ValueError as e:
    print(f"✗ 終了日パース失敗: {e}")

print("\nテスト完了")
