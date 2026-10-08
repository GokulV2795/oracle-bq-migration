variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "migration_bucket_name" {
  description = "Migration GCS bucket."
  type        = string
}

variable "cloud_run_runtime_service_account" {
  description = "Service account used by the Oracle migration Cloud Run Job."
  type        = string
}