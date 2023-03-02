"""Tests for contract_utils.py."""

import aneta_backend_v2.server.contract_utils as ctrs


def test_contract_utils():
    """Tests contract utils of server."""
    assert ctrs.check_box_confirmation(
        "e92af88b69a5d5a5443cdc87870ff8ee329f0c588f3dd775fa7d02825909060a")
    assert not ctrs.check_box_confirmation("bad-box-id")
    assert ctrs.run_contracts()
