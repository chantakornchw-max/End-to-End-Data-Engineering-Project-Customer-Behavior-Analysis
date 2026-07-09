# ==========================================
# Creat Service Account for Composer
# ==========================================
resource "google_service_account" "composer_sa" {
  account_id   = "composer-worker-sa"
  display_name = "Service Account for Cloud Composer"
}

resource "google_project_iam_member" "composer_worker" {
  project = var.gcp_project_id
  role    = "roles/composer.worker"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

# ==========================================
# Cloud Composer 2 (Managed Airflow)
# ==========================================
resource "google_composer_environment" "ecommerce_airflow" {
  name   = "ecommerce-airflow-${var.environment}"
  region = var.gcp_region

  config {
    environment_size = "ENVIRONMENT_SIZE_SMALL"

    node_config {
      service_account = google_service_account.composer_sa.email
    }

    software_config {
      image_version = "composer-2-airflow-2"
    }
  }

  depends_on = [
    google_project_iam_member.composer_worker
  ]

}

# ==========================================
# Output 
# ==========================================
output "airflow_dag_gcs_prefix" {
  description = "The GCS bucket path for deploying DAGs via GitHub Actions"
  value       = google_composer_environment.ecommerce_airflow.config[0].dag_gcs_prefix
}