<#
.SYNOPSIS
    Installs a Windows Task Scheduler entry for the Job Tracker daily email check.
.DESCRIPTION
    Creates a scheduled task that runs the Job Tracker email checker
    daily at 12:00 PM (local time). Uses the project's virtual environment
    python executable.
.NOTES
    Run this script from the project root directory.
    Requires administrative privileges.
#>

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

$projectDir = $PSScriptRoot
$venvPython = Join-Path $projectDir "venv" "Scripts" "python.exe"
$scriptPath = Join-Path $projectDir "scheduler.py"
$logDir     = Join-Path $projectDir "logs"

# ─────────────────────────────────────────────
# Validate
# ─────────────────────────────────────────────
if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual environment not found at: $venvPython"
    Write-Error "Run: python -m venv venv"
    exit 1
}

if (-not (Test-Path $scriptPath)) {
    Write-Error "scheduler.py not found at: $scriptPath"
    exit 1
}

# ─────────────────────────────────────────────
# Create logs directory
# ─────────────────────────────────────────────
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# ─────────────────────────────────────────────
# Register scheduled task
# ─────────────────────────────────────────────
$taskName   = "JobTracker_DailyEmailCheck"
$taskDesc   = "Job Tracker: check unread job emails and update Google Sheets daily at 12:00 PM"

$action = New-ScheduledTaskAction `
    -Execute $venvPython `
    -Argument "`"$scriptPath`" --once" `
    -WorkingDirectory $projectDir

$trigger = New-ScheduledTaskTrigger -Daily -At "12:00"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description $taskDesc `
        -Force

    Write-Host "✅ Task Scheduler entry created: '$taskName'" -ForegroundColor Green
    Write-Host "   Runs daily at 12:00 PM" -ForegroundColor Gray
    Write-Host "   Python: $venvPython" -ForegroundColor Gray
    Write-Host "   Script: $scriptPath" -ForegroundColor Gray
    Write-Host "   Logs:   $logDir\scheduler.log" -ForegroundColor Gray
} catch {
    Write-Error "Failed to register scheduled task: $_"
    exit 1
}

# ─────────────────────────────────────────────
# Display existing task info
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "To view the task, run:"
Write-Host "  Get-ScheduledTask -TaskName '$taskName' | Format-List *" -ForegroundColor Cyan
Write-Host ""
Write-Host "To uninstall, run:"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false" -ForegroundColor Yellow
