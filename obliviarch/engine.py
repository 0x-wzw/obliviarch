"""
OBLIVIARCH Engine — The Architecture of Controlled Oblivion.

Unified controller for the Trace Schema Compression pipeline:
  1. Episodic traces (mortal, <48h TTL)
  2. Semantic schemas (patterns born from traces, ~20x)
  3. Archetypal DNA (immortal patterns, ~500x)

The river Lethe runs through every consolidation cycle:
  promote → ascend → archive → forget
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .episodic.trace_capture import TraceCapture
from .semantic.schema_extractor import SchemaExtractor
from .archetypal.archetype_vault import ArchetypeVault
from .lethe.consolidation import run_consolidation

logger = logging.getLogger(__name__)


@dataclass
class ObliviarchConfig:
    """Configuration for the Obliviarch engine."""
    data_dir: str = "data/"
    schema_promotion_threshold: int = 10
    archetype_promotion_threshold: int = 50
    trace_ttl_hours: float = 48.0
    forgetting_threshold_days: int = 90
    consolidation_interval_minutes: float = 30.0

    @property
    def episodic_path(self) -> str:
        return str(Path(self.data_dir) / "episodic/")

    @property
    def semantic_path(self) -> str:
        return str(Path(self.data_dir) / "semantic/")

    @property
    def archetypal_path(self) -> str:
        return str(Path(self.data_dir) / "archetypal/")


class Obliviarch:
    """
    The Architecture of Controlled Oblivion.
    
    Manages the full TSC pipeline:
    - Accepts raw collaboration traces
    - Runs consolidation cycles (promote → ascend → archive → forget)
    - Provides query access across all memory tiers
    """

    def __init__(self, config: Optional[ObliviarchConfig] = None, data_dir: Optional[str] = None):
        if data_dir:
            config = ObliviarchConfig(data_dir=data_dir)
        self.config = config or ObliviarchConfig()

        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)

        self.traces = TraceCapture(storage_path=self.config.episodic_path)
        self.schemas = SchemaExtractor(
            promotion_threshold=self.config.schema_promotion_threshold,
            storage_path=self.config.semantic_path,
        )
        self.archetypes = ArchetypeVault(
            promotion_threshold=self.config.archetype_promotion_threshold,
            storage_path=self.config.archetypal_path,
        )

        self._running = False
        self._cycle_count = 0

    def start(self) -> None:
        """Start Obliviarch — load persistent state."""
        self.traces.load()
        self.schemas.load()
        self.archetypes.load()
        self._running = True
        logger.info(
            f"Obliviarch started: {len(self.traces)} traces, "
            f"{len(self.schemas)} schemas, {len(self.archetypes)} archetypes"
        )

    def stop(self) -> None:
        """Stop Obliviarch — persist all state."""
        self.traces.save()
        self.schemas.save()
        self.archetypes.save()
        self._running = False
        logger.info(f"Obliviarch stopped after {self._cycle_count} cycles")

    def record(
        self,
        agents: List[str],
        task: str,
        steps: List[Dict[str, Any]],
        outcome: str,
        score: float,
    ) -> str:
        """Record a collaboration trace into the mortal layer."""
        trace_id = self.traces.record(
            agents=agents, task=task, steps=steps,
            outcome=outcome, score=score,
        )
        logger.debug(f"Trace {trace_id} recorded: {len(agents)} agents, outcome={outcome}")
        return trace_id

    def consolidate(self) -> Dict[str, Any]:
        """
        Run the river Lethe — a full consolidation cycle.
        
        promote → ascend → archive → forget
        """
        if not self._running:
            raise RuntimeError("Obliviarch not started — call start() first")

        result = run_consolidation(self.traces, self.schemas, self.archetypes)
        self._cycle_count += 1
        logger.info(
            f"Lethe cycle {self._cycle_count}: +{result['new_schemas']} schemas, "
            f"+{result['new_archetypes']} archetypes, "
            f"{result['traces_archived']} archived, "
            f"{result['archetypes_forgotten']} forgotten"
        )
        return result

    def query(self, pattern: str, limit: int = 10) -> Dict[str, List]:
        """
        Query across all memory tiers.
        
        Searches archetypes (immortal), schemas (emerging), 
        and recent traces (mortal) for a pattern match.
        """
        result = {
            "archetypal": [],
            "semantic": [],
            "episodic": [],
        }

        # Level 3: Archetypal (always searched, including cold)
        arch_matches = self.archetypes.query(pattern, include_cold=True)
        result["archetypal"] = [
            {"name": a.name, "pattern": a.pattern, "activation_count": a.activation_count, "cold": a.cold}
            for a in arch_matches
        ]

        # Level 2: Semantic
        schema_matches = self.schemas.query_schemas(pattern, limit=limit)
        result["semantic"] = [
            {"name": s.name, "pattern": s.pattern, "activation_count": s.activation_count}
            for s in schema_matches
        ]

        # Level 1: Episodic (recent only)
        recent = self.traces.recent_traces(hours=24)
        pattern_lower = pattern.lower()
        for trace in recent:
            if pattern_lower in trace.task.lower():
                result["episodic"].append({
                    "trace_id": trace.trace_id,
                    "task": trace.task,
                    "agents": trace.agents,
                    "outcome": trace.outcome,
                    "score": trace.score,
                })

        return result

    def stats(self) -> Dict[str, Any]:
        """Get compression statistics across all tiers."""
        active_traces = len(self.traces.get_unarchived()) if hasattr(self.traces, 'get_unarchived') else len(self.traces)
        active_archetypes = len(self.archetypes.get_active())

        return {
            "episodic": {
                "total_traces": len(self.traces),
                "active_traces": active_traces,
            },
            "semantic": {
                "total_schemas": len(self.schemas),
                "seed_schemas": sum(1 for s in self.schemas.all_schemas() if s.schema_id.startswith("schema_seed_")),
            },
            "archetypal": {
                "total_archetypes": len(self.archetypes),
                "active_archetypes": active_archetypes,
                "cold_archetypes": len(self.archetypes) - active_archetypes,
            },
            "compression": {
                "estimated_raw_mb": active_traces * 0.1,  # ~100KB per trace
                "estimated_schema_kb": len(self.schemas) * 5,  # ~5KB per schema
                "estimated_archetype_kb": len(self.archetypes) * 2,  # ~2KB per archetype
                "total_cycles": self._cycle_count,
            },
        }