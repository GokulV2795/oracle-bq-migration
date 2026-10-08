from src.validation.reconciliation import reconcile_counts
from src.audit.audit_logger import build_audit_record, audit_to_json


def main():

    print("=" * 70)
    print("TESTING MIGRATION COMPONENTS")
    print("=" * 70)

    # ---------------------------------------------------------
    # Test reconciliation
    # ---------------------------------------------------------

    result = reconcile_counts(
        source_row_count=10,
        extracted_row_count=10,
    )

    print("\nReconciliation")
    print("----------------")
    print(f"Source rows     : {result.source_row_count}")
    print(f"Extracted rows  : {result.extracted_row_count}")
    print(f"Difference      : {result.difference}")
    print(f"Status          : {result.status}")

    # ---------------------------------------------------------
    # Test audit
    # ---------------------------------------------------------

    audit = build_audit_record(
        table_name="MB_CUSTOMERS",
        status="SUCCESS",
        start_time="2026-09-25T11:52:10+00:00",
        end_time="2026-09-25T11:52:13+00:00",
        source_row_count=10,
        extracted_row_count=10,
        batch_count=4,
        batch_size=3,
        columns=[
            "CUSTOMER_ID",
            "CUSTOMER_CODE",
            "FIRST_NAME",
            "LAST_NAME",
            "EMAIL",
            "PHONE",
            "GENDER",
            "DATE_OF_BIRTH",
            "CITY",
            "STATE",
            "COUNTRY",
            "CUSTOMER_STATUS",
            "CREATED_AT",
            "UPDATED_AT",
        ],
        gcs_bucket="mbazzar-oracle-migration-504603",
        gcs_prefix="oracle/raw/MB_CUSTOMERS",
        gcs_objects=[
            "oracle/raw/MB_CUSTOMERS/extract_date=2026-09-25/part-00001.parquet",
            "oracle/raw/MB_CUSTOMERS/extract_date=2026-09-25/part-00002.parquet",
            "oracle/raw/MB_CUSTOMERS/extract_date=2026-09-25/part-00003.parquet",
            "oracle/raw/MB_CUSTOMERS/extract_date=2026-09-25/part-00004.parquet",
        ],
        reconciliation_status=result.status,
        reconciliation_difference=result.difference,
    )

    print("\nAudit JSON")
    print("----------------")
    print(audit_to_json(audit))

    print("\nComponent tests completed successfully.")


if __name__ == "__main__":
    main()