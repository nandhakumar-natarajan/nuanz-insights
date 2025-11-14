# Deploy script for ai-dashboard.html to boondfs.in
# Usage: .\deploy_dashboard.ps1

param(
    [string]$Server = "boondfs.in",
    [string]$User = "",
    [string]$Port = "22",
    [string]$RemotePath = "/var/www/html/ai-dashboard.html"
)

Write-Host "=== AI Dashboard Deployment Script ===" -ForegroundColor Green
Write-Host ""

# Check if file exists
if (-not (Test-Path ".\ai-dashboard.html")) {
    Write-Error "ai-dashboard.html not found in current directory"
    exit 1
}

Write-Host "✓ Found ai-dashboard.html" -ForegroundColor Green

# Get SSH user if not provided
if ([string]::IsNullOrEmpty($User)) {
    $User = Read-Host "Enter SSH username for $Server"
}

Write-Host ""
Write-Host "Deployment Details:" -ForegroundColor Yellow
Write-Host "  Server: $Server"
Write-Host "  User: $User"
Write-Host "  Port: $Port"
Write-Host "  Remote Path: $RemotePath"
Write-Host ""

# Test SSH connectivity
Write-Host "Testing SSH connectivity..." -ForegroundColor Yellow
$sshTest = ssh -o ConnectTimeout=10 -o BatchMode=yes -p $Port "$User@$Server" "echo 'SSH OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warning "SSH test failed. This might be normal if password auth is required."
    Write-Host "SSH output: $sshTest"
    Write-Host ""
}

# Backup existing file (optional)
Write-Host "Creating backup of existing file..." -ForegroundColor Yellow
$backupCmd = "cp '$RemotePath' '${RemotePath}.backup.\$(date +%Y%m%d_%H%M%S)' 2>/dev/null; echo 'Backup attempted'"
ssh -p $Port "$User@$Server" $backupCmd

# Upload the file
Write-Host ""
Write-Host "Uploading ai-dashboard.html..." -ForegroundColor Yellow
scp -P $Port ".\ai-dashboard.html" "$User@${Server}:$RemotePath"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Upload successful!" -ForegroundColor Green
    
    # Verify the upload
    Write-Host ""
    Write-Host "Verifying deployment..." -ForegroundColor Yellow
    
    # Check file exists on server
    $verifyCmd = "ls -la '$RemotePath'"
    ssh -p $Port "$User@$Server" $verifyCmd
    
    Write-Host ""
    Write-Host "Testing web access..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "https://$Server/ai-dashboard.html" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Website is accessible!" -ForegroundColor Green
            Write-Host "✓ URL: https://$Server/ai-dashboard.html" -ForegroundColor Green
        } else {
            Write-Warning "Website returned status code: $($response.StatusCode)"
        }
    } catch {
        Write-Warning "Could not test web access: $($_.Exception.Message)"
        Write-Host "Try manually: https://$Server/ai-dashboard.html"
    }
} else {
    Write-Error "Upload failed with exit code: $LASTEXITCODE"
    Write-Host ""
    Write-Host "Common issues and solutions:" -ForegroundColor Yellow
    Write-Host "1. Permission denied: Try uploading to /tmp first, then move with sudo"
    Write-Host "2. Authentication failed: Check SSH key or password"
    Write-Host "3. Path doesn't exist: Verify the remote path is correct"
    Write-Host ""
    Write-Host "Alternative upload to /tmp:" -ForegroundColor Cyan
    Write-Host "scp -P $Port .\ai-dashboard.html $User@${Server}:/tmp/"
    Write-Host "ssh $User@$Server 'sudo mv /tmp/ai-dashboard.html $RemotePath'"
}

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green