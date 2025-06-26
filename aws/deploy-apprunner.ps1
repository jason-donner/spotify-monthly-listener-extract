# AWS App Runner Deployment Script for Spotify Monthly Listener Extract
# This script helps you deploy your Flask app to AWS App Runner

Write-Host "AWS App Runner Deployment Script" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Check if AWS CLI is installed
try {
    $awsVersion = aws --version 2>$null
    Write-Host "AWS CLI found: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "AWS CLI not found. Please install it from: https://aws.amazon.com/cli/" -ForegroundColor Red
    Write-Host "After installation, run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Check AWS credentials
try {
    $awsIdentity = aws sts get-caller-identity 2>$null | ConvertFrom-Json
    $awsAccountId = $awsIdentity.Account
    Write-Host "AWS credentials configured (Account: $awsAccountId)" -ForegroundColor Green
} catch {
    Write-Host "AWS credentials not configured. Please run: aws configure" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Setting up deployment configuration..." -ForegroundColor Cyan
Write-Host ""

# Generate Flask secret key
Add-Type -AssemblyName System.Web
$FlaskSecretKey = [System.Web.Security.Membership]::GeneratePassword(64, 0)
Write-Host "Generated Flask secret key" -ForegroundColor Green

# Get admin password
Write-Host ""
$AdminPassword = Read-Host "Enter admin password for your app" -AsSecureString
$AdminPasswordText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($AdminPassword))

if (-not $AdminPasswordText) {
    Write-Host "Admin password is required" -ForegroundColor Red
    exit 1
}

# Get Spotify credentials
Write-Host ""
Write-Host "Spotify Developer App Setup:" -ForegroundColor Yellow
Write-Host "1. Go to: https://developer.spotify.com/dashboard/" -ForegroundColor Yellow
Write-Host "2. Select your app or create a new one" -ForegroundColor Yellow
Write-Host "3. Copy the Client ID and Client Secret" -ForegroundColor Yellow
Write-Host ""

$SpotifyClientId = Read-Host "Enter your Spotify Client ID"
if (-not $SpotifyClientId) {
    Write-Host "Spotify Client ID is required" -ForegroundColor Red
    exit 1
}

$SpotifyClientSecret = Read-Host "Enter your Spotify Client Secret" -AsSecureString
$SpotifyClientSecretText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SpotifyClientSecret))

if (-not $SpotifyClientSecretText) {
    Write-Host "Spotify Client Secret is required" -ForegroundColor Red
    exit 1
}

# Generate service name
$ServiceName = "spotify-listener-extract-$(Get-Random -Minimum 1000 -Maximum 9999)"
$RedirectUri = "https://$ServiceName.us-east-1.awsapprunner.com/admin/callback"
$AppUrl = "https://$ServiceName.us-east-1.awsapprunner.com"
$AdminUrl = "$AppUrl/admin_login"

Write-Host ""
Write-Host "Deployment Configuration Generated:" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host "Service Name: $ServiceName" -ForegroundColor White
Write-Host "App URL: $AppUrl" -ForegroundColor White
Write-Host "Admin URL: $AdminUrl" -ForegroundColor White
Write-Host "Redirect URI: $RedirectUri" -ForegroundColor White
Write-Host ""

# Create configuration content
$ConfigLines = @(
    "AWS App Runner Deployment Configuration"
    "======================================="
    "Generated: $(Get-Date)"
    ""
    "SERVICE CONFIGURATION:"
    "- Service Name: $ServiceName"
    "- Region: us-east-1"
    "- App URL: $AppUrl"
    "- Admin URL: $AdminUrl"
    "- Redirect URI: $RedirectUri"
    ""
    "ENVIRONMENT VARIABLES FOR AWS:"
    "FLASK_SECRET_KEY=$FlaskSecretKey"
    "ADMIN_PASSWORD=$AdminPasswordText"
    "SPOTIPY_CLIENT_ID=$SpotifyClientId"
    "SPOTIPY_CLIENT_SECRET=$SpotifyClientSecretText"
    "SPOTIPY_REDIRECT_URI=$RedirectUri"
    "PORT=8080"
    "FLASK_DEBUG=false"
    ""
    "NEXT STEPS:"
    "1. Complete App Runner setup in AWS Console"
    "2. Update Spotify Developer App with redirect URI"
    "3. Test deployment"
    ""
    "AWS CONSOLE LINK:"
    "https://console.aws.amazon.com/apprunner/"
)

# Save configuration
$ConfigLines -join "`r`n" | Out-File -FilePath "aws-deployment-config.txt" -Encoding UTF8

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "===========" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Go to AWS App Runner Console:" -ForegroundColor Yellow
Write-Host "   https://console.aws.amazon.com/apprunner/" -ForegroundColor Blue
Write-Host ""
Write-Host "2. Create App Runner Service:" -ForegroundColor Yellow
Write-Host "   - Click 'Create service'" -ForegroundColor White
Write-Host "   - Source: Repository" -ForegroundColor White
Write-Host "   - Connect to GitHub" -ForegroundColor White
Write-Host "   - Select your repository" -ForegroundColor White
Write-Host "   - Branch: main" -ForegroundColor White
Write-Host "   - Configuration: Use configuration file (apprunner.yaml)" -ForegroundColor White
Write-Host ""
Write-Host "3. Configure Environment Variables:" -ForegroundColor Yellow
Write-Host "   Copy the environment variables from aws-deployment-config.txt" -ForegroundColor White
Write-Host ""
Write-Host "4. Update Spotify Developer App:" -ForegroundColor Yellow
Write-Host "   - Go to: https://developer.spotify.com/dashboard/" -ForegroundColor Blue
Write-Host "   - Select your app" -ForegroundColor White
Write-Host "   - Edit Settings > Redirect URIs" -ForegroundColor White
Write-Host "   - Add: $RedirectUri" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration saved to: aws-deployment-config.txt" -ForegroundColor Blue
Write-Host ""
Write-Host "Ready for deployment! Follow the instructions above." -ForegroundColor Green

# Clear sensitive variables
$AdminPasswordText = $null
$SpotifyClientSecretText = $null
