resource "google_bigquery_dataset" "raw" {
  project    = var.project_id
  dataset_id = var.raw_dataset
  location   = var.location

  description = "RAW layer for Oracle MBazzar migration."

  labels = {
    environment = var.environment
    layer       = "raw"
    managed_by  = "terraform"
  }
}

resource "google_bigquery_dataset" "staging" {
  project    = var.project_id
  dataset_id = var.staging_dataset
  location   = var.location

  description = "STAGING layer for transformed Oracle data."

  labels = {
    environment = var.environment
    layer       = "staging"
    managed_by  = "terraform"
  }
}

resource "google_bigquery_dataset" "core" {
  project    = var.project_id
  dataset_id = var.core_dataset
  location   = var.location

  description = "CORE business layer for MBazzar."

  labels = {
    environment = var.environment
    layer       = "core"
    managed_by  = "terraform"
  }
}

resource "google_bigquery_dataset" "mart" {
  project    = var.project_id
  dataset_id = var.mart_dataset
  location   = var.location

  description = "MART analytical layer for MBazzar."

  labels = {
    environment = var.environment
    layer       = "mart"
    managed_by  = "terraform"
  }
}

resource "google_bigquery_dataset" "control" {
  project    = var.project_id
  dataset_id = var.control_dataset
  location   = var.location

  description = "Migration control and audit metadata."

  delete_contents_on_destroy = false
}