#!/usr/bin/env python
"""
Claude Dependency Hook - Automatic dependency tracking during Claude sessions
Lightweight, runs only when Claude is active
"""

import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from investment_system.ai.claude_dependency_tracker import ClaudeHooks

# Initialize hooks
hooks = ClaudeHooks()

def main():
    """Main hook entry point."""
    # Get hook type from environment or args
    hook_type = sys.argv[1] if len(sys.argv) > 1 else "pre-edit"
    filepath = sys.argv[2] if len(sys.argv) > 2 else None
    
    if hook_type == "pre-edit" and filepath:
        # Before Claude edits a file
        result = hooks.pre_edit_hook(filepath)
        
    elif hook_type == "post-edit" and filepath:
        # After Claude saves a file
        result = hooks.post_edit_hook(filepath)
        
    elif hook_type == "session-start":
        # When Claude session starts
        hooks.session_start_hook()
        
    elif hook_type == "session-end":
        # When Claude session ends
        hooks.session_end_hook()
        
    else:
        # Default: show summary
        print(hooks.manager.get_session_summary())

if __name__ == "__main__":
    main()