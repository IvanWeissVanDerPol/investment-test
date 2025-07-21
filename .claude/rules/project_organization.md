# Project Organization Rules

This document establishes strict rules for organizing files in the investment analysis system to maintain clean structure and prevent root directory clutter.

## 🎯 Core Organization Principles

### **RULE 1: Code Placement**
- **ALL Python code MUST go in `src/investment_system/`**
- **NO Python modules (.py files) in the root directory**
- **NO code in docs/, config/, scripts/, or other directories**

### **RULE 2: Documentation Placement**
- **ALL documentation MUST go in `docs/`**
- **NO .md files in the root directory except:**
  - `README.md` (project overview only)
  - `CHANGELOG.md` (version history only)
  - `LICENSE.md` (license only)

### **RULE 3: Root Directory Restrictions**
- **Root directory should ONLY contain:**
  - Essential project files: `README.md`, `LICENSE.md`, `CHANGELOG.md`
  - Configuration files: `pyproject.toml`, `.gitignore`, `.env.example`
  - Directory structure: `src/`, `docs/`, `tests/`, `config/`, `scripts/`, etc.

## 📁 Mandatory Directory Structure

```
ivan/
├── src/investment_system/          # 🚨 ONLY location for Python code
│   ├── ai/                        # AI and Claude integration modules
│   ├── analysis/                  # Market analysis modules
│   ├── data/                      # Data collection and management
│   ├── ethics/                    # Ethics screening system
│   ├── integrations/              # Cross-module integrations
│   ├── monitoring/                # System monitoring
│   ├── portfolio/                 # Portfolio management
│   ├── reporting/                 # Report generation
│   ├── tracking/                  # Performance tracking
│   └── utils/                     # Utility functions
├── docs/                          # 🚨 ONLY location for documentation
│   ├── guides/                    # Setup and usage guides
│   ├── api/                       # API documentation
│   ├── research/                  # Market research documents
│   ├── strategy/                  # Investment strategies
│   ├── project_status/            # Project tracking
│   └── architecture/              # System architecture docs
├── tests/                         # Test files only
├── config/                        # Configuration files only
├── data/                          # Data files only
├── scripts/                       # Automation scripts only
├── reports/                       # Generated reports only
├── cache/                         # System cache only
└── .claude/                       # Claude Code configuration only
```

## 🚨 Strict File Placement Rules

### **Python Code Files (.py)**
```bash
✅ ALLOWED:
- src/investment_system/**/*.py
- tests/**/*.py
- scripts/**/*.py (automation only)

❌ FORBIDDEN:
- Root directory: *.py
- docs/**/*.py
- config/**/*.py
- Any other location
```

### **Documentation Files (.md)**
```bash
✅ ALLOWED:
- docs/**/*.md (preferred location)
- README.md (root, project overview only)
- CHANGELOG.md (root, version history only)
- LICENSE.md (root, license only)

❌ FORBIDDEN:
- src/**/*.md
- config/**/*.md
- scripts/**/*.md
- Random .md files in root
```

### **Configuration Files**
```bash
✅ ALLOWED:
- config/*.json (configuration only)
- .env.example (root)
- pyproject.toml (root)
- .gitignore (root)

❌ FORBIDDEN:
- *.json files in root (except package.json if needed)
- Configuration scattered in other directories
```

### **Data Files**
```bash
✅ ALLOWED:
- data/reference/*.json (reference data)
- data/cache/* (temporary data)
- data/exports/* (generated data)

❌ FORBIDDEN:
- Data files in config/
- Data files in root
- Data files mixed with code
```

## 📋 File Creation Guidelines

### **When Creating New Python Modules:**
1. **Determine the correct package:**
   - AI/ML code → `src/investment_system/ai/`
   - Data collection → `src/investment_system/data/`
   - Analysis logic → `src/investment_system/analysis/`
   - Ethics screening → `src/investment_system/ethics/`
   - Portfolio management → `src/investment_system/portfolio/`
   - Reporting → `src/investment_system/reporting/`
   - Utilities → `src/investment_system/utils/`

2. **Follow naming conventions:**
   - Use snake_case for file names
   - Be descriptive: `youtube_content_analyzer.py` not `analyzer.py`
   - Include module type: `*_engine.py`, `*_manager.py`, `*_client.py`

3. **Update package imports:**
   - Add to appropriate `__init__.py`
   - Export public classes/functions

### **When Creating Documentation:**
1. **Determine the correct docs subdirectory:**
   - Setup instructions → `docs/guides/`
   - API documentation → `docs/api/`
   - System design → `docs/architecture/`
   - Research notes → `docs/research/`
   - Project status → `docs/project_status/`

2. **Use clear naming:**
   - `installation_guide.md` not `setup.md`
   - `youtube_api_integration.md` not `youtube.md`
   - `ethics_system_architecture.md` not `ethics.md`

3. **Include proper metadata:**
   - Date created/updated
   - Author information
   - Purpose and scope

## 🔍 Regular Organization Audits

### **Monthly Checks:**
- [ ] No .py files in root directory
- [ ] No .md files outside docs/ (except README, LICENSE, CHANGELOG)
- [ ] All packages have proper `__init__.py` files
- [ ] No orphaned files in wrong directories

### **Before Each Commit:**
- [ ] New files in correct directories
- [ ] Updated appropriate `__init__.py` if needed
- [ ] Documentation updated if adding new modules
- [ ] No temporary files committed

## 🚧 Exception Handling

### **Allowed Exceptions:**
1. **Root Level Files:**
   - `README.md` - Project overview and quick start
   - `CHANGELOG.md` - Version history
   - `LICENSE.md` - Project license
   - `pyproject.toml` - Python project configuration
   - `.gitignore` - Git ignore rules
   - `.env.example` - Environment variables template

2. **Script Files:**
   - `scripts/*.py` - Automation and utility scripts
   - `scripts/*.bat` - Windows batch files

3. **Test Files:**
   - `tests/**/*.py` - Test modules
   - `tests/conftest.py` - Pytest configuration

### **NO Exceptions For:**
- Business logic in root directory
- Documentation outside docs/
- Configuration files scattered around
- Data files mixed with code
- Temporary files committed to git

## 🎯 Benefits of This Organization

### **Clarity:**
- Developers know exactly where to find/place files
- Clear separation between code, docs, config, and data
- Easier onboarding for new team members

### **Maintainability:**
- Easier to refactor when everything is properly organized
- Clear dependency management
- Simpler backup and deployment strategies

### **Scalability:**
- Structure supports project growth
- Easy to add new modules in correct locations
- Clear boundaries for different components

### **Professional Standards:**
- Follows Python packaging best practices
- Meets industry standards for project organization
- Clean structure for code reviews and audits

## 🚨 Enforcement

These rules are **MANDATORY** and will be enforced through:
- Pre-commit hooks (future implementation)
- Code review requirements
- Regular project audits
- Automated checks in CI/CD pipeline

**Violations of these rules should be caught and corrected immediately.**

---

*This document should be reviewed and updated as the project evolves, but the core principles of keeping code in `src/` and docs in `docs/` should remain constant.*