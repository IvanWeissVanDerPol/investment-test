"""
Sector Relationship Analyzer
Analyzes how different sectors influence each other and maps supply chain relationships
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SectorRelationshipAnalyzer:
    """
    Analyzes sector relationships, supply chains, and influence patterns
    """
    
    def __init__(self, config_path: str = "config"):
        self.config_path = Path(config_path)
        self.sectors_data = self.load_sectors_data()
        self.influence_matrix = None
        self.supply_chain_graph = None
        
        # Define sector influence relationships
        self.sector_influences = self.define_sector_influences()
        
    def load_sectors_data(self) -> Dict:
        """Load comprehensive sectors data"""
        try:
            with open(self.config_path / "comprehensive_sectors.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Comprehensive sectors file not found")
            return {}
    
    def define_sector_influences(self) -> Dict[str, Dict[str, float]]:
        """
        Define how much each sector influences others (0.0 to 1.0)
        This represents supply chain dependencies and market influence
        """
        return {
            # Technology sectors - high influence on most other sectors
            "artificial_intelligence": {
                "machine_learning": 0.95,
                "computer_vision": 0.90,
                "natural_language_processing": 0.85,
                "robotics_automation": 0.80,
                "autonomous_vehicles": 0.75,
                "medical_robotics": 0.70,
                "financial_technology": 0.65,
                "cybersecurity": 0.60,
                "cloud_infrastructure": 0.85,
                "edge_computing": 0.70
            },
            
            "semiconductor_design": {
                "artificial_intelligence": 0.90,
                "machine_learning": 0.85,
                "computer_vision": 0.80,
                "robotics_automation": 0.75,
                "electric_vehicles": 0.70,
                "renewable_energy": 0.65,
                "cloud_infrastructure": 0.85,
                "5g_wireless": 0.90,
                "quantum_computing": 0.95,
                "internet_of_things": 0.80
            },
            
            "semiconductor_manufacturing": {
                "semiconductor_design": 0.95,
                "artificial_intelligence": 0.85,
                "electric_vehicles": 0.75,
                "renewable_energy": 0.70,
                "industrial_robotics": 0.75,
                "consumer_electronics": 0.90,
                "telecommunications": 0.80,
                "automotive": 0.75,
                "defense_aerospace": 0.70,
                "medical_devices": 0.65
            },
            
            # Energy sectors - foundational influence
            "renewable_energy": {
                "electric_vehicles": 0.85,
                "energy_storage": 0.90,
                "smart_grid": 0.80,
                "industrial_manufacturing": 0.60,
                "data_centers": 0.55,
                "mining": 0.50,
                "agriculture": 0.45,
                "transportation": 0.70,
                "residential": 0.65,
                "commercial_real_estate": 0.60
            },
            
            "energy_storage": {
                "electric_vehicles": 0.95,
                "renewable_energy": 0.80,
                "smart_grid": 0.85,
                "portable_electronics": 0.70,
                "backup_power": 0.90,
                "grid_stabilization": 0.85,
                "remote_power": 0.75,
                "marine_applications": 0.60,
                "aerospace": 0.65,
                "medical_devices": 0.55
            },
            
            # Manufacturing and Industrial
            "industrial_robotics": {
                "manufacturing": 0.90,
                "automotive": 0.85,
                "electronics": 0.80,
                "aerospace": 0.75,
                "food_processing": 0.70,
                "pharmaceuticals": 0.65,
                "textiles": 0.60,
                "metals": 0.85,
                "chemicals": 0.70,
                "logistics": 0.75
            },
            
            "3d_printing": {
                "aerospace": 0.80,
                "automotive": 0.75,
                "medical_devices": 0.85,
                "architecture": 0.70,
                "consumer_goods": 0.65,
                "jewelry": 0.90,
                "prototyping": 0.95,
                "tooling": 0.80,
                "education": 0.60,
                "art_design": 0.70
            },
            
            # Transportation
            "electric_vehicles": {
                "automotive_traditional": 0.85,
                "battery_technology": 0.95,
                "charging_infrastructure": 0.90,
                "renewable_energy": 0.70,
                "semiconductor": 0.75,
                "materials": 0.80,
                "mining": 0.65,
                "software": 0.70,
                "insurance": 0.60,
                "real_estate": 0.55
            },
            
            "autonomous_vehicles": {
                "electric_vehicles": 0.80,
                "artificial_intelligence": 0.95,
                "sensor_technology": 0.90,
                "mapping": 0.85,
                "telecommunications": 0.80,
                "insurance": 0.75,
                "logistics": 0.85,
                "ride_sharing": 0.90,
                "public_transportation": 0.70,
                "urban_planning": 0.65
            },
            
            # Healthcare and Biotech
            "gene_therapy": {
                "pharmaceuticals": 0.85,
                "biotechnology": 0.90,
                "medical_devices": 0.70,
                "diagnostics": 0.75,
                "personalized_medicine": 0.95,
                "rare_diseases": 0.90,
                "cancer_treatment": 0.85,
                "genetic_testing": 0.80,
                "cell_therapy": 0.85,
                "regenerative_medicine": 0.80
            },
            
            "medical_robotics": {
                "healthcare": 0.85,
                "surgery": 0.95,
                "rehabilitation": 0.80,
                "diagnostics": 0.75,
                "elderly_care": 0.70,
                "hospital_automation": 0.85,
                "telemedicine": 0.65,
                "medical_training": 0.70,
                "precision_medicine": 0.75,
                "minimally_invasive": 0.90
            },
            
            # Financial Technology
            "digital_payments": {
                "banking": 0.80,
                "e_commerce": 0.90,
                "retail": 0.85,
                "remittances": 0.95,
                "mobile_commerce": 0.90,
                "peer_to_peer": 0.85,
                "small_business": 0.80,
                "international_trade": 0.75,
                "micropayments": 0.90,
                "subscription_services": 0.85
            },
            
            "cryptocurrency": {
                "digital_payments": 0.85,
                "decentralized_finance": 0.95,
                "cross_border_payments": 0.90,
                "store_of_value": 0.80,
                "gaming": 0.70,
                "nft_markets": 0.95,
                "web3": 0.90,
                "smart_contracts": 0.85,
                "digital_identity": 0.75,
                "supply_chain_tracking": 0.70
            },
            
            # Agriculture and Food
            "precision_agriculture": {
                "traditional_farming": 0.85,
                "crop_monitoring": 0.90,
                "livestock_management": 0.80,
                "irrigation": 0.85,
                "fertilizer": 0.70,
                "pesticides": 0.65,
                "food_safety": 0.75,
                "supply_chain": 0.80,
                "sustainability": 0.85,
                "climate_adaptation": 0.80
            },
            
            "vertical_farming": {
                "traditional_agriculture": 0.60,
                "urban_food_production": 0.95,
                "controlled_environment": 0.90,
                "led_lighting": 0.85,
                "hydroponics": 0.90,
                "automation": 0.80,
                "fresh_produce": 0.85,
                "local_food_systems": 0.90,
                "water_conservation": 0.80,
                "pesticide_free": 0.85
            },
            
            # Real Estate and Construction
            "construction_tech": {
                "traditional_construction": 0.80,
                "project_management": 0.85,
                "building_materials": 0.75,
                "safety": 0.90,
                "efficiency": 0.85,
                "cost_reduction": 0.80,
                "sustainable_building": 0.75,
                "modular_construction": 0.85,
                "infrastructure": 0.80,
                "urban_development": 0.75
            },
            
            "smart_buildings": {
                "real_estate": 0.75,
                "iot_devices": 0.90,
                "energy_management": 0.85,
                "security_systems": 0.80,
                "hvac": 0.85,
                "lighting": 0.80,
                "building_automation": 0.95,
                "tenant_experience": 0.75,
                "sustainability": 0.80,
                "maintenance": 0.85
            },
            
            # Education and Training
            "edtech": {
                "traditional_education": 0.70,
                "remote_learning": 0.95,
                "skill_development": 0.85,
                "corporate_training": 0.80,
                "lifelong_learning": 0.90,
                "certification": 0.85,
                "assessment": 0.80,
                "personalized_learning": 0.85,
                "accessibility": 0.75,
                "global_education": 0.80
            }
        }
    
    def build_influence_matrix(self) -> np.ndarray:
        """Build a matrix showing influence relationships between sectors"""
        sectors = list(self.sectors_data.keys())
        n_sectors = len(sectors)
        matrix = np.zeros((n_sectors, n_sectors))
        
        sector_to_idx = {sector: i for i, sector in enumerate(sectors)}
        
        for influencer, influenced_dict in self.sector_influences.items():
            if influencer in sector_to_idx:
                i = sector_to_idx[influencer]
                for influenced, strength in influenced_dict.items():
                    # Find best match for influenced sector
                    for sector in sectors:
                        if influenced.lower() in sector.lower() or sector.lower() in influenced.lower():
                            j = sector_to_idx[sector]
                            matrix[i, j] = strength
                            break
        
        self.influence_matrix = matrix
        return matrix
    
    def build_supply_chain_graph(self) -> nx.DiGraph:
        """Build a directed graph showing supply chain relationships"""
        G = nx.DiGraph()
        
        # Add nodes for each sector
        for sector in self.sectors_data.keys():
            G.add_node(sector)
        
        # Add edges based on influence relationships
        for influencer, influenced_dict in self.sector_influences.items():
            for influenced, strength in influenced_dict.items():
                # Find matching sectors
                influencer_matches = [s for s in self.sectors_data.keys() 
                                    if influencer.lower() in s.lower() or s.lower() in influencer.lower()]
                influenced_matches = [s for s in self.sectors_data.keys() 
                                    if influenced.lower() in s.lower() or s.lower() in influenced.lower()]
                
                for inf_sector in influencer_matches:
                    for infl_sector in influenced_matches:
                        if inf_sector != infl_sector:
                            G.add_edge(inf_sector, infl_sector, weight=strength, influence=strength)
        
        self.supply_chain_graph = G
        return G
    
    def analyze_sector_centrality(self) -> Dict[str, Dict[str, float]]:
        """Analyze which sectors are most central/influential in the economy"""
        if self.supply_chain_graph is None:
            self.build_supply_chain_graph()
        
        centrality_metrics = {
            'in_degree': nx.in_degree_centrality(self.supply_chain_graph),
            'out_degree': nx.out_degree_centrality(self.supply_chain_graph),
            'betweenness': nx.betweenness_centrality(self.supply_chain_graph),
            'eigenvector': nx.eigenvector_centrality(self.supply_chain_graph, max_iter=1000),
            'pagerank': nx.pagerank(self.supply_chain_graph)
        }
        
        return centrality_metrics
    
    def identify_key_sectors(self, top_n: int = 10) -> Dict[str, List[Tuple[str, float]]]:
        """Identify the most important sectors by different metrics"""
        centrality = self.analyze_sector_centrality()
        
        key_sectors = {}
        for metric, scores in centrality.items():
            sorted_sectors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            key_sectors[metric] = sorted_sectors[:top_n]
        
        return key_sectors
    
    def analyze_supply_chain_vulnerabilities(self) -> Dict[str, List[str]]:
        """Identify potential supply chain vulnerabilities"""
        if self.supply_chain_graph is None:
            self.build_supply_chain_graph()
        
        vulnerabilities = {
            'single_points_of_failure': [],
            'highly_dependent_sectors': [],
            'bottleneck_sectors': []
        }
        
        # Find articulation points (single points of failure)
        undirected_graph = self.supply_chain_graph.to_undirected()
        articulation_points = list(nx.articulation_points(undirected_graph))
        vulnerabilities['single_points_of_failure'] = articulation_points
        
        # Find highly dependent sectors (high in-degree)
        in_degrees = dict(self.supply_chain_graph.in_degree())
        high_dependency = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        vulnerabilities['highly_dependent_sectors'] = [sector for sector, _ in high_dependency]
        
        # Find bottleneck sectors (high betweenness centrality)
        betweenness = nx.betweenness_centrality(self.supply_chain_graph)
        bottlenecks = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
        vulnerabilities['bottleneck_sectors'] = [sector for sector, _ in bottlenecks]
        
        return vulnerabilities
    
    def simulate_sector_disruption(self, disrupted_sector: str, disruption_strength: float = 0.5) -> Dict[str, float]:
        """Simulate the impact of disrupting a specific sector"""
        if self.supply_chain_graph is None:
            self.build_supply_chain_graph()
        
        impact_scores = {}
        
        # Calculate direct impact (immediate downstream effects)
        direct_dependents = list(self.supply_chain_graph.successors(disrupted_sector))
        for dependent in direct_dependents:
            edge_data = self.supply_chain_graph.get_edge_data(disrupted_sector, dependent)
            influence = edge_data.get('influence', 0.5)
            impact_scores[dependent] = influence * disruption_strength
        
        # Calculate indirect impact (cascading effects)
        for sector in self.supply_chain_graph.nodes():
            if sector not in impact_scores and sector != disrupted_sector:
                # Find shortest path impact
                try:
                    path = nx.shortest_path(self.supply_chain_graph, disrupted_sector, sector)
                    if len(path) > 1:
                        # Calculate cascading impact with decay
                        cascading_impact = disruption_strength
                        for i in range(len(path) - 1):
                            edge_data = self.supply_chain_graph.get_edge_data(path[i], path[i+1])
                            if edge_data:
                                cascading_impact *= edge_data.get('influence', 0.5) * 0.8  # Decay factor
                        impact_scores[sector] = cascading_impact
                except nx.NetworkXNoPath:
                    impact_scores[sector] = 0.0
        
        return impact_scores
    
    def visualize_sector_network(self, output_path: str = "reports/sector_network.png", 
                               top_sectors: int = 20):
        """Create a network visualization of sector relationships"""
        if self.supply_chain_graph is None:
            self.build_supply_chain_graph()
        
        # Get top sectors by importance
        centrality = self.analyze_sector_centrality()
        pagerank_scores = centrality['pagerank']
        top_sector_names = [sector for sector, _ in 
                           sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:top_sectors]]
        
        # Create subgraph with only top sectors
        subgraph = self.supply_chain_graph.subgraph(top_sector_names)
        
        plt.figure(figsize=(16, 12))
        
        # Position nodes using spring layout
        pos = nx.spring_layout(subgraph, k=3, iterations=50)
        
        # Node sizes based on PageRank
        node_sizes = [pagerank_scores[node] * 5000 for node in subgraph.nodes()]
        
        # Edge widths based on influence strength
        edge_widths = [subgraph[u][v].get('influence', 0.5) * 3 for u, v in subgraph.edges()]
        
        # Draw the network
        nx.draw_networkx_nodes(subgraph, pos, node_size=node_sizes, 
                              node_color='lightblue', alpha=0.7)
        nx.draw_networkx_edges(subgraph, pos, width=edge_widths, 
                              alpha=0.6, edge_color='gray', arrows=True, arrowsize=20)
        nx.draw_networkx_labels(subgraph, pos, font_size=8, font_weight='bold')
        
        plt.title("Sector Influence Network\n(Node size = PageRank importance, Edge width = Influence strength)", 
                 fontsize=14, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        # Save the plot
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def visualize_influence_heatmap(self, output_path: str = "reports/influence_heatmap.png"):
        """Create a heatmap showing sector influence relationships"""
        if self.influence_matrix is None:
            self.build_influence_matrix()
        
        sectors = list(self.sectors_data.keys())
        
        plt.figure(figsize=(20, 16))
        
        # Create heatmap
        mask = self.influence_matrix == 0  # Mask zero values
        sns.heatmap(self.influence_matrix, 
                   xticklabels=sectors, 
                   yticklabels=sectors,
                   annot=False, 
                   cmap='YlOrRd', 
                   mask=mask,
                   cbar_kws={'label': 'Influence Strength'})
        
        plt.title("Sector Influence Matrix\n(Rows influence Columns)", 
                 fontsize=16, fontweight='bold')
        plt.xlabel("Influenced Sectors", fontsize=12)
        plt.ylabel("Influencing Sectors", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        # Save the plot
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_sector_analysis_report(self) -> Dict[str, any]:
        """Generate a comprehensive sector analysis report"""
        
        # Build analysis components
        self.build_influence_matrix()
        self.build_supply_chain_graph()
        
        # Perform analyses
        centrality_metrics = self.analyze_sector_centrality()
        key_sectors = self.identify_key_sectors()
        vulnerabilities = self.analyze_supply_chain_vulnerabilities()
        
        # Test disruption scenarios
        disruption_scenarios = {}
        test_sectors = ['artificial_intelligence', 'semiconductor_manufacturing', 'renewable_energy']
        for sector in test_sectors:
            if sector in self.supply_chain_graph.nodes():
                disruption_scenarios[sector] = self.simulate_sector_disruption(sector)
        
        report = {
            'analysis_date': datetime.now().isoformat(),
            'total_sectors_analyzed': len(self.sectors_data),
            'network_metrics': {
                'total_nodes': self.supply_chain_graph.number_of_nodes(),
                'total_edges': self.supply_chain_graph.number_of_edges(),
                'network_density': nx.density(self.supply_chain_graph),
                'average_clustering': nx.average_clustering(self.supply_chain_graph.to_undirected())
            },
            'key_sectors_by_metric': key_sectors,
            'supply_chain_vulnerabilities': vulnerabilities,
            'disruption_scenarios': disruption_scenarios,
            'sector_categories': list(self.sectors_data.keys()),
            'investment_implications': self.generate_investment_implications(key_sectors, vulnerabilities)
        }
        
        return report
    
    def generate_investment_implications(self, key_sectors: Dict, vulnerabilities: Dict) -> Dict[str, List[str]]:
        """Generate investment implications based on sector analysis"""
        implications = {
            'high_priority_sectors': [],
            'diversification_opportunities': [],
            'risk_mitigation_strategies': [],
            'growth_catalysts': []
        }
        
        # High priority sectors (high PageRank)
        top_pagerank = [sector for sector, _ in key_sectors.get('pagerank', [])[:5]]
        implications['high_priority_sectors'] = [
            f"Invest in {sector.replace('_', ' ').title()} - high network influence" 
            for sector in top_pagerank
        ]
        
        # Diversification opportunities (low correlation sectors)
        low_influence_sectors = [sector for sector, _ in key_sectors.get('pagerank', [])[-5:]]
        implications['diversification_opportunities'] = [
            f"Consider {sector.replace('_', ' ').title()} for portfolio diversification"
            for sector in low_influence_sectors
        ]
        
        # Risk mitigation
        bottlenecks = vulnerabilities.get('bottleneck_sectors', [])[:3]
        implications['risk_mitigation_strategies'] = [
            f"Monitor {sector.replace('_', ' ').title()} closely - potential bottleneck"
            for sector in bottlenecks
        ]
        
        # Growth catalysts
        high_out_degree = [sector for sector, _ in key_sectors.get('out_degree', [])[:3]]
        implications['growth_catalysts'] = [
            f"Invest in {sector.replace('_', ' ').title()} - drives growth in multiple sectors"
            for sector in high_out_degree
        ]
        
        return implications

def main():
    """Test the sector relationship analyzer"""
    analyzer = SectorRelationshipAnalyzer()
    
    print("🔍 Generating Sector Relationship Analysis...")
    
    # Generate comprehensive report
    report = analyzer.generate_sector_analysis_report()
    
    # Save report
    report_path = Path("reports/sector_analysis_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"✅ Analysis complete! Report saved to {report_path}")
    
    # Print key findings
    print("\n" + "="*60)
    print("KEY FINDINGS")
    print("="*60)
    
    print(f"\n📊 Network Overview:")
    print(f"   • Total sectors analyzed: {report['total_sectors_analyzed']}")
    print(f"   • Network connections: {report['network_metrics']['total_edges']}")
    print(f"   • Network density: {report['network_metrics']['network_density']:.3f}")
    
    print(f"\n🏆 Most Influential Sectors (PageRank):")
    for i, (sector, score) in enumerate(report['key_sectors_by_metric']['pagerank'][:5], 1):
        print(f"   {i}. {sector.replace('_', ' ').title()}: {score:.3f}")
    
    print(f"\n⚠️  Supply Chain Vulnerabilities:")
    vulnerabilities = report['supply_chain_vulnerabilities']
    print(f"   • Bottleneck sectors: {len(vulnerabilities['bottleneck_sectors'])}")
    print(f"   • Single points of failure: {len(vulnerabilities['single_points_of_failure'])}")
    
    print(f"\n💡 Investment Implications:")
    implications = report['investment_implications']
    for category, items in implications.items():
        print(f"\n   {category.replace('_', ' ').title()}:")
        for item in items[:3]:
            print(f"     • {item}")
    
    # Generate visualizations
    print(f"\n📈 Generating visualizations...")
    try:
        analyzer.visualize_sector_network()
        analyzer.visualize_influence_heatmap()
        print("✅ Visualizations saved to reports/ directory")
    except Exception as e:
        print(f"⚠️  Could not generate visualizations: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()