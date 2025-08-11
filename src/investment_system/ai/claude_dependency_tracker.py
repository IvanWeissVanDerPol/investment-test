"""
Optimized Claude-Aware Dependency Tracker
Lightweight, context-efficient system for maintaining interdependence during Claude sessions
"""

import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, Set, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class DependencySnapshot:
    """Compact dependency representation for Claude context."""
    module: str
    imports: List[str]
    exports: List[str]
    complexity: int
    hash: str


class ClaudeDependencyTracker:
    """
    Simplified dependency tracker optimized for Claude context windows.
    Maintains minimal state while preserving critical interdependence information.
    """
    
    def __init__(self, cache_file: str = ".claude/dependency_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(exist_ok=True)
        
        # Compact in-memory structures
        self.dependency_map = {}  # module -> set of dependencies
        self.reverse_map = {}     # module -> set of dependents
        self.snapshots = {}       # module -> DependencySnapshot
        self.session_changes = [] # track changes in current session
        
        self._load_cache()
    
    def _load_cache(self):
        """Load cached dependency data if available."""
        if self.cache_file.exists():
            with open(self.cache_file) as f:
                data = json.load(f)
                self.dependency_map = {k: set(v) for k, v in data.get('dependencies', {}).items()}
                self.reverse_map = {k: set(v) for k, v in data.get('dependents', {}).items()}
    
    def _save_cache(self):
        """Save dependency data to cache."""
        data = {
            'dependencies': {k: list(v) for k, v in self.dependency_map.items()},
            'dependents': {k: list(v) for k, v in self.reverse_map.items()},
            'snapshots': {k: asdict(v) for k, v in self.snapshots.items()}
        }
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def track_file_change(self, filepath: str) -> Dict:
        """
        Track a file change and return compact dependency info.
        This is called when Claude modifies a file.
        """
        path = Path(filepath)
        if not path.exists() or not path.suffix == '.py':
            return {}
        
        module_name = self._path_to_module(path)
        old_deps = self.dependency_map.get(module_name, set())
        
        # Analyze new dependencies
        new_deps = self._analyze_file(path)
        
        # Calculate impact
        impact = {
            'module': module_name,
            'added_deps': list(new_deps - old_deps),
            'removed_deps': list(old_deps - new_deps),
            'affected_modules': list(self.reverse_map.get(module_name, set())),
            'risk_level': self._calculate_risk(module_name, new_deps)
        }
        
        # Update maps
        self.dependency_map[module_name] = new_deps
        self._update_reverse_map(module_name, old_deps, new_deps)
        
        # Track session change
        self.session_changes.append(impact)
        
        # Save to cache
        self._save_cache()
        
        return impact
    
    def _analyze_file(self, filepath: Path) -> Set[str]:
        """Quickly analyze a Python file for dependencies."""
        deps = set()
        try:
            with open(filepath) as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if 'investment_system' in alias.name:
                            deps.add(alias.name.replace('investment_system.', ''))
                elif isinstance(node, ast.ImportFrom):
                    if node.module and 'investment_system' in node.module:
                        deps.add(node.module.replace('investment_system.', ''))
        except:
            pass
        
        return deps
    
    def _update_reverse_map(self, module: str, old_deps: Set[str], new_deps: Set[str]):
        """Update the reverse dependency map efficiently."""
        # Remove old reverse dependencies
        for dep in old_deps - new_deps:
            if dep in self.reverse_map:
                self.reverse_map[dep].discard(module)
        
        # Add new reverse dependencies
        for dep in new_deps - old_deps:
            if dep not in self.reverse_map:
                self.reverse_map[dep] = set()
            self.reverse_map[dep].add(module)
    
    def _calculate_risk(self, module: str, deps: Set[str]) -> str:
        """Calculate risk level of changes."""
        dependent_count = len(self.reverse_map.get(module, set()))
        
        if dependent_count > 10:
            return "HIGH"
        elif dependent_count > 5:
            return "MEDIUM"
        elif dependent_count > 0:
            return "LOW"
        return "NONE"
    
    def _path_to_module(self, filepath: Path) -> str:
        """Convert file path to module name."""
        # Simple conversion for investment_system
        parts = filepath.parts
        if 'investment_system' in parts:
            idx = parts.index('investment_system')
            module_parts = parts[idx+1:]
            if module_parts:
                return '.'.join(p.replace('.py', '') for p in module_parts)
        return filepath.stem
    
    def get_context_summary(self) -> Dict:
        """
        Get a compact summary for Claude's context.
        This is what Claude sees to understand dependencies.
        """
        # Find critical modules (high dependency count)
        critical_modules = [
            (mod, len(deps)) 
            for mod, deps in self.reverse_map.items() 
            if len(deps) > 5
        ]
        critical_modules.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'total_modules': len(self.dependency_map),
            'critical_modules': critical_modules[:5],
            'recent_changes': self.session_changes[-5:] if self.session_changes else [],
            'high_risk_modules': [
                mod for mod in self.dependency_map 
                if self._calculate_risk(mod, self.dependency_map[mod]) == "HIGH"
            ]
        }
    
    def check_before_edit(self, filepath: str) -> Dict:
        """
        Quick check before editing a file.
        Returns dependency info Claude needs to know.
        """
        path = Path(filepath)
        module_name = self._path_to_module(path)
        
        return {
            'module': module_name,
            'imports': list(self.dependency_map.get(module_name, [])),
            'imported_by': list(self.reverse_map.get(module_name, [])),
            'risk_level': self._calculate_risk(module_name, self.dependency_map.get(module_name, set())),
            'warning': self._get_edit_warning(module_name)
        }
    
    def _get_edit_warning(self, module: str) -> Optional[str]:
        """Get warning message if editing this module is risky."""
        dependents = self.reverse_map.get(module, set())
        
        if len(dependents) > 10:
            return f"⚠️ HIGH RISK: {len(dependents)} modules depend on this. Changes will have wide impact."
        elif len(dependents) > 5:
            return f"⚠️ MEDIUM RISK: {len(dependents)} modules depend on this."
        elif 'core' in module or 'contracts' in module:
            return "⚠️ CORE MODULE: Changes may affect system stability."
        
        return None
    
    def get_safe_refactoring_targets(self) -> List[str]:
        """Get list of modules safe to refactor (low dependency)."""
        safe_modules = []
        
        for module in self.dependency_map:
            if len(self.reverse_map.get(module, set())) <= 2:
                safe_modules.append(module)
        
        return safe_modules[:10]  # Limit to 10 for context efficiency


