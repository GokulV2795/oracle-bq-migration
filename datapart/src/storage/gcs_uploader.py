from pathlib import Path
from google.cloud import storage


class GCSUploader:

    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def upload_file(
        self,
        local_file: str,
        gcs_object: str,
        content_type: str = "application/octet-stream",
    ) -> str:

        blob = self.bucket.blob(gcs_object)

        blob.upload_from_filename(
            local_file,
            content_type=content_type,
        )

        return gcs_object

    def upload_json(
        self,
        json_content: str,
        gcs_object: str,
    ) -> str:

        blob = self.bucket.blob(gcs_object)

        blob.upload_from_string(
            json_content,
            content_type="application/json",
        )

        return gcs_object