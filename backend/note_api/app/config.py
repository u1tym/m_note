from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "tamtdb"
    db_user: str = "tamtuser"
    db_password: str = ""

    secret_key: str = "debug-local-only"
    algorithm: str = "HS256"
    cookie_name: str = "access_token"
    cors_origins: str = ""

    # デバッグ時は JWT を使わず debug_aid をアカウント ID として使う（for_human_memo/02_note.txt）
    debug: bool = False
    debug_aid: int = 1

    # パーツ置き換え時に保持する過去世代数（jpeg / png / binary）
    parts_max_revisions: int = 3

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins.strip():
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
