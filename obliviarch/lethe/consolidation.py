"""
Lethe — The river of forgetting.

Runs the full TSC compression cycle:
  1. Promote episodic traces → semantic schemas (24h window)
  2. Ascend semantic schemas → archetypal DNA (50+ activations)
  3. Archive old episodic traces
  4. Apply controlled forgetting to dormant archetypes

The river Lethe flows through all memory — noise drowns, signal lives.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from obliviarch.episodic.trace_capture import TraceCapture
from obliviarch.semantic.schema_extractor import SchemaExtractor
from obliviarch.archetypal.archetype_vault import ArchetypeVault

logger = logging.getLogger(__name__)


def run_consolidation(
    traces: TraceCapture,
    schemas: SchemaExtractor,
    archetypes: ArchetypeVault,
) -> Dict[str, Any]:
    """
    Run a complete Lethe cycle: promote → ascend → archive → forget.

    Returns summary of what was promoted, ascended, archived, and forgotten.
    """
    # Phase 1: Promote — extract schemas from recent traces
    recent = traces.recent_traces(hours=24)
    new_schemas = schemas.extract_from_traces(recent)

    # Phase 2: Ascend — promote schemas to archetypes
    all_schemas = schemas.all_schemas()
    new_archetypes = archetypes.promote_from_schemas(all_schemas)

    # Phase 3: Archive — bury old episodic traces
    archived = traces.archive_older_than(hours=48)

    # Phase 4: Forget — controlled oblivion for dormant archetypes
    forgotten = archetypes.apply_forgetting()

    result = {
        "new_schemas": new_schemas,
        "new_archetypes": new_archetypes,
        "traces_archived": archived,
        "archetypes_forgotten": forgotten,
        "trace_count": len(traces),
        "schema_count": len(schemas),
        "archetype_count": len(archetypes),
    }

    logger.info(
        f"Lethe cycle: +{new_schemas} schemas born, "
        f"+{new_archetypes} archetypes ascended, "
        f"{archived} traces buried, "
        f"{forgotten} archetypes forgotten"
    )

    return result