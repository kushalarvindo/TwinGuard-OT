"""
Configuration loader and path resolution utility for TwinGuard-OT.
"""

import os
from pathlib import Path
from typing import Any, Dict
import yaml


def get_project_root() -> Path:
    """Returns the absolute root directory of the TwinGuard-OT project."""
    # This file is located at <project_root>/src/twinguard/utils/config.py
    current_file = Path(__file__).resolve()
    # 3 levels up: utils -> twinguard -> src -> project_root
    return current_file.parent.parent.parent.parent


def load_yaml(file_path: Path | str) -> Dict[str, Any]:
    """Loads and parses a YAML file safely."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def load_system_config(config_path: Path | str | None = None) -> Dict[str, Any]:
    """
    Loads master system configuration.
    Falls back to <project_root>/config/config.yaml if not specified.
    """
    if config_path is None:
        config_path = get_project_root() / "config" / "config.yaml"
    config = load_yaml(config_path)

    # Ensure all configured data directories exist
    root = get_project_root()
    storage = config.get("storage", {})
    for key in ["raw_dir", "processed_dir", "models_dir", "results_dir"]:
        rel_path = storage.get(key, f"data/{key.replace('_dir', '')}")
        abs_dir = root / rel_path
        abs_dir.mkdir(parents=True, exist_ok=True)

    # Resolve db path
    db_rel = storage.get("db_path", "data/twinguard.db")
    storage["db_path_resolved"] = str(root / db_rel)

    return config


def load_modbus_map(map_path: Path | str | None = None) -> Dict[str, Any]:
    """
    Loads Modbus register mapping configuration.
    Falls back to <project_root>/config/modbus_map.yaml if not specified.
    """
    if map_path is None:
        map_path = get_project_root() / "config" / "modbus_map.yaml"
    return load_yaml(map_path)
