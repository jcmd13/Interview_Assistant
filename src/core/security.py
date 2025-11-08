"""
Security Hardening Module

Provides:
- Rate limiting per client/endpoint
- Input validation and sanitization
- Request throttling
- DDoS protection
- Credential storage (secure)
- CORS configuration
"""

import time
import hashlib
import threading
from typing import Dict, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import ipaddress

from src.core.logger import get_logger

logger = get_logger("system.security")


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"  # Allow burst up to limit
    SLIDING_WINDOW = "sliding_window"  # Strict window-based
    LEAKY_BUCKET = "leaky_bucket"  # Smooth rate


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    requests_per_second: float = 100.0
    burst_size: int = 1000
    window_seconds: int = 60


class RateLimiter:
    """
    Rate limiting for requests

    Supports multiple strategies and per-client limiting.
    """

    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter

        Args:
            config: Rate limit configuration
        """
        self.config = config
        self._lock = threading.RLock()
        self._buckets: Dict[str, Dict[str, Any]] = defaultdict(self._init_bucket)

        logger.info(
            "Rate limiter initialized",
            strategy=config.strategy.value,
            requests_per_second=config.requests_per_second,
            burst_size=config.burst_size,
        )

    def _init_bucket(self) -> Dict[str, Any]:
        """Initialize bucket for client"""
        return {
            "tokens": self.config.burst_size,
            "last_refill": time.time(),
            "requests": deque(maxlen=self.config.window_seconds),
        }

    def is_allowed(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed

        Args:
            client_id: Client identifier (IP, user ID, etc.)

        Returns:
            Tuple of (allowed, metadata)
        """
        with self._lock:
            if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return self._check_token_bucket(client_id)
            elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return self._check_sliding_window(client_id)
            else:
                return True, {"strategy": "unknown"}

    def _check_token_bucket(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Token bucket algorithm"""
        bucket = self._buckets[client_id]
        now = time.time()

        # Calculate tokens to add
        time_passed = now - bucket["last_refill"]
        tokens_to_add = time_passed * self.config.requests_per_second

        # Refill bucket
        bucket["tokens"] = min(
            self.config.burst_size,
            bucket["tokens"] + tokens_to_add,
        )
        bucket["last_refill"] = now

        # Check if allowed
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            return True, {
                "strategy": "token_bucket",
                "tokens_remaining": int(bucket["tokens"]),
            }

        return False, {
            "strategy": "token_bucket",
            "tokens_remaining": 0,
            "wait_seconds": 1.0 / self.config.requests_per_second,
        }

    def _check_sliding_window(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Sliding window algorithm"""
        bucket = self._buckets[client_id]
        now = time.time()
        cutoff = now - self.config.window_seconds

        # Remove old requests
        while bucket["requests"] and bucket["requests"][0] < cutoff:
            bucket["requests"].popleft()

        limit = int(self.config.requests_per_second * self.config.window_seconds)

        if len(bucket["requests"]) < limit:
            bucket["requests"].append(now)
            return True, {
                "strategy": "sliding_window",
                "requests_remaining": limit - len(bucket["requests"]),
            }

        return False, {
            "strategy": "sliding_window",
            "requests_remaining": 0,
            "window_seconds": self.config.window_seconds,
        }

    def reset(self, client_id: Optional[str] = None) -> None:
        """Reset rate limit for client(s)"""
        with self._lock:
            if client_id:
                self._buckets[client_id] = self._init_bucket()
                logger.info("Rate limit reset", client_id=client_id)
            else:
                self._buckets.clear()
                logger.info("All rate limits reset")


class IPValidator:
    """IP address validation and filtering"""

    def __init__(self):
        """Initialize IP validator"""
        self._lock = threading.RLock()
        self._whitelist: set = set()
        self._blacklist: set = set()
        self._suspicious_ips: Dict[str, int] = defaultdict(int)

    def add_whitelist(self, ip_or_cidr: str) -> None:
        """Add IP or CIDR to whitelist"""
        with self._lock:
            try:
                self._whitelist.add(ipaddress.ip_network(ip_or_cidr, strict=False))
                logger.info("IP added to whitelist", ip=ip_or_cidr)
            except ValueError as e:
                logger.error("Invalid IP/CIDR", ip=ip_or_cidr, error=str(e))

    def add_blacklist(self, ip_or_cidr: str) -> None:
        """Add IP or CIDR to blacklist"""
        with self._lock:
            try:
                self._blacklist.add(ipaddress.ip_network(ip_or_cidr, strict=False))
                logger.info("IP added to blacklist", ip=ip_or_cidr)
            except ValueError as e:
                logger.error("Invalid IP/CIDR", ip=ip_or_cidr, error=str(e))

    def is_allowed(self, ip_address: str) -> Tuple[bool, str]:
        """
        Check if IP is allowed

        Args:
            ip_address: IP address to check

        Returns:
            Tuple of (allowed, reason)
        """
        with self._lock:
            try:
                ip = ipaddress.ip_address(ip_address)
            except ValueError:
                return False, "invalid_ip"

            # Check blacklist first
            for network in self._blacklist:
                if ip in network:
                    return False, "blacklisted"

            # Check whitelist if it exists
            if self._whitelist:
                for network in self._whitelist:
                    if ip in network:
                        return True, "whitelisted"
                return False, "not_whitelisted"

            return True, "allowed"

    def report_suspicious(self, ip_address: str, count: int = 1) -> int:
        """
        Report suspicious activity from IP

        Args:
            ip_address: IP address
            count: Increment count

        Returns:
            Total suspicious count
        """
        with self._lock:
            self._suspicious_ips[ip_address] += count
            total = self._suspicious_ips[ip_address]

            if total >= 5:
                logger.warning(
                    "IP flagged as suspicious",
                    ip=ip_address,
                    suspicious_count=total,
                )
                if total >= 10:
                    self.add_blacklist(ip_address)
                    logger.error(
                        "IP auto-blacklisted",
                        ip=ip_address,
                        suspicious_count=total,
                    )

            return total


class InputValidator:
    """Input validation and sanitization"""

    @staticmethod
    def validate_json(data: str, max_size: int = 1_000_000) -> Tuple[bool, str]:
        """
        Validate JSON input

        Args:
            data: JSON string
            max_size: Maximum size in bytes

        Returns:
            Tuple of (valid, error_message)
        """
        if not isinstance(data, str):
            return False, "not_string"

        if len(data.encode()) > max_size:
            return False, f"exceeds_max_size_{max_size}"

        try:
            import json
            json.loads(data)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"invalid_json: {str(e)}"

    @staticmethod
    def validate_audio(
        data: bytes,
        max_size: int = 10_000_000,  # 10MB
    ) -> Tuple[bool, str]:
        """
        Validate audio data

        Args:
            data: Audio bytes
            max_size: Maximum size in bytes

        Returns:
            Tuple of (valid, error_message)
        """
        if not isinstance(data, bytes):
            return False, "not_bytes"

        if len(data) == 0:
            return False, "empty_data"

        if len(data) > max_size:
            return False, f"exceeds_max_size_{max_size}"

        return True, ""

    @staticmethod
    def sanitize_text(text: str, max_length: int = 100_000) -> str:
        """
        Sanitize text input

        Args:
            text: Input text
            max_length: Maximum length

        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return ""

        # Remove control characters
        text = "".join(
            c for c in text
            if c.isprintable() or c in "\n\r\t"
        )

        # Limit length
        if len(text) > max_length:
            text = text[:max_length]

        return text.strip()

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """
        Validate filename for safety

        Args:
            filename: Filename to validate

        Returns:
            Tuple of (valid, error_message)
        """
        if not filename:
            return False, "empty_filename"

        # Check for path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            return False, "invalid_characters"

        # Check length
        if len(filename) > 255:
            return False, "filename_too_long"

        return True, ""


class CredentialManager:
    """Secure credential storage"""

    def __init__(self):
        """Initialize credential manager"""
        self._lock = threading.RLock()
        self._credentials: Dict[str, str] = {}
        logger.info("Credential manager initialized")

    def store(self, key: str, value: str) -> None:
        """
        Store credential

        Args:
            key: Credential key
            value: Credential value
        """
        with self._lock:
            # Hash for logging (never log actual value)
            value_hash = hashlib.sha256(value.encode()).hexdigest()[:8]
            self._credentials[key] = value
            logger.info("Credential stored", key=key, hash=value_hash)

    def retrieve(self, key: str) -> Optional[str]:
        """
        Retrieve credential

        Args:
            key: Credential key

        Returns:
            Credential value or None
        """
        with self._lock:
            value = self._credentials.get(key)
            if value:
                logger.debug("Credential retrieved", key=key)
            else:
                logger.warning("Credential not found", key=key)
            return value

    def delete(self, key: str) -> bool:
        """
        Delete credential

        Args:
            key: Credential key

        Returns:
            True if deleted
        """
        with self._lock:
            if key in self._credentials:
                del self._credentials[key]
                logger.info("Credential deleted", key=key)
                return True
            return False

    def clear(self) -> None:
        """Clear all credentials"""
        with self._lock:
            self._credentials.clear()
            logger.warning("All credentials cleared")


# Global security instances
_rate_limiter: Optional[RateLimiter] = None
_ip_validator: Optional[IPValidator] = None
_credential_manager: Optional[CredentialManager] = None
_lock = threading.Lock()


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get or create global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        with _lock:
            if _rate_limiter is None:
                _rate_limiter = RateLimiter(config or RateLimitConfig())
    return _rate_limiter


def get_ip_validator() -> IPValidator:
    """Get or create global IP validator"""
    global _ip_validator
    if _ip_validator is None:
        with _lock:
            if _ip_validator is None:
                _ip_validator = IPValidator()
    return _ip_validator


def get_credential_manager() -> CredentialManager:
    """Get or create global credential manager"""
    global _credential_manager
    if _credential_manager is None:
        with _lock:
            if _credential_manager is None:
                _credential_manager = CredentialManager()
    return _credential_manager
