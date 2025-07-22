"""
Investment Blacklist System
Screens investments against ethical, environmental, and social criteria
"""

import json
import logging
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class BlacklistCategory(Enum):
    CONTROVERSIAL_LEADERSHIP = "controversial_leadership"
    ENVIRONMENTAL_DAMAGE = "environmental_damage"
    HUMAN_RIGHTS_VIOLATIONS = "human_rights_violations"
    UNETHICAL_BUSINESS_PRACTICES = "unethical_business_practices"
    POLITICAL_EXTREMISM = "political_extremism"
    LABOR_EXPLOITATION = "labor_exploitation"
    ANIMAL_CRUELTY = "animal_cruelty"
    HARMFUL_PRODUCTS = "harmful_products"
    CORRUPTION = "corruption"
    MILITARY_WEAPONS = "military_weapons"
    FOSSIL_FUELS = "fossil_fuels"
    PRIVACY_VIOLATIONS = "privacy_violations"
    CLIMATE_DENIAL = "climate_denial"
    BIODIVERSITY_DESTRUCTION = "biodiversity_destruction"
    WATER_POLLUTION = "water_pollution"
    PLASTIC_POLLUTION = "plastic_pollution"

class WhitelistCategory(Enum):
    RENEWABLE_ENERGY = "renewable_energy"
    CLEAN_TECHNOLOGY = "clean_technology"
    SUSTAINABLE_AGRICULTURE = "sustainable_agriculture"
    ELECTRIC_VEHICLES = "electric_vehicles"
    ENERGY_STORAGE = "energy_storage"
    WATER_CONSERVATION = "water_conservation"
    WASTE_MANAGEMENT = "waste_management"
    CARBON_CAPTURE = "carbon_capture"
    GREEN_BUILDINGS = "green_buildings"
    OCEAN_PRESERVATION = "ocean_preservation"
    FOREST_CONSERVATION = "forest_conservation"
    BIODIVERSITY_PROTECTION = "biodiversity_protection"
    SUSTAINABLE_MATERIALS = "sustainable_materials"
    ENVIRONMENTAL_MONITORING = "environmental_monitoring"
    CLIMATE_ADAPTATION = "climate_adaptation"

class SeverityLevel(Enum):
    LOW = 1          # Minor concerns, monitor
    MEDIUM = 2       # Significant concerns, reduce exposure
    HIGH = 3         # Major concerns, avoid investment
    CRITICAL = 4     # Complete ban, zero tolerance

class PriorityLevel(Enum):
    STANDARD = 1     # Normal investment consideration
    PREFERRED = 2    # Favored for ethical reasons
    PRIORITY = 3     # Strongly preferred for impact
    MISSION_CRITICAL = 4  # Essential for earth preservation

@dataclass
class BlacklistEntry:
    symbol: str
    company_name: str
    category: str
    severity: int
    reason: str
    sources: List[str]
    leadership_concerns: List[str]
    added_date: str
    last_updated: str
    notes: str = ""
    
    def __post_init__(self):
        if not self.added_date:
            self.added_date = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

@dataclass
class WhitelistEntry:
    symbol: str
    company_name: str
    category: str
    priority: int
    reason: str
    impact_areas: List[str]
    esg_score: float
    climate_commitment: str
    sources: List[str]
    added_date: str
    last_updated: str
    notes: str = ""
    
    def __post_init__(self):
        if not self.added_date:
            self.added_date = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

