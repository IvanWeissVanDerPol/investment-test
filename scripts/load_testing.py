#!/usr/bin/env python3
"""
Load Testing and Performance Optimization
Comprehensive load testing suite for the InvestmentAI system
"""

import asyncio
import aiohttp
import time
import json
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
import concurrent.futures
import threading
import psutil
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Load test result metrics"""
    test_name: str
    duration: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    requests_per_second: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95: float
    percentile_99: float
    error_rate: float
    throughput_mbps: float
    concurrent_users: int
    memory_usage: List[float]
    cpu_usage: List[float]
    errors: List[str]


@dataclass
class TestScenario:
    """Test scenario configuration"""
    name: str
    url_path: str
    method: str = 'GET'
    payload: Optional[Dict] = None
    headers: Optional[Dict] = None
    weight: float = 1.0  # Relative frequency
    auth_required: bool = False


class PerformanceMonitor:
    """Monitor system performance during load tests"""
    
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.monitoring = False
        self.cpu_usage = []
        self.memory_usage = []
        self.disk_io = []
        self.network_io = []
        
    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)
            
    def _monitor_loop(self):
        """Monitor system metrics"""
        while self.monitoring:
            # CPU usage
            cpu = psutil.cpu_percent(interval=None)
            self.cpu_usage.append(cpu)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.memory_usage.append(memory.percent)
            
            # Disk I/O
            disk = psutil.disk_io_counters()
            if disk:
                self.disk_io.append({
                    'read_bytes': disk.read_bytes,
                    'write_bytes': disk.write_bytes
                })
            
            # Network I/O
            network = psutil.net_io_counters()
            if network:
                self.network_io.append({
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                })
            
            time.sleep(self.interval)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        return {
            'cpu_usage': {
                'avg': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                'max': max(self.cpu_usage) if self.cpu_usage else 0,
                'samples': len(self.cpu_usage)
            },
            'memory_usage': {
                'avg': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                'max': max(self.memory_usage) if self.memory_usage else 0,
                'samples': len(self.memory_usage)
            },
            'disk_io': self.disk_io[-1] if self.disk_io else {},
            'network_io': self.network_io[-1] if self.network_io else {}
        }


class LoadTester:
    """Comprehensive load testing framework"""
    
    def __init__(self, base_url: str = "http://localhost:5000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.performance_monitor = PerformanceMonitor()
        
        # Test scenarios
        self.scenarios = [
            TestScenario("Health Check", "/health"),
            TestScenario("Dashboard", "/dashboard", auth_required=True),
            TestScenario("Portfolio Summary", "/api/portfolio/summary", auth_required=True),
            TestScenario("Stock Quote", "/api/data/quote/NVDA", auth_required=True),
            TestScenario("Market Analysis", "/api/analysis/quick/NVDA", auth_required=True),
            TestScenario("ML Prediction", "/api/ml/predict/NVDA", method='POST', 
                        payload={"horizon": 1, "model": "ensemble"}, auth_required=True),
            TestScenario("Portfolio Optimization", "/api/portfolio/optimize", method='POST',
                        payload={"symbols": ["NVDA", "MSFT", "GOOGL"], "method": "markowitz"}, 
                        auth_required=True),
            TestScenario("Login", "/login", method='POST',
                        payload={"email_or_username": "test@test.com", "password": "testpass"}),
            TestScenario("Real-time Data", "/api/data/realtime/NVDA", auth_required=True),
            TestScenario("Performance Metrics", "/api/monitoring/metrics", auth_required=True)
        ]
        
        # Authentication token
        self.auth_token = None
        
    async def authenticate(self, session: aiohttp.ClientSession) -> bool:
        """Authenticate and get token"""
        try:
            login_data = {
                "email_or_username": "admin@investmentai.com",
                "password": "ChangeMe123!@#"
            }
            
            async with session.post(f"{self.base_url}/api/auth/login", 
                                  json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('token')
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_headers(self, scenario: TestScenario) -> Dict[str, str]:
        """Get headers for request"""
        headers = {'Content-Type': 'application/json'}
        
        if scenario.headers:
            headers.update(scenario.headers)
        
        if scenario.auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
            
        return headers
    
    async def execute_request(self, session: aiohttp.ClientSession, 
                            scenario: TestScenario) -> Dict[str, Any]:
        """Execute a single request"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{scenario.url_path}"
            headers = self.get_headers(scenario)
            
            kwargs = {
                'timeout': aiohttp.ClientTimeout(total=self.timeout),
                'headers': headers
            }
            
            if scenario.payload and scenario.method in ['POST', 'PUT']:
                kwargs['json'] = scenario.payload
            
            async with getattr(session, scenario.method.lower())(url, **kwargs) as response:
                response_time = time.time() - start_time
                content = await response.text()
                
                return {
                    'success': response.status < 400,
                    'status_code': response.status,
                    'response_time': response_time,
                    'response_size': len(content),
                    'error': None if response.status < 400 else f"HTTP {response.status}"
                }
                
        except asyncio.TimeoutError:
            return {
                'success': False,
                'status_code': 0,
                'response_time': self.timeout,
                'response_size': 0,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 0,
                'response_time': time.time() - start_time,
                'response_size': 0,
                'error': str(e)
            }
    
    async def run_load_test(self, concurrent_users: int, duration: int, 
                          ramp_up_time: int = 30) -> LoadTestResult:
        """
        Run comprehensive load test
        
        Args:
            concurrent_users: Number of concurrent virtual users
            duration: Test duration in seconds
            ramp_up_time: Time to ramp up to full load
        """
        logger.info(f"Starting load test: {concurrent_users} users, {duration}s duration")
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring()
        
        test_start = time.time()
        results = []
        errors = []
        
        try:
            # Create session with connection pooling
            connector = aiohttp.TCPConnector(
                limit=concurrent_users * 2,
                limit_per_host=concurrent_users,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30
            )
            
            async with aiohttp.ClientSession(connector=connector) as session:
                # Authenticate once
                await self.authenticate(session)
                
                # Create semaphore to limit concurrent requests
                semaphore = asyncio.Semaphore(concurrent_users)
                
                # Generate test tasks
                tasks = []
                end_time = test_start + duration
                
                # Ramp up users gradually
                users_per_step = max(1, concurrent_users // (ramp_up_time // 5))
                current_users = 0
                
                while time.time() < end_time:
                    # Ramp up users
                    if current_users < concurrent_users:
                        current_users = min(concurrent_users, 
                                          current_users + users_per_step)
                    
                    # Create tasks for current batch
                    for _ in range(min(10, current_users)):  # Batch size
                        scenario = self._select_scenario()
                        task = self._execute_with_semaphore(
                            semaphore, session, scenario
                        )
                        tasks.append(asyncio.create_task(task))
                    
                    await asyncio.sleep(0.1)  # Small delay between batches
                
                # Wait for all tasks to complete
                logger.info("Waiting for tasks to complete...")
                completed_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for result in completed_results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                    elif isinstance(result, dict):
                        results.append(result)
        
        finally:
            # Stop performance monitoring
            self.performance_monitor.stop_monitoring()
        
        test_duration = time.time() - test_start
        
        return self._calculate_metrics(
            results, errors, test_duration, concurrent_users,
            self.performance_monitor.get_metrics()
        )
    
    async def _execute_with_semaphore(self, semaphore: asyncio.Semaphore,
                                    session: aiohttp.ClientSession,
                                    scenario: TestScenario) -> Dict[str, Any]:
        """Execute request with semaphore limiting"""
        async with semaphore:
            return await self.execute_request(session, scenario)
    
    def _select_scenario(self) -> TestScenario:
        """Select a scenario based on weights"""
        weights = [scenario.weight for scenario in self.scenarios]
        return random.choices(self.scenarios, weights=weights)[0]
    
    def _calculate_metrics(self, results: List[Dict], errors: List[str],
                          duration: float, concurrent_users: int,
                          system_metrics: Dict) -> LoadTestResult:
        """Calculate load test metrics"""
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = total_requests - successful_requests
        
        if not results:
            return LoadTestResult(
                test_name="Load Test",
                duration=duration,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                requests_per_second=0,
                avg_response_time=0,
                min_response_time=0,
                max_response_time=0,
                percentile_95=0,
                percentile_99=0,
                error_rate=1.0,
                throughput_mbps=0,
                concurrent_users=concurrent_users,
                memory_usage=[],
                cpu_usage=[],
                errors=errors
            )
        
        response_times = [r['response_time'] for r in results if r['success']]
        response_sizes = [r['response_size'] for r in results if r['success']]
        
        # Calculate percentiles
        response_times_sorted = sorted(response_times) if response_times else [0]
        percentile_95 = response_times_sorted[int(len(response_times_sorted) * 0.95)]
        percentile_99 = response_times_sorted[int(len(response_times_sorted) * 0.99)]
        
        # Calculate throughput
        total_bytes = sum(response_sizes)
        throughput_mbps = (total_bytes * 8) / (duration * 1_000_000)  # Mbps
        
        return LoadTestResult(
            test_name="Load Test",
            duration=duration,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            requests_per_second=successful_requests / duration if duration > 0 else 0,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            error_rate=failed_requests / total_requests if total_requests > 0 else 0,
            throughput_mbps=throughput_mbps,
            concurrent_users=concurrent_users,
            memory_usage=system_metrics.get('memory_usage', {}).get('samples', []),
            cpu_usage=system_metrics.get('cpu_usage', {}).get('samples', []),
            errors=errors[:10]  # Limit error samples
        )
    
    async def run_stress_test(self, max_users: int = 1000, step_size: int = 50,
                            step_duration: int = 60) -> List[LoadTestResult]:
        """
        Run stress test with gradually increasing load
        """
        logger.info(f"Starting stress test: 0 to {max_users} users")
        
        results = []
        current_users = step_size
        
        while current_users <= max_users:
            logger.info(f"Testing with {current_users} concurrent users...")
            
            result = await self.run_load_test(
                concurrent_users=current_users,
                duration=step_duration,
                ramp_up_time=10
            )
            
            result.test_name = f"Stress Test - {current_users} users"
            results.append(result)
            
            # Log key metrics
            logger.info(f"RPS: {result.requests_per_second:.2f}, "
                       f"Avg Response: {result.avg_response_time:.3f}s, "
                       f"Error Rate: {result.error_rate:.2%}")
            
            # Stop if error rate is too high
            if result.error_rate > 0.1:  # 10% error rate
                logger.warning("High error rate detected, stopping stress test")
                break
            
            current_users += step_size
            
            # Brief cooldown between tests
            await asyncio.sleep(5)
        
        return results
    
    async def run_spike_test(self, baseline_users: int = 50, 
                           spike_users: int = 500, spike_duration: int = 30) -> LoadTestResult:
        """
        Run spike test - sudden increase in load
        """
        logger.info(f"Starting spike test: {baseline_users} -> {spike_users} users")
        
        # Start with baseline load
        baseline_task = asyncio.create_task(
            self.run_load_test(baseline_users, spike_duration + 60, ramp_up_time=10)
        )
        
        # Wait for baseline to establish
        await asyncio.sleep(30)
        
        # Add spike load
        spike_task = asyncio.create_task(
            self.run_load_test(spike_users - baseline_users, spike_duration, ramp_up_time=0)
        )
        
        # Wait for both to complete
        baseline_result, spike_result = await asyncio.gather(baseline_task, spike_task)
        
        # Combine results
        combined_result = LoadTestResult(
            test_name="Spike Test",
            duration=max(baseline_result.duration, spike_result.duration),
            total_requests=baseline_result.total_requests + spike_result.total_requests,
            successful_requests=baseline_result.successful_requests + spike_result.successful_requests,
            failed_requests=baseline_result.failed_requests + spike_result.failed_requests,
            requests_per_second=(baseline_result.requests_per_second + spike_result.requests_per_second),
            avg_response_time=(baseline_result.avg_response_time + spike_result.avg_response_time) / 2,
            min_response_time=min(baseline_result.min_response_time, spike_result.min_response_time),
            max_response_time=max(baseline_result.max_response_time, spike_result.max_response_time),
            percentile_95=max(baseline_result.percentile_95, spike_result.percentile_95),
            percentile_99=max(baseline_result.percentile_99, spike_result.percentile_99),
            error_rate=((baseline_result.failed_requests + spike_result.failed_requests) /
                       (baseline_result.total_requests + spike_result.total_requests)),
            throughput_mbps=baseline_result.throughput_mbps + spike_result.throughput_mbps,
            concurrent_users=spike_users,
            memory_usage=baseline_result.memory_usage + spike_result.memory_usage,
            cpu_usage=baseline_result.cpu_usage + spike_result.cpu_usage,
            errors=baseline_result.errors + spike_result.errors
        )
        
        return combined_result
    
    def generate_report(self, results: List[LoadTestResult]) -> str:
        """Generate comprehensive test report"""
        report = [
            "=" * 80,
            "INVESTMENTAI LOAD TEST REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Target URL: {self.base_url}",
            "",
            "TEST RESULTS SUMMARY",
            "-" * 40
        ]
        
        for result in results:
            report.extend([
                f"\n{result.test_name}:",
                f"  Duration: {result.duration:.1f}s",
                f"  Total Requests: {result.total_requests:,}",
                f"  Successful: {result.successful_requests:,}",
                f"  Failed: {result.failed_requests:,}",
                f"  Requests/sec: {result.requests_per_second:.2f}",
                f"  Avg Response Time: {result.avg_response_time:.3f}s",
                f"  95th Percentile: {result.percentile_95:.3f}s",
                f"  99th Percentile: {result.percentile_99:.3f}s",
                f"  Error Rate: {result.error_rate:.2%}",
                f"  Throughput: {result.throughput_mbps:.2f} Mbps",
                f"  Concurrent Users: {result.concurrent_users}"
            ])
            
            if result.errors:
                report.extend([
                    f"  Top Errors:",
                    *[f"    - {error}" for error in result.errors[:5]]
                ])
        
        # Performance analysis
        if results:
            best_rps = max(results, key=lambda r: r.requests_per_second)
            worst_error_rate = max(results, key=lambda r: r.error_rate)
            
            report.extend([
                "",
                "PERFORMANCE ANALYSIS",
                "-" * 40,
                f"Best RPS: {best_rps.requests_per_second:.2f} ({best_rps.test_name})",
                f"Worst Error Rate: {worst_error_rate.error_rate:.2%} ({worst_error_rate.test_name})",
            ])
        
        # Recommendations
        report.extend([
            "",
            "OPTIMIZATION RECOMMENDATIONS",
            "-" * 40
        ])
        
        if results:
            avg_error_rate = statistics.mean([r.error_rate for r in results])
            avg_response_time = statistics.mean([r.avg_response_time for r in results])
            
            if avg_error_rate > 0.05:
                report.append("• High error rate detected - investigate application errors")
            
            if avg_response_time > 2.0:
                report.append("• Response times are high - consider database optimization")
            
            max_users_tested = max([r.concurrent_users for r in results])
            if max_users_tested < 200:
                report.append("• Test with higher concurrent users to find capacity limits")
            
            report.extend([
                "• Enable Redis caching for better performance",
                "• Consider implementing API rate limiting",
                "• Monitor database connection pool usage",
                "• Implement CDN for static assets",
                "• Consider horizontal scaling for high loads"
            ])
        
        return "\n".join(report)
    
    def save_results(self, results: List[LoadTestResult], filename: str = None):
        """Save test results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"
        
        results_data = []
        for result in results:
            results_data.append({
                'test_name': result.test_name,
                'duration': result.duration,
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'requests_per_second': result.requests_per_second,
                'avg_response_time': result.avg_response_time,
                'min_response_time': result.min_response_time,
                'max_response_time': result.max_response_time,
                'percentile_95': result.percentile_95,
                'percentile_99': result.percentile_99,
                'error_rate': result.error_rate,
                'throughput_mbps': result.throughput_mbps,
                'concurrent_users': result.concurrent_users,
                'errors': result.errors
            })
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"Results saved to {filename}")


async def main():
    """Main load testing function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='InvestmentAI Load Testing')
    parser.add_argument('--url', default='http://localhost:5000',
                      help='Base URL to test')
    parser.add_argument('--users', type=int, default=50,
                      help='Concurrent users for load test')
    parser.add_argument('--duration', type=int, default=300,
                      help='Test duration in seconds')
    parser.add_argument('--test-type', choices=['load', 'stress', 'spike'], 
                      default='load', help='Type of test to run')
    parser.add_argument('--report', help='Output report filename')
    
    args = parser.parse_args()
    
    # Create load tester
    tester = LoadTester(args.url)
    
    try:
        results = []
        
        if args.test_type == 'load':
            result = await tester.run_load_test(args.users, args.duration)
            results.append(result)
            
        elif args.test_type == 'stress':
            results = await tester.run_stress_test(args.users)
            
        elif args.test_type == 'spike':
            result = await tester.run_spike_test()
            results.append(result)
        
        # Generate and display report
        report = tester.generate_report(results)
        print(report)
        
        # Save results
        tester.save_results(results)
        
        if args.report:
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"\nReport saved to {args.report}")
        
    except Exception as e:
        logger.error(f"Load test failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    asyncio.run(main())