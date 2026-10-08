variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "Secret Manager replica region."
  type        = string
}

variable "runtime_service_account" {
  description = "Service account used by the Oracle migration Cloud Run Job."
  type        = string
}