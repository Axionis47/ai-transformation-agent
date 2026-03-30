import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

_DEFAULTS_PATH = Path(__file__).parent.parent / "config" / "defaults.yaml"

# Env var -> config path mappings (dot-separated path into config dict)
_ENV_OVERRIDES: dict[str, str] = {
    "REASONING_MODEL": "models.reasoning_model",
    "SYNTHESIS_MODEL": "models.synthesis_model",
    "GROUNDING_MODEL": "models.grounding_model",
    "GCP_PROJECT_ID": "gcp.project_id",
    "GCP_LOCATION": "gcp.location",
}


def _set_nested(d: dict, path: str, value: Any) -> None:
    keys = path.split(".")
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def load_config() -> dict:
    if not _DEFAULTS_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {_DEFAULTS_PATH}")
    with open(_DEFAULTS_PATH) as f:
        config = yaml.safe_load(f)

    for env_key, config_path in _ENV_OVERRIDES.items():
        env_val = os.getenv(env_key)
        if env_val is not None:
            _set_nested(config, config_path, env_val)

    return config


def freeze_config(overrides: dict | None = None) -> dict:
    config = load_config()
    if overrides:
        for path, value in overrides.items():
            _set_nested(config, path, value)
    return config
