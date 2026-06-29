from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
<<<<<<< HEAD
    DATABASE_URL: str  # Must be provided via .env
=======
    DATABASE_URL: str = "mysql+pymysql://root:rootpassword@localhost:3306/urlshortener"
>>>>>>> 9cd0f390705f6c3b83b1ed503d696fd316e74f67
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 10
    RATE_LIMIT_WINDOW: int = 60
    
    # Caching
    CACHE_EXPIRY: int = 3600
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
