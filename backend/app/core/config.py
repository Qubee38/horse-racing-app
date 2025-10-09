from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # データベース設定（SQLiteがデフォルト、PostgreSQL対応も含む）
    DATABASE_URL: str = "sqlite:///./horse_racing.db"
    # 将来PostgreSQLに変更する場合: "postgresql://user:password@localhost:5432/horse_racing"
    
    SECRET_KEY: str = "your-secret-key-here"
    
    # 開発/本番環境の切り替え
    ENVIRONMENT: str = "development"
    
    # データベースエンジン設定
    DB_ECHO: bool = True  # SQLログ出力（開発時のみ）

    # AI Commentary用: Claude API Key（修正: Optional型に変更）
    ANTHROPIC_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "allow"  # または "ignore"

settings = Settings()

# データベースURLからエンジンタイプを判定
def is_sqlite() -> bool:
    return settings.DATABASE_URL.startswith("sqlite")

def is_postgresql() -> bool:
    return settings.DATABASE_URL.startswith("postgresql")