from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionSettings(BaseSettings):

    # Application
    ENVIRONMENT: str = "local"
    DEBUG: bool = False

    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5434
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6381
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    # Government sources
    SEC_EDGAR_BASE_URL: str = "https://efts.sec.gov/LATEST/search-index"
    SEC_EDGAR_SUBMISSIONS_URL: str = "https://data.sec.gov/submissions"
    GOVTRACK_BASE_URL: str = "https://www.govtrack.us/api/v2"
    USASPENDING_BASE_URL: str = "https://api.usaspending.gov/api/v2"
    OPENSECRETS_API_KEY: str = ""

    # Ingestion settings
    BATCH_SIZE: int = 100
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "argos-raw-data"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = IngestionSettings()