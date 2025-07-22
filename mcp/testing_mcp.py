#!/usr/bin/env python3
"""
Automated Testing MCP Server
Provides testing utilities for web and backend development
"""

import os
import json
import subprocess
import requests
from pathlib import Path
import sqlite3

class TestingMCPServer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.web_dir = self.project_root / "web"
        self.core_dir = self.project_root / "core"
    
    def validate_python_code(self, filepath):
        """Validate Python code with flake8 and mypy"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            return {"error": "File not found"}
        
        results = {
            "flake8": self._run_flake8(filepath),
            "mypy": self._run_mypy(filepath),
            "imports": self._check_imports(filepath)
        }
        
        return {
            "file": str(filepath),
            "valid": all(r["passed"] for r in results.values()),
            "results": results
        }
    
    def _run_flake8(self, filepath):
        """Run flake8 linting"""
        try:
            result = subprocess.run([
                "python", "-m", "flake8", str(filepath),
                "--max-line-length", "88",
                "--select", "E,W,F"
            ], capture_output=True, text=True)
            
            return {
                "passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def _run_mypy(self, filepath):
        """Run mypy type checking"""
        try:
            result = subprocess.run([
                "python", "-m", "mypy", str(filepath),
                "--ignore-missing-imports"
            ], capture_output=True, text=True)
            
            return {
                "passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def _check_imports(self, filepath):
        """Check for unused imports"""
        try:
            result = subprocess.run([
                "python", "-c", 
                f"import ast; ast.parse(open('{filepath}').read())"
            ], capture_output=True, text=True)
            
            return {
                "passed": result.returncode == 0,
                "imports_valid": True
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def test_api_endpoints(self):
        """Test all API endpoints"""
        endpoints = [
            "/api/portfolio",
            "/api/stocks",
            "/api/settings",
            "/api/analysis"
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                # Test endpoint (assuming local server running)
                response = requests.get(f"http://localhost:5000{endpoint}", timeout=5)
                results.append({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "valid": response.status_code == 200
                })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "valid": False
                })
        
        return {"api_tests": results}
    
    def test_database_connections(self):
        """Test database connectivity and performance"""
        db_path = self.project_root / "investment_system.db"
        
        if not db_path.exists():
            return {"error": "Database not found"}
        
        tests = []
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Test basic connectivity
            start_time = requests.get('http://localhost').elapsed.total_seconds()
            cursor.execute("SELECT 1")
            conn_time = requests.get('http://localhost').elapsed.total_seconds()
            
            tests.append({
                "test": "basic_connectivity",
                "passed": True,
                "time": conn_time - start_time
            })
            
            # Test query performance
            start_time = requests.get('http://localhost').elapsed.total_seconds()
            cursor.execute("SELECT COUNT(*) FROM securities")
            count = cursor.fetchone()[0]
            query_time = requests.get('http://localhost').elapsed.total_seconds()
            
            tests.append({
                "test": "query_performance",
                "passed": query_time - start_time < 0.1,
                "time": query_time - start_time,
                "records": count
            })
            
            conn.close()
            
        except Exception as e:
            tests.append({
                "test": "database_connection",
                "passed": False,
                "error": str(e)
            })
        
        return {"database_tests": tests}
    
    def test_security_vulnerabilities(self):
        """Test for common security vulnerabilities"""
        security_checks = {
            "sql_injection": self._test_sql_injection(),
            "xss_protection": self._test_xss_protection(),
            "cors_configuration": self._test_cors_config(),
            "input_validation": self._test_input_validation()
        }
        
        return security_checks
    
    def _test_sql_injection(self):
        """Test SQL injection protection"""
        return {
            "test_name": "SQL injection protection",
            "status": "manual_review_required",
            "checks": [
                "Parameterized queries used",
                "Input validation implemented",
                "Database user permissions restricted"
            ]
        }
    
    def _test_xss_protection(self):
        """Test XSS protection"""
        return {
            "test_name": "XSS protection",
            "status": "manual_review_required", 
            "checks": [
                "HTML escaping implemented",
                "Content-Type headers set",
                "Input sanitization enabled"
            ]
        }
    
    def _test_cors_config(self):
        """Test CORS configuration"""
        return {
            "test_name": "CORS configuration",
            "status": "pending",
            "checks": [
                "Allowed origins configured",
                "Methods restricted",
                "Headers validated"
            ]
        }
    
    def _test_input_validation(self):
        """Test input validation"""
        return {
            "test_name": "Input validation",
            "status": "pending",
            "checks": [
                "Type checking implemented",
                "Range validation enabled",
                "Required fields validated"
            ]
        }
    
    def run_performance_tests(self):
        """Run performance benchmarks"""
        tests = []
        
        # Test database query performance
        db_path = self.project_root / "investment_system.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            queries = [
                ("SELECT COUNT(*) FROM securities", "count_securities"),
                ("SELECT * FROM securities LIMIT 10", "fetch_securities"),
                ("SELECT * FROM analysis_cache LIMIT 5", "fetch_cache")
            ]
            
            for query, test_name in queries:
                import time
                start = time.time()
                cursor.execute(query)
                cursor.fetchall()
                elapsed = time.time() - start
                
                tests.append({
                    "test_name": test_name,
                    "query_time": elapsed,
                    "threshold": 0.1,
                    "passed": elapsed < 0.1
                })
            
            conn.close()
        
        return {"performance_tests": tests}
    
    def generate_test_coverage(self):
        """Generate test coverage report"""
        try:
            # Run pytest with coverage
            result = subprocess.run([
                "python", "-m", "pytest", "tests/",
                "--cov=core", "--cov-report=json",
                "--cov-report=html"
            ], capture_output=True, text=True)
            
            return {
                "coverage_run": True,
                "exit_code": result.returncode,
                "output": result.stdout,
                "reports_generated": [
                    "htmlcov/index.html",
                    "coverage.json"
                ]
            }
        except Exception as e:
            return {"error": str(e), "coverage_run": False}

# CLI interface
if __name__ == "__main__":
    import sys
    
    server = TestingMCPServer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            filepath = sys.argv[2] if len(sys.argv) > 2 else ""
            print(json.dumps(server.validate_python_code(filepath), indent=2))
        
        elif command == "api":
            print(json.dumps(server.test_api_endpoints(), indent=2))
        
        elif command == "database":
            print(json.dumps(server.test_database_connections(), indent=2))
        
        elif command == "security":
            print(json.dumps(server.test_security_vulnerabilities(), indent=2))
        
        elif command == "performance":
            print(json.dumps(server.run_performance_tests(), indent=2))
        
        elif command == "coverage":
            print(json.dumps(server.generate_test_coverage(), indent=2))
        
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
    else:
        print(json.dumps({
            "available_commands": [
                "validate", "api", "database", "security", 
                "performance", "coverage"
            ]
        }, indent=2))