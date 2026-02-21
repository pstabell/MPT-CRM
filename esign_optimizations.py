"""
E-Signature Code Optimizations for Phase 4
==========================================

Performance optimizations, code cleanup, and refactoring
for the E-Signature system:

1. Performance improvements
2. Memory optimization
3. Code refactoring
4. Error handling enhancements
5. Logging and monitoring
6. Configuration management
7. Caching mechanisms
"""

import os
import json
import time
import functools
import logging
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from dataclasses import dataclass
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('esign.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ESignConfig:
    """Configuration management for E-Signature system"""
    
    # Database settings
    db_connection_pool_size: int = 10
    db_timeout: int = 30
    
    # File settings
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    temp_file_cleanup_interval: int = 3600  # 1 hour
    
    # Security settings
    token_expiry_days: int = 14
    max_login_attempts: int = 5
    session_timeout: int = 3600  # 1 hour
    
    # Performance settings
    cache_ttl: int = 300  # 5 minutes
    max_concurrent_operations: int = 10
    
    # Email settings
    email_retry_attempts: int = 3
    email_retry_delay: int = 5
    
    # SharePoint settings
    sharepoint_timeout: int = 60
    sharepoint_retry_attempts: int = 3
    
    @classmethod
    def from_env(cls) -> 'ESignConfig':
        """Load configuration from environment variables"""
        return cls(
            db_connection_pool_size=int(os.getenv('ESIGN_DB_POOL_SIZE', '10')),
            db_timeout=int(os.getenv('ESIGN_DB_TIMEOUT', '30')),
            max_file_size=int(os.getenv('ESIGN_MAX_FILE_SIZE', str(50 * 1024 * 1024))),
            temp_file_cleanup_interval=int(os.getenv('ESIGN_CLEANUP_INTERVAL', '3600')),
            token_expiry_days=int(os.getenv('ESIGN_TOKEN_EXPIRY_DAYS', '14')),
            max_login_attempts=int(os.getenv('ESIGN_MAX_LOGIN_ATTEMPTS', '5')),
            session_timeout=int(os.getenv('ESIGN_SESSION_TIMEOUT', '3600')),
            cache_ttl=int(os.getenv('ESIGN_CACHE_TTL', '300')),
            max_concurrent_operations=int(os.getenv('ESIGN_MAX_CONCURRENT_OPS', '10')),
            email_retry_attempts=int(os.getenv('ESIGN_EMAIL_RETRY_ATTEMPTS', '3')),
            email_retry_delay=int(os.getenv('ESIGN_EMAIL_RETRY_DELAY', '5')),
            sharepoint_timeout=int(os.getenv('ESIGN_SHAREPOINT_TIMEOUT', '60')),
            sharepoint_retry_attempts=int(os.getenv('ESIGN_SHAREPOINT_RETRY_ATTEMPTS', '3'))
        )


class ESignCache:
    """Lightweight caching system for E-Signature operations"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
    
    def get(self, key: str, default=None) -> Any:
        """Get value from cache"""
        with self._lock:
            if key in self.cache:
                if self._is_expired(key):
                    self._remove(key)
                    return default
                return self.cache[key]
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        with self._lock:
            self.cache[key] = value
            self.timestamps[key] = time.time() + (ttl or self.default_ttl)
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        with self._lock:
            self._remove(key)
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        with self._lock:
            expired_keys = [
                key for key in self.cache.keys()
                if self._is_expired(key)
            ]
            
            for key in expired_keys:
                self._remove(key)
            
            return len(expired_keys)
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        return key in self.timestamps and time.time() > self.timestamps[key]
    
    def _remove(self, key: str) -> None:
        """Remove key from cache and timestamps"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_entries = len(self.cache)
            expired_entries = sum(1 for key in self.cache.keys() if self._is_expired(key))
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'memory_usage_mb': sum(
                    len(str(k)) + len(str(v)) for k, v in self.cache.items()
                ) / (1024 * 1024)
            }


# Global cache instance
esign_cache = ESignCache()


def cache_result(ttl: int = 300, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            result = esign_cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            esign_cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, 
                    exceptions: tuple = (Exception,)):
    """Decorator for retrying failed operations"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator


def async_operation(timeout: float = 30.0):
    """Decorator for running operations asynchronously with timeout"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout)
                except TimeoutError:
                    logger.error(f"Operation {func.__name__} timed out after {timeout}s")
                    raise
        return wrapper
    return decorator


