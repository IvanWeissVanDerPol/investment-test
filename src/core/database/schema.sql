-- Investment System Database Schema
-- SQLite database for configuration and reference data

-- User Profile and Settings
CREATE TABLE user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    dukascopy_balance REAL DEFAULT 0,
    interactive_brokers_balance REAL DEFAULT 0,
    total_portfolio_value REAL DEFAULT 0,
    currency TEXT DEFAULT 'USD',
    risk_tolerance TEXT CHECK(risk_tolerance IN ('low', 'medium', 'high')) DEFAULT 'medium',
    target_ai_allocation_percent REAL DEFAULT 50,
    target_green_allocation_percent REAL DEFAULT 30,
    max_single_position_percent REAL DEFAULT 15,
    account_id TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_timestamp TIMESTAMP,
    timezone TEXT DEFAULT 'UTC'
);

-- Investment Goals (many-to-many)
CREATE TABLE investment_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal TEXT UNIQUE NOT NULL
);

CREATE TABLE user_goals (
    user_id INTEGER,
    goal_id INTEGER,
    PRIMARY KEY (user_id, goal_id),
    FOREIGN KEY (user_id) REFERENCES user_profile(id),
    FOREIGN KEY (goal_id) REFERENCES investment_goals(id)
);

-- Broker Configuration
CREATE TABLE broker_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    broker_name TEXT NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    connection_type TEXT CHECK(connection_type IN ('auto', 'manual')) DEFAULT 'auto',
    host TEXT DEFAULT '127.0.0.1',
    tws_port INTEGER DEFAULT 7497,
    gateway_port INTEGER DEFAULT 4001,
    client_id INTEGER DEFAULT 1,
    auto_sync BOOLEAN DEFAULT TRUE,
    sync_interval_minutes INTEGER DEFAULT 15
);

-- API Configuration
CREATE TABLE api_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT UNIQUE NOT NULL,
    api_key TEXT,
    base_url TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    config_json TEXT -- Additional service-specific config
);

-- Email Settings
CREATE TABLE email_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enabled BOOLEAN DEFAULT FALSE,
    smtp_server TEXT DEFAULT 'smtp.gmail.com',
    smtp_port INTEGER DEFAULT 587,
    username TEXT,
    password TEXT,
    recipient TEXT,
    use_tls BOOLEAN DEFAULT TRUE
);

-- Report Schedule
CREATE TABLE report_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT NOT NULL, -- daily, weekly, monthly
    scheduled_time TEXT,
    scheduled_day INTEGER, -- For weekly (1-7) or monthly (1-31)
    enabled BOOLEAN DEFAULT TRUE,
    last_run TIMESTAMP,
    config_json TEXT -- Additional report-specific config
);

-- Analysis Settings
CREATE TABLE analysis_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_type TEXT NOT NULL,
    name TEXT NOT NULL,
    value REAL,
    value_text TEXT,
    value_json TEXT,
    description TEXT
);

-- Stocks and ETFs
CREATE TABLE securities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    sector TEXT,
    market_cap_category TEXT,
    cik TEXT,
    security_type TEXT CHECK(security_type IN ('stock', 'etf')) DEFAULT 'stock',
    metadata_json TEXT -- Additional security info
);

-- Security Categories (many-to-many)
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL,
    category_type TEXT NOT NULL -- ai_software, green_energy, defense, etc.
);

CREATE TABLE security_categories (
    security_id INTEGER,
    category_id INTEGER,
    PRIMARY KEY (security_id, category_id),
    FOREIGN KEY (security_id) REFERENCES securities(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Institutional Funds
CREATE TABLE institutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    focus_area TEXT,
    priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
    metadata_json TEXT
);

-- Defense Contractors
CREATE TABLE defense_contractors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    symbol TEXT,
    ai_focus TEXT CHECK(ai_focus IN ('very_high', 'high', 'medium', 'low')) DEFAULT 'medium',
    government_contracts TEXT CHECK(government_contracts IN ('high', 'medium', 'low')) DEFAULT 'medium',
    metadata_json TEXT
);

