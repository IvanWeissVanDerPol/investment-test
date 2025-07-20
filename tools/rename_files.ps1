# PowerShell script to rename markdown files with more descriptive names
# Run this script from the project root directory

# Bank-related files
Rename-Item -Path ".\banks\final-updated-recommendations.md" -NewName "BANKING-STRATEGY-FINAL.md" -Force

# Analysis files
Rename-Item -Path ".\analysis\recommendations.md" -NewName "ANALYSIS-STRATEGY-RECOMMENDATIONS.md" -Force

# Investment sector files
Rename-Item -Path ".\investments\sectors\agriculture-robotics.md" -NewName "SECTOR-AGRI-ROBOTICS.md" -Force
Rename-Item -Path ".\investments\sectors\ai-development.md" -NewName "SECTOR-AI-SOFTWARE.md" -Force
Rename-Item -Path ".\investments\sectors\ai-hardware.md" -NewName "SECTOR-AI-HARDWARE.md" -Force

# Tracking files
Rename-Item -Path ".\tracking\portfolio-template.md" -NewName "TRACKING-PORTFOLIO-TEMPLATE.md" -Force
Rename-Item -Path ".\tracking\portfolio-tracker-2025-Q3.md" -NewName "TRACKING-PORTFOLIO-2025-Q3.md" -Force
Rename-Item -Path ".\tracking\top-investor-monitoring-guide.md" -NewName "TRACKING-MONITORING-GUIDE.md" -Force

# Reference files
Rename-Item -Path ".\reference\MAINTENANCE.md" -NewName "REF-MAINTENANCE-GUIDE.md" -Force
Rename-Item -Path ".\reference\quick-reference.md" -NewName "REF-QUICK-REFERENCE.md" -Force

# Tools
Rename-Item -Path ".\tools\mcp-setup.md" -NewName "TOOLS-MCP-SETUP.md" -Force

Write-Host "Files have been renamed with more descriptive names."
