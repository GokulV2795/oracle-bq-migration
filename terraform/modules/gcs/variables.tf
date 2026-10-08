variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "bucket_name" {
  description = "Migration GCS bucket name."
  type        = string
}

variable "region" {
  description = "GCP region."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}