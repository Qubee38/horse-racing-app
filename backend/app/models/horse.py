# backend/app/models/horse.py (修正版)
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Horse(Base):
    __tablename__ = "horses"
    
    # 基本情報
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False, index=True)
    
    # 馬の基本データ
    name = Column(String(100), nullable=False)              # 馬名
    jockey = Column(String(50))                             # 騎手名  
    frame_number = Column(Integer)                          # 枠番
    horse_number = Column(Integer)                          # 馬番
    netkeiba_horse_id = Column(String(20))                  # NetkeibaでのID
    # オッズ・人気
    odds = Column(Float)                                    # 単勝オッズ
    popularity = Column(Integer)                            # 人気
    # 馬体重
    weight = Column(Float)                                  # 馬体重
    weight_change = Column(Float)                           # 体重変化
    # 負担重量
    handicap = Column(Float)                                # 負担重量
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    race = relationship("Race", back_populates="horses")
    
    # レース結果との関係（HorseResultから参照される）
    horse_results = relationship("HorseResult", back_populates="horse")
    
    # 予測結果との関係性は削除（Predictionモデル側で定義されている）
    predictions = relationship("Prediction", back_populates="horse", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Horse(id={self.id}, name={self.name}, race_id={self.race_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "race_id": self.race_id,
            "name": self.name,
            "jockey": self.jockey,
            "frame_number": self.frame_number,
            "horse_number": self.horse_number,
            "netkeiba_horse_id": self.netkeiba_horse_id,
            "odds": self.odds,
            "popularity": self.popularity,
            "weight": self.weight,
            "weight_change": self.weight_change,
            "handicap": self.handicap,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }