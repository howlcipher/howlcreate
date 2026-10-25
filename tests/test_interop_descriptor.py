"""The howl.interop/v1 descriptor matches the real command line."""

import json
import os
import re
import subprocess
import sys

from howlcreate import __version__
from howlcreate.cli.main import build_parser, main

FLAG = re.compile(r"^--?[A-Za-z0-9][A-Za-z0-9_-]*$")
SCHEMA_ID = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+/v[0-9]+$")


def describe(capsys):
    assert main(["interop", "--json"]) == 0
    return json.loads(capsys.readouterr().out)


def test_descriptor_shape(capsys):
    d = describe(capsys)
    assert (d["schema"], d["component"], d["version"]) == ("howl.interop/v1", "howlcreate", __version__)
    assert set(d["exit_codes"]) == {"0", "1", "2", "3"}
    for command in d["commands"]:
        assert all(FLAG.match(f) for f in command["flags"]), command
        for schema in command.get("emits", []) + command.get("accepts", []):
            assert SCHEMA_ID.match(schema), schema


def test_version_matches_pyproject():
    from pathlib import Path
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    assert __version__ == data["project"]["version"]


def test_every_subcommand_and_flag_is_described(capsys):
    described = {tuple(c["path"]): set(c["flags"]) for c in describe(capsys)["commands"]}
    parser = build_parser()
    subparsers = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    for name, sub in subparsers.choices.items():
        assert described[(name,)] == {o for a in sub._actions for o in a.option_strings} - {"-h", "--help"}
    assert "--version" in described[()]


def test_commands_howlplane_runs_are_described(capsys):
    commands = {tuple(c["path"]): c for c in describe(capsys)["commands"]}
    for mode in ("develop", "scaffold"):
        assert {"--from-writer", "--from-dream", "--output", "--provider", "--command-config"} <= set(
            commands[(mode,)]["flags"]
        )
        assert "howl.development_result/v1" in commands[(mode,)]["emits"]
    assert {"--input", "--output-dir"} <= set(commands[("materialize",)]["flags"])


def test_unknown_run_is_rejected_input_not_an_incomplete_run(tmp_path, monkeypatch):
    monkeypatch.setenv("HOWLCREATE_RUNS_DIR", str(tmp_path))
    for command in ("show", "graph", "export"):
        assert main([command, "no-such-run"]) == 2, command


def test_status_lines_stay_off_stdout(tmp_path):
    out = tmp_path / "out.json"
    result = subprocess.run(
        [sys.executable, "-m", "howlcreate.cli.main", "explore", "a problem", "--provider",
         "deterministic", "--output", str(out), "--quiet"],
        capture_output=True, text=True, check=False, env={**os.environ, "HOWLCREATE_RUNS_DIR": str(tmp_path)},
    )
    assert "[Saved]" not in result.stdout
    assert "[Saved]" in result.stderr
