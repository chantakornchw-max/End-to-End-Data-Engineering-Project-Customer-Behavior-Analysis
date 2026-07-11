# ==========================================
# 1. Cloud SQL Instance 
# ==========================================
resource "google_sql_database_instance" "postgres_instance" {
  name             = "ecommerce-postgres-instance-${var.environment}"
  database_version = "POSTGRES_15"           
  region           = var.gcp_region
  deletion_protection = false                

  settings {
    tier = "db-f1-micro"                    
    disk_autoresize = true                   
    disk_type       = "PD_SSD" 

    location_preference {
      zone = "asia-southeast1-c" 
    }              

    ip_configuration {
      ipv4_enabled = true                    
      authorized_networks {                  
        name  = "allow-all-for-testing"      
        value = "0.0.0.0/0"
      }
    }
  }
}

# ==========================================
# 2. Database 
# ==========================================
resource "google_sql_database" "ecommerce_db" {
  name     = "ecommerce_db" 
  instance = google_sql_database_instance.postgres_instance.name
}

# ==========================================
# 3. Database User 
# ==========================================
resource "google_sql_user" "db_user" {
  instance = google_sql_database_instance.postgres_instance.name
  name     = var.db_username
  password = var.db_password 
}

# ==========================================
# Output 
# ==========================================
output "cloud_sql_public_ip" {
  description = "The public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres_instance.public_ip_address
}