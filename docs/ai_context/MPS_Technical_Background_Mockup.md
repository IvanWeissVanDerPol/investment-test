# Technical Background Mockup: Prediction & Signals Meta‑Module (MPS) — Integrable Specification

**Objective:** Provide a decoupled, scalable plug‑in subsystem that delivers **trading signals** (stocks and commodities) with **fresh multi‑source data**, **state‑of‑the‑art yet robust models**, **realistic backtesting**, and **risk/sizing metrics**, accessible from your existing website/app via API/SDK/Jobs.

---

## 1) Integration Architecture (high level)

**Pattern:** *Hexagonal / Ports & Adapters*  
**Deployment modes:** (pick one or combine)
- **Sidecar API:** `mps-api` (FastAPI) + Redis (cache) + MinIO/S3 (data) + Postgres (metadata). Your app consumes REST/WS.
- **Job Runner:** `mps-jobs` (Prefect) exposes queues/cron; your app triggers flows (ingest/score/backtest) via webhook.
- **Embedded SDK:** `pip install mps_client` for typed access to endpoints and contracts.

**Bounded Contexts:**
- `ingest` → `reconcile` → `featurize` → `train` → `serve` → `backtest`  
- `catalog` (Security Master, calendars, costs)  
- `governance` (model/data versioning, audit, MLflow model registry)

**Interfaces (Ports):**
- REST: `/bars`, `/features`, `/score`, `/signals/stream`, `/backtest`, `/health`
- gRPC (optional) for low latency: `ScoreService.Score(Symbol, TF, AsOf)`
- Events (Kafka/NATS optional): `signals.v1`, `data.freshness`  
- Webhooks: `on_model_promoted`, `on_data_stale`, `on_rollover`

---

## 2) Data Contracts (typed and minimal)

### 2.1 Security Master
```json
{
  "id":"AAPL:US",
  "symbol":"AAPL",
  "isin":"US0378331005",
  "mic":"XNAS",
  "asset_class":"equity|futures",
  "currency":"USD",
  "tick_size":0.01,
  "lot":1,
  "roll_rules":{"method":"back_adjusted","policy":"max_oi","days_before_fnd":3},
  "session_calendar":"XNAS_RTH"
}
```

### 2.2 Bars (silver, reconciled)
```json
{"ts":"2025-08-11T14:30:00Z","symbol_id":"AAPL:US",
 "o":182.1,"h":182.7,"l":181.9,"c":182.4,"v":1234567,
 "vwap":182.35,"quality":{"stale":false,"outlier_frac":0.0,"n_src":3,"lat_ms":320}}
```

### 2.3 FeatureRow (gold)
```json
{"ts":"2025-08-11T14:30:00Z","symbol_id":"CL:NYM",
 "tf":"15m","features":{"ret_1":0.0006,"rsi_14":58.3,"atr_14":1.12,"ema_20":76.2,
 "curve_slope":0.014,"carry":0.006,"mom_1m_rank":0.84,"lowvol_rank":0.22},
 "regime":"trend","meta":{"adv_pct":0.008,"spread_bp":1.9}}
```

### 2.4 Signal
```json
{"ts":"2025-08-11T14:30:02Z","symbol_id":"AAPL:US","tf":"15m",
 "horizon_bars":16,"score":0.0009,"prob_up":0.61,"conf":0.78,
 "expected_return":0.0007,
 "risk":{"target_vol":0.12,"realized_vol":0.18,"kelly_frac":0.17},
 "sizing":{"nav_frac":0.021,"max_adv_share":0.012},
 "model":{"ensemble":"thompson_bandit","members":["lgbm","tft"],"version":"2025.08.11-rc1"}}
```

---

## 3) Endpoints (Ports) — Stable API

