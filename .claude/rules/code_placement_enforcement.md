# Code Placement Enforcement Rules for Claude Code

This file contains strict enforcement rules for Claude Code to maintain proper project organization.

## 🚨 MANDATORY: File Placement Rules

### **Python Code Files (.py)**

**RULE**: ALL Python code MUST be placed in `src/investment_system/` directory structure.

**ENFORCEMENT**:
- ✅ **ALLOWED**: Creating .py files in `src/investment_system/` and its subdirectories
- ✅ **ALLOWED**: Creating .py files in `tests/` for testing
- ✅ **ALLOWED**: Creating .py files in `scripts/` for automation
- ❌ **FORBIDDEN**: Creating ANY .py files in root directory
- ❌ **FORBIDDEN**: Creating .py files in `docs/`, `config/`, `data/`, or other directories

**VIOLATION RESPONSE**: If asked to create a Python file outside these locations, Claude Code must:
1. Refuse to create the file in the wrong location
2. Suggest the correct location within `src/investment_system/`
3. Explain why the correct location is better for project organization

### **Documentation Files (.md)**

**RULE**: ALL documentation MUST be placed in `docs/` directory structure.

**ENFORCEMENT**:
- ✅ **ALLOWED**: Creating .md files in `docs/` and its subdirectories
- ✅ **ALLOWED**: Updating `README.md`, `CHANGELOG.md`, `LICENSE.md` in root (ONLY these files)
- ❌ **FORBIDDEN**: Creating .md files in `src/`, `config/`, or other directories
- ❌ **FORBIDDEN**: Creating random .md files in root directory

**VIOLATION RESPONSE**: If asked to create documentation outside `docs/`, Claude Code must:
1. Refuse to create the file in the wrong location
2. Suggest the appropriate subdirectory within `docs/`
3. Offer to create the file in the correct location instead

## 📁 Specific Directory Mappings

### **When Creating Python Modules:**

```
AI/ML Code → src/investment_system/ai/
├── Claude integration
├── Decision engines
├── Machine learning models
└── AI-powered analysis

Data Management → src/investment_system/data/
├── Data collection
├── API integrations
├── Database connections
└── Data processing

Analysis Code → src/investment_system/analysis/
├── Market analysis
├── Technical analysis
├── Sentiment analysis
└── Prediction engines

Ethics & ESG → src/investment_system/ethics/
├── ESG screening
├── Sustainability scoring
├── Ethics compliance
└── Green investment logic

Portfolio Management → src/investment_system/portfolio/
├── Portfolio optimization
├── Risk management
├── Asset allocation
└── Performance tracking

Reporting → src/investment_system/reporting/
├── Report generation
├── Visualization
├── Export functionality
└── Automated reporting

Utilities → src/investment_system/utils/
├── Helper functions
├── Configuration management
├── Caching systems
└── Common utilities

Integration → src/investment_system/integrations/
├── Cross-module integrations
├── Workflow orchestration
├── API coordination
└── System connectivity
```

### **When Creating Documentation:**

```
Setup & Guides → docs/guides/
├── Installation instructions
├── Usage tutorials
├── Configuration guides
└── Troubleshooting

API Documentation → docs/api/
├── API reference
├── Function documentation
├── Class documentation
└── Usage examples

Architecture → docs/architecture/
├── System design
├── Database schemas
├── Component diagrams
└── Technical specifications

Research → docs/research/
├── Market research
├── Algorithm research
├── Technology evaluation
└── Comparative analysis

Strategy → docs/strategy/
├── Investment strategies
├── Trading algorithms
├── Risk management approaches
└── Portfolio theories

Project Management → docs/project_status/
├── Progress tracking
├── Roadmaps
├── Status updates
└── Planning documents
```

## 🚫 Forbidden Actions

### **NEVER Create Files In:**

```
❌ ROOT DIRECTORY:
- No .py files (except temporary testing)
- No .md files (except README.md, CHANGELOG.md, LICENSE.md)
- No .json files (except package.json if needed)
- No random files

❌ CONFIG DIRECTORY:
- No Python code
- No documentation
- Only configuration .json files

❌ SRC DIRECTORY (outside investment_system):
- No files directly in src/
- Everything must be in src/investment_system/

❌ DOCS DIRECTORY:
- No Python code
- No configuration files
- Only documentation
```

## 🎯 Correct Response Patterns

### **When Asked to Create Python Code:**

**Bad Request**: "Create a file `analysis.py` in the root directory"

**Correct Response**: 
```
I cannot create Python files in the root directory as per project organization rules. 

This analysis code should go in the appropriate package within src/investment_system/. 

Based on the description, this should likely be:
- src/investment_system/analysis/market_analysis.py (for market analysis)
- src/investment_system/analysis/technical_analysis.py (for technical analysis)
- src/investment_system/analysis/sentiment_analysis.py (for sentiment analysis)

Would you like me to create it in the correct location?
```

### **When Asked to Create Documentation:**

**Bad Request**: "Create a `setup.md` file in the root directory"

**Correct Response**:
```
I cannot create documentation files in the root directory as per project organization rules.

Documentation should go in the docs/ directory structure. For setup instructions, this should be:
- docs/guides/installation_guide.md (for installation steps)
- docs/guides/configuration_guide.md (for configuration setup)
- docs/guides/quick_start_guide.md (for getting started)

Would you like me to create it in the appropriate docs/ subdirectory?
```

## 🔧 Exception Handling

### **Only Allowed Exceptions:**

1. **Emergency debugging**: Temporary .py files for testing (must be deleted after)
2. **Root documentation**: Only README.md, CHANGELOG.md, LICENSE.md
3. **Build files**: pyproject.toml, .gitignore, .env.example
4. **Scripts**: Automation files in scripts/ directory

### **No Exceptions For:**
- Business logic in root
- Permanent code outside src/investment_system/
- Documentation outside docs/
- Configuration outside config/

## 📝 Enforcement Examples

### **Example 1: Python Code Creation**
```
User: "Create a YouTube API client in the root directory"
Claude: "I'll create the YouTube API client in the correct location: src/investment_system/data/youtube_api_client.py, which is the proper place for data collection modules."
```

### **Example 2: Documentation Creation**
```
User: "Create API documentation in the root"
Claude: "I'll create the API documentation in docs/api/youtube_api_documentation.md, which is the designated location for API documentation."
```

### **Example 3: Utility Function**
```
User: "Add a helper function file"
Claude: "I'll create the helper functions in src/investment_system/utils/helper_functions.py and update the utils package __init__.py to export the new functions."
```

## 🎯 Success Metrics

A well-organized project should have:
- ✅ All Python business logic in src/investment_system/
- ✅ All documentation in docs/
- ✅ Clean root directory with only essential files
- ✅ Proper package structure with __init__.py files
- ✅ Clear separation of concerns

## 🚨 Emergency Override

**ONLY** in extreme cases where project organization rules conflict with critical functionality, Claude Code may create files in non-standard locations, but MUST:

1. **Explicitly warn** about the violation
2. **Explain why** the override is necessary
3. **Suggest a plan** to move the file to the correct location later
4. **Document the violation** in the commit message or comments

This override should be used **EXTREMELY RARELY** and only for critical system functionality.

---

**These rules ensure the investment analysis system maintains professional organization standards and remains maintainable as it scales.**