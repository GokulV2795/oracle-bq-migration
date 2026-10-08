resource "google_service_account" "migration" {
  project      = var.project_id
  account_id   = "mbazzar-migration-sa"
  display_name = "MBazzar Oracle to BigQuery Migration"
  description  = "Service account used by the Oracle to GCS and BigQuery migration pipeline."
}

resource "google_project_iam_member" "bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_project_iam_member" "bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_storage_bucket_iam_member" "migration_bucket_admin" {
  bucket = var.migration_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_project_iam_member" "cloud_run_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${var.cloud_run_runtime_service_account}"
}

resource "google_storage_bucket_iam_member" "cloud_run_migration_bucket" {
  bucket = var.migration_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.cloud_run_runtime_service_account}"
}

resource "google_project_iam_member" "cloud_run_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${var.cloud_run_runtime_service_account}"
}