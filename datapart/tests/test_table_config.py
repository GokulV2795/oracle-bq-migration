import yaml

from src.utils import config_loader


def test_load_table_config_normalizes_legacy_schema(tmp_path):
    config_path = tmp_path / "tables.yaml"

    config_path.write_text(
        yaml.safe_dump(
            {
                "tables": [
                    {
                        "name": "MB_CUSTOMERS",
                        "primary_key": "CUSTOMER_ID",
                        "watermark_column": "UPDATED_DATE",
                        "cdc_enabled": True,
                        "batch_size": 50000,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = config_loader.load_table_config(config_path)

    assert result["tables"][0]["source_table"] == "MB_CUSTOMERS"
    assert result["tables"][0]["name"] == "MB_CUSTOMERS"
    assert result["tables"][0]["enabled"] is True
    assert (
        result["tables"][0]["gcs_prefix"]
        == "oracle/raw/MB_CUSTOMERS"
    )
    assert result["tables"][0]["primary_key"] == "CUSTOMER_ID"
    assert result["tables"][0]["watermark_column"] == "UPDATED_DATE"
    assert result["tables"][0]["cdc_enabled"] is True
    assert result["tables"][0]["batch_size"] == 50000