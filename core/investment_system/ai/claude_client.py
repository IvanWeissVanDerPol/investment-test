"""
Claude API Client for Investment Analysis
Provides AI-powered investment insights and decision support
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

# Import anthropic if available, otherwise provide fallback
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("[WARNING] Anthropic library not installed. Install with: pip install anthropic")

from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class ClaudeInvestmentClient:
    """
    Claude API client specifically designed for investment analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client for investment analysis"""
        
        # Get API key from environment or parameter
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        
        if not self.api_key:
            logger.warning("Claude API key not found. Set CLAUDE_API_KEY environment variable")
            self.client = None
        elif not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic library not available. AI features disabled")
            self.client = None
        else:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Claude API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")
                self.client = None
        
        self.cache_manager = CacheManager()
        
        # Analysis templates for different investment scenarios
        self.templates = self._load_analysis_templates()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 second between requests
        
    def _load_analysis_templates(self) -> Dict[str, str]:
        """Load pre-defined analysis templates"""
        
        return {
            "stock_analysis": """
You are an expert investment analyst focusing on sustainable and ethical investing. 
Analyze the following stock with emphasis on:

1. SUSTAINABILITY FACTORS (40% weight):
   - ESG performance and ratings
   - Climate commitments and net-zero targets
   - Environmental impact and green technology
   - Social responsibility and governance

2. FINANCIAL PERFORMANCE (35% weight):
   - Revenue growth and profitability trends
   - Market position and competitive advantages
   - Financial stability and debt levels
   - Valuation metrics vs peers

3. ETHICS SCREENING (25% weight):
   - Leadership quality and controversies
   - Business practices and reputation
   - Regulatory compliance
   - Stakeholder treatment

INVESTMENT CONTEXT:
- Portfolio size: $900
- Target green allocation: 30%
- Target AI/robotics allocation: 50%
- Risk tolerance: Medium
- Investment timeline: Long-term (3-5 years)

Provide a clear BUY/HOLD/SELL recommendation with confidence score (1-10).
""",

            "portfolio_optimization": """
You are a portfolio optimization specialist focused on sustainable investing.
Analyze the current portfolio and provide optimization recommendations.

OPTIMIZATION PRIORITIES:
1. Achieve 30% green technology allocation
2. Maintain 50% AI/robotics allocation
3. Eliminate ethics violations (blocked stocks)
4. Maximize ESG scores while maintaining returns
5. Optimize for $900 total portfolio size

CURRENT PORTFOLIO CONTEXT:
{portfolio_data}

ETHICS SCREENING RESULTS:
{ethics_results}

Provide specific BUY/SELL recommendations with dollar amounts and rationale.
Focus on actionable steps to improve sustainability while maintaining growth potential.
""",

            "market_analysis": """
You are a market analyst specializing in green technology and AI/robotics sectors.
Provide daily market insights focusing on sustainability trends and opportunities.

ANALYSIS FOCUS:
1. Green Technology Sector Trends
   - Renewable energy developments
   - Climate policy impacts
   - ESG investing flows
   
2. AI/Robotics Sector Analysis
   - Technology breakthroughs
   - Market adoption trends
   - Regulatory developments

3. Sustainable Investment Opportunities
   - Emerging green companies
   - ESG leaders vs laggards
   - Impact investing trends

4. Risk Assessment
   - Climate transition risks
   - Regulatory changes
   - Market volatility factors

Provide actionable insights for a $900 portfolio targeting sustainable growth.
""",

            "ethics_analysis": """
You are an ethical investment advisor specializing in ESG analysis.
Evaluate investments based on comprehensive ethical criteria.

ETHICS EVALUATION FRAMEWORK:
1. Environmental Impact (40%)
   - Carbon footprint and climate commitments
   - Resource usage and waste management
   - Biodiversity and ecosystem impact

2. Social Responsibility (35%)
   - Labor practices and worker rights
   - Community impact and development
   - Product safety and consumer protection

3. Governance Quality (25%)
   - Leadership integrity and transparency
   - Board composition and independence
   - Anti-corruption and compliance

SPECIFIC CONCERNS TO FLAG:
- Controversial leadership (especially Elon Musk affiliations)
- Environmental damage or climate denial
- Human rights violations
- Unethical business practices

Rate each stock on ESG factors (1-10) and provide clear ethical guidance.
""",

            "green_alternative_analysis": """
You are a sustainable investment specialist focused on green alternatives.
When traditional investments have ethical concerns, recommend green alternatives.

ALTERNATIVE SELECTION CRITERIA:
1. Strong ESG performance (8.0+ score)
2. Clear environmental benefits
3. Solid financial fundamentals
4. Growth potential in green sectors

PRIORITY GREEN SECTORS:
- Renewable Energy (solar, wind, hydro)
- Electric Vehicles and Transportation
- Energy Storage and Grid Technology
- Water Conservation and Management
- Waste Management and Circular Economy
- Sustainable Agriculture and Food

