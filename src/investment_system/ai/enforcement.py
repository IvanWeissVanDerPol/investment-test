"""
Conditional enforcement for AI safety checks.
Only runs expensive checks when meaningful risk exists.
"""

import os
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import json


class ConditionalEnforcer:
    """Manages conditional enforcement of AI safety checks."""
    
    def __init__(self, policy_path: str = "src/investment_system/ai/policy.yaml"):
        """
        Initialize enforcer with policy.
        
        Args:
            policy_path: Path to policy YAML file
        """
        self.policy = self._load_policy(policy_path)
        self.enforcement_history = []
        self.last_full_check = None
    
    def _load_policy(self, policy_path: str) -> Dict[str, Any]:
        """Load enforcement policy from YAML."""
        with open(policy_path, "r") as f:
            return yaml.safe_load(f)
    
    def should_enforce(
        self,
        changed_files: List[str],
        commit_message: str = "",
        force: bool = False
    ) -> tuple[bool, str]:
        """
        Determine if enforcement should run.
        
        Args:
            changed_files: List of changed file paths
            commit_message: Git commit message
            force: Force enforcement regardless of policy
            
        Returns:
            Tuple of (should_enforce, reason)
        """
        enforcement_config = self.policy["enforcement"]
        
        # Check if enforcement is disabled
        if enforcement_config["mode"] == "off":
            return False, "Enforcement disabled"
        
        # Force enforcement if requested
        if force or enforcement_config["mode"] == "full":
            return True, "Forced enforcement"
        
        # Check commit message overrides
        overrides = enforcement_config["overrides"]
        if any(tag in commit_message for tag in overrides["commit_tags_full"]):
            return True, f"Commit tag override: full enforcement"
        if any(tag in commit_message for tag in overrides["commit_tags_skip"]):
            return False, f"Commit tag override: skip enforcement"
        
        # Check scheduled backstop
        backstop_days = enforcement_config.get("schedule_backstop_days", 7)
        if self.last_full_check:
            days_since = (datetime.now() - self.last_full_check).days
            if days_since >= backstop_days:
                return True, f"Scheduled backstop ({backstop_days} days)"
        
        # Check path triggers
        trigger_paths = enforcement_config["triggers"]["paths"]
        for file in changed_files:
            for trigger_path in trigger_paths:
                if trigger_path.endswith("/**"):
                    # Directory wildcard
                    if file.startswith(trigger_path[:-3]):
                        return True, f"Critical path changed: {file}"
                elif file == trigger_path or file.endswith(trigger_path):
                    return True, f"Critical file changed: {file}"
        
        # Check LOC delta
        loc_delta = self._calculate_loc_delta(changed_files)
        max_loc = enforcement_config["triggers"]["max_loc_delta"]
        if loc_delta > max_loc:
            return True, f"Large change: {loc_delta} lines (> {max_loc})"
        
        # Check for schema changes
        if enforcement_config["triggers"]["schema_changed"]:
            if self._has_schema_changes(changed_files):
                return True, "Schema/contract changes detected"
        
        # Check for endpoint catalog changes
        if enforcement_config["triggers"]["endpoint_catalog_changed"]:
            if any("endpoints.yaml" in f for f in changed_files):
                return True, "Endpoint catalog changed"
        
        return False, "No enforcement triggers met"
    
    def _calculate_loc_delta(self, changed_files: List[str]) -> int:
        """Calculate lines of code changed."""
        try:
            # Use git diff to get LOC changes
            result = subprocess.run(
                ["git", "diff", "--shortstat", "HEAD~1"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Parse output like "2 files changed, 10 insertions(+), 5 deletions(-)"
                parts = result.stdout.split(",")
                total = 0
                for part in parts:
                    numbers = [int(s) for s in part.split() if s.isdigit()]
                    total += sum(numbers)
                return total
        except:
            pass
        
        # Fallback: count lines in changed files
        total_lines = 0
        for file in changed_files:
            if Path(file).exists() and file.endswith(".py"):
                try:
                    with open(file, "r") as f:
                        total_lines += len(f.readlines())
                except:
                    pass
        
        return total_lines
    
    def _has_schema_changes(self, changed_files: List[str]) -> bool:
        """Check if any schema/contract files changed."""
        schema_patterns = [
            "contracts.py",
            "models.py",
            "schema.py",
            "database.py"
        ]
        
        for file in changed_files:
            for pattern in schema_patterns:
                if pattern in file:
                    return True
        return False
    
    def run_enforcement(self) -> Dict[str, Any]:
        """
        Run full enforcement checks.
        
        Returns:
            Enforcement results
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "passed": True,
            "errors": []
        }
        
        # Run Sonar diff check
        try:
            sonar_result = self._run_sonar_diff()
            results["checks"]["sonar_diff"] = sonar_result
            if not sonar_result["passed"]:
                results["passed"] = False
        except Exception as e:
            results["errors"].append(f"Sonar diff failed: {e}")
        
        # Run endpoint catalog validation
        try:
            catalog_result = self._validate_endpoint_catalog()
            results["checks"]["endpoint_catalog"] = catalog_result
            if not catalog_result["passed"]:
                results["passed"] = False
        except Exception as e:
            results["errors"].append(f"Endpoint catalog validation failed: {e}")
        
        # Run contract validation
        try:
            contract_result = self._validate_contracts()
            results["checks"]["contracts"] = contract_result
            if not contract_result["passed"]:
                results["passed"] = False
        except Exception as e:
            results["errors"].append(f"Contract validation failed: {e}")
        
        # Run security scans
        try:
            security_result = self._run_security_scans()
            results["checks"]["security"] = security_result
            if not security_result["passed"]:
                results["passed"] = False
        except Exception as e:
            results["errors"].append(f"Security scan failed: {e}")
        
        # Update last check time
        self.last_full_check = datetime.now()
        self.enforcement_history.append(results)
        
        return results
    
    def _run_sonar_diff(self) -> Dict[str, Any]:
        """Run Sonar core delta check."""
        from investment_system.sonar.indexer import SonarIndexer
        
        # Build current graph
        indexer = SonarIndexer()
        current_graph = indexer.index()
        
        # Load previous graph if exists
        old_graph_path = Path("sonar/store/graph.json")
        if old_graph_path.exists():
            old_graph = indexer.load(str(old_graph_path))
            
            # Calculate core delta
            core_delta = self._calculate_core_delta(old_graph, current_graph)
            
            # Check against epsilon
            eps = self.policy["enforcement"]["triggers"]["core_delta_eps"]
            passed = abs(core_delta) <= eps
            
            return {
                "passed": passed,
                "core_delta": core_delta,
                "threshold": eps
            }
        
        return {"passed": True, "message": "No previous graph to compare"}
    
    def _calculate_core_delta(self, old_graph, new_graph) -> float:
        """Calculate change in core node importance."""
        # Simple heuristic: ratio of changed core files
        old_core = set(n for n in old_graph.nodes if "core/" in n)
        new_core = set(n for n in new_graph.nodes if "core/" in n)
        
        if not old_core:
            return 0.0
        
        changed = old_core.symmetric_difference(new_core)
        return len(changed) / len(old_core)
    
    def _validate_endpoint_catalog(self) -> Dict[str, Any]:
        """Validate endpoint catalog consistency."""
        from investment_system.api.router import EndpointCatalog
        
        try:
            catalog = EndpointCatalog()
            
            # Check for duplicate IDs
            ids = [s["id"] for s in catalog.endpoints["services"]]
            duplicates = [id for id in ids if ids.count(id) > 1]
            
            # Check for path conflicts
            paths = {}
            conflicts = []
            for service in catalog.endpoints["services"]:
                key = (service["method"], service["path"])
                if key in paths:
                    conflicts.append(f"{service['method']} {service['path']}")
                paths[key] = service["id"]
            
            passed = len(duplicates) == 0 and len(conflicts) == 0
            
            return {
                "passed": passed,
                "duplicate_ids": duplicates,
                "path_conflicts": conflicts
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def _validate_contracts(self) -> Dict[str, Any]:
        """Validate Pydantic contracts."""
        try:
            # Import all contract models to check for errors
            from investment_system.core import contracts
            
            # Check that all models can be instantiated
            test_models = [
                contracts.User,
                contracts.TradingSignal,
                contracts.MarketData,
                contracts.SignalRequest
            ]
            
            for model in test_models:
                # Try to get schema (will fail if model is invalid)
                schema = model.schema()
            
            return {"passed": True, "models_validated": len(test_models)}
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def _run_security_scans(self) -> Dict[str, Any]:
        """Run basic security scans."""
        from investment_system.sonar.security import ai_security_guard
        
        # Check for blocked attempts
        security_report = ai_security_guard.get_security_report()
        
        # Check for secrets in code
        secrets_found = self._scan_for_secrets()
        
        passed = security_report["blocked_attempts"] == 0 and len(secrets_found) == 0
        
        return {
            "passed": passed,
            "blocked_attempts": security_report["blocked_attempts"],
            "secrets_found": len(secrets_found)
        }
    
    def _scan_for_secrets(self) -> List[str]:
        """Scan for hardcoded secrets."""
        import re
        
        secret_patterns = [
            r'api[_-]?key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
            r'secret[_-]?key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']'
        ]
        
        secrets = []
        for py_file in Path("src").rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        secrets.append(str(py_file))
                        break
            except:
                pass
        
        return secrets


# Global enforcer instance
_enforcer: Optional[ConditionalEnforcer] = None


def get_enforcer() -> ConditionalEnforcer:
    """Get global enforcer instance."""
    global _enforcer
    if _enforcer is None:
        _enforcer = ConditionalEnforcer()
    return _enforcer