-- Government Agencies
CREATE TABLE government_agencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    abbreviation TEXT,
    ai_budget_level TEXT CHECK(ai_budget_level IN ('very_high', 'high', 'medium', 'low')) DEFAULT 'medium',
    metadata_json TEXT
);

-- Ethics Configuration
CREATE TABLE ethics_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_type TEXT CHECK(category_type IN ('preferred', 'neutral', 'blocked')) NOT NULL,
    category_name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE ethics_blacklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT,
    reason TEXT,
    alternative_symbol TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ethics Scoring Weights
CREATE TABLE ethics_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factor_type TEXT NOT NULL, -- environmental, social, governance
    factor_name TEXT NOT NULL,
    weight REAL CHECK(weight >= 0 AND weight <= 1),
    description TEXT,
    UNIQUE(factor_type, factor_name)
);

-- Keywords Configuration
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_type TEXT NOT NULL, -- ai, sustainability, etc.
    keyword TEXT UNIQUE NOT NULL,
    weight REAL DEFAULT 1.0,
    enabled BOOLEAN DEFAULT TRUE
);

-- ETF Mappings
CREATE TABLE etf_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etf_symbol TEXT NOT NULL,
    etf_name TEXT,
    category TEXT,
    metadata_json TEXT
);

-- Portfolio Holdings (for tracking actual positions)
CREATE TABLE portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    security_id INTEGER,
    shares REAL,
    average_cost REAL,
    current_price REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT,
    FOREIGN KEY (security_id) REFERENCES securities(id)
);

-- Historical Performance
CREATE TABLE performance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE,
    total_value REAL,
    cash_balance REAL,
    invested_amount REAL,
    daily_change REAL,
    daily_change_percent REAL,
    metadata_json TEXT
);

-- Analysis Results Cache
CREATE TABLE analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_type TEXT NOT NULL,
    security_symbol TEXT,
    result_data TEXT, -- JSON string
    confidence_score REAL,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_securities_symbol ON securities(symbol);
CREATE INDEX idx_securities_sector ON securities(sector);
CREATE INDEX idx_categories_name ON categories(category_name);
CREATE INDEX idx_keywords_type ON keywords(keyword_type);
CREATE INDEX idx_analysis_cache_type ON analysis_cache(analysis_type);
CREATE INDEX idx_analysis_cache_symbol ON analysis_cache(security_symbol);
CREATE INDEX idx_performance_history_date ON performance_history(date);
CREATE INDEX idx_portfolio_holdings_security ON portfolio_holdings(security_id);

-- Initialize core data
INSERT INTO investment_goals (goal) VALUES 
    ('AI/robotics growth'),
    ('earth preservation'),
    ('clean technology'),
    ('government contract exposure'),
    ('smart money following');

INSERT INTO ethics_categories (category_type, category_name, description) VALUES
    ('preferred', 'renewable_energy', 'Companies focused on renewable energy solutions'),
    ('preferred', 'clean_technology', 'Clean technology and sustainable innovation'),
    ('preferred', 'electric_vehicles', 'Electric vehicle manufacturers and infrastructure'),
    ('preferred', 'energy_storage', 'Battery and energy storage companies'),
    ('blocked', 'fossil_fuels', 'Fossil fuel extraction and processing'),
    ('blocked', 'tobacco', 'Tobacco product manufacturers'),
    ('blocked', 'weapons_manufacturing', 'Military weapons manufacturing');

INSERT INTO ethics_weights (factor_type, factor_name, weight, description) VALUES
    ('environmental', 'carbon_emissions', 0.4, 'Carbon footprint and emissions reduction'),
    ('environmental', 'renewable_energy_use', 0.3, 'Use of renewable energy sources'),
    ('social', 'employee_treatment', 0.35, 'Employee satisfaction and treatment'),
    ('social', 'community_impact', 0.25, 'Impact on local communities'),
    ('governance', 'transparency', 0.4, 'Corporate transparency and reporting'),
    ('governance', 'board_diversity', 0.3, 'Diversity in board composition');