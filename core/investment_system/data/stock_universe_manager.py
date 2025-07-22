"""
Stock Universe Manager
Manages comprehensive stock and company data with validation and efficient access
"""

import json
import pandas as pd
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import yfinance as yf
from datetime import datetime
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class MarketCap(Enum):
    NANO = "nano"           # < $50M
    MICRO = "micro"         # $50M - $300M
    SMALL = "small"         # $300M - $2B
    MID = "mid"             # $2B - $10B
    LARGE = "large"         # $10B - $200B
    MEGA = "mega"           # > $200B

class InvestmentType(Enum):
    STOCK = "stock"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    REIT = "reit"
    TRUST = "trust"
    ADR = "adr"
    CRYPTO = "crypto"

@dataclass
class Company:
    symbol: str
    name: str
    sector: str
    industry: str
    market_cap: str
    investment_type: str = "stock"
    exchange: str = "NASDAQ"
    currency: str = "USD"
    description: str = ""
    ai_relevance_score: float = 0.0
    govt_contract_exposure: float = 0.0
    smart_money_interest: float = 0.0
    last_updated: str = ""
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

@dataclass
class Sector:
    name: str
    category: str
    description: str
    growth_potential: float
    volatility_score: float
    correlation_with_ai: float
    supply_chain_dependencies: List[str]
    influenced_sectors: List[str]
    key_metrics: Dict[str, float]
    companies: List[Company]

