terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "terraform_state" {
  name                        = var.state_bucket_name
  location                    = "ASIA-SOUTH1"
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  public_access_prevention = "enforced"

  labels = {
    project     = "oracle-bq-migration"
    environment = var.environment
    managed_by  = "terraform"
    purpose     = "terraform-state"
  }
}