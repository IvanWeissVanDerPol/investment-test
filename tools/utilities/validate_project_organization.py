"""
Project Organization Validator
Checks for violations of project organization rules and suggests fixes
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

def check_organization_rules(project_root: str = ".") -> Dict[str, List[str]]:
    """
    Check project for organization rule violations
    
    Returns:
        Dictionary with violation categories and lists of violations
    """
    project_path = Path(project_root)
    violations = {
        "python_files_in_wrong_location": [],
        "documentation_in_wrong_location": [],
        "files_in_root": [],
        "missing_init_files": [],
        "recommendations": []
    }
    
    # Check for Python files in wrong locations
    print("Checking Python file locations...")
    
    # Check root directory for Python files
    for file in project_path.glob("*.py"):
        if file.name not in ["setup.py"]:  # setup.py is allowed in root
            violations["python_files_in_wrong_location"].append(
                f"ERROR: {file} - Python files should be in src/investment_system/"
            )
    
    # Check for Python files in docs/
    docs_path = project_path / "docs"
    if docs_path.exists():
        for file in docs_path.rglob("*.py"):
            violations["python_files_in_wrong_location"].append(
                f"ERROR: {file} - Python files should not be in docs/"
            )
    
    # Check for Python files in config/
    config_path = project_path / "config"
    if config_path.exists():
        for file in config_path.glob("*.py"):
            violations["python_files_in_wrong_location"].append(
                f"ERROR: {file} - Python files should not be in config/ (move to src/investment_system/utils/)"
            )
    
    # Check for documentation files in wrong locations
    print("Checking documentation file locations...")
    
    # Check src/ for markdown files
    src_path = project_path / "src"
    if src_path.exists():
        for file in src_path.rglob("*.md"):
            violations["documentation_in_wrong_location"].append(
                f"ERROR: {file} - Documentation should be in docs/"
            )
    
    # Check config/ for markdown files
    if config_path.exists():
        for file in config_path.rglob("*.md"):
            if file.name != "README.md":  # README.md in config is acceptable
                violations["documentation_in_wrong_location"].append(
                    f"ERROR: {file} - Documentation should be in docs/"
                )
    
    # Check for excessive files in root directory
    print("Checking root directory cleanliness...")
    
    allowed_root_files = {
        # Essential project files
        "README.md", "CHANGELOG.md", "LICENSE.md", "LICENSE",
        # Configuration files
        "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
        ".gitignore", ".env.example", ".env.template",
        # IDE/Editor files
        ".vscode", ".idea", 
        # Git
        ".git",
        # Others that might be needed
        "Makefile", "docker-compose.yml", "Dockerfile"
    }
    
    allowed_root_extensions = {".md", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".ini"}
    
    for item in project_path.iterdir():
        if item.is_file():
            if (item.name not in allowed_root_files and 
                item.suffix not in allowed_root_extensions and
                not item.name.startswith(".")):
                violations["files_in_root"].append(
                    f"WARNING: {item.name} - Consider moving to appropriate subdirectory"
                )
        elif item.is_dir():
            # Check for unexpected directories in root
            expected_dirs = {
                "src", "docs", "tests", "config", "scripts", "data", 
                "reports", "cache", ".claude", ".git", ".vscode", 
                ".idea", "__pycache__", ".pytest_cache", "htmlcov"
            }
            if item.name not in expected_dirs:
                violations["files_in_root"].append(
                    f"WARNING: {item.name}/ - Unexpected directory in root"
                )
    
    # Check for missing __init__.py files in packages
    print("Checking package structure...")
    
    investment_system_path = project_path / "src" / "investment_system"
    if investment_system_path.exists():
        for subdir in investment_system_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("__"):
                init_file = subdir / "__init__.py"
                if not init_file.exists():
                    violations["missing_init_files"].append(
                        f"ERROR: Missing {init_file} - Package directory needs __init__.py"
                    )
    
    # Generate recommendations
    if violations["python_files_in_wrong_location"]:
        violations["recommendations"].append(
            "RECOMMENDATION: Move all Python business logic to src/investment_system/ packages"
        )
    
    if violations["documentation_in_wrong_location"]:
        violations["recommendations"].append(
            "RECOMMENDATION: Move all documentation to docs/ with appropriate subdirectories"
        )
    
    if violations["files_in_root"]:
        violations["recommendations"].append(
            "RECOMMENDATION: Clean up root directory - keep only essential project files"
        )
    
    if violations["missing_init_files"]:
        violations["recommendations"].append(
            "RECOMMENDATION: Add missing __init__.py files to make directories proper Python packages"
        )
    
    return violations

def print_violations_report(violations: Dict[str, List[str]]):
    """Print a formatted report of violations"""
    
    print("\n" + "="*80)
    print("PROJECT ORGANIZATION VALIDATION REPORT")
    print("="*80)
    
    total_violations = sum(len(v) for k, v in violations.items() if k != "recommendations")
    
    if total_violations == 0:
        print("SUCCESS: No organization rule violations found.")
        print("Project structure follows all organization rules.")
        return
    
    print(f"WARNING: Found {total_violations} organization violations")
    print()
    
    # Python file violations
    if violations["python_files_in_wrong_location"]:
        print("PYTHON FILE LOCATION VIOLATIONS:")
        for violation in violations["python_files_in_wrong_location"]:
            print(f"   {violation}")
        print()
    
    # Documentation violations
    if violations["documentation_in_wrong_location"]:
        print("DOCUMENTATION LOCATION VIOLATIONS:")
        for violation in violations["documentation_in_wrong_location"]:
            print(f"   {violation}")
        print()
    
    # Root directory violations
    if violations["files_in_root"]:
        print("ROOT DIRECTORY CLEANLINESS ISSUES:")
        for violation in violations["files_in_root"]:
            print(f"   {violation}")
        print()
    
    # Missing package files
    if violations["missing_init_files"]:
        print("MISSING PACKAGE FILES:")
        for violation in violations["missing_init_files"]:
            print(f"   {violation}")
        print()
    
    # Recommendations
    if violations["recommendations"]:
        print("RECOMMENDATIONS:")
        for recommendation in violations["recommendations"]:
            print(f"   {recommendation}")
        print()
    
    print("FIX THESE ISSUES TO MAINTAIN CLEAN PROJECT STRUCTURE")
    print("See .claude/rules/project_organization.md for detailed rules")

def suggest_fixes(violations: Dict[str, List[str]]):
    """Suggest specific fixes for violations"""
    
    if not any(violations.values()):
        return
    
    print("\n" + "="*80)
    print("SUGGESTED FIXES")
    print("="*80)
    
    # Python file fixes
    for violation in violations["python_files_in_wrong_location"]:
        if "config/" in violation and ".py" in violation:
            print("Move config/*.py files:")
            print("   mv config/*.py src/investment_system/utils/")
            print("   Update src/investment_system/utils/__init__.py imports")
            print()
    
    # Documentation fixes
    for violation in violations["documentation_in_wrong_location"]:
        if "src/" in violation and ".md" in violation:
            print("Move documentation files:")
            print("   mv src/**/*.md docs/appropriate_category/")
            print("   Choose: docs/api/, docs/guides/, docs/architecture/, etc.")
            print()
    
    # Package fixes
    if violations["missing_init_files"]:
        print("Add missing __init__.py files:")
        for violation in violations["missing_init_files"]:
            if "Missing" in violation:
                path = violation.split("Missing ")[1].split(" -")[0]
                print(f"   touch {path}")
        print()
    
    print("Run this script again after making fixes to verify compliance")

def main():
    """Main function to run organization validation"""
    
    print("Starting project organization validation...")
    print("Checking investment analysis system structure...")
    
    # Get project root (assuming script is in scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run validation
    violations = check_organization_rules(project_root)
    
    # Print report
    print_violations_report(violations)
    
    # Suggest fixes
    suggest_fixes(violations)
    
    # Exit with appropriate code
    total_violations = sum(len(v) for k, v in violations.items() if k != "recommendations")
    if total_violations > 0:
        print(f"\nValidation failed with {total_violations} violations")
        sys.exit(1)
    else:
        print(f"\nValidation passed - project structure is clean!")
        sys.exit(0)

if __name__ == "__main__":
    main()