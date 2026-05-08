from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    anthropic_api_key: str = ""
    jwt_secret_key: str = "dev-secret-change-in-production"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    app_env: str = "development"
    upload_dir: str = "./uploads"
    qdrant_collection: str = "asset_embeddings"


settings = Settings()
