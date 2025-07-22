#!/usr/bin/env python3
"""
Web Development MCP Server
Enforces clean code rules and provides web development utilities
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
import re

class WebDevMCPServer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.web_dir = self.project_root / "web"
        self.rules_dir = self.project_root / ".claude" / "mcp_rules"
    
    def validate_file_creation(self, filepath, content):
        """Validate file meets clean code standards"""
        filepath = Path(filepath)
        
        violations = []
        
        # Check for empty files
        if not content or content.strip() == "":
            violations.append("File is empty")
        
        # Check for TODO placeholders
        if "TODO" in content.upper() or "FIXME" in content.upper():
            violations.append("Contains TODO/FIXME placeholders")
        
        # Check for meaningful content
        if len(content.strip()) < 10:
            violations.append("Content too minimal")
        
        # Check for empty functions/classes
        if re.search(r'def\s+\w+\s*\(\s*\):\s*pass', content):
            violations.append("Contains empty functions")
        
        if re.search(r'class\s+\w+\s*:?\s*pass', content):
            violations.append("Contains empty classes")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "content_length": len(content),
            "filepath": str(filepath)
        }
    
    def check_naming_convention(self, filename, file_type):
        """Check file naming conventions"""
        conventions = {
            "html": r"^[a-z0-9_]+\.html$",
            "css": r"^[a-z0-9-]+\.css$",
            "js": r"^[a-zA-Z][a-zA-Z0-9]*\.js$",
            "py": r"^[a-z_]+\.py$"
        }
        
        pattern = conventions.get(file_type, r".*")
        return {
            "conforms": bool(re.match(pattern, filename)),
            "expected_pattern": pattern,
            "filename": filename
        }
    
    def scan_web_structure(self):
        """Scan web directory structure"""
        structure = {}
        
        if not self.web_dir.exists():
            return {"error": "Web directory not found"}
        
        for root, dirs, files in os.walk(self.web_dir):
            rel_path = Path(root).relative_to(self.web_dir)
            structure[str(rel_path)] = {
                "directories": dirs,
                "files": files,
                "file_count": len(files)
            }
        
        return structure
    
    def validate_html_template(self, template_path):
        """Validate HTML template structure"""
        if not Path(template_path).exists():
            return {"error": "Template not found"}
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        issues = []
        
        # Check for required HTML structure
        if "<!DOCTYPE html>" not in content:
            issues.append("Missing DOCTYPE declaration")
        
        if "<html>" not in content.lower():
            issues.append("Missing html tag")
        
        if "<head>" not in content.lower():
            issues.append("Missing head section")
        
        if "<body>" not in content.lower():
            issues.append("Missing body section")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "template_path": str(template_path)
        }
    
    def check_security_headers(self, endpoint_path):
        """Check security configurations"""
        security_checks = {
            "cors_configured": False,
            "input_validation": False,
            "sql_injection_protection": False,
            "xss_protection": False
        }
        
        # Simulate security checks
        endpoint_file = self.web_dir / "api" / f"{endpoint_path}.py"
        
        if endpoint_file.exists():
            with open(endpoint_file, 'r') as f:
                content = f.read()
            
            security_checks["cors_configured"] = "CORS" in content
            security_checks["input_validation"] = "validate" in content.lower()
            security_checks["sql_injection_protection"] = "parameterized" in content.lower()
            security_checks["xss_protection"] = "escape" in content.lower()
        
        return security_checks
    
    def generate_api_structure(self, resource_name):
        """Generate API endpoint structure"""
        return {
            "endpoints": {
                f"GET /api/{resource_name}": f"Get all {resource_name}",
                f"GET /api/{resource_name}/<id>": f"Get specific {resource_name}",
                f"POST /api/{resource_name}": f"Create new {resource_name}",
                f"PUT /api/{resource_name}/<id>": f"Update {resource_name}",
                f"DELETE /api/{resource_name}/<id>": f"Delete {resource_name}"
            },
            "file_structure": {
                "template": f"web/templates/{resource_name}.html",
                "api_endpoint": f"web/api/{resource_name}.py",
                "js_file": f"web/static/js/{resource_name}.js",
                "css_file": f"web/static/css/{resource_name}.css"
            }
        }
    
    def optimize_database_queries(self, query_type):
        """Provide optimization suggestions"""
        optimizations = {
            "portfolio": [
                "Add index on securities.symbol",
                "Use connection pooling",
                "Implement query caching"
            ],
            "analysis": [
                "Batch queries instead of N+1",
                "Use materialized views",
                "Implement pagination"
            ],
            "market_data": [
                "Cache frequent queries",
                "Use prepared statements",
                "Implement rate limiting"
            ]
        }
        
        return {
            "query_type": query_type,
            "optimizations": optimizations.get(query_type, ["Review query structure"])
        }
    
    def run_linting(self, filepath):
        """Run linting on Python files"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            return {"error": "File not found"}
        
        if filepath.suffix != ".py":
            return {"error": "Only Python files supported"}
        
        try:
            # Run flake8 or pylint
            result = subprocess.run([
                "python", "-m", "flake8", str(filepath),
                "--max-line-length", "88",
                "--select", "E,W,F"
            ], capture_output=True, text=True)
            
            return {
                "file": str(filepath),
                "has_issues": result.returncode != 0,
                "output": result.stdout,
                "error_output": result.stderr
            }
        except Exception as e:
            return {"error": str(e)}
    
    def check_performance_bottlenecks(self):
        """Check for common performance issues"""
        issues = []
        
        # Check for large files
        for root, dirs, files in os.walk(self.web_dir):
            for file in files:
                filepath = Path(root) / file
                if filepath.stat().st_size > 1024 * 1024:  # 1MB
                    issues.append(f"Large file: {filepath} ({filepath.stat().st_size} bytes)")
        
        # Check for missing optimizations
        static_dir = self.web_dir / "static"
        if static_dir.exists():
            css_files = list(static_dir.glob("**/*.css"))
            js_files = list(static_dir.glob("**/*.js"))
            
            if css_files and not any("min.css" in str(f) for f in css_files):
                issues.append("CSS files not minified")
            
            if js_files and not any("min.js" in str(f) for f in js_files):
                issues.append("JS files not minified")
        
        return {
            "performance_issues": issues,
            "recommendations": [
                "Minify CSS and JavaScript files",
                "Compress images",
                "Enable gzip compression",
                "Use CDN for static assets"
            ]
        }