- `GET /health` → liveness + model versions and per‑source latencies.  
- `GET /bars?symbol_id=&tf=&window=` → reconciled bars (silver).  
- `GET /features?symbol_id=&tf=&asof=` → latest gold row.  
- `POST /score {symbol_id, tf, horizon_bars, asof?}` → `Signal`.  
- `POST /backtest {symbols[], params{...}}` → JSON report (+ link to Parquet/HTML).  
- `POST /governance/promote {model_version}` → model *blue/green*.  
- `GET /telemetry/freshness?symbol_id` → data age and *staleness guards*.

**Suggested SLAs:**  
- p99 `POST /score` ≤ 120 ms (with cached features), p50 ≤ 35 ms.  
- Freshness `equity 1m` < 5 s; `futures 1m` < 3 s during RTH/ETH.

---

## 4) Pipelines (Prefect Jobs) — Orchestration

1. **Ingest** `*/15s`–`*/60s` per TF  
   - Parallel pull from 2–3 vendors (exchange + consolidated). Normalize to UTC/exchange_tz. Persist to `bronze/`.
2. **Reconcile** on‑ingest  
   - Weighted‑median by latency×uptime×reliability; outliers if `|src−cons|>kσ`.  
   - Corporate actions; **continuous futures** (back/ratio). Emit `silver/`.
3. **Featurize** on bar close  
   - TS (lags/RSI/ATR/Donchian/EWMA vol), cross‑sectional (momentum/low‑vol ranks), curve (carry/slope/F1F2), regime (BOCPD/HMM). Emit `gold/`.
4. **Train** nightly/weekly with **walk‑forward expanding**  
   - Baselines (LGBM/XGB), advanced (TFT, N‑BEATS), calibration (Platt/Isotonic), conformal bands (ICP). Log in MLflow.
5. **Promote** with *shadow eval* + *canary*  
   - Online bandit meta‑ensembler (Thompson). Fallback rules.
6. **Serve** (sync/async)  
   - Cache features in Redis by (symbol, tf, asof). Score → Signal with risk sizing.
7. **Backtest** on demand  
   - Event‑driven, realistic frictions (commissions, spread, slippage ∝ ADV share), roll consistent with method.

---

## 5) Multi‑Source Reconciliation (math and robustness)

**Consensus price:** weighted median
\[
\tilde{p}_t = \operatorname{median}_w \{ p_{t}^{(i)} \},\quad 
w_i \propto \frac{\text{uptime}_i \cdot \text{reliability}_i}{\text{latency}_i + \epsilon}
\]
**Outlier detection:** exclude \(i\) if \(|p^{(i)}_t-\tilde{p}_t|>k\,\hat{\sigma}_t\) (MAD‑based).  
**Staleness guard:** if `age_ms > θ(tf)` mark `stale=true` and degrade to delayed; *cut real‑time signals*.

---

## 6) Feature Engineering (lean yet powerful)

- **TS:** returns \(\Delta \ln P\), rolling mean/std, RSI, ATR, Donchian, EWMA vol.  
- **Cross‑sectional:** momentum 1–3–6m (ranks in liquid universe), low‑vol anomaly, *quality* if fundamentals exist.  
- **Curve (futures):** \( \text{slope}= \frac{F_2-F_1}{F_1} \), carry %, F1–F2 spread, butterfly.  
- **Regime:** BOCPD (adaptive hazard) or HMM (3 states: *trend/meanrev/stress*), *features‑aware*.  
- **Meta:** liquidity (ADV%), spread proxy, VIX proxy (for equities).

**Eliminate look‑ahead:** strict *as‑of joins*, windows closing at t‑1.

---

## 7) Models (quality + novelty)

### 7.1 Robust tabular baselines
- **LGBM/XGB** for `prob_up` and/or `return@h`.  
- *TimeSeriesSplit* (**walk‑forward**), *group‑aware* by symbol, *target encoding* for sectors.

