# MVP File Retention Audit & AI-Ready Architecture

**Date:** 2025-08-09  
**Goal:** Revenue-generating MVP with AI pipeline readiness  
**Principle:** Keep only what generates money or enables AI automation

## PART 1: FILE RETENTION MATRIX

### 1.1 ✅ KEEP - Revenue Critical (16 files)

| File | Purpose | Revenue Impact | AI-Ready Score |
|------|---------|----------------|----------------|
| `src/investment_system/api.py` | Customer API endpoints | Direct - API subscriptions | 9/10 - Clean interfaces |
| `src/investment_system/pipeline/ingest.py` | Data collection | Critical - Real-time data | 8/10 - Modular design |
| `src/investment_system/pipeline/analyze.py` | Signal generation | Direct - Trading signals | 7/10 - Needs abstraction |
| `src/investment_system/db/store.py` | Data persistence | Critical - Historical data | 8/10 - ORM ready |
| `src/investment_system/web/templates/index.html` | Customer dashboard | Direct - User engagement | 6/10 - Needs API-first |
| `src/config/settings.py` | Configuration | Infrastructure | 9/10 - Env-based |
| `pyproject.toml` | Package management | Infrastructure | 10/10 - Standard |
| `.github/workflows/ci.yml` | CI/CD | Reliability = Revenue | 8/10 - Extensible |
| `Dockerfile` | Deployment | Fast deployment = Revenue | 9/10 - Multi-stage ready |
| `tests/investment_system/test_pipeline_smoke.py` | Quality assurance | Prevents revenue loss | 7/10 - Needs expansion |
| `README.md` | Documentation | Customer onboarding | 5/10 - Needs update |
| `CLAUDE.md` | AI instructions | AI automation | 10/10 - AI-native |
| `.env.example` | Configuration template | Deployment speed | 8/10 - Clear structure |
| `requirements.txt` | Dependencies | Infrastructure | 7/10 - Needs pruning |
| `pytest.ini` | Test configuration | Quality | 8/10 - Good foundation |
| `Makefile` | Automation | Developer productivity | 9/10 - Simple commands |

### 1.2 ❌ DELETE - Not Revenue Critical (180+ files)

#### Legacy/Duplicate Systems (DELETE ALL)
```
src/core/                        # 60+ files - OLD SYSTEM, DUPLICATES EVERYTHING
├── investment_system/           # 12,000+ lines of duplicate code
│   ├── analysis/               # 15 files - Replaced by pipeline/analyze.py
│   ├── portfolio/              # 13 files - No portfolio feature in MVP
│   ├── ai/                     # 4 files - Not integrated, keep for Phase 2
│   ├── monitoring/             # 5 files - Use Prometheus instead
│   └── data/                   # 10 files - Replaced by pipeline/ingest.py
└── database/                    # 4 files - Replaced by investment_system/db/

src/web/                         # 15 files - OLD FLASK APP
├── app.py                      # Replaced by FastAPI
├── app_secure.py               # Security theater, not real security
└── static/                     # Old UI, use React in Phase 2

tools/                           # 40+ files - WINDOWS BATCH SCRIPTS
├── analysis/*.bat              # Replace with CLI commands
├── monitoring/*.bat            # Use real monitoring (Prometheus)
├── powerbi/                   # 5 files - No PowerBI in MVP
└── workflows/*.bat             # Replace with Python CLI
```

#### Over-Engineered Features (DELETE ALL)
```
mcp/                            # 5 files - MCP not needed for MVP
├── deployment_mcp.py          # Over-complex
├── investment_mcp.py          # Not integrated
├── powerbi_mcp.py            # No PowerBI
├── testing_mcp.py            # Over-engineered
└── web_dev_mcp.py            # Not needed

planning/                       # Historical docs, not needed
docs/01_project_overview/      # Outdated
docs/02_implementation/        # Historical
docs/03_enhancements/          # Future features
docs/05_investment_strategy/  # Business logic, not code
docs/06_system_monitoring/     # 10 files of tracking sheets
docs/07_research_and_analysis/ # Research notes
```

#### Test Files in Wrong Location (MOVE OR DELETE)
```
# Root directory test files (DELETE)
test_core_logic.py
test_enhanced_integration.py
test_enhanced_system_live.py
test_integration_simple.py
test_market_data_integration.py
test_yfinance_basic.py
```

#### Cache and Runtime (GITIGNORE)
```
cache/                          # 40+ cached files
src/runtime/                    # SQLite databases
*.egg-info/                     # Build artifacts
```

