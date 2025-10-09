# backend/scripts/init_race_results.py
"""
レース結果機能の初期化スクリプト

使用方法:
    python -m backend.scripts.init_race_results

機能:
    1. race_result関連テーブルの作成
    2. bet_typesマスターデータの投入
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.core.config import settings

# 全モデルをインポート（リレーションシップ解決のため）
# 重要: インポート順序を守る（依存関係を考慮）
from app.models.race import Race
from app.models.horse import Horse
from app.models.prediction import Prediction, PredictionBatch
from app.models.race_result import BetType, RaceResult, HorseResult, Payout

# Baseにすべてのモデルが登録されていることを確認
print(f"登録済みモデル: {list(Base.metadata.tables.keys())}")


# 券種マスターデータ
BET_TYPES_INITIAL_DATA = [
    {"code": "win", "name": "単勝", "is_active": True},
    {"code": "place", "name": "複勝", "is_active": True},
    {"code": "bracket_quinella", "name": "枠連", "is_active": False},
    {"code": "quinella", "name": "馬連", "is_active": False},
    {"code": "exacta", "name": "馬単", "is_active": False},
    {"code": "wide", "name": "ワイド", "is_active": False},
    {"code": "trio", "name": "三連複", "is_active": False},
    {"code": "trifecta", "name": "三連単", "is_active": False},
]


def init_race_results_tables():
    """レース結果テーブルの初期化"""
    
    # データベースURL
    database_url = settings.DATABASE_URL
    if database_url.startswith("sqlite"):
        # SQLiteの場合、ファイルパスを絶対パスに変換
        db_path = database_url.replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            # backend配下のDBファイルを参照
            backend_dir = os.path.join(project_root, "backend")
            db_path = os.path.join(backend_dir, db_path)
            database_url = f"sqlite:///{db_path}"
    
    print(f"データベースURL: {database_url}")
    
    # エンジン作成
    engine = create_engine(database_url, echo=True)
    
    # セッション作成
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        print("\n=== レース結果テーブルの作成開始 ===")
        
        # テーブル作成（既存テーブルは影響を受けない）
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        print("\n=== テーブル作成完了 ===")
        
        # マスターデータ投入
        print("\n=== 券種マスターデータの投入開始 ===")
        
        session = SessionLocal()
        
        try:
            # 既存データをチェック
            existing_count = session.query(BetType).count()
            
            if existing_count > 0:
                print(f"券種マスターデータは既に存在します（{existing_count}件）")
                print("スキップします。")
            else:
                # マスターデータ投入
                for bet_type_data in BET_TYPES_INITIAL_DATA:
                    bet_type = BetType(**bet_type_data)
                    session.add(bet_type)
                
                session.commit()
                print(f"券種マスターデータを投入しました（{len(BET_TYPES_INITIAL_DATA)}件）")
            
            # 投入結果確認
            print("\n=== 投入結果 ===")
            all_bet_types = session.query(BetType).all()
            for bt in all_bet_types:
                status = "有効" if bt.is_active else "無効"
                print(f"  - {bt.code}: {bt.name} ({status})")
            
        except Exception as e:
            session.rollback()
            print(f"エラーが発生しました: {e}")
            raise
        finally:
            session.close()
        
        print("\n=== 初期化完了 ===")
        print("\n作成されたテーブル:")
        print("  - bet_types (券種マスター)")
        print("  - race_results (レース結果)")
        print("  - horse_results (各馬の着順)")
        print("  - payouts (払い戻し)")
        
    except Exception as e:
        print(f"\n初期化に失敗しました: {e}")
        raise


if __name__ == "__main__":
    init_race_results_tables()