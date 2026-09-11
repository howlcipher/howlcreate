"""Tests for HowlCreate candidate ingestion and deliberate sandbox development."""

import json
import subprocess
import sys
from pathlib import Path
import pytest

from howlcreate.engine.candidate_ingestion import develop_candidate, IngestionError


def make_payloads():
    candidate = {
        "schema_version": "howl.candidate/v1",
        "candidate_id": "run-20260911-001/candidates/0/1",
        "source_run_id": "run-20260911-001",
        "parent_request_id": "req-20260911-alpha",
        "objective": "Explore alternative diagnostic strategies for deployment timeouts",
        "text": "IDEA: eBPF socket tracing probes on staging ingress proxies to catch TCP RST packets during blue-green switchovers",
        "condition": "dream",
        "trust": "UNVERIFIED",
        "status": "LOCALLY_VERIFIED",
        "authority": {"type": "ADVISORY", "executable": False},
        "claims": [
            {"kind": "IDEA", "text": "eBPF socket tracing probes on staging ingress proxies"},
            {"kind": "FACT", "text": "staging ingress runs Linux kernel 6.8+"},
        ],
        "assumptions": ["Kernel BTF support is enabled on staging proxies"],
        "unresolved_issues": ["Overhead under 10k conn/sec unverified"],
        "contradictions": [],
        "verified_constraints": ["Kernel 6.8+ present"],
    }
    assessment = {
        "schema_version": "howl.assessment/v1",
        "assessment_id": "assess-run-20260911-001-c1",
        "candidate_id": "run-20260911-001/candidates/0/1",
        "disposition": "ACCEPT_FOR_DEVELOPMENT",
        "confidence": "MEDIUM",
        "reason": "sufficient evidence invariants passed for deliberate development",
        "authority": {"type": "ADVISORY", "executable": False},
    }
    return candidate, assessment


def test_develop_candidate_accepted():
    cand, assess = make_payloads()
    result = develop_candidate(cand, assess)

    assert result["schema_version"] == "howl.development_result/v1"
    assert result["source_candidate_id"] == cand["candidate_id"]
    assert result["origin"] == "howldream"
    assert result["epistemic_status"] == "IMAGINED_POSSIBILITY"
    assert result["authority"]["executable"] is False
    assert result["authority"]["type"] == "ADVISORY"
    assert result["execution_authority"] == "NONE"

    # Verify idea
    idea = result["idea"]
    assert idea["origin"] == "howldream"
    assert idea["parent_ids"] == [cand["candidate_id"]]

    # Verify lineage
    lineage = result["lineage"]
    assert lineage["parent_id"] == cand["candidate_id"]
    assert cand["candidate_id"] in lineage["ancestors"]

    # Verify sandbox plan
    proto = result["sandbox_prototype_design"]
    assert "isolated_local_testbed" in proto["target_sandbox_environment"]
    assert "NO_PRODUCTION_DEPLOYMENT" in proto["isolation_controls"]


def test_develop_candidate_rejected_fails_closed():
    cand, assess = make_payloads()
    assess["disposition"] = "REJECT"

    with pytest.raises(IngestionError, match="must be 'ACCEPT_FOR_DEVELOPMENT'"):
        develop_candidate(cand, assess)


def test_develop_candidate_unresolved_fails_closed():
    cand, assess = make_payloads()
    assess["disposition"] = "UNRESOLVED"

    with pytest.raises(IngestionError, match="must be 'ACCEPT_FOR_DEVELOPMENT'"):
        develop_candidate(cand, assess)


def test_develop_candidate_authority_escalation_fails_closed():
    cand, assess = make_payloads()
    cand["authority"]["executable"] = True

    with pytest.raises(IngestionError, match="Authority escalation prohibited"):
        develop_candidate(cand, assess)

    cand, assess = make_payloads()
    assess["authority"]["type"] = "EXECUTIVE"

    with pytest.raises(IngestionError, match="Authority escalation prohibited"):
        develop_candidate(cand, assess)


def test_cli_develop(tmp_path: Path):
    cand, assess = make_payloads()
    cand_file = tmp_path / "candidate.json"
    assess_file = tmp_path / "assessment.json"
    out_file = tmp_path / "development_result.json"

    cand_file.write_text(json.dumps(cand, indent=2))
    assess_file.write_text(json.dumps(assess, indent=2))

    cmd = [
        sys.executable,
        "-m",
        "howlcreate.cli.main",
        "develop",
        str(cand_file),
        "--assessment",
        str(assess_file),
        "--output",
        str(out_file),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "[Saved]" in res.stdout
    assert out_file.exists()

    dev_data = json.loads(out_file.read_text())
    assert dev_data["schema_version"] == "howl.development_result/v1"
    assert dev_data["authority"]["executable"] is False
