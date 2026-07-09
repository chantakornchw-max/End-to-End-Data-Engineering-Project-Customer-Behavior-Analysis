# ==========================================
# BigQuery Dataset 
# ==========================================
resource "google_bigquery_dataset" "gold_dataset" {
  dataset_id                  = "ecommerce_wh_${var.environment}"
  location                    = var.gcp_region 
  delete_contents_on_destroy  = true
}
