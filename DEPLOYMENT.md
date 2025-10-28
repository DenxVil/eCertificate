# Deployment Guide for eCertificate

This document provides detailed instructions for deploying the eCertificate application to Azure.

## Prerequisites

- Azure subscription
- Azure CLI installed and configured (`az login`)
- Docker Desktop installed and running (for local builds)
- GitHub repository with the eCertificate code

## Deployment Options

There are three main ways to deploy this project to Azure:

### Option 1: PowerShell Script (Local Interactive)

**Best for:** Quick local deployment with automatic resource provisioning

**Prerequisites:**
- Azure CLI installed & logged in (`az login`)
- Docker Desktop installed and running

**Steps:**
1. Navigate to the repository root
2. Run the deployment script:
   ```powershell
   .\scripts\azure\deploy-azure.ps1
   ```
3. The script will:
   - Provision an Azure Resource Group
   - Create a Cosmos DB with MongoDB API
   - Create an Azure Container Registry (ACR)
   - Build and push the Docker image
   - Create an App Service for Containers
   - Configure app settings
4. Follow the prompts for required secrets (e.g., Telegram Bot Token)
5. The script will output the created resource names and web app URL

### Option 2: GitHub Actions with Secrets (Recommended for Production)

**Best for:** Production CI/CD with flexible resource naming

**Workflow File:** `.github/workflows/azure-deploy.yml`

**Required GitHub Secrets:**
Configure these in your GitHub repository settings (Settings → Secrets and variables → Actions):

1. **AZURE_CREDENTIALS** - Azure service principal JSON
   ```bash
   az ad sp create-for-rbac --name "github-action-sp" \
     --role contributor \
     --scopes /subscriptions/<SUBSCRIPTION_ID> \
     --sdk-auth
   ```
   Copy the entire JSON output and add it as a secret.

2. **ACR_NAME** - Your Azure Container Registry name (e.g., `myecertacr`)

3. **AZURE_RESOURCE_GROUP** - Resource group containing your Web App (e.g., `ecert-rg`)

4. **AZURE_WEBAPP_NAME** - Name of your App Service Web App (e.g., `ecertificate-app`)

**How it works:**
- Triggers automatically on push to `main` branch
- Builds the Docker image
- Pushes image to ACR
- Updates the Web App to use the new image

### Option 3: GitHub Actions with Hardcoded Values (Quick Setup)

**Best for:** Quick deployment when you have existing Azure resources with specific names

**Workflow File:** `.github/workflows/deploy.yml`

**Pre-configured for:**
- ACR Name: `denxcertacr`
- Web App Name: `denx-certificate-app`
- Resource Group: `nexus-ai-rg`

**Required GitHub Secret:**
- **AZURE_CREDENTIALS** only (same as Option 2)

**To customize:**
Edit `.github/workflows/deploy.yml` and update the hardcoded values:
```yaml
env:
  acr_name: denxcertacr  # Change this
# ...
app-name: denx-certificate-app  # Change this
resource-group-name: nexus-ai-rg  # Change this
```

## Azure Resources Required

For all deployment options, you need:

1. **Azure Container Registry (ACR)** - Stores Docker images
2. **App Service Plan** - Hosts the web app
3. **App Service (Web App for Containers)** - Runs the containerized app
4. **Azure Cosmos DB with MongoDB API** - Database for the application

## Environment Variables

The following environment variables must be configured in your Azure Web App:

### Required:
- `MONGO_URI` - MongoDB connection string (from Cosmos DB)
  ```
  mongodb://your-cosmosdb:key@your-cosmosdb.mongo.cosmos.azure.com:10255/ecertificate?ssl=true&replicaSet=globaldb
  ```
- `SECRET_KEY` - Flask secret key (generate a random string)
- `FLASK_ENV` - Set to `production`
- `FLASK_DEBUG` - Set to `False`

### Optional (for email functionality):
- `MAIL_SERVER` - SMTP server (e.g., `smtp.gmail.com`)
- `MAIL_PORT` - SMTP port (e.g., `587`)
- `MAIL_USE_TLS` - Set to `True`
- `MAIL_USERNAME` - Email username
- `MAIL_PASSWORD` - Email password or app password
- `MAIL_DEFAULT_SENDER` - Default sender email

### Optional (for Telegram bot):
- `TELEGRAM_BOT_TOKEN` - Token from BotFather

## Configuring Azure Web App Settings

You can set environment variables in the Azure Portal:

1. Go to your App Service
2. Navigate to **Settings** → **Configuration**
3. Click **New application setting**
4. Add each environment variable
5. Click **Save**

Or use Azure CLI:
```bash
az webapp config appsettings set \
  --name <webapp-name> \
  --resource-group <resource-group> \
  --settings MONGO_URI="<connection-string>" \
              SECRET_KEY="<random-key>" \
              FLASK_ENV="production" \
              FLASK_DEBUG="False"
```

## Troubleshooting

### Build Fails
- Check that all required secrets are configured in GitHub
- Verify Docker builds locally: `docker build -t test .`
- Check GitHub Actions logs for specific errors

### App Won't Start
- Verify `MONGO_URI` is correctly configured
- Check Application Logs in Azure Portal
- Ensure port 8000 is exposed in container settings

### Database Connection Issues
- Verify Cosmos DB connection string
- Check firewall rules in Cosmos DB
- Ensure the Web App has network access to Cosmos DB

### Email Not Working
- Verify SMTP settings
- Use app-specific passwords for Gmail
- Check Web App logs for email errors

## Post-Deployment Steps

1. **Verify the deployment:**
   - Open the Web App URL
   - Check that the application loads

2. **Configure MongoDB:**
   - Ensure Cosmos DB is properly configured
   - Create necessary indexes if needed

3. **Test functionality:**
   - Create a test event
   - Upload a certificate template
   - Generate a test certificate

4. **Monitor the application:**
   - Set up Application Insights (recommended)
   - Monitor logs in Azure Portal
   - Configure alerts for errors

## Security Recommendations

- Enable HTTPS only in App Service
- Use managed identities where possible
- Store secrets in Azure Key Vault
- Enable Azure AD authentication for the web app
- Regularly update dependencies
- Use network security groups to restrict access
- Enable diagnostic logs

## Cost Optimization

- Use Basic or Standard App Service Plan for development
- Scale up to Premium for production
- Consider using Azure Container Instances for lower traffic scenarios
- Use Cosmos DB serverless mode for development
- Set up auto-scaling based on demand

## Support

For issues or questions:
- Check the [main README](README.md)
- Review [GitHub Issues](https://github.com/DenxVil/eCertificate/issues)
- Consult Azure documentation for Azure-specific issues
