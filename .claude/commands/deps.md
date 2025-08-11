# Dependency Commands for Claude

## Quick Commands

### Check dependencies before editing
```bash
python .claude/hooks/dependency_hook.py pre-edit <filepath>
```

### Track changes after editing
```bash
python .claude/hooks/dependency_hook.py post-edit <filepath>
```

### Get current session summary
```bash
python .claude/hooks/dependency_hook.py summary
```

### Find safe refactoring targets
```bash
python src/investment_system/ai/claude_dependency_tracker.py safe
```

## Automatic Integration

These hooks run automatically when:
- Claude opens a file (pre-edit)
- Claude saves a file (post-edit)
- Claude session starts (loads context)
- Claude session ends (saves context)

## Context Preservation

The system maintains a lightweight cache in `.claude/dependency_cache.json` that:
- Tracks module dependencies
- Identifies high-risk changes
- Preserves context between sessions
- Uses minimal memory (< 1KB per module)

## Risk Indicators

- **HIGH**: Module has >10 dependents
- **MEDIUM**: Module has 5-10 dependents
- **LOW**: Module has 2-5 dependents
- **NONE**: Module has 0-1 dependents