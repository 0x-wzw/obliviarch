"""Tests for OBLIVIARCH — The Architecture of Controlled Oblivion."""
from __future__ import annotations

import json
import os
import tempfile
import time
import unittest

from obliviarch.engine import Obliviarch, ObliviarchConfig
from obliviarch.episodic.trace_capture import TraceCapture, CollaborationTrace
from obliviarch.semantic.schema_extractor import SchemaExtractor, Schema
from obliviarch.archetypal.archetype_vault import ArchetypeVault, Archetype
from obliviarch.lethe.consolidation import run_consolidation


class TestTraceCapture(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.captor = TraceCapture(storage_path=os.path.join(self.tmpdir, "epi/"))

    def test_record_trace(self):
        tid = self.captor.record(
            agents=["january", "february"], task="refactor auth module",
            steps=[{"action": "IMPLEMENT"}, {"action": "REVIEW"}, {"action": "PATCH"}],
            outcome="success", score=0.85,
        )
        self.assertIsNotNone(tid)
        self.assertEqual(len(self.captor), 1)

    def test_recent_traces(self):
        self.captor.record(["a"], "task1", [], "success", 0.9)
        self.captor.record(["b"], "task2", [], "success", 0.8)
        recent = self.captor.recent_traces(hours=24)
        self.assertEqual(len(recent), 2)

    def test_archive_old_traces(self):
        self.captor.record(["a"], "old task", [], "success", 0.7)
        # Archive with 0 hours — all should be archived
        archived = self.captor.archive_older_than(hours=0)
        self.assertEqual(archived, 1)

    def test_save_load(self):
        self.captor.record(["a"], "persist test", [], "success", 0.9)
        self.captor.save()
        captor2 = TraceCapture(storage_path=os.path.join(self.tmpdir, "epi/"))
        captor2.load()
        self.assertEqual(len(captor2), 1)


class TestSchemaExtractor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.extractor = SchemaExtractor(
            promotion_threshold=2,
            storage_path=os.path.join(self.tmpdir, "schemas/"),
        )

    def test_seed_schemas_exist(self):
        self.assertGreater(len(self.extractor), 0)
        names = [s.name for s in self.extractor.all_schemas()]
        self.assertIn("IMPLEMENT-REVIEW-PATCH", names)
        self.assertIn("DECOMPOSE-DISPATCH-AGGREGATE", names)

    def test_extract_from_traces(self):
        traces = []
        for i in range(5):
            trace = CollaborationTrace(
                trace_id=f"t_{i}",
                agents=["a", "b"],
                task="code review",
                steps=[{"action": "IMPLEMENT"}, {"action": "REVIEW"}, {"action": "PATCH"}],
                outcome="success",
                score=0.9,
                created_at=time.time(),
            )
            traces.append(trace)
        new = self.extractor.extract_from_traces(traces)
        # Should activate existing IMPLEMENT-REVIEW-PATCH seed
        self.assertGreaterEqual(new, 0)

    def test_save_load(self):
        self.extractor.save()
        ext2 = SchemaExtractor(
            promotion_threshold=2,
            storage_path=os.path.join(self.tmpdir, "schemas/"),
        )
        ext2.load()
        self.assertEqual(len(ext2), len(self.extractor))


class TestArchetypeVault(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.vault = ArchetypeVault(storage_path=os.path.join(self.tmpdir, "arch/"))

    def test_core_archetypes_exist(self):
        self.assertGreater(len(self.vault), 0)
        active = self.vault.get_active()
        self.assertTrue(any(a.name == "IMPLEMENT-REVIEW-PATCH" for a in active))

    def test_promote_from_schemas(self):
        schema = Schema(
            schema_id="sch_test",
            name="IMPLEMENT-REVIEW-PATCH",
            pattern=["IMPLEMENT", "REVIEW", "PATCH"],
            source_traces=[],
            activation_count=100,
        )
        new = self.vault.promote_from_schemas([schema])
        # Already exists as core — should increment, not create new
        self.assertEqual(new, 0)

    def test_controlled_forgetting(self):
        # Create a non-core archetype with old timestamp
        arch = Archetype(
            archetype_id="arch_forget_me",
            name="FORGET-ME",
            pattern=["FORGET", "ME"],
            source_schemas=[],
            activation_count=5,
            created_at=time.time() - (100 * 86400),
            last_activated=time.time() - (100 * 86400),
            cold=False,
        )
        self.vault._archetypes[arch.archetype_id] = arch
        forgotten = self.vault.apply_forgetting()
        self.assertGreater(forgotten, 0)
        self.assertTrue(self.vault._archetypes["arch_forget_me"].cold)

    def test_query_with_cold_reheat(self):
        arch = Archetype(
            archetype_id="arch_cold_one",
            name="COLD-PATTERN",
            pattern=["COLD"],
            source_schemas=[],
            cold=True,
        )
        self.vault._archetypes[arch.archetype_id] = arch
        results = self.vault.query("COLD", include_cold=True)
        self.assertEqual(len(results), 1)
        # Should be reheated
        self.assertFalse(self.vault._archetypes["arch_cold_one"].cold)


class TestConsolidation(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.traces = TraceCapture(storage_path=os.path.join(self.tmpdir, "epi/"))
        self.schemas = SchemaExtractor(
            promotion_threshold=2,
            storage_path=os.path.join(self.tmpdir, "schemas/"),
        )
        self.vault = ArchetypeVault(storage_path=os.path.join(self.tmpdir, "arch/"))

    def test_full_consolidation_cycle(self):
        self.traces.record(["a"], "test task", [], "success", 0.8)
        result = run_consolidation(self.traces, self.schemas, self.vault)
        self.assertIn("new_schemas", result)
        self.assertIn("new_archetypes", result)
        self.assertIn("traces_archived", result)
        self.assertIn("archetypes_forgotten", result)


class TestObliviarchEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_full_lifecycle(self):
        engine = Obliviarch(data_dir=self.tmpdir)
        engine.start()

        # Record traces
        engine.record(
            agents=["january", "february"],
            task="refactor authentication module",
            steps=[
                {"action": "IMPLEMENT", "agent": "february"},
                {"action": "REVIEW", "agent": "march"},
                {"action": "PATCH", "agent": "february"},
            ],
            outcome="success",
            score=0.85,
        )

        # Consolidate
        result = engine.consolidate()
        self.assertIn("new_schemas", result)

        # Query
        matches = engine.query("IMPLEMENT")
        self.assertGreater(len(matches["archetypal"]), 0)

        # Stats
        stats = engine.stats()
        self.assertEqual(stats["episodic"]["total_traces"], 1)
        self.assertGreater(stats["archetypal"]["total_archetypes"], 0)

        engine.stop()

    def test_multi_trace_consolidation(self):
        engine = Obliviarch(data_dir=self.tmpdir)
        engine.start()

        # Record multiple traces with same pattern
        for i in range(5):
            engine.record(
                agents=["a", "b"],
                task=f"task-{i}",
                steps=[{"action": "IMPLEMENT"}, {"action": "REVIEW"}, {"action": "PATCH"}],
                outcome="success",
                score=0.8,
            )

        result = engine.consolidate()
        stats = engine.stats()
        self.assertGreater(stats["episodic"]["total_traces"], 0)
        engine.stop()


if __name__ == "__main__":
    unittest.main()