#!/usr/bin/env python3
"""
Security Audit and Compliance Tool
Comprehensive security assessment and compliance checking for InvestmentAI
"""

import os
import sys
import json
import hashlib
import secrets
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging
import requests
import ssl
import socket
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """Security audit finding"""
    category: str  # 'critical', 'high', 'medium', 'low', 'info'
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None
    cve_id: Optional[str] = None
    compliance_framework: Optional[str] = None


@dataclass
class ComplianceResult:
    """Compliance check result"""
    framework: str  # 'GDPR', 'SOC2', 'PCI-DSS', 'NIST', etc.
    control_id: str
    control_name: str
    status: str  # 'pass', 'fail', 'partial', 'not_applicable'
    findings: List[SecurityFinding]
    evidence: Optional[str] = None


@dataclass
class SecurityAuditReport:
    """Complete security audit report"""
    timestamp: datetime
    target_system: str
    findings: List[SecurityFinding]
    compliance_results: List[ComplianceResult]
    summary: Dict[str, int]
    recommendations: List[str]
    risk_score: float  # 0-100


class SecurityScanner:
    """Security vulnerability scanner"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.findings: List[SecurityFinding] = []
        
        # Vulnerability patterns
        self.vulnerability_patterns = {
            'hardcoded_secrets': [
                (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded password detected'),
                (r'api_key\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded API key detected'),
                (r'secret_key\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded secret key detected'),
                (r'private_key\s*=\s*["\'][^"\']{32,}["\']', 'Hardcoded private key detected'),
                (r'token\s*=\s*["\'][^"\']{16,}["\']', 'Hardcoded token detected'),
            ],
            'sql_injection': [
                (r'query\s*=\s*["\'].*%s.*["\']', 'Potential SQL injection vulnerability'),
                (r'execute\(["\'][^"\']*\+.*["\']', 'Potential SQL injection via concatenation'),
                (r'cursor\.execute\([^)]*format\(', 'SQL injection via string formatting'),
            ],
            'xss_vulnerabilities': [
                (r'innerHTML\s*=\s*.*\+', 'Potential XSS via innerHTML'),
                (r'document\.write\(.*\+', 'Potential XSS via document.write'),
                (r'render_template_string\([^)]*\+', 'Template injection vulnerability'),
            ],
            'insecure_random': [
                (r'random\.random\(\)', 'Insecure random number generation'),
                (r'random\.randint\(', 'Insecure random number generation'),
                (r'Math\.random\(\)', 'Insecure random number generation'),
            ],
            'insecure_protocols': [
                (r'http://[^"\'>\s]+', 'Insecure HTTP protocol detected'),
                (r'ftp://[^"\'>\s]+', 'Insecure FTP protocol detected'),
                (r'telnet://', 'Insecure Telnet protocol detected'),
            ],
            'debug_info': [
                (r'debug\s*=\s*True', 'Debug mode enabled'),
                (r'DEBUG\s*=\s*True', 'Debug mode enabled'),
                (r'console\.log\(', 'Debug console.log statements'),
                (r'print\(["\'][^"\']*password', 'Password printed to console'),
            ],
            'weak_crypto': [
                (r'md5\(', 'Weak MD5 hashing algorithm'),
                (r'sha1\(', 'Weak SHA1 hashing algorithm'),
                (r'DES\(', 'Weak DES encryption algorithm'),
            ]
        }
    
    def scan_code_vulnerabilities(self) -> List[SecurityFinding]:
        """Scan source code for security vulnerabilities"""
        logger.info("Scanning source code for vulnerabilities...")
        
        findings = []
        
        # Scan Python files
        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Check each vulnerability pattern
                for category, patterns in self.vulnerability_patterns.items():
                    for pattern, description in patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            
                            # Determine severity
                            if category in ['hardcoded_secrets', 'sql_injection']:
                                severity = 'critical'
                            elif category in ['xss_vulnerabilities', 'weak_crypto']:
                                severity = 'high'
                            elif category in ['insecure_protocols', 'insecure_random']:
                                severity = 'medium'
                            else:
                                severity = 'low'
                            
                            finding = SecurityFinding(
                                category=severity,
                                title=f"{category.replace('_', ' ').title()} Vulnerability",
                                description=description,
                                file_path=str(py_file.relative_to(self.project_root)),
                                line_number=line_num,
                                recommendation=self._get_recommendation(category)
                            )
                            findings.append(finding)
                            
            except Exception as e:
                logger.warning(f"Failed to scan {py_file}: {e}")
        
        # Scan JavaScript files
        for js_file in self.project_root.rglob("*.js"):
            if self._should_skip_file(js_file):
                continue
            
            try:
                with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check for common JS vulnerabilities
                js_patterns = [
                    (r'eval\(', 'Code injection via eval()'),
                    (r'innerHTML\s*=\s*.*\+', 'XSS via innerHTML'),
                    (r'document\.write\(.*\+', 'XSS via document.write'),
                    (r'window\.location\s*=.*\+', 'Open redirect vulnerability'),
                ]
                
                for pattern, description in js_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        
                        finding = SecurityFinding(
                            category='high',
                            title="JavaScript Security Vulnerability",
                            description=description,
                            file_path=str(js_file.relative_to(self.project_root)),
                            line_number=line_num,
                            recommendation="Sanitize user input and avoid dynamic code execution"
                        )
                        findings.append(finding)
                        
            except Exception as e:
                logger.warning(f"Failed to scan {js_file}: {e}")
        
        return findings
    
    def check_dependencies(self) -> List[SecurityFinding]:
        """Check for vulnerable dependencies"""
        logger.info("Checking dependencies for known vulnerabilities...")
        
        findings = []
        
        # Check Python dependencies
        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists():
            try:
                # Run safety check (if available)
                result = subprocess.run([
                    'safety', 'check', '-r', str(requirements_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("No known vulnerabilities in Python dependencies")
                else:
                    # Parse safety output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'vulnerability' in line.lower():
                            finding = SecurityFinding(
                                category='high',
                                title="Vulnerable Python Dependency",
                                description=line.strip(),
                                file_path='requirements.txt',
                                recommendation="Update to the latest secure version"
                            )
                            findings.append(finding)
                            
            except FileNotFoundError:
                finding = SecurityFinding(
                    category='info',
                    title="Safety Tool Not Found",
                    description="Install 'safety' package to check for vulnerable dependencies",
                    recommendation="pip install safety"
                )
                findings.append(finding)
            except Exception as e:
                logger.warning(f"Dependency check failed: {e}")
        
        # Check Node.js dependencies
        package_json = self.project_root / 'package.json'
        if package_json.exists():
            try:
                result = subprocess.run([
                    'npm', 'audit', '--json'
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.stdout:
                    audit_data = json.loads(result.stdout)
                    
                    for vuln in audit_data.get('vulnerabilities', {}):
                        finding = SecurityFinding(
                            category='high',
                            title="Vulnerable Node.js Dependency",
                            description=f"Vulnerability in {vuln}",
                            file_path='package.json',
                            recommendation="Run 'npm audit fix' to resolve"
                        )
                        findings.append(finding)
                        
            except Exception as e:
                logger.warning(f"npm audit failed: {e}")
        
        return findings
    
    def check_file_permissions(self) -> List[SecurityFinding]:
        """Check file permissions for security issues"""
        logger.info("Checking file permissions...")
        
        findings = []
        
        # Skip on Windows
        if os.name == 'nt':
            return findings
        
        sensitive_files = [
            '.env',
            'config/config.json',
            'private_key.pem',
            'ssl_cert.pem'
        ]
        
        for file_pattern in sensitive_files:
            for file_path in self.project_root.rglob(file_pattern):
                try:
                    stat = file_path.stat()
                    mode = stat.st_mode & 0o777
                    
                    # Check if file is world-readable
                    if mode & 0o004:
                        finding = SecurityFinding(
                            category='medium',
                            title="Sensitive File World-Readable",
                            description=f"File {file_path} is readable by all users",
                            file_path=str(file_path.relative_to(self.project_root)),
                            recommendation=f"Run: chmod 600 {file_path}"
                        )
                        findings.append(finding)
                    
                    # Check if file is world-writable
                    if mode & 0o002:
                        finding = SecurityFinding(
                            category='high',
                            title="Sensitive File World-Writable",
                            description=f"File {file_path} is writable by all users",
                            file_path=str(file_path.relative_to(self.project_root)),
                            recommendation=f"Run: chmod 600 {file_path}"
                        )
                        findings.append(finding)
                        
                except Exception as e:
                    logger.warning(f"Failed to check permissions for {file_path}: {e}")
        
        return findings
    
    def check_ssl_configuration(self, url: str) -> List[SecurityFinding]:
        """Check SSL/TLS configuration"""
        logger.info(f"Checking SSL configuration for {url}")
        
        findings = []
        
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            if parsed_url.scheme != 'https':
                finding = SecurityFinding(
                    category='high',
                    title="Insecure HTTP Protocol",
                    description=f"Application is using HTTP instead of HTTPS",
                    recommendation="Enable HTTPS with valid SSL certificate"
                )
                findings.append(finding)
                return findings
            
            # Check SSL certificate
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Check expiration
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_to_expiry = (not_after - datetime.now()).days
                    
                    if days_to_expiry < 30:
                        finding = SecurityFinding(
                            category='high' if days_to_expiry < 7 else 'medium',
                            title="SSL Certificate Expiring Soon",
                            description=f"SSL certificate expires in {days_to_expiry} days",
                            recommendation="Renew SSL certificate before expiration"
                        )
                        findings.append(finding)
                    
                    # Check cipher suite
                    cipher = ssock.cipher()
                    if cipher and 'RC4' in cipher[0]:
                        finding = SecurityFinding(
                            category='medium',
                            title="Weak SSL Cipher",
                            description=f"Weak cipher suite in use: {cipher[0]}",
                            recommendation="Configure server to use strong cipher suites"
                        )
                        findings.append(finding)
                        
        except Exception as e:
            finding = SecurityFinding(
                category='medium',
                title="SSL Check Failed",
                description=f"Could not verify SSL configuration: {e}",
                recommendation="Manually verify SSL configuration"
            )
            findings.append(finding)
        
        return findings
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during scanning"""
        skip_patterns = [
            '.git/',
            '__pycache__/',
            '.pytest_cache/',
            'node_modules/',
            '.venv/',
            'venv/',
            '.env',
            'test_',
            '_test.py',
            '.min.js',
            'vendor/',
            'third_party/'
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)
    
    def _get_recommendation(self, category: str) -> str:
        """Get security recommendation for vulnerability category"""
        recommendations = {
            'hardcoded_secrets': "Use environment variables or secure key management",
            'sql_injection': "Use parameterized queries and input validation",
            'xss_vulnerabilities': "Sanitize all user input and use Content Security Policy",
            'insecure_random': "Use cryptographically secure random number generators",
            'insecure_protocols': "Use HTTPS/TLS for all communications",
            'debug_info': "Disable debug mode in production",
            'weak_crypto': "Use strong cryptographic algorithms (SHA-256, AES-256)"
        }
        return recommendations.get(category, "Follow security best practices")


class ComplianceChecker:
    """Compliance framework checker"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        
    def check_gdpr_compliance(self) -> List[ComplianceResult]:
        """Check GDPR compliance"""
        logger.info("Checking GDPR compliance...")
        
        results = []
        
        # Data Processing Documentation
        privacy_policy = self.project_root / 'docs' / 'privacy_policy.md'
        result = ComplianceResult(
            framework='GDPR',
            control_id='Art.13',
            control_name='Information to be provided - Data Collection',
            status='fail' if not privacy_policy.exists() else 'pass',
            findings=[
                SecurityFinding(
                    category='medium',
                    title="Privacy Policy Missing",
                    description="No privacy policy documentation found",
                    recommendation="Create comprehensive privacy policy"
                )
            ] if not privacy_policy.exists() else []
        )
        results.append(result)
        
        # Data Encryption (Art. 32)
        env_file = self.project_root / '.env'
        has_encryption = False
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    has_encryption = 'ENCRYPTION_KEY' in content
            except:
                pass
        
        result = ComplianceResult(
            framework='GDPR',
            control_id='Art.32',
            control_name='Security of Processing - Encryption',
            status='pass' if has_encryption else 'partial',
            findings=[
                SecurityFinding(
                    category='medium',
                    title="Data Encryption Not Configured",
                    description="No encryption configuration found",
                    recommendation="Implement data encryption for sensitive information"
                )
            ] if not has_encryption else []
        )
        results.append(result)
        
        # Audit Logging (Art. 30)
        audit_logs = list(self.project_root.rglob("*audit*"))
        result = ComplianceResult(
            framework='GDPR',
            control_id='Art.30',
            control_name='Records of Processing Activities',
            status='pass' if audit_logs else 'fail',
            findings=[
                SecurityFinding(
                    category='medium',
                    title="Audit Logging Missing",
                    description="No audit logging implementation found",
                    recommendation="Implement comprehensive audit logging"
                )
            ] if not audit_logs else []
        )
        results.append(result)
        
        return results
    
    def check_soc2_compliance(self) -> List[ComplianceResult]:
        """Check SOC 2 compliance"""
        logger.info("Checking SOC 2 compliance...")
        
        results = []
        
        # Access Controls (CC6.1)
        auth_files = list(self.project_root.rglob("*auth*"))
        result = ComplianceResult(
            framework='SOC2',
            control_id='CC6.1',
            control_name='Logical and Physical Access Controls',
            status='pass' if auth_files else 'fail',
            findings=[
                SecurityFinding(
                    category='high',
                    title="Access Controls Missing",
                    description="No authentication system found",
                    recommendation="Implement role-based access controls"
                )
            ] if not auth_files else []
        )
        results.append(result)
        
        # System Monitoring (CC7.1)
        monitoring_files = list(self.project_root.rglob("*monitor*"))
        result = ComplianceResult(
            framework='SOC2',
            control_id='CC7.1',
            control_name='System Monitoring',
            status='pass' if monitoring_files else 'fail',
            findings=[
                SecurityFinding(
                    category='medium',
                    title="System Monitoring Missing",
                    description="No monitoring system found",
                    recommendation="Implement system monitoring and alerting"
                )
            ] if not monitoring_files else []
        )
        results.append(result)
        
        # Change Management (CC8.1)
        version_control = (self.project_root / '.git').exists()
        result = ComplianceResult(
            framework='SOC2',
            control_id='CC8.1',
            control_name='Change Management',
            status='pass' if version_control else 'fail',
            findings=[
                SecurityFinding(
                    category='low',
                    title="Version Control Missing",
                    description="No version control system found",
                    recommendation="Use Git for version control"
                )
            ] if not version_control else []
        )
        results.append(result)
        
        return results
    
    def check_nist_compliance(self) -> List[ComplianceResult]:
        """Check NIST Cybersecurity Framework compliance"""
        logger.info("Checking NIST compliance...")
        
        results = []
        
        # Identity and Access Management (PR.AC)
        auth_system = len(list(self.project_root.rglob("*auth*"))) > 0
        result = ComplianceResult(
            framework='NIST',
            control_id='PR.AC-1',
            control_name='Identity and Access Management',
            status='pass' if auth_system else 'partial',
            findings=[] if auth_system else [
                SecurityFinding(
                    category='medium',
                    title="IAM System Incomplete",
                    description="Identity and access management system needs improvement",
                    recommendation="Implement comprehensive IAM controls"
                )
            ]
        )
        results.append(result)
        
        # Data Protection (PR.DS)
        has_encryption = self._check_encryption_implementation()
        result = ComplianceResult(
            framework='NIST',
            control_id='PR.DS-1',
            control_name='Data-at-rest Protection',
            status='pass' if has_encryption else 'fail',
            findings=[] if has_encryption else [
                SecurityFinding(
                    category='high',
                    title="Data Encryption Missing",
                    description="Data at rest encryption not implemented",
                    recommendation="Implement database and file encryption"
                )
            ]
        )
        results.append(result)
        
        # Security Continuous Monitoring (DE.CM)
        monitoring_system = len(list(self.project_root.rglob("*monitor*"))) > 0
        result = ComplianceResult(
            framework='NIST',
            control_id='DE.CM-1',
            control_name='Security Continuous Monitoring',
            status='pass' if monitoring_system else 'partial',
            findings=[] if monitoring_system else [
                SecurityFinding(
                    category='medium',
                    title="Continuous Monitoring Incomplete",
                    description="Security monitoring system needs enhancement",
                    recommendation="Implement comprehensive security monitoring"
                )
            ]
        )
        results.append(result)
        
        return results
    
    def _check_encryption_implementation(self) -> bool:
        """Check if encryption is properly implemented"""
        env_file = self.project_root / '.env'
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    return 'ENCRYPTION_KEY' in content
            except:
                pass
        return False


class SecurityAuditor:
    """Main security audit orchestrator"""
    
    def __init__(self, project_root: Path, target_url: Optional[str] = None):
        self.project_root = project_root
        self.target_url = target_url or "http://localhost:5000"
        
        self.scanner = SecurityScanner(project_root)
        self.compliance_checker = ComplianceChecker(project_root)
        
    def run_comprehensive_audit(self) -> SecurityAuditReport:
        """Run comprehensive security audit"""
        logger.info("Starting comprehensive security audit...")
        
        timestamp = datetime.now()
        all_findings = []
        all_compliance_results = []
        
        # Code vulnerability scanning
        code_findings = self.scanner.scan_code_vulnerabilities()
        all_findings.extend(code_findings)
        logger.info(f"Found {len(code_findings)} code vulnerabilities")
        
        # Dependency checking
        dep_findings = self.scanner.check_dependencies()
        all_findings.extend(dep_findings)
        logger.info(f"Found {len(dep_findings)} dependency issues")
        
        # File permission checking
        perm_findings = self.scanner.check_file_permissions()
        all_findings.extend(perm_findings)
        logger.info(f"Found {len(perm_findings)} permission issues")
        
        # SSL/TLS checking
        if self.target_url:
            ssl_findings = self.scanner.check_ssl_configuration(self.target_url)
            all_findings.extend(ssl_findings)
            logger.info(f"Found {len(ssl_findings)} SSL/TLS issues")
        
        # Compliance checking
        gdpr_results = self.compliance_checker.check_gdpr_compliance()
        soc2_results = self.compliance_checker.check_soc2_compliance()
        nist_results = self.compliance_checker.check_nist_compliance()
        
        all_compliance_results.extend(gdpr_results)
        all_compliance_results.extend(soc2_results)
        all_compliance_results.extend(nist_results)
        
        # Calculate summary and risk score
        summary = self._calculate_summary(all_findings, all_compliance_results)
        risk_score = self._calculate_risk_score(all_findings, all_compliance_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_findings, all_compliance_results)
        
        report = SecurityAuditReport(
            timestamp=timestamp,
            target_system=str(self.project_root),
            findings=all_findings,
            compliance_results=all_compliance_results,
            summary=summary,
            recommendations=recommendations,
            risk_score=risk_score
        )
        
        logger.info(f"Security audit completed. Risk score: {risk_score:.1f}/100")
        return report
    
    def _calculate_summary(self, findings: List[SecurityFinding], 
                          compliance_results: List[ComplianceResult]) -> Dict[str, int]:
        """Calculate audit summary statistics"""
        summary = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0,
            'total_findings': len(findings),
            'compliance_pass': 0,
            'compliance_fail': 0,
            'compliance_partial': 0
        }
        
        # Count findings by severity
        for finding in findings:
            if finding.category in summary:
                summary[finding.category] += 1
        
        # Count compliance results
        for result in compliance_results:
            if result.status == 'pass':
                summary['compliance_pass'] += 1
            elif result.status == 'fail':
                summary['compliance_fail'] += 1
            elif result.status == 'partial':
                summary['compliance_partial'] += 1
        
        return summary
    
    def _calculate_risk_score(self, findings: List[SecurityFinding],
                            compliance_results: List[ComplianceResult]) -> float:
        """Calculate overall security risk score (0-100, lower is better)"""
        base_score = 0
        
        # Weight findings by severity
        severity_weights = {
            'critical': 25,
            'high': 15,
            'medium': 8,
            'low': 3,
            'info': 1
        }
        
        for finding in findings:
            weight = severity_weights.get(finding.category, 1)
            base_score += weight
        
        # Add compliance failures
        for result in compliance_results:
            if result.status == 'fail':
                base_score += 10
            elif result.status == 'partial':
                base_score += 5
        
        # Normalize to 0-100 scale
        max_possible_score = len(findings) * 25 + len(compliance_results) * 10
        if max_possible_score > 0:
            risk_score = min(100, (base_score / max_possible_score) * 100)
        else:
            risk_score = 0
        
        return risk_score
    
    def _generate_recommendations(self, findings: List[SecurityFinding],
                                compliance_results: List[ComplianceResult]) -> List[str]:
        """Generate prioritized security recommendations"""
        recommendations = []
        
        # Critical issues first
        critical_findings = [f for f in findings if f.category == 'critical']
        if critical_findings:
            recommendations.append("🚨 CRITICAL: Address all critical security vulnerabilities immediately")
            for finding in critical_findings[:3]:  # Top 3
                if finding.recommendation:
                    recommendations.append(f"  • {finding.recommendation}")
        
        # High-priority compliance failures
        failed_compliance = [r for r in compliance_results if r.status == 'fail']
        if failed_compliance:
            recommendations.append("📋 COMPLIANCE: Address failed compliance controls")
            for result in failed_compliance[:3]:  # Top 3
                recommendations.append(f"  • {result.control_name} ({result.framework})")
        
        # Security best practices
        recommendations.extend([
            "🔐 SECURITY: Enable HTTPS with valid SSL certificates",
            "🛡️ AUTHENTICATION: Implement multi-factor authentication",
            "📊 MONITORING: Set up security monitoring and alerting",
            "🔄 BACKUP: Implement secure backup and disaster recovery",
            "📚 TRAINING: Provide security awareness training",
            "🔍 AUDIT: Schedule regular security audits and penetration testing"
        ])
        
        return recommendations[:10]  # Limit to top 10
    
    def generate_report_html(self, report: SecurityAuditReport) -> str:
        """Generate HTML audit report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>InvestmentAI Security Audit Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; }}
                .critical {{ color: #dc3545; }}
                .high {{ color: #fd7e14; }}
                .medium {{ color: #ffc107; }}
                .low {{ color: #28a745; }}
                .finding {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }}
                .finding.critical {{ border-color: #dc3545; }}
                .finding.high {{ border-color: #fd7e14; }}
                .finding.medium {{ border-color: #ffc107; }}
                .finding.low {{ border-color: #28a745; }}
                .compliance {{ margin: 20px 0; }}
                .pass {{ color: #28a745; }}
                .fail {{ color: #dc3545; }}
                .partial {{ color: #ffc107; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔐 InvestmentAI Security Audit Report</h1>
                <p><strong>Generated:</strong> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Target System:</strong> {report.target_system}</p>
                <p><strong>Risk Score:</strong> <span class="{'critical' if report.risk_score > 75 else 'high' if report.risk_score > 50 else 'medium' if report.risk_score > 25 else 'low'}">{report.risk_score:.1f}/100</span></p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3 class="critical">{report.summary['critical']}</h3>
                    <p>Critical</p>
                </div>
                <div class="metric">
                    <h3 class="high">{report.summary['high']}</h3>
                    <p>High</p>
                </div>
                <div class="metric">
                    <h3 class="medium">{report.summary['medium']}</h3>
                    <p>Medium</p>
                </div>
                <div class="metric">
                    <h3 class="low">{report.summary['low']}</h3>
                    <p>Low</p>
                </div>
            </div>
            
            <h2>🔍 Security Findings</h2>
        """
        
        # Add findings
        for finding in sorted(report.findings, key=lambda f: ['critical', 'high', 'medium', 'low', 'info'].index(f.category)):
            file_info = f" ({finding.file_path}:{finding.line_number})" if finding.file_path else ""
            html += f"""
            <div class="finding {finding.category}">
                <h4>{finding.title}</h4>
                <p><strong>Severity:</strong> {finding.category.upper()}{file_info}</p>
                <p>{finding.description}</p>
                {f'<p><strong>Recommendation:</strong> {finding.recommendation}</p>' if finding.recommendation else ''}
            </div>
            """
        
        # Add compliance results
        html += "<h2>📋 Compliance Results</h2>"
        for framework in ['GDPR', 'SOC2', 'NIST']:
            framework_results = [r for r in report.compliance_results if r.framework == framework]
            if framework_results:
                html += f"<div class='compliance'><h3>{framework}</h3>"
                for result in framework_results:
                    html += f"""
                    <p><span class="{result.status}">{result.status.upper()}</span> 
                       {result.control_id}: {result.control_name}</p>
                    """
                html += "</div>"
        
        # Add recommendations
        html += "<h2>🚀 Recommendations</h2><ul>"
        for rec in report.recommendations:
            html += f"<li>{rec}</li>"
        html += "</ul>"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def save_report(self, report: SecurityAuditReport, filename: str = None):
        """Save audit report to file"""
        if not filename:
            timestamp = report.timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"security_audit_{timestamp}"
        
        # Save JSON report
        json_data = {
            'timestamp': report.timestamp.isoformat(),
            'target_system': report.target_system,
            'risk_score': report.risk_score,
            'summary': report.summary,
            'findings': [
                {
                    'category': f.category,
                    'title': f.title,
                    'description': f.description,
                    'file_path': f.file_path,
                    'line_number': f.line_number,
                    'recommendation': f.recommendation
                }
                for f in report.findings
            ],
            'compliance_results': [
                {
                    'framework': r.framework,
                    'control_id': r.control_id,
                    'control_name': r.control_name,
                    'status': r.status
                }
                for r in report.compliance_results
            ],
            'recommendations': report.recommendations
        }
        
        with open(f"{filename}.json", 'w') as f:
            json.dump(json_data, f, indent=2)
        
        # Save HTML report
        html_report = self.generate_report_html(report)
        with open(f"{filename}.html", 'w') as f:
            f.write(html_report)
        
        logger.info(f"Security audit report saved as {filename}.json and {filename}.html")


def main():
    """Main security audit function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='InvestmentAI Security Audit')
    parser.add_argument('--target-url', default='http://localhost:5000',
                      help='Target URL to audit')
    parser.add_argument('--output', help='Output filename prefix')
    parser.add_argument('--project-root', default='.',
                      help='Project root directory')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    auditor = SecurityAuditor(project_root, args.target_url)
    
    try:
        report = auditor.run_comprehensive_audit()
        
        # Print summary
        print("\n" + "="*60)
        print("SECURITY AUDIT SUMMARY")
        print("="*60)
        print(f"Risk Score: {report.risk_score:.1f}/100")
        print(f"Total Findings: {report.summary['total_findings']}")
        print(f"Critical: {report.summary['critical']}")
        print(f"High: {report.summary['high']}")
        print(f"Medium: {report.summary['medium']}")
        print(f"Low: {report.summary['low']}")
        
        print(f"\nCompliance Results:")
        print(f"Pass: {report.summary['compliance_pass']}")
        print(f"Fail: {report.summary['compliance_fail']}")
        print(f"Partial: {report.summary['compliance_partial']}")
        
        print(f"\nTop Recommendations:")
        for rec in report.recommendations[:5]:
            print(f"  • {rec}")
        
        # Save report
        auditor.save_report(report, args.output)
        
        return 0 if report.risk_score < 50 else 1
        
    except Exception as e:
        logger.error(f"Security audit failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())