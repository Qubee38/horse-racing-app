from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os

class Settings(BaseSettings):
    # プロジェクトルート取得
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # データディレクトリ
    DATA_DIR: Path = BASE_DIR / "data"
    
    # データベース設定（動的に生成）
    _DATABASE_URL: Optional[str] = None
    
    @property
    def DATABASE_URL(self) -> str:
        """データベースURLを返す（環境変数または自動生成）"""
        if self._DATABASE_URL:
            return self._DATABASE_URL
        # デフォルト: プロジェクトルートのdata/horse_racing.db
        db_path = self.DATA_DIR / "horse_racing.db"
        return f"sqlite:///{db_path}"
    
    # セキュリティ
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    
    # 環境設定
    ENVIRONMENT: str = "development"
    
    # データベースエンジン設定
    DB_ECHO: bool = True  # SQLログ出力（開発時のみ）
    
    # Anthropic Claude API
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # CORS設定（カンマ区切りで複数URL対応）
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins(self) -> list:
        """CORS許可オリジンのリストを返す"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()

# データディレクトリ作成（重要）
os.makedirs(settings.DATA_DIR, exist_ok=True)

# データベースURLからエンジンタイプを判定
def is_sqlite() -> bool:
    return settings.DATABASE_URL.startswith("sqlite")

def is_postgresql() -> bool:
    return settings.DATABASE_URL.startswith("postgresql")