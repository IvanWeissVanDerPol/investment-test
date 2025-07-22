 Y # PowerShell script to archive redundant files while keeping consolidated versions
$archiveDir = "$PSScriptRoot\..\archive\old_files"

# Files to archive (keep the consolidated versions)
$filesToArchive = @(
    "analysis\budget-allocation.md",
    "banks\banks-overview.md",
    "banks\comprehensive-bank-features.md",
    "banks\current-banks.md",
    "banks\dual-citizenship-advantages.md",
    "banks\dukascopy-advanced-strategy.md",
    "banks\dukascopy-ueno-optimization.md",
    "banks\recommendations.md",
    "investments\brokers.md",
    "investments\first-world-ai-robotics-plan.md",
    "investments\itau-dukascopy-investment-plans.md"
)

# Create timestamp for archive
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveSubdir = "$archiveDir\archive_$timestamp"
New-Item -ItemType Directory -Path $archiveSubdir -Force

# Archive files
foreach ($file in $filesToArchive) {
    $source = "$PSScriptRoot\..\$file"
    $destination = "$archiveSubdir\$(Split-Path $file -Leaf)"
    
    if (Test-Path $source) {
        Write-Host "Archiving $file"
        Move-Item -Path $source -Destination $destination -Force
    }
}

Write-Host "Archiving complete. Files moved to: $archiveSubdir"
