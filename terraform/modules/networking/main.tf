resource "google_compute_network" "oracle_migration_vpc" {
  name                    = var.network_name
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "oracle_migration_subnet" {
  name          = var.subnet_name
  project       = var.project_id
  region        = var.region
  network       = google_compute_network.oracle_migration_vpc.id
  ip_cidr_range = var.subnet_cidr

  private_ip_google_access = true
}