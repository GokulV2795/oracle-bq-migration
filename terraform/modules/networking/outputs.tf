output "network_name" {
  description = "Migration VPC name"
  value       = google_compute_network.oracle_migration_vpc.name
}

output "network_id" {
  description = "Migration VPC ID"
  value       = google_compute_network.oracle_migration_vpc.id
}

output "subnet_name" {
  description = "Migration subnet name"
  value       = google_compute_subnetwork.oracle_migration_subnet.name
}

output "subnet_id" {
  description = "Migration subnet ID"
  value       = google_compute_subnetwork.oracle_migration_subnet.id
}

output "subnet_cidr" {
  description = "Migration subnet CIDR"
  value       = google_compute_subnetwork.oracle_migration_subnet.ip_cidr_range
}