class InvestmentBlacklistManager:
    """Manages ethical investment screening and blacklist enforcement"""
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.blacklist: Dict[str, BlacklistEntry] = {}
        self.green_whitelist: Dict[str, WhitelistEntry] = {}  # Priority green/sustainable companies
        self.standard_whitelist: Set[str] = set()  # Explicitly approved companies
        self.watchlist: Dict[str, str] = {}  # Companies to monitor
        
        # Load predefined blacklists and whitelists
        self.load_blacklist_data()
        self.load_green_whitelist_data()
        
    def load_blacklist_data(self):
        """Load comprehensive blacklist data"""
        
        # Controversial Leadership
        controversial_leaders = [
            BlacklistEntry(
                symbol="TSLA",
                company_name="Tesla Inc.",
                category=BlacklistCategory.CONTROVERSIAL_LEADERSHIP.value,
                severity=SeverityLevel.HIGH.value,
                reason="Elon Musk - Market manipulation, erratic behavior, controversial statements",
                sources=["SEC filings", "Twitter/X posts", "Court records"],
                leadership_concerns=["Market manipulation tweets", "Pump and dump schemes", "Political extremism", "Worker rights violations"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="CEO with history of market manipulation and controversial statements affecting stock price"
            ),
            
            BlacklistEntry(
                symbol="DWAC",
                company_name="Digital World Acquisition Corp",
                category=BlacklistCategory.POLITICAL_EXTREMISM.value,
                severity=SeverityLevel.CRITICAL.value,
                reason="Trump-affiliated SPAC for Truth Social platform",
                sources=["SEC filings", "News reports"],
                leadership_concerns=["Donald Trump affiliation", "January 6th involvement", "Election fraud claims"],
                added_date="2023-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="SPAC associated with Donald Trump and Truth Social platform"
            ),
            
            BlacklistEntry(
                symbol="TWTR",
                company_name="Twitter Inc. (Pre-Musk)",
                category=BlacklistCategory.CONTROVERSIAL_LEADERSHIP.value,
                severity=SeverityLevel.HIGH.value,
                reason="Elon Musk takeover, content moderation changes, worker rights issues",
                sources=["News reports", "Employee testimonials"],
                leadership_concerns=["Mass layoffs", "Content moderation rollback", "Platform manipulation"],
                added_date="2022-10-27T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Post-Musk acquisition concerns about platform direction and employee treatment"
            )
        ]
        
        # Environmental Damage
        environmental_offenders = [
            BlacklistEntry(
                symbol="XOM",
                company_name="Exxon Mobil Corporation",
                category=BlacklistCategory.ENVIRONMENTAL_DAMAGE.value,
                severity=SeverityLevel.HIGH.value,
                reason="Climate change denial, environmental destruction, lobbying against clean energy",
                sources=["Environmental studies", "Internal documents", "Scientific reports"],
                leadership_concerns=["Climate change denial", "Greenwashing", "Lobbying against climate action"],
                added_date="2020-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Major fossil fuel company with history of climate change denial"
            ),
            
            BlacklistEntry(
                symbol="CVX",
                company_name="Chevron Corporation",
                category=BlacklistCategory.ENVIRONMENTAL_DAMAGE.value,
                severity=SeverityLevel.HIGH.value,
                reason="Oil spills, environmental contamination, indigenous rights violations",
                sources=["Court cases", "Environmental reports"],
                leadership_concerns=["Environmental contamination", "Indigenous rights violations"],
                added_date="2020-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Oil company with multiple environmental violations"
            ),
            
            BlacklistEntry(
                symbol="BP",
                company_name="BP plc",
                category=BlacklistCategory.ENVIRONMENTAL_DAMAGE.value,
                severity=SeverityLevel.HIGH.value,
                reason="Deepwater Horizon oil spill, ongoing environmental damage",
                sources=["Court records", "Environmental assessments"],
                leadership_concerns=["Safety violations", "Environmental negligence"],
                added_date="2010-04-20T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Responsible for major environmental disaster in Gulf of Mexico"
            )
        ]
        
        # Unethical Business Practices
        unethical_companies = [
            BlacklistEntry(
                symbol="NSRGY",
                company_name="Nestlé S.A.",
                category=BlacklistCategory.UNETHICAL_BUSINESS_PRACTICES.value,
                severity=SeverityLevel.CRITICAL.value,
                reason="Water privatization, child labor, infant formula marketing in developing countries",
                sources=["UN reports", "NGO investigations", "Documentary evidence"],
                leadership_concerns=["Water rights exploitation", "Child labor in supply chain", "Predatory marketing"],
                added_date="2000-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Multiple ongoing ethical violations including water privatization and child labor"
            ),
            
            BlacklistEntry(
                symbol="META",
                company_name="Meta Platforms Inc.",
                category=BlacklistCategory.PRIVACY_VIOLATIONS.value,
                severity=SeverityLevel.HIGH.value,
                reason="Privacy violations, misinformation spread, election interference",
                sources=["Congressional hearings", "Whistleblower reports", "Academic studies"],
                leadership_concerns=["Privacy violations", "Misinformation amplification", "Election interference"],
                added_date="2018-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Significant privacy and democracy concerns"
            ),
            
            BlacklistEntry(
                symbol="WMT",
                company_name="Walmart Inc.",
                category=BlacklistCategory.LABOR_EXPLOITATION.value,
                severity=SeverityLevel.MEDIUM.value,
                reason="Worker rights violations, union busting, low wages",
                sources=["Labor reports", "Worker testimonials", "Legal cases"],
                leadership_concerns=["Anti-union practices", "Low wage policies", "Worker safety issues"],
                added_date="2005-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Ongoing labor practices concerns"
            )
        ]
        
        # Human Rights Violations
        human_rights_violators = [
            BlacklistEntry(
                symbol="BABA",
                company_name="Alibaba Group Holding",
                category=BlacklistCategory.HUMAN_RIGHTS_VIOLATIONS.value,
                severity=SeverityLevel.HIGH.value,
                reason="Complicity in Uyghur surveillance and oppression",
                sources=["Human rights reports", "Government investigations"],
                leadership_concerns=["Surveillance technology", "Oppression complicity"],
                added_date="2021-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Chinese company with ties to Uyghur oppression"
            ),
            
            BlacklistEntry(
                symbol="TCEHY",
                company_name="Tencent Holdings Limited",
                category=BlacklistCategory.HUMAN_RIGHTS_VIOLATIONS.value,
                severity=SeverityLevel.HIGH.value,
                reason="Surveillance and censorship technology for authoritarian regime",
                sources=["Human rights organizations", "Technology analysis"],
                leadership_concerns=["Surveillance technology", "Censorship tools"],
                added_date="2020-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Technology used for surveillance and oppression"
            )
        ]
        
        # Military Weapons (Optional - some may want to avoid)
        military_weapons = [
            BlacklistEntry(
                symbol="LMT",
                company_name="Lockheed Martin Corporation",
                category=BlacklistCategory.MILITARY_WEAPONS.value,
                severity=SeverityLevel.MEDIUM.value,
                reason="Weapons manufacturing for global conflicts",
                sources=["Public records", "Defense contracts"],
                leadership_concerns=["Weapons export", "Conflict profiteering"],
                added_date="2020-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Major defense contractor - optional exclusion based on personal ethics"
            ),
            
            BlacklistEntry(
                symbol="RTX",
                company_name="Raytheon Technologies",
                category=BlacklistCategory.MILITARY_WEAPONS.value,
                severity=SeverityLevel.MEDIUM.value,
                reason="Weapons systems and military technology",
                sources=["Defense contracts", "Export records"],
                leadership_concerns=["Weapons export", "Military-industrial complex"],
                added_date="2020-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Defense contractor with weapons systems"
            )
        ]
        
        # Harmful Products
        harmful_products = [
            BlacklistEntry(
                symbol="MO",
                company_name="Altria Group Inc.",
                category=BlacklistCategory.HARMFUL_PRODUCTS.value,
                severity=SeverityLevel.HIGH.value,
                reason="Tobacco products causing death and disease",
                sources=["Health studies", "Legal settlements"],
                leadership_concerns=["Health damage denial", "Addiction promotion"],
                added_date="2000-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Tobacco company with documented health harms"
            ),
            
            BlacklistEntry(
                symbol="BTI",
                company_name="British American Tobacco",
                category=BlacklistCategory.HARMFUL_PRODUCTS.value,
                severity=SeverityLevel.HIGH.value,
                reason="Tobacco products and predatory marketing",
                sources=["Health organizations", "Legal cases"],
                leadership_concerns=["Predatory marketing", "Health denial"],
                added_date="2000-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="International tobacco company"
            )
        ]
        
        # Compile all blacklist entries
        all_entries = (controversial_leaders + environmental_offenders + 
                      unethical_companies + human_rights_violators + 
                      military_weapons + harmful_products)
        
        for entry in all_entries:
            self.blacklist[entry.symbol] = entry
        
        # Load watchlist (companies to monitor but not ban)
        self.watchlist = {
            "AMZN": "Labor practices and market dominance concerns",
            "GOOGL": "Privacy and market dominance concerns", 
            "AAPL": "Labor practices in supply chain",
            "JPM": "Fossil fuel financing",
            "BAC": "Fossil fuel financing",
            "WFC": "Customer fraud scandals",
            "GS": "Wall Street practices",
            "MS": "Wall Street practices"
        }
        
        # Load standard whitelist (explicitly approved companies)
        self.standard_whitelist = {
            "BRK.B",  # Berkshire Hathaway - generally ethical
            "COST",   # Costco - good labor practices
            "JNJ",    # Johnson & Johnson - healthcare
            "PG",     # Procter & Gamble - consumer goods
            "KO",     # Coca-Cola - established consumer brand
            "PEP",    # PepsiCo - established brand
        }
    
    def load_green_whitelist_data(self):
        """Load comprehensive green technology and earth preservation whitelist"""
        
        # Renewable Energy - Solar Companies
        solar_companies = [
            WhitelistEntry(
                symbol="FSLR",
                company_name="First Solar Inc.",
                category=WhitelistCategory.RENEWABLE_ENERGY.value,
                priority=PriorityLevel.MISSION_CRITICAL.value,
                reason="Leading thin-film solar panel manufacturer with strong sustainability commitment",
                impact_areas=["Solar Energy", "Climate Change Mitigation", "Clean Manufacturing"],
                esg_score=8.5,
                climate_commitment="Net zero by 2030, sustainable manufacturing",
                sources=["Company ESG reports", "S&P Global ESG", "CDP Climate"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Industry leader in sustainable solar technology with excellent ESG practices"
            ),
            
            WhitelistEntry(
                symbol="ENPH",
                company_name="Enphase Energy Inc.",
                category=WhitelistCategory.RENEWABLE_ENERGY.value,
                priority=PriorityLevel.PRIORITY.value,
                reason="Microinverter technology enabling distributed solar energy systems",
                impact_areas=["Solar Energy", "Energy Storage", "Grid Modernization"],
                esg_score=8.2,
                climate_commitment="Carbon neutral operations, renewable energy enabler",
                sources=["Company sustainability reports", "Industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Critical technology for residential and commercial solar adoption"
            ),
            
            WhitelistEntry(
                symbol="SPWR",
                company_name="SunPower Corporation",
                category=WhitelistCategory.RENEWABLE_ENERGY.value,
                priority=PriorityLevel.PRIORITY.value,
                reason="High-efficiency solar panels and integrated solar solutions",
                impact_areas=["Solar Energy", "Residential Solar", "Commercial Solar"],
                esg_score=7.8,
                climate_commitment="Sustainable manufacturing, circular economy principles",
                sources=["Company reports", "Solar industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Premium solar technology provider with strong environmental focus"
            )
        ]
        
        # Wind Energy Companies
        wind_companies = [
            WhitelistEntry(
                symbol="VWDRY",
                company_name="Vestas Wind Systems",
                category=WhitelistCategory.RENEWABLE_ENERGY.value,
                priority=PriorityLevel.MISSION_CRITICAL.value,
                reason="Global leader in wind turbine manufacturing and installation",
                impact_areas=["Wind Energy", "Climate Change Mitigation", "Offshore Wind"],
                esg_score=9.1,
                climate_commitment="Carbon neutral by 2030, leader in sustainable wind technology",
                sources=["Company sustainability reports", "Global Wind Energy Council"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="World's largest wind turbine manufacturer with exceptional environmental leadership"
            ),
            
            WhitelistEntry(
                symbol="GE",
                company_name="General Electric Company",
                category=WhitelistCategory.RENEWABLE_ENERGY.value,
                priority=PriorityLevel.PREFERRED.value,
                reason="Major wind turbine manufacturer and renewable energy solutions",
                impact_areas=["Wind Energy", "Grid Solutions", "Energy Transition"],
                esg_score=7.5,
                climate_commitment="Carbon neutral by 2030, focus on renewable energy",
                sources=["Company ESG reports", "Industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Diversified company with significant renewable energy business"
            )
        ]
        
        # Electric Vehicle Companies (Tesla excluded due to leadership concerns)
        ev_companies = [
            WhitelistEntry(
                symbol="NIO",
                company_name="NIO Inc.",
                category=WhitelistCategory.ELECTRIC_VEHICLES.value,
                priority=PriorityLevel.PRIORITY.value,
                reason="Premium electric vehicle manufacturer with battery swapping technology",
                impact_areas=["Electric Vehicles", "Battery Technology", "Transportation Decarbonization"],
                esg_score=8.0,
                climate_commitment="Carbon neutral products and operations by 2030",
                sources=["Company sustainability reports", "EV industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Innovative EV company with strong environmental commitment"
            ),
            
            WhitelistEntry(
                symbol="RIVN",
                company_name="Rivian Automotive Inc.",
                category=WhitelistCategory.ELECTRIC_VEHICLES.value,
                priority=PriorityLevel.PRIORITY.value,
                reason="Electric vehicle manufacturer focused on sustainable transportation",
                impact_areas=["Electric Vehicles", "Sustainable Transportation", "Commercial EVs"],
                esg_score=8.3,
                climate_commitment="Carbon neutral by 2040, sustainable manufacturing",
                sources=["Company ESG reports", "Automotive industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Purpose-built for sustainability with strong environmental mission"
            ),
            
            WhitelistEntry(
                symbol="LCID",
                company_name="Lucid Group Inc.",
                category=WhitelistCategory.ELECTRIC_VEHICLES.value,
                priority=PriorityLevel.PREFERRED.value,
                reason="Luxury electric vehicle manufacturer with advanced battery technology",
                impact_areas=["Electric Vehicles", "Battery Efficiency", "Luxury EV Market"],
                esg_score=7.9,
                climate_commitment="Sustainable manufacturing, efficient EV technology",
                sources=["Company reports", "EV technology analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="High-efficiency electric vehicles with strong technology focus"
            )
        ]
        
        # Energy Storage Companies
        energy_storage = [
            WhitelistEntry(
                symbol="EOSE",
                company_name="Eos Energy Enterprises",
                category=WhitelistCategory.ENERGY_STORAGE.value,
                priority=PriorityLevel.MISSION_CRITICAL.value,
                reason="Grid-scale battery storage solutions enabling renewable energy integration",
                impact_areas=["Energy Storage", "Grid Stability", "Renewable Integration"],
                esg_score=8.7,
                climate_commitment="Enabling renewable energy transition through storage",
                sources=["Company reports", "Energy storage industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Critical technology for renewable energy grid integration"
            ),
            
            WhitelistEntry(
                symbol="NKLA",
                company_name="Nikola Corporation",
                category=WhitelistCategory.CLEAN_TECHNOLOGY.value,
                priority=PriorityLevel.PREFERRED.value,
                reason="Hydrogen fuel cell and battery electric commercial vehicles",
                impact_areas=["Hydrogen Technology", "Commercial Transportation", "Zero Emissions"],
                esg_score=7.6,
                climate_commitment="Zero emission transportation solutions",
                sources=["Company sustainability reports", "Hydrogen industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Focus on hydrogen and electric commercial vehicle solutions"
            )
        ]
        
        # Water Conservation and Management
        water_companies = [
            WhitelistEntry(
                symbol="AWK",
                company_name="American Water Works",
                category=WhitelistCategory.WATER_CONSERVATION.value,
                priority=PriorityLevel.PRIORITY.value,
                reason="Water utility focused on conservation and sustainable water management",
                impact_areas=["Water Conservation", "Infrastructure", "Sustainable Utilities"],
                esg_score=8.1,
                climate_commitment="Water conservation, climate resilient infrastructure",
                sources=["Company ESG reports", "Water industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Leading water utility with strong conservation focus"
            ),
            
            WhitelistEntry(
                symbol="XYL",
                company_name="Xylem Inc.",
                category=WhitelistCategory.WATER_CONSERVATION.value,
                priority=PriorityLevel.MISSION_CRITICAL.value,
                reason="Water technology solutions for conservation and treatment",
                impact_areas=["Water Technology", "Conservation", "Water Treatment"],
                esg_score=8.9,
                climate_commitment="Water security and sustainability solutions",
                sources=["Company sustainability reports", "Water technology analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Critical water technology solutions for global water challenges"
            )
        ]
        
        # Waste Management and Circular Economy
        waste_management = [
            WhitelistEntry(
                symbol="WM",
                company_name="Waste Management Inc.",
                category=WhitelistCategory.WASTE_MANAGEMENT.value,
                priority=PriorityLevel.PREFERRED.value,
                reason="Leading waste management company with recycling and renewable energy focus",
                impact_areas=["Waste Management", "Recycling", "Renewable Energy from Waste"],
                esg_score=7.8,
                climate_commitment="Circular economy, waste-to-energy solutions",
                sources=["Company ESG reports", "Waste management industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Large-scale waste management with sustainability focus"
            ),
            
            WhitelistEntry(
                symbol="RSG",
                company_name="Republic Services Inc.",
                category=WhitelistCategory.WASTE_MANAGEMENT.value,
                priority=PriorityLevel.PREFERRED.value,
                reason="Waste management and recycling services with environmental focus",
                impact_areas=["Waste Management", "Recycling", "Environmental Services"],
                esg_score=7.7,
                climate_commitment="Circular economy principles, sustainable waste solutions",
                sources=["Company reports", "Industry sustainability analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Comprehensive waste management with recycling emphasis"
            )
        ]
        
        # Sustainable Agriculture and Food
        agriculture_companies = [
            WhitelistEntry(
                symbol="DE",
                company_name="Deere & Company",
                category=WhitelistCategory.SUSTAINABLE_AGRICULTURE.value,
                priority=PriorityLevel.PRIORITY.value,
                reason="Precision agriculture technology reducing environmental impact",
                impact_areas=["Precision Agriculture", "Sustainable Farming", "Agricultural Technology"],
                esg_score=8.0,
                climate_commitment="Sustainable agriculture solutions, precision farming",
                sources=["Company sustainability reports", "Agricultural technology analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Advanced agricultural technology enabling sustainable farming practices"
            )
        ]
        
        # Clean Technology ETFs and Funds
        clean_tech_etfs = [
            WhitelistEntry(
                symbol="ICLN",
                company_name="iShares Global Clean Energy ETF",
                category=WhitelistCategory.CLEAN_TECHNOLOGY.value,
                priority=PriorityLevel.MISSION_CRITICAL.value,
                reason="Diversified exposure to global clean energy companies",
                impact_areas=["Clean Energy", "Renewable Energy", "Energy Transition"],
                esg_score=9.0,
                climate_commitment="100% focus on clean energy transition",
                sources=["Fund prospectus", "ESG fund analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Primary vehicle for diversified clean energy investment"
            ),
            
            WhitelistEntry(
                symbol="QCLN",
                company_name="First Trust NASDAQ Clean Edge Green Energy Index Fund",
                category=WhitelistCategory.CLEAN_TECHNOLOGY.value,
                priority=PriorityLevel.PRIORITY.value,
                reason="Clean energy technology companies focused on environmental solutions",
                impact_areas=["Clean Technology", "Green Energy", "Environmental Innovation"],
                esg_score=8.8,
                climate_commitment="Clean energy and environmental technology focus",
                sources=["Fund analysis", "Clean technology research"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Focused on innovative clean technology companies"
            ),
            
            WhitelistEntry(
                symbol="PBW",
                company_name="Invesco WilderHill Clean Energy ETF",
                category=WhitelistCategory.CLEAN_TECHNOLOGY.value,
                priority=PriorityLevel.PRIORITY.value,
                reason="Clean energy and environmental technology companies",
                impact_areas=["Clean Energy", "Environmental Technology", "Renewable Energy"],
                esg_score=8.6,
                climate_commitment="Focus on clean energy and environmental solutions",
                sources=["ETF analysis", "Clean energy sector research"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Comprehensive clean energy and environmental technology exposure"
            )
        ]
        
        # Environmental Monitoring and Technology
        environmental_tech = [
            WhitelistEntry(
                symbol="TRMB",
                company_name="Trimble Inc.",
                category=WhitelistCategory.ENVIRONMENTAL_MONITORING.value,
                priority=PriorityLevel.PREFERRED.value,
                reason="Precision technology for agriculture, construction, and environmental monitoring",
                impact_areas=["Environmental Monitoring", "Precision Agriculture", "Sustainable Construction"],
                esg_score=7.9,
                climate_commitment="Technology enabling sustainable practices across industries",
                sources=["Company reports", "Technology industry analysis"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Technology solutions enabling environmental efficiency and monitoring"
            )
        ]
        
        # Carbon Capture and Climate Technology
        carbon_tech = [
            WhitelistEntry(
                symbol="AMZN",
                company_name="Amazon.com Inc.",
                category=WhitelistCategory.CLIMATE_ADAPTATION.value,
                priority=PriorityLevel.PREFERRED.value,
                reason="Climate Pledge commitment and renewable energy investments",
                impact_areas=["Renewable Energy", "Climate Commitment", "Sustainable Logistics"],
                esg_score=7.5,
                climate_commitment="Net zero by 2040, $10B climate fund, renewable energy leader",
                sources=["Climate Pledge", "Company sustainability reports"],
                added_date="2024-01-01T00:00:00",
                last_updated=datetime.now().isoformat(),
                notes="Major climate commitments and renewable energy investments despite other concerns"
            )
        ]
        
        # Compile all green whitelist entries
        all_green_entries = (solar_companies + wind_companies + ev_companies + 
                           energy_storage + water_companies + waste_management + 
                           agriculture_companies + clean_tech_etfs + environmental_tech + carbon_tech)
        
        for entry in all_green_entries:
            self.green_whitelist[entry.symbol] = entry
    
    def check_investment(self, symbol: str) -> Dict[str, any]:
        """Check if an investment passes ethical screening with priority scoring"""
        
        result = {
            "symbol": symbol,
            "status": "approved",  # approved, warning, blocked, priority, mission_critical
            "severity": 0,
            "priority_score": 0,
            "green_impact": False,
            "concerns": [],
            "benefits": [],
            "recommendations": [],
            "alternative_suggestions": []
        }
        
        # Check green whitelist first (highest priority)
        if symbol in self.green_whitelist:
            entry = self.green_whitelist[symbol]
            priority_level = entry.priority
            
            # Set status based on priority level
            if priority_level == PriorityLevel.MISSION_CRITICAL.value:
                result["status"] = "mission_critical"
                result["priority_score"] = 10
            elif priority_level == PriorityLevel.PRIORITY.value:
                result["status"] = "priority"
                result["priority_score"] = 8
            elif priority_level == PriorityLevel.PREFERRED.value:
                result["status"] = "preferred"
                result["priority_score"] = 6
            else:
                result["status"] = "approved"
                result["priority_score"] = 4
            
            result["green_impact"] = True
            result["benefits"].append({
                "category": entry.category,
                "reason": entry.reason,
                "impact_areas": entry.impact_areas,
                "esg_score": entry.esg_score,
                "climate_commitment": entry.climate_commitment,
                "sources": entry.sources
            })
            
            # Priority-specific recommendations
            if priority_level == PriorityLevel.MISSION_CRITICAL.value:
                result["recommendations"].append("[MISSION CRITICAL] Essential for earth preservation - STRONGLY RECOMMENDED")
                result["recommendations"].append(f"ESG Score: {entry.esg_score}/10 - Climate Leadership")
            elif priority_level == PriorityLevel.PRIORITY.value:
                result["recommendations"].append("[PRIORITY] High impact for sustainability - RECOMMENDED")
                result["recommendations"].append(f"ESG Score: {entry.esg_score}/10 - Strong environmental focus")
            elif priority_level == PriorityLevel.PREFERRED.value:
                result["recommendations"].append("[PREFERRED] Positive environmental impact - CONSIDER")
                result["recommendations"].append(f"ESG Score: {entry.esg_score}/10 - Good sustainability practices")
            
            result["recommendations"].append(f"Impact areas: {', '.join(entry.impact_areas)}")
            result["recommendations"].append(f"Climate commitment: {entry.climate_commitment}")
            
        # Check blacklist
        elif symbol in self.blacklist:
            entry = self.blacklist[symbol]
            result["status"] = "blocked" if entry.severity >= SeverityLevel.HIGH.value else "warning"
            result["severity"] = entry.severity
            result["priority_score"] = -entry.severity * 2  # Negative score for blacklisted items
            result["concerns"].append({
                "category": entry.category,
                "reason": entry.reason,
                "leadership_concerns": entry.leadership_concerns,
                "sources": entry.sources
            })
            
            if entry.severity >= SeverityLevel.HIGH.value:
                result["recommendations"].append("[AVOID] High ethical concerns")
                result["alternative_suggestions"] = self._suggest_green_alternatives(symbol, entry.category)
            else:
                result["recommendations"].append("[MONITOR] Consider reducing exposure")
        
        # Check watchlist
        elif symbol in self.watchlist:
            result["status"] = "warning"
            result["severity"] = SeverityLevel.LOW.value
            result["priority_score"] = 1
            result["concerns"].append({
                "category": "monitoring",
                "reason": self.watchlist[symbol],
                "sources": ["General monitoring"]
            })
            result["recommendations"].append("[MONITOR] Minor concerns, regular review recommended")
        
        # Check standard whitelist
        elif symbol in self.standard_whitelist:
            result["status"] = "approved"
            result["priority_score"] = 3
            result["recommendations"].append("[APPROVED] Passes ethical screening")
        
        else:
            result["status"] = "unknown"
            result["priority_score"] = 0
            result["recommendations"].append("[UNKNOWN] Requires manual review")
            
            # Suggest reviewing for potential green classification
            result["recommendations"].append("Consider researching ESG practices and environmental impact")
        
        return result
    
    def _suggest_alternatives(self, blocked_symbol: str, category: str) -> List[str]:
        """Suggest ethical alternatives to blocked investments (legacy method)"""
        return self._suggest_green_alternatives(blocked_symbol, category)
    
    def _suggest_green_alternatives(self, blocked_symbol: str, category: str) -> List[str]:
        """Suggest green/sustainable alternatives to blocked investments with priority for earth preservation"""
        
        # Priority green alternatives organized by category
        green_alternatives = {
            BlacklistCategory.CONTROVERSIAL_LEADERSHIP.value: {
                "TSLA": ["RIVN", "NIO", "LCID", "FSLR", "ENPH"],  # Green EV and renewable alternatives
                "TWTR": ["ICLN", "QCLN"],  # Suggest clean tech instead of social media
                "DWAC": ["PBW", "ICLN"]  # Clean energy ETFs instead of media
            },
            
            BlacklistCategory.ENVIRONMENTAL_DAMAGE.value: {
                "XOM": ["FSLR", "ENPH", "ICLN", "QCLN", "VWDRY"],  # Solar and wind alternatives
                "CVX": ["SPWR", "FSLR", "XYL", "AWK"],  # Solar and water tech
                "BP": ["ICLN", "QCLN", "PBW", "EOSE"],  # Clean energy ETFs and storage
                "COP": ["FSLR", "ENPH", "VWDRY"],  # Renewable energy
                "PSX": ["RIVN", "NIO", "LCID"]  # EV alternatives to oil refining
            },
            
            BlacklistCategory.UNETHICAL_BUSINESS_PRACTICES.value: {
                "NSRGY": ["XYL", "AWK", "WM"],  # Water and waste management alternatives
                "META": ["TRMB", "DE"],  # Technology with environmental focus
                "WMT": ["WM", "RSG"]  # Sustainable waste management
            },
            
            BlacklistCategory.HUMAN_RIGHTS_VIOLATIONS.value: {
                "BABA": ["AMZN", "ICLN"],  # Include green alternatives to Chinese tech
                "TCEHY": ["FSLR", "ENPH", "QCLN"]  # Clean technology alternatives
            },
            
            BlacklistCategory.MILITARY_WEAPONS.value: {
                "LMT": ["GE", "TRMB", "DE"],  # Industrial with green focus
                "RTX": ["XYL", "EOSE", "ENPH"]  # Clean technology alternatives
            },
            
            BlacklistCategory.HARMFUL_PRODUCTS.value: {
                "MO": ["XYL", "AWK", "FSLR"],  # Health-positive environmental alternatives
                "BTI": ["ENPH", "SPWR", "WM"]  # Clean technology alternatives
            },
            
            BlacklistCategory.FOSSIL_FUELS.value: {
                "XOM": ["ICLN", "QCLN", "PBW", "FSLR", "VWDRY"],
                "CVX": ["ENPH", "SPWR", "EOSE", "XYL"],
                "BP": ["RIVN", "NIO", "LCID", "FSLR"],
                "Shell": ["ICLN", "QCLN", "VWDRY"],
                "Total": ["FSLR", "ENPH", "SPWR"]
            }
        }
        
        # Get category-specific alternatives
        category_alternatives = green_alternatives.get(category, {}).get(blocked_symbol, [])
        
        # If no specific alternatives, suggest general green investments based on category
        if not category_alternatives:
            if "environmental" in category.lower() or "fossil" in category.lower():
                category_alternatives = ["ICLN", "QCLN", "FSLR", "ENPH", "VWDRY"]
            elif "transportation" in category.lower() or "vehicle" in category.lower():
                category_alternatives = ["RIVN", "NIO", "LCID", "ICLN"]
            elif "technology" in category.lower():
                category_alternatives = ["ENPH", "FSLR", "TRMB", "DE"]
            elif "consumer" in category.lower():
                category_alternatives = ["WM", "RSG", "XYL", "AWK"]
            else:
                # Default green alternatives for any category
                category_alternatives = ["ICLN", "QCLN", "FSLR", "ENPH", "RIVN"]
        
        return category_alternatives
    
    def screen_portfolio(self, symbols: List[str]) -> Dict[str, any]:
        """Screen an entire portfolio for ethical concerns with green impact scoring"""
        
        portfolio_screening = {
            "total_symbols": len(symbols),
            "mission_critical": [],
            "priority": [],
            "preferred": [],
            "approved": [],
            "warnings": [],
            "blocked": [],
            "unknown": [],
            "overall_score": 0.0,
            "green_impact_score": 0.0,
            "sustainability_rating": "",
            "recommendations": []
        }
        
        total_priority_score = 0
        green_investments = 0
        
        for symbol in symbols:
            result = self.check_investment(symbol)
            total_priority_score += result["priority_score"]
            
            if result["green_impact"]:
                green_investments += 1
            
            # Categorize by status
            if result["status"] == "mission_critical":
                portfolio_screening["mission_critical"].append({
                    "symbol": symbol,
                    "benefits": result["benefits"],
                    "priority_score": result["priority_score"]
                })
            elif result["status"] == "priority":
                portfolio_screening["priority"].append({
                    "symbol": symbol,
                    "benefits": result["benefits"],
                    "priority_score": result["priority_score"]
                })
            elif result["status"] == "preferred":
                portfolio_screening["preferred"].append({
                    "symbol": symbol,
                    "benefits": result["benefits"],
                    "priority_score": result["priority_score"]
                })
            elif result["status"] == "approved":
                portfolio_screening["approved"].append(symbol)
            elif result["status"] == "warning":
                portfolio_screening["warnings"].append({
                    "symbol": symbol,
                    "concerns": result["concerns"]
                })
            elif result["status"] == "blocked":
                portfolio_screening["blocked"].append({
                    "symbol": symbol,
                    "concerns": result["concerns"],
                    "alternatives": result["alternative_suggestions"]
                })
            else:
                portfolio_screening["unknown"].append(symbol)
        
        # Calculate scores
        total_weight = len(symbols)
        if total_weight > 0:
            # Traditional ethics score
            approved_weight = (len(portfolio_screening["approved"]) + 
                             len(portfolio_screening["preferred"]) + 
                             len(portfolio_screening["priority"]) + 
                             len(portfolio_screening["mission_critical"]))
            warning_weight = len(portfolio_screening["warnings"]) * 0.5
            blocked_weight = len(portfolio_screening["blocked"]) * 0.0
            
            portfolio_screening["overall_score"] = (
                (approved_weight + warning_weight + blocked_weight) / total_weight
            )
            
            # Green impact score (percentage of green investments)
            portfolio_screening["green_impact_score"] = green_investments / total_weight
            
            # Average priority score
            avg_priority_score = total_priority_score / total_weight
            
            # Sustainability rating
            if portfolio_screening["green_impact_score"] >= 0.7 and avg_priority_score >= 6:
                portfolio_screening["sustainability_rating"] = "[EARTH CHAMPION]"
            elif portfolio_screening["green_impact_score"] >= 0.5 and avg_priority_score >= 4:
                portfolio_screening["sustainability_rating"] = "[SUSTAINABILITY LEADER]"
            elif portfolio_screening["green_impact_score"] >= 0.3 and avg_priority_score >= 2:
                portfolio_screening["sustainability_rating"] = "[ENVIRONMENTALLY CONSCIOUS]"
            elif portfolio_screening["overall_score"] >= 0.8:
                portfolio_screening["sustainability_rating"] = "[ETHICALLY SOUND]"
            elif portfolio_screening["overall_score"] >= 0.6:
                portfolio_screening["sustainability_rating"] = "[MIXED IMPACT]"
            else:
                portfolio_screening["sustainability_rating"] = "[NEEDS IMPROVEMENT]"
        
        # Generate portfolio-level recommendations
        if portfolio_screening["blocked"]:
            portfolio_screening["recommendations"].append(
                f"[URGENT] Remove {len(portfolio_screening['blocked'])} blocked investments immediately"
            )
        
        if portfolio_screening["mission_critical"]:
            portfolio_screening["recommendations"].append(
                f"[EXCELLENT] {len(portfolio_screening['mission_critical'])} mission-critical sustainability investments"
            )
        
        if portfolio_screening["priority"]:
            portfolio_screening["recommendations"].append(
                f"[GOOD] {len(portfolio_screening['priority'])} high-priority green investments"
            )
        
        if portfolio_screening["green_impact_score"] < 0.3:
            portfolio_screening["recommendations"].append(
                "[OPPORTUNITY] Consider increasing green/sustainable investments for earth preservation"
            )
        
        if portfolio_screening["warnings"]:
            portfolio_screening["recommendations"].append(
                f"[MONITOR] Review {len(portfolio_screening['warnings'])} investments with concerns"
            )
        
        # Overall portfolio guidance
        if portfolio_screening["green_impact_score"] >= 0.5:
            portfolio_screening["recommendations"].append(
                f"[IMPACT] {portfolio_screening['green_impact_score']:.1%} of portfolio supports earth preservation"
            )
        
        return portfolio_screening
    
    def add_blacklist_entry(self, entry: BlacklistEntry):
        """Add a new entry to the blacklist"""
        self.blacklist[entry.symbol] = entry
    
    def remove_blacklist_entry(self, symbol: str):
        """Remove an entry from the blacklist"""
        if symbol in self.blacklist:
            del self.blacklist[symbol]
    
    def add_green_whitelist_entry(self, entry: WhitelistEntry):
        """Add a new entry to the green whitelist"""
        self.green_whitelist[entry.symbol] = entry
    
    def add_to_standard_whitelist(self, symbol: str):
        """Add a company to the standard whitelist"""
        self.standard_whitelist.add(symbol)
    
    def add_to_whitelist(self, symbol: str):
        """Add a company to the standard whitelist (legacy method)"""
        self.standard_whitelist.add(symbol)
    
    def add_to_watchlist(self, symbol: str, reason: str):
        """Add a company to the watchlist"""
        self.watchlist[symbol] = reason
    
    def export_ethics_data(self, filepath: str):
        """Export all ethics data to JSON file"""
        data = {
            "blacklist": {symbol: asdict(entry) for symbol, entry in self.blacklist.items()},
            "green_whitelist": {symbol: asdict(entry) for symbol, entry in self.green_whitelist.items()},
            "standard_whitelist": list(self.standard_whitelist),
            "watchlist": self.watchlist,
            "exported_date": datetime.now().isoformat(),
            "version": "2.0_green_enhanced"
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def export_blacklist(self, filepath: str):
        """Export blacklist to JSON file (legacy method)"""
        self.export_ethics_data(filepath)
    
    def import_ethics_data(self, filepath: str):
        """Import all ethics data from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Import blacklist entries
        for symbol, entry_data in data.get("blacklist", {}).items():
            self.blacklist[symbol] = BlacklistEntry(**entry_data)
        
        # Import green whitelist entries
        for symbol, entry_data in data.get("green_whitelist", {}).items():
            self.green_whitelist[symbol] = WhitelistEntry(**entry_data)
        
        # Import watchlist and standard whitelist
        self.watchlist.update(data.get("watchlist", {}))
        self.standard_whitelist.update(data.get("standard_whitelist", []))
        
        # Handle legacy whitelist format
        if "whitelist" in data and "standard_whitelist" not in data:
            self.standard_whitelist.update(data.get("whitelist", []))
    
    def import_blacklist(self, filepath: str):
        """Import blacklist from JSON file (legacy method)"""
        self.import_ethics_data(filepath)
    
    def generate_ethics_report(self) -> Dict[str, any]:
        """Generate a comprehensive ethics screening report with green impact analysis"""
        
        # Blacklist analysis
        blacklist_categories = {}
        for entry in self.blacklist.values():
            if entry.category not in blacklist_categories:
                blacklist_categories[entry.category] = []
            blacklist_categories[entry.category].append(entry.symbol)
        
        severity_distribution = {
            "critical": len([e for e in self.blacklist.values() if e.severity == SeverityLevel.CRITICAL.value]),
            "high": len([e for e in self.blacklist.values() if e.severity == SeverityLevel.HIGH.value]),
            "medium": len([e for e in self.blacklist.values() if e.severity == SeverityLevel.MEDIUM.value]),
            "low": len([e for e in self.blacklist.values() if e.severity == SeverityLevel.LOW.value])
        }
        
        # Green whitelist analysis
        green_categories = {}
        priority_distribution = {
            "mission_critical": len([e for e in self.green_whitelist.values() if e.priority == PriorityLevel.MISSION_CRITICAL.value]),
            "priority": len([e for e in self.green_whitelist.values() if e.priority == PriorityLevel.PRIORITY.value]),
            "preferred": len([e for e in self.green_whitelist.values() if e.priority == PriorityLevel.PREFERRED.value]),
            "standard": len([e for e in self.green_whitelist.values() if e.priority == PriorityLevel.STANDARD.value])
        }
        
        for entry in self.green_whitelist.values():
            if entry.category not in green_categories:
                green_categories[entry.category] = []
            green_categories[entry.category].append({
                "symbol": entry.symbol,
                "esg_score": entry.esg_score,
                "priority": entry.priority
            })
        
        # Calculate average ESG score
        total_esg = sum(entry.esg_score for entry in self.green_whitelist.values())
        avg_esg_score = total_esg / len(self.green_whitelist) if self.green_whitelist else 0
        
        report = {
            "generated_date": datetime.now().isoformat(),
            "version": "2.0_green_enhanced",
            "blacklist_summary": {
                "total_entries": len(self.blacklist),
                "categories": blacklist_categories,
                "severity_distribution": severity_distribution
            },
            "green_whitelist_summary": {
                "total_entries": len(self.green_whitelist),
                "categories": green_categories,
                "priority_distribution": priority_distribution,
                "average_esg_score": round(avg_esg_score, 2)
            },
            "watchlist_summary": {
                "total_entries": len(self.watchlist),
                "companies": list(self.watchlist.keys())
            },
            "standard_whitelist_summary": {
                "total_entries": len(self.standard_whitelist),
                "companies": list(self.standard_whitelist)
            },
            "sustainability_metrics": {
                "total_green_investments": len(self.green_whitelist),
                "mission_critical_count": priority_distribution["mission_critical"],
                "high_impact_percentage": round((priority_distribution["mission_critical"] + priority_distribution["priority"]) / max(len(self.green_whitelist), 1) * 100, 1)
            },
            "top_concerns": self._get_top_concerns(),
            "top_green_opportunities": self._get_top_green_opportunities(),
            "ethical_guidelines": self._get_enhanced_ethical_guidelines()
        }
        
        return report
    
    def _get_top_concerns(self) -> List[Dict[str, str]]:
        """Get the most severe ethical concerns"""
        critical_entries = [e for e in self.blacklist.values() if e.severity == SeverityLevel.CRITICAL.value]
        critical_entries.sort(key=lambda x: x.added_date)
        
        return [
            {
                "symbol": entry.symbol,
                "company": entry.company_name,
                "reason": entry.reason,
                "category": entry.category
            }
            for entry in critical_entries[:10]
        ]
    
    def _get_top_green_opportunities(self) -> List[Dict[str, any]]:
        """Get the top green investment opportunities"""
        mission_critical = [e for e in self.green_whitelist.values() if e.priority == PriorityLevel.MISSION_CRITICAL.value]
        mission_critical.sort(key=lambda x: x.esg_score, reverse=True)
        
        return [
            {
                "symbol": entry.symbol,
                "company": entry.company_name,
                "category": entry.category,
                "esg_score": entry.esg_score,
                "reason": entry.reason,
                "impact_areas": entry.impact_areas,
                "climate_commitment": entry.climate_commitment
            }
            for entry in mission_critical[:10]
        ]
    
    def _get_enhanced_ethical_guidelines(self) -> List[str]:
        """Get enhanced ethical investment guidelines including green priorities"""
        return [
            "🌍 PRIORITIZE earth preservation and climate change mitigation investments",
            "🌱 FAVOR renewable energy, clean technology, and sustainable companies",
            "♻️ SUPPORT circular economy, waste reduction, and water conservation",
            "🚗 INVEST in electric vehicles and sustainable transportation solutions",
            "⚡ CHOOSE energy storage and grid modernization technologies",
            "❌ AVOID companies with controversial leadership involved in market manipulation",
            "🏭 EXCLUDE companies with significant environmental damage or climate denial",
            "🚫 SCREEN OUT companies with human rights violations or authoritarian complicity",
            "👥 CONSIDER labor practices and worker rights in investment decisions",
            "🔒 EVALUATE privacy practices and data handling policies",
            "🔍 REVIEW supply chain ethics and child labor practices",
            "📊 ASSESS ESG scores and sustainability commitments",
            "🎯 MONITOR corporate climate goals and net-zero commitments",
            "📈 TRACK environmental impact and carbon footprint reduction",
            "🌊 SUPPORT ocean preservation and biodiversity protection initiatives"
        ]
    
    def _get_ethical_guidelines(self) -> List[str]:
        """Get ethical investment guidelines (legacy method)"""
        return [guideline.split(' ', 1)[1] if ' ' in guideline else guideline 
                for guideline in self._get_enhanced_ethical_guidelines()]

def main():
    """Test the investment blacklist system"""
    print("Initializing Investment Blacklist Manager...")
    
    blacklist_manager = InvestmentBlacklistManager()
    
    print(f"Loaded blacklist with {len(blacklist_manager.blacklist)} entries")
    print(f"Watchlist: {len(blacklist_manager.watchlist)} companies")
    print(f"Whitelist: {len(blacklist_manager.whitelist)} companies")
    
    # Test individual stock screening
    test_symbols = ["TSLA", "NVDA", "MSFT", "NSRGY", "COST", "META"]
    
    print("\nTesting Individual Stock Screening:")
    print("=" * 50)
    
    for symbol in test_symbols:
        result = blacklist_manager.check_investment(symbol)
        status_emoji = {
            "approved": "✅",
            "warning": "⚠️",
            "blocked": "❌",
            "unknown": "❓"
        }
        
        print(f"{status_emoji.get(result['status'], '?')} {symbol}: {result['status'].upper()}")
        if result['concerns']:
            for concern in result['concerns']:
                print(f"   Reason: {concern['reason']}")
        for rec in result['recommendations']:
            print(f"   → {rec}")
        if result['alternative_suggestions']:
            print(f"   Alternatives: {', '.join(result['alternative_suggestions'])}")
        print()
    
    # Test portfolio screening
    test_portfolio = ["AAPL", "MSFT", "TSLA", "NVDA", "NSRGY", "META", "COST", "BRK.B"]
    
    print("Testing Portfolio Screening:")
    print("=" * 50)
    
    portfolio_result = blacklist_manager.screen_portfolio(test_portfolio)
    
    print(f"Portfolio Ethics Score: {portfolio_result['overall_score']:.2%}")
    print(f"Approved: {len(portfolio_result['approved'])} stocks")
    print(f"Warnings: {len(portfolio_result['warnings'])} stocks")
    print(f"Blocked: {len(portfolio_result['blocked'])} stocks")
    print(f"Unknown: {len(portfolio_result['unknown'])} stocks")
    
    print("\nPortfolio Recommendations:")
    for rec in portfolio_result['recommendations']:
        print(f"• {rec}")
    
    if portfolio_result['blocked']:
        print("\nBlocked Investments:")
        for blocked in portfolio_result['blocked']:
            print(f"❌ {blocked['symbol']}: {blocked['concerns'][0]['reason']}")
            if blocked['alternatives']:
                print(f"   Alternatives: {', '.join(blocked['alternatives'])}")
    
    # Generate and display ethics report
    print("\nGenerating Ethics Report...")
    report = blacklist_manager.generate_ethics_report()
    
    print(f"\nEthics Screening Summary:")
    print(f"• Total blacklisted companies: {report['blacklist_summary']['total_entries']}")
    print(f"• Companies under monitoring: {report['watchlist_summary']['total_entries']}")
    print(f"• Approved companies: {report['whitelist_summary']['total_entries']}")
    
    print(f"\nSeverity Distribution:")
    severity = report['blacklist_summary']['severity_distribution']
    print(f"• Critical: {severity['critical']}")
    print(f"• High: {severity['high']}")
    print(f"• Medium: {severity['medium']}")
    print(f"• Low: {severity['low']}")
    
    print("\nTop Ethical Concerns:")
    for concern in report['top_concerns'][:5]:
        print(f"• {concern['symbol']} ({concern['company']}): {concern['reason'][:80]}...")

if __name__ == "__main__":
    main()