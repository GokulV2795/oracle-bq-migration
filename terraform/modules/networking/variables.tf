variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "network_name" {
  description = "Migration VPC name"
  type        = string
  default     = "oracle-migration-vpc"
}

variable "subnet_name" {
  description = "Migration subnet name"
  type        = string
  default     = "oracle-migration-subnet"
}

variable "subnet_cidr" {
  description = "Migration subnet CIDR"
  type        = string
  default     = "10.20.0.0/24"
}