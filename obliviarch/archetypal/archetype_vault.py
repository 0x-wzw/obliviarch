"""
Archetype Vault — Schema → Archetype promotion (Level 3 of TSC).

The highest compression level. Archetypes are the "DNA" of swarm behavior —
irreducible patterns that recur across thousands of sessions.

~500x total compression (100MB raw → 200KB archetypes).
Cold storage — accessed only via explicit semantic retrieval.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading

from obliviarch.semantic.schema_extractor import Schema

logger = __import__("logging").getLogger(__name__)


@dataclass
class Archetype:
    """An archetypal collaboration primitive — the DNA of swarm behavior."""
    archetype_id: str
    name: str
    pattern: List[str]
    source_schemas: List[str]
    activation_count: int = 0
    created_at: float = 0.0
    last_activated: float = 0.0
    description: str = ""
    cold: bool = False  # Cold = archived to slow storage

    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()
        if self.last_activated == 0:
            self.last_activated = self.created_at


# Core archetypes — the irreducible primitives
CORE_ARCHETYPES = [
    {
        "name": "IMPLEMENT-REVIEW-PATCH",
        "pattern": ["IMPLEMENT", "REVIEW", "PATCH"],
        "description": "Build something, have it reviewed, fix the issues. The fundamental code collaboration loop.",
    },
    {
        "name": "DECOMPOSE-DISPATCH-AGGREGATE",
        "pattern": ["DECOMPOSE", "DISPATCH", "AGGREGATE"],
        "description": "Break a problem into parts, delegate, combine results. The fundamental parallelism pattern.",
    },
    {
        "name": "CHALLENGE-DEFEND-RESOLVE",
        "pattern": ["CHALLENGE", "DEFEND", "RESOLVE"],
        "description": "One agent challenges an assumption, another defends, both arrive at truth. The adversarial truth-seeking pattern.",
    },
    {
        "name": "EXPLORE-EXPLOIT",
        "pattern": ["EXPLORE", "EXPLOIT"],
        "description": "Search for options, then commit to the best one. The fundamental decision pattern.",
    },
    {
        "name": "PLAN-BUILD-TEST-SHIP",
        "pattern": ["PLAN", "BUILD", "TEST", "SHIP"],
        "description": "Design, implement, verify, deploy. The fundamental delivery pipeline.",
    },
]


class ArchetypeVault:
    """
    Long-term storage of archetypal swarm behavior patterns.
    
    Level 3 of the TSC pipeline. Schemas that recur across 50+ sessions
    are promoted to archetypes — the irreducible patterns that define
    the swarm's behavior DNA.
    
    Compression: ~5MB schemas → ~200KB archetypes (25x).
    Total from raw: ~500x.
    
    Archetypes that stop being activated undergo controlled forgetting —
    not deletion, but demotion to cold storage.
    """

    FORGETTING_THRESHOLD_DAYS = 90  # No activation in 90 days → cold
    REHEAT_THRESHOLD = 0.5  # If a cold archetype is accessed, reheat it

    def __init__(
        self,
        promotion_threshold: int = 50,
        storage_path: str = "data/memory/archetypes/",
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.promotion_threshold = promotion_threshold
        self._archetypes: Dict[str, Archetype] = {}
        self._lock = threading.Lock()

        # Seed core archetypes
        self._seed_core()

    def __len__(self) -> int:
        return len(self._archetypes)

    def _seed_core(self) -> None:
        """Seed with known core archetypes."""
        for adef in CORE_ARCHETYPES:
            aid = f"arch_core_{adef['name'].lower().replace('-', '_')}"
            self._archetypes[aid] = Archetype(
                archetype_id=aid,
                name=adef["name"],
                pattern=adef["pattern"],
                source_schemas=[],
                activation_count=1000,  # Core archetypes start high
                description=adef["description"],
            )

    def promote_from_schemas(self, schemas: List[Schema]) -> int:
        """
        Promote high-activation schemas to archetypes.
        
        Returns count of newly promoted archetypes.
        """
        new_archetypes = 0

        for schema in schemas:
            if schema.promoted_to_archetype:
                continue
            if schema.activation_count < self.promotion_threshold:
                continue

            # Check if this pattern already exists as an archetype
            pattern_key = "-".join(schema.pattern)
            existing = any(a.name == pattern_key for a in self._archetypes.values())

            if not existing:
                with self._lock:
                    aid = f"arch_{uuid.uuid4().hex[:8]}"
                    archetype = Archetype(
                        archetype_id=aid,
                        name=pattern_key,
                        pattern=schema.pattern,
                        source_schemas=[schema.schema_id],
                        activation_count=schema.activation_count,
                        description=f"Auto-promoted from schema after {schema.activation_count} activations",
                    )
                    self._archetypes[aid] = archetype
                    schema.promoted_to_archetype = True
                    new_archetypes += 1
                    logger.info(f"Promoted archetype: {pattern_key}")
            else:
                # Increment existing archetype
                for a in self._archetypes.values():
                    if a.name == pattern_key:
                        a.activation_count += 1
                        a.last_activated = time.time()
                        if a.source_schemas and schema.schema_id not in a.source_schemas:
                            a.source_schemas.append(schema.schema_id)
                        schema.promoted_to_archetype = True
                        break

        return new_archetypes

    def apply_forgetting(self) -> int:
        """
        Apply controlled forgetting — demote cold archetypes.
        
        Archetypes with no activation in FORGETTING_THRESHOLD_DAYS
        are moved to cold storage (not deleted).
        """
        cutoff = time.time() - (self.FORGETTING_THRESHOLD_DAYS * 86400)
        forgotten = 0

        with self._lock:
            for archetype in self._archetypes.values():
                if (not archetype.cold and
                    archetype.last_activated < cutoff and
                    not archetype.archetype_id.startswith("arch_core_")):
                    archetype.cold = True
                    forgotten += 1
                    logger.info(f"Archetype {archetype.name} moved to cold storage")

        return forgotten

    def query(self, pattern: str, include_cold: bool = False) -> List[Archetype]:
        """Find archetypes matching a pattern query."""
        pattern_lower = pattern.lower()
        results = []

        for archetype in self._archetypes.values():
            if archetype.cold and not include_cold:
                continue
            if pattern_lower in archetype.name.lower() or pattern_lower in archetype.description.lower():
                results.append(archetype)
                archetype.last_activated = time.time()
                if archetype.cold:
                    archetype.cold = False  # Reheat on access
                    logger.info(f"Archetype {archetype.name} reheated from cold storage")

        return results

    def get_active(self) -> List[Archetype]:
        """Get all non-cold archetypes."""
        return [a for a in self._archetypes.values() if not a.cold]

    def load(self) -> None:
        """Load archetypes from disk."""
        vault_file = self.storage_path / "archetypes.json"
        if not vault_file.exists():
            return
        try:
            with open(vault_file) as f:
                data = json.load(f)
            self._archetypes.clear()
            self._seed_core()  # Always have core archetypes
            for entry in data.get("archetypes", []):
                arch = Archetype(**entry)
                self._archetypes[arch.archetype_id] = arch
            logger.info(f"Loaded {len(self._archetypes)} archetypes")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load archetypes: {e}")

    def save(self) -> None:
        """Persist archetypes to disk."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        vault_file = self.storage_path / "archetypes.json"
        with self._lock:
            data = {
                "archetypes": [asdict(a) for a in self._archetypes.values()],
                "updated_at": time.time(),
            }
        with open(vault_file, "w") as f:
            json.dump(data, f, indent=2)