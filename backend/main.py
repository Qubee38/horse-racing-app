from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import races, predictions, ai_commentary, admin, selenium_test, race_results, statistics  # Seleniumテスト用に追加
from app.core.database import Base, sync_engine
from app.core.config import settings, is_sqlite, is_postgresql
from app.models import race, horse, prediction  # prediction モデルを追加
from app.ml.predictor import predictor  # 統合予測エンジンをインポート

import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Horse Racing Prediction API",
    version="1.0.0",
    description="競馬予測アプリのバックエンドAPI"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーターを登録
app.include_router(races.router, prefix="/api", tags=["races"])
app.include_router(predictions.router, prefix="/api", tags=["predictions"])  # 予測APIルーターを追加
app.include_router(ai_commentary.router, prefix="/api", tags=["ai-commentary"])  # 生成AI解説ルーターを追加
app.include_router(admin.router, prefix="/api", tags=["admin"])  # admin管理ルーターを追加
app.include_router(race_results.router, prefix="/api/race-results", tags=["race-results"])  # レース結果取得ルーターを追加
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])  # 統計APIルーターを追加
app.include_router(selenium_test.router, prefix="/api", tags=["selenium-test"])  # Seleniumテスト用ルーターを追加


@app.get("/")
async def root():
    db_type = "SQLite" if is_sqlite() else "PostgreSQL" if is_postgresql() else "Unknown"
    
    # 予測エンジンの状態も表示
    predictor_status = "loaded" if predictor.is_loaded else "not_loaded"
    model_type = "legacy" if predictor.use_legacy else "new" if predictor.is_loaded else "unknown"
    
    return {
        "message": "Horse Racing Prediction API", 
        "version": "1.0.0",
        "database": db_type,
        "environment": settings.ENVIRONMENT,
        "predictor_status": predictor_status,
        "model_type": model_type,
        "features": {
            "integrated_prediction": True,
            "netkeiba_scraping": True,
            "batch_processing": True
        }
    }

@app.get("/health")
async def health_check():
    db_type = "sqlite" if is_sqlite() else "postgresql" if is_postgresql() else "unknown"
    
    # 予測エンジンのヘルスチェック
    predictor_health = "healthy" if predictor.is_loaded else "unhealthy"
    
    return {
        "status": "healthy", 
        "database": db_type,
        "predictor": predictor_health
    }

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    try:
        # データベース初期化
        Base.metadata.create_all(bind=sync_engine)
        db_type = "SQLite" if is_sqlite() else "PostgreSQL"
        logger.info(f"Database tables created successfully using {db_type}")
        
        # 予測エンジンの初期化
        logger.info("Initializing integrated prediction engine...")
        model_loaded = predictor.load_models()
        
        if model_loaded:
            model_info = predictor.get_model_info()
            logger.info(f"Prediction models loaded successfully:")
            logger.info(f"  - Model type: {model_info.get('model_type', 'unknown')}")
            logger.info(f"  - Feature count: {model_info.get('feature_count', 0)}")
            logger.info(f"  - Models path: {model_info.get('models_path', 'unknown')}")
        else:
            logger.warning("Failed to load prediction models - prediction features will be limited")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        # 起動は継続するが、エラーログを残す

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("Application shutdown initiated")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 開発時の自動リロード
        log_level="info"
    )