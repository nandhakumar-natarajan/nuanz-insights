<#
Simple deploy script for ai-dashboard.html.
Usage: run this from C:\Users\USER\Insights where ai-dashboard.html lives.
This script will attempt to create a backup of the remote file and then upload the local file via scp.
It requires OpenSSH `ssh` and `scp` to be available in your shell PATH.
#>

param(
  [Parameter(Mandatory=$false)] [string] $Server,
  [Parameter(Mandatory=$false)] [string] $User,
  [Parameter(Mandatory=$false)] [int] $Port = 22,
  [Parameter(Mandatory=$false)] [string] $RemotePath = "/var/www/html/ai-dashboard.html"
)

if(-not $Server){ $Server = Read-Host 'Server (host or ip)'}
if(-not $User){ $User = Read-Host 'SSH user'}

Write-Host "Backing up remote file on $User@$Server:$RemotePath"
$backupCmd = "cp '$RemotePath' '${RemotePath}.bak.$(date +%Y%m%d%H%M%S)'"
# Note: the $(date ...) is evaluated on the remote host
$sshCmd = "ssh -p $Port $User@$Server '$backupCmd'"
Write-Host "Running: $sshCmd"
& ssh -p $Port $User@$Server $backupCmd
if($LASTEXITCODE -ne 0){
  Write-Warning "Remote backup command returned non-zero exit code. Proceeding anyway."
}

# Upload with scp
$localFile = Join-Path (Get-Location) 'ai-dashboard.html'
if(-not (Test-Path $localFile)){
  Write-Error "Local file $localFile not found. Run this script from the Insights folder."
  exit 1
}

Write-Host "Uploading $localFile to $User@$Server:$RemotePath"
& scp -P $Port $localFile "$User@$Server:$RemotePath"
if($LASTEXITCODE -ne 0){
  Write-Error "scp failed (exit $LASTEXITCODE)."
  exit $LASTEXITCODE
}

Write-Host "Upload complete. Verify with a browser or curl. Example:" -ForegroundColor Green
Write-Host "curl -sS https://$Server/ai-dashboard.html | head -n 40"
Write-Host "If the site is behind a CDN, purge the CDN cache for the file."

Write-Host "Done." -ForegroundColor Green
