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

# =========================================================
# Grant Service Agent V2 Ext role to Google's internal bot
# =========================================================
resource "google_project_iam_member" "composer_service_agent_v2ext" {
  project = var.gcp_project_id
  role    = "roles/composer.ServiceAgentV2Ext"
  member  = "serviceAccount:service-100590769502@cloudcomposer-accounts.iam.gserviceaccount.com"
}

# ==========================================
# Cloud Composer 2 (Managed Airflow)
# ==========================================
resource "google_composer_environment" "ecommerce_airflow" {
  name   = "ecommerce-airflow-${var.environment}"
  region = "us-east1"

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
    google_project_iam_member.composer_worker,
    google_project_iam_member.composer_service_agent_v2ext
  ]

}

# ==========================================
# Output 
# ==========================================
output "airflow_dag_gcs_prefix" {
  description = "The GCS bucket path for deploying DAGs via GitHub Actions"
  value       = google_composer_environment.ecommerce_airflow.config[0].dag_gcs_prefix
}