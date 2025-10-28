# PowerShell Script for Deploying the eCertificate App to Azure

# This script automates the following:
# 1. Provisioning an Azure Resource Group.
# 2. Provisioning an Azure Cosmos DB account with the MongoDB API.
# 3. Provisioning an Azure Container Registry (ACR).
# 4. Building the application's Docker image and pushing it to ACR.
# 5. Provisioning an Azure App Service Plan.
# 6. Provisioning an Azure App Service for Containers.
# 7. Configuring the App Service with the correct Docker image and environment variables.

# Prerequisites:
# - Azure CLI installed and authenticated (run `az login`).
# - Docker Desktop installed and running.
# - A valid Telegram Bot Token.

# --- Configuration ---
$ErrorActionPreference = "Stop"

# Prompt for required secrets
$telegramBotToken = Read-Host -Prompt "Enter your Telegram Bot Token"
if ([string]::IsNullOrWhiteSpace($telegramBotToken)) {
    Write-Error "Telegram Bot Token is required."
    exit
}

# Generate a unique suffix for resources to avoid naming conflicts
$uniqueSuffix = (Get-Random -Minimum 1000 -Maximum 9999).ToString()

# Resource names
$resourceGroupName = "eCertificate-rg-$uniqueSuffix"
$location = "EastUS" # You can change this to a region closer to you
$cosmosDbAccountName = "ecert-cosmosdb-$uniqueSuffix"
$containerRegistryName = "ecertacr$uniqueSuffix"
$appServicePlanName = "eCertificate-plan-$uniqueSuffix"
$webAppName = "eCertificate-app-$uniqueSuffix"
$dockerImageName = "ecertificate-app:latest"

# --- Script Body ---

# 1. Login to Azure (uncomment if you are not already logged in)
# Write-Host "Logging into Azure..."
# az login

# Set the subscription context (optional, uncomment and set if you have multiple subscriptions)
# $subscriptionId = "YOUR_SUBSCRIPTION_ID"
# az account set --subscription $subscriptionId
# Write-Host "Using subscription: $subscriptionId"

# 2. Create Resource Group
Write-Host "Creating resource group '$resourceGroupName' in '$location'..."
az group create --name $resourceGroupName --location $location

# 3. Create Cosmos DB with MongoDB API
Write-Host "Creating Cosmos DB account '$cosmosDbAccountName'..."
az cosmosdb create `
    --name $cosmosDbAccountName `
    --resource-group $resourceGroupName `
    --kind MongoDB `
    --server-version "4.2" `
    --locations "regionName=$location" `
    --enable-free-tier $true # Use free tier to minimize costs

Write-Host "Fetching Cosmos DB connection string..."
$connectionStringResult = az cosmosdb keys list `
    --name $cosmosDbAccountName `
    --resource-group $resourceGroupName `
    --type connection-strings `
    | ConvertFrom-Json

$mongoConnectionString = $connectionStringResult.connectionStrings[0].connectionString

# 4. Create Azure Container Registry (ACR)
Write-Host "Creating Azure Container Registry '$containerRegistryName'..."
az acr create `
    --resource-group $resourceGroupName `
    --name $containerRegistryName `
    --sku Basic `
    --admin-enabled $true

# 5. Build and Push Docker Image to ACR
Write-Host "Building and pushing Docker image to ACR..."
$acrLoginServer = (az acr show --name $containerRegistryName --query loginServer --output tsv)

# Login to ACR
$acrPassword = (az acr credential show --name $containerRegistryName --query "passwords[0].value" --output tsv)
$acrUsername = (az acr credential show --name $containerRegistryName --query "username" --output tsv)
echo $acrPassword | docker login $acrLoginServer -u $acrUsername --password-stdin

# Build the Docker image
Write-Host "Building Docker image '$dockerImageName'..."
# Navigate to the root of the project before running this script
docker build -t $dockerImageName .

# Tag the image for ACR
$acrImageName = "$acrLoginServer/$dockerImageName"
Write-Host "Tagging image as '$acrImageName'..."
docker tag $dockerImageName $acrImageName

# Push the image to ACR
Write-Host "Pushing image to '$acrImageName'..."
docker push $acrImageName

# 6. Create App Service Plan
Write-Host "Creating App Service Plan '$appServicePlanName'..."
az appservice plan create `
    --name $appServicePlanName `
    --resource-group $resourceGroupName `
    --sku B1 `
    --is-linux

# 7. Create Web App for Containers
Write-Host "Creating Web App '$webAppName'..."
az webapp create `
    --resource-group $resourceGroupName `
    --plan $appServicePlanName `
    --name $webAppName `
    --deployment-container-image-name $acrImageName

# 8. Configure Web App Settings
Write-Host "Configuring Web App settings..."
$appSettings = @(
    "MONGO_URI=$mongoConnectionString",
    "TELEGRAM_BOT_TOKEN=$telegramBotToken",
    "FLASK_APP=app.py",
    "SECRET_KEY=$(New-Guid)" # Generate a random secret key
)

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $webAppName `
    --settings $appSettings

# Enable container logging
az webapp log config `
    --name $webAppName `
    --resource-group $resourceGroupName `
    --docker-container-logging filesystem

# --- Final Output ---
$appUrl = "http://$webAppName.azurewebsites.net"
Write-Host -ForegroundColor Green "----------------------------------------------------"
Write-Host -ForegroundColor Green "✅ Deployment Successful!"
Write-Host -ForegroundColor Green "----------------------------------------------------"
Write-Host "Resource Group: $resourceGroupName"
Write-Host "Web App URL: $appUrl"
Write-Host "To view logs, run the following command:"
Write-Host -ForegroundColor Cyan "az webapp log tail --name $webAppName --resource-group $resourceGroupName"
Write-Host "It may take a few minutes for the container to start up."
Write-Host "----------------------------------------------------"