### 7.2 Advanced SOTA
- **TFT** (Temporal Fusion Transformer) with covariates (gold features).  
- **N‑BEATS** (trend/seasonality blocks) for per‑symbol pure TS.  
- **Meta‑learning/transfer:** pre‑train on wide universe, *fine‑tune* by cluster (equities/commodities/energy/metals).  
- **Online bandit ensemblers:** Thompson Sampling with reward \(R_t = \text{Sharpe}_{\text{rolling,OOS}}\).  
- **Conformal Prediction:** Inductive CP for intervals/sets; filter low‑validity signals.  
- **Probabilistic calibration:** Platt/Isotonic; target ECE ≤ 0.05.  
- **Drift detection:** PSI/KL; triggers partial re‑training.

**Production model selection:**  
\[
\text{Score} = \underbrace{\text{Sharpe}_{OOS}}_{\text{quality}} - \lambda_1 \underbrace{\sigma(\text{Sharpe})}_{\text{stability}} - \lambda_2 \underbrace{\text{ECE}}_{\text{calibration}} - \lambda_3 \underbrace{\text{latency}}_{\text{serving}}
\]

---

## 8) Signal → Sizing → Risk

**Expected Return:**
\[
E[R] = p\,G - (1-p)\,L - \text{fees} - \text{slip}
\]
where \(p=\Pr(\text{up})\), \(G,L\) estimated conditional on **regime**.

**Fractional Kelly:**
\[
f^* = p - \frac{1-p}{b},\quad b=\frac{G}{L}\quad\Rightarrow\quad f = \alpha\, f^*,\; \alpha\in[0.25,0.5]
\]

**Target Vol Scaling:** position size \(\propto \frac{\text{vol\_target}}{\text{vol\_realized}}\).  
**Guards:** max %NAV per symbol, max %ADV, intraday DD *kill‑switch*.

---

## 9) Realistic Backtesting (auditable)

- **Event‑driven** aware of *sessions/gaps/halts*.  
- **Futures:** roll by `max OI/vol` or *days before FND/LTD*; method *back‑adjusted* or *ratio‑adjusted* consistent.  
- **Frictions:** venue fees, **slippage ∝ ADV share** + *bid‑ask spread*.  
- **Metric CIs:** *clustered bootstrap* by day/week for Sharpe/Calmar/MaxDD/HitRate/ProfitFactor.  
- **Validation:** *anchored walk‑forward* + *rolling window*; *purging/embargo* (López de Prado) if stacking labels.

---

## 10) Performance & SLOs

- **p99 scoring latency** ≤ 120 ms (CPU); ≤ 40 ms with batch pre‑scoring.  
- **Freshness** p99 equity 1m < 5 s; futures 1m < 3 s.  
- **Cost:** columnar Parquet storage; *compaction* and *z‑order* by `symbol_id, ts`.  
- **Scale:** 5k symbols, TF 1m–1d ⇒ 150–300 GB/year (Parquet snappy); training on spot instances.

---

## 11) Observability & Governance

- Metrics: `data_freshness_ms`, `outlier_rate`, `stale_rate`, `drift_psi`, `score_latency_ms`, `oos_sharpe`, `ece`, `abort_dd_intraday`.  
- OpenTelemetry traces; structured logs.  
- MLflow for artifacts, signatures, dependencies. Auto‑generated **model cards** (methodology, data, fairness).  
- **Auto rollback** if `ECE↑` or `Sharpe_OOS↓` > threshold during canary.

---

## 12) Security & Compliance

- Rate‑limit, rotating JWTs, RBAC (read:bars, read:signals, admin).  
- **Market data licenses:** realtime vs delayed; user entitlement by symbol/venue.  
- GDPR/LPD: minimization, deletion; S3 **object‑lock** for backtest invariants.  
- **Disclaimer** visible: educational information; if you execute orders → KYC/AML, best‑execution.

---

## 13) Testing (hard quality)

