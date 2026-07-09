# ==========================================
# Cloud Composer 2 (Managed Airflow)
# ==========================================
resource "google_composer_environment" "ecommerce_airflow" {
  name   = "ecommerce-airflow-${var.environment}"
  region = var.gcp_region

  config {
    environment_size = "ENVIRONMENT_SIZE_SMALL"

    software_config {
      image_version = "composer-2-airflow-2"
    }
  }
}

# ==========================================
# Output 
# ==========================================
output "airflow_dag_gcs_prefix" {
  description = "The GCS bucket path for deploying DAGs via GitHub Actions"
  value       = google_composer_environment.ecommerce_airflow.config[0].dag_gcs_prefix
}