# CLI interface
if __name__ == "__main__":
    import sys
    
    server = WebDevMCPServer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            filepath = sys.argv[2] if len(sys.argv) > 2 else ""
            content = sys.argv[3] if len(sys.argv) > 3 else ""
            print(json.dumps(server.validate_file_creation(filepath, content), indent=2))
        
        elif command == "structure":
            print(json.dumps(server.scan_web_structure(), indent=2))
        
        elif command == "api":
            resource = sys.argv[2] if len(sys.argv) > 2 else "portfolio"
            print(json.dumps(server.generate_api_structure(resource), indent=2))
        
        elif command == "security":
            endpoint = sys.argv[2] if len(sys.argv) > 2 else "portfolio"
            print(json.dumps(server.check_security_headers(endpoint), indent=2))
        
        elif command == "optimize":
            query_type = sys.argv[2] if len(sys.argv) > 2 else "portfolio"
            print(json.dumps(server.optimize_database_queries(query_type), indent=2))
        
        elif command == "performance":
            print(json.dumps(server.check_performance_bottlenecks(), indent=2))
        
        elif command == "lint":
            filepath = sys.argv[2] if len(sys.argv) > 2 else ""
            print(json.dumps(server.run_linting(filepath), indent=2))
        
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
    else:
        print(json.dumps({
            "available_commands": [
                "validate", "structure", "api", "security", 
                "optimize", "performance", "lint"
            ]
        }, indent=2))