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

variable "ssh_key_ids" {
  type        = list(string)
  description = "List of SSH key IDs from DigitalOcean"
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
  ssh_keys = var.ssh_key_ids
}

resource "digitalocean_droplet" "web_server" {
  name     = "web-server"
  region   = var.region
  size     = var.droplet_size
  image    = var.image
  ssh_keys = var.ssh_key_ids
}

resource "digitalocean_droplet" "model_server" {
  name     = "model-server"
  region   = var.region
  size     = var.droplet_size
  image    = var.image
  ssh_keys = var.ssh_key_ids
}

# --------------------------
# Spaces Bucket
# --------------------------
resource "digitalocean_spaces_bucket" "middleware_space" {
  name   = "middleware-artifacts"
  region = var.region
}

# --------------------------
# Create Spaces Access Key using doctl
# --------------------------
resource "null_resource" "spaces_access_key" {
  provisioner "local-exec" {
    command = <<EOT
      mkdir -p ${path.module}/tmp
      doctl compute cdn create --format ID --no-header > /dev/null # Just to ensure Spaces API is ready
      doctl compute cdn create --no-header # This is just a placeholder to ensure connectivity
      doctl compute cdn delete # cleanup placeholder
      
      # Actually create Spaces key
      doctl compute cdn create # This command is placeholder for actual spaces key creation
    EOT
  }
}

# NOTE: doctl does not have a direct "spaces access-key create" command, so we'd use the API
# This step would realistically call `doctl` with `--output json` and jq to parse keys

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

# DigitalOcean Space Info
# Name: ${digitalocean_spaces_bucket.middleware_space.name}
# Region: ${digitalocean_spaces_bucket.middleware_space.region}
EOF
}

# --------------------------
# Generate group_vars/middleware.yml
# --------------------------
resource "local_file" "middleware_group_vars" {
  filename = "${path.module}/group_vars/middleware.yml"
  content = <<EOF
mlflow_version: "2.12.1"
mlflow_port: 5000
artifact_bucket: "${digitalocean_spaces_bucket.middleware_space.name}"
s3_region: "${var.region}"
s3_endpoint: "https://${var.region}.digitaloceanspaces.com"

do_spaces_access_key_id: "PLACEHOLDER_KEY"
do_spaces_secret_access_key: "PLACEHOLDER_SECRET"
EOF
}

# --------------------------
# Assign all resources to the project
# --------------------------
resource "digitalocean_project_resources" "assign" {
  project = digitalocean_project.main.id
  resources = [
    digitalocean_droplet.middleware.urn,
    digitalocean_droplet.web_server.urn,
    digitalocean_droplet.model_server.urn,
    digitalocean_spaces_bucket.middleware_space.urn
  ]
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
