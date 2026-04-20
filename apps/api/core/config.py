from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    redis_url: str
    qdrant_url: str
    qdrant_api_key: str
    anthropic_api_key: str
    jwt_secret_key: str
    celery_broker_url: str
    celery_result_backend: str
    app_env: str = "development"


settings = Settings()