- **Data:** OHLCV invariants, reconciliation (inter‑source spread distribution), deterministic *replay*.  
- **Features:** *no look‑ahead* via *as‑of* tests.  
- **Models:** leakage checks, SHAP stability across splits, OOS ECE/ROC.  
- **E2E:** *golden runs* of backtests with hashes in CI; latencies under load (Locust).

---

## 14) Declarative Configuration (strategy YAML)
```yaml
strategy:
  universe: ["AAPL:US","MSFT:US","CL:NYM","GC:CMX"]
  timeframe: "15m"
  horizon_bars: 16
  roll_method: "back_adjusted"
  regime_model: "bocpd"
  features:
    ts: {rsi:14, atr:14, ema:[10,20,50], mom:[5,20]}
    cross: {momentum_months:[1,3,6], low_vol:true}
    curve: {use:true, spreads:["F1F2","F2F3"], carry:true}
  models:
    tabular: {type:"lgbm", params:{num_leaves:64, learning_rate:0.05}}
    deep: {type:"tft", params:{hidden:64, dropout:0.1}}
    ensemble: {type:"thompson_bandit", decay:0.95}
  risk:
    vol_target: 0.12
    kelly_fraction: 0.35
    max_nav_per_symbol: 0.05
    max_adv_share: 0.02
  costs:
    fee_bps: 1.0
    slippage: {model:"adv_participation", bps_per_adv_share: 30}
  guards:
    stale_threshold_s: 10
    dd_kill_intraday: 0.05
```

---

## 15) Operational Pseudocode (for Claude)

### 15.1 Reconcile
```python
def reconcile_bars(bars_df):
    # group by (symbol, ts); compute weighted median by w = uptime*reliab/(lat_ms+eps)
    cons = weighted_median(bars_df, key="price", w="w")
    mad = median_abs_dev(bars_df["price"])
    flags = abs(bars_df["price"]-cons) > 3*mad
    cons = cons[~flags]  # drop outliers
    cons = apply_corporate_actions(cons)
    cons = build_continuous_futures(cons, method=cfg.roll.method, policy=cfg.roll.policy)
    cons["stale"] = cons["age_ms"] > stale_threshold(tf)
    return cons
```

### 15.2 Features
```python
def make_features(silver):
    f = add_ts(silver)           # rsi/atr/ema/mom/vol
    f = add_cross_sectional(f)   # ranks momentum/lowvol
    f = add_curve(f)             # slope/carry/F1F2
    f["regime"] = bocpd(f[["ret","vol","corr"]])
    return as_of_join(f)
```

### 15.3 Train (walk‑forward + bandit ensemble)
```python
for tr, va in time_series_splits(gold):
    m_tab = fit_lgbm(tr.X, tr.y); p_tab = m_tab.predict(va.X)
    m_tft = fit_tft(tr.seqX, tr.y); p_tft = m_tft.predict(va.seqX)
    # calibration
    p_tab = calibrate(p_tab, va.y); p_tft = calibrate(p_tft, va.y)
    # bandit reward = rolling sharpe
    w = bandit_update({"lgbm":p_tab,"tft":p_tft}, reward=rolling_sharpe(va.y, mix(p_tab,p_tft)))
    log_metrics(va, sharpe=sharpe(va.y, mix(p_tab,p_tft,w)), ece=e_calib([...]))
promote_if_canary_ok()
```

### 15.4 Serving
```python
def score(symbol, tf, horizon):
    x = load_cached_features(symbol, tf)  # Redis
    p_up, conf = ensemble_predict(x)      # Thompson weights
    G,L = cond_gains_losses(symbol, tf, regime=x["regime"])
    er = p_up*G - (1-p_up)*L - fees(symbol) - slippage(symbol, x["adv_pct"])
    f_star = p_up - (1-p_up)/(G/L)
    size = clip(alpha*f_star * vol_target/x["realized_vol"], adv_cap(symbol))
    return build_signal(er, p_up, conf, size)
```

