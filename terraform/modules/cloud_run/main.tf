resource "google_cloud_run_v2_job" "oracle_migration" {
  name     = var.job_name
  project  = var.project_id
  location = var.region

  template {
    task_count = 1

    template {
      service_account = var.service_account_email

      timeout = var.timeout

      max_retries = var.max_retries

      containers {
        image = var.image

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "GCS_BUCKET"
          value = var.gcs_bucket_name
        }

        env {
          name  = "GCS_BUCKET_NAME"
          value = var.gcs_bucket_name
        }

        env {
          name  = "BQ_LOCATION"
          value = var.bigquery_location
        }
       
        env {
          name = "ORACLE_PASSWORD"

          value_source {
            secret_key_ref {
              secret  = var.oracle_password_secret
              version = "latest"
            }
          }
        }

        env {
          name = "ORACLE_PORT"

          value_source {
            secret_key_ref {
              secret  = var.oracle_port_secret
              version = "latest"
            }
          }
        }

        env {
          name = "ORACLE_SERVICE_NAME"

          value_source {
            secret_key_ref {
              secret  = var.oracle_service_secret
              version = "latest"
            }
          }
        }

        env {
          name = "ORACLE_USERNAME"

          value_source {
            secret_key_ref {
              secret  = var.oracle_username_secret
              version = "latest"
            }
          }
        }
      }

      vpc_access {
        network_interfaces {
          network    = var.vpc_name
          subnetwork = var.subnet_name
        }
      }
    }
  }
}
