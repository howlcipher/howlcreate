"""The ``howl.interop/v1`` descriptor printed by ``howlcreate interop --json``.

HowlPlane runs ``develop``, ``scaffold`` and ``materialize``; ``howl doctor``
reads this descriptor to check that those commands and flags still exist. It
is built from the live argparse tree, so it cannot list a flag the CLI does not
accept. Contract: https://github.com/howlcipher/howl/blob/main/docs/INTEROP.md
"""

import argparse

from howlcreate import __version__

SCHEMA = "howl.interop/v1"

EXIT_CODES = {
    "0": "ok",
    "1": "an exploration or resumed run that did not complete (its record is still written)",
    "2": "rejected input, unknown run ID, or a provider or input failure",
    "3": "materialization denied by the sandbox rules",
}

ENV = ["HOWLCREATE_RUNS_DIR", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE", "OLLAMA_HOST"]

# Commands that print JSON on stdout: always, or with --format json.
JSON_COMMANDS = {"explore", "run", "create", "resume", "show", "export", "develop", "scaffold", "interop"}

EMITS = {
    "export": ["howl.candidate/v1"],
    "develop": ["howl.development_result/v1"],
    "scaffold": ["howl.development_result/v1"],
    "materialize": ["howlcreate.artifact_manifest/v1"],
    "interop": [SCHEMA],
}

ACCEPTS = {
    "explore": ["howl.candidate/v1"],
    "run": ["howl.candidate/v1"],
    "create": ["howl.candidate/v1"],
    "develop": ["howl.candidate/v1", "howl.assessment/v1", "howlwriter.copy_package/v1"],
    "scaffold": ["howl.candidate/v1", "howl.assessment/v1", "howlwriter.copy_package/v1"],
    "materialize": ["howl.development_result/v1"],
}


def _flags(parser: argparse.ArgumentParser) -> list:
    return sorted(
        option
        for action in parser._actions
        for option in action.option_strings
        if option not in ("-h", "--help")
    )


def describe(parser: argparse.ArgumentParser) -> dict:
    """Return the descriptor for ``parser`` and its subcommands (aliases included)."""
    commands = [{"path": [], "flags": _flags(parser), "json": False}]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                entry = {"path": [name], "flags": _flags(sub), "json": name in JSON_COMMANDS}
                if name in EMITS:
                    entry["emits"] = EMITS[name]
                if name in ACCEPTS:
                    entry["accepts"] = ACCEPTS[name]
                commands.append(entry)
    return {
        "schema": SCHEMA,
        "component": "howlcreate",
        "version": __version__,
        "commands": commands,
        "exit_codes": EXIT_CODES,
        "env": ENV,
        "consumes": [],
    }
