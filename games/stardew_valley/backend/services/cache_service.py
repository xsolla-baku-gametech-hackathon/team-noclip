import hashlib
import time
from typing import Dict, Optional, Tuple

from backend.models import GameStateDto, RecapResponseDto


class StateCacheService:
    """
    In-memory state cache using SHA-256 state fingerprints.
    Avoids redundant LLM inferences and eliminates lag when the recap
    modal is opened multiple times within the same in-game day/hour.
    """

    def __init__(self, default_ttl_seconds: float = 60.0, max_size: int = 500):
        self.default_ttl = default_ttl_seconds
        self.max_size = max_size
        # Mapping: fingerprint -> (RecapResponseDto, expiration_timestamp)
        self._cache: Dict[str, Tuple[RecapResponseDto, float]] = {}

    def compute_fingerprint(self, state: GameStateDto) -> str:
        """
        Creates a deterministic hash representing the exact farm condition.
        """
        key_elements = [
            str(state.player.gold),
            str(state.player.farm_name),
            str(state.date.season),
            str(state.date.day),
            str(state.date.year),
            str(state.date.time_of_day),
            str(state.farm.crop_count),
            str(state.farm.ready_to_harvest),
            str(state.farm.needs_water),
            str(state.farm.dead_crops),
            str(len(state.active_quests)),
            str(state.community_center.completed_bundles),
        ]
        raw = "|".join(key_elements)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, state: GameStateDto) -> Optional[RecapResponseDto]:
        """
        Returns cached response if present and unexpired, else None.
        """
        fp = self.compute_fingerprint(state)
        entry = self._cache.get(fp)
        if not entry:
            return None

        response, expires_at = entry
        if time.time() > expires_at:
            del self._cache[fp]
            return None

        return response

    def set(
        self,
        state: GameStateDto,
        response: RecapResponseDto,
        ttl_seconds: Optional[float] = None,
    ) -> None:
        """
        Stores response in cache with TTL and enforces capacity limits.
        """
        now = time.time()
        if len(self._cache) >= self.max_size:
            expired = [k for k, (_, exp) in self._cache.items() if now > exp]
            for k in expired:
                del self._cache[k]
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]

        fp = self.compute_fingerprint(state)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[fp] = (response, now + ttl)

    def clear(self) -> None:
        """Clears all cached entries."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Returns number of currently active cached states."""
        now = time.time()
        expired = [k for k, (_, exp) in self._cache.items() if now > exp]
        for k in expired:
            del self._cache[k]
        return len(self._cache)


# Global singleton instance
cache_service = StateCacheService(default_ttl_seconds=60.0)
