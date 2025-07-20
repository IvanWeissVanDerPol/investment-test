# Performance Analysis & Optimization

Comprehensive performance analysis and optimization workflow for the investment analysis system.

## Performance Benchmarking

### 1. Analysis Speed Benchmarks
```bash
# Quick Analysis Performance Test
echo "=== ANALYSIS PERFORMANCE BENCHMARKS ==="
python -c "
import time
import sys
sys.path.append('src')

# Test quick analysis speed
print('Testing Quick Analysis Performance...')
start_time = time.time()

try:
    from investment_system.analysis.quick_analysis import get_stock_analysis
    
    # Test with multiple stocks
    test_stocks = ['NVDA', 'MSFT', 'TSLA']
    results = []
    
    for stock in test_stocks:
        stock_start = time.time()
        result = get_stock_analysis(stock)
        stock_time = time.time() - stock_start
        results.append((stock, stock_time, result is not None))
        
    total_time = time.time() - start_time
    
    print(f'\\nResults:')
    for stock, duration, success in results:
        status = '✅' if success else '❌'
        print(f'{status} {stock}: {duration:.2f}s')
    
    print(f'\\nTotal Quick Analysis Time: {total_time:.2f}s')
    print(f'Target: <180s (3 minutes)')
    
    if total_time < 180:
        print('✅ Performance target met')
    else:
        print('❌ Performance optimization needed')
        
except Exception as e:
    print(f'❌ Performance test failed: {e}')
"
```

### 2. System Resource Monitoring
```bash
# Monitor system resources during analysis
python -c "
import psutil
import time
import threading
import subprocess

class ResourceMonitor:
    def __init__(self):
        self.monitoring = True
        self.max_cpu = 0
        self.max_memory = 0
        
    def monitor(self):
        while self.monitoring:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent
            
            self.max_cpu = max(self.max_cpu, cpu)
            self.max_memory = max(self.max_memory, memory)
            time.sleep(0.5)
    
    def start(self):
        self.thread = threading.Thread(target=self.monitor)
        self.thread.start()
    
    def stop(self):
        self.monitoring = False
        self.thread.join()
        return self.max_cpu, self.max_memory

print('=== RESOURCE USAGE MONITORING ===')
monitor = ResourceMonitor()
monitor.start()

# Simulate analysis workload
try:
    time.sleep(2)  # Simulate analysis
finally:
    max_cpu, max_memory = monitor.stop()

print(f'Peak CPU Usage: {max_cpu:.1f}%')
print(f'Peak Memory Usage: {max_memory:.1f}%')

# Resource usage recommendations
if max_cpu > 80:
    print('⚠️  High CPU usage detected - consider optimization')
if max_memory > 80:
    print('⚠️  High memory usage detected - consider cleanup')
"
```

### 3. Cache Performance Analysis
```bash
# Analyze cache hit rates and effectiveness
python -c "
from pathlib import Path
import json
from datetime import datetime, timedelta

cache_dir = Path('cache')
if cache_dir.exists():
    print('=== CACHE PERFORMANCE ANALYSIS ===')
    
    cache_files = list(cache_dir.glob('*.json'))
    total_files = len(cache_files)
    
    if total_files == 0:
        print('No cache files found')
    else:
        # Analyze cache freshness
        now = datetime.now()
        fresh_count = 0
        stale_count = 0
        total_size = 0
        
        for cache_file in cache_files:
            mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age_hours = (now - mod_time).total_seconds() / 3600
            file_size = cache_file.stat().st_size
            total_size += file_size
            
            if age_hours < 24:  # Fresh if less than 24 hours
                fresh_count += 1
            else:
                stale_count += 1
        
        cache_efficiency = (fresh_count / total_files) * 100 if total_files > 0 else 0
        avg_file_size = total_size / total_files if total_files > 0 else 0
        
        print(f'Total cache files: {total_files}')
        print(f'Fresh files (< 24h): {fresh_count}')
        print(f'Stale files (> 24h): {stale_count}')
        print(f'Cache efficiency: {cache_efficiency:.1f}%')
        print(f'Total cache size: {total_size / 1024:.1f} KB')
        print(f'Average file size: {avg_file_size / 1024:.1f} KB')
        
        # Performance recommendations
        if cache_efficiency < 50:
            print('⚠️  Low cache efficiency - consider cleaning stale files')
        if total_size > 100 * 1024 * 1024:  # 100MB
            print('⚠️  Large cache size - consider cleanup')
        
        print('\\nCache cleanup command:')
        print('python -c \"from pathlib import Path; import time; [f.unlink() for f in Path(\\\"cache\\\").glob(\\\"*.json\\\") if time.time() - f.stat().st_mtime > 86400]\"')
else:
    print('Cache directory not found')
"
```

## Performance Optimization

### 1. Database Query Optimization
```bash
# Optimize data retrieval patterns
echo "=== DATA RETRIEVAL OPTIMIZATION ==="
python -c "
import time
import yfinance as yf

# Test batch vs individual requests
symbols = ['NVDA', 'MSFT', 'TSLA', 'DE', 'TSM']

print('Testing individual requests...')
start_time = time.time()
individual_data = {}
for symbol in symbols:
    ticker = yf.Ticker(symbol)
    individual_data[symbol] = ticker.history(period='1d')
individual_time = time.time() - start_time

print('Testing batch request...')
start_time = time.time()
batch_data = yf.download(' '.join(symbols), period='1d', group_by='ticker')
batch_time = time.time() - start_time

print(f'\\nResults:')
print(f'Individual requests: {individual_time:.2f}s')
print(f'Batch request: {batch_time:.2f}s')
print(f'Performance improvement: {(individual_time/batch_time):.1f}x faster')

if batch_time < individual_time:
    print('✅ Batch requests are more efficient')
else:
    print('⚠️  Individual requests performed better')
"
```

### 2. Memory Usage Optimization
```bash
# Analyze memory usage patterns
python -c "
import tracemalloc
import gc
import sys

print('=== MEMORY USAGE OPTIMIZATION ===')

# Start memory tracing
tracemalloc.start()
initial_memory = tracemalloc.get_traced_memory()[0]

# Simulate analysis workload
try:
    sys.path.append('src')
    from investment_system.analysis.quick_analysis import get_stock_analysis
    
    # Run analysis
    result = get_stock_analysis('NVDA')
    
    # Measure memory after analysis
    current_memory = tracemalloc.get_traced_memory()[0]
    memory_used = (current_memory - initial_memory) / 1024 / 1024  # MB
    
    print(f'Memory used during analysis: {memory_used:.2f} MB')
    
    # Force garbage collection
    gc.collect()
    after_gc_memory = tracemalloc.get_traced_memory()[0]
    memory_freed = (current_memory - after_gc_memory) / 1024 / 1024  # MB
    
    print(f'Memory freed by garbage collection: {memory_freed:.2f} MB')
    
    # Memory usage recommendations
    if memory_used > 100:  # 100MB
        print('⚠️  High memory usage - consider optimization')
    if memory_freed > 10:  # 10MB
        print('✅ Garbage collection effective')
        
finally:
    tracemalloc.stop()
"
```

### 3. API Rate Limiting Optimization
```bash
# Optimize API call patterns
echo "=== API RATE LIMITING OPTIMIZATION ==="
python -c "
import time
from collections import defaultdict

class APIRateLimiter:
    def __init__(self, calls_per_minute=60):
        self.calls_per_minute = calls_per_minute
        self.calls = defaultdict(list)
    
    def can_make_call(self, api_name):
        now = time.time()
        # Remove calls older than 1 minute
        self.calls[api_name] = [call_time for call_time in self.calls[api_name] 
                               if now - call_time < 60]
        
        return len(self.calls[api_name]) < self.calls_per_minute
    
    def record_call(self, api_name):
        self.calls[api_name].append(time.time())
    
    def get_stats(self):
        stats = {}
        for api_name, call_times in self.calls.items():
            stats[api_name] = len(call_times)
        return stats

# Test rate limiting
limiter = APIRateLimiter(calls_per_minute=60)

# Simulate API calls
apis = ['yahoo_finance', 'alpha_vantage', 'news_api']
total_calls = 0

for i in range(100):  # Simulate 100 calls
    for api in apis:
        if limiter.can_make_call(api):
            limiter.record_call(api)
            total_calls += 1
        time.sleep(0.01)  # Small delay

stats = limiter.get_stats()
print('API Call Statistics:')
for api, count in stats.items():
    print(f'  {api}: {count} calls')

print(f'\\nTotal calls made: {total_calls}')
print(f'Rate limiting effectiveness: {(300 - total_calls)/300*100:.1f}% reduction')
"
```

## Performance Monitoring Dashboard

