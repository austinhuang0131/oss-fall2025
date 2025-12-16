# Terraform configuration for deploying AI Ticket API Service to GCP Cloud Run

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run service"
  type        = string
  default     = "ai-ticket-api-service"
}

variable "image" {
  description = "Container image to deploy"
  type        = string
}

variable "discord_token" {
  description = "Discord bot token"
  type        = string
  sensitive   = true
}

variable "discord_channel_id" {
  description = "Discord channel ID"
  type        = string
  sensitive   = true
}

variable "trello_token" {
  description = "Trello OAuth token"
  type        = string
  sensitive   = true
}

variable "trello_board_id" {
  description = "Trello board ID"
  type        = string
  default     = ""
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "poll_interval" {
  description = "Message polling interval in seconds"
  type        = string
  default     = "1.0"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

# Enable required APIs
resource "google_project_service" "cloud_run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "artifact_registry" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "ai-ticket-api"
  description   = "Docker repository for AI Ticket API Service"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

# Secret Manager secrets for sensitive data
resource "google_secret_manager_secret" "discord_token" {
  secret_id = "discord-token"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "discord_token" {
  secret      = google_secret_manager_secret.discord_token.id
  secret_data = var.discord_token
}

resource "google_secret_manager_secret" "trello_token" {
  secret_id = "trello-token"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "trello_token" {
  secret      = google_secret_manager_secret.trello_token.id
  secret_data = var.trello_token
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

# Service account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "ai-ticket-api-service"
  display_name = "AI Ticket API Service Account"
  description  = "Service account for AI Ticket API Cloud Run service"
}

# Grant Secret Manager access to service account
resource "google_secret_manager_secret_iam_member" "discord_token_access" {
  secret_id = google_secret_manager_secret.discord_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "trello_token_access" {
  secret_id = google_secret_manager_secret.trello_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "openai_api_key_access" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "ai_ticket_api" {
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.cloud_run_sa.email
    
    containers {
      image = var.image
      
      ports {
        container_port = 8080
      }
      
      env {
        name  = "PORT"
        value = "8080"
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      env {
        name = "DISCORD_ACCESS_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.discord_token.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "TEST_DISCORD_CHANNEL_ID"
        value = var.discord_channel_id
      }
      
      env {
        name = "TRELLO_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.trello_token.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "TEST_TRELLO_BOARD_ID"
        value = var.trello_board_id
      }
      
      env {
        name = "TEST_OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }
      
      env {
        name  = "POLL_INTERVAL"
        value = var.poll_interval
      }
      
      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = "http://localhost:4317"
      }
      
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
    
    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }
  }

  depends_on = [
    google_project_service.cloud_run,
    google_secret_manager_secret_version.discord_token,
    google_secret_manager_secret_version.trello_token,
    google_secret_manager_secret_version.openai_api_key,
  ]
}

# Allow unauthenticated access to the service (for health checks)
resource "google_cloud_run_v2_service_iam_member" "noauth" {
  location = google_cloud_run_v2_service.ai_ticket_api.location
  name     = google_cloud_run_v2_service.ai_ticket_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Outputs
output "service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.ai_ticket_api.uri
}

output "service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_v2_service.ai_ticket_api.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository name"
  value       = google_artifact_registry_repository.docker_repo.name
}
