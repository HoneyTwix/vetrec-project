"""
Performance monitoring utility for tracking optimization improvements
"""
import time
import functools
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os
import asyncio

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        self.current_operation = None
        self.start_time = None
    
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.current_operation = operation_name
        self.start_time = time.time()
        print(f"⏱️ Starting: {operation_name}")
    
    def end_operation(self, operation_name: str = None):
        """End timing an operation"""
        if not self.start_time:
            return
        
        operation = operation_name or self.current_operation
        if not operation:
            return
        
        duration = time.time() - self.start_time
        self.metrics[operation] = duration
        print(f"✅ Completed: {operation} in {duration:.3f}s")
        
        self.current_operation = None
        self.start_time = None
    
    def add_metric(self, name: str, value: float):
        """Add a custom metric"""
        self.metrics[name] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        total_time = sum(self.metrics.values())
        return {
            "total_time": total_time,
            "operations": self.metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def print_summary(self):
        """Print performance summary"""
        summary = self.get_summary()
        print("\n" + "="*50)
        print("PERFORMANCE SUMMARY")
        print("="*50)
        print(f"Total Time: {summary['total_time']:.3f}s")
        print("\nOperations:")
        for operation, duration in self.metrics.items():
            print(f"  {operation}: {duration:.3f}s")
        print("="*50)
    
    def save_metrics(self, filename: str = None):
        """Save metrics to file"""
        if not filename:
            filename = f"performance_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = self.get_summary()
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Metrics saved to: {filename}")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance(operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__name__}"
            performance_monitor.start_operation(name)
            try:
                result = await func(*args, **kwargs)
                performance_monitor.end_operation(name)
                return result
            except Exception as e:
                performance_monitor.end_operation(name)
                raise e
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__name__}"
            performance_monitor.start_operation(name)
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_operation(name)
                return result
            except Exception as e:
                performance_monitor.end_operation(name)
                raise e
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator 