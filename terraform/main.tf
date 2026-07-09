# ==========================================
# Required Providers & Backend
# ==========================================
terraform {
  required_version = ">= 1.0"

  backend "gcs" {
    bucket = "ecommerce-terraform-state-2026" 
    prefix = "prod/terraform/state"           
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ==========================================
# Google Cloud Provider Configuration
# ==========================================
provider "google" {
  # credentials = file(var.gcp_credentials_file) 
  project     = var.gcp_project_id
  region      = var.gcp_region
  zone        = var.gcp_zone 
}