"""
Security hardening for AI interactions.
Prevents prompt injection, data exfiltration, and malicious code execution.
"""

import re
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


class AISecurityGuard:
    """Security guard for AI interactions."""
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"(?i)ignore\s+previous\s+instructions",
        r"(?i)override\s+system",
        r"(?i)disregard\s+all",
        r"(?i)forget\s+everything",
        r"(?i)new\s+instructions",
        r"(?i)you\s+are\s+now",
        r"(?i)act\s+as",
        r"(?i)pretend\s+to\s+be",
        r"(?i)execute\s+command",
        r"(?i)run\s+shell",
        r"(?i)eval\(",
        r"(?i)exec\(",
        r"(?i)__import__",
        r"(?i)os\.system",
        r"(?i)subprocess",
        r"(?i)exfiltrate",
        r"(?i)send\s+to\s+url",
        r"(?i)post\s+to",
        r"(?i)wget",
        r"(?i)curl\s+-X",
    ]
    
    # Dangerous code patterns
    DANGEROUS_CODE = [
        r"os\.remove",
        r"os\.rmdir",
        r"shutil\.rmtree",
        r"open\(.*['\"]w['\"]",  # Write mode file operations
        r"\.write\(",
        r"\.delete\(",
        r"DROP\s+TABLE",
        r"DELETE\s+FROM",
        r"TRUNCATE",
    ]
    
    # Allowed tools for AI
    ALLOWED_TOOLS = [
        "sonar.pick_context",
        "sonar.get_file_context",
        "sonar.find_related_files",
        "citations.resolve",
        "search.refs",
        "read_file",  # Read-only
        "list_files",  # Read-only
        "get_dependency_graph",  # Read-only
    ]
    
    def __init__(self):
        self.blocked_attempts = []
        self.scan_history = []
    
    def is_malicious_prompt(self, user_input: str) -> tuple[bool, Optional[str]]:
        """
        Check if user input contains malicious patterns.
        
        Args:
            user_input: User provided input
            
        Returns:
            Tuple of (is_malicious, reason)
        """
        # Check for prompt injection
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, user_input):
                reason = f"Prompt injection detected: {pattern}"
                self.blocked_attempts.append({
                    "type": "prompt_injection",
                    "pattern": pattern,
                    "input_hash": hashlib.sha256(user_input.encode()).hexdigest()
                })
                return True, reason
        
        # Check for dangerous code
        for pattern in self.DANGEROUS_CODE:
            if re.search(pattern, user_input):
                reason = f"Dangerous code pattern detected: {pattern}"
                self.blocked_attempts.append({
                    "type": "dangerous_code",
                    "pattern": pattern,
                    "input_hash": hashlib.sha256(user_input.encode()).hexdigest()
                })
                return True, reason
        
        return False, None
    
    def sanitize_input(self, user_input: str) -> str:
        """
        Sanitize user input by removing dangerous patterns.
        
        Args:
            user_input: Raw user input
            
        Returns:
            Sanitized input
        """
        sanitized = user_input
        
        # Remove markdown links that could be malicious
        sanitized = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', sanitized)
        
        # Remove HTML tags
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        
        # Remove potential command injections
        sanitized = re.sub(r'`[^`]+`', '[code removed]', sanitized)
        
        # Remove URLs that aren't whitelisted
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, sanitized)
        for url in urls:
            if not self._is_safe_url(url):
                sanitized = sanitized.replace(url, '[url removed]')
        
        return sanitized
    
    def _is_safe_url(self, url: str) -> bool:
        """Check if URL is safe/whitelisted."""
        safe_domains = [
            "github.com",
            "docs.python.org",
            "pypi.org",
            "stackoverflow.com",
            "anthropic.com",
            "openai.com"
        ]
        
        for domain in safe_domains:
            if domain in url:
                return True
        return False
    
    def validate_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate if tool call is allowed.
        
        Args:
            tool_name: Name of tool to call
            parameters: Tool parameters
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check if tool is allowed
        if tool_name not in self.ALLOWED_TOOLS:
            return False, f"Tool '{tool_name}' is not in allowlist"
        
        # Validate parameters based on tool
        if tool_name == "read_file":
            file_path = parameters.get("file_path", "")
            if not self._is_safe_path(file_path):
                return False, f"Access to path '{file_path}' is not allowed"
        
        return True, None
    
    def _is_safe_path(self, file_path: str) -> bool:
        """Check if file path is safe to access."""
        path = Path(file_path)
        
        # Prevent directory traversal
        if ".." in str(path):
            return False
        
        # Check if path is within allowed directories
        allowed_roots = ["src", "tests", "config", "docs"]
        path_parts = path.parts
        
        if not path_parts:
            return False
        
        return path_parts[0] in allowed_roots
    
    def redact_secrets(self, content: str) -> str:
        """
        Redact secrets from content before passing to AI.
        
        Args:
            content: Content that may contain secrets
            
        Returns:
            Redacted content
        """
        # Common secret patterns
        secret_patterns = [
            (r'(["\'])([A-Za-z0-9+/]{40,})\1', r'\1[REDACTED_KEY]\1'),  # Long keys
            (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'api_key="[REDACTED]"'),
            (r'secret[_-]?key\s*=\s*["\']([^"\']+)["\']', 'secret_key="[REDACTED]"'),
            (r'password\s*=\s*["\']([^"\']+)["\']', 'password="[REDACTED]"'),
            (r'token\s*=\s*["\']([^"\']+)["\']', 'token="[REDACTED]"'),
            (r'JWT_SECRET\s*=\s*["\']([^"\']+)["\']', 'JWT_SECRET="[REDACTED]"'),
            (r'stripe_[a-z]+_[a-zA-Z0-9]{24,}', '[STRIPE_KEY_REDACTED]'),
        ]
        
        redacted = content
        for pattern, replacement in secret_patterns:
            redacted = re.sub(pattern, replacement, redacted)
        
        return redacted
    
    def enforce_token_limit(self, content: str, max_tokens: int = 8000) -> str:
        """
        Enforce token limit for AI context.
        
        Args:
            content: Content to limit
            max_tokens: Maximum tokens (rough estimate)
            
        Returns:
            Truncated content if needed
        """
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        if len(content) > max_chars:
            return content[:max_chars] + "\n[Content truncated for token limit]"
        
        return content
    
    def validate_output(self, ai_output: str) -> tuple[bool, Optional[str]]:
        """
        Validate AI output for safety.
        
        Args:
            ai_output: Output from AI
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check for dangerous code in output
        for pattern in self.DANGEROUS_CODE:
            if re.search(pattern, ai_output):
                return False, f"AI output contains dangerous code: {pattern}"
        
        # Check for attempts to exfiltrate data
        if re.search(r'(?i)(curl|wget|requests\.post|urllib)', ai_output):
            return False, "AI output attempts to make external requests"
        
        return True, None
    
    def get_security_report(self) -> Dict[str, Any]:
        """
        Get security report of blocked attempts.
        
        Returns:
            Security report
        """
        return {
            "blocked_attempts": len(self.blocked_attempts),
            "recent_blocks": self.blocked_attempts[-10:],
            "scan_count": len(self.scan_history)
        }


class ContextGuard:
    """Guards context passed to AI to prevent information leakage."""
    
    def __init__(self, max_files: int = 20, max_tokens: int = 8000):
        self.max_files = max_files
        self.max_tokens = max_tokens
        self.security_guard = AISecurityGuard()
    
    def prepare_context(self, files: List[Dict[str, Any]]) -> str:
        """
        Prepare safe context for AI.
        
        Args:
            files: List of file information
            
        Returns:
            Safe context string
        """
        # Limit number of files
        safe_files = files[:self.max_files]
        
        context_parts = []
        
        for file_info in safe_files:
            file_path = file_info.get("file", "unknown")
            
            # Only include safe metadata
            safe_metadata = {
                "path": file_path,
                "lines": file_info.get("lines", 0),
                "functions": len(file_info.get("functions", [])),
                "classes": len(file_info.get("classes", [])),
                "has_tests": "test" in file_path.lower()
            }
            
            # Don't include actual code content, just structure
            context_parts.append(json.dumps(safe_metadata))
        
        context = "\n".join(context_parts)
        
        # Redact any secrets
        context = self.security_guard.redact_secrets(context)
        
        # Enforce token limit
        context = self.security_guard.enforce_token_limit(context, self.max_tokens)
        
        return context
    
    def validate_file_excerpt(self, file_path: str, content: str, checksum: str) -> bool:
        """
        Validate file excerpt hasn't been tampered with.
        
        Args:
            file_path: Path to file
            content: File content
            checksum: Expected checksum
            
        Returns:
            True if valid
        """
        actual_checksum = hashlib.sha256(content.encode()).hexdigest()
        return actual_checksum == checksum


# Global security instances
ai_security_guard = AISecurityGuard()
context_guard = ContextGuard()