"""
Dynamic API router that builds routes from endpoints.yaml.
Single source of truth for all API endpoints.
"""

import yaml
import importlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from investment_system.api.deps import (
    get_auth_dependency,
    get_rate_limiter_dependency,
    idempotency_dependency,
    get_tier_dependency
)


class EndpointCatalog:
    """Manages API endpoints from YAML configuration."""
    
    def __init__(self, config_path: str = "src/investment_system/api/endpoints.yaml"):
        """
        Initialize endpoint catalog.
        
        Args:
            config_path: Path to endpoints.yaml file
        """
        self.config_path = Path(config_path)
        self.endpoints = self._load_endpoints()
        self._validate_endpoints()
    
    def _load_endpoints(self) -> Dict[str, Any]:
        """Load endpoints from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Endpoints file not found: {self.config_path}")
        
        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)
        
        return {
            "version": data.get("version", 1),
            "metadata": data.get("metadata", {}),
            "services": data.get("services", [])
        }
    
    def _validate_endpoints(self):
        """Validate endpoint configuration."""
        required_fields = ["id", "path", "method", "handler", "auth", "tier", "rate"]
        
        for service in self.endpoints["services"]:
            for field in required_fields:
                if field not in service:
                    raise ValueError(f"Missing required field '{field}' in endpoint {service.get('id', 'unknown')}")
    
    def get_endpoint(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get endpoint configuration by ID.
        
        Args:
            endpoint_id: Endpoint identifier
            
        Returns:
            Endpoint configuration or None
        """
        for service in self.endpoints["services"]:
            if service["id"] == endpoint_id:
                return service
        return None
    
    def get_endpoints_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get all endpoints with specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of endpoints with the tag
        """
        return [
            service for service in self.endpoints["services"]
            if tag in service.get("tags", [])
        ]
    
    def get_all_endpoints(self) -> List[Dict[str, Any]]:
        """Get all endpoint configurations."""
        return self.endpoints["services"]


class DynamicRouter:
    """Builds FastAPI router from endpoint catalog."""
    
    def __init__(self, catalog: Optional[EndpointCatalog] = None):
        """
        Initialize dynamic router.
        
        Args:
            catalog: Endpoint catalog instance
        """
        self.catalog = catalog or EndpointCatalog()
        self.router = APIRouter()
        self._handler_cache = {}
    
    def _resolve_handler(self, handler_path: str) -> Callable:
        """
        Resolve handler function from module path.
        
        Args:
            handler_path: Path in format "module.path:function_name"
            
        Returns:
            Handler function
        """
        if handler_path in self._handler_cache:
            return self._handler_cache[handler_path]
        
        try:
            module_path, function_name = handler_path.split(":")
            
            # Handle relative imports
            if module_path.startswith("api.handlers"):
                module_path = f"investment_system.{module_path}"
            
            module = importlib.import_module(module_path)
            handler = getattr(module, function_name)
            
            self._handler_cache[handler_path] = handler
            return handler
        except Exception as e:
            raise ImportError(f"Failed to resolve handler '{handler_path}': {e}")
    
    def _build_dependencies(self, service: Dict[str, Any]) -> List[Depends]:
        """
        Build dependencies for endpoint.
        
        Args:
            service: Service configuration
            
        Returns:
            List of FastAPI dependencies
        """
        dependencies = []
        
        # Add rate limiting
        if service["rate"] != "unlimited":
            dependencies.append(
                Depends(get_rate_limiter_dependency(
                    service["rate"],
                    service.get("tier_limits", {})
                ))
            )
        
        # Add authentication
        if service["auth"] != "none":
            dependencies.append(
                Depends(get_auth_dependency(service["auth"]))
            )
        
        # Add tier checking
        if service["tier"] not in ["all", "none"]:
            dependencies.append(
                Depends(get_tier_dependency(service["tier"]))
            )
        
        # Add idempotency for mutating operations
        if service["method"] in ["POST", "PUT", "PATCH", "DELETE"]:
            dependencies.append(Depends(idempotency_dependency()))
        
        return dependencies
    
    def build(self) -> APIRouter:
        """
        Build FastAPI router from endpoint catalog.
        
        Returns:
            Configured FastAPI router
        """
        for service in self.catalog.get_all_endpoints():
            try:
                # Skip if handler not implemented yet
                handler_path = service["handler"]
                if ":" not in handler_path:
                    continue
                
                # Try to resolve handler
                try:
                    handler = self._resolve_handler(handler_path)
                except ImportError:
                    # Handler not implemented yet, skip
                    print(f"Warning: Handler not found for {service['id']}: {handler_path}")
                    continue
                
                # Build dependencies
                dependencies = self._build_dependencies(service)
                
                # Add route to router
                self.router.add_api_route(
                    path=service["path"],
                    endpoint=handler,
                    methods=[service["method"]],
                    dependencies=dependencies,
                    tags=service.get("tags", []),
                    name=service["id"],
                    description=service.get("description", ""),
                    response_model=service.get("response_model"),
                    status_code=service.get("status_code", 200)
                )
                
            except Exception as e:
                print(f"Error adding route {service['id']}: {e}")
        
        return self.router


def get_endpoint_url(endpoint_id: str) -> str:
    """
    Get URL for endpoint by ID.
    
    Args:
        endpoint_id: Endpoint identifier
        
    Returns:
        Endpoint URL path
    """
    catalog = EndpointCatalog()
    endpoint = catalog.get_endpoint(endpoint_id)
    if not endpoint:
        raise ValueError(f"Endpoint '{endpoint_id}' not found")
    return endpoint["path"]


def get_endpoint_config(endpoint_id: str) -> Dict[str, Any]:
    """
    Get full configuration for endpoint.
    
    Args:
        endpoint_id: Endpoint identifier
        
    Returns:
        Endpoint configuration
    """
    catalog = EndpointCatalog()
    endpoint = catalog.get_endpoint(endpoint_id)
    if not endpoint:
        raise ValueError(f"Endpoint '{endpoint_id}' not found")
    return endpoint


# Global router instance
def create_dynamic_router() -> APIRouter:
    """Create and configure dynamic router."""
    router_builder = DynamicRouter()
    return router_builder.build()