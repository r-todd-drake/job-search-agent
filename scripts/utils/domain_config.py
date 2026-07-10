# scripts/utils/domain_config.py

from pathlib import Path
import yaml

_DOMAIN_CONFIG_PATH = Path("context/domain/domain_config.yaml")
_config = None


def load():
    global _config
    if _config is None:
        if not _DOMAIN_CONFIG_PATH.exists():
            raise FileNotFoundError(
                f"domain_config.yaml not found at {_DOMAIN_CONFIG_PATH}. "
                "Copy context/domain/domain_config.example.yaml to "
                "context/domain/domain_config.yaml and fill in your domain_label."
            )
        with open(_DOMAIN_CONFIG_PATH, encoding="utf-8") as f:
            _config = yaml.safe_load(f) or {}
    return _config


def get_label():
    """Return the domain_label string from domain_config.yaml."""
    return load()["domain_label"]
