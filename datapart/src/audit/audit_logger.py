import json
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_audit_record(
    *,
    table_name: str,
    status: str,
    start_time: str,
    end_time: str,
    source_row_count: int,
    extracted_row_count: int,
    batch_count: int,
    batch_size: int,
    columns: list[str],
    gcs_bucket: str,
    gcs_prefix: str,
    gcs_objects: list[str],
    reconciliation_status: str,
    reconciliation_difference: int,
) -> dict[str, Any]:

    return {
        "table_name": table_name,
        "status": status,
        "start_time": start_time,
        "end_time": end_time,

        "source": {
            "row_count": source_row_count,
            "column_count": len(columns),
            "columns": columns,
        },

        "extraction": {
            "row_count": extracted_row_count,
            "batch_count": batch_count,
            "batch_size": batch_size,
        },

        "reconciliation": {
            "status": reconciliation_status,
            "difference": reconciliation_difference,
        },

        "target": {
            "gcs_bucket": gcs_bucket,
            "gcs_prefix": gcs_prefix,
            "object_count": len(gcs_objects),
            "objects": gcs_objects,
        },
    }


def audit_to_json(audit_record: dict[str, Any]) -> str:
    return json.dumps(
        audit_record,
        indent=2,
        default=str,
    )