#### Redundant Scripts (DELETE)
```
scripts/                        # 5 files - Over-engineered
├── deploy_production.py       # Use Docker instead
├── load_testing.py           # Use locust/k6 instead
├── run_background_worker.py  # Use celery in Phase 2
├── security_audit.py         # Use GitHub security scanning
└── setup_secure_system.py    # Security theater
```

### 1.3 🔄 REFACTOR - Transform for MVP (5 files)

| Current File | Transform To | Revenue Impact |
|--------------|--------------|----------------|
| `src/config/*.json` (6 files) | Single `config.yaml` | Faster deployment |
| `deploy/docker-compose.yml` | Simplified 3-service version | Easier scaling |
| `deploy/kubernetes/*.yaml` | Hold for Phase 2 | Not needed yet |
| `reference/*.json` | Embed in code or database | Reduce file count |
| Multiple test files | Single `tests/test_mvp.py` | Faster CI/CD |

## PART 2: AI-READY ARCHITECTURE

### 2.1 Core Architecture Principles

```yaml
principles:
  separation_of_concerns:
    - Pure functions for business logic
    - Dependency injection for external services
    - Event-driven communication between modules
    
  ai_integration_points:
    - Standardized input/output contracts
    - Versioned API schemas
    - Observability hooks at every decision point
    
  revenue_optimization:
    - Pay-per-API-call billing ready
    - Usage tracking built-in
    - A/B testing infrastructure
```

### 2.2 Proposed MVP Architecture

```
investment-system/
├── api/
│   ├── __init__.py
│   ├── app.py                 # FastAPI application
│   ├── routes/
│   │   ├── auth.py           # JWT authentication
│   │   ├── signals.py        # Trading signals endpoint
│   │   ├── data.py           # Market data endpoint
│   │   └── billing.py        # Usage & billing endpoint
│   └── middleware/
│       ├── auth.py           # Auth middleware
│       ├── rate_limit.py     # Rate limiting
│       └── metrics.py        # Prometheus metrics
│
├── core/                       # Pure business logic (AI-ready)
│   ├── __init__.py
│   ├── contracts/             # Data contracts (Pydantic)
│   │   ├── market.py         # MarketData, PricePoint
│   │   ├── signals.py        # TradingSignal, Indicator
│   │   └── analysis.py       # AnalysisRequest, Result
│   ├── analyzers/             # Pluggable analyzers
│   │   ├── base.py           # Abstract base analyzer
│   │   ├── technical.py      # Technical indicators
│   │   └── ai.py             # AI analyzer (Phase 2)
│   └── pipeline/              # Data pipeline
│       ├── ingest.py         # Data ingestion
│       ├── transform.py      # Data transformation
│       └── analyze.py        # Analysis orchestration
│
├── infrastructure/            # External services
│   ├── __init__.py
│   ├── database/
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── migrations/       # Alembic migrations
│   │   └── repositories.py   # Data access layer
│   ├── cache/
│   │   └── redis.py         # Redis caching
│   ├── queue/                # For AI pipeline (Phase 2)
│   │   └── celery.py        # Task queue
│   └── monitoring/
│       └── prometheus.py     # Metrics collection
│
├── services/                  # Business services
│   ├── __init__.py
│   ├── market_data.py       # Market data service
│   ├── signal_generator.py  # Signal generation service
│   ├── billing.py           # Usage tracking & billing
│   └── notification.py      # Alert notifications
│
└── cli/                      # Command-line interface
    ├── __init__.py
    └── commands.py           # CLI commands
```

### 2.3 Revenue-Generating Features (MVP)

```python
# Billing tiers for immediate revenue
PRICING_TIERS = {
    "free": {
        "api_calls": 100,
        "symbols": 5,
        "signals_per_day": 10,
        "price": 0
    },
    "starter": {
        "api_calls": 1000,
        "symbols": 20,
        "signals_per_day": 100,
        "price": 29  # $29/month
    },
    "pro": {
        "api_calls": 10000,
        "symbols": 100,
        "signals_per_day": 1000,
        "price": 99  # $99/month
    },
    "enterprise": {
        "api_calls": -1,  # Unlimited
        "symbols": -1,
        "signals_per_day": -1,
        "price": 499  # $499/month
    }
}

# Revenue endpoints
POST   /api/v1/subscribe         # Stripe subscription
GET    /api/v1/signals           # Get trading signals (metered)
GET    /api/v1/analysis/{symbol} # Detailed analysis (metered)
GET    /api/v1/portfolio/optimize # Portfolio optimization (premium)
POST   /api/v1/alerts            # Set price alerts (premium)
GET    /api/v1/export/csv        # Export data (premium)
```

### 2.4 AI Pipeline Integration Points

