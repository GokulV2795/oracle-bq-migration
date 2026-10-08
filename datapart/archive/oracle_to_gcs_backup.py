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

from src.connections.oracle_connection import get_oracle_connection
from src.storage.gcs_uploader import GCSUploader


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_FILE = PROJECT_ROOT / "config" / "tables.yaml"


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

    return config


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

def get_source_row_count(connection, table_name: str) -> int:
    """Get source COUNT(*) without loading table data into Python."""

    query = f"""
        SELECT COUNT(*)
        FROM {table_name}
    """

    with connection.cursor() as cursor:
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
# AUDIT JSON → GCS
# ============================================================

def upload_json_to_gcs(
    gcs_uploader: GCSUploader,
    gcs_object: str,
    payload: dict,
) -> str:
    """
    Upload JSON directly through GCSUploader.

    No permanent local JSON file is created.
    """

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
    gcs_uploader: GCSUploader,
    bucket_name: str,
) -> dict:

    table_name = table_config["source_table"]

    gcs_prefix = table_config["gcs_prefix"]

    batch_size = int(
        table_config.get("batch_size", 50000)
    )

    start_time = datetime.now(timezone.utc)

    total_rows = 0
    batch_number = 0
    uploaded_objects = []
    columns = []

    connection = None

    print()
    print("=" * 70)
    print(f"Starting table : {table_name}")
    print(f"Batch size     : {batch_size}")
    print(f"Extract date   : {extract_date}")
    print("=" * 70)

    try:
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
        )

        print(
            f"Source row count: {source_row_count}"
        )

        # ----------------------------------------------------
        # Oracle cursor
        # ----------------------------------------------------

        with connection.cursor() as cursor:

            cursor.arraysize = batch_size
            cursor.prefetchrows = batch_size

            query = f"""
                SELECT *
                FROM {table_name}
            """

            print(
                f"Executing query for {table_name}"
            )

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

                # TemporaryDirectory automatically deletes
                # the local Parquet file here.

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

        # ----------------------------------------------------
        # Do not mark successful if counts don't match.
        # ----------------------------------------------------

        if reconciliation["status"] != "MATCH":
            raise RuntimeError(
                f"Row count mismatch for {table_name}: "
                f"source={source_row_count}, "
                f"extracted={total_rows}, "
                f"difference={reconciliation['difference']}"
            )

        # ========================================================
        # SUCCESS AUDIT
        # ========================================================

        end_time = datetime.now(timezone.utc)

        audit_record = {
            "table_name": table_name,
            "status": "SUCCESS",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "source_row_count": source_row_count,
            "extracted_row_count": total_rows,
            "reconciliation": reconciliation,
            "batch_count": batch_number,
            "batch_size": batch_size,
            "column_count": len(columns),
            "columns": columns,
            "gcs_bucket": bucket_name,
            "gcs_prefix": gcs_prefix,
            "gcs_objects": uploaded_objects,
        }

        audit_object = (
            f"audit/extraction/"
            f"extract_date={extract_date}/"
            f"{table_name}.json"
        )

        upload_json_to_gcs(
            gcs_uploader=gcs_uploader,
            gcs_object=audit_object,
            payload=audit_record,
        )

        print()
        print(
            f"Audit uploaded: gs://"
            f"{bucket_name}/{audit_object}"
        )

        print()
        print("=" * 70)
        print(f"Completed table : {table_name}")
        print(f"Total rows      : {total_rows}")
        print(f"Total batches   : {batch_number}")
        print(f"Total columns   : {len(columns)}")
        print("=" * 70)

        return audit_record

    except Exception as error:

        end_time = datetime.now(timezone.utc)

        audit_record = {
            "table_name": table_name,
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
            "error_message": str(error),
        }

        print()
        print("=" * 70)
        print(f"FAILED table : {table_name}")
        print(f"Error        : {error}")
        print("=" * 70)

        # Try to upload failure audit.
        try:
            audit_object = (
                f"audit/extraction/"
                f"extract_date={extract_date}/"
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
    print("ORACLE → GCS MIGRATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    config = load_table_config()

    extract_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    bucket_name = os.getenv(
        "GCS_BUCKET_NAME"
    )

    if not bucket_name:
        raise ValueError(
            "GCS_BUCKET_NAME is missing from .env"
        )

    print(
        f"GCS bucket: {bucket_name}"
    )

    print(
        f"Extract date: {extract_date}"
    )

    # --------------------------------------------------------
    # Create ONE GCS uploader/client for the entire run.
    # --------------------------------------------------------

    gcs_uploader = GCSUploader(bucket_name)

    audit_records = []

    # --------------------------------------------------------
    # Process enabled tables
    # --------------------------------------------------------

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
            gcs_uploader=gcs_uploader,
            bucket_name=bucket_name,
        )

        audit_records.append(result)

        # ----------------------------------------------------
        # Stop on failure
        # ----------------------------------------------------

        if result["status"] == "FAILED":

            print()
            print(
                "Migration stopped because "
                f"{result['table_name']} failed."
            )

            break

    # --------------------------------------------------------
    # Migration summary
    # --------------------------------------------------------

    summary = upload_run_summary(
        gcs_uploader=gcs_uploader,
        bucket_name=bucket_name,
        extract_date=extract_date,
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