### 1. Real-time Performance Metrics
```bash
# Create performance monitoring dashboard
python -c "
import time
import psutil
from datetime import datetime

def performance_dashboard():
    print('=== INVESTMENT SYSTEM PERFORMANCE DASHBOARD ===')
    print(f'Timestamp: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print()
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('.')
    
    print('🖥️  System Resources:')
    print(f'   CPU Usage: {cpu_percent:.1f}%')
    print(f'   Memory Usage: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB used)')
    print(f'   Disk Usage: {disk.used/disk.total*100:.1f}% ({disk.free/1024**3:.1f}GB free)')
    print()
    
    # Application metrics
    print('📊 Application Performance:')
    
    # Check cache status
    from pathlib import Path
    cache_dir = Path('cache')
    if cache_dir.exists():
        cache_files = len(list(cache_dir.glob('*.json')))
        cache_size = sum(f.stat().st_size for f in cache_dir.glob('*.json')) / 1024
        print(f'   Cache Files: {cache_files} ({cache_size:.1f} KB)')
    
    # Check reports
    reports_dir = Path('reports')
    if reports_dir.exists():
        recent_reports = len([f for f in reports_dir.glob('*.json') 
                            if time.time() - f.stat().st_mtime < 86400])
        print(f'   Recent Reports: {recent_reports} (last 24h)')
    
    print()
    
    # Performance recommendations
    print('💡 Performance Recommendations:')
    if cpu_percent > 80:
        print('   ⚠️  High CPU usage - consider reducing analysis frequency')
    if memory.percent > 80:
        print('   ⚠️  High memory usage - restart system or clear cache')
    if disk.free / 1024**3 < 1:  # Less than 1GB free
        print('   ⚠️  Low disk space - clean old reports and cache')
    
    if cpu_percent < 50 and memory.percent < 50:
        print('   ✅ System performance optimal')

performance_dashboard()
"
```

### 2. Analysis Performance Trends
```bash
# Track analysis performance over time
python -c "
from pathlib import Path
import json
from datetime import datetime, timedelta

def analyze_performance_trends():
    print('=== ANALYSIS PERFORMANCE TRENDS ===')
    
    reports_dir = Path('reports')
    if not reports_dir.exists():
        print('No reports directory found')
        return
    
    # Analyze report generation frequency
    report_files = sorted(reports_dir.glob('*.json'), 
                         key=lambda f: f.stat().st_mtime, reverse=True)
    
    if not report_files:
        print('No report files found')
        return
    
    # Calculate daily report counts for last 7 days
    now = datetime.now()
    daily_counts = {}
    
    for i in range(7):
        date = now - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        daily_counts[date_str] = 0
    
    for report_file in report_files:
        mod_time = datetime.fromtimestamp(report_file.stat().st_mtime)
        if (now - mod_time).days < 7:
            date_str = mod_time.strftime('%Y-%m-%d')
            if date_str in daily_counts:
                daily_counts[date_str] += 1
    
    print('Daily Report Generation (Last 7 Days):')
    for date, count in sorted(daily_counts.items(), reverse=True):
        print(f'   {date}: {count} reports')
    
    # Average reports per day
    avg_reports = sum(daily_counts.values()) / 7
    print(f'\\nAverage reports per day: {avg_reports:.1f}')
    
    # Performance assessment
    if avg_reports >= 2:
        print('✅ Good analysis frequency')
    elif avg_reports >= 1:
        print('⚠️  Moderate analysis frequency')
    else:
        print('❌ Low analysis frequency - increase automation')

analyze_performance_trends()
"
```

## Optimization Recommendations

### 1. Quick Wins
- **Cache Optimization**: Implement intelligent cache invalidation
- **Batch Processing**: Group API calls to reduce latency
- **Parallel Processing**: Run independent analysis modules concurrently
- **Memory Management**: Implement garbage collection triggers

### 2. Long-term Optimizations
- **Database Integration**: Replace file-based storage with SQLite
- **Async Processing**: Implement async/await for I/O operations
- **Data Compression**: Compress cache and report files
- **Load Balancing**: Distribute analysis across multiple processes

### 3. Infrastructure Improvements
- **SSD Storage**: Ensure fast disk I/O for cache and reports
- **Memory Upgrade**: Increase RAM for larger datasets
- **Network Optimization**: Use CDN for static data sources
- **Monitoring Integration**: Add APM tools for detailed insights

Your investment analysis system now includes comprehensive performance monitoring and optimization capabilities to ensure efficient $900 portfolio management!