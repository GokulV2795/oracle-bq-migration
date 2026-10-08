output "oracle_username_secret_id" {
  value = google_secret_manager_secret.oracle_username.secret_id
}

output "oracle_password_secret_id" {
  value = google_secret_manager_secret.oracle_password.secret_id
}

output "oracle_port_secret_id" {
  value = google_secret_manager_secret.oracle_port.secret_id
}

output "oracle_service_secret_id" {
  value = google_secret_manager_secret.oracle_service.secret_id
}