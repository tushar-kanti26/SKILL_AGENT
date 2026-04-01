import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/skill_agent",
    )
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return self.database_url

    def masked_database_url(self) -> str:
        url = self.database_url
        if "@" not in url:
            return url
        prefix, suffix = url.split("@", 1)
        if "://" in prefix:
            scheme, credentials = prefix.split("://", 1)
            if ":" in credentials:
                username = credentials.split(":", 1)[0]
                return f"{scheme}://{username}:***@{suffix}"
        return url

    def uses_local_default_database(self) -> bool:
        return self.database_url.startswith("postgresql+psycopg2://postgres:postgres@localhost") or self.database_url.startswith("postgresql://postgres:postgres@localhost")


settings = Settings()