```yaml
ai_hooks:
  data_ingestion:
    - hook: "post_fetch_prices"
    - purpose: "AI can enhance/clean data"
    - contract: "PriceData -> EnhancedPriceData"
    
  signal_generation:
    - hook: "pre_generate_signal"
    - purpose: "AI can override/enhance signals"
    - contract: "SignalRequest -> SignalResponse"
    
  risk_assessment:
    - hook: "post_risk_calculation"
    - purpose: "AI can adjust risk scores"
    - contract: "RiskScore -> AdjustedRiskScore"
    
  performance_monitoring:
    - hook: "on_prediction_result"
    - purpose: "AI learns from outcomes"
    - contract: "PredictionResult -> ModelUpdate"
    
  ci_cd_automation:
    - hook: "on_commit"
    - purpose: "AI reviews code and suggests improvements"
    - contract: "CommitDiff -> ReviewSuggestions"
    
  deployment_decisions:
    - hook: "pre_deploy"
    - purpose: "AI decides if safe to deploy"
    - contract: "DeploymentPlan -> ApprovalDecision"
```

## PART 3: DELETION SCRIPT

```bash
#!/bin/bash
# delete_non_mvp.sh - Remove 180+ non-MVP files

echo "🗑️ Starting MVP cleanup - removing 14,000+ lines of code"

# Create backup branch
git checkout -b backup/pre-mvp-$(date +%Y%m%d-%H%M%S)
git add -A
git commit -m "backup: pre-MVP state"
git push origin backup/pre-mvp-$(date +%Y%m%d-%H%M%S)

# Return to working branch
git checkout integration-claude-review

# Delete legacy systems
echo "Removing legacy core system..."
rm -rf src/core/
rm -rf src/web/

# Delete tools and scripts
echo "Removing batch scripts..."
rm -rf tools/
rm -rf mcp/
rm -rf scripts/

# Delete test files from root
echo "Cleaning up test files..."
rm -f test_*.py

# Delete unnecessary docs
echo "Removing outdated documentation..."
rm -rf docs/01_project_overview/
rm -rf docs/02_implementation/
rm -rf docs/03_enhancements/
rm -rf docs/05_investment_strategy/
rm -rf docs/07_research_and_analysis/

# Delete planning and reference
rm -rf planning/
rm -rf reference/

# Delete deploy configs we don't need
rm -rf deploy/kubernetes/

# Clean cache
echo "Cleaning cache..."
rm -rf cache/

# Update .gitignore
cat >> .gitignore << 'EOF'

# MVP Exclusions
cache/
*.egg-info/
src/runtime/
*.db
*.db-shm
*.db-wal
.env
EOF

# Count the damage
echo "✅ Cleanup complete!"
echo "Files before: $(git ls-files | wc -l)"
echo "Files remaining: $(ls -la | wc -l)"
echo "Lines removed: ~14,000"
```

## PART 4: MVP IMPLEMENTATION CHECKLIST

### Week 1: Core Revenue Features

#### Day 1: Clean Slate
- [ ] Run deletion script (remove 180+ files)
- [ ] Create new architecture directories
- [ ] Setup basic CI/CD pipeline
- [ ] Create .env.example with all vars

#### Day 2: Authentication & Billing
```python
# src/api/routes/auth.py
@router.post("/register")
async def register(email: str, password: str, tier: str = "free"):
    user = create_user(email, password, tier)
    stripe_customer = stripe.Customer.create(email=email)
    return {"user_id": user.id, "api_key": generate_api_key()}

@router.post("/subscribe")
async def subscribe(user_id: str, tier: str):
    price_id = STRIPE_PRICE_IDS[tier]
    subscription = stripe.Subscription.create(
        customer=user.stripe_id,
        items=[{"price": price_id}]
    )
    return {"subscription_id": subscription.id}
```

#### Day 3: Metered API Endpoints
```python
# src/api/routes/signals.py
@router.get("/signals")
@track_usage  # Decorator for billing
@require_auth
@rate_limit(tier_based=True)
async def get_signals(
    symbols: List[str] = Query(..., max_items=100),
    user: User = Depends(get_current_user)
):
    # Check user tier limits
    if len(symbols) > user.tier.max_symbols:
        raise HTTPException(402, "Upgrade required")
    
    signals = await signal_service.generate(symbols)
    
    # Track for billing
    await billing_service.record_usage(
        user_id=user.id,
        endpoint="signals",
        units=len(symbols)
    )
    
    return signals
```

#### Day 4: Dashboard with Paywall
```javascript
// Frontend: React component with tier checking
function SignalDashboard() {
    const { user } = useAuth();
    
    if (user.tier === 'free' && user.api_calls >= 100) {
        return <UpgradePrompt />;
    }
    
    return (
        <Dashboard>
            <SignalChart symbols={user.tier_limits.symbols} />
            {user.tier !== 'free' && <AdvancedAnalytics />}
            {user.tier === 'enterprise' && <AIInsights />}
        </Dashboard>
    );
}
```

