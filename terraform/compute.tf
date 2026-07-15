# =========================================================
# Create Service Account
# =========================================================
resource "google_service_account" "composer_sa" {
  account_id   = "airflow-vm-sa"
  display_name = "Service Account for Airflow VM "
}

resource "google_project_iam_member" "airflow_vm_sa_editor" {
  project = "modern-webbing-493413-r8" 
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

# =========================================================
# Create Virtual Machine 
# =========================================================
resource "google_compute_instance" "airflow_vm" {
  name         = "ecommerce-airflow-vm-${var.environment}"
  machine_type = "e2-standard-2" 
  zone         = "us-east1-b"    

  tags = ["airflow-server"] 

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 30
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg git

    # 1. Install Docker and Docker Compose
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    ln -s /usr/libexec/docker/cli-plugins/docker-compose /usr/bin/docker-compose

    # 2. Prepare a working folder
    USER_HOME="/home/chantakorn_chw"
    mkdir -p $USER_HOME/airflow/dags $USER_HOME/airflow/logs $USER_HOME/airflow/plugins
    
    # 3. Pull docker-compose.yaml from GCS and push to VM
    gcloud storage cp gs://ecommerce-customer-behavior-2026-prod/config/docker-compose.yml $USER_HOME/airflow/docker-compose.yml

    # 4. Change folder ownership to Airflow (UID 50000) to prevent permission denied.
    chown -R 50000:0 $USER_HOME/airflow/dags $USER_HOME/airflow/logs $USER_HOME/airflow/plugins
    chown chantakorn_chw:chantakorn_chw $USER_HOME/airflow/docker-compose.yml

    # 5. Start Airflow 
    cd $USER_HOME/airflow
    sudo docker-compose up -d
  EOF

  service_account {
    email  = google_service_account.composer_sa.email
    scopes = ["cloud-platform"]
  }
}

# =========================================================
# Create Firewall
# =========================================================
resource "google_compute_firewall" "allow_airflow_web" {
  name    = "allow-airflow-web-port"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["airflow-server"]
}

# =========================================================
# Public IP address
# =========================================================
output "airflow_vm_public_ip" {
  value       = google_compute_instance.airflow_vm.network_interface[0].access_config[0].nat_ip
  description = "The public IP address of the Airflow VM"
  sensitive   = true
}