# Simple deployment script for ai-dashboard.html
param(
    [string]$Server = "boondfs.in",
    [string]$User = "",
    [string]$RemotePath = "/var/www/html/ai-dashboard.html"
)

Write-Host "=== AI Dashboard Deployment ===" -ForegroundColor Green

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

Write-Host "Uploading to $User@$Server..." -ForegroundColor Yellow

# Upload the file
scp ".\ai-dashboard.html" "$User@${Server}:$RemotePath"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Upload successful!" -ForegroundColor Green
    Write-Host "✓ URL: https://$Server/ai-dashboard.html" -ForegroundColor Green
    
    # Test if accessible
    Write-Host "Testing web access..." -ForegroundColor Yellow
    $testUrl = "https://$Server/ai-dashboard.html"
    try {
        $response = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        Write-Host "✓ Website is live and accessible!" -ForegroundColor Green
    }
    catch {
        Write-Warning "Upload successful but web test failed: $($_.Exception.Message)"
        Write-Host "Try accessing manually: $testUrl"
    }
}
else {
    Write-Error "Upload failed. Try alternative method:"
    Write-Host "scp .\ai-dashboard.html $User@${Server}:/tmp/" -ForegroundColor Cyan
    Write-Host "ssh $User@$Server 'sudo mv /tmp/ai-dashboard.html $RemotePath'" -ForegroundColor Cyan
}