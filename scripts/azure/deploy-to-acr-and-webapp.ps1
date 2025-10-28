<#
Non-interactive Azure deployment script for eCertificate

Requirements (environment variables):
 - AZ_SUBSCRIPTION_ID (optional if using `az login` already)
 - RESOURCE_GROUP
 - ACR_NAME
 - WEBAPP_NAME
 - TELEGRAM_BOT_TOKEN
 - LOCATION (optional, defaults to EastUS)
 - APP_SERVICE_PLAN_NAME (optional, defaults to <webapp>-plan)
 - APP_SERVICE_PLAN_SKU (optional, defaults to B1)
 - MONGO_URI (optional)
 - SECRET_KEY (optional, generated if not provided)

This script assumes `az` CLI and Docker are installed and available in PATH.
For CI, use a service principal or `az login --service-principal` before running.

This script is intentionally non-destructive: it creates missing resources but will NOT delete existing ones.
#>

param()

$ErrorActionPreference = 'Stop'

function Get-RequiredEnv([string]$name) {
    $val = [Environment]::GetEnvironmentVariable($name)
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Error "Environment variable '$name' is required but not set."
        exit 1
    }
    return $val
}

function New-ResourceGroupIfMissing([string]$name, [string]$location) {
    Write-Host "Ensuring resource group '$name' exists in $location..."
    $exists = az group exists --name $name
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to check if resource group '$name' exists."
        exit $LASTEXITCODE
    }
    if ($exists.Trim().ToLower() -ne 'true') {
        Write-Host "Creating resource group '$name'..."
        az group create --name $name --location $location | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create resource group '$name'."
            exit $LASTEXITCODE
        }
    } else {
        Write-Host "Resource group '$name' already exists."
    }
}

function New-AcrIfMissing([string]$resourceGroup, [string]$acrName, [string]$location) {
    Write-Host "Ensuring Azure Container Registry '$acrName' exists..."
    $loginServer = az acr show --name $acrName --resource-group $resourceGroup --query loginServer -o tsv 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($loginServer)) {
        Write-Host "Creating Azure Container Registry '$acrName' (Basic SKU)..."
        az acr create --name $acrName --resource-group $resourceGroup --sku Basic --location $location --admin-enabled true | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create Azure Container Registry '$acrName'."
            exit $LASTEXITCODE
        }
        $loginServer = az acr show --name $acrName --resource-group $resourceGroup --query loginServer -o tsv
    } else {
        Write-Host "Azure Container Registry '$acrName' already exists. Ensuring admin user is enabled..."
        az acr update --name $acrName --resource-group $resourceGroup --admin-enabled true | Out-Null
    }
    if ([string]::IsNullOrWhiteSpace($loginServer)) {
        Write-Error "Unable to resolve login server for ACR '$acrName'."
        exit 1
    }
    return $loginServer.Trim()
}

function New-AppServicePlanIfMissing([string]$resourceGroup, [string]$planName, [string]$location, [string]$sku) {
    Write-Host "Ensuring App Service plan '$planName' exists..."
    az appservice plan show --name $planName --resource-group $resourceGroup | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Creating App Service plan '$planName' (Linux, $sku)..."
        az appservice plan create --name $planName --resource-group $resourceGroup --location $location --is-linux --sku $sku | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create App Service plan '$planName'."
            exit $LASTEXITCODE
        }
    } else {
        Write-Host "App Service plan '$planName' already exists."
    }
}

function New-WebAppIfMissing([string]$resourceGroup, [string]$webAppName, [string]$planName, [string]$placeholderImage) {
    Write-Host "Ensuring Web App '$webAppName' exists..."
    az webapp show --name $webAppName --resource-group $resourceGroup | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Creating Web App '$webAppName' using placeholder container..."
        az webapp create --resource-group $resourceGroup --plan $planName --name $webAppName --deployment-container-image-name $placeholderImage | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create Web App '$webAppName'."
            exit $LASTEXITCODE
        }
    } else {
        Write-Host "Web App '$webAppName' already exists."
    }
}

function Get-AcrCredentials([string]$resourceGroup, [string]$acrName) {
    Write-Host "Retrieving credentials for ACR '$acrName'..."
    $creds = az acr credential show --name $acrName --resource-group $resourceGroup | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0 -or $null -eq $creds) {
        Write-Error "Failed to retrieve credentials for ACR '$acrName'."
        exit $LASTEXITCODE
    }
    if ($creds.passwords.Count -eq 0 -or [string]::IsNullOrWhiteSpace($creds.passwords[0].value)) {
        Write-Error "ACR '$acrName' returned no admin passwords."
        exit 1
    }
    return @{ Username = $creds.username; Password = $creds.passwords[0].value }
}