For each blocked investment, provide 2-3 specific green alternatives with:
- Company overview and green credentials
- ESG score and climate commitments
- Financial performance and growth prospects
- Risk assessment and recommendation confidence
"""
        }
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            wait_time = self.min_request_interval - elapsed
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Make a request to Claude API with error handling"""
        
        if not self.client:
            logger.warning("Claude client not available. Returning mock response")
            return "[AI ANALYSIS UNAVAILABLE] Claude API not configured. Set CLAUDE_API_KEY environment variable."
        
        try:
            self._wait_for_rate_limit()
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            if response.content and len(response.content) > 0:
                return response.content[0].text
            else:
                logger.warning("Empty response from Claude API")
                return "[AI ANALYSIS] No response received from Claude API"
                
        except Exception as e:
            logger.error(f"Claude API request failed: {e}")
            return f"[AI ANALYSIS ERROR] {str(e)}"
    
    def analyze_stock(self, symbol: str, stock_data: Dict, ethics_result: Dict) -> Dict:
        """
        Comprehensive AI-powered stock analysis
        """
        logger.info(f"Running AI analysis for {symbol}")
        
        # Check cache first
        cache_key = f"ai_analysis_{symbol}_{datetime.now().strftime('%Y%m%d')}"
        cached_result = self.cache_manager.get_cached_data("ai_analysis", cache_key)
        
        if cached_result:
            logger.debug(f"Using cached AI analysis for {symbol}")
            return cached_result
        
        # Prepare analysis prompt
        analysis_prompt = f"""
{self.templates['stock_analysis']}

STOCK: {symbol}

CURRENT DATA:
{json.dumps(stock_data, indent=2)}

ETHICS SCREENING:
{json.dumps(ethics_result, indent=2)}

Provide detailed analysis with specific recommendations for this $900 portfolio.
Include confidence scores and risk assessments.
"""
        
        # Get AI analysis
        ai_response = self._make_request(analysis_prompt)
        
        if not ai_response:
            return {"error": "AI analysis unavailable"}
        
        # Structure the response
        analysis_result = {
            "symbol": symbol,
            "ai_analysis": ai_response,
            "timestamp": datetime.now().isoformat(),
            "confidence_available": True if self.client else False,
            "analysis_type": "comprehensive_stock_analysis"
        }
        
        # Cache the result
        self.cache_manager.cache_data("ai_analysis", cache_key, analysis_result)
        
        return analysis_result
    
    def optimize_portfolio(self, portfolio_data: Dict, ethics_results: Dict) -> Dict:
        """
        AI-powered portfolio optimization with sustainability focus
        """
        logger.info("Running AI portfolio optimization")
        
        # Check cache
        cache_key = f"portfolio_optimization_{datetime.now().strftime('%Y%m%d_%H')}"
        cached_result = self.cache_manager.get_cached_data("ai_analysis", cache_key)
        
        if cached_result:
            logger.debug("Using cached portfolio optimization")
            return cached_result
        
        # Prepare optimization prompt
        optimization_prompt = self.templates["portfolio_optimization"].format(
            portfolio_data=json.dumps(portfolio_data, indent=2),
            ethics_results=json.dumps(ethics_results, indent=2)
        )
        
        # Get AI recommendations
        ai_response = self._make_request(optimization_prompt, max_tokens=5000)
        
        optimization_result = {
            "optimization_analysis": ai_response,
            "timestamp": datetime.now().isoformat(),
            "portfolio_value": portfolio_data.get("total_value", 900),
            "green_target": 0.30,
            "ai_target": 0.50
        }
        
        # Cache the result
        self.cache_manager.cache_data("ai_analysis", cache_key, optimization_result)
        
        return optimization_result
    
    def analyze_market_conditions(self) -> Dict:
        """
        AI analysis of current market conditions for green tech and AI sectors
        """
        logger.info("Running AI market analysis")
        
        # Check cache (update every 4 hours)
        cache_key = f"market_analysis_{datetime.now().strftime('%Y%m%d_%H')}"
        cached_result = self.cache_manager.get_cached_data("ai_analysis", cache_key)
        
        if cached_result:
            logger.debug("Using cached market analysis")
            return cached_result
        
        # Get current market analysis
        ai_response = self._make_request(self.templates["market_analysis"])
        
        market_result = {
            "market_analysis": ai_response,
            "timestamp": datetime.now().isoformat(),
            "focus_sectors": ["green_technology", "ai_robotics", "sustainable_investing"]
        }
        
        # Cache for 4 hours
        self.cache_manager.cache_data("ai_analysis", cache_key, market_result)
        
        return market_result
    
    def get_green_alternatives(self, blocked_stock: str, reason: str) -> Dict:
        """
        AI-powered green alternative recommendations
        """
        logger.info(f"Getting green alternatives for blocked stock {blocked_stock}")
        
        alternatives_prompt = f"""
{self.templates['green_alternative_analysis']}

BLOCKED STOCK: {blocked_stock}
BLOCKING REASON: {reason}

PORTFOLIO CONTEXT:
- Size: $900
- Current green allocation target: 30%
- Focus on earth preservation and climate solutions

Provide 3 specific green alternative stocks with detailed analysis.
Include ESG scores, financial metrics, and recommendation confidence.
"""
        
        ai_response = self._make_request(alternatives_prompt)
        
        return {
            "blocked_stock": blocked_stock,
            "green_alternatives": ai_response,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_investment_insights(self, query: str, context: Dict = None) -> str:
        """
        Generate AI insights for specific investment questions
        """
        logger.info(f"Generating AI insights for query: {query[:50]}...")
        
        context_str = ""
        if context:
            context_str = f"\nCONTEXT:\n{json.dumps(context, indent=2)}\n"
        
        insight_prompt = f"""
You are Ivan's personal AI investment advisor specializing in sustainable and ethical investing.

PORTFOLIO PROFILE:
- Balance: $900
- Target: 50% AI/robotics, 30% green technology, 20% other
- Focus: Earth preservation and climate solutions
- Ethics: Avoid Elon Musk companies, fossil fuels, unethical practices
- Timeline: Long-term growth with sustainability impact

{context_str}

QUESTION: {query}

Provide specific, actionable advice tailored to Ivan's sustainable investment goals.
Include stock recommendations, allocation advice, and timing considerations.
"""
        
        return self._make_request(insight_prompt) or "[AI UNAVAILABLE] Please set up Claude API key"
    
    def analyze_ethics_compliance(self, portfolio_positions: List[Dict]) -> Dict:
        """
        AI-powered ethics compliance analysis
        """
        logger.info("Running AI ethics compliance analysis")
        
        ethics_prompt = f"""
{self.templates['ethics_analysis']}

PORTFOLIO POSITIONS:
{json.dumps(portfolio_positions, indent=2)}

Analyze each position for ethical compliance and provide:
1. Individual ESG scores (1-10)
2. Specific ethical concerns or benefits
3. Compliance recommendations
4. Green alternative suggestions where needed

Focus on identifying companies that conflict with earth preservation goals.
"""
        
        ai_response = self._make_request(ethics_prompt, max_tokens=6000)
        
        return {
            "ethics_analysis": ai_response,
            "timestamp": datetime.now().isoformat(),
            "positions_analyzed": len(portfolio_positions)
        }
    
    def is_available(self) -> bool:
        """Check if Claude API is available and configured"""
        return self.client is not None
    
    def get_usage_stats(self) -> Dict:
        """Get API usage statistics"""
        return {
            "api_configured": self.client is not None,
            "anthropic_library_available": ANTHROPIC_AVAILABLE,
            "cache_entries": len(os.listdir(self.cache_manager.cache_dir)) if os.path.exists(self.cache_manager.cache_dir) else 0
        }

def main():
    """Test the Claude client"""
    
    print("="*80)
    print("TESTING CLAUDE INVESTMENT API CLIENT")
    print("="*80)
    
    # Initialize client
    client = ClaudeInvestmentClient()
    
    # Check availability
    print(f"Claude API Available: {client.is_available()}")
    print(f"Usage Stats: {client.get_usage_stats()}")
    
    if not client.is_available():
        print("\n[SETUP REQUIRED] To enable AI features:")
        print("1. Install anthropic library: pip install anthropic")
        print("2. Get Claude API key from: https://console.anthropic.com/")
        print("3. Set environment variable: CLAUDE_API_KEY=your_key_here")
        print("\nFalling back to mock responses for testing...")
    
    # Test stock analysis
    print(f"\n[TEST] Stock Analysis")
    print("-"*40)
    
    test_stock_data = {
        "symbol": "FSLR",
        "price": 150.25,
        "market_cap": "15.8B",
        "sector": "Clean Energy"
    }
    
    test_ethics_result = {
        "status": "mission_critical",
        "priority_score": 10,
        "esg_score": 8.5,
        "green_impact": True
    }
    
    analysis = client.analyze_stock("FSLR", test_stock_data, test_ethics_result)
    print(f"Analysis Type: {analysis.get('analysis_type', 'N/A')}")
    print(f"Response Length: {len(analysis.get('ai_analysis', ''))}")
    print(f"First 200 chars: {analysis.get('ai_analysis', '')[:200]}...")
    
    # Test market analysis
    print(f"\n[TEST] Market Analysis")
    print("-"*40)
    
    market_analysis = client.analyze_market_conditions()
    print(f"Market Analysis Length: {len(market_analysis.get('market_analysis', ''))}")
    print(f"Focus Sectors: {market_analysis.get('focus_sectors', [])}")
    
    # Test investment insights
    print(f"\n[TEST] Investment Insights")
    print("-"*40)
    
    insights = client.generate_investment_insights(
        "Should I sell TSLA and buy RIVN for better ESG alignment?",
        {"current_green_allocation": 0.25, "target": 0.30}
    )
    print(f"Insight Length: {len(insights)}")
    print(f"First 200 chars: {insights[:200]}...")
    
    print(f"\n[SUCCESS] Claude client testing complete!")

if __name__ == "__main__":
    main()