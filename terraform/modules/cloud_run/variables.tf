variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "Cloud Run region."
  type        = string
}

variable "job_name" {
  description = "Cloud Run Job name."
  type        = string
}

variable "image" {
  description = "Container image for the migration job."
  type        = string
}

variable "service_account_email" {
  description = "Cloud Run Job runtime service account."
  type        = string
}

variable "gcs_bucket_name" {
  description = "Migration GCS bucket."
  type        = string
}

variable "bigquery_location" {
  description = "BigQuery location."
  type        = string
}

variable "memory" {
  description = "Cloud Run container memory."
  type        = string
  default     = "512Mi"
}

variable "cpu" {
  description = "Cloud Run container CPU."
  type        = string
  default     = "1000m"
}

variable "timeout" {
  description = "Cloud Run Job task timeout."
  type        = string
  default     = "600s"
}

variable "max_retries" {
  description = "Maximum Cloud Run task retries."
  type        = number
  default     = 3
}

variable "vpc_name" {
  description = "Migration VPC name."
  type        = string
}

variable "subnet_name" {
  description = "Migration subnet name."
  type        = string
}

variable "oracle_password_secret" {
  description = "Secret Manager secret containing Oracle password."
  type        = string
}

variable "oracle_port_secret" {
  description = "Secret Manager secret containing Oracle port."
  type        = string
}

variable "oracle_service_secret" {
  description = "Secret Manager secret containing Oracle service name."
  type        = string
}

variable "oracle_username_secret" {
  description = "Secret Manager secret containing Oracle username."
  type        = string
}
