# ==========================================
# GCP Provider Variables
# ==========================================
variable "gcp_project_id" {
  description = "The ID of the Google Cloud Project"
  type        = string
  default     = "modern-webbing-493413-r8"
}

variable "gcp_region" {
  description = "The region where GCP resources will be created"
  type        = string
  default     = "asia-southeast1" 
}

variable "gcp_zone" {
  description = "The zone within the region"
  type        = string
  default     = "asia-southeast1-c"
}

# ==========================================
# DB Variables
# ==========================================
variable "db_username" {
  type        = string
  description = "DB Username"
  default     = "postgres"
}

variable "db_password" {
  type        = string
  description = "DB Password"
  sensitive   = true 
}

# ==========================================
# Project Specific Variables 
# ==========================================
variable "bucket_name_prefix" {
  description = "Prefix for GCS bucket names to ensure global uniqueness"
  type        = string
  default     = "ecommerce-customer-behavior-2026"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
  default     = "prod"
}