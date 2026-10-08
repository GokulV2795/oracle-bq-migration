import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from dotenv import load_dotenv
from google.cloud import bigquery

from src.connections.oracle_connection import get_oracle_connection
from src.storage.gcs_uploader import GCSUploader


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "tables.yaml"


# ============================================================
# BIGQUERY CONTROL CONFIGURATION
# ============================================================

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
CONTROL_DATASET = os.getenv("BQ_CONTROL_DATASET", "mbazzar_control")

if not GCP_PROJECT_ID:
    raise ValueError(
        "GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set for watermark lookup."
    )


# ============================================================
# CONFIGURATION
# ============================================================

def load_table_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_FILE}"
        )

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not config or "tables" not in config:
        raise ValueError(
            "tables.yaml must contain a 'tables' section."
        )

    normalized_tables = []

    for table_config in config["tables"]:
        if not isinstance(table_config, dict):
            raise ValueError(
                "Each table entry in tables.yaml must be a mapping."
            )

        normalized = dict(table_config)

        if "source_table" not in normalized:
            if "name" in normalized:
                normalized["source_table"] = normalized["name"]
            else:
                raise ValueError(
                    "Each table entry must include 'name' or 'source_table'."
                )

        if "gcs_prefix" not in normalized:
            normalized["gcs_prefix"] = (
                f"oracle/raw/{normalized['source_table']}"
            )

        if "enabled" not in normalized:
            normalized["enabled"] = normalized.get(
                "cdc_enabled",
                True,
            )

        normalized_tables.append(normalized)

    config["tables"] = normalized_tables
    return config


# ============================================================
# WATERMARK CONTROL
# ============================================================

def get_bigquery_client():
    return bigquery.Client(project=GCP_PROJECT_ID)


def get_watermark_config(table_name: str) -> dict:
    """
    Read the watermark configuration/state for one source table.

    The extractor only READS the watermark. It does not advance it.
    The watermark should be committed later, after the downstream load
    succeeds.
    """

    query = f"""
        SELECT
            source_table,
            watermark_column,
            last_watermark,
            current_watermark,
            last_run_id,
            status
        FROM `{GCP_PROJECT_ID}.{CONTROL_DATASET}.watermarks`
        WHERE UPPER(source_system) = 'ORACLE'
          AND UPPER(source_table) = @source_table
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY source_system, source_table
            ORDER BY updated_at DESC
        ) = 1
    """

    client = get_bigquery_client()

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "source_table",
                "STRING",
                table_name.upper(),
            )
        ]
    )

    rows = list(client.query(query, job_config=job_config).result())

    if not rows:
        raise RuntimeError(
            f"No watermark configuration found for Oracle table {table_name}."
        )

    row = rows[0]

    watermark_column = row["watermark_column"]
    last_watermark = row["last_watermark"]

    if not watermark_column:
        raise RuntimeError(
            f"Watermark column is empty for Oracle table {table_name}."
        )

    return {
        "source_table": row["source_table"],
        "watermark_column": watermark_column,
        "last_watermark": last_watermark,
        "current_watermark": row["current_watermark"],
        "last_run_id": row["last_run_id"],
        "status": row["status"],
    }


# ============================================================
# PARQUET
# ============================================================

def write_parquet(dataframe: pd.DataFrame, output_file: str) -> None:
    """Write only the current batch to compressed Parquet."""

    arrow_table = pa.Table.from_pandas(
        dataframe,
        preserve_index=False,
    )

    pq.write_table(
        arrow_table,
        output_file,
        compression="snappy",
    )


# ============================================================
# ORACLE ROW COUNT
# ============================================================

