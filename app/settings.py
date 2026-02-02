from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    openai_api_key: str
    openai_model: str = "gpt-4.1"
    openai_embed_model: str = "text-embedding-3-large"

    # Crawl4AI Docker container base URL (e.g. http://crawl4ai:11235 in compose)
    crawl4ai_base_url: str = "http://localhost:11235"

    chunk_size: int = 1200
    chunk_overlap: int = 150

settings = Settings()
