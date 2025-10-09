# backend/app/models/prediction.py (モデルバージョン追加版)
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Prediction(Base):
    """予測結果テーブル"""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    
    # 予測結果
    win_probability = Column(Float, nullable=False)      # 1着確率
    place_probability = Column(Float, nullable=False)    # 3着以内確率
    expected_value = Column(Float, nullable=True)        # 期待値（オッズとの比較）
    
    # メタデータ
    model_version = Column(String(100), nullable=True)   # モデルバージョン（"v1.0_win+place"など）← String(100)に拡張
    prediction_date = Column(DateTime, default=datetime.utcnow)  # 予測実行日時
    feature_count = Column(Integer, nullable=True)       # 使用特徴量数
    confidence_score = Column(Float, nullable=True)      # 予測信頼度
    
    # 特徴量データ（JSON形式で保存）
    features_json = Column(Text, nullable=True)
    
    # フラグ
    is_active = Column(Boolean, default=True)            # 有効/無効
    
    # リレーション
    horse = relationship("Horse")
    race = relationship("Race")


class PredictionBatch(Base):
    """予測バッチ実行記録テーブル"""
    __tablename__ = "prediction_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    target_date = Column(String, nullable=False)         # 対象日（YYYY-MM-DD）
    status = Column(String, nullable=False)              # RUNNING, COMPLETED, FAILED
    
    # 統計情報
    total_races = Column(Integer, nullable=True)         # 対象レース数
    total_horses = Column(Integer, nullable=True)        # 対象馬数
    completed_predictions = Column(Integer, default=0)   # 完了予測数
    failed_predictions = Column(Integer, default=0)      # 失敗予測数
    
    # 実行時間
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # エラー情報
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # モデル情報
    model_version = Column(String(100), nullable=True)   # 統合バージョン ← String(100)に拡張
    feature_engineering_version = Column(String, nullable=True)