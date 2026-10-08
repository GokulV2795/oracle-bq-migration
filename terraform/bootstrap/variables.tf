variable "project_id" {
  description = "GCP project ID where the migration infrastructure will be created."
  type        = string
}

variable "region" {
  description = "Default GCP region."
  type        = string
}

variable "state_bucket_name" {
  description = "Globally unique GCS bucket name used for Terraform state."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}