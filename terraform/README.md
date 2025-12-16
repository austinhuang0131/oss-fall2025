# AI Ticket API Service - Terraform Infrastructure

This directory contains Terraform configuration for deploying the AI Ticket API Service to Google Cloud Platform (GCP).

## Architecture

The infrastructure includes:
- **Cloud Run**: Serverless container deployment
- **Artifact Registry**: Docker image storage
- **Secret Manager**: Secure credential storage
- **Service Account**: Managed identity with least-privilege access

## Prerequisites

1. **GCP Project**: An active GCP project with billing enabled
2. **gcloud CLI**: [Install gcloud](https://cloud.google.com/sdk/docs/install)
3. **Terraform**: [Install Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) (>= 1.0)
4. **Docker**: For building container images
5. **Credentials**: Discord, Trello, and OpenAI API tokens

## Setup

### 1. Authenticate with GCP

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
```

### 2. Configure Variables

Copy the example tfvars file and fill in your values:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values
```

**Required variables:**
- `project_id`: Your GCP project ID
- `discord_token`: Discord bot token
- `discord_channel_id`: Discord channel ID to monitor
- `trello_token`: Trello OAuth token
- `openai_api_key`: OpenAI API key
- `image`: Container image URL (build first, see below)

### 3. Build and Push Container Image

```bash
# Set your project ID
export PROJECT_ID=your-gcp-project-id
export REGION=us-central1

# Initialize Terraform to create Artifact Registry
terraform init
terraform apply -target=google_artifact_registry_repository.docker_repo

# Configure Docker for Artifact Registry
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build the Docker image from project root
cd ..
docker build -f src/ai_ticket_api_service/Dockerfile \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-ticket-api/ai-ticket-api-service:latest .

# Push to Artifact Registry
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-ticket-api/ai-ticket-api-service:latest
```

### 4. Deploy Infrastructure

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

## Deployment

After successful deployment, Terraform outputs the service URL:

```
service_url = "https://ai-ticket-api-service-xxxxx-uc.a.run.app"
```

### Verify Deployment

```bash
# Get the service URL
export SERVICE_URL=$(terraform output -raw service_url)

# Health check
curl ${SERVICE_URL}/health

# View metrics
curl ${SERVICE_URL}/metrics

# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-ticket-api-service" \
  --limit=50 \
  --format=json
```

## Monitoring

### View Logs

```bash
# Real-time logs
gcloud alpha run services logs tail ai-ticket-api-service --region=us-central1

# Recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=100
```

### Metrics

Cloud Run provides built-in metrics:
- Request count
- Request latency
- Container CPU/memory utilization
- Instance count

Access via:
- [Cloud Console](https://console.cloud.google.com/run)
- `gcloud run services describe ai-ticket-api-service`

## Updating the Service

### Update Code

```bash
# Rebuild and push new image
docker build -f src/ai_ticket_api_service/Dockerfile \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-ticket-api/ai-ticket-api-service:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-ticket-api/ai-ticket-api-service:latest

# Cloud Run will automatically deploy the new image
# Or force a new revision:
gcloud run services update ai-ticket-api-service \
  --region=us-central1 \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/ai-ticket-api/ai-ticket-api-service:latest
```

### Update Configuration

Modify `terraform.tfvars` and run:

```bash
terraform apply
```

## Secrets Management

Secrets are stored in Google Secret Manager and automatically injected as environment variables. To rotate secrets:

```bash
# Update secret in terraform.tfvars
# Apply changes
terraform apply

# Cloud Run will automatically use the new secret version
```

## Cost Optimization

- **Min instances**: Set to 1 for production (always available)
- **Max instances**: Set to 5 (adjustable based on load)
- **CPU allocation**: "CPU is always allocated" for background polling
- **Memory**: 512Mi (adjust based on actual usage)

**Estimated cost**: ~$20-40/month for light usage (1 always-on instance)

## Troubleshooting

### Service won't start

```bash
# Check service status
gcloud run services describe ai-ticket-api-service --region=us-central1

# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

### Environment variable issues

```bash
# Verify secrets are accessible
gcloud secrets versions access latest --secret=discord-token
```

### Permission errors

```bash
# Grant necessary roles to service account
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:ai-ticket-api-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Cleanup

To destroy all infrastructure:

```bash
terraform destroy
```

**Warning**: This will delete:
- Cloud Run service
- Secrets (and their values)
- Service account
- Artifact Registry repository (and all images)

## CI/CD Integration

See `.circleci/config.yml` for automated deployment configuration.

## Security Notes

- ✅ Secrets stored in Secret Manager (not in environment directly)
- ✅ Service account with least-privilege access
- ✅ terraform.tfvars excluded from git
- ⚠️ Service is publicly accessible (health/metrics endpoints)
- ⚠️ Consider VPC connector for private resources

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
