import os

from dotenv import load_dotenv
from google.cloud import storage


load_dotenv()


def main():
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = os.getenv("GCS_BUCKET_NAME")

    client = storage.Client(project=project_id)

    bucket = client.bucket(bucket_name)

    exists = bucket.exists()

    print(f"GCP project: {project_id}")
    print(f"GCS bucket: {bucket_name}")
    print(f"Bucket exists: {exists}")


if __name__ == "__main__":
    main()