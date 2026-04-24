"""
Configuration management for the backend API.
Loads environment variables and provides settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
from typing import Optional
import os

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    app_name: str = "AI Boss Decision Engine"
    api_version: str = "v1"
    port: int = 8000

    # Supabase Configuration (optional in local-filesystem stage)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None

    # Database Configuration (direct PostgreSQL if needed)
    database_url: Optional[str] = None

    # LLM Configuration (manager + document extraction)
    google_api_key: Optional[str] = None
    llm_provider: str = "zhipu"
    openai_api_key: Optional[str] = None
    llm_model: str = "ilmu-glm-5.1"
    llm_temperature: float = 0.7

    # LangChain Configuration
    langchain_tracing: bool = False
    langchain_api_key: Optional[str] = None

    # Vector Store Configuration
    vector_store_type: str = "chroma"  # "chroma" or "faiss"
    chroma_persist_directory: str = "./data/chroma"

    # Cloudinary (document upload pipeline)
    cloudinary_url: Optional[str] = None

    # Zhipu AI (data writer / SQL generation)
    zhipu_api_key: Optional[str] = None
    zhipu_base_url: str = "https://api.ilmu.ai/v1"
    zhipu_model: str = "nemo-super"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
