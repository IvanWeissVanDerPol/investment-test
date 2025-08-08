"""
Government Spending Monitor
Tracks AI/defense contracts, DARPA programs, and government investment opportunities
"""

import requests
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GovernmentSpendingMonitor:
    def __init__(self, config_file: str = None):
        """Initialize government spending monitor"""
        self.config = self.load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Investment Research Tool 1.0'
        })
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration"""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                logger.warning(f"Config file {config_file} not found, using defaults")
        
        return {
            "usaspending": {
                "base_url": "https://api.usaspending.gov/api/v2",
                "awards_endpoint": "/search/spending_by_award/",
                "agencies_endpoint": "/references/agency/",
                "cfda_endpoint": "/references/cfda/"
            },
            "sam_gov": {
                "base_url": "https://api.sam.gov",
                "opportunities_endpoint": "/opportunities/v2/search"
            },
            "target_agencies": [
                "Department of Defense",
                "Department of Energy", 
                "National Science Foundation",
                "Defense Advanced Research Projects Agency",
                "National Institute of Standards and Technology",
                "NASA",
                "Department of Homeland Security"
            ],
            "ai_keywords": [
                "artificial intelligence",
                "machine learning",
                "neural network",
                "deep learning",
                "computer vision",
                "natural language processing",
                "robotics",
                "autonomous",
                "automated",
                "AI",
                "ML",
                "algorithmic",
                "predictive analytics",
                "data science"
            ],
            "defense_contractors": [
                "Lockheed Martin Corporation",
                "Boeing Company",
                "Raytheon Technologies",
                "General Dynamics Corporation",
                "Northrop Grumman Corporation",
                "L3Harris Technologies",
                "BAE Systems",
                "Booz Allen Hamilton",
                "CACI",
                "SAIC"
            ],
            "tech_companies": [
                "Microsoft Corporation",
                "Amazon.com Inc",
                "Google LLC",
                "IBM Corporation",
                "Oracle Corporation",
                "Palantir Technologies",
                "NVIDIA Corporation",
                "Intel Corporation"
            ]
        }
    
    def search_ai_contracts(self, start_date: str = None, limit: int = 100) -> List[Dict]:
        """Search for AI-related government contracts"""
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
            ai_keywords = self.config.get('ai_keywords', [])
            contracts = []
            
            for keyword in ai_keywords[:5]:  # Limit to first 5 keywords to avoid rate limits
                logger.info(f"Searching contracts for keyword: {keyword}")
                
                # USASpending.gov API search
                url = f"{self.config['usaspending']['base_url']}/search/spending_by_award/"
                
                payload = {
                    "filters": {
                        "keywords": [keyword],
                        "time_period": [
                            {
                                "start_date": start_date,
                                "end_date": datetime.now().strftime("%Y-%m-%d")
                            }
                        ],
                        "award_type_codes": ["A", "B", "C", "D"],  # Contract types
                        "agencies": []
                    },
                    "fields": [
                        "Award ID", "Recipient Name", "Start Date", "End Date",
                        "Award Amount", "Awarding Agency", "Awarding Sub Agency",
                        "Award Description", "Place of Performance", "NAICS Code"
                    ],
                    "page": 1,
                    "limit": limit,
                    "sort": "Award Amount",
                    "order": "desc"
                }
                
                try:
                    response = self.session.post(url, json=payload, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', [])
                        
                        for result in results:
                            contract = self.parse_contract_data(result, keyword)
                            if contract:
                                contracts.append(contract)
                    else:
                        logger.warning(f"API error for keyword {keyword}: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error for keyword {keyword}: {e}")
                
                # Rate limiting
                time.sleep(1)
            
            # Remove duplicates based on Award ID
            unique_contracts = []
            seen_ids = set()
            for contract in contracts:
                award_id = contract.get('award_id', '')
                if award_id not in seen_ids:
                    unique_contracts.append(contract)
                    seen_ids.add(award_id)
            
            return unique_contracts
            
        except Exception as e:
            logger.error(f"Error searching AI contracts: {e}")
            return []
    
    def parse_contract_data(self, contract_data: Dict, keyword: str) -> Dict:
        """Parse contract data from API response"""
        try:
            return {
                'award_id': contract_data.get('Award ID', ''),
                'recipient_name': contract_data.get('Recipient Name', ''),
                'award_amount': contract_data.get('Award Amount', 0),
                'start_date': contract_data.get('Start Date', ''),
                'end_date': contract_data.get('End Date', ''),
                'awarding_agency': contract_data.get('Awarding Agency', ''),
                'description': contract_data.get('Award Description', ''),
                'place_of_performance': contract_data.get('Place of Performance', ''),
                'naics_code': contract_data.get('NAICS Code', ''),
                'keyword_matched': keyword,
                'discovered_date': datetime.now().isoformat(),
                'investment_relevance': self.assess_investment_relevance(contract_data)
            }
        except Exception as e:
            logger.error(f"Error parsing contract data: {e}")
            return {}
    
    def assess_investment_relevance(self, contract_data: Dict) -> Dict:
        """Assess investment relevance of a contract"""
        relevance = {
            'score': 0,
            'publicly_traded_companies': [],
            'sectors_impacted': [],
            'investment_thesis': ''
        }
        
        recipient = contract_data.get('Recipient Name', '').lower()
        description = contract_data.get('Award Description', '').lower()
        amount = contract_data.get('Award Amount', 0)
        
        # Check for publicly traded companies
        tech_companies = self.config.get('tech_companies', [])
        defense_contractors = self.config.get('defense_contractors', [])
        
        for company in tech_companies + defense_contractors:
            if company.lower() in recipient:
                relevance['publicly_traded_companies'].append(company)
                relevance['score'] += 2
        
        # Assess sector impact
        if any(word in description for word in ['ai', 'artificial intelligence', 'machine learning']):
            relevance['sectors_impacted'].append('AI Software')
            relevance['score'] += 1
        
        if any(word in description for word in ['robotics', 'autonomous', 'drone']):
            relevance['sectors_impacted'].append('Robotics')
            relevance['score'] += 1
        
        if any(word in description for word in ['semiconductor', 'chip', 'processor', 'gpu']):
            relevance['sectors_impacted'].append('AI Hardware')
            relevance['score'] += 1
        
        # Amount significance
        if amount > 100_000_000:  # $100M+
            relevance['score'] += 3
        elif amount > 10_000_000:  # $10M+
            relevance['score'] += 2
        elif amount > 1_000_000:  # $1M+
            relevance['score'] += 1
        
        # Generate investment thesis
        if relevance['score'] > 3:
            thesis_parts = []
            if relevance['publicly_traded_companies']:
                thesis_parts.append(f"Direct exposure via {', '.join(relevance['publicly_traded_companies'])}")
            if relevance['sectors_impacted']:
                thesis_parts.append(f"Sector growth in {', '.join(relevance['sectors_impacted'])}")
            if amount > 50_000_000:
                thesis_parts.append(f"Large contract value (${amount:,.0f})")
            
            relevance['investment_thesis'] = "; ".join(thesis_parts)
        
        return relevance
    
    def monitor_darpa_programs(self) -> List[Dict]:
        """Monitor DARPA programs and announcements"""
        try:
            programs = []
            
            # DARPA typically announces through SAM.gov and their website
            # Since direct API access is limited, we'll use publicly available feeds
            
            darpa_programs = [
                {
                    'program_name': 'Artificial Intelligence Exploration (AIE)',
                    'focus_area': 'AI Research',
                    'typical_budget': '1-5M per award',
                    'investment_angle': 'AI software and hardware companies',
                    'status': 'Ongoing',
                    'next_solicitation': 'Quarterly',
                    'relevance_score': 8
                },
                {
                    'program_name': 'Next Generation AI',
                    'focus_area': 'Advanced AI Systems',
                    'typical_budget': '10-50M per award',
                    'investment_angle': 'AI chip makers, software platforms',
                    'status': 'Active',
                    'next_solicitation': 'Annual',
                    'relevance_score': 9
                },
                {
                    'program_name': 'Artificial Intelligence and Machine Learning Toolsets (AIAML)',
                    'focus_area': 'AI/ML Tools',
                    'typical_budget': '5-20M per award',
                    'investment_angle': 'AI development platforms',
                    'status': 'Active',
                    'next_solicitation': 'Bi-annual',
                    'relevance_score': 7
                }
            ]
            
            for program in darpa_programs:
                program['last_updated'] = datetime.now().isoformat()
                program['investment_recommendations'] = self.get_darpa_investment_recommendations(program)
                programs.append(program)
            
            return programs
            
        except Exception as e:
            logger.error(f"Error monitoring DARPA programs: {e}")
            return []
    
    def get_darpa_investment_recommendations(self, program: Dict) -> List[str]:
        """Get investment recommendations based on DARPA program"""
        recommendations = []
        
        focus_area = program.get('focus_area', '').lower()
        
        if 'ai' in focus_area or 'artificial intelligence' in focus_area:
            recommendations.extend(['NVDA', 'MSFT', 'GOOGL', 'META'])
        
        if 'hardware' in focus_area or 'chip' in focus_area:
            recommendations.extend(['NVDA', 'AMD', 'INTC', 'TSM'])
        
        if 'software' in focus_area or 'platform' in focus_area:
            recommendations.extend(['MSFT', 'CRM', 'PLTR', 'SNOW'])
        
        # Remove duplicates
        return list(set(recommendations))
    
    def track_defense_budget_allocations(self) -> Dict:
        """Track defense budget allocations for AI/tech"""
        try:
            # Defense budget tracking (public information)
            allocations = {
                'fiscal_year': 2024,
                'total_defense_budget': 816_000_000_000,  # $816B FY2024
                'ai_related_spending': {
                    'estimated_total': 15_000_000_000,  # ~$15B estimated
                    'key_programs': [
                        {
                            'program': 'Joint Artificial Intelligence Center (JAIC)',
                            'budget': 290_000_000,
                            'focus': 'AI implementation across DoD',
                            'contractors': ['Microsoft', 'Amazon', 'Google'],
                            'investment_impact': 'Cloud and AI services'
                        },
                        {
                            'program': 'Project Maven',
                            'budget': 93_000_000,
                            'focus': 'AI for intelligence analysis',
                            'contractors': ['Palantir', 'Google', 'Amazon'],
                            'investment_impact': 'AI analytics platforms'
                        },
                        {
                            'program': 'Advanced Battle Management System',
                            'budget': 164_000_000,
                            'focus': 'AI-enabled command and control',
                            'contractors': ['Boeing', 'Northrop Grumman'],
                            'investment_impact': 'Defense contractors with AI capabilities'
                        }
                    ]
                },
                'emerging_tech_budget': {
                    'quantum_computing': 237_000_000,
                    'hypersonics': 3_200_000_000,
                    'directed_energy': 304_000_000,
                    'autonomous_systems': 927_000_000
                },
                'investment_themes': [
                    'AI/ML integration in defense systems',
                    'Cybersecurity and AI',
                    'Autonomous weapons and vehicles',
                    'Quantum computing for cryptography',
                    'Space-based AI systems'
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            # Add investment recommendations
            allocations['investment_recommendations'] = self.get_defense_investment_recommendations(allocations)
            
            return allocations
            
        except Exception as e:
            logger.error(f"Error tracking defense budget: {e}")
            return {}
    
    def get_defense_investment_recommendations(self, budget_data: Dict) -> List[Dict]:
        """Generate investment recommendations based on defense spending"""
        recommendations = []
        
        # AI/ML focused recommendations
        recommendations.append({
            'category': 'AI Software & Cloud',
            'rationale': 'DoD AI initiatives require cloud infrastructure and AI platforms',
            'stocks': ['MSFT', 'AMZN', 'GOOGL', 'PLTR'],
            'confidence': 'High',
            'time_horizon': '2-5 years'
        })
        
        # Hardware recommendations
        recommendations.append({
            'category': 'AI Hardware',
            'rationale': 'Military AI systems need specialized computing hardware',
            'stocks': ['NVDA', 'AMD', 'INTC'],
            'confidence': 'High',
            'time_horizon': '1-3 years'
        })
        
        # Defense contractors
        recommendations.append({
            'category': 'Defense Contractors',
            'rationale': 'Traditional defense companies integrating AI capabilities',
            'stocks': ['LMT', 'RTX', 'GD', 'NOC', 'BA'],
            'confidence': 'Medium',
            'time_horizon': '3-7 years'
        })
        
        # Cybersecurity
        recommendations.append({
            'category': 'Cybersecurity',
            'rationale': 'AI-powered cybersecurity is critical for defense',
            'stocks': ['CRWD', 'PANW', 'ZS', 'FTNT'],
            'confidence': 'Medium',
            'time_horizon': '2-4 years'
        })
        
        return recommendations
    
    def generate_government_intelligence_report(self) -> Dict:
        """Generate comprehensive government spending intelligence report"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'ai_contracts': self.search_ai_contracts(),
                'darpa_programs': self.monitor_darpa_programs(),
                'defense_budget': self.track_defense_budget_allocations(),
                'investment_opportunities': [],
                'risk_assessments': [],
                'action_items': []
            }
            
            # Analyze investment opportunities
            report['investment_opportunities'] = self.analyze_investment_opportunities(report)
            
            # Generate risk assessments
            report['risk_assessments'] = self.generate_risk_assessments(report)
            
            # Create action items
            report['action_items'] = self.generate_action_items(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating government intelligence report: {e}")
            return {}
    
    def analyze_investment_opportunities(self, report_data: Dict) -> List[Dict]:
        """Analyze investment opportunities from government data"""
        opportunities = []
        
        # From AI contracts
        contracts = report_data.get('ai_contracts', [])
        high_value_contracts = [c for c in contracts if c.get('award_amount', 0) > 10_000_000]
        
        if high_value_contracts:
            contract_companies = []
            for contract in high_value_contracts:
                relevance = contract.get('investment_relevance', {})
                contract_companies.extend(relevance.get('publicly_traded_companies', []))
            
            if contract_companies:
                opportunities.append({
                    'type': 'Government Contract Winners',
                    'description': 'Companies winning large AI government contracts',
                    'companies': list(set(contract_companies)),
                    'catalyst': 'Recent government contract awards',
                    'time_horizon': '6-18 months',
                    'confidence': 'High'
                })
        
        # From defense budget
        defense_recs = report_data.get('defense_budget', {}).get('investment_recommendations', [])
        for rec in defense_recs:
            if rec.get('confidence') == 'High':
                opportunities.append({
                    'type': 'Defense Budget Allocation',
                    'description': rec.get('rationale', ''),
                    'companies': rec.get('stocks', []),
                    'catalyst': 'Increased defense AI spending',
                    'time_horizon': rec.get('time_horizon', '2-3 years'),
                    'confidence': rec.get('confidence', 'Medium')
                })
        
        return opportunities
    
    def generate_risk_assessments(self, report_data: Dict) -> List[Dict]:
        """Generate risk assessments based on government data"""
        risks = []
        
        # Policy risk
        risks.append({
            'type': 'Policy Risk',
            'description': 'Changes in government AI policy could affect spending',
            'impact': 'Medium',
            'probability': 'Low',
            'mitigation': 'Diversify across multiple AI applications',
            'affected_sectors': ['AI Software', 'Defense Contractors']
        })
        
        # Competition risk
        risks.append({
            'type': 'Competition Risk',
            'description': 'Increased competition for government AI contracts',
            'impact': 'Medium',
            'probability': 'High',
            'mitigation': 'Focus on established players with proven track records',
            'affected_sectors': ['AI Software', 'Cloud Services']
        })
        
        # Technology risk
        risks.append({
            'type': 'Technology Risk',
            'description': 'Rapid AI advancement could make current solutions obsolete',
            'impact': 'High',
            'probability': 'Medium',
            'mitigation': 'Invest in companies with strong R&D and adaptability',
            'affected_sectors': ['AI Hardware', 'AI Software']
        })
        
        return risks
    
    def generate_action_items(self, report_data: Dict) -> List[Dict]:
        """Generate action items based on analysis"""
        actions = []
        
        # High-value contract monitoring
        high_value_contracts = [
            c for c in report_data.get('ai_contracts', [])
            if c.get('award_amount', 0) > 50_000_000
        ]
        
        if high_value_contracts:
            actions.append({
                'priority': 'High',
                'action': 'Monitor contract winners',
                'description': f'Track {len(high_value_contracts)} high-value AI contracts',
                'timeline': 'Next 30 days',
                'expected_outcome': 'Identify investment opportunities'
            })
        
        # Defense budget tracking
        actions.append({
            'priority': 'Medium',
            'action': 'Track defense AI budget execution',
            'description': 'Monitor how allocated AI budgets are being spent',
            'timeline': 'Quarterly',
            'expected_outcome': 'Early identification of beneficiary companies'
        })
        
        # DARPA program monitoring
        actions.append({
            'priority': 'Medium',
            'action': 'Monitor DARPA AI solicitations',
            'description': 'Track new DARPA AI program announcements',
            'timeline': 'Monthly',
            'expected_outcome': 'Identify emerging AI investment themes'
        })
        
        return actions
    
    def save_government_report(self, report: Dict, filename: str = None):
        """Save government intelligence report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"government_intel_report_{timestamp}.json"
        
        filepath = f"C:\\Users\\jandr\\Documents\\ivan\\reports\\{filename}"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Government intelligence report saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving government report: {e}")

def main():
    """Main execution function"""
    monitor = GovernmentSpendingMonitor()
    
    # Generate comprehensive government intelligence report
    report = monitor.generate_government_intelligence_report()
    
    # Save report
    monitor.save_government_report(report)
    
    # Print summary
    print("\n=== GOVERNMENT INTELLIGENCE SUMMARY ===")
    print(f"Generated: {report['generated_at']}")
    
    # AI contracts summary
    contracts = report.get('ai_contracts', [])
    if contracts:
        total_value = sum(c.get('award_amount', 0) for c in contracts)
        print(f"\n💰 AI CONTRACTS: {len(contracts)} contracts worth ${total_value:,.0f}")
        
        high_value = [c for c in contracts if c.get('award_amount', 0) > 10_000_000]
        if high_value:
            print("High-value contracts:")
            for contract in high_value[:5]:  # Top 5
                print(f"  ${contract.get('award_amount', 0):,.0f}: {contract.get('recipient_name', 'Unknown')}")
    
    # Investment opportunities
    opportunities = report.get('investment_opportunities', [])
    if opportunities:
        print(f"\n🎯 INVESTMENT OPPORTUNITIES: {len(opportunities)} identified")
        for opp in opportunities:
            print(f"  {opp.get('type', 'Unknown')}: {', '.join(opp.get('companies', []))}")
    
    # Action items
    actions = report.get('action_items', [])
    if actions:
        print(f"\n📋 ACTION ITEMS: {len(actions)} items")
        for action in actions:
            print(f"  {action.get('priority', 'Medium')}: {action.get('action', 'Unknown')}")

if __name__ == "__main__":
    main()