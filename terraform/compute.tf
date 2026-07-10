# =========================================================
# Create Service Account
# =========================================================
resource "google_service_account" "composer_sa" {
  account_id   = "airflow-vm-sa"
  display_name = "Service Account for Airflow VM "
}

# =========================================================
# Create Virtual Machine 
# =========================================================
resource "google_compute_instance" "airflow_vm" {
  name         = "ecommerce-airflow-vm-${var.environment}"
  machine_type = "e2-standard-2" # สเปค 2 vCPU, 8GB RAM (แรงพอสำหรับ LocalExecutor)
  zone         = "us-east1-b"    # หนีโซน C ที่โควต้าเต็มมาอยู่โซน B แทน

  tags = ["airflow-server"] # แปะป้ายให้ รปภ. (Firewall) รู้จัก

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 30
    }
  }

  network_interface {
    network = "default"
    access_config {
      # เปิดไว้ว่างๆ เพื่อรับ Public IP
    }
  }

  # สคริปต์นี้เทียบเท่า user_data ของ AWS
  # ลงเครื่องมือรอไว้ให้ แต่ "ไม่สั่งรัน" เพื่อรอให้กัปตันเข้ามาสั่งการเอง!
  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y ca-certificates curl gnupg git

    # ติดตั้ง Docker และผองเพื่อน
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # สร้าง Alias ให้เราพิมพ์คำสั่ง docker-compose ได้ง่ายๆ
    ln -s /usr/libexec/docker/cli-plugins/docker-compose /usr/bin/docker-compose
  EOF

  # ใช้ Service Account ของโปรเจกต์ เพื่อให้ Airflow คุยกับ BigQuery/GCS ได้
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
}