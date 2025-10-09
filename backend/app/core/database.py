from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings, is_sqlite, is_postgresql

Base = declarative_base()

# データベースタイプに応じてエンジンを作成
if is_sqlite():
    # SQLite用（非同期対応）
    DATABASE_URL = settings.DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DB_ECHO,
        # SQLite用の追加設定
        connect_args={"check_same_thread": False}
    )
    
    # 同期エンジン（テーブル作成用）
    sync_engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        connect_args={"check_same_thread": False}
    )
    
elif is_postgresql():
    # PostgreSQL用（非同期対応）
    DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.DB_ECHO
    )
    
    # 同期エンジン（テーブル作成用）
    sync_engine = create_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"),
        echo=settings.DB_ECHO
    )
else:
    raise ValueError("Unsupported database type")

# 非同期セッション
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 同期セッション（必要に応じて）
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=sync_engine
)

async def get_db():
    """非同期データベースセッションの依存性注入"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    """同期データベースセッション（テスト用など）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()