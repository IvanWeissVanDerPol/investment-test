#!/bin/bash
# MVP Cleanup Script - Remove 180+ non-revenue files
# This script will delete ~14,000 lines of code to focus on MVP

echo "🚀 MVP Cleanup Script - Creating lean, revenue-generating codebase"
echo "================================================================"
echo ""
echo "This will DELETE 180+ files (~14,000 lines of code)"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Create backup branch with timestamp
BACKUP_BRANCH="backup/pre-mvp-$(date +%Y%m%d-%H%M%S)"
echo "📦 Creating backup branch: $BACKUP_BRANCH"
git checkout -b "$BACKUP_BRANCH"
git add -A
git commit -m "backup: complete state before MVP cleanup" || true
git push origin "$BACKUP_BRANCH" || echo "⚠️  Could not push backup (may need auth)"

# Return to working branch
git checkout integration-claude-review

echo ""
echo "🗑️  Starting deletion of non-MVP files..."
echo ""

# Delete legacy core system (biggest chunk)
echo "Removing legacy core system (60+ files, ~12,000 lines)..."
rm -rf src/core/

# Delete old web application
echo "Removing old Flask web app (15 files)..."
rm -rf src/web/

# Delete Windows batch scripts
echo "Removing batch script tools (40+ files)..."
rm -rf tools/

# Delete MCP integrations (not needed for MVP)
echo "Removing MCP integrations..."
rm -rf mcp/

# Delete scripts directory
echo "Removing over-engineered scripts..."
rm -rf scripts/

# Delete test files from root
echo "Removing test files from root directory..."
rm -f test_*.py

# Delete planning documents
echo "Removing planning documents..."
rm -rf planning/

# Delete reference data (should be in DB)
echo "Removing reference JSON files..."
rm -rf reference/
rm -rf data/reference/

# Delete unnecessary documentation
echo "Removing outdated documentation..."
rm -rf docs/01_project_overview/
rm -rf docs/02_implementation/
rm -rf docs/03_enhancements/
rm -rf docs/05_investment_strategy/
rm -rf docs/06_system_monitoring/
rm -rf docs/07_research_and_analysis/

# Delete kubernetes configs (not needed for MVP)
echo "Removing Kubernetes configs..."
rm -rf deploy/kubernetes/

# Delete PowerBI configs
echo "Removing PowerBI integration..."
rm -f src/config/powerbi_config.json

# Delete unused config JSONs
echo "Removing redundant config files..."
rm -f src/config/analysis.json
rm -f src/config/content.json
rm -f src/config/data.json
rm -f src/config/system.json

# Clean cache directory
echo "Cleaning cache directory..."
rm -rf cache/

# Remove egg-info
echo "Removing build artifacts..."
rm -rf src/*.egg-info/

# Update .gitignore
echo ""
echo "📝 Updating .gitignore..."
cat >> .gitignore << 'EOF'

# MVP Exclusions
cache/
*.egg-info/
src/runtime/
runtime/
*.db
*.db-shm
*.db-wal
.env
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
EOF

# Count the results
echo ""
echo "================================================================"
echo "✅ CLEANUP COMPLETE!"
echo "================================================================"
echo ""

# Statistics
REMAINING_FILES=$(find . -type f -name "*.py" 2>/dev/null | wc -l)
REMAINING_LINES=$(find . -type f -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')

echo "📊 Statistics:"
echo "  - Files deleted: ~180+"
echo "  - Lines removed: ~14,000"
echo "  - Python files remaining: $REMAINING_FILES"
echo "  - Lines remaining: ~$REMAINING_LINES"
echo ""
echo "💰 Ready for MVP development!"
echo "  - Next step: Run 'make install' to reinstall dependencies"
echo "  - Then: Run 'uvicorn investment_system.api:app' to start API"
echo ""
echo "🎯 Focus: Generate revenue with minimal, clean code"