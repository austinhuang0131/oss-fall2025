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

variable "bot_user_id" {
  description = "Discord bot user ID"
  type        = string
  sensitive   = true
}

variable "trello_token" {
  description = "Trello OAuth token"
  type        = string
  sensitive   = true
}

variable "trello_api_key" {
  description = "Trello API key"
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

  lifecycle {
    ignore_changes = all
  }
}

# Secret Manager secrets for sensitive data
resource "google_secret_manager_secret" "discord_token" {
  secret_id = "discord-token"

  replication {
    auto {}
  }

  lifecycle {
    ignore_changes = all
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

  lifecycle {
    ignore_changes = all
  }
}

resource "google_secret_manager_secret_version" "trello_token" {
  secret      = google_secret_manager_secret.trello_token.id
  secret_data = var.trello_token
}

resource "google_secret_manager_secret" "trello_api_key" {
  secret_id = "trello-api-key"

  replication {
    auto {}
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "google_secret_manager_secret_version" "trello_api_key" {
  secret      = google_secret_manager_secret.trello_api_key.id
  secret_data = var.trello_api_key
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"

  replication {
    auto {}
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  secret      = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

# OpenTelemetry Collector configuration
resource "google_secret_manager_secret" "otel_collector_config" {
  secret_id = "otel-collector-config"

  replication {
    auto {}
  }

  lifecycle {
    ignore_changes = all
  }
}

# https://docs.cloud.google.com/stackdriver/docs/instrumentation/opentelemetry-collector-cloud-run#gotc-provided-config

resource "google_secret_manager_secret_version" "otel_collector_config" {
  secret = google_secret_manager_secret.otel_collector_config.id
  secret_data = <<-EOT
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: localhost:4317
      http:
        cors:
          allowed_origins:
          - http://*
          - https://*
        endpoint: localhost:4318

processors:
  batch:
    send_batch_max_size: 200
    send_batch_size: 200
    timeout: 5s

  memory_limiter:
    check_interval: 1s
    limit_percentage: 65
    spike_limit_percentage: 20

  resourcedetection:
    detectors: [gcp]
    timeout: 10s

  transform/collision:
    metric_statements:
    - context: datapoint
      statements:
      - set(attributes["exported_location"], attributes["location"])
      - delete_key(attributes, "location")
      - set(attributes["exported_cluster"], attributes["cluster"])
      - delete_key(attributes, "cluster")
      - set(attributes["exported_namespace"], attributes["namespace"])
      - delete_key(attributes, "namespace")
      - set(attributes["exported_job"], attributes["job"])
      - delete_key(attributes, "job")
      - set(attributes["exported_instance"], attributes["instance"])
      - delete_key(attributes, "instance")
      - set(attributes["exported_project_id"], attributes["project_id"])
      - delete_key(attributes, "project_id")

exporters:
  googlecloud:
    log:
      default_log_name: opentelemetry-collector

  googlemanagedprometheus:

extensions:
  health_check:
    endpoint: 0.0.0.0:13133

service:
  extensions:
  - health_check
  pipelines:
    logs:
      receivers:
      - otlp
      processors:
      - resourcedetection
      - memory_limiter
      - batch
      exporters:
      - googlecloud
    metrics/otlp:
      receivers:
      - otlp
      processors:
      - resourcedetection
      - transform/collision
      - memory_limiter
      - batch
      exporters:
      - googlemanagedprometheus
    traces:
      receivers:
      - otlp
      processors:
      - resourcedetection
      - memory_limiter
      - batch
      exporters:
      - googlecloud
  telemetry:
    metrics:
      readers:
        - periodic:
            exporter:
              otlp:
                protocol: grpc
                endpoint: localhost:4317
                insecure: true
EOT
}

# Service account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  account_id   = "ai-ticket-api-service"
  display_name = "AI Ticket API Service Account"
  description  = "Service account for AI Ticket API Cloud Run service"

  lifecycle {
    ignore_changes = all
  }
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

resource "google_secret_manager_secret_iam_member" "trello_api_key_access" {
  secret_id = google_secret_manager_secret.trello_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "openai_api_key_access" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "otel_collector_config_access" {
  secret_id = google_secret_manager_secret.otel_collector_config.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Grant Cloud Trace and Monitoring permissions to service account
resource "google_project_iam_member" "cloud_trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "monitoring_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Cloud Run service
resource "google_cloud_run_v2_service" "ai_ticket_api" {
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.cloud_run_sa.email

    containers {
      image = var.image
      name  = "ai-ticket-api"

      ports {
        container_port = 8080
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = "http://localhost:4317"
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
        name  = "BOT_USER_ID"
        value = var.bot_user_id
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
        name = "TRELLO_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.trello_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "TRELLO_API_SECRET"
        value = "skibidi"
      }

      env {
        name  = "REDIRECT_URI"
        value = "skibidi"
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

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        timeout_seconds   = 30
        period_seconds    = 30
        failure_threshold = 20
      }
    }

    # OpenTelemetry Collector sidecar for Google Cloud Operations
    containers {
      name  = "otel-collector"
      image = "us-docker.pkg.dev/cloud-ops-agents-artifacts/google-cloud-opentelemetry-collector/otelcol-google:0.141.0"

      startup_probe {
        http_get {
          path = "/"
          port = 13133
        }
        timeout_seconds   = 30
        period_seconds    = 30
      }

      liveness_probe {
        http_get {
          path = "/"
          port = 13133
        }
        timeout_seconds   = 30
        period_seconds    = 30
      }

      args = ["--config=/etc/otel-collector-config.yaml"]

      # Mount configuration from volume
      volume_mounts {
        name       = "otel-collector-config"
        mount_path = "/etc/otel-collector-config.yaml"
        read_only  = true
      }

      resources {
        limits = {
          cpu    = "0.5"
          memory = "256Mi"
        }
      }
    }

    # Volume for OpenTelemetry Collector configuration
    volumes {
      name = "otel-collector-config"
      secret {
        secret  = google_secret_manager_secret.otel_collector_config.secret_id
        items {
          version = "latest"
          path    = "otel-collector-config.yaml"
        }
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 1
    }
  }

  depends_on = [
    google_project_service.cloud_run,
    google_secret_manager_secret_version.discord_token,
    google_secret_manager_secret_version.trello_token,
    google_secret_manager_secret_version.trello_api_key,
    google_secret_manager_secret_version.openai_api_key,
    google_secret_manager_secret_version.otel_collector_config,
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
