terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "~> 2.0" # Specify a version constraint
    }
  }
}

provider "digitalocean" {
}

variable "ssh_key_ids" {
  type        = list(string)
  description = "List of SSH key IDs to access the droplets"
}

variable "region" {
  default     = "nyc3"
  description = "DigitalOcean region"
}

variable "image" {
  default     = "ubuntu-24-04-x64"
}

variable "droplet_size" {
  default     = "s-1vcpu-1gb"
}

# --- Project: Brand-Community-Analysis ---
resource "digitalocean_project" "main" {
  name        = "brand-community-analysis"
  purpose     = "Web Application"
  environment = "Development"
  description = "Infrastructure for ML, Web, and Model services and storage"
}


# --- Droplet: Middleware ---
resource "digitalocean_droplet" "middleware" {
  name     = "middleware-server"
  region   = var.region
  size     = var.droplet_size
  image    = var.image
  ssh_keys = var.ssh_key_ids
}

# --- Droplet: Web Server ---
resource "digitalocean_droplet" "web_server" {
  name     = "web-server"
  region   = var.region
  size     = var.droplet_size
  image    = var.image
  ssh_keys = var.ssh_key_ids
}

# --- Droplet: Model Server ---
resource "digitalocean_droplet" "model_server" {
  name     = "model-server"
  region   = var.region
  size     = var.droplet_size
  image    = var.image
  ssh_keys = var.ssh_key_ids
}

# --- Space for Artifact Storage ---
resource "digitalocean_spaces_access_key" "middleware_key" {
  name = "middleware-access-key"
}

resource "digitalocean_spaces_bucket" "middleware_space" {
  name   = "middleware-artifacts"
  region = var.region
}

resource "digitalocean_project_resources" "assign" {
  project = digitalocean_project.main.id
  resources = [
    digitalocean_droplet.middleware.urn,
    digitalocean_droplet.web_server.urn,
    digitalocean_droplet.model_server.urn,
    digitalocean_spaces_bucket.middleware_space.urn
  ]
}


# --- Output Ansible Inventory File ---
resource "local_file" "ansible_inventory" {
  filename = "${path.module}/inventory.ini"
  content = <<EOF
[middleware]
${digitalocean_droplet.middleware.ipv4_address} ansible_user=root

[web]
${digitalocean_droplet.web_server.ipv4_address} ansible_user=root

[model]
${digitalocean_droplet.model_server.ipv4_address} ansible_user=root

# DigitalOcean Space Info
# Name: ${digitalocean_spaces_bucket.middleware_space.name}
# Region: ${digitalocean_spaces_bucket.middleware_space.region}
EOF
}

resource "local_file" "middleware_group_vars" {
  filename = "${path.module}/group_vars/middleware.yml"
  content = <<-EOT
    mlflow_version: "2.12.1"
    mlflow_port: 5000
    artifact_bucket: "${digitalocean_spaces_bucket.middleware_space.name}"
    s3_region: "${var.region}"
    s3_endpoint: "https://${var.region}.digitaloceanspaces.com"

    do_spaces_access_key_id: "${digitalocean_spaces_access_key.mlflow.key}"
    do_spaces_secret_access_key: "${digitalocean_spaces_access_key.mlflow.secret}"
  EOT
}


# --- Outputs ---
output "middleware_ip" {
  value = digitalocean_droplet.middleware.ipv4_address
}

output "web_server_ip" {
  value = digitalocean_droplet.web_server.ipv4_address
}

output "model_server_ip" {
  value = digitalocean_droplet.model_server.ipv4_address
}

output "space_name" {
  value = digitalocean_spaces_bucket.mlflow_space.name
}

output "space_access_key" {
  value     = digitalocean_spaces_access_key.middleware_key.access_key
  sensitive = true
}

output "space_secret_key" {
  value     = digitalocean_spaces_access_key.middleware_key.secret_key
  sensitive = true
}
