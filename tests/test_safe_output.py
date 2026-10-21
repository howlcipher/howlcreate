"""Provider output is redacted with howl-provider-core's shared rules before it is kept."""

from howlcreate.providers.runtime import safe_output


def test_credentials_and_env_secrets_are_redacted(monkeypatch):
    monkeypatch.setenv("HOWLCREATE_TEST_TOKEN", "plain-secret-value-123")
    out = safe_output(
        "token plain-secret-value-123 key sk-abcdefghijklmnop aws AKIAABCDEFGHIJKLMNOP api_key=zzz"
    )
    for leaked in ("plain-secret-value-123", "sk-abc", "AKIA", "zzz"):
        assert leaked not in out
    assert "[REDACTED]" in out


def test_output_is_bounded():
    assert len(safe_output("x" * 70000)) == 65536
