"""Writer copy package -> Create development -> sandbox materialization."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from howlcreate.cli.main import main
from howlcreate.engine.candidate_ingestion import IngestionError
from howlcreate.engine.materialize import MANIFEST_NAME, materialize
from howlcreate.engine.sandbox import SandboxError, SandboxRoot, validate_relative
from howlcreate.engine.writer_intake import develop_from_writer, validate_writer_package
from howlcreate.providers.base import BaseProvider, ProviderResponse

FIXTURES = Path(__file__).parent / "fixtures"


def package():
    return json.loads((FIXTURES / "writer_copy_package.json").read_text())


def dream():
    return json.loads((FIXTURES / "dream_candidate.json").read_text())


class DesigningRemote(BaseProvider):
    """Stands in for a live remote adapter; returns a page design over Writer copy."""

    def __init__(self):
        super().__init__("fake-model")
        self.prompts = []

    def generate(self, prompt, **kwargs):
        self.prompts.append(prompt)
        data = {
            "sandbox_prototype_design": {
                "page": {
                    "title": "Fictional portfolio",
                    "sections": [
                        {"id": "hero", "heading": "", "layout": "hero", "items": ["hero"]},
                        {
                            "id": "what-i-build",
                            "heading": "What I Build",
                            "layout": "cards",
                            "items": [{"title": "tool-title", "body": "tool-body"}, "invented-id"],
                        },
                    ],
                }
            },
            "test_specification": [{"assertion": "artifact cards precede metrics"}],
            "architecture_proposal": "Artifact-first single page.",
        }
        return ProviderResponse(
            json.dumps(data),
            "fake-model",
            "fake_remote",
            metadata={
                "execution": {
                    "actual_provider": "fake_remote",
                    "model": "fake-model",
                    "mocked": False,
                    "inference_occurred": True,
                }
            },
        )


def test_writer_package_ingested_natively_with_lineage():
    result = develop_from_writer(package(), dream(), scaffold=True)
    slot = result["sandbox_prototype_design"]["writer_copy"]
    assert slot["writer_proposal_id"] == package()["writer_proposal_id"]
    assert result["lineage"]["dream_source_id"] == dream()["candidate_id"]
    assert result["lineage"]["writer_proposal_id"] == package()["writer_proposal_id"]
    assert result["lineage"]["create_development_id"] == result["development_id"]
    assert result["source_candidate_id"] == dream()["candidate_id"]
    assert result["provenance"]["contribution"]["operation"] == "DESIGNED"


def test_unpreserved_proposals_are_withheld_not_materialized():
    slot = develop_from_writer(package(), scaffold=True)["sandbox_prototype_design"]["writer_copy"]
    assert slot["withheld_item_ids"] == ["tool-body"]
    body = next(p for p in slot["proposals"] if p["item_id"] == "tool-body")
    assert body["materialized_text"] == body["current_text"]


def test_writer_package_must_match_dream_source():
    other = dream()
    other["candidate_id"] = "hd-other/candidate/1"
    with pytest.raises(IngestionError, match="do not match"):
        develop_from_writer(package(), other, scaffold=True)


@pytest.mark.parametrize(
    "mutate,where",
    [
        (lambda p: p.update(authority={"type": "ADVISORY", "executable": True}), "authority"),
        (lambda p: p.pop("writer_proposal_id"), "(root)"),
        (
            lambda p: p["proposals"][0].update(factual_status="TRUST_ME"),
            "proposals/0/factual_status",
        ),
    ],
)
def test_invalid_writer_package_is_rejected_with_location(mutate, where):
    value = package()
    mutate(value)
    with pytest.raises(IngestionError, match=where.replace("(", r"\(").replace(")", r"\)")):
        validate_writer_package(value)


def test_model_backed_develop_designs_page_from_writer_copy():
    remote = DesigningRemote()
    result = develop_from_writer(package(), dream(), remote)
    assert "writer_copy" in remote.prompts[0] and "page" in remote.prompts[0]
    assert result["sandbox_prototype_design"]["page"]["title"] == "Fictional portfolio"
    assert result["provenance"]["contribution"]["inference_occurred"] is True


def test_materialize_writes_artifacts_and_manifest(tmp_path):
    development = develop_from_writer(package(), dream(), DesigningRemote())
    out = tmp_path / "sandbox"
    manifest = materialize(development, str(out))
    names = sorted(a["path"] for a in manifest["artifacts"])
    assert names == ["DESIGN.md", "copy.json", "index.html", "styles.css"]
    on_disk = json.loads((out / MANIFEST_NAME).read_text())
    assert on_disk["create_run_id"] == development["development_id"]
    assert on_disk["source_dream_ids"] == [dream()["candidate_id"]]
    assert on_disk["source_writer_ids"] == [package()["writer_proposal_id"]]
    assert on_disk["contribution"] == {"component": "howlcreate", "operation": "MATERIALIZED"}
    assert on_disk["materialization"]["inference_occurred"] is False
    assert on_disk["design"]["model"] == "fake-model"
    assert on_disk["withheld_item_ids"] == ["tool-body"]
    assert "What I Build" in on_disk["design_authored_text"]
    assert "ignored unknown copy reference 'invented-id'" in on_disk["design_warnings"]
    html = (out / "index.html").read_text()
    assert html.index('data-copy-id="hero"') < html.index('id="what-i-build"')
    # The conflicting proposal never reaches the page; the current copy does.
    assert "in production" not in html
    assert "Dry-run validated release paths for 9 of 12 services." in html
    # Unplaced copy is rendered and named, never silently dropped.
    assert on_disk["unplaced_item_ids"] == ["scope"]
    for artifact in on_disk["artifacts"]:
        assert artifact["create_run_id"] == development["development_id"]
        assert artifact["artifact_id"].startswith("art-")


def test_materialization_is_deterministic(tmp_path):
    development = develop_from_writer(package(), dream(), scaffold=True)
    first = materialize(development, str(tmp_path / "a"))
    second = materialize(development, str(tmp_path / "b"))
    assert [a["sha256"] for a in first["artifacts"]] == [a["sha256"] for a in second["artifacts"]]


def test_html_escapes_copy(tmp_path):
    value = package()
    value["proposals"][0]["proposed_text"] = "<script>alert(1)</script>"
    value["proposals"][0]["current_text"] = "<script>alert(1)</script>"
    development = develop_from_writer(value, scaffold=True)
    materialize(development, str(tmp_path / "out"))
    html = (tmp_path / "out" / "index.html").read_text()
    assert "<script>" not in html and "&lt;script&gt;" in html


@pytest.mark.parametrize(
    "name",
    [
        "../escape.html",
        "a/../../escape.html",
        "/etc/passwd.html",
        "~/x.html",
        "x.sh",
        ".git/config.md",
        "a\\b.html",
        "",
    ],
)
def test_unsafe_artifact_paths_denied(name):
    with pytest.raises(SandboxError):
        validate_relative(name)


def test_approved_sandbox_passes(tmp_path):
    root = SandboxRoot(tmp_path / "ok")
    assert root.write("nested/page.html", b"x") == root.path / "nested/page.html"


def test_symlinked_leaf_escape_denied(tmp_path):
    outside = tmp_path / "outside.html"
    outside.write_text("original")
    root = SandboxRoot(tmp_path / "box")
    (root.path / "index.html").symlink_to(outside)
    with pytest.raises(SandboxError):
        root.write("index.html", b"pwned")
    assert outside.read_text() == "original"


def test_symlinked_directory_escape_denied(tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    root = SandboxRoot(tmp_path / "box")
    (root.path / "assets").symlink_to(outside, target_is_directory=True)
    with pytest.raises(SandboxError):
        root.write("assets/page.html", b"pwned")
    assert not (outside / "page.html").exists()


def test_symlinked_root_denied(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "link").symlink_to(real, target_is_directory=True)
    with pytest.raises(SandboxError, match="symlink"):
        SandboxRoot(tmp_path / "link")


def test_live_repository_denied_by_default(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    with pytest.raises(SandboxError, match="git work tree"):
        SandboxRoot(repo / "site")
    assert SandboxRoot(repo / "site", allow_repo=True).path == (repo / "site").resolve()


def test_unapproved_absolute_root_denied_by_allowlist(tmp_path, monkeypatch):
    monkeypatch.setenv("HOWLCREATE_SANDBOX_ROOTS", str(tmp_path / "approved"))
    (tmp_path / "approved").mkdir()
    SandboxRoot(tmp_path / "approved" / "run")
    with pytest.raises(SandboxError, match="outside"):
        SandboxRoot(tmp_path / "unapproved")


def test_overbroad_and_nonempty_roots_denied(tmp_path):
    with pytest.raises(SandboxError):
        SandboxRoot("/")
    (tmp_path / "full").mkdir()
    (tmp_path / "full" / "keep.txt").write_text("x")
    with pytest.raises(SandboxError, match="not empty"):
        SandboxRoot(tmp_path / "full")


def test_cli_scaffold_then_materialize(tmp_path):
    pkg, dev, out = FIXTURES / "writer_copy_package.json", tmp_path / "dev.json", tmp_path / "site"
    assert (
        main(
            [
                "scaffold",
                "--from-writer",
                str(pkg),
                "--from-dream",
                str(FIXTURES / "dream_candidate.json"),
                "--output",
                str(dev),
            ]
        )
        == 0
    )
    assert main(["materialize", "--input", str(dev), "--output-dir", str(out)]) == 0
    assert (out / "index.html").is_file() and (out / MANIFEST_NAME).is_file()


def test_cli_materialize_denies_repo_and_reports(tmp_path, capsys):
    dev = tmp_path / "dev.json"
    main(
        [
            "scaffold",
            "--from-writer",
            str(FIXTURES / "writer_copy_package.json"),
            "--output",
            str(dev),
        ]
    )
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    assert main(["materialize", "--input", str(dev), "--output-dir", str(repo / "site")]) == 3
    assert "denied" in capsys.readouterr().err
    assert not (repo / "site").exists()


def test_cli_develop_from_writer_requires_model_provider(tmp_path):
    assert main(["develop", "--from-writer", str(FIXTURES / "writer_copy_package.json")]) == 2


def test_module_entrypoint():
    process = subprocess.run(
        [sys.executable, "-m", "howlcreate.cli", "--version"],
        capture_output=True,
        check=False,
        text=True,
        env={**os.environ},
    )
    assert process.returncode == 0


def test_oversized_candidate_error_names_field_and_size():
    # Run 5 CX CF02: a 50,329-character input failed with no field or size.
    from howlcreate.engine.candidate_ingestion import validate_envelope

    candidate = dream()
    candidate["text"] = "x" * 50329
    with pytest.raises(IngestionError, match=r"at text \(maxLength 50000, got 50329 characters\)"):
        validate_envelope(candidate, "howl.candidate.v1")
