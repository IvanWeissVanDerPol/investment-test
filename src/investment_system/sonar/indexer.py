"""
Sonar Indexer - Builds dependency graph of codebase for AI context optimization.
Identifies file interdependencies and core logic to minimize LLM token usage.
"""

import ast
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
from investment_system.core.logging import get_logger
from investment_system.core.monitoring import track_custom_metric, increment_counter

logger = get_logger(__name__)


class SonarGraph:
    """Graph structure for code dependencies."""
    
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[tuple[str, str, str]] = []
        self.metadata: Dict[str, Any] = {
            "indexed_at": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        # Track SONAR metrics
        track_custom_metric("sonar_graph_initialized", datetime.utcnow().isoformat())
    
    def add_node(self, node_id: str, kind: str, meta: Dict[str, Any]):
        """Add node to graph."""
        self.nodes[node_id] = {"kind": kind, **meta}
        increment_counter(f"sonar_nodes_{kind}")
        logger.debug("Added SONAR node", node_id=node_id, kind=kind)
    
    def add_edge(self, src: str, dst: str, edge_type: str):
        """Add edge between nodes."""
        self.edges.append((src, dst, edge_type))
        increment_counter(f"sonar_edges_{edge_type}")
        logger.debug("Added SONAR edge", src=src, dst=dst, edge_type=edge_type)
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """Get all dependencies of a node."""
        return [dst for src, dst, _ in self.edges if src == node_id]
    
    def get_dependents(self, node_id: str) -> List[str]:
        """Get all nodes that depend on this node."""
        return [src for src, dst, _ in self.edges if dst == node_id]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary."""
        result = {
            "nodes": self.nodes,
            "edges": [{"src": s, "dst": d, "type": t} for s, d, t in self.edges],
            "metadata": self.metadata
        }
        # Update metrics
        track_custom_metric("sonar_total_nodes", len(self.nodes))
        track_custom_metric("sonar_total_edges", len(self.edges))
        logger.info("SONAR graph serialized", nodes=len(self.nodes), edges=len(self.edges))
        return result


class PythonAnalyzer:
    """Analyzes Python files for dependencies and structure."""
    
    def __init__(self):
        self.imports: Set[str] = set()
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.constants: List[str] = []
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze Python file for structure and dependencies.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Analysis results
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.imports.add(node.module)
                elif isinstance(node, ast.FunctionDef):
                    self.functions.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    })
                elif isinstance(node, ast.ClassDef):
                    self.classes.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "bases": [self._get_name(base) for base in node.bases],
                        "methods": self._get_class_methods(node)
                    })
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            self.constants.append(target.id)
            
            return {
                "imports": list(self.imports),
                "functions": self.functions,
                "classes": self.classes,
                "constants": self.constants,
                "lines": len(content.splitlines()),
                "has_main": "__main__" in content
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return "unknown"
    
    def _get_name(self, node) -> str:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"
    
    def _get_class_methods(self, class_node: ast.ClassDef) -> List[str]:
        """Extract method names from class."""
        methods = []
        for node in class_node.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(node.name)
        return methods


class SonarIndexer:
    """Main indexer for building code dependency graph."""
    
    def __init__(self, root_path: str = ".", policy_path: Optional[str] = None):
        """
        Initialize indexer.
        
        Args:
            root_path: Root directory to index
            policy_path: Path to policy.yaml file
        """
        self.root = Path(root_path)
        self.graph = SonarGraph()
        self.policy = self._load_policy(policy_path)
        self.analyzer = PythonAnalyzer()
    
    def _load_policy(self, policy_path: Optional[str]) -> Dict[str, Any]:
        """Load indexing policy."""
        if not policy_path:
            # Default policy
            return {
                "allow_dirs": ["src", "tests"],
                "ignore_dirs": ["__pycache__", ".git", "venv", "env", "runtime"],
                "ignore_files": ["*.pyc", "*.pyo", "__pycache__"],
                "max_file_size": 1024 * 1024,  # 1MB
                "scan_imports": True,
                "scan_secrets": True
            }
        
        import yaml
        with open(policy_path, "r") as f:
            return yaml.safe_load(f)
    
    def _should_index_file(self, file_path: Path) -> bool:
        """Check if file should be indexed based on policy."""
        # Check if in allowed directories
        relative_path = file_path.relative_to(self.root)
        path_parts = relative_path.parts
        
        # Check ignored directories
        for ignored in self.policy.get("ignore_dirs", []):
            if ignored in path_parts:
                return False
        
        # Check allowed directories
        allow_dirs = self.policy.get("allow_dirs", [])
        if allow_dirs:
            if not any(str(relative_path).startswith(d) for d in allow_dirs):
                return False
        
        # Check file size
        max_size = self.policy.get("max_file_size", 1024 * 1024)
        if file_path.stat().st_size > max_size:
            return False
        
        return True
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()
    
    def _detect_secrets(self, content: str) -> List[str]:
        """Detect potential secrets in code."""
        import re
        
        patterns = [
            r'api[_-]?key\s*=\s*["\'][\w\-]+["\']',
            r'secret[_-]?key\s*=\s*["\'][\w\-]+["\']',
            r'password\s*=\s*["\'][\w\-]+["\']',
            r'token\s*=\s*["\'][\w\-]+["\']',
            r'AWS[_-]?ACCESS[_-]?KEY[_-]?ID\s*=\s*["\'][\w\-]+["\']',
            r'JWT[_-]?SECRET\s*=\s*["\'][\w\-]+["\']'
        ]
        
        secrets = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            secrets.extend(matches)
        
        return secrets
    
    def index(self) -> SonarGraph:
        """
        Index the codebase and build dependency graph.
        
        Returns:
            Dependency graph
        """
        # Index Python files
        for py_file in self.root.rglob("*.py"):
            if not self._should_index_file(py_file):
                continue
            
            file_id = str(py_file.relative_to(self.root))
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(py_file)
            
            # Analyze file structure
            analysis = self.analyzer.analyze_file(py_file)
            
            # Check for secrets if enabled
            secrets = []
            if self.policy.get("scan_secrets", True):
                content = py_file.read_text(encoding="utf-8")
                secrets = self._detect_secrets(content)
            
            # Add file node
            self.graph.add_node(
                file_id,
                "file",
                {
                    "hash": file_hash,
                    "size": py_file.stat().st_size,
                    "modified": py_file.stat().st_mtime,
                    "analysis": analysis,
                    "has_secrets": len(secrets) > 0,
                    "secrets_count": len(secrets)
                }
            )
            
            # Add import edges
            if self.policy.get("scan_imports", True):
                for import_name in analysis.get("imports", []):
                    # Try to resolve import to file
                    import_file = self._resolve_import(import_name)
                    if import_file:
                        self.graph.add_edge(file_id, import_file, "imports")
        
        # Index configuration files
        for config_pattern in ["*.yaml", "*.yml", "*.json", "*.ini", "*.toml"]:
            for config_file in self.root.rglob(config_pattern):
                if not self._should_index_file(config_file):
                    continue
                
                file_id = str(config_file.relative_to(self.root))
                self.graph.add_node(
                    file_id,
                    "config",
                    {
                        "hash": self._calculate_file_hash(config_file),
                        "size": config_file.stat().st_size,
                        "modified": config_file.stat().st_mtime
                    }
                )
        
        return self.graph
    
    def _resolve_import(self, import_name: str) -> Optional[str]:
        """Try to resolve import to a file in the project."""
        # Convert import to potential file path
        parts = import_name.split(".")
        
        # Try different combinations
        potential_paths = [
            Path("src") / Path(*parts) / "__init__.py",
            Path("src") / f"{'/'.join(parts)}.py",
            Path(*parts) / "__init__.py",
            Path(f"{'/'.join(parts)}.py")
        ]
        
        for path in potential_paths:
            full_path = self.root / path
            if full_path.exists():
                return str(path)
        
        return None
    
    def save(self, output_path: str = "sonar/store/graph.json"):
        """
        Save graph to file.
        
        Args:
            output_path: Output file path
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, "w") as f:
            json.dump(self.graph.to_dict(), f, indent=2)
    
    def load(self, input_path: str = "sonar/store/graph.json") -> SonarGraph:
        """
        Load graph from file.
        
        Args:
            input_path: Input file path
            
        Returns:
            Loaded graph
        """
        with open(input_path, "r") as f:
            data = json.load(f)
        
        graph = SonarGraph()
        graph.nodes = data["nodes"]
        graph.edges = [(e["src"], e["dst"], e["type"]) for e in data["edges"]]
        graph.metadata = data["metadata"]
        
        return graph


if __name__ == "__main__":
    # Example usage
    indexer = SonarIndexer()
    graph = indexer.index()
    indexer.save()
    print(f"Indexed {len(graph.nodes)} files with {len(graph.edges)} dependencies")