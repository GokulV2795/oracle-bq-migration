variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "Default GCP region."
  type        = string
}

variable "bigquery_location" {
  description = "BigQuery dataset location."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "migration_bucket_name" {
  description = "GCS bucket used for Oracle to BigQuery migration."
  type        = string
}

variable "raw_dataset" {
  description = "BigQuery raw dataset."
  type        = string
}

variable "staging_dataset" {
  description = "BigQuery staging dataset."
  type        = string
}

variable "core_dataset" {
  description = "BigQuery core dataset."
  type        = string
}

variable "mart_dataset" {
  description = "BigQuery mart dataset."
  type        = string
}

variable "cloud_run_job_name" {
  description = "Oracle migration Cloud Run Job name."
  type        = string
}

variable "cloud_run_image" {
  description = "Oracle migration container image."
  type        = string
}

variable "cloud_run_service_account" {
  description = "Cloud Run runtime service account."
  type        = string
}

variable "oracle_password_secret" {
  description = "Oracle password Secret Manager secret."
  type        = string
}

variable "oracle_port_secret" {
  description = "Oracle port Secret Manager secret."
  type        = string
}

variable "oracle_service_secret" {
  description = "Oracle service Secret Manager secret."
  type        = string
}

variable "oracle_username_secret" {
  description = "Oracle username Secret Manager secret."
  type        = string
}



variable "control_dataset" {
  description = "BigQuery dataset for migration control and audit metadata."
  type        = string
  default     = "mbazzar_control"
}