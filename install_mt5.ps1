$ErrorActionPreference = "Stop"

Write-Host "Downloading MT5 Setup..."
Invoke-WebRequest -Uri "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" -OutFile "mt5setup.exe"

Write-Host "Running MT5 Installer silently..."
Start-Process -FilePath "mt5setup.exe" -ArgumentList "/auto" -NoNewWindow

Write-Host "Waiting for installation to complete (this may take 1-2 minutes)..."
$installedDir = "C:\Program Files\MetaTrader 5"
$targetDir = "e:\forex data downloader\backend\engines\mt5_bridge\MT5_Terminal"

$timeout = 180 # 3 minutes timeout
$elapsed = 0

while (-not (Test-Path "$installedDir\terminal64.exe")) {
    Start-Sleep -Seconds 5
    $elapsed += 5
    if ($elapsed -ge $timeout) {
        Write-Host "Timeout reached! Installation took too long or failed."
        exit 1
    }
}

Write-Host "MT5 Installed successfully! Waiting 10 seconds for it to finalize..."
Start-Sleep -Seconds 10

# Kill the terminal if it auto-started
Get-Process | Where-Object {$_.Name -eq "terminal64"} | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Copying MT5 folder to Docker context..."
if (Test-Path $targetDir) {
    Remove-Item -Recurse -Force $targetDir
}
Copy-Item -Path $installedDir -Destination $targetDir -Recurse -Force

Write-Host "Done! You can now build the Docker image."