### 15.5 Backtest
```python
def backtest(params):
    env = MarketEnv(calendars, halts, rolls=params.roll_method, costs=params.costs)
    sim = Simulator(env, slippage=adv_model(params))
    res = sim.run(signals, bars_silver)
    return metrics_and_cis(res)  # Sharpe/Calmar/DD/HitRate/ProfitFactor + CIs
```
---

## 16) Deployment & Rollback Strategy

- **Blue/Green** models with *shadow* (on/off users) + 10–20% canary.  
- Auto‑revert if `oos_sharpe` falls >30% vs baseline or `ece` rises >0.03 across 3 windows.  
- Versioned feature store; reproducibility via `data_snapshot_id`.

---

## 17) Expected UI Interface (from your app)

- *Knobs*: TF (1m/5m/15m/1h/1d), roll method, fees/slippage, regime ON/OFF, universe.  
- *Asset panel*: price, **data age**, freshness semaphore, signal + confidence, expected return, target vol, suggested size.  
- *Portfolio*: aggregate risk, %NAV used, expected DD.  
- *What‑if*: vary fees/slippage and observe impacts.

---

## 18) Success Metrics (promotion to production)

- **OOS Sharpe ≥ 1.0** (bootstrap CI > 0.6), **MaxDD < 15%**, **ECE ≤ 0.05**, p99 latency ≤ 120 ms, *data stale rate* < 1%.  
- Feature importance stability (SHAP) across splits; drift robustness (degradation < 40% under stress).

---

## 19) Integration Roadmap (1–2 sprints)

1. Wire `mps-api` (sidecar) and `mps_client` in your backend.  
2. Load Security Master + calendars.  
3. Enable 2–3 sources and reconciliation; validate `freshness` and `outlier_rate`.  
4. Generate gold + baseline LGBM; expose `/score`.  
5. Add TFT + bandit + conformal; canary/shadow.  
6. UI: freshness semaphores + knobs; *what‑if*.  
7. On‑demand backtest with downloadable report.  
8. Telemetry/alerts/auto‑rollback.

---

## 20) Mathematical Annex (summary)

- **Penalized Sharpe:** \(\text{Sharpe}_\lambda = \bar{R}/\sigma - \lambda\,\sigma(\text{Sharpe})\).  
- **Conformal p‑value:** \(p = \frac{1}{n+1}\big(1 + \sum \mathbb{1}\{\alpha_i \ge \alpha_{new}\}\big)\).  
- **Adaptive BOCPD hazard:** \(H_t = \min\{H_{max}, c\,\hat{\sigma}_{\Delta R}\}\).  
- **ADV slippage:** \(\text{slip\_bps} \approx \beta \cdot \%\text{ADV} + \gamma \cdot \text{spread\_bps}\).

---

## 21) Example Calls

### Score
```bash
curl -X POST https://mps.local/score \
 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
 -d '{"symbol_id":"AAPL:US","tf":"15m","horizon_bars":16}'
```

### Backtest
```bash
curl -X POST https://mps.local/backtest \
 -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
 -d '{
  "symbols":["AAPL:US","CL:NYM"],
  "params":{"timeframe":"15m","horizon_bars":16,
            "fees_bps":1.0,"slippage_model":"adv_participation",
            "adv_cap":0.02,"roll_method":"back_adjusted"}
 }'
```

---

## 22) Integrable Repo Structure
```
mps/
  apps/
    api/            # FastAPI (ports)
    jobs/           # Prefect flows
  services/
    ingest/ reconcile/ featurize/ train/ serve/ backtest/
  shared/
    schemas/ utils/ config/ clients/ (mps_client SDK)
  data/ bronze/ silver/ gold/
  infra/ terraform/ ci/
```

**Delivery:** package `mps-api` and `mps-jobs` as containers; expose `mps_client` (Python/TypeScript).  
**Coupling:** only through contracts/ports — your website consumes without touching the core.
