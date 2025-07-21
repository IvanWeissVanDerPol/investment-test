# QUICK ORGANIZATION RULES

## 🚨 IMMEDIATE ENFORCEMENT

### **Python Code (.py files):**
- ✅ **ONLY** in `src/investment_system/`
- ❌ **NEVER** in root directory
- ❌ **NEVER** in docs/, config/, or other directories

### **Documentation (.md files):**
- ✅ **ONLY** in `docs/`
- ❌ **NEVER** in src/, config/, or other directories
- ❌ **NEVER** random .md files in root (except README.md, CHANGELOG.md, LICENSE.md)

## 📁 WHERE TO PUT NEW FILES

```
Python Code → src/investment_system/[module]/
Documentation → docs/[category]/
Tests → tests/
Config → config/
Data → data/
Scripts → scripts/
```

## 🚫 REFUSE THESE REQUESTS

- "Create `analysis.py` in root"
- "Add `setup.md` to root" 
- "Put Python code in docs/"
- "Add .md files to src/"

## ✅ SUGGEST INSTEAD

```
"I'll create that in the correct location:
- Python code → src/investment_system/[appropriate_package]/
- Documentation → docs/[appropriate_category]/
```

## 🎯 KEEP ROOT CLEAN

**Root should ONLY have:**
- README.md, CHANGELOG.md, LICENSE.md
- pyproject.toml, .gitignore, .env.example
- Directory folders (src/, docs/, tests/, config/, etc.)

**NO random files in root!**