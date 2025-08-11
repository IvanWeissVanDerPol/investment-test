# Investment System - AI Project Context

## 🎯 Project Overview
**Name:** Investment System MVP  
**Type:** AI-Ready Trading Signal Platform  
**Stage:** Phase 1 Security Implementation  
**Revenue Model:** Tiered SaaS (Free/$29/$99/$499)  

## 🏗️ Architecture Summary

### Core Components
1. **FastAPI Backend** - RESTful API with JWT auth
2. **SQLAlchemy + PostgreSQL** - Secure data persistence  
3. **Redis Cache** - Performance optimization
4. **Alembic Migrations** - Database versioning
5. **AI Hooks** - Extensible signal enhancement

### Directory Structure
```
investment-test/
├── config/                 # Centralized configuration
│   ├── alembic.ini        # Database migrations
│   ├── pytest.ini         # Test configuration
│   ├── settings.py        # Python settings
│   ├── config.json        # App configuration
│   └── dependency_graph.yaml # Module dependencies
├── docs/                   # Documentation
│   ├── architecture/      # System design
│   ├── implementation/    # Development workflow
│   ├── audits/           # Security & code audits
│   └── ai_context/       # AI agent instructions
├── src/                   # Source code
│   └── investment_system/
│       ├── api/          # REST API endpoints
│       ├── core/         # Business logic
│       ├── infrastructure/ # Database, cache
│       ├── pipeline/     # Data processing
│       ├── security/     # Auth & encryption
│       └── services/     # Business services
├── tests/                # Test suite
└── runtime/             # Runtime artifacts (gitignored)
```

## 🔐 Security Features
- **Argon2** password hashing
- **JWT** authentication with environment-based secrets
- **API key** rotation mechanism
- **Audit logging** for compliance
- **Rate limiting** per tier
- **Account lockout** after failed attempts

## 💰 Revenue Features
- **Tiered Subscriptions:** Free, Starter ($29), Pro ($99), Enterprise ($499)
- **Usage Tracking:** API calls, symbols, signals
- **Stripe Integration:** Ready for payment processing
- **Export Features:** CSV/PDF for premium users

## 🤖 AI Integration Points
The system has built-in hooks for AI enhancement:

1. **Signal Analysis Hooks:**
   - `pre_analysis` - Before market data processing
   - `post_indicators` - After technical indicators
   - `signal_override` - Override trading signals
   - `confidence_adjustment` - Adjust confidence scores

2. **AI-Ready Features:**
   - Dependency graph prevents breaking changes
   - Modular analyzers for easy extension
   - Cached results for performance
   - Audit trails for decisions

## 📊 Data Flow
1. **Ingest:** Fetch market data → Cache → Validate
2. **Analyze:** Calculate indicators → Generate signals → Apply AI hooks
3. **Persist:** Store in PostgreSQL → Track usage → Audit log
4. **Serve:** REST API → Rate limit → Response cache

## 🚀 Current Status
- ✅ Phase 1 Day 1-2: Security foundation complete
- 🔄 Phase 1 Day 3-5: Audit logging & monitoring (in progress)
- ⏳ Phase 2: Revenue features (Stripe, dashboard)
- ⏳ Phase 3: Production readiness
- ⏳ Phase 4: AI integration

## 🛠️ Development Guidelines

### Before Making Changes:
1. Check `config/dependency_graph.yaml` for module dependencies
2. Review `CLAUDE.md` for coding standards
3. Run tests: `pytest tests/`
4. Check security: Review `docs/audits/SECURITY_AUDIT.md`

### Key Commands:
```bash
# Setup
pip install -e .[dev]
cp .env.example .env
# Edit .env with secure values

# Database
alembic -c config/alembic.ini upgrade head

# Run API
uvicorn investment_system.api.app:app --reload

# Tests
pytest -c config/pytest.ini tests/
```

### Configuration Priority:
1. Environment variables (.env)
2. config/settings.py
3. config/config.json
4. Defaults in code

## 📝 Important Files for AI

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Main AI instructions |
| `config/dependency_graph.yaml` | Module dependencies |
| `docs/implementation/WORKFLOW.md` | Current tasks |
| `docs/audits/SECURITY_AUDIT.md` | Security requirements |
| `.env.example` | Environment template |

## ⚠️ Critical Rules
1. **NEVER** hardcode secrets
2. **ALWAYS** hash passwords with Argon2
3. **CHECK** dependency graph before changes
4. **TEST** all changes locally
5. **AUDIT** security impact

## 🎯 Success Metrics
- API response time < 200ms
- 99.9% uptime
- 80%+ test coverage
- Security score 8/10
- $20K MRR within 3 months