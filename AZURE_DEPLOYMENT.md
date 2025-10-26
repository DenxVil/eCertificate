# Azure Deployment Setup Guide

This guide explains how to set up continuous deployment for the Denx Certificate Generator application to Microsoft Azure using GitHub Actions.

## Prerequisites

Before you begin, ensure you have:
- An Azure account with an active subscription
- An Azure Container Registry (ACR)
- An Azure App Service (Web App for Containers)
- GitHub repository access to configure secrets

## Architecture Overview

The deployment workflow consists of:
1. **Docker Image Build**: The application is containerized using Docker
2. **Azure Container Registry**: Docker images are stored in ACR
3. **Azure App Service**: The containerized application runs on Azure App Service

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository settings:

### 1. AZURE_CREDENTIALS
Azure service principal credentials for authentication.

To create these credentials:
```bash
az ad sp create-for-rbac --name "ecertificate-deploy" --role contributor \
    --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
    --sdk-auth
```

This will output JSON credentials. Copy the entire JSON output and save it as the `AZURE_CREDENTIALS` secret.

### 2. ACR_LOGIN_SERVER
The login server URL for your Azure Container Registry.

Example: `myregistry.azurecr.io`

To find this:
```bash
az acr show --name <your-acr-name> --query loginServer --output tsv
```

### 3. ACR_USERNAME
The username for your Azure Container Registry.

This is typically the name of your ACR. To get it:
```bash
az acr credential show --name <your-acr-name> --query username --output tsv
```

### 4. ACR_PASSWORD
The password for your Azure Container Registry.

To get the password:
```bash
az acr credential show --name <your-acr-name> --query passwords[0].value --output tsv
```

**Security Note**: Enable admin user on your ACR if not already enabled:
```bash
az acr update --name <your-acr-name> --admin-enabled true
```

### 5. AZURE_WEBAPP_NAME
The name of your Azure App Service web app.

Example: `ecertificate-app`

## Setting Up Azure Resources

If you haven't created the Azure resources yet, follow these steps:

### 1. Create a Resource Group
```bash
az group create --name ecertificate-rg --location eastus
```

### 2. Create Azure Container Registry
```bash
az acr create --resource-group ecertificate-rg \
    --name <your-unique-acr-name> \
    --sku Basic \
    --admin-enabled true
```

### 3. Create App Service Plan
```bash
az appservice plan create --name ecertificate-plan \
    --resource-group ecertificate-rg \
    --is-linux \
    --sku B1
```

### 4. Create Web App
```bash
az webapp create --resource-group ecertificate-rg \
    --plan ecertificate-plan \
    --name <your-webapp-name> \
    --deployment-container-image-name <your-acr-name>.azurecr.io/ecertificate:latest
```

### 5. Configure Web App to use ACR
```bash
az webapp config container set --name <your-webapp-name> \
    --resource-group ecertificate-rg \
    --docker-custom-image-name <your-acr-name>.azurecr.io/ecertificate:latest \
    --docker-registry-server-url https://<your-acr-name>.azurecr.io \
    --docker-registry-server-user <acr-username> \
    --docker-registry-server-password <acr-password>
```

### 6. Configure Environment Variables
Set the required environment variables for your Flask application:

```bash
az webapp config appsettings set --name <your-webapp-name> \
    --resource-group ecertificate-rg \
    --settings \
    SECRET_KEY="your-production-secret-key" \
    FLASK_ENV="production" \
    MAIL_SERVER="smtp.gmail.com" \
    MAIL_PORT="587" \
    MAIL_USE_TLS="True" \
    MAIL_USERNAME="your-email@gmail.com" \
    MAIL_PASSWORD="your-app-password" \
    MAIL_DEFAULT_SENDER="your-email@gmail.com" \
    DATABASE_URL="sqlite:///certificates.db" \
    WEBSITES_PORT="5000"
```

**Important**: Replace the placeholder values with your actual configuration.

## Configuring GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** > **Secrets and variables** > **Actions**
3. Click **New repository secret**
4. Add each of the following secrets:
   - `AZURE_CREDENTIALS`
   - `ACR_LOGIN_SERVER`
   - `ACR_USERNAME`
   - `ACR_PASSWORD`
   - `AZURE_WEBAPP_NAME`

## How the Workflow Works

The GitHub Actions workflow (`.github/workflows/azure-deploy.yml`) automatically:

1. **Triggers** on every push to the `main` branch
2. **Checks out** the code from the repository
3. **Logs in** to Azure using the service principal credentials
4. **Logs in** to Azure Container Registry
5. **Builds** the Docker image using the Dockerfile
6. **Tags** the image with both the commit SHA and `latest`
7. **Pushes** both tags to Azure Container Registry
8. **Deploys** the image to Azure App Service
9. **Logs out** from Azure

## Testing the Deployment

After setting up all secrets and pushing to the `main` branch:

1. Go to the **Actions** tab in your GitHub repository
2. You should see the "Deploy to Azure" workflow running
3. Wait for the workflow to complete (typically 2-5 minutes)
4. Once complete, visit your Azure App Service URL to see the deployed application

## Troubleshooting

### Workflow fails during Azure login
- Verify the `AZURE_CREDENTIALS` secret is correctly formatted JSON
- Ensure the service principal has appropriate permissions

### Docker push fails
- Check that `ACR_USERNAME` and `ACR_PASSWORD` are correct
- Verify admin access is enabled on your ACR

### Deployment succeeds but app doesn't work
- Check Azure App Service logs: `az webapp log tail --name <webapp-name> --resource-group <resource-group>`
- Verify environment variables are set correctly in App Service
- Ensure `WEBSITES_PORT` is set to `5000`

### Application errors
- Check that all required environment variables are configured
- Verify the database is accessible
- Check mail server credentials if using email functionality

## Security Best Practices

1. **Rotate credentials regularly**: Update ACR passwords and service principal credentials periodically
2. **Use Key Vault**: For production, consider storing secrets in Azure Key Vault
3. **Limit permissions**: Ensure the service principal has minimal required permissions
4. **Monitor access**: Enable audit logging on your Azure resources
5. **Use managed identities**: Consider using Azure Managed Identities instead of service principals

## Monitoring and Maintenance

- Monitor your App Service through the Azure Portal
- Set up Application Insights for detailed telemetry
- Configure auto-scaling based on your needs
- Regularly update dependencies in `requirements.txt`
- Keep the base Docker image up to date

## Cost Optimization

- Use the Basic (B1) App Service Plan for development/testing
- Scale up to Standard (S1) or Premium (P1v2) for production
- Consider using Azure Container Instances for lower-traffic applications
- Use Azure Cost Management to monitor spending

## Additional Resources

- [Azure Container Registry Documentation](https://learn.microsoft.com/azure/container-registry/)
- [Azure App Service Documentation](https://learn.microsoft.com/azure/app-service/)
- [GitHub Actions for Azure](https://github.com/Azure/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
