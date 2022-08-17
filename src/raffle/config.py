import string
from typing import Literal

import pydantic
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # application settings
    manager_ip_addresses: list[str] = []
    participate_max_attempts: pydantic.PositiveInt = 3
    participate_ticket_pool: pydantic.PositiveInt = 10
    verification_code_allowed_characters: str = string.ascii_uppercase
    verification_code_crypt_algorithm: Literal["bf", "des", "md5", "xdes"] = "bf"
    verification_code_length: pydantic.PositiveInt = 8

    # database settings
    db_database: str = Field(..., env="PGDATABASE")
    db_host: str = Field(..., env="PGHOST")
    db_password: pydantic.SecretStr = Field(..., env="PGPASSWORD")
    db_port: str = Field(..., env="PGPORT")
    db_user: str = Field(..., env="PGUSER")

    class Config:
        env_file = ".env"

    def __hash__(self):
        return hash(repr(self))

    @property
    def db_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_database}"


def load_settings() -> Settings:
    return Settings()
