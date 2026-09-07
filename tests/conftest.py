"""Shared fixtures for HowlCreate test suite."""

import pytest
from howlcreate.models.idea import EpistemicStatus, Idea
from howlcreate.providers.deterministic import DeterministicProvider


@pytest.fixture
def deterministic_provider():
    return DeterministicProvider()


@pytest.fixture
def sample_idea_a():
    return Idea(
        id="idea-test-01",
        title="Verifiable Offline Proof Mesh",
        description="A localized mesh network where nodes verify test suites without continuous internet.",
        core_mechanism="Deterministic replay of recorded execution logs.",
        epistemic_status=EpistemicStatus.HYPOTHESIS,
    )


@pytest.fixture
def sample_idea_b():
    return Idea(
        id="idea-test-02",
        title="Reputation Staking Circles",
        description="Autonomous mutual-credit rings staking bounties on pull requests.",
        core_mechanism="Escrowed staking with automated dispute slashing.",
        epistemic_status=EpistemicStatus.IMAGINED_POSSIBILITY,
    )


@pytest.fixture
def temp_storage_dir(tmp_path):
    storage_path = tmp_path / "howlcreate_test_runs"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path
