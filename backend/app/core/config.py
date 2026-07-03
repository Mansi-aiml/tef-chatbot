from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/tef_chatbot"

    chroma_persist_dir: str = "./chroma_data"

    confidence_threshold: float = 0.6

    frontend_origin: str = "http://localhost:5173"


settings = Settings()
