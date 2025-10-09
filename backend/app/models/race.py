# backend/app/models/race.py (リレーション追加版)
from sqlalchemy import Column, Integer, String, Float, Date, Time, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Race(Base):
    __tablename__ = "races"
    
    # 基本情報
    id = Column(Integer, primary_key=True, index=True)
    venue = Column(String(20), nullable=False)              # 開催場 (東京、阪神など)
    race_name = Column(String(100), nullable=False)         # レース名
    race_number = Column(Integer, nullable=False)           # レース番号
    
    # 日時情報
    race_date = Column(Date, nullable=False, index=True)    # 開催日
    start_time = Column(String(10))                         # 発走時刻 (HH:MM形式)
    
    # レース条件
    distance = Column(Integer)                              # 距離 (m)
    surface = Column(String(10))                            # 馬場 (芝、ダート)
    weather = Column(String(10))                            # 天気 (晴、曇、雨など)
    track_condition = Column(String(10))                    # 馬場状態 (良、稍、重、不)
    grade = Column(String(10))                              # グレード (G1, G2, G3等)
    
    # 統計情報
    horse_count = Column(Integer, default=0)                # 出走頭数
    
    # NetkeibaレースID（重要）
    netkeiba_race_id = Column(String(50), index=True)       # Netkeibaでのレース識別子
    
    # メタデータ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    horses = relationship("Horse", back_populates="race", cascade="all, delete-orphan")
    # Predictionとのリレーションは削除（Predictionモデルで定義されている）
    
    # レース結果とのリレーション（1対1）
    race_result = relationship("RaceResult", back_populates="race", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Race(id={self.id}, name={self.race_name}, date={self.race_date})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "venue": self.venue,
            "race_name": self.race_name,
            "race_number": self.race_number,
            "race_date": self.race_date.isoformat() if self.race_date else None,
            "start_time": self.start_time,
            "distance": self.distance,
            "surface": self.surface,
            "weather": self.weather,
            "track_condition": self.track_condition,
            "grade": self.grade,
            "horse_count": self.horse_count,
            "netkeiba_race_id": self.netkeiba_race_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }