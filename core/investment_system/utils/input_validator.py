"""
Input Validation and Sanitization Module
Provides comprehensive input validation, sanitization, and security controls
"""

import re
import html
import bleach
import json
from typing import Any, Dict, List, Optional, Union, Type
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error for '{field}': {message}")


class SanitizationLevel(Enum):
    """Levels of input sanitization"""
    MINIMAL = "minimal"    # Basic HTML escaping
    STANDARD = "standard"  # Remove dangerous HTML, keep safe formatting  
    STRICT = "strict"      # Strip all HTML and special characters
    FINANCIAL = "financial" # Extra strict for financial data


@dataclass
class ValidationRule:
    """Individual validation rule"""
    name: str
    validator_func: callable
    error_message: str
    required: bool = True


class InputValidator:
    """
    Comprehensive input validation and sanitization system
    """
    
    def __init__(self):
        """Initialize validator with security rules"""
        
        # Allowed HTML tags for standard sanitization
        self.allowed_tags = [
            'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ]
        
        # Allowed HTML attributes
        self.allowed_attributes = {
            '*': ['class'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height']
        }
        
        # SQL injection patterns to detect
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|OR|AND)\b)",
            r"('|('')|(\-\-)|(\;)|(\||(\*|\%|\?))",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR|ONCLICK)\b)",
        ]
        
        # XSS patterns to detect
        self.xss_patterns = [
            r"<\s*script[^>]*>",
            r"javascript\s*:",
            r"on\w+\s*=",
            r"<\s*iframe[^>]*>",
            r"<\s*object[^>]*>",
            r"<\s*embed[^>]*>",
        ]
    
    def sanitize_string(self, value: str, level: SanitizationLevel = SanitizationLevel.STANDARD) -> str:
        """
        Sanitize string input based on specified level
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        if level == SanitizationLevel.MINIMAL:
            # Just escape HTML
            return html.escape(value, quote=True)
        
        elif level == SanitizationLevel.STANDARD:
            # Remove dangerous HTML but keep safe formatting
            return bleach.clean(
                value,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                strip=True
            )
        
        elif level == SanitizationLevel.STRICT:
            # Strip all HTML and limit to alphanumeric + basic punctuation
            cleaned = bleach.clean(value, tags=[], strip=True)
            # Allow letters, numbers, spaces, and basic punctuation
            cleaned = re.sub(r'[^\w\s\-_.,!?@#$%&*()+=\[\]{}|\\:";\'<>]', '', cleaned)
            return cleaned.strip()
        
        elif level == SanitizationLevel.FINANCIAL:
            # Extra strict for financial data
            cleaned = bleach.clean(value, tags=[], strip=True)
            # Only allow letters, numbers, spaces, and minimal punctuation
            cleaned = re.sub(r'[^\w\s\-_.,()]', '', cleaned)
            return cleaned.strip()
        
        return value
    
    def detect_sql_injection(self, value: str) -> bool:
        """Detect potential SQL injection attempts"""
        value_lower = value.lower()
        
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    def detect_xss(self, value: str) -> bool:
        """Detect potential XSS attempts"""
        value_lower = value.lower()
        
        for pattern in self.xss_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    def validate_string(self, value: Any, field_name: str, 
                       min_length: int = 0, max_length: int = 1000,
                       pattern: str = None, required: bool = True,
                       sanitization_level: SanitizationLevel = SanitizationLevel.STANDARD) -> str:
        """Validate and sanitize string input"""
        
        # Check if required
        if not value and required:
            raise ValidationError(field_name, "This field is required")
        
        if not value and not required:
            return ""
        
        # Convert to string
        if not isinstance(value, str):
            value = str(value)
        
        # Check for security threats
        if self.detect_sql_injection(value):
            logger.warning(f"SQL injection attempt detected in field '{field_name}': {value[:100]}")
            raise ValidationError(field_name, "Invalid input detected")
        
        if self.detect_xss(value):
            logger.warning(f"XSS attempt detected in field '{field_name}': {value[:100]}")
            raise ValidationError(field_name, "Invalid input detected")
        
        # Sanitize
        sanitized_value = self.sanitize_string(value, sanitization_level)
        
        # Length validation
        if len(sanitized_value) < min_length:
            raise ValidationError(field_name, f"Must be at least {min_length} characters long")
        
        if len(sanitized_value) > max_length:
            raise ValidationError(field_name, f"Must be no more than {max_length} characters long")
        
        # Pattern validation
        if pattern and not re.match(pattern, sanitized_value):
            raise ValidationError(field_name, "Invalid format")
        
        return sanitized_value
    
    def validate_email(self, value: Any, field_name: str = "email", required: bool = True) -> str:
        """Validate email address"""
        if not value and not required:
            return ""
        
        if not value and required:
            raise ValidationError(field_name, "Email is required")
        
        value = str(value).strip().lower()
        
        # Email pattern (RFC 5322 simplified)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, value):
            raise ValidationError(field_name, "Invalid email format")
        
        # Additional security checks
        if len(value) > 254:  # RFC 5321 limit
            raise ValidationError(field_name, "Email address too long")
        
        # Check for dangerous patterns
        dangerous_patterns = ['script', 'javascript', 'data:', 'vbscript']
        for pattern in dangerous_patterns:
            if pattern in value.lower():
                raise ValidationError(field_name, "Invalid email format")
        
        return value
    
    def validate_number(self, value: Any, field_name: str,
                       min_value: float = None, max_value: float = None,
                       decimal_places: int = None, required: bool = True) -> Union[int, float, Decimal]:
        """Validate numeric input"""
        
        if value is None and not required:
            return None
        
        if value is None and required:
            raise ValidationError(field_name, "This field is required")
        
        # Handle string input
        if isinstance(value, str):
            value = value.strip()
            if not value:
                if required:
                    raise ValidationError(field_name, "This field is required")
                return None
        
        try:
            # Convert to appropriate numeric type
            if decimal_places is not None:
                # Use Decimal for precise decimal arithmetic
                numeric_value = Decimal(str(value))
                
                # Check decimal places
                if numeric_value.as_tuple().exponent < -decimal_places:
                    raise ValidationError(field_name, f"Maximum {decimal_places} decimal places allowed")
                
            elif isinstance(value, int) or (isinstance(value, str) and '.' not in value):
                numeric_value = int(value)
            else:
                numeric_value = float(value)
            
        except (ValueError, InvalidOperation):
            raise ValidationError(field_name, "Invalid number format")
        
        # Range validation
        if min_value is not None and numeric_value < min_value:
            raise ValidationError(field_name, f"Must be at least {min_value}")
        
        if max_value is not None and numeric_value > max_value:
            raise ValidationError(field_name, f"Must be no more than {max_value}")
        
        return numeric_value
    
    def validate_date(self, value: Any, field_name: str,
                     min_date: date = None, max_date: date = None,
                     required: bool = True) -> Optional[date]:
        """Validate date input"""
        
        if value is None and not required:
            return None
        
        if value is None and required:
            raise ValidationError(field_name, "This field is required")
        
        # Handle different input types
        if isinstance(value, date):
            date_value = value
        elif isinstance(value, datetime):
            date_value = value.date()
        elif isinstance(value, str):
            value = value.strip()
            if not value:
                if required:
                    raise ValidationError(field_name, "This field is required")
                return None
            
            # Try common date formats
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S'
            ]
            
            date_value = None
            for date_format in date_formats:
                try:
                    parsed_datetime = datetime.strptime(value, date_format)
                    date_value = parsed_datetime.date()
                    break
                except ValueError:
                    continue
            
            if date_value is None:
                raise ValidationError(field_name, "Invalid date format")
        else:
            raise ValidationError(field_name, "Invalid date type")
        
        # Range validation
        if min_date and date_value < min_date:
            raise ValidationError(field_name, f"Date must be after {min_date}")
        
        if max_date and date_value > max_date:
            raise ValidationError(field_name, f"Date must be before {max_date}")
        
        return date_value
    
    def validate_stock_symbol(self, value: Any, field_name: str = "symbol", required: bool = True) -> str:
        """Validate stock symbol"""
        if not value and not required:
            return ""
        
        if not value and required:
            raise ValidationError(field_name, "Stock symbol is required")
        
        symbol = str(value).strip().upper()
        
        # Stock symbol pattern (1-5 letters, optionally followed by . and more letters)
        symbol_pattern = r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$'
        
        if not re.match(symbol_pattern, symbol):
            raise ValidationError(field_name, "Invalid stock symbol format")
        
        # Length check
        if len(symbol) > 8:
            raise ValidationError(field_name, "Stock symbol too long")
        
        return symbol
    
    def validate_money_amount(self, value: Any, field_name: str,
                             min_amount: Decimal = None, max_amount: Decimal = None,
                             required: bool = True) -> Optional[Decimal]:
        """Validate monetary amounts with high precision"""
        
        if value is None and not required:
            return None
        
        if value is None and required:
            raise ValidationError(field_name, "Amount is required")
        
        # Handle string input
        if isinstance(value, str):
            value = value.strip()
            # Remove currency symbols and commas
            value = re.sub(r'[$,]', '', value)
            
            if not value:
                if required:
                    raise ValidationError(field_name, "Amount is required")
                return None
        
        try:
            # Convert to Decimal for precise monetary calculations
            amount = Decimal(str(value))
            
            # Round to 2 decimal places for money
            amount = amount.quantize(Decimal('0.01'))
            
        except InvalidOperation:
            raise ValidationError(field_name, "Invalid amount format")
        
        # Range validation
        if min_amount is not None and amount < min_amount:
            raise ValidationError(field_name, f"Amount must be at least ${min_amount}")
        
        if max_amount is not None and amount > max_amount:
            raise ValidationError(field_name, f"Amount must be no more than ${max_amount}")
        
        # Reasonable limits for financial data
        if amount < Decimal('-999999999.99') or amount > Decimal('999999999.99'):
            raise ValidationError(field_name, "Amount is outside reasonable limits")
        
        return amount
    
    def validate_json(self, value: Any, field_name: str, 
                     schema: Dict = None, required: bool = True) -> Optional[Dict]:
        """Validate JSON input"""
        
        if value is None and not required:
            return None
        
        if value is None and required:
            raise ValidationError(field_name, "JSON data is required")
        
        # Handle string JSON
        if isinstance(value, str):
            value = value.strip()
            if not value:
                if required:
                    raise ValidationError(field_name, "JSON data is required")
                return None
            
            try:
                json_data = json.loads(value)
            except json.JSONDecodeError as e:
                raise ValidationError(field_name, f"Invalid JSON format: {e}")
        
        elif isinstance(value, dict):
            json_data = value
        else:
            raise ValidationError(field_name, "Invalid JSON type")
        
        # Basic schema validation (simplified)
        if schema:
            for required_key in schema.get('required', []):
                if required_key not in json_data:
                    raise ValidationError(field_name, f"Missing required field: {required_key}")
        
        # Size limit for security
        json_str = json.dumps(json_data)
        if len(json_str) > 100000:  # 100KB limit
            raise ValidationError(field_name, "JSON data too large")
        
        return json_data
    
    def validate_dict(self, data: Dict[str, Any], validation_rules: Dict[str, List[ValidationRule]]) -> Dict[str, Any]:
        """
        Validate a dictionary of data against validation rules
        """
        validated_data = {}
        errors = {}
        
        for field_name, rules in validation_rules.items():
            field_value = data.get(field_name)
            
            try:
                for rule in rules:
                    if field_value is None and not rule.required:
                        validated_data[field_name] = None
                        break
                    
                    if field_value is None and rule.required:
                        raise ValidationError(field_name, "This field is required")
                    
                    # Apply validation rule
                    validated_value = rule.validator_func(field_value, field_name)
                    validated_data[field_name] = validated_value
                    
            except ValidationError as e:
                errors[field_name] = e.message
        
        if errors:
            raise ValidationError("validation", f"Multiple validation errors: {errors}", errors)
        
        return validated_data


# Global validator instance
_validator: Optional[InputValidator] = None


def get_validator() -> InputValidator:
    """Get the global input validator instance"""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator


# Convenience functions
def validate_string(value: Any, field_name: str, **kwargs) -> str:
    """Convenience function for string validation"""
    return get_validator().validate_string(value, field_name, **kwargs)


def validate_email(value: Any, field_name: str = "email", **kwargs) -> str:
    """Convenience function for email validation"""
    return get_validator().validate_email(value, field_name, **kwargs)


def validate_number(value: Any, field_name: str, **kwargs) -> Union[int, float, Decimal]:
    """Convenience function for number validation"""
    return get_validator().validate_number(value, field_name, **kwargs)


def validate_stock_symbol(value: Any, field_name: str = "symbol", **kwargs) -> str:
    """Convenience function for stock symbol validation"""
    return get_validator().validate_stock_symbol(value, field_name, **kwargs)


def validate_money_amount(value: Any, field_name: str, **kwargs) -> Optional[Decimal]:
    """Convenience function for money amount validation"""
    return get_validator().validate_money_amount(value, field_name, **kwargs)


def sanitize_string(value: str, level: SanitizationLevel = SanitizationLevel.STANDARD) -> str:
    """Convenience function for string sanitization"""
    return get_validator().sanitize_string(value, level)


if __name__ == "__main__":
    # Test validation functions
    validator = InputValidator()
    
    # Test string validation
    try:
        result = validator.validate_string("Hello <script>alert('xss')</script>", "test")
        print(f"Sanitized string: {result}")
    except ValidationError as e:
        print(f"Validation error: {e}")
    
    # Test email validation
    try:
        email = validator.validate_email("user@example.com", "email")
        print(f"Valid email: {email}")
    except ValidationError as e:
        print(f"Email error: {e}")
    
    # Test money validation
    try:
        amount = validator.validate_money_amount("$1,234.56", "amount")
        print(f"Valid amount: ${amount}")
    except ValidationError as e:
        print(f"Amount error: {e}")