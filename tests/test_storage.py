"""Tests for run persistence and retrieval."""

import pytest
from howlcreate.engine.storage import RunStorage
from howlcreate.models.idea import Idea
from howlcreate.models.run import RunRecord


def test_storage_save_and_load(temp_storage_dir):
    storage = RunStorage(storage_dir=temp_storage_dir)

    record = RunRecord(
        run_id="run-storage-test",
        problem="Test Problem for Storage",
    )
    record.graph.add_idea(Idea(id="node-1", title="Node 1", description="Description 1"))
    record.finalist_ids = ["node-1"]

    path = storage.save_run(record)
    assert path.exists()

    loaded = storage.load_run("run-storage-test")
    assert loaded.run_id == "run-storage-test"
    assert loaded.problem == "Test Problem for Storage"
    assert "node-1" in loaded.graph.nodes
    assert loaded.finalist_ids == ["node-1"]


def test_storage_list_runs(temp_storage_dir):
    storage = RunStorage(storage_dir=temp_storage_dir)
    r1 = RunRecord(run_id="run-001", problem="Prob 1")
    r2 = RunRecord(run_id="run-002", problem="Prob 2")

    storage.save_run(r1)
    storage.save_run(r2)

    runs = storage.list_runs()
    assert len(runs) == 2
    ids = {r["run_id"] for r in runs}
    assert ids == {"run-001", "run-002"}


def test_storage_missing_run_raises(temp_storage_dir):
    storage = RunStorage(storage_dir=temp_storage_dir)
    with pytest.raises(FileNotFoundError):
        storage.load_run("non_existent_run_id_99999")
