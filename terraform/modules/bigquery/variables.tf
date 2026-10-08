variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "location" {
  description = "BigQuery dataset location."
  type        = string
}

variable "raw_dataset" {
  description = "RAW dataset name."
  type        = string
}

variable "staging_dataset" {
  description = "STAGING dataset name."
  type        = string
}

variable "core_dataset" {
  description = "CORE dataset name."
  type        = string
}

variable "mart_dataset" {
  description = "MART dataset name."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "control_dataset" {
  description = "BigQuery control and audit dataset."
  type        = string
}