def get_source_row_count(
    connection,
    table_name: str,
    watermark_column: str,
    last_watermark,
) -> int:
    """Count the exact rows that the extraction query will read."""

    if last_watermark is None:
        query = f"""
            SELECT COUNT(*)
            FROM {table_name}
        """
        params = None
    else:
        query = f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {watermark_column} > :last_watermark
        """
        params = {"last_watermark": oracle_bind_datetime(last_watermark)}

    with connection.cursor() as cursor:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        result = cursor.fetchone()

    return int(result[0])


# ============================================================
# RECONCILIATION
# ============================================================

def reconcile_counts(
    source_row_count: int,
    extracted_row_count: int,
) -> dict:
    difference = source_row_count - extracted_row_count

    return {
        "source_row_count": source_row_count,
        "extracted_row_count": extracted_row_count,
        "difference": difference,
        "status": "MATCH" if difference == 0 else "MISMATCH",
    }


# ============================================================
# WATERMARK VALUE HELPERS
# ============================================================

def normalize_watermark(value):
    """Normalize Oracle/Pandas datetime values for audit serialization."""

    if value is None or pd.isna(value):
        return None

    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")

    return timestamp.to_pydatetime()


def oracle_bind_datetime(value):
    """Return a timezone-naive UTC datetime for Oracle TIMESTAMP binds."""

    normalized = normalize_watermark(value)
    if normalized is None:
        return None
    return normalized.replace(tzinfo=None)


def get_max_watermark_from_dataframe(dataframe: pd.DataFrame, watermark_column: str):
    """Return MAX(watermark_column) from the current batch."""

    if watermark_column not in dataframe.columns:
        raise RuntimeError(
            f"Watermark column {watermark_column} was not returned by Oracle."
        )

    values = dataframe[watermark_column].dropna()

    if values.empty:
        return None

    return normalize_watermark(values.max())


def format_watermark(value):
    if value is None:
        return None

    normalized = normalize_watermark(value)
    return normalized.isoformat() if normalized else None


# ============================================================
# AUDIT JSON → GCS
# ============================================================

def upload_json_to_gcs(
    gcs_uploader: GCSUploader,
    gcs_object: str,
    payload: dict,
) -> str:
    """Upload JSON directly through GCSUploader."""

    json_content = json.dumps(
        payload,
        indent=2,
        default=str,
    )

    return gcs_uploader.upload_json(
        json_content=json_content,
        gcs_object=gcs_object,
    )


# ============================================================
# EXTRACT ONE TABLE
# ============================================================

def extract_table(
    table_config: dict,
    extract_date: str,
    run_id: str,
    gcs_uploader: GCSUploader,
    bucket_name: str,
) -> dict:

    table_name = table_config["source_table"]
    gcs_prefix = table_config["gcs_prefix"]
    batch_size = int(table_config.get("batch_size", 50000))

    start_time = datetime.now(timezone.utc)

    total_rows = 0
    batch_number = 0
    uploaded_objects = []
    columns = []
    current_watermark = None
    connection = None

    print()
    print("=" * 70)
    print(f"Starting table : {table_name}")
    print(f"Batch size     : {batch_size}")
    print(f"Extract date   : {extract_date}")
    print(f"Run ID         : {run_id}")
    print("=" * 70)

    try:
        # ----------------------------------------------------
        # Read watermark state from BigQuery control table
        # ----------------------------------------------------

        watermark_state = get_watermark_config(table_name)
        watermark_column = watermark_state["watermark_column"]
        last_watermark = watermark_state["last_watermark"]

        load_type = "FULL" if last_watermark is None else "INCREMENTAL"

        print(f"Load type      : {load_type}")
        print(f"Watermark col  : {watermark_column}")
        print(
            f"Last watermark : "
            f"{format_watermark(last_watermark) or 'NULL'}"
        )

        # ----------------------------------------------------
        # Oracle connection
        # ----------------------------------------------------

        connection = get_oracle_connection()

        print(
            f"Oracle connection established for {table_name}"
        )

        # ----------------------------------------------------
        # Source count
        # ----------------------------------------------------

        source_row_count = get_source_row_count(
            connection,
            table_name,
            watermark_column,
            last_watermark,
        )

        print(
            f"Source rows for {load_type}: {source_row_count}"
        )

        # ----------------------------------------------------
        # Oracle cursor
        # ----------------------------------------------------

        with connection.cursor() as cursor:
            cursor.arraysize = batch_size
            cursor.prefetchrows = batch_size

            if last_watermark is None:
                query = f"""
                    SELECT *
                    FROM {table_name}
                """
                query_params = None
            else:
                query = f"""
                    SELECT *
                    FROM {table_name}
                    WHERE {watermark_column} > :last_watermark
                """
                query_params = {"last_watermark": oracle_bind_datetime(last_watermark)}

            print(
                f"Executing {load_type} query for {table_name}"
            )

            if query_params:
                cursor.execute(query, query_params)
            else:
                cursor.execute(query)

            columns = [
                column[0]
                for column in cursor.description
            ]

            print(
                f"Columns discovered: {len(columns)}"
            )

            # ------------------------------------------------
            # Batch extraction
            # ------------------------------------------------

            while True:
                rows = cursor.fetchmany(batch_size)

                if not rows:
                    break

                batch_number += 1
                row_count = len(rows)
                total_rows += row_count

                print()
                print(
                    f"{table_name} | "
                    f"Load: {load_type} | "
                    f"Batch: {batch_number} | "
                    f"Rows: {row_count} | "
                    f"Total: {total_rows} / {source_row_count}"
                )

                # ------------------------------------------------
                # Current batch only
                # ------------------------------------------------

                dataframe = pd.DataFrame(
                    rows,
                    columns=columns,
                )

                batch_watermark = get_max_watermark_from_dataframe(
                    dataframe,
                    watermark_column,
                )

                if batch_watermark is not None:
                    if (
                        current_watermark is None
                        or batch_watermark > current_watermark
                    ):
                        current_watermark = batch_watermark

                # ------------------------------------------------
                # Temporary Parquet
                # ------------------------------------------------

                with tempfile.TemporaryDirectory() as temp_dir:
                    local_file = (
                        Path(temp_dir)
                        / f"part-{batch_number:05d}.parquet"
                    )

                    write_parquet(
                        dataframe,
                        str(local_file),
                    )

                    # ------------------------------------------------
                    # GCS object
                    # ------------------------------------------------

                    gcs_object = (
                        f"{gcs_prefix}/"
                        f"extract_date={extract_date}/"
                        f"run_id={run_id}/"
                        f"part-{batch_number:05d}.parquet"
                    )

                    # ------------------------------------------------
                    # Upload immediately
                    # ------------------------------------------------

                    gcs_uploader.upload_file(
                        local_file=str(local_file),
                        gcs_object=gcs_object,
                        content_type="application/vnd.apache.parquet",
                    )

                    uploaded_objects.append(gcs_object)

                    print(
                        f"Uploaded: gs://"
                        f"{bucket_name}/"
                        f"{gcs_object}"
                    )

                del dataframe
                del rows

        # ========================================================
        # RECONCILIATION
        # ========================================================

        reconciliation = reconcile_counts(
            source_row_count=source_row_count,
            extracted_row_count=total_rows,
        )

        print()
        print("-" * 70)
        print("RECONCILIATION")
        print("-" * 70)
        print(
            f"Source rows     : "
            f"{reconciliation['source_row_count']}"
        )
        print(
            f"Extracted rows  : "
            f"{reconciliation['extracted_row_count']}"
        )
        print(
            f"Difference      : "
            f"{reconciliation['difference']}"
        )
        print(
            f"Status          : "
            f"{reconciliation['status']}"
        )
        print("-" * 70)

        if reconciliation["status"] != "MATCH":
            raise RuntimeError(
                f"Row count mismatch for {table_name}: "
                f"source={source_row_count}, "
                f"extracted={total_rows}, "
                f"difference={reconciliation['difference']}"
            )

        # --------------------------------------------------------
        # No changed rows in an incremental run.
        # Keep the previous successful watermark unchanged.
        # --------------------------------------------------------

        if current_watermark is None:
            current_watermark = normalize_watermark(last_watermark)

        # ========================================================
        # SUCCESS AUDIT
        # ========================================================

        end_time = datetime.now(timezone.utc)

        audit_record = {
            "table_name": table_name,
            "run_id": run_id,
            "status": "SUCCESS",
            "load_type": load_type,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "source_row_count": source_row_count,
            "extracted_row_count": total_rows,
            "reconciliation": reconciliation,
            "batch_count": batch_number,
            "batch_size": batch_size,
            "column_count": len(columns),
            "columns": columns,
            "watermark_column": watermark_column,
            "last_watermark": format_watermark(last_watermark),
            "current_watermark": format_watermark(current_watermark),
            "watermark_advanced": (
                last_watermark is None
                or (
                    current_watermark is not None
                    and current_watermark > normalize_watermark(last_watermark)
                )
            ),
            "watermark_commit_required": True,
            "gcs_bucket": bucket_name,
            "gcs_prefix": (
                f"gs://{bucket_name}/"
                f"{gcs_prefix}/"
                f"extract_date={extract_date}/"
                f"run_id={run_id}/"
            ),
            "gcs_objects": uploaded_objects,
        }

        audit_object = (
            f"audit/extraction/"
            f"extract_date={extract_date}/"
            f"run_id={run_id}/"
            f"{table_name}.json"
        )

        upload_json_to_gcs(
            gcs_uploader=gcs_uploader,
            gcs_object=audit_object,
            payload=audit_record,
        )

        print()
        print(
            f"Current watermark: "
            f"{format_watermark(current_watermark) or 'NULL'}"
        )
        print(
            "Watermark status : READ ONLY - commit handled downstream"
        )
        print()
        print(
            f"Audit uploaded: gs://"
            f"{bucket_name}/{audit_object}"
        )

        print()
        print("=" * 70)
        print(f"Completed table : {table_name}")
        print(f"Load type       : {load_type}")
        print(f"Run ID          : {run_id}")
        print(f"Total rows      : {total_rows}")
        print(f"Total batches   : {batch_number}")
        print(f"Total columns   : {len(columns)}")
        print("=" * 70)

        return audit_record

    except Exception as error:
        end_time = datetime.now(timezone.utc)

        audit_record = {
            "table_name": table_name,
            "run_id": run_id,
            "status": "FAILED",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "source_row_count": locals().get(
                "source_row_count",
                None,
            ),
            "extracted_row_count": total_rows,
            "batch_count": batch_number,
            "batch_size": batch_size,
            "watermark_column": locals().get(
                "watermark_column",
                None,
            ),
            "last_watermark": format_watermark(
                locals().get("last_watermark")
            ),
            "current_watermark": format_watermark(
                locals().get("current_watermark")
            ),
            "error_message": str(error),
        }

        print()
        print("=" * 70)
        print(f"FAILED table : {table_name}")
        print(f"Error        : {error}")
        print("=" * 70)

        try:
            audit_object = (
                f"audit/extraction/"
                f"extract_date={extract_date}/"
                f"run_id={run_id}/"
                f"{table_name}.json"
            )

            upload_json_to_gcs(
                gcs_uploader=gcs_uploader,
                gcs_object=audit_object,
                payload=audit_record,
            )

            print(
                f"Failure audit uploaded: gs://"
                f"{bucket_name}/{audit_object}"
            )

        except Exception as audit_error:
            print(
                "WARNING: Could not upload failure audit: "
                f"{audit_error}"
            )

        return audit_record

    finally:
        if connection is not None:
            connection.close()
            print(
                f"Oracle connection closed for {table_name}"
            )


# ============================================================
# RUN SUMMARY → GCS
# ============================================================

def upload_run_summary(
    gcs_uploader: GCSUploader,
    bucket_name: str,
    extract_date: str,
    run_id: str,
    audit_records: list,
) -> dict:

    successful_tables = sum(
        1
        for record in audit_records
        if record["status"] == "SUCCESS"
    )

    failed_tables = sum(
        1
        for record in audit_records
        if record["status"] == "FAILED"
    )

    summary = {
        "extract_date": extract_date,
        "run_id": run_id,
        "run_end_time": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_tables_processed": len(audit_records),
        "successful_tables": successful_tables,
        "failed_tables": failed_tables,
        "tables": audit_records,
    }

    summary_object = (
        f"audit/runs/"
        f"extract_date={extract_date}/"
        f"run_id={run_id}/"
        f"migration_summary.json"
    )

    upload_json_to_gcs(
        gcs_uploader=gcs_uploader,
        gcs_object=summary_object,
        payload=summary,
    )

    print()
    print(
        f"Run summary uploaded: gs://"
        f"{bucket_name}/{summary_object}"
    )

    return summary


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("ORACLE → GCS MIGRATION - WATERMARK CDC EXTRACTION")
    print("=" * 70)

    config = load_table_config()

    run_start_time = datetime.now(timezone.utc)
    extract_date = run_start_time.strftime("%Y-%m-%d")
    run_id = run_start_time.strftime("%Y%m%d_%H%M%S")

    bucket_name = os.getenv("GCS_BUCKET_NAME")

    if not bucket_name:
        raise ValueError(
            "GCS_BUCKET_NAME is missing from .env"
        )

    print(f"GCS bucket: {bucket_name}")
    print(f"Extract date: {extract_date}")
    print(f"Run ID: {run_id}")
    print(f"Control dataset: {GCP_PROJECT_ID}.{CONTROL_DATASET}")

    gcs_uploader = GCSUploader(bucket_name)
    audit_records = []

    for table_config in config["tables"]:
        table_name = table_config["source_table"]

        if not table_config.get("enabled", False):
            print(
                f"Skipping disabled table: {table_name}"
            )
            continue

        result = extract_table(
            table_config=table_config,
            extract_date=extract_date,
            run_id=run_id,
            gcs_uploader=gcs_uploader,
            bucket_name=bucket_name,
        )

        audit_records.append(result)

        if result["status"] == "FAILED":
            print()
            print(
                "Migration stopped because "
                f"{result['table_name']} failed."
            )
            break

    summary = upload_run_summary(
        gcs_uploader=gcs_uploader,
        bucket_name=bucket_name,
        extract_date=extract_date,
        run_id=run_id,
        audit_records=audit_records,
    )

    print()
    print("=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(
        f"Successful tables : "
        f"{summary['successful_tables']}"
    )
    print(
        f"Failed tables     : "
        f"{summary['failed_tables']}"
    )
    print(
        f"Audit location    : "
        f"gs://{bucket_name}/audit/"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