class ESignPerformanceMonitor:
    """Performance monitoring for E-Signature operations"""
    
    def __init__(self):
        self.metrics = {}
        self._lock = threading.RLock()
    
    def start_timing(self, operation: str) -> str:
        """Start timing an operation"""
        timing_id = f"{operation}_{int(time.time() * 1000000)}"
        with self._lock:
            if operation not in self.metrics:
                self.metrics[operation] = {
                    'count': 0,
                    'total_time': 0.0,
                    'min_time': float('inf'),
                    'max_time': 0.0,
                    'active_timings': {}
                }
            
            self.metrics[operation]['active_timings'][timing_id] = time.time()
        
        return timing_id
    
    def end_timing(self, timing_id: str) -> Optional[float]:
        """End timing an operation"""
        end_time = time.time()
        
        with self._lock:
            for operation, data in self.metrics.items():
                if timing_id in data['active_timings']:
                    start_time = data['active_timings'].pop(timing_id)
                    duration = end_time - start_time
                    
                    # Update metrics
                    data['count'] += 1
                    data['total_time'] += duration
                    data['min_time'] = min(data['min_time'], duration)
                    data['max_time'] = max(data['max_time'], duration)
                    
                    return duration
        
        return None
    
    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        with self._lock:
            if operation:
                if operation not in self.metrics:
                    return {}
                
                data = self.metrics[operation]
                return {
                    'operation': operation,
                    'count': data['count'],
                    'average_time': data['total_time'] / data['count'] if data['count'] > 0 else 0,
                    'min_time': data['min_time'] if data['min_time'] != float('inf') else 0,
                    'max_time': data['max_time'],
                    'total_time': data['total_time'],
                    'active_operations': len(data['active_timings'])
                }
            else:
                stats = {}
                for op_name, data in self.metrics.items():
                    stats[op_name] = {
                        'count': data['count'],
                        'average_time': data['total_time'] / data['count'] if data['count'] > 0 else 0,
                        'min_time': data['min_time'] if data['min_time'] != float('inf') else 0,
                        'max_time': data['max_time'],
                        'total_time': data['total_time'],
                        'active_operations': len(data['active_timings'])
                    }
                return stats


# Global performance monitor
performance_monitor = ESignPerformanceMonitor()


