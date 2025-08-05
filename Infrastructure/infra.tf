terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    local = {
      source = "hashicorp/local"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

variable "do_token" {
  type        = string
  sensitive   = true
  description = "DigitalOcean API token"
}

variable "region" {
  default = "nyc3"
}

variable "image" {
  default = "ubuntu-24-04-x64"
}

variable "droplet_size" {
  default = "s-1vcpu-1gb"
}

variable "spaces_access_key" {
  type        = string
  sensitive   = true
  description = "Manually created DigitalOcean Spaces Access Key"
}

variable "spaces_secret_key" {
  type        = string
  sensitive   = true
  description = "Manually created DigitalOcean Spaces Secret Key"
}

variable "spaces_bucket_name" {
  type        = string
  description = "Manually created DigitalOcean Spaces bucket name"
}

variable "ssh_key_name" {
  type        = string
  description = "Name of the SSH key uploaded to DigitalOcean"
}

# --------------------------
# Look up SSH key ID by name
# --------------------------
data "digitalocean_ssh_key" "default" {
  name = var.ssh_key_name
}

# --------------------------
# Project
# --------------------------
resource "digitalocean_project" "main" {
  name        = "brand-community-analysis"
  purpose     = "Web Application"
  environment = "Development"
  description = "Infrastructure for MLflow, web, and model servers"
}

# --------------------------
# Droplets
# --------------------------
resource "digitalocean_droplet" "middleware" {
  name     = "middleware-server"
  region   = var.region
  size     = var.droplet_size
  image    = var.image
  ssh_keys = [data.digitalocean_ssh_key.default.id]
}

resource "digitalocean_droplet" "web_server" {
  name     = "web-server"
  region   = var.region
  size     = var.droplet_size
  image    = var.image
  ssh_keys = [data.digitalocean_ssh_key.default.id]
}

resource "digitalocean_droplet" "model_server" {
  name     = "model-server"
  region   = var.region
  size     = var.droplet_size
  image    = var.image
  ssh_keys = [data.digitalocean_ssh_key.default.id]
}

# --------------------------
# Assign droplets to the project
# --------------------------
resource "digitalocean_project_resources" "assign" {
  project = digitalocean_project.main.id
  resources = [
    digitalocean_droplet.middleware.urn,
    digitalocean_droplet.web_server.urn,
    digitalocean_droplet.model_server.urn
  ]
}

# --------------------------
# Generate inventory.ini
# --------------------------
resource "local_file" "ansible_inventory" {
  filename = "${path.module}/inventory.ini"
  content = <<EOF
[middleware]
${digitalocean_droplet.middleware.ipv4_address} ansible_user=root

[flask_server]
${digitalocean_droplet.web_server.ipv4_address} ansible_user=root

[model]
${digitalocean_droplet.model_server.ipv4_address} ansible_user=root
EOF
}

# --------------------------
# Generate group_vars/middleware.yml (with placeholders for Spaces info)
# --------------------------
resource "local_file" "middleware_group_vars" {
  filename = "${path.module}/group_vars/middleware.yml"
  content = <<EOF
mlflow_version: "2.12.1"
mlflow_port: 5000
artifact_bucket: "${var.spaces_bucket_name}"
s3_region: "${var.region}"
s3_endpoint: "https://${var.region}.digitaloceanspaces.com"

do_spaces_access_key_id: "${var.spaces_access_key}"
do_spaces_secret_access_key: "${var.spaces_secret_key}"
EOF
}

# --------------------------
# Outputs
# --------------------------
output "middleware_ip" {
  value = digitalocean_droplet.middleware.ipv4_address
}

output "web_server_ip" {
  value = digitalocean_droplet.web_server.ipv4_address
}

output "model_server_ip" {
  value = digitalocean_droplet.model_server.ipv4_address
}
