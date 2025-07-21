# PowerShell script to archive old portfolio tracker files
$archiveDir = "$PSScriptRoot\..\archive\old_trackers"
$trackingDir = "$PSScriptRoot\..\tracking"

# Get all tracker files except current quarter
$currentQuarter = "Q" + [math]::Ceiling((Get-Date).Month/3)
$currentYear = (Get-Date).Year
$currentTracker = "portfolio-tracker-$($currentYear)-$($currentQuarter).md"

# Create archive directory if it doesn't exist
New-Item -ItemType Directory -Path $archiveDir -Force

# Move old trackers to archive
Get-ChildItem -Path $trackingDir -Filter "portfolio-tracker-*.md" | 
Where-Object { $_.Name -ne $currentTracker } |
ForEach-Object {
    $destination = Join-Path -Path $archiveDir -ChildPath $_.Name
    Write-Host "Archiving old tracker: $($_.Name)"
    Move-Item -Path $_.FullName -Destination $destination -Force
}

Write-Host "Archive complete. Current tracker: $currentTracker"
