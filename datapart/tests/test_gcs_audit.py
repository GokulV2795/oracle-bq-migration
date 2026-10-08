from src.storage.gcs_uploader import GCSUploader


BUCKET_NAME = "mbazzar-oracle-migration-504603"

TEST_OBJECT = (
    "audit/test/"
    "component_test.json"
)

TEST_JSON = """
{
  "test": true,
  "component": "gcs_uploader",
  "status": "SUCCESS"
}
"""


def main():

    print("=" * 70)
    print("TESTING GCS AUDIT UPLOAD")
    print("=" * 70)

    uploader = GCSUploader(BUCKET_NAME)

    uploaded_object = uploader.upload_json(
        TEST_JSON,
        TEST_OBJECT
    )

    print()
    print("GCS upload successful")
    print(f"Bucket : {BUCKET_NAME}")
    print(f"Object : {uploaded_object}")
    print(
        f"URI    : gs://{BUCKET_NAME}/{uploaded_object}"
    )


if __name__ == "__main__":
    main()