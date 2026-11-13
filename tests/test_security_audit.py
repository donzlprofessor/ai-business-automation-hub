from pathlib import Path

import pytest

from scripts.check_secrets import findings, private_path


@pytest.mark.parametrize("name", [".env", ".env.local", "private.pem", "id_ed25519", ".npmrc"])
def test_guard_rejects_private_paths(name):
    assert private_path(Path(name))


def test_guard_allows_placeholder_examples_and_detects_known_local_credentials():
    assert not private_path(Path("frontend/.env.example"))
    assert not findings("PASSWORD=replace-with-random-password", [])
    secret = "example-" + "private-value-for-test"
    assert findings("copied value: " + secret, [secret])
    assert findings("ghp_" + "A" * 36, [])
