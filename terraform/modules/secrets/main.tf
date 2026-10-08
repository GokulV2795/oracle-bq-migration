resource "google_secret_manager_secret" "oracle_username" {
  project   = var.project_id
  secret_id = "oracle-db-username"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "oracle_password" {
  project   = var.project_id
  secret_id = "oracle-db-password"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "oracle_port" {
  project   = var.project_id
  secret_id = "oracle-db-port"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "oracle_service" {
  project   = var.project_id
  secret_id = "oracle-db-service"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret_iam_member" "oracle_username_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.oracle_username.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.runtime_service_account}"
}

resource "google_secret_manager_secret_iam_member" "oracle_password_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.oracle_password.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.runtime_service_account}"
}

resource "google_secret_manager_secret_iam_member" "oracle_port_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.oracle_port.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.runtime_service_account}"
}

resource "google_secret_manager_secret_iam_member" "oracle_service_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.oracle_service.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.runtime_service_account}"
}