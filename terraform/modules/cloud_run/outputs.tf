output "job_name" {
  description = "Cloud Run migration job name."
  value       = google_cloud_run_v2_job.oracle_migration.name
}

output "job_id" {
  description = "Cloud Run migration job ID."
  value       = google_cloud_run_v2_job.oracle_migration.id
}

output "job_uid" {
  description = "Cloud Run migration job UID."
  value       = google_cloud_run_v2_job.oracle_migration.uid
}