"""Tests for HowlCreate CLI commands."""

from howlcreate.cli.main import main


def test_cli_assumptions(capsys):
    ret = main(["assumptions", "Test problem statement", "--provider", "deterministic"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Assumptions & Inversions" in captured.out


def test_cli_reframe(capsys):
    ret = main(["reframe", "Test problem statement", "--provider", "deterministic"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Reframing Lenses" in captured.out


def test_cli_explore(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("HOWLCREATE_RUNS_DIR", str(tmp_path))
    output_file = tmp_path / "report.md"

    ret = main([
        "explore",
        "How to coordinate remote work?",
        "--provider", "deterministic",
        "--top-n", "2",
        "--output", str(output_file),
    ])
    assert ret == 0
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "HowlCreate Exploration Report" in content
    assert "Converged Finalist Concepts" in content


def test_cli_explore_auto_detect_json(capsys, tmp_path, monkeypatch):
    import json
    monkeypatch.setenv("HOWLCREATE_RUNS_DIR", str(tmp_path))
    output_file = tmp_path / "run.json"

    ret = main([
        "explore",
        "Problem requiring JSON output",
        "--provider", "deterministic",
        "--top-n", "2",
        "--output", str(output_file),
    ])
    assert ret == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["problem"] == "Problem requiring JSON output"
    assert "graph" in data
    assert len(data["finalist_ids"]) == 2


def test_cli_list_and_show(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("HOWLCREATE_RUNS_DIR", str(tmp_path))

    # First run explore
    main([
        "explore",
        "Problem for listing",
        "--provider", "deterministic",
        "--quiet",
    ])

    # List runs
    ret = main(["list"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Problem for listing" in captured.out
