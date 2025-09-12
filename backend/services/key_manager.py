import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
import random

class APIKeyManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.keys = []
        self.key_status = {}  # key -> {'status': 'active'|'rate_limited'|'error', 'last_used': timestamp, 'requests_count': 0, 'tokens_used': 0}
        self.rate_limit_reset_time = time.time() + 60  # Reset every minute
        self.lock = threading.Lock()
        self._initialized = True
    
    def initialize_keys(self, keys):
        """Initialize with API keys"""
        with self.lock:
            self.keys = [key for key in keys if key.strip()]
            for key in self.keys:
                self.key_status[key] = {
                    'status': 'active',
                    'last_used': 0,
                    'requests_count': 0,
                    'tokens_used': 0,
                    'errors_count': 0,
                    'last_error': None
                }
            print(f"Initialized {len(self.keys)} API keys")
    
    def get_active_key(self):
        """Get an active API key with load balancing"""
        with self.lock:
            # Reset counters if minute has passed
            if time.time() > self.rate_limit_reset_time:
                self._reset_counters()
            
            active_keys = [
                key for key in self.keys 
                if self.key_status[key]['status'] == 'active'
            ]
            
            if not active_keys:
                # If all keys are rate limited, try to reset some
                self._reset_old_rate_limits()
                active_keys = [
                    key for key in self.keys 
                    if self.key_status[key]['status'] == 'active'
                ]
            
            if not active_keys:
                raise Exception("All API keys are rate limited or unavailable")
            
            # Choose key with least recent usage (round-robin with load balancing)
            active_keys.sort(key=lambda k: self.key_status[k]['last_used'])
            selected_key = active_keys[0]
            
            self.key_status[selected_key]['last_used'] = time.time()
            self.key_status[selected_key]['requests_count'] += 1
            
            return selected_key
    
    def report_success(self, key, tokens_used=0):
        """Report successful API call"""
        with self.lock:
            if key in self.key_status:
                self.key_status[key]['tokens_used'] += tokens_used
                self.key_status[key]['errors_count'] = 0
    
    def report_error(self, key, error_message):
        """Report API error"""
        with self.lock:
            if key in self.key_status:
                self.key_status[key]['errors_count'] += 1
                self.key_status[key]['last_error'] = error_message
                
                # If too many errors, temporarily disable the key
                if self.key_status[key]['errors_count'] >= 5:
                    self.key_status[key]['status'] = 'error'
                    print(f"Key disabled due to multiple errors: {key[:10]}...")
    
    def report_rate_limit(self, key):
        """Report rate limit hit"""
        with self.lock:
            if key in self.key_status:
                self.key_status[key]['status'] = 'rate_limited'
                # Auto-reenable after 2 minutes
                threading.Timer(120, self._reenable_key, args=[key]).start()
                print(f"Key rate limited: {key[:10]}...")
    
    def _reset_counters(self):
        """Reset rate limit counters"""
        for key in self.keys:
            self.key_status[key]['requests_count'] = 0
            self.key_status[key]['tokens_used'] = 0
        self.rate_limit_reset_time = time.time() + 60
    
    def _reset_old_rate_limits(self):
        """Reset old rate limits"""
        current_time = time.time()
        for key in self.keys:
            if (self.key_status[key]['status'] == 'rate_limited' and 
                current_time - self.key_status[key]['last_used'] > 120):
                self.key_status[key]['status'] = 'active'
                self.key_status[key]['errors_count'] = 0
    
    def _reenable_key(self, key):
        """Re-enable a rate limited key"""
        with self.lock:
            if key in self.key_status:
                self.key_status[key]['status'] = 'active'
                self.key_status[key]['errors_count'] = 0
                print(f"Key re-enabled: {key[:10]}...")
    
    def get_status(self):
        """Get current status of all keys"""
        with self.lock:
            status = {}
            for key in self.keys:
                status[key[:10] + '...'] = self.key_status[key].copy()
                # Don't expose full key in status
                if 'key' in status[key[:10] + '...']:
                    del status[key[:10] + '...']['key']
            return status

# Global instance
key_manager = APIKeyManager()