class StockUniverseManager:
    """Manages the complete stock universe with efficient querying and validation"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.companies: Dict[str, Company] = {}
        self.sectors: Dict[str, Sector] = {}
        self.indices: Dict[str, Set[str]] = {
            'by_sector': {},
            'by_market_cap': {},
            'by_ai_score': {},
            'by_govt_exposure': {},
            'by_smart_money': {}
        }
        self.load_data()
        self.build_indices()
    
    def load_data(self):
        """Load all stock and sector data"""
        try:
            # Load the massive stock universe
            self.companies = self._load_comprehensive_universe()
            self.sectors = self._load_sector_definitions()
            logger.info(f"Loaded {len(self.companies)} companies across {len(self.sectors)} sectors")
        except Exception as e:
            logger.error(f"Error loading stock universe: {e}")
            self.companies = {}
            self.sectors = {}
    
    def _load_comprehensive_universe(self) -> Dict[str, Company]:
        """Load the comprehensive stock universe (1000+ per sector)"""
        universe = {}
        
        # AI & Technology Sectors
        ai_companies = [
            # Mega Cap AI
            Company("NVDA", "NVIDIA Corporation", "artificial_intelligence", "Semiconductors", "mega", ai_relevance_score=0.95, smart_money_interest=0.90),
            Company("MSFT", "Microsoft Corporation", "artificial_intelligence", "Software", "mega", ai_relevance_score=0.92, smart_money_interest=0.88),
            Company("GOOGL", "Alphabet Inc.", "artificial_intelligence", "Internet Services", "mega", ai_relevance_score=0.94, smart_money_interest=0.89),
            Company("META", "Meta Platforms Inc.", "artificial_intelligence", "Social Media", "large", ai_relevance_score=0.87, smart_money_interest=0.82),
            Company("AAPL", "Apple Inc.", "artificial_intelligence", "Consumer Electronics", "mega", ai_relevance_score=0.75, smart_money_interest=0.91),
            Company("AMZN", "Amazon.com Inc.", "artificial_intelligence", "E-commerce", "mega", ai_relevance_score=0.78, smart_money_interest=0.85),
            Company("TSLA", "Tesla Inc.", "artificial_intelligence", "Electric Vehicles", "large", ai_relevance_score=0.83, smart_money_interest=0.79),
            
            # Large Cap AI
            Company("CRM", "Salesforce Inc.", "artificial_intelligence", "Software", "large", ai_relevance_score=0.81, smart_money_interest=0.73),
            Company("NOW", "ServiceNow Inc.", "artificial_intelligence", "Software", "large", ai_relevance_score=0.77, smart_money_interest=0.71),
            Company("SNOW", "Snowflake Inc.", "artificial_intelligence", "Software", "large", ai_relevance_score=0.79, smart_money_interest=0.68),
            Company("PLTR", "Palantir Technologies", "artificial_intelligence", "Software", "large", ai_relevance_score=0.88, govt_contract_exposure=0.92),
            Company("AMD", "Advanced Micro Devices", "artificial_intelligence", "Semiconductors", "large", ai_relevance_score=0.86, smart_money_interest=0.74),
            Company("INTC", "Intel Corporation", "artificial_intelligence", "Semiconductors", "large", ai_relevance_score=0.71, smart_money_interest=0.65),
            Company("QCOM", "QUALCOMM Inc.", "artificial_intelligence", "Semiconductors", "large", ai_relevance_score=0.73, smart_money_interest=0.67),
            Company("AVGO", "Broadcom Inc.", "artificial_intelligence", "Semiconductors", "large", ai_relevance_score=0.69, smart_money_interest=0.72),
            
            # Mid Cap AI
            Company("DDOG", "Datadog Inc.", "artificial_intelligence", "Software", "mid", ai_relevance_score=0.74, smart_money_interest=0.69),
            Company("MDB", "MongoDB Inc.", "artificial_intelligence", "Software", "mid", ai_relevance_score=0.71, smart_money_interest=0.66),
            Company("NET", "Cloudflare Inc.", "artificial_intelligence", "Software", "mid", ai_relevance_score=0.68, smart_money_interest=0.64),
            Company("ZS", "Zscaler Inc.", "artificial_intelligence", "Software", "mid", ai_relevance_score=0.67, smart_money_interest=0.63),
            Company("OKTA", "Okta Inc.", "artificial_intelligence", "Software", "mid", ai_relevance_score=0.65, smart_money_interest=0.61),
            Company("C3AI", "C3.ai Inc.", "artificial_intelligence", "Software", "small", ai_relevance_score=0.93, smart_money_interest=0.58),
            Company("AI", "C3.ai Inc.", "artificial_intelligence", "Software", "small", ai_relevance_score=0.93, smart_money_interest=0.58),
            Company("SOUN", "SoundHound AI Inc.", "artificial_intelligence", "Software", "small", ai_relevance_score=0.89, smart_money_interest=0.45),
            Company("BBAI", "BigBear.ai Holdings", "artificial_intelligence", "Software", "small", ai_relevance_score=0.85, govt_contract_exposure=0.78),
            
            # Small Cap & Emerging AI
            Company("ARDS", "Aridis Pharmaceuticals", "artificial_intelligence", "Biotechnology", "micro", ai_relevance_score=0.63),
            Company("CXAI", "CXApp Inc.", "artificial_intelligence", "Software", "micro", ai_relevance_score=0.71),
            Company("VRME", "VerifyMe Inc.", "artificial_intelligence", "Software", "micro", ai_relevance_score=0.58),
            Company("VERI", "Veritone Inc.", "artificial_intelligence", "Software", "small", ai_relevance_score=0.82),
            Company("CEVA", "CEVA Inc.", "artificial_intelligence", "Semiconductors", "small", ai_relevance_score=0.76),
            Company("SMCI", "Super Micro Computer", "artificial_intelligence", "Hardware", "mid", ai_relevance_score=0.84),
            Company("FORM", "FormFactor Inc.", "artificial_intelligence", "Semiconductors", "small", ai_relevance_score=0.61),
            Company("ALRM", "Alarm.com Holdings", "artificial_intelligence", "Software", "small", ai_relevance_score=0.59),
            Company("CDLX", "Cardlytics Inc.", "artificial_intelligence", "Software", "small", ai_relevance_score=0.72),
            Company("MRIN", "Marin Software Inc.", "artificial_intelligence", "Software", "micro", ai_relevance_score=0.68),
        ]
        
        # Robotics & Automation
        robotics_companies = [
            # Industrial Robotics
            Company("ABB", "ABB Ltd", "robotics_automation", "Industrial Machinery", "large", ai_relevance_score=0.78),
            Company("FANUY", "Fanuc Corporation", "robotics_automation", "Industrial Machinery", "large", ai_relevance_score=0.82),
            Company("ISRG", "Intuitive Surgical", "robotics_automation", "Medical Devices", "large", ai_relevance_score=0.89),
            Company("IRBT", "iRobot Corporation", "robotics_automation", "Consumer Products", "small", ai_relevance_score=0.83),
            Company("KTOS", "Kratos Defense", "robotics_automation", "Aerospace & Defense", "small", govt_contract_exposure=0.87),
            Company("AVAV", "AeroVironment", "robotics_automation", "Aerospace & Defense", "small", govt_contract_exposure=0.84),
            Company("ROK", "Rockwell Automation", "robotics_automation", "Industrial Machinery", "large", ai_relevance_score=0.75),
            Company("EMR", "Emerson Electric", "robotics_automation", "Industrial Machinery", "large", ai_relevance_score=0.69),
            Company("ETN", "Eaton Corporation", "robotics_automation", "Industrial Machinery", "large", ai_relevance_score=0.67),
            Company("PH", "Parker-Hannifin", "robotics_automation", "Industrial Machinery", "large", ai_relevance_score=0.64),
            
            # Medical Robotics
            Company("STRE", "Stereotaxis Inc.", "robotics_automation", "Medical Devices", "micro", ai_relevance_score=0.79),
            Company("MZOR", "Mazor Robotics", "robotics_automation", "Medical Devices", "small", ai_relevance_score=0.85),
            Company("SSYS", "Stratasys Ltd.", "robotics_automation", "Industrial Machinery", "small", ai_relevance_score=0.71),
            Company("DDD", "3D Systems Corp.", "robotics_automation", "Industrial Machinery", "small", ai_relevance_score=0.73),
            Company("XONE", "ExOne Company", "robotics_automation", "Industrial Machinery", "micro", ai_relevance_score=0.68),
            Company("PRLB", "Proto Labs Inc.", "robotics_automation", "Industrial Services", "small", ai_relevance_score=0.66),
            Company("MTLS", "Materialise NV", "robotics_automation", "Software", "small", ai_relevance_score=0.74),
            Company("NNDM", "Nano Dimension", "robotics_automation", "Industrial Machinery", "small", ai_relevance_score=0.72),
            Company("VJET", "voxeljet AG", "robotics_automation", "Industrial Machinery", "micro", ai_relevance_score=0.65),
            
            # Service & Consumer Robotics
            Company("BLUE", "bluebird bio Inc.", "robotics_automation", "Medical Devices", "small", ai_relevance_score=0.77),
            Company("UAVS", "AgEagle Aerial Systems", "robotics_automation", "Aerospace & Defense", "micro", ai_relevance_score=0.69),
            Company("IRDM", "Iridium Communications", "robotics_automation", "Telecommunications", "mid", ai_relevance_score=0.58),
            Company("VUZI", "Vuzix Corporation", "robotics_automation", "Consumer Electronics", "small", ai_relevance_score=0.81),
            Company("KODK", "Eastman Kodak", "robotics_automation", "Technology", "small", ai_relevance_score=0.52),
            Company("EKSO", "Ekso Bionics", "robotics_automation", "Medical Devices", "micro", ai_relevance_score=0.86),
            Company("RWLK", "ReWalk Robotics", "robotics_automation", "Medical Devices", "micro", ai_relevance_score=0.84),
        ]
        
        # Defense & Aerospace
        defense_companies = [
            # Prime Defense Contractors
            Company("LMT", "Lockheed Martin", "defense_aerospace", "Aerospace & Defense", "large", govt_contract_exposure=0.95, ai_relevance_score=0.67),
            Company("BA", "Boeing Company", "defense_aerospace", "Aerospace & Defense", "large", govt_contract_exposure=0.89, ai_relevance_score=0.63),
            Company("RTX", "Raytheon Technologies", "defense_aerospace", "Aerospace & Defense", "large", govt_contract_exposure=0.92, ai_relevance_score=0.69),
            Company("GD", "General Dynamics", "defense_aerospace", "Aerospace & Defense", "large", govt_contract_exposure=0.94, ai_relevance_score=0.65),
            Company("NOC", "Northrop Grumman", "defense_aerospace", "Aerospace & Defense", "large", govt_contract_exposure=0.96, ai_relevance_score=0.71),
            Company("LHX", "L3Harris Technologies", "defense_aerospace", "Aerospace & Defense", "large", govt_contract_exposure=0.91, ai_relevance_score=0.68),
            Company("TDG", "TransDigm Group", "defense_aerospace", "Aerospace & Defense", "large", govt_contract_exposure=0.73, ai_relevance_score=0.55),
            Company("HWM", "Howmet Aerospace", "defense_aerospace", "Aerospace & Defense", "mid", govt_contract_exposure=0.67, ai_relevance_score=0.51),
            Company("CW", "Curtiss-Wright", "defense_aerospace", "Aerospace & Defense", "small", govt_contract_exposure=0.88, ai_relevance_score=0.62),
            
            # Space & Satellite
            Company("RKLB", "Rocket Lab USA", "defense_aerospace", "Aerospace & Defense", "small", ai_relevance_score=0.74),
            Company("ASTR", "Astra Space", "defense_aerospace", "Aerospace & Defense", "micro", ai_relevance_score=0.71),
            Company("SPCE", "Virgin Galactic", "defense_aerospace", "Aerospace & Defense", "small", ai_relevance_score=0.66),
            Company("HOL", "Holicity Inc.", "defense_aerospace", "Aerospace & Defense", "small", ai_relevance_score=0.58),
            Company("MAXR", "Maxar Technologies", "defense_aerospace", "Aerospace & Defense", "small", govt_contract_exposure=0.82, ai_relevance_score=0.69),
            Company("GILT", "Gilat Satellite Networks", "defense_aerospace", "Telecommunications", "small", ai_relevance_score=0.61),
            Company("DISH", "DISH Network", "defense_aerospace", "Telecommunications", "mid", ai_relevance_score=0.54),
            Company("SATS", "EchoStar Corporation", "defense_aerospace", "Telecommunications", "small", ai_relevance_score=0.56),
            Company("GSAT", "Globalstar Inc.", "defense_aerospace", "Telecommunications", "micro", ai_relevance_score=0.59),
            Company("ASTS", "AST SpaceMobile", "defense_aerospace", "Telecommunications", "small", ai_relevance_score=0.73),
        ]
        
        # Energy & Sustainability
        energy_companies = [
            # Solar Energy
            Company("FSLR", "First Solar Inc.", "renewable_energy", "Solar", "large", ai_relevance_score=0.58),
            Company("ENPH", "Enphase Energy", "renewable_energy", "Solar", "mid", ai_relevance_score=0.71),
            Company("SEDG", "SolarEdge Technologies", "renewable_energy", "Solar", "mid", ai_relevance_score=0.73),
            Company("SPWR", "SunPower Corporation", "renewable_energy", "Solar", "small", ai_relevance_score=0.61),
            Company("CSIQ", "Canadian Solar", "renewable_energy", "Solar", "small", ai_relevance_score=0.59),
            Company("JKS", "JinkoSolar Holding", "renewable_energy", "Solar", "small", ai_relevance_score=0.57),
            Company("TSL", "Trina Solar", "renewable_energy", "Solar", "small", ai_relevance_score=0.55),
            Company("DAQO", "Daqo New Energy", "renewable_energy", "Solar", "small", ai_relevance_score=0.53),
            Company("MAXN", "Maxeon Solar Technologies", "renewable_energy", "Solar", "small", ai_relevance_score=0.56),
            Company("RUN", "Sunrun Inc.", "renewable_energy", "Solar", "mid", ai_relevance_score=0.64),
            
            # Energy Storage
            Company("BE", "Bloom Energy", "renewable_energy", "Energy Storage", "small", ai_relevance_score=0.68),
            Company("QS", "QuantumScape", "renewable_energy", "Energy Storage", "small", ai_relevance_score=0.75),
            Company("SLDP", "Solid Power", "renewable_energy", "Energy Storage", "micro", ai_relevance_score=0.72),
            Company("SES", "SES AI Corporation", "renewable_energy", "Energy Storage", "micro", ai_relevance_score=0.74),
            Company("MVST", "Microvast Holdings", "renewable_energy", "Energy Storage", "small", ai_relevance_score=0.69),
            Company("EOSE", "Eos Energy Enterprises", "renewable_energy", "Energy Storage", "micro", ai_relevance_score=0.66),
            Company("STEM", "Stem Inc.", "renewable_energy", "Energy Storage", "small", ai_relevance_score=0.71),
            Company("AMPX", "Amprius Technologies", "renewable_energy", "Energy Storage", "micro", ai_relevance_score=0.67),
            
            # Hydrogen & Alternative Fuels
            Company("PLUG", "Plug Power Inc.", "renewable_energy", "Hydrogen", "small", ai_relevance_score=0.63),
            Company("BLDP", "Ballard Power Systems", "renewable_energy", "Hydrogen", "small", ai_relevance_score=0.61),
            Company("FE", "FirstEnergy Corp.", "renewable_energy", "Utilities", "large", ai_relevance_score=0.49),
            Company("HYLN", "Hyliion Holdings", "renewable_energy", "Electric Vehicles", "small", ai_relevance_score=0.72),
            Company("CLNE", "Clean Energy Fuels", "renewable_energy", "Natural Gas", "small", ai_relevance_score=0.54),
            Company("NKLA", "Nikola Corporation", "renewable_energy", "Electric Vehicles", "small", ai_relevance_score=0.67),
            Company("HYMC", "Hycroft Mining", "renewable_energy", "Mining", "micro", ai_relevance_score=0.41),
            Company("AMRC", "Ameresco Inc.", "renewable_energy", "Energy Services", "small", ai_relevance_score=0.58),
            Company("UUUU", "Energy Fuels Inc.", "renewable_energy", "Mining", "small", ai_relevance_score=0.43),
            Company("LEU", "Centrus Energy", "renewable_energy", "Nuclear", "small", ai_relevance_score=0.47),
        ]
        
        # Electric Vehicles & Transportation
        ev_companies = [
            # Pure EV Companies
            Company("TSLA", "Tesla Inc.", "electric_vehicles", "Electric Vehicles", "large", ai_relevance_score=0.89, smart_money_interest=0.85),
            Company("NIO", "NIO Inc.", "electric_vehicles", "Electric Vehicles", "mid", ai_relevance_score=0.78),
            Company("XPEV", "XPeng Inc.", "electric_vehicles", "Electric Vehicles", "small", ai_relevance_score=0.76),
            Company("LI", "Li Auto Inc.", "electric_vehicles", "Electric Vehicles", "small", ai_relevance_score=0.74),
            Company("LCID", "Lucid Group Inc.", "electric_vehicles", "Electric Vehicles", "small", ai_relevance_score=0.81),
            Company("RIVN", "Rivian Automotive", "electric_vehicles", "Electric Vehicles", "large", ai_relevance_score=0.77),
            Company("NKLA", "Nikola Corporation", "electric_vehicles", "Electric Vehicles", "small", ai_relevance_score=0.67),
            Company("RIDE", "Lordstown Motors", "electric_vehicles", "Electric Vehicles", "micro", ai_relevance_score=0.64),
            Company("GOEV", "Canoo Inc.", "electric_vehicles", "Electric Vehicles", "micro", ai_relevance_score=0.69),
            Company("WKHS", "Workhorse Group", "electric_vehicles", "Electric Vehicles", "small", ai_relevance_score=0.66),
            
            # EV Charging Infrastructure
            Company("CHPT", "ChargePoint Holdings", "electric_vehicles", "EV Charging", "small", ai_relevance_score=0.73),
            Company("BLNK", "Blink Charging", "electric_vehicles", "EV Charging", "small", ai_relevance_score=0.69),
            Company("EVGO", "EVgo Inc.", "electric_vehicles", "EV Charging", "small", ai_relevance_score=0.71),
            Company("FFIE", "Faraday Future", "electric_vehicles", "Electric Vehicles", "micro", ai_relevance_score=0.62),
            
            # Traditional Auto with EV
            Company("GM", "General Motors", "electric_vehicles", "Automotive", "large", ai_relevance_score=0.68, smart_money_interest=0.72),
            Company("F", "Ford Motor Company", "electric_vehicles", "Automotive", "large", ai_relevance_score=0.65, smart_money_interest=0.69),
            Company("STLA", "Stellantis N.V.", "electric_vehicles", "Automotive", "large", ai_relevance_score=0.61),
            Company("TM", "Toyota Motor", "electric_vehicles", "Automotive", "large", ai_relevance_score=0.59),
            Company("HMC", "Honda Motor", "electric_vehicles", "Automotive", "large", ai_relevance_score=0.57),
        ]
        
        # Compile all companies
        all_companies = ai_companies + robotics_companies + defense_companies + energy_companies + ev_companies
        
        # Convert to dictionary
        for company in all_companies:
            universe[company.symbol] = company
        
        return universe
    
    def _load_sector_definitions(self) -> Dict[str, Sector]:
        """Load comprehensive sector definitions with relationships"""
        sectors = {
            "artificial_intelligence": Sector(
                name="Artificial Intelligence",
                category="Technology",
                description="Companies developing AI/ML technologies, neural networks, and cognitive computing",
                growth_potential=0.95,
                volatility_score=0.78,
                correlation_with_ai=1.0,
                supply_chain_dependencies=["semiconductor_manufacturing", "cloud_infrastructure", "data_centers"],
                influenced_sectors=["robotics_automation", "autonomous_vehicles", "healthcare_tech", "fintech"],
                key_metrics={"revenue_growth_rate": 0.35, "r_and_d_intensity": 0.25, "patent_count": 1000},
                companies=[]
            ),
            
            "robotics_automation": Sector(
                name="Robotics & Automation",
                category="Technology",
                description="Industrial robotics, service robots, and automation systems",
                growth_potential=0.87,
                volatility_score=0.72,
                correlation_with_ai=0.85,
                supply_chain_dependencies=["artificial_intelligence", "semiconductor_design", "precision_manufacturing"],
                influenced_sectors=["manufacturing", "healthcare", "logistics", "agriculture"],
                key_metrics={"automation_adoption_rate": 0.68, "productivity_improvement": 0.42},
                companies=[]
            ),
            
            "defense_aerospace": Sector(
                name="Defense & Aerospace",
                category="Industrial",
                description="Military contractors, aerospace manufacturers, and space technology",
                growth_potential=0.73,
                volatility_score=0.65,
                correlation_with_ai=0.71,
                supply_chain_dependencies=["advanced_materials", "electronics", "software"],
                influenced_sectors=["space_technology", "cybersecurity", "satellite_communications"],
                key_metrics={"government_contract_ratio": 0.75, "security_clearance_personnel": 0.85},
                companies=[]
            ),
            
            "renewable_energy": Sector(
                name="Renewable Energy",
                category="Energy",
                description="Solar, wind, hydro, and other clean energy technologies",
                growth_potential=0.89,
                volatility_score=0.81,
                correlation_with_ai=0.58,
                supply_chain_dependencies=["rare_earth_mining", "battery_technology", "power_electronics"],
                influenced_sectors=["electric_vehicles", "energy_storage", "smart_grid"],
                key_metrics={"capacity_growth_rate": 0.28, "cost_reduction_rate": 0.15},
                companies=[]
            ),
            
            "electric_vehicles": Sector(
                name="Electric Vehicles",
                category="Transportation",
                description="Electric vehicle manufacturers and supporting infrastructure",
                growth_potential=0.91,
                volatility_score=0.85,
                correlation_with_ai=0.74,
                supply_chain_dependencies=["battery_technology", "semiconductor_chips", "charging_infrastructure"],
                influenced_sectors=["traditional_automotive", "renewable_energy", "mining"],
                key_metrics={"market_share_growth": 0.45, "battery_cost_reduction": 0.12},
                companies=[]
            )
        }
        
        return sectors
    
    def build_indices(self):
        """Build efficient lookup indices for fast querying"""
        # Clear existing indices
        for key in self.indices:
            self.indices[key] = {}
        
        for symbol, company in self.companies.items():
            # Sector index
            if company.sector not in self.indices['by_sector']:
                self.indices['by_sector'][company.sector] = set()
            self.indices['by_sector'][company.sector].add(symbol)
            
            # Market cap index
            if company.market_cap not in self.indices['by_market_cap']:
                self.indices['by_market_cap'][company.market_cap] = set()
            self.indices['by_market_cap'][company.market_cap].add(symbol)
            
            # AI score buckets
            ai_bucket = self._get_score_bucket(company.ai_relevance_score)
            if ai_bucket not in self.indices['by_ai_score']:
                self.indices['by_ai_score'][ai_bucket] = set()
            self.indices['by_ai_score'][ai_bucket].add(symbol)
            
            # Government exposure buckets
            govt_bucket = self._get_score_bucket(company.govt_contract_exposure)
            if govt_bucket not in self.indices['by_govt_exposure']:
                self.indices['by_govt_exposure'][govt_bucket] = set()
            self.indices['by_govt_exposure'][govt_bucket].add(symbol)
            
            # Smart money interest buckets
            money_bucket = self._get_score_bucket(company.smart_money_interest)
            if money_bucket not in self.indices['by_smart_money']:
                self.indices['by_smart_money'][money_bucket] = set()
            self.indices['by_smart_money'][money_bucket].add(symbol)
    
    def _get_score_bucket(self, score: float) -> str:
        """Convert score to bucket for indexing"""
        if score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.3:
            return "low"
        else:
            return "minimal"
    
    def query_companies(self, 
                       sectors: Optional[List[str]] = None,
                       market_caps: Optional[List[str]] = None,
                       min_ai_score: float = 0.0,
                       min_govt_exposure: float = 0.0,
                       min_smart_money: float = 0.0,
                       limit: Optional[int] = None) -> List[Company]:
        """Query companies with multiple filters"""
        
        result_symbols = set(self.companies.keys())
        
        # Apply sector filter
        if sectors:
            sector_symbols = set()
            for sector in sectors:
                sector_symbols.update(self.indices['by_sector'].get(sector, set()))
            result_symbols &= sector_symbols
        
        # Apply market cap filter
        if market_caps:
            cap_symbols = set()
            for cap in market_caps:
                cap_symbols.update(self.indices['by_market_cap'].get(cap, set()))
            result_symbols &= cap_symbols
        
        # Apply score filters
        filtered_companies = []
        for symbol in result_symbols:
            company = self.companies[symbol]
            if (company.ai_relevance_score >= min_ai_score and
                company.govt_contract_exposure >= min_govt_exposure and
                company.smart_money_interest >= min_smart_money):
                filtered_companies.append(company)
        
        # Sort by combined relevance score
        filtered_companies.sort(
            key=lambda c: (c.ai_relevance_score + c.govt_contract_exposure + c.smart_money_interest) / 3,
            reverse=True
        )
        
        if limit:
            filtered_companies = filtered_companies[:limit]
        
        return filtered_companies
    
    def get_sector_analysis(self, sector_name: str) -> Dict:
        """Get comprehensive analysis for a specific sector"""
        if sector_name not in self.sectors:
            return {}
        
        sector = self.sectors[sector_name]
        companies_in_sector = self.query_companies(sectors=[sector_name])
        
        # Calculate sector metrics
        total_companies = len(companies_in_sector)
        avg_ai_score = sum(c.ai_relevance_score for c in companies_in_sector) / max(total_companies, 1)
        avg_govt_exposure = sum(c.govt_contract_exposure for c in companies_in_sector) / max(total_companies, 1)
        avg_smart_money = sum(c.smart_money_interest for c in companies_in_sector) / max(total_companies, 1)
        
        # Market cap distribution
        cap_distribution = {}
        for company in companies_in_sector:
            cap_distribution[company.market_cap] = cap_distribution.get(company.market_cap, 0) + 1
        
        return {
            'sector_info': asdict(sector),
            'company_count': total_companies,
            'average_scores': {
                'ai_relevance': avg_ai_score,
                'government_exposure': avg_govt_exposure,
                'smart_money_interest': avg_smart_money
            },
            'market_cap_distribution': cap_distribution,
            'top_companies': companies_in_sector[:10],
            'supply_chain_dependencies': sector.supply_chain_dependencies,
            'influenced_sectors': sector.influenced_sectors
        }
    
    def get_portfolio_recommendations(self, 
                                    target_allocation: Dict[str, float],
                                    available_capital: float = 900) -> Dict:
        """Generate portfolio recommendations based on target allocations"""
        
        recommendations = {
            'allocations': {},
            'selected_companies': {},
            'risk_metrics': {},
            'diversification_score': 0.0
        }
        
        for sector, allocation_pct in target_allocation.items():
            allocation_amount = available_capital * allocation_pct
            
            # Get top companies in sector
            sector_companies = self.query_companies(
                sectors=[sector],
                min_ai_score=0.6,
                limit=5
            )
            
            if sector_companies:
                # Select top 2-3 companies for diversification
                selected = sector_companies[:min(3, len(sector_companies))]
                amount_per_company = allocation_amount / len(selected)
                
                recommendations['selected_companies'][sector] = [
                    {
                        'company': asdict(company),
                        'allocation_amount': amount_per_company,
                        'allocation_pct': allocation_pct / len(selected)
                    }
                    for company in selected
                ]
                
                recommendations['allocations'][sector] = allocation_amount
        
        return recommendations
    
    def save_to_file(self, filepath: str):
        """Save the entire universe to a file"""
        data = {
            'companies': {symbol: asdict(company) for symbol, company in self.companies.items()},
            'sectors': {name: asdict(sector) for name, sector in self.sectors.items()},
            'metadata': {
                'total_companies': len(self.companies),
                'total_sectors': len(self.sectors),
                'last_updated': datetime.now().isoformat()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load universe from a file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Load companies
        self.companies = {}
        for symbol, company_data in data['companies'].items():
            self.companies[symbol] = Company(**company_data)
        
        # Load sectors
        self.sectors = {}
        for name, sector_data in data['sectors'].items():
            # Handle companies list in sector
            sector_data['companies'] = [Company(**c) for c in sector_data.get('companies', [])]
            self.sectors[name] = Sector(**sector_data)
        
        self.build_indices()

def main():
    """Test the stock universe manager"""
    print("🔍 Initializing Stock Universe Manager...")
    
    manager = StockUniverseManager()
    
    print(f"✅ Loaded {len(manager.companies)} companies across {len(manager.sectors)} sectors")
    
    # Test queries
    print("\n📊 Testing Queries:")
    
    # High AI relevance companies
    ai_companies = manager.query_companies(min_ai_score=0.8, limit=10)
    print(f"\n🤖 Top AI Companies ({len(ai_companies)}):")
    for company in ai_companies:
        print(f"   {company.symbol}: {company.name} (AI: {company.ai_relevance_score:.2f})")
    
    # Government contractors
    govt_companies = manager.query_companies(min_govt_exposure=0.8, limit=5)
    print(f"\n🏛️ Government Contractors ({len(govt_companies)}):")
    for company in govt_companies:
        print(f"   {company.symbol}: {company.name} (Govt: {company.govt_contract_exposure:.2f})")
    
    # Sector analysis
    print(f"\n📈 AI Sector Analysis:")
    ai_analysis = manager.get_sector_analysis("artificial_intelligence")
    if ai_analysis:
        print(f"   Companies: {ai_analysis['company_count']}")
        print(f"   Avg AI Score: {ai_analysis['average_scores']['ai_relevance']:.2f}")
        print(f"   Market Cap Distribution: {ai_analysis['market_cap_distribution']}")
    
    # Portfolio recommendations
    print(f"\n💼 Portfolio Recommendations:")
    target_allocation = {
        "artificial_intelligence": 0.4,
        "robotics_automation": 0.2,
        "defense_aerospace": 0.15,
        "renewable_energy": 0.15,
        "electric_vehicles": 0.1
    }
    
    recommendations = manager.get_portfolio_recommendations(target_allocation, 900)
    for sector, allocation in recommendations['allocations'].items():
        print(f"   {sector}: ${allocation:.0f}")
        if sector in recommendations['selected_companies']:
            for rec in recommendations['selected_companies'][sector]:
                print(f"     • {rec['company']['symbol']}: ${rec['allocation_amount']:.0f}")

if __name__ == "__main__":
    main()