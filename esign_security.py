"""
E-Signature Security Components for MPT-CRM
==========================================

Enhanced security features for Phase 4:
1. Input validation and sanitization
2. Rate limiting protection
3. Security headers
4. Anti-fraud measures
5. Secure token management
"""

import hashlib
import hmac
import time
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import streamlit as st
from functools import wraps
import uuid
import secrets


class ESignSecurityValidator:
    """Security validation for E-Signature operations"""
    
    # Input validation patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    NAME_PATTERN = re.compile(r'^[a-zA-Z\s\-\'\.]{1,100}$')  # Letters, spaces, hyphens, apostrophes, periods
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    
    # File validation
    MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_PDF_MIMES = ['application/pdf']
    PDF_MAGIC_NUMBERS = [b'%PDF-']
    
    @classmethod
    def validate_email(cls, email: str) -> Dict[str, Any]:
        """Validate email address"""
        result = {"valid": False, "errors": []}
        
        if not email:
            result["errors"].append("Email is required")
            return result
        
        if len(email) > 254:  # RFC standard max length
            result["errors"].append("Email too long (max 254 characters)")
            return result
        
        if not cls.EMAIL_PATTERN.match(email):
            result["errors"].append("Invalid email format")
            return result
        
        # Check for common suspicious patterns
        suspicious_patterns = [
            r'\.{2,}',  # Multiple dots
            r'^\.|\.$',  # Starts or ends with dot
            r'@.*@',  # Multiple @ symbols
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, email):
                result["errors"].append("Email contains suspicious patterns")
                return result
        
        result["valid"] = True
        return result
    
    @classmethod
    def validate_name(cls, name: str, field_name: str = "Name") -> Dict[str, Any]:
        """Validate person name"""
        result = {"valid": False, "errors": []}
        
        if not name:
            result["errors"].append(f"{field_name} is required")
            return result
        
        if len(name) > 100:
            result["errors"].append(f"{field_name} too long (max 100 characters)")
            return result
        
        if not cls.NAME_PATTERN.match(name):
            result["errors"].append(f"{field_name} contains invalid characters")
            return result
        
        # Check for suspicious patterns
        if len(name.strip()) < 2:
            result["errors"].append(f"{field_name} too short")
            return result
        
        # Check for script injection attempts
        script_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
        ]
        
        name_lower = name.lower()
        for pattern in script_patterns:
            if pattern in name_lower:
                result["errors"].append(f"{field_name} contains prohibited content")
                return result
        
        result["valid"] = True
        return result
    
    @classmethod
    def validate_uuid_token(cls, token: str) -> Dict[str, Any]:
        """Validate UUID token format"""
        result = {"valid": False, "errors": []}
        
        if not token:
            result["errors"].append("Token is required")
            return result
        
        if not cls.UUID_PATTERN.match(token):
            result["errors"].append("Invalid token format")
            return result
        
        result["valid"] = True
        return result
    
    @classmethod
    def validate_pdf_file(cls, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded PDF file"""
        result = {"valid": False, "errors": []}
        
        if not file_data:
            result["errors"].append("File data is required")
            return result
        
        # Check file size
        if len(file_data) > cls.MAX_PDF_SIZE:
            result["errors"].append(f"File too large (max {cls.MAX_PDF_SIZE // (1024*1024)}MB)")
            return result
        
        if len(file_data) < 100:  # Minimum PDF size
            result["errors"].append("File too small to be a valid PDF")
            return result
        
        # Check PDF magic number
        is_pdf = False
        for magic in cls.PDF_MAGIC_NUMBERS:
            if file_data.startswith(magic):
                is_pdf = True
                break
        
        if not is_pdf:
            result["errors"].append("File is not a valid PDF")
            return result
        
        # Check filename
        if not filename.lower().endswith('.pdf'):
            result["errors"].append("File must have .pdf extension")
            return result
        
        # Basic PDF structure validation
        if b'%%EOF' not in file_data[-1024:]:  # EOF marker should be near end
            result["errors"].append("PDF file appears to be corrupted")
            return result
        
        result["valid"] = True
        return result
    
    @classmethod
    def sanitize_input(cls, input_str: str, max_length: int = 255) -> str:
        """Sanitize user input"""
        if not input_str:
            return ""
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in input_str if ord(char) >= 32 or char in '\t\n\r')
        
        # Trim whitespace and limit length
        sanitized = sanitized.strip()[:max_length]
        
        return sanitized
    
    @classmethod
    def generate_secure_token(cls) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def hash_sensitive_data(cls, data: str, salt: str = None) -> str:
        """Hash sensitive data with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for secure hashing
        from hashlib import pbkdf2_hmac
        hash_value = pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return f"{salt}:{hash_value.hex()}"


class ESignRateLimit:
    """Rate limiting for E-Signature operations"""
    
    def __init__(self):
        # In production, use Redis or database for distributed rate limiting
        self._requests = {}  # {ip: [(timestamp, action), ...]}
        self._cleanup_interval = 3600  # 1 hour
        self._last_cleanup = time.time()
    
    def _cleanup_old_requests(self):
        """Remove old request records"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Keep last hour
        for ip in list(self._requests.keys()):
            self._requests[ip] = [
                (timestamp, action) for timestamp, action in self._requests[ip]
                if timestamp > cutoff_time
            ]
            if not self._requests[ip]:
                del self._requests[ip]
        
        self._last_cleanup = current_time
    
    def is_rate_limited(self, client_ip: str, action: str, 
                       limit: int = 10, window: int = 3600) -> bool:
        """Check if client is rate limited"""
        self._cleanup_old_requests()
        
        current_time = time.time()
        window_start = current_time - window
        
        if client_ip not in self._requests:
            self._requests[client_ip] = []
        
        # Count requests in window
        recent_requests = [
            (timestamp, req_action) for timestamp, req_action in self._requests[client_ip]
            if timestamp > window_start and req_action == action
        ]
        
        if len(recent_requests) >= limit:
            return True
        
        # Record this request
        self._requests[client_ip].append((current_time, action))
        return False
    
    def get_remaining_requests(self, client_ip: str, action: str, 
                              limit: int = 10, window: int = 3600) -> int:
        """Get remaining requests for client"""
        current_time = time.time()
        window_start = current_time - window
        
        if client_ip not in self._requests:
            return limit
        
        recent_count = sum(
            1 for timestamp, req_action in self._requests[client_ip]
            if timestamp > window_start and req_action == action
        )
        
        return max(0, limit - recent_count)


# Global rate limiter instance
rate_limiter = ESignRateLimit()


def rate_limit(action: str, limit: int = 10, window: int = 3600):
    """Decorator for rate limiting Streamlit functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get client IP (in production, use proper IP detection)
            client_ip = st.session_state.get('client_ip', 'unknown')
            
            if rate_limiter.is_rate_limited(client_ip, action, limit, window):
                remaining = rate_limiter.get_remaining_requests(client_ip, action, limit, window)
                st.error(f"Rate limit exceeded for {action}. Try again in a few minutes.")
                st.info(f"Remaining requests: {remaining}")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class ESignSecurityHeaders:
    """Security headers for E-Signature pages"""
    
    @staticmethod
    def inject_security_headers():
        """Inject security headers into Streamlit page"""
        security_headers = """
        <script>
            // Inject security headers via meta tags
            const head = document.head;
            
            // Content Security Policy
            const csp = document.createElement('meta');
            csp.httpEquiv = 'Content-Security-Policy';
            csp.content = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self' https://fonts.gstatic.com;";
            head.appendChild(csp);
            
            // X-Content-Type-Options
            const xcto = document.createElement('meta');
            xcto.httpEquiv = 'X-Content-Type-Options';
            xcto.content = 'nosniff';
            head.appendChild(xcto);
            
            // X-Frame-Options
            const xfo = document.createElement('meta');
            xfo.httpEquiv = 'X-Frame-Options';
            xfo.content = 'DENY';
            head.appendChild(xfo);
            
            // X-XSS-Protection
            const xxp = document.createElement('meta');
            xxp.httpEquiv = 'X-XSS-Protection';
            xxp.content = '1; mode=block';
            head.appendChild(xxp);
            
            // Referrer Policy
            const rp = document.createElement('meta');
            rp.name = 'referrer';
            rp.content = 'strict-origin-when-cross-origin';
            head.appendChild(rp);
            
            // Disable right-click and text selection for signed documents
            if (window.location.pathname.includes('/sign/')) {
                document.addEventListener('contextmenu', function(e) {
                    e.preventDefault();
                });
                
                document.addEventListener('selectstart', function(e) {
                    if (e.target.closest('.pdf-viewer') || e.target.closest('.signature-area')) {
                        e.preventDefault();
                    }
                });
                
                // Disable F12, Ctrl+Shift+I, etc.
                document.addEventListener('keydown', function(e) {
                    if (e.key === 'F12' || 
                        (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C' || e.key === 'J')) ||
                        (e.ctrlKey && e.key === 'U')) {
                        e.preventDefault();
                        return false;
                    }
                });
            }
        </script>
        """
        
        st.components.v1.html(security_headers, height=0)


class ESignFraudDetection:
    """Fraud detection for E-Signature operations"""
    
    @staticmethod
    def detect_suspicious_activity(signer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potentially fraudulent signing activity"""
        flags = []
        risk_score = 0
        
        # Check for suspicious email patterns
        email = signer_data.get('email', '')
        if email:
            # Temporary/disposable email domains
            temp_domains = [
                'mailinator.com', 'guerrillamail.com', 'tempmail.org',
                '10minutemail.com', 'throwaway.email', 'temp-mail.org'
            ]
            
            domain = email.split('@')[-1].lower()
            if domain in temp_domains:
                flags.append("Temporary email domain")
                risk_score += 30
            
            # Sequential characters or obvious patterns
            if re.search(r'(.)\1{3,}', email) or '12345' in email:
                flags.append("Suspicious email pattern")
                risk_score += 20
        
        # Check signing speed (too fast might indicate automated signing)
        time_to_sign = signer_data.get('time_to_sign', 0)
        if time_to_sign < 30:  # Less than 30 seconds
            flags.append("Very fast signing (potential automation)")
            risk_score += 25
        
        # Check signature consistency
        signature_type = signer_data.get('signature_type', '')
        if signature_type == 'typed' and signer_data.get('typed_name', '').lower() != signer_data.get('signer_name', '').lower():
            flags.append("Typed signature doesn't match signer name")
            risk_score += 40
        
        # Check for multiple signing attempts
        attempt_count = signer_data.get('attempt_count', 1)
        if attempt_count > 5:
            flags.append("Multiple signing attempts")
            risk_score += 15
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "flags": flags,
            "recommended_action": "MANUAL_REVIEW" if risk_score >= 60 else "APPROVE"
        }


def secure_session_state(key: str, default_value: Any = None, 
                        validator: callable = None) -> Any:
    """Securely get/set session state with validation"""
    if key not in st.session_state:
        st.session_state[key] = default_value
    
    value = st.session_state[key]
    
    if validator and value is not None:
        if not validator(value):
            st.session_state[key] = default_value
            return default_value
    
    return value


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """Log security-related events"""
    timestamp = datetime.utcnow().isoformat()
    client_ip = st.session_state.get('client_ip', 'unknown')
    user_agent = st.session_state.get('user_agent', 'unknown')
    
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "severity": severity,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "details": details
    }
    
    # In production, send to proper logging system (e.g., CloudWatch, Splunk)
    print(f"[SECURITY] {severity}: {event_type} - {details}")
    
    # Store in session state for debugging
    if 'security_logs' not in st.session_state:
        st.session_state['security_logs'] = []
    
    st.session_state['security_logs'].append(log_entry)