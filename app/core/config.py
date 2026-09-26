"""
Purpose: Configures global application settings and storage directory paths.
Flow:
      1. Define Pydantic settings attributes and defaults.
      2. Construct host directory paths for SQLite database and audio files.
      3. Execute storage directory creation on module initialization.
Inputs: Environment variables or .env file parameters.
Outputs: Exposes global settings singleton instance.
"""

import pathlib

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Purpose: Manages environment configuration and local file path declarations.
    Flow:
          1. Store application name and debug flags.
          2. Compute host path targets for application database and local audio storage.
          3. Ensure required directories exist on local filesystem.
    Inputs: Environment variable inputs or default config fallbacks.
    Outputs: Initialized settings instance with configured directory paths.
    """

    PROJECT_NAME: str = "Synapse AI Minutes Studio"
    DEBUG: bool = True


    # Storage Directories (Relative to current execution root)
    BASE_DATA_DIR: pathlib.Path = pathlib.Path.cwd() / ".data"
    AUDIO_STORAGE_DIR: pathlib.Path = BASE_DATA_DIR / "audio"

    # SQLite Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DATA_DIR}/app_data.db"

    def setup_directories(self) -> None:
        """
        Purpose: Creates required storage directories on host filesystem.
        Flow:
              1. Evaluate target audio storage directory path.
              2. Recursively create parent directories if missing on disk.
        Inputs: None.
        Outputs: None.
        """
        self.AUDIO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    class Config:
        env_file = ".env"


settings = Settings()
settings.setup_directories()