def monitor_performance(operation_name: str):
    """Decorator for monitoring operation performance"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timing_id = performance_monitor.start_timing(operation_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = performance_monitor.end_timing(timing_id)
                if duration:
                    logger.info(f"Operation {operation_name} completed in {duration:.3f}s")
        return wrapper
    return decorator


class ESignMemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def process_large_file_in_chunks(file_path: str, chunk_size: int = 1024 * 1024) -> bytes:
        """Process large files in chunks to minimize memory usage"""
        hasher = hashlib.sha256()
        total_size = 0
        
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
                    total_size += len(chunk)
            
            logger.info(f"Processed {total_size} bytes from {file_path}")
            return hasher.digest()
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    @staticmethod
    def cleanup_temp_files(temp_dir: str = "/tmp", max_age_hours: int = 24):
        """Clean up old temporary files"""
        temp_path = Path(temp_dir)
        cutoff_time = time.time() - (max_age_hours * 3600)
        cleaned_count = 0
        cleaned_size = 0
        
        try:
            for file_path in temp_path.glob("esign_*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_count += 1
                    cleaned_size += file_size
            
            logger.info(f"Cleaned up {cleaned_count} temp files ({cleaned_size} bytes)")
            return cleaned_count
        
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")
            return 0
    
    @staticmethod
    def optimize_memory_usage():
        """Optimize overall memory usage"""
        import gc
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collector freed {collected} objects")
        
        # Clean up expired cache entries
        cleaned = esign_cache.cleanup_expired()
        logger.info(f"Cleaned up {cleaned} expired cache entries")
        
        # Get cache stats
        cache_stats = esign_cache.stats()
        logger.info(f"Cache stats: {cache_stats}")
        
        return {
            'gc_objects_freed': collected,
            'cache_entries_cleaned': cleaned,
            'cache_stats': cache_stats
        }


class ESignErrorHandler:
    """Enhanced error handling and logging"""
    
    @staticmethod
    def handle_database_error(error: Exception, operation: str, **context):
        """Handle database-related errors"""
        error_id = hashlib.md5(f"{time.time()}{operation}".encode()).hexdigest()[:8]
        
        logger.error(f"Database error [{error_id}] in {operation}: {error}", extra={
            'error_id': error_id,
            'operation': operation,
            'context': context,
            'error_type': type(error).__name__
        })
        
        return {
            'success': False,
            'error_id': error_id,
            'message': f"Database operation failed. Reference: {error_id}",
            'details': str(error) if os.getenv('DEBUG') else None
        }
    
    @staticmethod
    def handle_validation_error(errors: list, operation: str):
        """Handle validation errors"""
        logger.warning(f"Validation errors in {operation}: {errors}")
        
        return {
            'success': False,
            'message': "Validation failed",
            'errors': errors
        }
    
    @staticmethod
    def handle_security_error(error: Exception, operation: str, client_info: dict):
        """Handle security-related errors"""
        error_id = hashlib.md5(f"{time.time()}{operation}".encode()).hexdigest()[:8]
        
        logger.error(f"Security error [{error_id}] in {operation}: {error}", extra={
            'error_id': error_id,
            'operation': operation,
            'client_info': client_info,
            'error_type': type(error).__name__,
            'severity': 'HIGH'
        })
        
        # Could trigger security alerts here
        
        return {
            'success': False,
            'error_id': error_id,
            'message': "Security validation failed",
            'details': None  # Don't expose security details
        }


class ESignBatchProcessor:
    """Batch processing for bulk operations"""
    
    def __init__(self, batch_size: int = 100, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_documents_batch(self, documents: list, processor_func: Callable) -> list:
        """Process documents in batches"""
        results = []
        total_batches = (len(documents) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")
            
            # Submit batch to thread pool
            future = self.executor.submit(self._process_batch, batch, processor_func)
            batch_results = future.result()
            results.extend(batch_results)
        
        return results
    
    def _process_batch(self, batch: list, processor_func: Callable) -> list:
        """Process a single batch of documents"""
        results = []
        for document in batch:
            try:
                result = processor_func(document)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing document {document.get('id', 'unknown')}: {e}")
                results.append({'success': False, 'error': str(e)})
        
        return results
    
    def shutdown(self):
        """Shutdown the batch processor"""
        self.executor.shutdown(wait=True)


def optimize_esign_system():
    """Run comprehensive system optimization"""
    
    logger.info("Starting E-Signature system optimization...")
    
    optimization_results = {}
    
    # Memory optimization
    logger.info("Running memory optimization...")
    memory_results = ESignMemoryOptimizer.optimize_memory_usage()
    optimization_results['memory'] = memory_results
    
    # Cleanup temp files
    logger.info("Cleaning up temporary files...")
    cleaned_files = ESignMemoryOptimizer.cleanup_temp_files()
    optimization_results['temp_files_cleaned'] = cleaned_files
    
    # Performance stats
    logger.info("Gathering performance statistics...")
    perf_stats = performance_monitor.get_stats()
    optimization_results['performance'] = perf_stats
    
    # Cache statistics
    cache_stats = esign_cache.stats()
    optimization_results['cache'] = cache_stats
    
    logger.info(f"System optimization completed: {optimization_results}")
    
    return optimization_results


# Enhanced utility functions for existing code

@cache_result(ttl=600)
@monitor_performance("document_hash_generation")
def optimized_generate_document_hash(pdf_data: bytes, signature_data: bytes, timestamp: str) -> str:
    """Optimized version of document hash generation"""
    try:
        # Use memory-efficient hashing for large files
        if len(pdf_data) > 10 * 1024 * 1024:  # > 10MB
            hasher = hashlib.sha256()
            
            # Process PDF data in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            for i in range(0, len(pdf_data), chunk_size):
                hasher.update(pdf_data[i:i + chunk_size])
            
            hasher.update(signature_data)
            hasher.update(timestamp.encode('utf-8'))
            
            return hasher.hexdigest()
        else:
            # For smaller files, use the original method
            combined_data = pdf_data + signature_data + timestamp.encode('utf-8')
            return hashlib.sha256(combined_data).hexdigest()
    
    except Exception as e:
        logger.error(f"Error generating document hash: {e}")
        raise


@retry_on_failure(max_attempts=3, delay=2.0)
@monitor_performance("email_sending")
async def optimized_send_email(doc_data: dict, base_url: str) -> bool:
    """Optimized email sending with retry logic"""
    try:
        # Import here to avoid circular imports
        from esign_email_service import send_esign_request_email
        
        return send_esign_request_email(doc_data, base_url)
    
    except Exception as e:
        logger.error(f"Error sending email for document {doc_data.get('id')}: {e}")
        raise


@cache_result(ttl=1800, key_func=lambda path: f"pdf_validation:{hashlib.md5(path.encode()).hexdigest()}")
@monitor_performance("pdf_validation")
def optimized_validate_pdf(file_path: str) -> dict:
    """Optimized PDF validation with caching"""
    try:
        # Use chunked reading for large files
        file_size = os.path.getsize(file_path)
        
        if file_size > 50 * 1024 * 1024:  # > 50MB
            return {'valid': False, 'errors': ['File too large']}
        
        # Read only the header and footer for basic validation
        with open(file_path, 'rb') as f:
            header = f.read(1024)
            
            if not header.startswith(b'%PDF-'):
                return {'valid': False, 'errors': ['Not a valid PDF file']}
            
            # Check for EOF marker
            f.seek(max(0, file_size - 1024))
            footer = f.read()
            
            if b'%%EOF' not in footer:
                return {'valid': False, 'errors': ['PDF file appears corrupted']}
        
        return {'valid': True, 'errors': []}
    
    except Exception as e:
        logger.error(f"Error validating PDF {file_path}: {e}")
        return {'valid': False, 'errors': [str(e)]}


# Initialize configuration
config = ESignConfig.from_env()

# Schedule periodic optimization
def schedule_optimization():
    """Schedule periodic system optimization"""
    import threading
    
    def run_optimization():
        while True:
            time.sleep(3600)  # Run every hour
            try:
                optimize_esign_system()
            except Exception as e:
                logger.error(f"Scheduled optimization failed: {e}")
    
    optimization_thread = threading.Thread(target=run_optimization, daemon=True)
    optimization_thread.start()
    logger.info("Scheduled optimization thread started")


# Auto-start optimization scheduler when module is imported
if __name__ != "__main__":
    schedule_optimization()