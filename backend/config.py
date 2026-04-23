"""
Configuration management for the backend API.
Loads environment variables and provides settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    app_name: str = "AI Boss Decision Engine"
    api_version: str = "v1"
    port: int = 8000

    # Supabase Configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str

    # Database Configuration (direct PostgreSQL if needed)
    database_url: str | None = None

    # LLM Configuration (OpenAI fallback)
    openai_api_key: str | None = None
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7

    # Zhipu AI / GLM Configuration (primary LLM)
    zhipu_api_key: str | None = None
    zhipu_base_url: str = "https://api.ilmu.ai/v1"
    zhipu_model: str = "ilmu-glm-5.1"

    # LangChain Configuration
    langchain_tracing: bool = False
    langchain_api_key: str | None = None

    # Vector Store Configuration
    vector_store_type: str = "chroma"
    chroma_persist_directory: str = "./data/chroma"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
