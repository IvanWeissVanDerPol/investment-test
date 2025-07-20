# Claude Code Rule: No Emojis in Code Files

## Rule: NEVER Use Emojis in Code Files

**CRITICAL**: Claude Code must NEVER use emojis (Unicode characters like 🚀, 🌍, 💰, etc.) in any code files, including:

- Python files (.py)
- JavaScript files (.js, .ts)
- Configuration files (.json, .yaml, .toml)
- Documentation files (.md, .rst)
- Any source code or configuration

## Why This Rule Exists

1. **Encoding Issues**: Emojis cause `UnicodeEncodeError` on Windows systems with cp1252 encoding
2. **Cross-Platform Compatibility**: Different systems handle Unicode differently
3. **Professional Standards**: Code should be text-based and universally readable
4. **Terminal Compatibility**: Many terminal environments don't render emojis correctly

## Acceptable Alternatives

Instead of emojis, use:

### ✅ GOOD - Text-based indicators:
```python
# [SUCCESS] Operation completed
print("[ERROR] Failed to process")
print("[WARNING] Potential issue detected")
print("[INFO] Processing data...")
```

### ✅ GOOD - ASCII characters:
```python
print("*** IMPORTANT ***")
print(">>> Processing...")
print("--- RESULTS ---")
```

### ❌ BAD - Emojis in code:
```python
# 🚀 NEVER DO THIS
print("🌍 Processing...")  # CAUSES UNICODE ERRORS
print("💰 Results...")     # BREAKS ON WINDOWS
```

## Exception: User-Facing Output Only

Emojis may ONLY be used in:
- User documentation (README files for display only)
- User interface text (when specifically requested)
- Comments in markdown files intended for display

## Enforcement

This rule applies to ALL code generation by Claude Code. Violation of this rule causes system failures and must be avoided at all costs.

## Example Fix

❌ **Before (breaks system):**
```python
print("🚀 Starting analysis...")
result["status"] = "🌍 Green investment"
```

✅ **After (works correctly):**
```python
print("[ROCKET] Starting analysis...")
result["status"] = "[GREEN] Green investment"
```

**Remember: Code must be universally compatible. NO EMOJIS EVER.**