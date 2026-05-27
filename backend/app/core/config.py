from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_BACKEND_DIR / ".env", extra="ignore")

    anthropic_api_key: str = ""
    planner_model: str = "claude-sonnet-4-6"
    data_path: Path = _REPO_ROOT / "data" / "Vendor-Payments_2021-23_FY_2023_.csv"
    log_dir: Path = _REPO_ROOT / "logs"
    cors_allow_origins: list[str] = ["http://localhost:5173"]
    cors_allow_origin_regex: str = r"http://localhost:\d+"


settings = Settings()
