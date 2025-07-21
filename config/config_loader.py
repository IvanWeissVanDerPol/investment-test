"""
Configuration Loader Utility

Centralized configuration management for the Investment Analysis System.
Loads and validates all configuration files with caching and error handling.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """Centralized configuration manager for all system settings"""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize configuration manager
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_duration = timedelta(minutes=30)  # Cache configs for 30 minutes
        
        # Configuration file mappings - consolidated structure
        self.config_files = {
            'data': 'data.json',           # companies, institutions, ethics
            'system': 'system.json',       # network, api_keys, timeframes
            'analysis': 'analysis.json',   # analysis_parameters, thresholds
            'content': 'content.json'      # social_platforms, file_patterns
        }
        
        # Validate config directory exists
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Configuration directory not found: {self.config_dir}")
    
    def load_config(self, config_name: str, use_cache: bool = True) -> Dict[str, Any]:
        """Load a specific configuration file
        
        Args:
            config_name: Name of the configuration (key from config_files)
            use_cache: Whether to use cached version if available
            
        Returns:
            Dictionary containing configuration data
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If configuration file is invalid JSON
        """
        # Check cache first
        if use_cache and self._is_cache_valid(config_name):
            logger.debug(f"Using cached configuration for {config_name}")
            return self.cache[config_name]
        
        # Get file path
        if config_name not in self.config_files:
            raise ValueError(f"Unknown configuration: {config_name}")
        
        config_file = self.config_dir / self.config_files[config_name]
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Cache the configuration
            self.cache[config_name] = config_data
            self.cache_timestamps[config_name] = datetime.now()
            
            logger.debug(f"Loaded configuration from {config_file}")
            return config_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {config_file}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration {config_file}: {e}")
            raise
    
    def load_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load all configuration files
        
        Returns:
            Dictionary with all configuration data
        """
        all_configs = {}
        
        for config_name in self.config_files.keys():
            try:
                all_configs[config_name] = self.load_config(config_name)
            except Exception as e:
                logger.error(f"Failed to load {config_name} configuration: {e}")
                # Continue loading other configs
                
        return all_configs
    
    def get_stock_symbols(self, category: str = None) -> List[str]:
        """Get stock symbols from data configuration
        
        Args:
            category: Specific category (e.g., 'ai_software', 'green_investments')
            
        Returns:
            List of stock symbols
        """
        data_config = self.load_config('data')
        companies_config = data_config.get('companies', {})
        
        if category:
            # Look in stock_universe first
            if category in companies_config.get('stock_universe', {}):
                return companies_config['stock_universe'][category]
            
            # Look in green_investments
            if category in companies_config.get('green_investments', {}):
                return companies_config['green_investments'][category]
            
            # Look in etfs
            if category in companies_config.get('etfs', {}):
                return companies_config['etfs'][category]
                
            return []
        
        # Return all symbols if no category specified
        all_symbols = set()
        
        for universe in ['stock_universe', 'green_investments', 'etfs']:
            if universe in companies_config:
                for symbols in companies_config[universe].values():
                    all_symbols.update(symbols)
        
        return list(all_symbols)
    
    def get_company_metadata(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific company
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company metadata dictionary or None if not found
        """
        data_config = self.load_config('data')
        companies_config = data_config.get('companies', {})
        return companies_config.get('company_metadata', {}).get(symbol)
    
    def get_analysis_threshold(self, threshold_type: str, threshold_name: str) -> Any:
        """Get a specific analysis threshold
        
        Args:
            threshold_type: Type of threshold (e.g., 'data_quality', 'risk_management')
            threshold_name: Name of the threshold
            
        Returns:
            Threshold value
        """
        analysis_config = self.load_config('analysis')
        thresholds_config = analysis_config.get('thresholds', {})
        return thresholds_config.get(threshold_type, {}).get(threshold_name)
    
    def get_api_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """Get API configuration for a provider
        
        Args:
            provider: API provider name
            
        Returns:
            API configuration dictionary or None if not found
        """
        system_config = self.load_config('system')
        api_config = system_config.get('api_keys', {})
        return api_config.get('api_providers', {}).get(provider)
    
    def get_network_config(self, service: str) -> Optional[Dict[str, Any]]:
        """Get network configuration for a service
        
        Args:
            service: Service name (e.g., 'interactive_brokers')
            
        Returns:
            Network configuration dictionary or None if not found
        """
        system_config = self.load_config('system')
        network_config = system_config.get('network', {})
        return network_config.get(service)
    
    def get_timeframe_config(self, category: str) -> Optional[Dict[str, Any]]:
        """Get timeframe configuration for a category
        
        Args:
            category: Category name (e.g., 'data_collection', 'cache_settings')
            
        Returns:
            Timeframe configuration dictionary or None if not found
        """
        system_config = self.load_config('system')
        timeframes_config = system_config.get('timeframes', {})
        return timeframes_config.get(category)
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate all configuration files
        
        Returns:
            Dictionary with validation errors for each config file
        """
        validation_errors = {}
        
        for config_name in self.config_files.keys():
            errors = []
            
            try:
                config_data = self.load_config(config_name, use_cache=False)
                
                # Perform basic validation
                if not isinstance(config_data, dict):
                    errors.append("Configuration must be a JSON object")
                
                if not config_data:
                    errors.append("Configuration is empty")
                
                # Specific validations
                if config_name == 'data':
                    errors.extend(self._validate_data_config(config_data))
                elif config_name == 'analysis':
                    errors.extend(self._validate_analysis_config(config_data))
                elif config_name == 'system':
                    errors.extend(self._validate_system_config(config_data))
                elif config_name == 'content':
                    errors.extend(self._validate_content_config(config_data))
                    
            except Exception as e:
                errors.append(f"Failed to load configuration: {str(e)}")
            
            if errors:
                validation_errors[config_name] = errors
        
        return validation_errors
    
    def reload_config(self, config_name: str) -> Dict[str, Any]:
        """Force reload a configuration file (bypass cache)
        
        Args:
            config_name: Name of the configuration to reload
            
        Returns:
            Reloaded configuration data
        """
        return self.load_config(config_name, use_cache=False)
    
    def clear_cache(self):
        """Clear all cached configurations"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Configuration cache cleared")
    
    def _is_cache_valid(self, config_name: str) -> bool:
        """Check if cached configuration is still valid
        
        Args:
            config_name: Name of the configuration
            
        Returns:
            True if cache is valid, False otherwise
        """
        if config_name not in self.cache:
            return False
        
        if config_name not in self.cache_timestamps:
            return False
        
        cache_age = datetime.now() - self.cache_timestamps[config_name]
        return cache_age < self.cache_duration
    
    def _validate_data_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate data configuration"""
        errors = []
        
        required_sections = ['companies', 'institutions', 'ethics']
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Validate companies section
        if 'companies' in config:
            companies = config['companies']
            if 'stock_universe' not in companies:
                errors.append("Missing stock_universe in companies section")
            if 'company_metadata' not in companies:
                errors.append("Missing company_metadata in companies section")
                
            # Validate company metadata
            if 'company_metadata' in companies:
                for symbol, metadata in companies['company_metadata'].items():
                    if not isinstance(metadata, dict):
                        errors.append(f"Invalid metadata for {symbol}")
                        continue
                    
                    required_fields = ['name', 'sector']
                    for field in required_fields:
                        if field not in metadata:
                            errors.append(f"Missing {field} for {symbol}")
        
        return errors
    
    def _validate_analysis_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate analysis configuration"""
        errors = []
        
        required_sections = ['analysis_parameters', 'thresholds']
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Check that numeric thresholds are actually numbers
        if 'thresholds' in config:
            for category, thresholds in config['thresholds'].items():
                if isinstance(thresholds, dict):
                    for name, value in thresholds.items():
                        if isinstance(value, str) and name.endswith(('_percent', '_threshold', '_limit')):
                            errors.append(f"Threshold {category}.{name} should be numeric, got string")
        
        return errors
    
    def _validate_system_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate system configuration"""
        errors = []
        
        required_sections = ['network', 'api_keys', 'timeframes']
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Validate API keys section
        if 'api_keys' in config and 'api_providers' in config['api_keys']:
            for provider, provider_config in config['api_keys']['api_providers'].items():
                if 'api_key' not in provider_config:
                    errors.append(f"Missing api_key for {provider}")
                if 'base_url' not in provider_config:
                    errors.append(f"Missing base_url for {provider}")
        
        return errors
    
    def _validate_content_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate content configuration"""
        errors = []
        
        required_sections = ['social_platforms', 'file_patterns']
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        return errors


# Global configuration manager instance
config_manager = ConfigurationManager()

# Convenience functions for common operations
def get_stock_symbols(category: str = None) -> List[str]:
    """Get stock symbols from configuration"""
    return config_manager.get_stock_symbols(category)

def get_company_metadata(symbol: str) -> Optional[Dict[str, Any]]:
    """Get company metadata"""
    return config_manager.get_company_metadata(symbol)

def get_threshold(threshold_type: str, threshold_name: str) -> Any:
    """Get analysis threshold"""
    return config_manager.get_analysis_threshold(threshold_type, threshold_name)

def get_api_config(provider: str) -> Optional[Dict[str, Any]]:
    """Get API configuration"""
    return config_manager.get_api_config(provider)

def load_config(config_name: str) -> Dict[str, Any]:
    """Load configuration file"""
    return config_manager.load_config(config_name)
