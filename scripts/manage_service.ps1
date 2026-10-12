<#>
.SYNOPSIS
    Redragon Controller - Windows Service Manager
.DESCRIPTION
    PowerShell script to install, manage, and uninstall the Redragon Controller Windows Service.
.NOTES
    Run as Administrator!
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Install', 'Uninstall', 'Start', 'Stop', 'Restart', 'Status', 'Console')]
    [string]$Action,
    
    [string]$InstallPath = ".\dist"
)

# Check Admin
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script requires Administrator privileges. Run PowerShell as Administrator."
    exit 1
}

$serviceExe = Join-Path $InstallPath "redragon-service.exe"
$cliExe = Join-Path $InstallPath "redragon-controller.exe"

if (-not (Test-Path $serviceExe)) {
    Write-Error "Service executable not found at: $serviceExe"
    Write-Error "Run build_windows.bat first to build the executables."
    exit 1
}

function Install-Service {
    Write-Host "Installing Redragon Controller Service..." -ForegroundColor Green
    & $serviceExe install
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service installed. Starting..." -ForegroundColor Green
        Start-Service
    }
}

function Uninstall-Service {
    Write-Host "Stopping service..." -ForegroundColor Yellow
    & $serviceExe stop
    Start-Sleep 2
    Write-Host "Uninstalling service..." -ForegroundColor Yellow
    & $serviceExe uninstall
}

function Start-Service {
    Write-Host "Starting service..." -ForegroundColor Green
    & $serviceExe start
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Service started! API at http://localhost:8080" -ForegroundColor Green
    }
}

function Stop-Service {
    Write-Host "Stopping service..." -ForegroundColor Yellow
    & $serviceExe stop
}

function Restart-Service {
    Stop-Service
    Start-Sleep 3
    Start-Service
}

function Get-Status {
    $service = Get-Service -Name "RedragonController" -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "Service Status: $($service.Status)" -ForegroundColor Cyan
        Write-Host "Start Type: $($service.StartType)" -ForegroundColor Cyan
    } else {
        Write-Host "Service not installed" -ForegroundColor Red
    }
}

function Run-Console {
    Write-Host "Running in console mode (Ctrl+C to stop)..." -ForegroundColor Cyan
    & $cliExe
}

switch ($Action) {
    'Install'   { Install-Service }
    'Uninstall' { Uninstall-Service }
    'Start'     { Start-Service }
    'Stop'      { Stop-Service }
    'Restart'   { Restart-Service }
    'Status'    { Get-Status }
    'Console'   { Run-Console }
}