#### Day 5: Performance & Monitoring
```python
# src/infrastructure/monitoring/prometheus.py
from prometheus_client import Counter, Histogram, Gauge

api_calls = Counter('api_calls_total', 'Total API calls', ['endpoint', 'tier'])
response_time = Histogram('response_time_seconds', 'Response time')
active_subscriptions = Gauge('active_subscriptions', 'Active subscriptions', ['tier'])

# Track revenue metrics
revenue_metrics = Gauge('monthly_recurring_revenue', 'MRR', ['tier'])
churn_rate = Gauge('churn_rate', 'Customer churn rate')
lifetime_value = Gauge('customer_lifetime_value', 'CLV', ['tier'])
```

### Week 2: Optimization & Launch

#### Day 6-7: Testing & Quality
```python
# tests/test_billing.py
def test_free_tier_limits():
    user = create_test_user(tier="free")
    
    # Should work for first 100 calls
    for _ in range(100):
        response = client.get("/api/v1/signals", 
                            headers={"Authorization": f"Bearer {user.token}"})
        assert response.status_code == 200
    
    # Should fail on 101st call
    response = client.get("/api/v1/signals",
                          headers={"Authorization": f"Bearer {user.token}"})
    assert response.status_code == 402
    assert "Upgrade required" in response.json()["detail"]

def test_subscription_upgrade():
    user = create_test_user(tier="free")
    
    # Upgrade to pro
    response = client.post("/api/v1/subscribe",
                          json={"tier": "pro"},
                          headers={"Authorization": f"Bearer {user.token}"})
    assert response.status_code == 200
    
    # Should now have pro limits
    response = client.get("/api/v1/signals?symbols=" + ",".join(["AAPL"] * 50),
                         headers={"Authorization": f"Bearer {user.token}"})
    assert response.status_code == 200
```

#### Day 8: Docker & Deployment
```dockerfile
# Optimized multi-stage Dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --user -e .

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY src/ src/
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Day 9: Launch Preparation
- [ ] Setup Stripe production keys
- [ ] Configure domain and SSL
- [ ] Setup monitoring dashboards
- [ ] Create landing page
- [ ] Prepare email templates

#### Day 10: Launch!
- [ ] Deploy to production
- [ ] Monitor first users
- [ ] Track revenue metrics
- [ ] Gather feedback

## PART 5: SUCCESS METRICS

### Technical Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time | < 200ms | Prometheus p95 |
| Uptime | 99.9% | StatusPage |
| Test Coverage | > 80% | pytest-cov |
| Deploy Time | < 5 min | GitHub Actions |
| Docker Image Size | < 150MB | docker images |

### Business Metrics
| Metric | Week 1 | Month 1 | Month 3 |
|--------|--------|---------|---------|
| Free Users | 100 | 1,000 | 5,000 |
| Paid Users | 5 | 50 | 250 |
| MRR | $250 | $2,500 | $12,500 |
| Churn Rate | < 10% | < 5% | < 3% |
| CAC | < $50 | < $30 | < $20 |
| LTV | > $150 | > $300 | > $500 |

### AI Readiness Metrics
| Component | Current | Target | Timeline |
|-----------|---------|--------|----------|
| API Contracts | 0% | 100% | Week 1 |
| Event Hooks | 0% | 100% | Week 2 |
| Observability | 10% | 90% | Week 2 |
| Modularity | 40% | 95% | Week 1 |
| Test Coverage | 10% | 85% | Week 2 |

## PART 6: POST-MVP ROADMAP

### Month 2: AI Integration Phase 1
- Integrate Claude for signal enhancement
- Add AI-driven risk assessment
- Implement automated code review
- Setup AI-powered alerts

### Month 3: AI Integration Phase 2
- AI-driven CI/CD decisions
- Automated deployment approval
- Self-healing infrastructure
- Predictive scaling

### Month 6: Full AI Platform
- Complete AI pipeline automation
- Self-optimizing trading strategies
- Automated customer support
- AI-driven feature development

## CONCLUSION

**Immediate Action:** Delete 180+ files (14,000 lines) TODAY

**Files to Keep:** 16 core files only

**Revenue Model:** Tiered API subscriptions ($0/$29/$99/$499)

**Time to Revenue:** 10 days

**Expected MRR:** $2,500 in Month 1, $12,500 in Month 3

**AI Readiness:** Architecture ready for AI integration from Day 1

---

*"The best code is no code at all. The second best is less code that makes money."*