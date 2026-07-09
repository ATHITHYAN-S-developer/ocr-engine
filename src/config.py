import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    APP_NAME: str = "Enterprise OCR Engine"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Security
    JWT_SECRET_KEY: str = Field(default="supersecretkeythatshouldbechangedinproduction", alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Database (PostgreSQL)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ocr_db"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis / Celery
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @computed_field
    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @computed_field
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # Storage Abstraction (local, s3, minio, gcs, azure)
    STORAGE_PROVIDER: str = "local"  # "local", "s3", "minio", "gcs", "azure"
    STORAGE_LOCAL_DIR: str = "uploads"
    
    # AWS S3 / MinIO Settings
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET_NAME: str = "ocr-engine-bucket"
    AWS_S3_ENDPOINT_URL: Optional[str] = None  # Needed for MinIO or localstack

    # Pluggable OCR Engine Configuration
    # Options: "mock", "easyocr", "paddleocr", "trocr"
    OCR_RECOGNITION_ENGINE: str = "mock"

settings = Settings()