Write-Host "Starting non-interactive deploy-to-acr-and-webapp.ps1"

# Read env vars (required)
$resourceGroup = Get-RequiredEnv 'RESOURCE_GROUP'
$acrName = Get-RequiredEnv 'ACR_NAME'
$webAppName = Get-RequiredEnv 'WEBAPP_NAME'
$telegramBotToken = Get-RequiredEnv 'TELEGRAM_BOT_TOKEN'

# Optional env vars
$mongoUri = [Environment]::GetEnvironmentVariable('MONGO_URI')
$secretKey = [Environment]::GetEnvironmentVariable('SECRET_KEY')
if ([string]::IsNullOrWhiteSpace($secretKey)) { $secretKey = [Guid]::NewGuid().ToString() }
$location = [Environment]::GetEnvironmentVariable('LOCATION')
if ([string]::IsNullOrWhiteSpace($location)) { $location = 'EastUS' }
$appServicePlanName = [Environment]::GetEnvironmentVariable('APP_SERVICE_PLAN_NAME')
if ([string]::IsNullOrWhiteSpace($appServicePlanName)) { $appServicePlanName = "$webAppName-plan" }
$appServicePlanSku = [Environment]::GetEnvironmentVariable('APP_SERVICE_PLAN_SKU')
if ([string]::IsNullOrWhiteSpace($appServicePlanSku)) { $appServicePlanSku = 'B1' }
Write-Host "Resource Group: $resourceGroup"
Write-Host "ACR: $acrName"
Write-Host "Web App: $webAppNacd C:\Users\Den\Downloads\eCertificate-1
$env:RESOURCE_GROUP     = 'nexus-ai-rg'
$env:ACR_NAME           = 'ecertificateacr'
$env:WEBAPP_NAME        = 'denx-certificate-app'
$env:TELEGRAM_BOT_TOKEN = '8486963487:AAFaHNd9VfYiDJRcToYg9xfxOc6jd1uyFKM'
az ad sp create-for-rbac --name "eCertificate-deploy" --role contributor --scopes /subscriptions/{7e91bdbf-345c-4da8-81bd-e34087c64227}/resourceGroups/nexus-ai-rg --sdk-auth
# optional overrides if needed
$env:LOCATION              = 'uaenorth'
$env:APP_SERVICE_PLAN_NAME = 'your-plan'
$env:APP_SERVICE_PLAN_SKU  = 'B1'
$env:MONGO_URI             = 'mongodb+srv://ShanxAi:@Harsh7991@cluster0.vpijpmf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
$env:SECRET_KEY            = 'custom-secret'

.\scripts\azure\deploy-to-acr-and-webapp.ps1cd C:\Users\Den\Downloads\eCertificate-1
$env:RESOURCE_GROUP     = 'your-resource-group'
$env:ACR_NAME           = 'youracrname'
$env:WEBAPP_NAME        = 'your-webapp-name'
$env:TELEGRAM_BOT_TOKEN = 'paste-bot-token'

# optional overrides if needed
$env:LOCATION              = 'uaenorth'
$env:APP_SERVICE_PLAN_NAME = 'your-plan'
$env:APP_SERVICE_PLAN_SKU  = 'B1'
$env:MONGO_URI             = 'mongodb+srv://...'
$env:SECRET_KEY            = 'custom-secret'

.\scripts\azure\deploy-to-acr-and-webapp.ps1cd C:\Users\Den\Downloads\eCertificate-1
$env:RESOURCE_GROUP     = 'your-resource-group'
$env:ACR_NAME           = 'youracrname'
$env:WEBAPP_NAME        = 'your-webapp-name'
$env:TELEGRAM_BOT_TOKEN = 'paste-bot-token'

# optional overrides if needed
$env:LOCATION              = 'uaenorth'
$env:APP_SERVICE_PLAN_NAME = 'your-plan'
$env:APP_SERVICE_PLAN_SKU  = 'B1'
$env:MONGO_URI             = 'mongodb+srv://...'
$env:SECRET_KEY            = 'custom-secret'

.\scripts\azure\deploy-to-acr-and-webapp.ps1cd C:\Users\Den\Downloads\eCertificate-1
$env:RESOURCE_GROUP     = 'your-resource-group'
$env:ACR_NAME           = 'youracrname'
$env:WEBAPP_NAME        = 'your-webapp-name'
$env:TELEGRAM_BOT_TOKEN = 'paste-bot-token'

