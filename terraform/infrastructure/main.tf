terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }

  backend "gcs" {
    bucket = "mbazzar-terraform-state-504603"
    prefix = "infrastructure"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "gcs" {
  source = "../modules/gcs"

  project_id  = var.project_id
  bucket_name = var.migration_bucket_name
  environment = var.environment
  region      = var.region
}

module "bigquery" {
  source = "../modules/bigquery"

  project_id      = var.project_id
  location        = var.bigquery_location
  raw_dataset     = var.raw_dataset
  staging_dataset = var.staging_dataset
  core_dataset    = var.core_dataset
  mart_dataset    = var.mart_dataset
  control_dataset = var.control_dataset
  environment     = var.environment
}

module "iam" {
  source = "../modules/iam"

  project_id                        = var.project_id
  environment                       = var.environment
  migration_bucket_name             = module.gcs.bucket_name
  cloud_run_runtime_service_account = var.cloud_run_service_account
}

module "networking" {
  source = "../modules/networking"

  project_id = var.project_id
  region     = var.region

  network_name = "oracle-migration-vpc"
  subnet_name  = "oracle-migration-subnet"
  subnet_cidr  = "10.20.0.0/24"
}

module "cloud_run" {
  source = "../modules/cloud_run"

  project_id = var.project_id
  region     = var.region

  job_name = var.cloud_run_job_name
  image    = var.cloud_run_image

  service_account_email = var.cloud_run_service_account

  gcs_bucket_name   = module.gcs.bucket_name
  bigquery_location = var.bigquery_location

  vpc_name    = module.networking.network_name
  subnet_name = module.networking.subnet_name

  oracle_password_secret = var.oracle_password_secret
  oracle_port_secret     = var.oracle_port_secret
  oracle_service_secret  = var.oracle_service_secret
  oracle_username_secret = var.oracle_username_secret
}

module "secrets" {
  source = "../modules/secrets"

  project_id              = var.project_id
  region                  = var.region
  runtime_service_account = var.cloud_run_service_account
}