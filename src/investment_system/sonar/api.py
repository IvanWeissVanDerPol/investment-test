"""
Sonar API - Provides context slicing for AI agents to minimize token usage.
Read-only interface to code dependency graph.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from investment_system.sonar.indexer import SonarGraph, SonarIndexer


class SonarAPI:
    """API for querying code dependency graph."""
    
    def __init__(self, graph_path: str = "sonar/store/graph.json"):
        """
        Initialize Sonar API.
        
        Args:
            graph_path: Path to stored graph
        """
        self.graph_path = Path(graph_path)
        self.graph: Optional[SonarGraph] = None
        self._load_graph()
    
    def _load_graph(self):
        """Load graph from storage."""
        if self.graph_path.exists():
            indexer = SonarIndexer()
            self.graph = indexer.load(str(self.graph_path))
        else:
            # Build graph if not exists
            indexer = SonarIndexer()
            self.graph = indexer.index()
            indexer.save(str(self.graph_path))
    
    def refresh_index(self) -> Dict[str, Any]:
        """
        Refresh the code index.
        
        Returns:
            Index statistics
        """
        indexer = SonarIndexer()
        self.graph = indexer.index()
        indexer.save(str(self.graph_path))
        
        return {
            "status": "refreshed",
            "files": len(self.graph.nodes),
            "dependencies": len(self.graph.edges),
            "indexed_at": datetime.utcnow().isoformat()
        }
    
    def get_file_context(
        self,
        file_path: str,
        depth: int = 1,
        include_dependencies: bool = True,
        include_dependents: bool = False
    ) -> Dict[str, Any]:
        """
        Get context for a specific file.
        
        Args:
            file_path: Path to file
            depth: Dependency depth to include
            include_dependencies: Include files this file imports
            include_dependents: Include files that import this file
            
        Returns:
            File context with dependencies
        """
        if not self.graph:
            return {"error": "Graph not loaded"}
        
        if file_path not in self.graph.nodes:
            return {"error": f"File not found: {file_path}"}
        
        context = {
            "file": file_path,
            "metadata": self.graph.nodes[file_path],
            "dependencies": [],
            "dependents": []
        }
        
        visited = set()
        
        if include_dependencies:
            deps = self._get_dependencies_recursive(file_path, depth, visited)
            context["dependencies"] = deps
        
        if include_dependents:
            deps = self._get_dependents_recursive(file_path, depth, visited)
            context["dependents"] = deps
        
        return context
    
    def _get_dependencies_recursive(
        self,
        file_path: str,
        depth: int,
        visited: Set[str]
    ) -> List[Dict[str, Any]]:
        """Get dependencies recursively up to depth."""
        if depth <= 0 or file_path in visited:
            return []
        
        visited.add(file_path)
        dependencies = []
        
        for src, dst, edge_type in self.graph.edges:
            if src == file_path and dst not in visited:
                dep_info = {
                    "file": dst,
                    "type": edge_type,
                    "metadata": self.graph.nodes.get(dst, {})
                }
                
                if depth > 1:
                    dep_info["dependencies"] = self._get_dependencies_recursive(
                        dst, depth - 1, visited
                    )
                
                dependencies.append(dep_info)
        
        return dependencies
    
    def _get_dependents_recursive(
        self,
        file_path: str,
        depth: int,
        visited: Set[str]
    ) -> List[Dict[str, Any]]:
        """Get dependents recursively up to depth."""
        if depth <= 0 or file_path in visited:
            return []
        
        visited.add(file_path)
        dependents = []
        
        for src, dst, edge_type in self.graph.edges:
            if dst == file_path and src not in visited:
                dep_info = {
                    "file": src,
                    "type": edge_type,
                    "metadata": self.graph.nodes.get(src, {})
                }
                
                if depth > 1:
                    dep_info["dependents"] = self._get_dependents_recursive(
                        src, depth - 1, visited
                    )
                
                dependents.append(dep_info)
        
        return dependents
    
    def find_related_files(
        self,
        keywords: List[str],
        file_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find files related to keywords.
        
        Args:
            keywords: Keywords to search for
            file_types: File types to include (file, config)
            limit: Maximum results
            
        Returns:
            List of related files
        """
        if not self.graph:
            return []
        
        results = []
        file_types = file_types or ["file", "config"]
        
        for file_path, metadata in self.graph.nodes.items():
            if metadata["kind"] not in file_types:
                continue
            
            # Calculate relevance score
            score = 0
            
            # Check file path
            for keyword in keywords:
                if keyword.lower() in file_path.lower():
                    score += 10
            
            # Check analysis data (for Python files)
            if "analysis" in metadata:
                analysis = metadata["analysis"]
                
                # Check imports
                for imp in analysis.get("imports", []):
                    for keyword in keywords:
                        if keyword.lower() in imp.lower():
                            score += 5
                
                # Check functions
                for func in analysis.get("functions", []):
                    for keyword in keywords:
                        if keyword.lower() in func["name"].lower():
                            score += 8
                
                # Check classes
                for cls in analysis.get("classes", []):
                    for keyword in keywords:
                        if keyword.lower() in cls["name"].lower():
                            score += 8
            
            if score > 0:
                results.append({
                    "file": file_path,
                    "score": score,
                    "metadata": metadata
                })
        
        # Sort by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def get_module_boundary(self, module_name: str) -> Dict[str, Any]:
        """
        Get all files within a module boundary.
        
        Args:
            module_name: Module name (e.g., "api", "core", "services")
            
        Returns:
            Module boundary information
        """
        if not self.graph:
            return {"error": "Graph not loaded"}
        
        module_files = []
        module_path = f"src/investment_system/{module_name}"
        
        for file_path in self.graph.nodes:
            if file_path.startswith(module_path):
                module_files.append({
                    "file": file_path,
                    "metadata": self.graph.nodes[file_path]
                })
        
        return {
            "module": module_name,
            "path": module_path,
            "files": module_files,
            "file_count": len(module_files)
        }
    
    def get_security_report(self) -> Dict[str, Any]:
        """
        Get security report for codebase.
        
        Returns:
            Security analysis report
        """
        if not self.graph:
            return {"error": "Graph not loaded"}
        
        files_with_secrets = []
        total_secrets = 0
        
        for file_path, metadata in self.graph.nodes.items():
            if metadata.get("has_secrets", False):
                files_with_secrets.append({
                    "file": file_path,
                    "secrets_count": metadata.get("secrets_count", 0)
                })
                total_secrets += metadata.get("secrets_count", 0)
        
        return {
            "total_files": len(self.graph.nodes),
            "files_with_secrets": len(files_with_secrets),
            "total_secrets": total_secrets,
            "flagged_files": files_with_secrets,
            "scanned_at": self.graph.metadata.get("indexed_at")
        }
    
    def get_complexity_metrics(self) -> Dict[str, Any]:
        """
        Get code complexity metrics.
        
        Returns:
            Complexity analysis
        """
        if not self.graph:
            return {"error": "Graph not loaded"}
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        largest_files = []
        most_dependencies = []
        
        for file_path, metadata in self.graph.nodes.items():
            if metadata["kind"] != "file":
                continue
            
            analysis = metadata.get("analysis", {})
            
            # Count lines
            lines = analysis.get("lines", 0)
            total_lines += lines
            
            # Count functions and classes
            total_functions += len(analysis.get("functions", []))
            total_classes += len(analysis.get("classes", []))
            
            # Track largest files
            largest_files.append({
                "file": file_path,
                "lines": lines
            })
            
            # Track files with most dependencies
            dep_count = len(self.graph.get_dependencies(file_path))
            if dep_count > 0:
                most_dependencies.append({
                    "file": file_path,
                    "dependencies": dep_count
                })
        
        # Sort and limit
        largest_files.sort(key=lambda x: x["lines"], reverse=True)
        most_dependencies.sort(key=lambda x: x["dependencies"], reverse=True)
        
        return {
            "total_files": len([n for n in self.graph.nodes.values() if n["kind"] == "file"]),
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "average_file_size": total_lines // len(self.graph.nodes) if self.graph.nodes else 0,
            "largest_files": largest_files[:5],
            "most_dependencies": most_dependencies[:5],
            "total_edges": len(self.graph.edges)
        }
    
    def pick_minimal_context(
        self,
        target_files: List[str],
        max_files: int = 10
    ) -> List[str]:
        """
        Pick minimal set of files needed for context.
        
        Args:
            target_files: Target files to understand
            max_files: Maximum files to include
            
        Returns:
            Minimal file set
        """
        if not self.graph:
            return []
        
        context_files = set(target_files)
        
        # Add immediate dependencies
        for file in target_files:
            deps = self.graph.get_dependencies(file)
            context_files.update(deps[:max_files // len(target_files)])
        
        # Limit to max_files
        return list(context_files)[:max_files]


# Global API instance
_sonar_api: Optional[SonarAPI] = None


def get_sonar_api() -> SonarAPI:
    """Get global Sonar API instance."""
    global _sonar_api
    if _sonar_api is None:
        _sonar_api = SonarAPI()
    return _sonar_api