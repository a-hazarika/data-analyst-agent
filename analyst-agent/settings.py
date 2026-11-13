from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    readonly_database_url: str
    anthropic_api_key: str
    model_name: str
    
settings = Settings()