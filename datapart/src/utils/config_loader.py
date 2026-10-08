from pathlib import Path
from typing import Any, Dict, Optional

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "config" / "tables.yaml"


def load_table_config(config_file: Optional[Path] = None) -> Dict[str, Any]:
    """Load and normalize the migration table configuration."""

    config_path = Path(config_file or CONFIG_FILE)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        raise ValueError("tables.yaml must contain a YAML mapping.")

    tables = config.get("tables")

    if tables is None:
        raise ValueError(
            "tables.yaml must contain a top-level 'tables' list."
        )

    if not isinstance(tables, list):
        raise ValueError("'tables' must be a list.")

    normalized_tables = []

    for index, table in enumerate(tables, start=1):
        if not isinstance(table, dict):
            raise ValueError(
                f"Table configuration #{index} must be a mapping."
            )

        normalized = dict(table)

        # Support both the current 'name' field and legacy
        # 'source_table' configuration.
        source_table = (
            normalized.get("source_table")
            or normalized.get("name")
        )

        if not source_table:
            raise ValueError(
                f"Table configuration #{index} is missing "
                "'name' or 'source_table'."
            )

        source_table = str(source_table).strip().upper()

        if not source_table:
            raise ValueError(
                f"Table configuration #{index} has an empty table name."
            )

        normalized["source_table"] = source_table
        normalized.setdefault("name", source_table)
        normalized.setdefault("enabled", True)
        normalized.setdefault(
            "gcs_prefix",
            f"oracle/raw/{source_table}",
        )

        # CDC configuration defaults.
        normalized.setdefault("cdc_enabled", False)
        normalized.setdefault("watermark_column", None)
        normalized.setdefault("primary_key", None)
        normalized.setdefault("batch_size", 50000)

        batch_size = normalized["batch_size"]

        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError(
                f"Invalid batch_size for {source_table}: {batch_size}. "
                "batch_size must be a positive integer."
            )

        if normalized["cdc_enabled"] and not normalized["watermark_column"]:
            raise ValueError(
                f"CDC is enabled for {source_table}, but "
                "'watermark_column' is not configured."
            )

        normalized_tables.append(normalized)

    result = dict(config)
    result["tables"] = normalized_tables

    return result


def get_enabled_tables(
    config_file: Optional[Path] = None,
) -> list[Dict[str, Any]]:
    """Return only enabled tables."""

    config = load_table_config(config_file)

    return [
        table
        for table in config["tables"]
        if table.get("enabled", True)
    ]


def get_table_config(
    table_name: str,
    config_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Return the configuration for one table."""

    table_name = table_name.strip().upper()

    for table in load_table_config(config_file)["tables"]:
        if table["source_table"].upper() == table_name:
            return table

    raise KeyError(
        f"Table '{table_name}' was not found in tables.yaml."
    )
