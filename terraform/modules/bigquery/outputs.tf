output "raw_dataset_id" {
  value = google_bigquery_dataset.raw.dataset_id
}

output "staging_dataset_id" {
  value = google_bigquery_dataset.staging.dataset_id
}

output "core_dataset_id" {
  value = google_bigquery_dataset.core.dataset_id
}

output "mart_dataset_id" {
  value = google_bigquery_dataset.mart.dataset_id
}