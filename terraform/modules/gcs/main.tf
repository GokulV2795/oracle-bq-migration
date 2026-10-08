resource "google_storage_bucket" "migration" {
  name                        = var.bucket_name
  project                     = var.project_id
  location                    = "ASIA-SOUTH1"
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  public_access_prevention = "enforced"

  versioning {
    enabled = true
  }

  labels = {
    project     = "oracle-bq-migration"
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "oracle-migration"
  }
}