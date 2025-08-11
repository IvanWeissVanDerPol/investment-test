/**
 * TypeScript types matching backend Pydantic models and MPS contracts
 */

// Enums matching backend
export enum TimeFrame {
  ONE_MIN = "1m",
  FIVE_MIN = "5m",
  FIFTEEN_MIN = "15m",
  THIRTY_MIN = "30m",
  ONE_HOUR = "1h",
  FOUR_HOUR = "4h",
  ONE_DAY = "1d",
  ONE_WEEK = "1w",
  ONE_MONTH = "1M"
}

export enum AssetClass {
  EQUITY = "equity",
  FUTURES = "futures",
  OPTIONS = "options",
  FOREX = "forex",
  CRYPTO = "crypto",
  COMMODITY = "commodity",
  INDEX = "index"
}

export enum SignalDirection {
  BUY = "buy",
  SELL = "sell",
  HOLD = "hold"
}

export enum DataQuality {
  BRONZE = "bronze",
  SILVER = "silver",
  GOLD = "gold"
}

// Security Master
export interface SecurityMaster {
  id: string;  // e.g., "AAPL:US"
  symbol: string;
  exchange: string;
  isin?: string;
  assetClass: AssetClass;
  currency: string;
  tickSize: number;
  lotSize: number;
  marketHours?: {
    open: string;
    close: string;
    timezone: string;
  };
  isActive: boolean;
}

// Market Data Bar (matching MPS spec)
export interface MarketDataBar {
  ts: string;  // ISO timestamp
  symbolId: string;
  o: number;  // open
  h: number;  // high
  l: number;  // low
  c: number;  // close
  v: number;  // volume
  vwap?: number;
  quality: {
    stale: boolean;
    outlierFrac: number;
    nSrc: number;
    latMs: number;
  };
}

// Feature Row (matching MPS spec)
export interface FeatureRow {
  ts: string;
  symbolId: string;
  tf: TimeFrame;
  features: {
    ret_1?: number;
    rsi_14?: number;
    atr_14?: number;
    ema_20?: number;
    ema_50?: number;
    sma_20?: number;
    sma_50?: number;
    curveSlope?: number;
    carry?: number;
    mom1mRank?: number;
    lowvolRank?: number;
  };
  regime?: "trend" | "mean_reversion" | "stress";
  meta?: {
    advPct: number;
    spreadBp: number;
  };
}

// Trading Signal (matching MPS spec)
export interface TradingSignal {
  ts: string;
  symbolId: string;
  tf: TimeFrame;
  horizonBars: number;
  score: number;
  probUp: number;
  conf: number;
  expectedReturn: number;
  risk: {
    targetVol: number;
    realizedVol: number;
    kellyFrac: number;
  };
  sizing: {
    navFrac: number;
    maxAdvShare: number;
  };
  model: {
    ensemble: string;
    members: string[];
    version: string;
  };
  // UI-specific additions
  direction?: SignalDirection;
  isExecuted?: boolean;
  executionPrice?: number;
}

// Data freshness indicator
export interface DataFreshness {
  symbolId: string;
  lastUpdate: string;
  ageMs: number;
  isStale: boolean;
  staleSince?: string;
  status: "fresh" | "delayed" | "stale" | "error";
}

// Backtest Request
export interface BacktestRequest {
  symbols: string[];
  params: {
    timeframe: TimeFrame;
    horizonBars: number;
    startDate: string;
    endDate: string;
    feesBps: number;
    slippageModel: "fixed" | "adv_participation";
    advCap?: number;
    rollMethod?: "back_adjusted" | "ratio_adjusted";
  };
}

// Backtest Result
export interface BacktestResult {
  id: string;
  strategyId: string;
  symbols: string[];
  period: {
    start: string;
    end: string;
  };
  metrics: {
    totalReturn: number;
    annualizedReturn: number;
    sharpeRatio: number;
    sortinoRatio: number;
    calmarRatio: number;
    maxDrawdown: number;
    winRate: number;
    profitFactor: number;
    totalTrades: number;
  };
  equityCurve: Array<{
    date: string;
    value: number;
    drawdown: number;
  }>;
  trades?: Array<{
    symbol: string;
    entryDate: string;
    exitDate: string;
    direction: "long" | "short";
    pnl: number;
    returnPct: number;
  }>;
}

// Portfolio Summary
export interface PortfolioSummary {
  totalValue: number;
  cash: number;
  positions: number;
  dailyPnl: number;
  dailyPnlPct: number;
  totalPnl: number;
  totalPnlPct: number;
  risk: {
    portfolioVol: number;
    var95: number;
    expectedDrawdown: number;
    navUsed: number;
  };
}

// Position
export interface Position {
  symbolId: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
  allocation: number;  // % of portfolio
  signal?: TradingSignal;
}

// WebSocket messages
export interface WSMessage {
  type: "price" | "signal" | "execution" | "status";
  data: any;
  timestamp: string;
}

export interface PriceUpdate {
  symbolId: string;
  price: number;
  bid: number;
  ask: number;
  volume: number;
  timestamp: string;
}

export interface SignalUpdate {
  signal: TradingSignal;
  action: "new" | "update" | "cancel";
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T;
  status: "success" | "error";
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// User preferences
export interface UserPreferences {
  defaultTimeframe: TimeFrame;
  defaultUniverse: string[];
  theme: "light" | "dark" | "auto";
  notifications: {
    signals: boolean;
    executions: boolean;
    alerts: boolean;
  };
  display: {
    showStaleData: boolean;
    autoRefresh: boolean;
    refreshInterval: number;  // seconds
  };
  risk: {
    maxPositions: number;
    maxAllocationPerSymbol: number;
    stopLoss: number;
    takeProfit: number;
  };
}