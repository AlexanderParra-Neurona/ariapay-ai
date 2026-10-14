import os
import subprocess
import sys

from app.tracing import REDACTED, mask_pii

_CHECK_MASK = """
import app.main
from langfuse import get_client
from app.tracing import mask_pii
assert get_client()._resources.mask is mask_pii
"""


def test_langfuse_client_has_pii_mask_after_app_import() -> None:
    # Langfuse keeps the first client built per public key, and agent.py builds a
    # CallbackHandler at import, so the mask must be registered before that. Runs
    # in a fresh interpreter with dummy keys: the check depends on import order,
    # and without a public key no keyed client is registered at all.
    env = {
        **os.environ,
        "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
        "LANGFUSE_SECRET_KEY": "sk-lf-test",
        "LANGFUSE_TRACING_ENABLED": "false",
    }
    result = subprocess.run(
        [sys.executable, "-c", _CHECK_MASK],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_mask_pii_redacts_access_token_in_span_input() -> None:
    masked = mask_pii(data={"access_token": "eyJ.secret", "page_size": 20})
    assert masked == {"access_token": REDACTED, "page_size": 20}