class ClaudeContextManager:
    """
    Manages dependency context for Claude sessions.
    Integrates with Claude's workflow to maintain awareness.
    """
    
    def __init__(self):
        self.tracker = ClaudeDependencyTracker()
        self.context_file = Path(".claude/current_context.json")
        self.context_file.parent.mkdir(exist_ok=True)
    
    def on_file_open(self, filepath: str) -> str:
        """Called when Claude opens a file for editing."""
        info = self.tracker.check_before_edit(filepath)
        
        # Generate concise context message
        msg = f"📁 Opening: {info['module']}\n"
        
        if info['warning']:
            msg += f"{info['warning']}\n"
        
        if info['imported_by']:
            msg += f"Used by: {', '.join(info['imported_by'][:5])}\n"
        
        return msg
    
    def on_file_save(self, filepath: str) -> str:
        """Called when Claude saves a file."""
        impact = self.tracker.track_file_change(filepath)
        
        if not impact:
            return ""
        
        # Generate impact summary
        msg = f"💾 Saved: {impact['module']}\n"
        
        if impact['risk_level'] == 'HIGH':
            msg += f"⚠️ HIGH IMPACT: {len(impact['affected_modules'])} modules affected\n"
        elif impact['affected_modules']:
            msg += f"Impact: {len(impact['affected_modules'])} modules\n"
        
        if impact['added_deps']:
            msg += f"Added deps: {', '.join(impact['added_deps'][:3])}\n"
        
        return msg
    
    def get_session_summary(self) -> str:
        """Get summary of current session for Claude."""
        summary = self.tracker.get_context_summary()
        
        msg = "📊 Dependency Status:\n"
        msg += f"• Modules tracked: {summary['total_modules']}\n"
        
        if summary['critical_modules']:
            msg += "• Critical modules:\n"
            for mod, count in summary['critical_modules'][:3]:
                msg += f"  - {mod}: {count} dependents\n"
        
        if summary['recent_changes']:
            msg += f"• Recent changes: {len(summary['recent_changes'])}\n"
        
        if summary['high_risk_modules']:
            msg += f"• ⚠️ High risk modules: {len(summary['high_risk_modules'])}\n"
        
        return msg
    
    def save_context(self):
        """Save current context for next Claude session."""
        context = {
            'summary': self.tracker.get_context_summary(),
            'session_changes': self.tracker.session_changes,
            'timestamp': str(Path.ctime(Path.cwd()))
        }
        
        with open(self.context_file, 'w') as f:
            json.dump(context, f, indent=2)
    
    def load_context(self) -> Dict:
        """Load context from previous Claude session."""
        if self.context_file.exists():
            with open(self.context_file) as f:
                return json.load(f)
        return {}


# Claude Hook Integration
class ClaudeHooks:
    """
    Lightweight hooks for Claude file operations.
    These run automatically during Claude's workflow.
    """
    
    def __init__(self):
        self.manager = ClaudeContextManager()
    
    def pre_edit_hook(self, filepath: str):
        """Run before Claude edits a file."""
        msg = self.manager.on_file_open(filepath)
        if msg:
            print(msg)
        return msg
    
    def post_edit_hook(self, filepath: str):
        """Run after Claude saves a file."""
        msg = self.manager.on_file_save(filepath)
        if msg:
            print(msg)
        return msg
    
    def session_start_hook(self):
        """Run when Claude session starts."""
        context = self.manager.load_context()
        if context:
            print("📥 Loaded dependency context from previous session")
            if 'summary' in context:
                if context['summary'].get('high_risk_modules'):
                    print(f"⚠️ {len(context['summary']['high_risk_modules'])} high-risk modules identified")
    
    def session_end_hook(self):
        """Run when Claude session ends."""
        self.manager.save_context()
        print("💾 Dependency context saved")
        print(self.manager.get_session_summary())


# Simple CLI for testing
if __name__ == "__main__":
    import sys
    
    hooks = ClaudeHooks()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check" and len(sys.argv) > 2:
            filepath = sys.argv[2]
            hooks.pre_edit_hook(filepath)
        
        elif command == "track" and len(sys.argv) > 2:
            filepath = sys.argv[2]
            hooks.post_edit_hook(filepath)
        
        elif command == "summary":
            print(hooks.manager.get_session_summary())
        
        elif command == "safe":
            safe = hooks.manager.tracker.get_safe_refactoring_targets()
            print("Safe to refactor:")
            for module in safe:
                print(f"  - {module}")
    else:
        # Run session summary by default
        hooks.session_start_hook()
        print(hooks.manager.get_session_summary())