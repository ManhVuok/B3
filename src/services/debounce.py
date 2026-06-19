import time
import threading

from src.config import settings

class HardwareDebounce:
    def __init__(self):
        self._cache: dict[str, float] = {}
        self._lock = threading.Lock()

    def check(self, card_id: str) -> bool:
        """
        Check if the card is currently debounced.
        Returns True if the card can be processed (not debounced).
        Returns False if the card is in debounce period (should reject).
        """
        now = time.time()
        with self._lock:
            # Cleanup old entries to prevent memory leak
            self._cleanup(now)
            
            last_seen = self._cache.get(card_id)
            if last_seen and (now - last_seen) < settings.debounce_ttl_seconds:
                return False  # Debounced
            
            # Record this check
            self._cache[card_id] = now
            return True

    def _cleanup(self, now: float):
        """Removes entries older than TTL."""
        expired_keys = [k for k, v in self._cache.items() if (now - v) >= settings.debounce_ttl_seconds]
        for k in expired_keys:
            del self._cache[k]

# Global instance
debounce = HardwareDebounce()
