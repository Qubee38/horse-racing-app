# backend/app/models/race_result.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime


class BetType(Base):
    """券種マスターテーブル"""
    __tablename__ = "bet_types"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)  # win, place, exacta, etc.
    name = Column(String(50), nullable=False)  # 単勝, 複勝, 馬連, etc.
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    payouts = relationship("Payout", back_populates="bet_type_ref")
    
    # Index
    __table_args__ = (
        Index('idx_bet_types_code', 'code'),
        Index('idx_bet_types_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<BetType(code={self.code}, name={self.name}, is_active={self.is_active})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "is_active": self.is_active
        }


class RaceResult(Base):
    """レース結果の基本情報（1レース1レコード）"""
    __tablename__ = "race_results"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), unique=True, nullable=False)
    
    # ステータス管理
    race_status = Column(String(20), nullable=False, default="completed")
    # completed: 正常終了
    # cancelled: 中止
    # partial_data: 一部データのみ取得
    
    # 取得日時
    result_fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    race = relationship("Race", back_populates="race_result")
    horse_results = relationship("HorseResult", back_populates="race_result", cascade="all, delete-orphan")
    payouts = relationship("Payout", back_populates="race_result", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RaceResult(id={self.id}, race_id={self.race_id}, status={self.race_status})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "race_id": self.race_id,
            "race_status": self.race_status,
            "result_fetched_at": self.result_fetched_at.isoformat() if self.result_fetched_at else None,
            "horse_results": [hr.to_dict() for hr in self.horse_results] if self.horse_results else [],
            "payouts": [p.to_dict() for p in self.payouts] if self.payouts else []
        }


class HorseResult(Base):
    """各馬の着順（1頭1レコード）"""
    __tablename__ = "horse_results"
    
    id = Column(Integer, primary_key=True, index=True)
    race_result_id = Column(Integer, ForeignKey("race_results.id"), nullable=False)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=True)  # nullable=True に変更（照合前はNull）
    
    # Netkeiba馬ID（照合用）
    netkeiba_horse_id = Column(String(20), nullable=True)  # Netkeibaでの馬ID
    horse_number = Column(Integer, nullable=False)  # 馬番（照合キー）
    
    # 着順情報
    finish_position = Column(Integer, nullable=True)  # 1, 2, 3... (除外・取消の場合null)
    
    # 人気順位
    popularity = Column(Integer, nullable=True)  # 1番人気, 2番人気...
    
    # Relationships
    race_result = relationship("RaceResult", back_populates="horse_results")
    race = relationship("Race")
    horse = relationship("Horse", back_populates="horse_results")
    
    # Index
    __table_args__ = (
        Index('idx_horse_results_race_id', 'race_id'),
        Index('idx_horse_results_horse_id', 'horse_id'),
        Index('idx_horse_results_race_horse_number', 'race_id', 'horse_number'),  # race_id + horse_number で照合
        UniqueConstraint('race_id', 'horse_number', name='uq_race_horse_number'),  # race_id + horse_number でユニーク
    )
    
    def __repr__(self):
        return f"<HorseResult(race_id={self.race_id}, horse_id={self.horse_id}, position={self.finish_position})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "race_result_id": self.race_result_id,
            "race_id": self.race_id,
            "horse_id": self.horse_id,
            "finish_position": self.finish_position,
            "popularity": self.popularity
        }


class Payout(Base):
    """払い戻し情報（1券種1レコード）"""
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    race_result_id = Column(Integer, ForeignKey("race_results.id"), nullable=False)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    
    # 券種（外部キー化）
    bet_type_id = Column(Integer, ForeignKey("bet_types.id"), nullable=False)
    
    # 的中馬番
    winning_numbers = Column(String(50), nullable=False)
    # 単勝: "3"
    # 複勝: "3", "7", "12" (複数レコード)
    
    # 払い戻し額（100円あたり）
    payout_amount = Column(Integer, nullable=False)
    
    # Relationships
    race_result = relationship("RaceResult", back_populates="payouts")
    race = relationship("Race")
    bet_type_ref = relationship("BetType", back_populates="payouts")
    
    # Index
    __table_args__ = (
        Index('idx_payouts_race_id', 'race_id'),
        Index('idx_payouts_bet_type_id', 'bet_type_id'),
    )
    
    def __repr__(self):
        return f"<Payout(race_id={self.race_id}, bet_type_id={self.bet_type_id}, amount={self.payout_amount})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "race_result_id": self.race_result_id,
            "race_id": self.race_id,
            "bet_type_id": self.bet_type_id,
            "bet_type": self.bet_type_ref.to_dict() if self.bet_type_ref else None,
            "winning_numbers": self.winning_numbers,
            "payout_amount": self.payout_amount
        }