# ==========================================
# Google Cloud Storage 
# ==========================================
resource "google_storage_bucket" "gcs_bucket" {
  name          = "${var.bucket_name_prefix}-${var.environment}"
  location      = var.gcp_region
  force_destroy = true 
  storage_class = "STANDARD"

  uniform_bucket_level_access = true
}