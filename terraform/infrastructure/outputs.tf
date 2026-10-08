output "migration_bucket_name" {
  description = "GCS bucket used for Oracle migration data."
  value       = module.gcs.bucket_name
}

output "migration_bucket_url" {
  description = "GCS URL of the migration bucket."
  value       = module.gcs.bucket_url
}

output "raw_dataset_id" {
  description = "BigQuery RAW dataset."
  value       = module.bigquery.raw_dataset_id
}

output "staging_dataset_id" {
  description = "BigQuery STAGING dataset."
  value       = module.bigquery.staging_dataset_id
}

output "core_dataset_id" {
  description = "BigQuery CORE dataset."
  value       = module.bigquery.core_dataset_id
}

output "mart_dataset_id" {
  description = "BigQuery MART dataset."
  value       = module.bigquery.mart_dataset_id
}

output "migration_service_account_email" {
  description = "Migration service account email."
  value       = module.iam.service_account_email
}

output "oracle_migration_vpc_name" {
  description = "Oracle migration VPC"
  value       = module.networking.network_name
}

output "oracle_migration_subnet_name" {
  description = "Oracle migration subnet"
  value       = module.networking.subnet_name
}

output "oracle_migration_subnet_cidr" {
  description = "Oracle migration subnet CIDR"
  value       = module.networking.subnet_cidr
}

output "oracle_migration_cloud_run_job" {
  description = "Oracle migration Cloud Run Job."
  value       = module.cloud_run.job_name
}

output "oracle_migration_cloud_run_job_id" {
  description = "Oracle migration Cloud Run Job ID."
  value       = module.cloud_run.job_id
}