# optional overrides if needed
$env:LOCATION              = 'EastUS'
$env:APP_SERVICE_PLAN_NAME = 'your-plan'
$env:APP_SERVICE_PLAN_SKU  = 'B1'
$env:MONGO_URI             = 'mongodb+srv://...'
$env:SECRET_KEY            = 'custom-secret'

.\scripts\azure\deploy-to-acr-and-webapp.ps1cd C:\Users\Den\Downloads\eCertificate-1
$env:RESOURCE_GROUP     = 'your-resource-group'
$env:ACR_NAME           = 'youracrname'
$env:WEBAPP_NAME        = 'your-webapp-name'
$env:TELEGRAM_BOT_TOKEN = 'paste-bot-token'

# optional overrides if needed
$env:LOCATION              = 'EastUS'
$env:APP_SERVICE_PLAN_NAME = 'your-plan'
$env:APP_SERVICE_PLAN_SKU  = 'B1'
$env:MONGO_URI             = 'mongodb+srv://...'
$env:SECRET_KEY            = 'custom-secret'

.\scripts\azure\deploy-to-acr-and-webapp.ps1cd C:\Users\Den\Downloads\eCertificate-1
$env:RESOURCE_GROUP     = 'your-resource-group'
$env:ACR_NAME           = 'youracrname'
$env:WEBAPP_NAME        = 'your-webapp-name'
$env:TELEGRAM_BOT_TOKEN = 'paste-bot-token'

# optional overrides if needed
$env:LOCATION              = 'EastUS'
$env:APP_SERVICE_PLAN_NAME = 'your-plan'
$env:APP_SERVICE_PLAN_SKU  = 'B1'
$env:MONGO_URI             = 'mongodb+srv://...'
$env:SECRET_KEY            = 'custom-secret'

.\scripts\azure\deploy-to-acr-and-webapp.ps1me"
Write-Host "App Service Plan: $appServicePlanName ($appServicePlanSku)"
Write-Host "Location: $location"
$placeholderImage = 'mcr.microsoft.com/appsvc/sample-images/aspnetcore:latest'

# Optional subscription selection
$subscriptionId = [Environment]::GetEnvironmentVariable('AZ_SUBSCRIPTION_ID')
if (-not [string]::IsNullOrWhiteSpace($subscriptionId)) {
    Write-Host "Setting subscription to $subscriptionId"
    az account set --subscription $subscriptionId | Out-Null
}

New-ResourceGroupIfMissing -name $resourceGroup -location $location
$acrLoginServer = New-AcrIfMissing -resourceGroup $resourceGroup -acrName $acrName -location $location
Write-Host "ACR login server: $acrLoginServer"
New-AppServicePlanIfMissing -resourceGroup $resourceGroup -planName $appServicePlanName -location $location -sku $appServicePlanSku
New-WebAppIfMissing -resourceGroup $resourceGroup -webAppName $webAppName -planName $appServicePlanName -placeholderImage $placeholderImage
$acrCredentials = Get-AcrCredentials -resourceGroup $resourceGroup -acrName $acrName
$acrUser = $acrCredentials.Username
$acrPassword = $acrCredentials.Password

Write-Host "Logging into ACR..."
az acr login --name $acrName

# Build and tag image
$localImage = 'ecertificate-app:latest'
$acrImage = "$acrLoginServer/ecertificate-app:latest"

Write-Host "Building Docker image ($localImage)..."
docker build -t $localImage .

Write-Host "Tagging image for ACR ($acrImage)..."
docker tag $localImage $acrImage

Write-Host "Pushing image to ACR..."
docker push $acrImage

Write-Host "Configuring Web App to use image..."
az webapp config container set --name $webAppName --resource-group $resourceGroup --docker-custom-image-name $acrImage --docker-registry-server-url "https://$acrLoginServer" --docker-registry-server-user $acrUser --docker-registry-server-password $acrPassword

Write-Host "Setting application settings on Web App..."
$settings = @(
    "TELEGRAM_BOT_TOKEN=$telegramBotToken",
    "FLASK_APP=app.py",
    "SECRET_KEY=$secretKey",
    "WEBSITES_PORT=5000"
)
if (-not [string]::IsNullOrWhiteSpace($mongoUri)) { $settings += "MONGO_URI=$mongoUri" }

az webapp config appsettings set --resource-group $resourceGroup --name $webAppName --settings $settings

Write-Host "Enabling container logging (filesystem)..."
az webapp log config --name $webAppName --resource-group $resourceGroup --docker-container-logging filesystem

Write-Host "Deployment finished. Web App should start the new container shortly."
Write-Host "Web App URL: https://$webAppName.azurewebsites.net"
Write-Host "To tail logs: az webapp log tail --name $webAppName --resource-group $resourceGroup"

Exit 0
